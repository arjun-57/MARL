"""Check 4 — Statistical Anomaly Detection (Rolling Z-Score & EWMA)."""

import logging
from typing import Dict, Any, Tuple
from collections import defaultdict, deque
import numpy as np

logger = logging.getLogger(__name__)


class StatisticalAnomalyDetector:
    """Detects statistical anomalies using rolling Z-scores and EWMA residuals."""

    def __init__(self, window_size: int = 24, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        # Rolling buffers per agent signal
        self.history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))

    def evaluate_metric(self, agent_id: str, metric_name: str, value: float) -> Tuple[bool, float, str]:
        """
        Calculates rolling z-score of signal.
        Returns (is_normal, anomaly_score, reason).
        """
        key = f"{agent_id}_{metric_name}"
        buf = self.history[key]

        if len(buf) < 10:
            # Warm-up period
            buf.append(value)
            return True, 0.0, "Warm-up phase"

        arr = np.array(buf)
        mean = float(np.mean(arr))
        std = float(np.std(arr))

        buf.append(value)

        if std < 1e-4:
            # Flat signal
            is_anomaly = abs(value - mean) > 0.5
            return not is_anomaly, 0.5 if is_anomaly else 0.0, "Near-zero variance"

        z_score = abs(value - mean) / std
        if z_score > self.z_threshold:
            anomaly_score = min(1.0, (z_score - self.z_threshold) / 2.0)
            return False, float(anomaly_score), f"Statistical anomaly: Z-score={z_score:.2f} > {self.z_threshold}"

        return True, 0.0, f"Normal Z-score={z_score:.2f}"
