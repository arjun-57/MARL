"""Multi-Objective Reward Function for Power Grid Operations and Resilience."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EnergyRewardCalculator:
    """
    Computes economic and physical penalty reward:
    R_t = - C_t - lambda_1 * U_t - lambda_2 * V_t - lambda_3 * D_t + lambda_4 * R_t^{RE} - lambda_5 * O_t
    
    Where:
    C_t : Electricity procurement cost (EUR)
    U_t : Unserved energy penalty (EUR/MWh)
    V_t : Voltage and line constraint violation penalty
    D_t : Battery degradation cost (EUR)
    R_t^{RE} : Renewable solar self-consumption bonus
    O_t : Operational / switching overhead penalty
    """

    def __init__(
        self,
        lambda_unserved: float = 200.0,
        lambda_violation: float = 150.0,
        lambda_degradation: float = 1.0,
        lambda_renewable: float = 20.0,
        lambda_overhead: float = 5.0
    ):
        self.lambda_unserved = lambda_unserved
        self.lambda_violation = lambda_violation
        self.lambda_degradation = lambda_degradation
        self.lambda_renewable = lambda_renewable
        self.lambda_overhead = lambda_overhead

    def compute_reward(
        self,
        electricity_cost_eur: float,
        unserved_energy_mwh: float,
        constraint_violations: Dict[str, Any],
        battery_degradation_cost: float,
        solar_utilized_mw: float,
        action_overhead: float = 0.0
    ) -> Dict[str, float]:
        """Calculates scalar reward and decomposed components for logging."""
        c_cost = float(electricity_cost_eur)
        u_unserved = float(unserved_energy_mwh) * self.lambda_unserved

        v_severity = float(constraint_violations.get("voltage_violation_severity", 0.0))
        l_overload = float(constraint_violations.get("max_line_overload", 0.0)) / 100.0
        v_penalty = (v_severity + l_overload) * self.lambda_violation

        d_degradation = float(battery_degradation_cost) * self.lambda_degradation
        re_bonus = float(solar_utilized_mw) * self.lambda_renewable
        o_overhead = float(action_overhead) * self.lambda_overhead

        total_reward = - c_cost - u_unserved - v_penalty - d_degradation + re_bonus - o_overhead

        return {
            "reward": float(total_reward),
            "electricity_cost": c_cost,
            "unserved_penalty": u_unserved,
            "violation_penalty": v_penalty,
            "degradation_cost": d_degradation,
            "renewable_bonus": re_bonus,
            "overhead_penalty": o_overhead
        }
