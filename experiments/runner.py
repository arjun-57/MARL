"""Experiment Execution Engine running comparative benchmarks and attack scenarios."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from environment.energy_env import EnergyManagementEnv
from communication.message_bus import SimulatedMessageBus
from coordination.centralized_controller import CentralizedRuleController
from coordination.independent_controller import IndependentMASController
from coordination.multi_agent_controller import ResilientMASController
from evaluation.resilience_metrics import ExperimentMetricsAggregator
from attacks.false_data import FalseDataInjectionAttack
from attacks.communication_delay import CommunicationDelayAttack, PacketLossAttack, AgentFailureAttack, CombinedAttack
from attacks.demand_spike import DemandSpikeAttack, SolarDropAttack

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class ExperimentRunner:
    """Orchestrates experimental simulations across controllers and attack scenarios."""

    def __init__(
        self,
        dataset_path: str = "data/processed/aligned_energy_data.csv",
        output_dir: str = "results",
        default_episode_length: int = 168,
        random_seed: int = 42
    ):
        self.dataset_path = dataset_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.episode_length = default_episode_length
        self.random_seed = random_seed

    def run_scenario(
        self,
        controller_type: str,
        attack_scenario: Optional[str] = None,
        episode_length: Optional[int] = None,
        start_idx: int = 1000
    ) -> Dict[str, Any]:
        """
        Runs a single experiment scenario.
        
        controller_type: 'centralized', 'independent', 'coordinated', 'resilient'
        attack_scenario: None, 'false_data', 'communication_delay', 'packet_loss', 'agent_failure', 'combined'
        """
        ep_len = episode_length or self.episode_length
        env = EnergyManagementEnv(
            dataset_path=self.dataset_path,
            episode_length=ep_len,
            start_step_offset=start_idx,
            random_seed=self.random_seed
        )

        bus = SimulatedMessageBus(random_seed=self.random_seed)
        aggregator = ExperimentMetricsAggregator()

        # Instantiate controller
        if controller_type == "centralized":
            controller = CentralizedRuleController()
        elif controller_type == "independent":
            controller = IndependentMASController(bus=bus)
        elif controller_type == "coordinated":
            controller = ResilientMASController(bus=bus, enable_resilience=False)
        elif controller_type == "resilient":
            controller = ResilientMASController(bus=bus, enable_resilience=True)
        else:
            raise ValueError(f"Unknown controller type: {controller_type}")

        # Instantiate attack
        attack = None
        if attack_scenario == "false_data":
            attack = FalseDataInjectionAttack(start_step=24, end_step=72)
        elif attack_scenario == "communication_delay":
            attack = CommunicationDelayAttack(delay_steps=2, start_step=20, end_step=60)
        elif attack_scenario == "packet_loss":
            attack = PacketLossAttack(drop_probability=0.35, start_step=20, end_step=60)
        elif attack_scenario == "agent_failure":
            attack = AgentFailureAttack(target_agent="battery_agent", start_step=30, end_step=70)
        elif attack_scenario == "combined":
            attack = CombinedAttack(start_step=24, end_step=72)
        elif attack_scenario == "demand_spike":
            attack = DemandSpikeAttack(spike_factor=1.8, start_step=36, end_step=42)
        elif attack_scenario == "solar_drop":
            attack = SolarDropAttack(drop_factor=0.05, start_step=50, end_step=56)

        obs, info = env.reset(seed=self.random_seed, options={"start_idx": start_idx})
        current_state_dict = info["state"]

        trajectory = []

        for step in range(ep_len):
            # Apply cyber attack to message bus if active
            bus.clear_interceptors()
            if attack:
                attack.apply_cyber(bus, current_step=step)

            # Determine control actions
            audit_info = {}
            observed_state = dict(current_state_dict)
            if attack and attack_scenario == "false_data" and attack.is_triggered(step):
                # SCADA / sensor readings received over the network are tampered by FDI
                observed_state["solar_available_mw"] = observed_state.get("solar_available_mw", 0.0) + getattr(attack, "bias_mw", 2.0)

            if controller_type == "centralized":
                action = controller.compute_action(observed_state)
            elif controller_type == "independent":
                action = controller.step(current_step=step, env_state=observed_state)
            else:  # 'coordinated' or 'resilient'
                action, audit_info = controller.step(current_step=step, env_state=current_state_dict)

            # Step environment with physical attack modifier if present
            phys_mod = attack.apply_physical if attack else None
            obs, reward, terminated, truncated, step_info = env.step(action, physical_modifier=phys_mod)
            current_state_dict = step_info["state"]
            metrics = step_info["metrics"]
            r_breakdown = step_info["reward_breakdown"]

            # Record step in metrics
            aggregator.record_step(current_state_dict, metrics, r_breakdown)

            step_record = {
                "step": step,
                "timestamp": current_state_dict["timestamp"],
                "price": current_state_dict["price_eur_mwh"],
                "load_mw": current_state_dict["load_mw"],
                "solar_mw": current_state_dict["solar_available_mw"],
                "soc": current_state_dict["battery_soc"],
                "battery_p_mw": current_state_dict["battery_power_mw"],
                "ev_p_mw": current_state_dict["ev_power_mw"],
                "grid_import_mw": current_state_dict["grid_import_mw"],
                "v_min_pu": current_state_dict["v_min_pu"],
                "v_max_pu": current_state_dict["v_max_pu"],
                "line_loading_pct": current_state_dict["max_line_loading_pct"],
                "reward": reward,
                "trust_scores": current_state_dict.get("agent_trust_scores", {})
            }
            trajectory.append(step_record)

            if terminated or truncated:
                break

        summary = aggregator.compute_summary()
        summary["controller"] = controller_type
        summary["attack_scenario"] = attack_scenario or "none"

        # Save trajectory and summary
        run_id = f"{controller_type}_{attack_scenario or 'normal'}"
        traj_df = pd.DataFrame(trajectory)
        traj_df.to_csv(self.output_dir / f"traj_{run_id}.csv", index=False)

        with open(self.output_dir / f"summary_{run_id}.json", "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(
            f"Completed Scenario [{run_id}]: Total Cost={summary['total_operating_cost_eur']} EUR, "
            f"V-Violations={summary['voltage_violation_hours']}h, Reward={summary['cumulative_reward']}"
        )

        return {"summary": summary, "trajectory": traj_df}

    def run_benchmark_matrix(self, attack_scenario: str = "false_data", episode_length: int = 168) -> pd.DataFrame:
        """
        Runs all 4 controllers under a given attack and compares degradation.
        """
        controllers = ["centralized", "independent", "coordinated", "resilient"]
        results = []

        # 1. Normal baseline
        normal_summaries = {}
        for c in controllers:
            res_norm = self.run_scenario(controller_type=c, attack_scenario=None, episode_length=episode_length)
            normal_summaries[c] = res_norm["summary"]

        # 2. Under attack
        for c in controllers:
            res_att = self.run_scenario(controller_type=c, attack_scenario=attack_scenario, episode_length=episode_length)
            att_summary = res_att["summary"]

            # Compute degradation
            deg_reward = ExperimentMetricsAggregator.calculate_resilience_degradation(
                normal_summaries[c], att_summary, metric_key="cumulative_reward"
            )

            res_row = {
                "Controller": c,
                "Normal_Cost_EUR": normal_summaries[c]["total_operating_cost_eur"],
                "Attack_Cost_EUR": att_summary["total_operating_cost_eur"],
                "Normal_Violations_h": normal_summaries[c]["voltage_violation_hours"],
                "Attack_Violations_h": att_summary["voltage_violation_hours"],
                "Normal_Reward": normal_summaries[c]["cumulative_reward"],
                "Attack_Reward": att_summary["cumulative_reward"],
                "Performance_Degradation": round(deg_reward, 4)
            }
            results.append(res_row)

        df_bench = pd.DataFrame(results)
        df_bench.to_csv(self.output_dir / f"benchmark_matrix_{attack_scenario}.csv", index=False)
        logger.info(f"\n=== Benchmark Matrix under {attack_scenario} ===\n{df_bench.to_string()}")
        return df_bench


if __name__ == "__main__":
    runner = ExperimentRunner(default_episode_length=72)
    runner.run_benchmark_matrix(attack_scenario="false_data", episode_length=72)
