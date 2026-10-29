"""Check 2 — Temporal Consistency & Ramp Rate Validation."""

import logging
from typing import Dict, Any, Tuple
from collections import defaultdict
import numpy as np

from communication.message import AgentMessage

logger = logging.getLogger(__name__)


class TemporalConsistencyChecker:
    """Verifies temporal continuity and checks for unphysical telemetry jumps/gradients."""

    def __init__(self, max_solar_ramp_mw_per_h: float = 0.9, max_load_ramp_ratio: float = 0.6):
        self.max_solar_ramp_mw_per_h = max_solar_ramp_mw_per_h
        self.max_load_ramp_ratio = max_load_ramp_ratio
        # Store last values per agent
        self.last_values: Dict[str, Dict[str, float]] = defaultdict(dict)

    def check(self, msg: AgentMessage) -> Tuple[bool, float, str]:
        sender = msg.sender
        p = msg.payload

        if sender == "solar_agent":
            val = p.get("generation_mw", p.get("forecast_mw", None))
            if val is not None and "solar_val" in self.last_values[sender]:
                prev = self.last_values[sender]["solar_val"]
                delta = abs(val - prev)
                self.last_values[sender]["solar_val"] = val
                if delta > self.max_solar_ramp_mw_per_h:
                    penalty = min(1.0, (delta - self.max_solar_ramp_mw_per_h) / self.max_solar_ramp_mw_per_h)
                    return False, penalty, f"Unphysical solar ramp rate: delta={delta:.2f} MW > limit={self.max_solar_ramp_mw_per_h} MW/h"
            elif val is not None:
                self.last_values[sender]["solar_val"] = val

        elif sender == "demand_agent":
            val = p.get("reported_load_mw", None)
            if val is not None and "load_val" in self.last_values[sender]:
                prev = self.last_values[sender]["load_val"]
                if prev > 0:
                    jump_ratio = abs(val - prev) / prev
                    self.last_values[sender]["load_val"] = val
                    if jump_ratio > self.max_load_ramp_ratio:
                        penalty = min(1.0, jump_ratio - self.max_load_ramp_ratio)
                        return False, penalty, f"Extreme demand surge/drop jump ratio: {jump_ratio*100:.1f}%"
            elif val is not None:
                self.last_values[sender]["load_val"] = val

        return True, 0.0, "Temporal continuity passed"
