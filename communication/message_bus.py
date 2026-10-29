"""Simulated Multi-Agent Message Bus with Cyber-Physical Attack Hooks."""

import logging
from typing import Dict, List, Optional, Callable
from collections import defaultdict

from communication.message import AgentMessage
from communication.latency import LatencyChannel, PacketLossChannel, StaleDataChannel
from communication.network_monitor import NetworkMonitor

logger = logging.getLogger(__name__)


class SimulatedMessageBus:
    """
    Simulates inter-agent communication network with configurable latency,
    packet drop rates, and adversarial message manipulation.
    """

    def __init__(self, random_seed: int = 42):
        self.monitor = NetworkMonitor()
        self.latency_channel = LatencyChannel(delay_steps=1)
        self.loss_channel = PacketLossChannel(drop_probability=0.0, random_seed=random_seed)
        self.stale_channel = StaleDataChannel(replay_lag_steps=3)

        # Message inboxes keyed by receiver agent ID
        self.inboxes: Dict[str, List[AgentMessage]] = defaultdict(list)
        # Sequence counter
        self.msg_sequence = 0

        # Attack modifiers (pluggable functions that intercept messages)
        self.attack_interceptors: List[Callable[[AgentMessage], Optional[AgentMessage]]] = []

        # Flags for active channel attacks
        self.delay_active = False
        self.loss_active = False
        self.stale_active = False

    def register_interceptor(self, interceptor_fn: Callable[[AgentMessage], Optional[AgentMessage]]):
        """Add an attack interceptor to modify or drop messages."""
        self.attack_interceptors.append(interceptor_fn)

    def clear_interceptors(self):
        """Reset all attack interceptors."""
        self.attack_interceptors = []
        self.delay_active = False
        self.loss_active = False
        self.stale_active = False

    def send_message(self, msg: AgentMessage, current_step: int):
        """Processes and delivers or queues a message."""
        self.monitor.record_sent()
        msg.sequence_id = self.msg_sequence
        self.msg_sequence += 1

        # 1. Packet Loss Attack Check
        if self.loss_active and self.loss_channel.should_drop():
            self.monitor.record_dropped()
            return

        # 2. Stale Data Attack Check
        if self.stale_active:
            msg = self.stale_channel.record_and_corrupt(msg)
            if msg.tampered:
                self.monitor.record_tampered()

        # 3. Interceptors (e.g., False Data Injection)
        for interceptor in self.attack_interceptors:
            msg = interceptor(msg)
            if msg is None:
                self.monitor.record_dropped()
                return

        # 4. Latency Delay Attack Check
        if self.delay_active:
            self.monitor.record_delayed()
            self.latency_channel.buffer_message(current_step, msg)
            return

        # Immediate Delivery
        self.inboxes[msg.receiver].append(msg)
        self.monitor.record_delivered()

    def step(self, current_step: int):
        """Flush delayed messages that are ready for delivery at current_step."""
        if self.delay_active:
            ready_msgs = self.latency_channel.get_deliverable_messages(current_step)
            for msg in ready_msgs:
                self.inboxes[msg.receiver].append(msg)
                self.monitor.record_delivered()

    def receive_messages(self, receiver_id: str) -> List[AgentMessage]:
        """Pulls and drains all messages currently in receiver's inbox."""
        msgs = self.inboxes.pop(receiver_id, [])
        return msgs
