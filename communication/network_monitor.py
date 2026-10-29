"""Communication Network Telemetry Monitor."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Tracks communication bus traffic, packet loss rates, and latency statistics."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.total_messages_sent = 0
        self.total_messages_delivered = 0
        self.total_messages_dropped = 0
        self.total_messages_delayed = 0
        self.total_messages_tampered = 0

    def record_sent(self):
        self.total_messages_sent += 1

    def record_delivered(self):
        self.total_messages_delivered += 1

    def record_dropped(self):
        self.total_messages_dropped += 1

    def record_delayed(self):
        self.total_messages_delayed += 1

    def record_tampered(self):
        self.total_messages_tampered += 1

    def get_stats(self) -> Dict[str, Any]:
        """Calculates loss rates and transmission statistics."""
        loss_rate = (
            self.total_messages_dropped / max(1, self.total_messages_sent)
        )
        return {
            "total_sent": self.total_messages_sent,
            "total_delivered": self.total_messages_delivered,
            "total_dropped": self.total_messages_dropped,
            "total_delayed": self.total_messages_delayed,
            "total_tampered": self.total_messages_tampered,
            "packet_loss_rate": float(loss_rate)
        }
