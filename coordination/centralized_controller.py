"""Baseline 1: Centralized Rule-Based Controller."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CentralizedRuleController:
    """
    Classical centralized benchmark controller.
    Uses centralized global rules to dispatch BESS, EV, and solar curtailment
    without distributed agent decomposition, trust scores, or cyber resilience.
    """

    def __init__(self, bess_max_p_mw: float = 0.8, ev_max_p_mw: float = 0.5):
        self.bess_max_p_mw = bess_max_p_mw
        self.ev_max_p_mw = ev_max_p_mw

    def compute_action(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates control action directly from global state telemetry."""
        price = float(current_state.get("price_eur_mwh", 50.0))
        solar = float(current_state.get("solar_available_mw", 0.0))
        soc = float(current_state.get("battery_soc", 0.50))
        v_min = float(current_state.get("v_min_pu", 1.0))
        v_max = float(current_state.get("v_max_pu", 1.0))
        ev_count = int(current_state.get("ev_connected_count", 0))

        # Battery logic: Simple peak shaving & price thresholding
        bess_p = 0.0
        if v_min < 0.94 and soc > 0.15:
            bess_p = - self.bess_max_p_mw  # Discharge to boost voltage
        elif solar > 0.8 and soc < 0.90:
            bess_p = min(self.bess_max_p_mw, solar * 0.7)  # Absorb solar
        elif price < 35.0 and soc < 0.90:
            bess_p = 0.5 * self.bess_max_p_mw  # Charge cheap power
        elif price > 70.0 and soc > 0.15:
            bess_p = - 0.6 * self.bess_max_p_mw  # Discharge expensive power

        # EV logic: Charge all connected cars up to limit
        ev_p = min(self.ev_max_p_mw, ev_count * 0.05)

        # Solar curtailment only if overvoltage
        curtail_mw = 0.0
        if v_max > 1.05:
            curtail_mw = min(solar, (v_max - 1.05) * 5.0)

        return {
            "battery_p_mw": float(bess_p),
            "ev_p_mw": float(ev_p),
            "solar_curtail_mw": float(curtail_mw),
            "load_shift_ratio": 0.0
        }
