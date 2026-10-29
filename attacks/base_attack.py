"""Abstract Base Class for Cyber and Physical Attacks."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from communication.message import AgentMessage
from communication.message_bus import SimulatedMessageBus


class BaseAttack(ABC):
    """Abstract interface for all attack scenarios."""

    def __init__(self, name: str, start_step: int = 24, end_step: int = 72):
        self.name = name
        self.start_step = start_step
        self.end_step = end_step
        self.is_active = False

    def is_triggered(self, current_step: int) -> bool:
        """Determines if the attack is active at the current timestep."""
        self.is_active = self.start_step <= current_step <= self.end_step
        return self.is_active

    @abstractmethod
    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        """Applies communication or message-level attack modifications."""
        pass

    @abstractmethod
    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        """Applies physical-level environment modifications (if any)."""
        return data_row
