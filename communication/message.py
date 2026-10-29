"""Communication Message Data Structures."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time


@dataclass
class AgentMessage:
    """Standardized asynchronous inter-agent message structure."""
    sender: str
    receiver: str
    message_type: str
    timestamp: float
    step: int
    payload: Dict[str, Any]
    confidence: float = 1.0
    sequence_id: int = 0
    tampered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
            "step": self.step,
            "payload": self.payload,
            "confidence": self.confidence,
            "sequence_id": self.sequence_id,
            "tampered": self.tampered,
        }
