"""Safety Agent acting as hard cyber-physical constraint governor."""

import logging
from typing import Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class SafetyAgent:
    """
    Final protective authority between agent coordination and the physical grid.
    Enforces battery SOC limits, converter capacities, voltage guardbands, and emergency overrides.
    """

    def __init__(
        self,
        bess_max_p_mw: float = 0.8,
        soc_min: float = 0.10,
        soc_max: float = 0.95,
        ev_max_p_mw: float = 0.5,
        v_crit_low: float = 0.92,
        v_crit_high: float = 1.08
    ):
        self.bess_max_p_mw = bess_max_p_mw
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.ev_max_p_mw = ev_max_p_mw
        self.v_crit_low = v_crit_low
        self.v_crit_high = v_crit_high

    def filter_actions(
        self,
        proposed_actions: Dict[str, Any],
        current_env_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str, list]:
        """
        Validates proposed actions against strict physical constraints.
        Returns: (safe_actions, status ['ACCEPT', 'MODIFY', 'REJECT', 'EMERGENCY'], modifications_list)
        """
        modifications = []
        safe_actions = dict(proposed_actions)
        status = "ACCEPT"

        battery_p = float(proposed_actions.get("battery_p_mw", 0.0))
        ev_p = float(proposed_actions.get("ev_p_mw", 0.1))
        solar_curtail = float(proposed_actions.get("solar_curtail_mw", 0.0))
        load_shift = float(proposed_actions.get("load_shift_ratio", 0.0))

        current_soc = float(current_env_state.get("battery_soc", 0.50))
        v_min = float(current_env_state.get("v_min_pu", 1.0))
        v_max = float(current_env_state.get("v_max_pu", 1.0))

        # 1. Battery Power & SOC Hard Guard
        if battery_p > 0:  # Charging
            if current_soc >= self.soc_max:
                safe_actions["battery_p_mw"] = 0.0
                modifications.append(f"Blocked BESS charge: SOC {current_soc:.2f} >= max {self.soc_max}")
                status = "MODIFY"
            else:
                clamped_p = min(battery_p, self.bess_max_p_mw)
                if clamped_p != battery_p:
                    safe_actions["battery_p_mw"] = clamped_p
                    modifications.append(f"Clamped BESS charge to rating {self.bess_max_p_mw} MW")
                    status = "MODIFY"

        elif battery_p < 0:  # Discharging
            if current_soc <= self.soc_min:
                safe_actions["battery_p_mw"] = 0.0
                modifications.append(f"Blocked BESS discharge: SOC {current_soc:.2f} <= min {self.soc_min}")
                status = "MODIFY"
            else:
                clamped_p = max(battery_p, -self.bess_max_p_mw)
                if clamped_p != battery_p:
                    safe_actions["battery_p_mw"] = clamped_p
                    modifications.append(f"Clamped BESS discharge to rating {self.bess_max_p_mw} MW")
                    status = "MODIFY"

        # 2. EV Power Rating
        clamped_ev = float(np.clip(ev_p, 0.0, self.ev_max_p_mw))
        if clamped_ev != ev_p:
            safe_actions["ev_p_mw"] = clamped_ev
            modifications.append(f"Clamped EV power to {self.ev_max_p_mw} MW")
            status = "MODIFY"

        # 3. Voltage Stress Intervention
        if v_min < self.v_crit_low:
            # Critical undervoltage: forbid battery charging, throttle EV charging by 50%
            if safe_actions.get("battery_p_mw", 0.0) > 0:
                safe_actions["battery_p_mw"] = 0.0
                modifications.append("EMERGENCY: Forbade BESS charging due to grid undervoltage")
                status = "EMERGENCY"
            cur_ev = safe_actions.get("ev_p_mw", 0.0)
            safe_actions["ev_p_mw"] = cur_ev * 0.5
            modifications.append("EMERGENCY: Throttled EV fleet charging to prevent feeder collapse")
            status = "EMERGENCY"

        if v_max > self.v_crit_high:
            # Critical overvoltage: mandate solar curtailment if not already active
            if safe_actions.get("solar_curtail_mw", 0.0) < 0.5:
                safe_actions["solar_curtail_mw"] = 0.8
                modifications.append("EMERGENCY: Forced solar curtailment to mitigate overvoltage")
                status = "EMERGENCY"

        safe_actions["solar_curtail_mw"] = max(0.0, safe_actions.get("solar_curtail_mw", 0.0))
        safe_actions["load_shift_ratio"] = float(np.clip(load_shift, -0.15, 0.15))

        return safe_actions, status, modifications
