"""Baseline 2: Independent Multi-Agent System (Decentralized Uncoordinated)."""

import logging
from typing import Dict, Any

from communication.message_bus import SimulatedMessageBus
from agents.solar_agent import SolarAgent
from agents.demand_agent import DemandAgent
from agents.battery_agent import BatteryAgent
from agents.ev_agent import EVAgent
from agents.market_agent import MarketAgent

logger = logging.getLogger(__name__)


class IndependentMASController:
    """
    Decentralized multi-agent baseline where agents operate independently
    without coordination, trust checks, or cyber-attack resilience.
    Actions are applied directly without conflict resolution or trust weighting.
    """

    def __init__(self, bus: SimulatedMessageBus):
        self.bus = bus
        self.solar_agent = SolarAgent(bus=bus)
        self.demand_agent = DemandAgent(bus=bus)
        self.battery_agent = BatteryAgent(bus=bus)
        self.ev_agent = EVAgent(bus=bus)
        self.market_agent = MarketAgent(bus=bus)

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs all independent agents and merges raw proposals greedily."""
        solar_res = self.solar_agent.step(current_step, env_state)
        demand_res = self.demand_agent.step(current_step, env_state)
        battery_res = self.battery_agent.step(current_step, env_state)
        ev_res = self.ev_agent.step(current_step, env_state)
        market_res = self.market_agent.step(current_step, env_state)

        # Uncoordinated greedy actions:
        # 1. Battery reacts greedily to perceived solar or market
        perceived_solar = float(env_state.get("solar_available_mw", 0.0))
        bess_p = float(battery_res.get("proposed_power_mw", 0.0))

        if perceived_solar > 0.8:
            bess_p = min(0.8, perceived_solar * 0.7)
        elif market_res.get("action") == "BUY":
            bess_p = max(bess_p, 0.5)
        elif market_res.get("action") == "SELL":
            bess_p = min(bess_p, -0.5)

        # 2. EV fleet charges greedily (uncoordinated fast charging)
        ev_count = int(env_state.get("ev_connected_count", 0))
        if perceived_solar > 0.8:
            ev_p = min(0.5, ev_count * 0.05)  # Fast charge under perceived green solar
        else:
            ev_p = min(0.35, ev_count * 0.035)

        return {
            "battery_p_mw": bess_p,
            "ev_p_mw": float(ev_p),
            "solar_curtail_mw": float(solar_res.get("proposed_curtailment_mw", 0.0)),
            "load_shift_ratio": 0.0  # Uncoordinated: no demand response shifting
        }
