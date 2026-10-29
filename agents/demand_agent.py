"""Demand Agent responsible for feeder load monitoring and flexible demand response."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class DemandAgent(BaseAgent):
    """Monitors feeder electrical demand and proposes load curtailment/shifting under stress."""

    def __init__(self, agent_id: str = "demand_agent", bus: SimulatedMessageBus = None, max_flexibility: float = 0.10):
        super().__init__(agent_id=agent_id, bus=bus)
        self.max_flexibility = max_flexibility

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        self.receive_messages()

        load_mw = float(env_state.get("load_mw", 40000.0))
        v_min = float(env_state.get("v_min_pu", 1.0))
        price = float(env_state.get("price_eur_mwh", 50.0))

        # Under severe undervoltage (< 0.93 p.u.) or extreme price spikes, propose demand reduction
        proposed_shift = 0.0
        if v_min < 0.93:
            # Shift down load to alleviate undervoltage
            proposed_shift = - min(self.max_flexibility, (0.93 - v_min) * 2.0)
        elif price > 120.0:
            # Shift down 5% to avoid exorbitant spot price
            proposed_shift = -0.05

        self.send_message(
            receiver="coordinator_agent",
            message_type="demand_forecast_report",
            payload={
                "reported_load_mw": load_mw,
                "proposed_load_shift_ratio": proposed_shift,
                "flexibility_available": self.max_flexibility
            },
            step=current_step,
            confidence=0.92
        )

        return {
            "agent": self.agent_id,
            "load_mw": load_mw,
            "proposed_load_shift_ratio": proposed_shift
        }
