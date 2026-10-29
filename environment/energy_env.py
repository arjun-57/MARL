"""Gymnasium-Compatible Energy Management Environment for IEEE 33-Bus."""

import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces

from grid.network_builder import DERNetworkBuilder
from grid.constraints import GridConstraints
from assets.battery import BatteryStorage
from assets.solar import SolarPV
from assets.ev import EVFleetHub
from assets.grid_connection import GridConnection
from environment.profile_mapper import ProfileMapper
from environment.transition import GridTransitionManager
from environment.reward import EnergyRewardCalculator
from environment.state import EnvironmentState

logger = logging.getLogger(__name__)


class EnergyManagementEnv(gym.Env):
    """
    Standard Reinforcement Learning & Simulation Environment for Resilient Multi-Agent Microgrids.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        dataset_path: str = "data/processed/aligned_energy_data.csv",
        episode_length: int = 168,
        start_step_offset: int = 0,
        random_seed: int = 42
    ):
        super().__init__()
        self.dataset_path = dataset_path
        self.episode_length = episode_length
        self.start_step_offset = start_step_offset
        self.rng = np.random.default_rng(random_seed)

        # Load aligned time-series
        self.df = pd.read_csv(self.dataset_path)
        self.total_dataset_steps = len(self.df)
        logger.info(f"Loaded environment dataset: {self.total_dataset_steps} steps from {dataset_path}")

        # Core physical components
        self.builder = DERNetworkBuilder()
        self.net = self.builder.build_network()
        self.constraints = GridConstraints()
        self.battery = BatteryStorage()
        self.solar = SolarPV(capacity_mw=1.5, bus_id=18)
        self.ev = EVFleetHub(num_chargers=10, charger_rating_kw=50.0, bus_id=24, random_seed=random_seed)
        self.grid_conn = GridConnection(pcc_bus=0)
        self.mapper = ProfileMapper()
        self.reward_calc = EnergyRewardCalculator()

        self.transition_mgr = GridTransitionManager(
            net=self.net,
            battery=self.battery,
            solar=self.solar,
            ev=self.ev,
            grid_conn=self.grid_conn,
            mapper=self.mapper,
            constraints=self.constraints
        )

        # Action space: continuous vector [battery_p_mw (-0.8 to +0.8), ev_p_mw (0 to 0.5), solar_curtail (0 to 1.5)]
        self.action_space = spaces.Box(
            low=np.array([-0.8, 0.0, 0.0], dtype=np.float32),
            high=np.array([0.8, 0.5, 1.5], dtype=np.float32),
            dtype=np.float32
        )

        # Observation space: [price, load_scale, solar, soc, ev_p, v_min, v_max, line_loading, is_safe]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(9,), dtype=np.float32
        )

        self.current_step = 0
        self.current_data_idx = 0
        self.current_state: Optional[EnvironmentState] = None

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Resets environment to starting state of episode."""
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        self.current_step = 0
        max_start = max(0, self.total_dataset_steps - self.episode_length - 1)

        if options and "start_idx" in options:
            self.current_data_idx = options["start_idx"]
        elif self.start_step_offset > 0:
            self.current_data_idx = self.start_step_offset
        else:
            self.current_data_idx = int(self.rng.integers(0, max(1, max_start)))

        self.battery.reset(initial_soc=0.50)
        self.ev.reset()

        # Initial baseline state
        row = self.df.iloc[self.current_data_idx].to_dict()
        timestamp_str = str(row.get("timestamp", self.current_data_idx))

        hour_of_day = int(row.get("hour", 0))
        self.ev.step_arrivals_and_departures(hour_of_day)

        default_action = {"battery_p_mw": 0.0, "ev_p_mw": 0.1, "solar_curtail_mw": 0.0}
        self.current_state, metrics = self.transition_mgr.execute_transition(
            step_idx=0,
            timestamp_str=timestamp_str,
            data_row=row,
            control_action=default_action
        )

        obs = self.current_state.to_observation_vector()
        info = {"state": self.current_state.to_dict(), "metrics": metrics}
        return obs, info

    def step(
        self,
        action: Any,
        physical_modifier: Optional[Any] = None
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Executes one simulation timestep with optional physical fault modifier."""
        self.current_step += 1
        self.current_data_idx += 1

        if isinstance(action, (list, np.ndarray)):
            action_dict = {
                "battery_p_mw": float(action[0]),
                "ev_p_mw": float(action[1]),
                "solar_curtail_mw": float(action[2]) if len(action) > 2 else 0.0
            }
        elif isinstance(action, dict):
            action_dict = action
        else:
            action_dict = {}

        row = self.df.iloc[self.current_data_idx].to_dict()
        if physical_modifier is not None:
            row = physical_modifier(row, self.current_step)

        timestamp_str = str(row.get("timestamp", self.current_data_idx))
        hour_of_day = int(row.get("hour", 0))
        self.ev.step_arrivals_and_departures(hour_of_day)

        self.current_state, metrics = self.transition_mgr.execute_transition(
            step_idx=self.current_step,
            timestamp_str=timestamp_str,
            data_row=row,
            control_action=action_dict
        )

        reward_dict = self.reward_calc.compute_reward(
            electricity_cost_eur=metrics["electricity_cost_eur"],
            unserved_energy_mwh=metrics["unserved_energy_mwh"],
            constraint_violations=metrics["constraint_eval"],
            battery_degradation_cost=metrics["battery_degradation_cost"],
            solar_utilized_mw=metrics["solar_utilized_mw"]
        )

        terminated = bool(self.current_step >= self.episode_length)
        truncated = bool(self.current_data_idx >= self.total_dataset_steps - 1)

        obs = self.current_state.to_observation_vector()
        info = {
            "state": self.current_state.to_dict(),
            "metrics": metrics,
            "reward_breakdown": reward_dict
        }

        return obs, reward_dict["reward"], terminated, truncated, info
