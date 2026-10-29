"""Check 1 — Physical Consistency Validation."""

import logging
from typing import Dict, Any, Tuple

from communication.message import AgentMessage

logger = logging.getLogger(__name__)


class PhysicalConsistencyChecker:
    """Verifies that reported agent telemetry and actions conform to physical capacity bounds."""

    def __init__(
        self,
        solar_capacity_mw: float = 1.5,
        bess_max_p_mw: float = 0.8,
        ev_max_p_mw: float = 0.5,
    ):
        self.solar_capacity_mw = solar_capacity_mw
        self.bess_max_p_mw = bess_max_p_mw
        self.ev_max_p_mw = ev_max_p_mw

    def check(self, msg: AgentMessage) -> Tuple[bool, float, str]:
        """
        Returns (is_valid, penalty_score, reason).
        penalty_score is in [0, 1] where 0 = perfect, 1 = severe violation.
        """
        sender = msg.sender
        p = msg.payload

        if sender == "solar_agent":
            # Solar generation cannot exceed rated capacity or be negative
            solar_p = p.get("generation_mw", p.get("forecast_mw", None))
            if solar_p is not None:
                if solar_p < -1e-3:
                    return False, 1.0, f"Negative solar generation {solar_p:.2f} MW physically impossible"
                if solar_p > self.solar_capacity_mw * 1.05:  # 5% sensor tolerance
                    overshoot = (solar_p - self.solar_capacity_mw) / self.solar_capacity_mw
                    penalty = min(1.0, float(overshoot))
                    return False, penalty, f"Solar power {solar_p:.2f} MW exceeds physical rating {self.solar_capacity_mw} MW"

        elif sender == "battery_agent":
            # BESS power must be within converter ratings
            bess_p = p.get("proposed_power_mw", None)
            if bess_p is not None:
                if abs(bess_p) > self.bess_max_p_mw * 1.05:
                    return False, 0.9, f"BESS power {bess_p:.2f} MW exceeds inverter capacity {self.bess_max_p_mw} MW"
            soc = p.get("soc", None)
            if soc is not None:
                if soc < 0.0 or soc > 1.0:
                    return False, 1.0, f"BESS SOC {soc:.2f} out of physical bounds [0, 1]"

        elif sender == "ev_agent":
            ev_p = p.get("charging_power_mw", None)
            if ev_p is not None:
                if ev_p < 0.0 or ev_p > self.ev_max_p_mw * 1.05:
                    return False, 0.8, f"EV charging power {ev_p:.2f} MW exceeds station capacity {self.ev_max_p_mw} MW"

        elif sender == "demand_agent":
            load_mw = p.get("reported_load_mw", None)
            if load_mw is not None and load_mw < 0.0:
                return False, 1.0, f"Negative customer load {load_mw:.2f} MW"

        return True, 0.0, "Physical checks passed"
