"""Network degradation primitives: Latency, Packet Loss, and Stale Data Replay."""

import logging
from typing import List, Optional
import numpy as np

from communication.message import AgentMessage

logger = logging.getLogger(__name__)


class LatencyChannel:
    """Delays message delivery by N timesteps."""

    def __init__(self, delay_steps: int = 1):
        self.delay_steps = delay_steps
        self.delayed_queue: List[tuple[int, AgentMessage]] = []

    def buffer_message(self, current_step: int, msg: AgentMessage):
        """Queue message with deliverable step."""
        deliver_step = current_step + self.delay_steps
        self.delayed_queue.append((deliver_step, msg))

    def get_deliverable_messages(self, current_step: int) -> List[AgentMessage]:
        """Release messages that have completed their delay period."""
        ready = [msg for step, msg in self.delayed_queue if step <= current_step]
        self.delayed_queue = [item for item in self.delayed_queue if item[0] > current_step]
        return ready


class PacketLossChannel:
    """Stochastically drops messages based on drop probability."""

    def __init__(self, drop_probability: float = 0.20, random_seed: int = 42):
        self.drop_probability = drop_probability
        self.rng = np.random.default_rng(random_seed)

    def should_drop(self) -> bool:
        """Determines if the current packet should be discarded."""
        return bool(self.rng.random() < self.drop_probability)


class StaleDataChannel:
    """Replaces current live telemetry with an old frozen/stale message."""

    def __init__(self, replay_lag_steps: int = 4):
        self.replay_lag_steps = replay_lag_steps
        self.history_buffer: List[AgentMessage] = []

    def record_and_corrupt(self, current_msg: AgentMessage) -> AgentMessage:
        """Saves message and returns a stale historical version if buffer allows."""
        self.history_buffer.append(current_msg)
        if len(self.history_buffer) > self.replay_lag_steps:
            stale_msg = self.history_buffer[-self.replay_lag_steps - 1]
            stale_copy = AgentMessage(
                sender=current_msg.sender,
                receiver=current_msg.receiver,
                message_type=current_msg.message_type,
                timestamp=stale_msg.timestamp,
                step=stale_msg.step,
                payload=stale_msg.payload,
                confidence=0.5,
                sequence_id=current_msg.sequence_id,
                tampered=True
            )
            return stale_copy
        return current_msg
