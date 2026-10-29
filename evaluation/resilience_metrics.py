"""Resilience and Comprehensive Evaluation Metrics Engine."""

import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


class ExperimentMetricsAggregator:
    """
    Computes economic, physical, reliability, communication, security,
    and resilience performance degradation metrics across experimental runs.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.steps = 0
        self.total_electricity_cost = 0.0
        self.total_degradation_cost = 0.0
        self.total_grid_import_mwh = 0.0
        self.total_grid_export_mwh = 0.0
        self.total_losses_mwh = 0.0
        self.total_solar_generated_mwh = 0.0
        self.total_unserved_energy_mwh = 0.0
        self.voltage_violation_steps = 0
        self.total_voltage_severity = 0.0
        self.line_overload_steps = 0
        self.total_rewards = 0.0

        self.min_voltage = 1.0
        self.max_voltage = 1.0
        self.max_line_loading = 0.0

        self.trust_trajectories: Dict[str, List[float]] = {}

    def record_step(self, env_state: Dict[str, Any], metrics: Dict[str, Any], reward_dict: Dict[str, float]):
        self.steps += 1
        elec_cost = float(metrics.get("electricity_cost_eur", 0.0))
        self.total_electricity_cost += elec_cost

        deg_cost = float(metrics.get("battery_degradation_cost", 0.0))
        self.total_degradation_cost += deg_cost

        grid_import = float(env_state.get("grid_import_mw", 0.0))
        if grid_import >= 0:
            self.total_grid_import_mwh += grid_import
        else:
            self.total_grid_export_mwh += abs(grid_import)

        self.total_losses_mwh += float(env_state.get("losses_mw", 0.0))
        self.total_solar_generated_mwh += float(env_state.get("solar_available_mw", 0.0))
        self.total_unserved_energy_mwh += float(metrics.get("unserved_energy_mwh", 0.0))

        v_min = float(env_state.get("v_min_pu", 1.0))
        v_max = float(env_state.get("v_max_pu", 1.0))
        self.min_voltage = min(self.min_voltage, v_min)
        self.max_voltage = max(self.max_voltage, v_max)

        line_load = float(env_state.get("max_line_loading_pct", 0.0))
        self.max_line_loading = max(self.max_line_loading, line_load)

        c_eval = metrics.get("constraint_eval", {})
        if c_eval.get("voltage_violation_count", 0) > 0:
            self.voltage_violation_steps += 1
            self.total_voltage_severity += float(c_eval.get("voltage_violation_severity", 0.0))

        if c_eval.get("overloaded_line_count", 0) > 0:
            self.line_overload_steps += 1

        self.total_rewards += float(reward_dict.get("reward", 0.0))

        # Record trust scores
        scores = env_state.get("agent_trust_scores", {})
        for agent, score in scores.items():
            if agent not in self.trust_trajectories:
                self.trust_trajectories[agent] = []
            self.trust_trajectories[agent].append(float(score))

    def compute_summary(self) -> Dict[str, Any]:
        """Returns consolidated key performance indicators (KPIs)."""
        total_cost = self.total_electricity_cost + self.total_degradation_cost
        avg_reward = self.total_rewards / max(1, self.steps)

        return {
            "total_operating_cost_eur": round(total_cost, 2),
            "electricity_cost_eur": round(self.total_electricity_cost, 2),
            "battery_degradation_cost_eur": round(self.total_degradation_cost, 2),
            "grid_import_mwh": round(self.total_grid_import_mwh, 2),
            "grid_export_mwh": round(self.total_grid_export_mwh, 2),
            "solar_generated_mwh": round(self.total_solar_generated_mwh, 2),
            "network_losses_mwh": round(self.total_losses_mwh, 2),
            "unserved_energy_mwh": round(self.total_unserved_energy_mwh, 4),
            "voltage_violation_hours": self.voltage_violation_steps,
            "voltage_violation_rate": round(self.voltage_violation_steps / max(1, self.steps), 4),
            "voltage_severity_integral": round(self.total_voltage_severity, 4),
            "min_voltage_pu": round(self.min_voltage, 4),
            "max_voltage_pu": round(self.max_voltage, 4),
            "max_line_loading_pct": round(self.max_line_loading, 2),
            "cumulative_reward": round(self.total_rewards, 2),
            "average_step_reward": round(avg_reward, 2),
            "simulated_hours": self.steps
        }

    @staticmethod
    def calculate_resilience_degradation(
        baseline_summary: Dict[str, Any],
        attacked_summary: Dict[str, Any],
        metric_key: str = "cumulative_reward"
    ) -> float:
        """
        Calculates performance degradation:
        Degradation = (Performance_normal - Performance_attack) / |Performance_normal|
        """
        val_normal = float(baseline_summary.get(metric_key, 0.0))
        val_attack = float(attacked_summary.get(metric_key, 0.0))
        if abs(val_normal) < 1e-6:
            return 0.0
        return (val_normal - val_attack) / abs(val_normal)
