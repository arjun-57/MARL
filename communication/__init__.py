"""Communication package for inter-agent messaging and attack injection."""

from .message import AgentMessage
from .message_bus import SimulatedMessageBus
from .latency import LatencyChannel, PacketLossChannel, StaleDataChannel
from .network_monitor import NetworkMonitor

__all__ = [
    "AgentMessage",
    "SimulatedMessageBus",
    "LatencyChannel",
    "PacketLossChannel",
    "StaleDataChannel",
    "NetworkMonitor",
]
