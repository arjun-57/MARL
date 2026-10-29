"""Abstract Base Agent Definition."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time

from communication.message import AgentMessage
from communication.message_bus import SimulatedMessageBus


class BaseAgent(ABC):
    """Abstract Base Class for all specialized agents in the Resilient MAS."""

    def __init__(self, agent_id: str, bus: SimulatedMessageBus):
        self.agent_id = agent_id
        self.bus = bus
        self.inbox: List[AgentMessage] = []

    def receive_messages(self):
        """Pulls messages delivered to this agent from the bus."""
        self.inbox.extend(self.bus.receive_messages(self.agent_id))

    def send_message(self, receiver: str, message_type: str, payload: Dict[str, Any], step: int, confidence: float = 1.0):
        """Dispatches an asynchronous message through the bus."""
        msg = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            timestamp=time.time(),
            step=step,
            payload=payload,
            confidence=confidence
        )
        self.bus.send_message(msg, current_step=step)

    @abstractmethod
    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        """Observes environment, updates internal state, and generates proposals/messages."""
        pass
