"""Trust Agent managing continuous cyber-physical verification of all MAS agents."""

import logging
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from communication.message import AgentMessage
from communication.message_bus import SimulatedMessageBus
from security.incident_manager import IncidentManager

logger = logging.getLogger(__name__)


class TrustAgent(BaseAgent):
    """
    Independent sentinel agent that inspects all messages transmitted across the communication bus,
    evaluates physical/temporal/cross/statistical consistency, and updates trust scores.
    """

    def __init__(self, agent_id: str = "trust_agent", bus: SimulatedMessageBus = None):
        super().__init__(agent_id=agent_id, bus=bus)
        self.incident_manager = IncidentManager()

    def inspect_messages(
        self,
        messages: List[AgentMessage],
        current_step: int,
        timestamp_str: str,
        grid_load_mw: float,
        hour_of_day: int
    ) -> Dict[str, float]:
        """Runs security checks on every message delivered to the coordinator."""
        for msg in messages:
            self.incident_manager.evaluate_incoming_message(
                msg=msg,
                step=current_step,
                timestamp_str=timestamp_str,
                grid_load_mw=grid_load_mw,
                hour_of_day=hour_of_day
            )
        return self.incident_manager.get_trust_scores()

    def get_trust_scores(self) -> Dict[str, float]:
        return self.incident_manager.get_trust_scores()

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent": self.agent_id, "trust_scores": self.get_trust_scores()}
