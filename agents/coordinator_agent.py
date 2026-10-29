"""Coordinator Agent resolving multi-agent conflicts with trust weighting."""

import logging
from typing import Dict, Any, List, Tuple

from agents.base_agent import BaseAgent
from agents.safety_agent import SafetyAgent
from communication.message_bus import SimulatedMessageBus
from communication.message import AgentMessage

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Central or decentralized cluster coordinator that collects agent proposals,
    weights them by cyber-physical trust scores, resolves objective conflicts,
    and dispatches final control directives through the Safety Agent.
    """

    def __init__(
        self,
        agent_id: str = "coordinator_agent",
        bus: SimulatedMessageBus = None,
        use_trust_weighting: bool = True
    ):
        super().__init__(agent_id=agent_id, bus=bus)
        self.use_trust_weighting = use_trust_weighting
        self.safety_agent = SafetyAgent()

    def coordinate(
        self,
        current_step: int,
        env_state: Dict[str, Any],
        agent_proposals: Dict[str, Dict[str, Any]],
        trust_scores: Dict[str, float]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Synthesizes agent proposals, applies trust scores to filter out tampered data,
        resolves conflicts, and filters via Safety Agent.
        """
        # Default baseline actions
        aggregated = {
            "battery_p_mw": 0.0,
            "ev_p_mw": 0.1,
            "solar_curtail_mw": 0.0,
            "load_shift_ratio": 0.0
        }

        # 1. Evaluate Solar Agent proposal
        solar_prop = agent_proposals.get("solar_agent", {})
        solar_gen = float(solar_prop.get("generation_mw", 0.0))
        solar_curtail = float(solar_prop.get("curtailment_proposed_mw", 0.0))
        solar_trust = trust_scores.get("solar_agent", 1.0) if self.use_trust_weighting else 1.0

        if solar_trust >= 0.40:
            # Trusted or unverified: Coordinator accepts reported solar generation
            # If reported solar generation > 0.8 MW, coordinator perceives a local renewable surplus!
            perceived_solar_surplus = max(0.0, solar_gen - 0.6)
            aggregated["solar_curtail_mw"] = solar_curtail
        else:
            # Quarantined / Untrusted: Coordinator discounts fraudulent solar report
            logger.warning(f"Coordinator discounting Solar Agent (Trust={solar_trust:.2f})")
            perceived_solar_surplus = 0.0
            aggregated["solar_curtail_mw"] = 0.0

        # 2. Evaluate Demand Agent proposal
        demand_prop = agent_proposals.get("demand_agent", {})
        demand_trust = trust_scores.get("demand_agent", 1.0) if self.use_trust_weighting else 1.0
        if demand_trust >= 0.40:
            aggregated["load_shift_ratio"] = float(demand_prop.get("proposed_load_shift_ratio", 0.0))
        else:
            logger.warning(f"Coordinator discounting Demand Agent (Trust={demand_trust:.2f})")
            aggregated["load_shift_ratio"] = 0.0

        # 3. Evaluate Battery Agent & Market Agent interaction
        bess_prop = agent_proposals.get("battery_agent", {})
        bess_trust = trust_scores.get("battery_agent", 1.0) if self.use_trust_weighting else 1.0
        market_prop = agent_proposals.get("market_agent", {})
        market_trust = trust_scores.get("market_agent", 1.0) if self.use_trust_weighting else 1.0

        bess_power = float(bess_prop.get("proposed_power_mw", 0.0))
        market_action = market_prop.get("action", "HOLD")
        market_power = float(market_prop.get("power_mw", 0.0))

        # Solar surplus absorption logic:
        # If perceived solar surplus is high, coordinator commands BESS to absorb it!
        if perceived_solar_surplus > 0.4:
            aggregated["battery_p_mw"] = min(0.8, perceived_solar_surplus)
        elif bess_trust >= 0.40:
            if market_trust >= 0.40:
                if market_action == "BUY" and bess_power >= 0:
                    aggregated["battery_p_mw"] = max(bess_power, market_power)
                elif market_action == "SELL" and bess_power <= 0:
                    aggregated["battery_p_mw"] = min(bess_power, market_power)
                else:
                    aggregated["battery_p_mw"] = bess_power
            else:
                aggregated["battery_p_mw"] = bess_power
        else:
            logger.warning(f"Coordinator discounting Battery Agent (Trust={bess_trust:.2f})")
            aggregated["battery_p_mw"] = 0.0

        # 4. Evaluate EV Agent proposal
        ev_prop = agent_proposals.get("ev_agent", {})
        ev_trust = trust_scores.get("ev_agent", 1.0) if self.use_trust_weighting else 1.0
        nominal_ev = float(ev_prop.get("charging_power_mw", 0.1))

        # Under perceived solar surplus, coordinator commands boosted EV charging
        if perceived_solar_surplus > 0.7:
            aggregated["ev_p_mw"] = 0.5
        elif ev_trust >= 0.40:
            aggregated["ev_p_mw"] = nominal_ev
        else:
            aggregated["ev_p_mw"] = 0.1

        # 5. Pass through Safety Agent for physical constraint enforcement
        safe_actions, safety_status, safety_mods = self.safety_agent.filter_actions(
            proposed_actions=aggregated,
            current_env_state=env_state
        )

        audit = {
            "raw_aggregated": aggregated,
            "safe_actions": safe_actions,
            "safety_status": safety_status,
            "safety_modifications": safety_mods,
            "trust_scores_used": trust_scores
        }

        return safe_actions, audit

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.agent_id}
