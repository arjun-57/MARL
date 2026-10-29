"""Proposed Coordinated and Resilient Multi-Agent Controllers."""

import logging
from typing import Dict, Any, Tuple

from communication.message_bus import SimulatedMessageBus
from agents.solar_agent import SolarAgent
from agents.demand_agent import DemandAgent
from agents.battery_agent import BatteryAgent
from agents.ev_agent import EVAgent
from agents.market_agent import MarketAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.trust_agent import TrustAgent

logger = logging.getLogger(__name__)


class ResilientMASController:
    """
    Proposed Resilient Multi-Agent System (Resilient-MAS).
    Full closed-loop architecture:
    1. Agents observe state and broadcast proposals through SimulatedMessageBus
    2. TrustAgent inspects messages (Checks 1-4: Physical, Temporal, Cross, Statistical)
    3. Coordinator weights proposals by real-time Trust Scores [0, 1]
    4. SafetyAgent filters aggregated actions for hard electrical constraints
    """

    def __init__(self, bus: SimulatedMessageBus, enable_resilience: bool = True):
        self.bus = bus
        self.enable_resilience = enable_resilience

        self.solar_agent = SolarAgent(bus=bus)
        self.demand_agent = DemandAgent(bus=bus)
        self.battery_agent = BatteryAgent(bus=bus)
        self.ev_agent = EVAgent(bus=bus)
        self.market_agent = MarketAgent(bus=bus)

        self.trust_agent = TrustAgent(bus=bus)
        self.coordinator = CoordinatorAgent(bus=bus, use_trust_weighting=enable_resilience)

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Executes complete multi-agent communication, verification, and coordination loop.
        """
        # 1. Step specialized agents -> emits messages to bus
        solar_p = self.solar_agent.step(current_step, env_state)
        demand_p = self.demand_agent.step(current_step, env_state)
        battery_p = self.battery_agent.step(current_step, env_state)
        ev_p = self.ev_agent.step(current_step, env_state)
        market_p = self.market_agent.step(current_step, env_state)

        # 2. Flush and deliver any delayed messages on bus
        self.bus.step(current_step)

        # 3. Coordinator collects messages delivered to its inbox
        coord_msgs = self.bus.receive_messages("coordinator_agent")

        # 4. Coordinator extracts proposals directly from messages delivered via the message bus
        proposals = {}
        for msg in coord_msgs:
            proposals[msg.sender] = msg.payload

        # For any agent whose message was dropped/delayed, default to autonomous fallback
        if "solar_agent" not in proposals:
            proposals["solar_agent"] = {"generation_mw": 0.0, "curtailment_proposed_mw": 0.0}
        if "demand_agent" not in proposals:
            proposals["demand_agent"] = {"reported_load_mw": float(env_state.get("load_mw", 40000.0)), "proposed_load_shift_ratio": 0.0}
        if "battery_agent" not in proposals:
            proposals["battery_agent"] = {"proposed_power_mw": 0.0, "soc": float(env_state.get("battery_soc", 0.5))}
        if "ev_agent" not in proposals:
            proposals["ev_agent"] = {"charging_power_mw": 0.1}
        if "market_agent" not in proposals:
            proposals["market_agent"] = {"action": "HOLD", "power_mw": 0.0}

        # 5. Trust Agent inspects all incoming coordinator messages if resilience enabled
        if self.enable_resilience:
            trust_scores = self.trust_agent.inspect_messages(
                messages=coord_msgs,
                current_step=current_step,
                timestamp_str=str(env_state.get("timestamp", current_step)),
                grid_load_mw=float(env_state.get("load_mw", 40000.0)),
                hour_of_day=int(current_step % 24)
            )
        else:
            # Unprotected Coordinated MAS: Trust scores are static 1.0 (blind trust)
            trust_scores = {
                "solar_agent": 1.0,
                "demand_agent": 1.0,
                "battery_agent": 1.0,
                "ev_agent": 1.0,
                "market_agent": 1.0
            }

        # 6. Coordinator synthesizes proposals with trust scores
        safe_action, audit = self.coordinator.coordinate(
            current_step=current_step,
            env_state=env_state,
            agent_proposals=proposals,
            trust_scores=trust_scores
        )

        # In unprotected Coordinated MAS, execute raw unverified action without safety agent override
        if not self.enable_resilience:
            safe_action = dict(audit["raw_aggregated"])

        audit["trust_scores"] = trust_scores
        audit["comm_stats"] = self.bus.monitor.get_stats()

        return safe_action, audit
