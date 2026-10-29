"""Solar Agent responsible for PV monitoring, forecasting, and curtailment proposals."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class SolarAgent(BaseAgent):
    """Monitors Bus 18 Solar PV output and broadcasts generation telemetry & curtailment proposals."""

    def __init__(self, agent_id: str = "solar_agent", bus: SimulatedMessageBus = None, capacity_mw: float = 1.5):
        super().__init__(agent_id=agent_id, bus=bus)
        self.capacity_mw = capacity_mw

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        self.receive_messages()

        solar_avail = float(env_state.get("solar_available_mw", 0.0))
        v_max = float(env_state.get("v_max_pu", 1.0))

        # Heuristic: Propose curtailment only if overvoltage occurs (> 1.05 p.u.)
        curtail_proposal = 0.0
        if v_max > 1.045:
            curtail_proposal = min(solar_avail, (v_max - 1.045) * 5.0)

        # Broadcast telemetry to coordinator
        self.send_message(
            receiver="coordinator_agent",
            message_type="solar_generation_report",
            payload={
                "generation_mw": solar_avail,
                "curtailment_proposed_mw": curtail_proposal,
                "bus_id": 18
            },
            step=current_step,
            confidence=0.95
        )

        return {
            "agent": self.agent_id,
            "solar_available_mw": solar_avail,
            "proposed_curtailment_mw": curtail_proposal
        }
