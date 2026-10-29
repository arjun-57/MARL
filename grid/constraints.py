"""Grid Operational Constraints and Violation Checking."""

import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


class GridConstraints:
    """Evaluates physical and operational grid constraints."""

    def __init__(
        self,
        v_min_nominal: float = 0.95,
        v_max_nominal: float = 1.05,
        v_min_emergency: float = 0.90,
        v_max_emergency: float = 1.10,
        max_line_loading_pct: float = 100.0
    ):
        self.v_min_nominal = v_min_nominal
        self.v_max_nominal = v_max_nominal
        self.v_min_emergency = v_min_emergency
        self.v_max_emergency = v_max_emergency
        self.max_line_loading_pct = max_line_loading_pct

    def evaluate(self, pf_results: Dict[str, Any]) -> Dict[str, Any]:
        """Checks power flow telemetry against operational standards (ANSI C84.1 / EN 50160)."""
        if not pf_results.get("converged", False):
            return {
                "safe": False,
                "converged": False,
                "voltage_violation_count": 33,
                "voltage_violation_severity": 10.0,
                "overloaded_line_count": 32,
                "max_line_overload": 200.0,
                "details": ["Power flow did not converge - physical collapse/severe islanding"]
            }

        bus_voltages = pf_results.get("bus_voltages", {})
        line_loadings = pf_results.get("line_loadings", {})

        v_violations: List[str] = []
        total_v_deviation = 0.0

        for bus_id, v in bus_voltages.items():
            if v < self.v_min_nominal:
                dev = self.v_min_nominal - v
                total_v_deviation += dev
                v_violations.append(f"Bus {bus_id} undervoltage: {v:.4f} p.u. (< {self.v_min_nominal})")
            elif v > self.v_max_nominal:
                dev = v - self.v_max_nominal
                total_v_deviation += dev
                v_violations.append(f"Bus {bus_id} overvoltage: {v:.4f} p.u. (> {self.v_max_nominal})")

        line_violations: List[str] = []
        max_line_overload = 0.0

        for line_id, loading in line_loadings.items():
            if loading > self.max_line_loading_pct:
                over = loading - self.max_line_loading_pct
                if over > max_line_overload:
                    max_line_overload = over
                line_violations.append(f"Line {line_id} overloaded: {loading:.1f}% (> {self.max_line_loading_pct}%)")

        is_safe = (len(v_violations) == 0) and (len(line_violations) == 0)

        return {
            "safe": is_safe,
            "converged": True,
            "voltage_violation_count": len(v_violations),
            "voltage_violation_severity": float(total_v_deviation),
            "overloaded_line_count": len(line_violations),
            "max_line_overload": float(max_line_overload),
            "v_min_pu": pf_results.get("v_min_pu", 1.0),
            "v_max_pu": pf_results.get("v_max_pu", 1.0),
            "max_line_loading_pct": pf_results.get("max_line_loading_pct", 0.0),
            "details": v_violations + line_violations
        }
