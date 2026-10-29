"""Check 3 — Cross-Agent & Redundancy Consistency Validation."""

import logging
from typing import Dict, Any, Tuple
import numpy as np

from communication.message import AgentMessage

logger = logging.getLogger(__name__)


class CrossAgentConsistencyChecker:
    """Validates telemetry consistency across multiple independent agents and sensor nodes."""

    def __init__(self, tolerance_pct: float = 0.25):
        self.tolerance_pct = tolerance_pct

    def check_demand_vs_grid(
        self,
        demand_agent_load_mw: float,
        grid_measured_load_mw: float
    ) -> Tuple[bool, float, str]:
        """Compares Demand Agent reported load against physical grid substation feeder flow."""
        if grid_measured_load_mw <= 0:
            return True, 0.0, "Zero baseline"

        discrepancy = abs(demand_agent_load_mw - grid_measured_load_mw) / grid_measured_load_mw
        if discrepancy > self.tolerance_pct:
            penalty = min(1.0, (discrepancy - self.tolerance_pct) / self.tolerance_pct)
            return False, penalty, (
                f"Cross-check mismatch: Demand Agent reported {demand_agent_load_mw:.2f} MW, "
                f"Grid measured {grid_measured_load_mw:.2f} MW (diff: {discrepancy*100:.1f}%)"
            )
        return True, 0.0, "Cross-agent validation passed"

    def check_solar_vs_clock(
        self,
        reported_solar_mw: float,
        hour_of_day: int
    ) -> Tuple[bool, float, str]:
        """Verifies solar is zero during nighttime hours (21:00 - 05:00)."""
        if (hour_of_day >= 21 or hour_of_day <= 5) and reported_solar_mw > 0.01:
            return False, 1.0, f"Nighttime solar generation reported at hour {hour_of_day}: {reported_solar_mw:.2f} MW"
        return True, 0.0, "Astronomical clock consistency passed"
