"""State definitions and telemetry container for Energy Management System."""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import numpy as np


@dataclass
class EnvironmentState:
    """Holds comprehensive physical and cyber state snapshot at timestep t."""
    step: int
    timestamp: str
    price_eur_mwh: float
    load_mw: float
    load_scale_factor: float
    solar_available_mw: float
    battery_soc: float
    battery_power_mw: float
    ev_power_mw: float
    ev_connected_count: int
    grid_import_mw: float
    losses_mw: float
    v_min_pu: float
    v_max_pu: float
    max_line_loading_pct: float
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    agent_trust_scores: Dict[str, float] = field(default_factory=dict)
    active_attacks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to serializable dictionary."""
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "price_eur_mwh": float(self.price_eur_mwh),
            "load_mw": float(self.load_mw),
            "load_scale_factor": float(self.load_scale_factor),
            "solar_available_mw": float(self.solar_available_mw),
            "battery_soc": float(self.battery_soc),
            "battery_power_mw": float(self.battery_power_mw),
            "ev_power_mw": float(self.ev_power_mw),
            "ev_connected_count": int(self.ev_connected_count),
            "grid_import_mw": float(self.grid_import_mw),
            "losses_mw": float(self.losses_mw),
            "v_min_pu": float(self.v_min_pu),
            "v_max_pu": float(self.v_max_pu),
            "max_line_loading_pct": float(self.max_line_loading_pct),
            "is_safe": bool(self.is_safe),
            "violations": self.violations,
            "agent_trust_scores": self.agent_trust_scores,
            "active_attacks": self.active_attacks,
        }

    def to_observation_vector(self) -> np.ndarray:
        """Converts state to flat normalized vector for RL agent consumption."""
        return np.array([
            np.clip(self.price_eur_mwh / 100.0, -1.0, 5.0),
            np.clip(self.load_scale_factor, 0.0, 2.0),
            np.clip(self.solar_available_mw / 1.5, 0.0, 1.0),
            np.clip(self.battery_soc, 0.0, 1.0),
            np.clip(self.ev_power_mw / 0.5, 0.0, 1.0),
            np.clip(self.v_min_pu, 0.8, 1.2),
            np.clip(self.v_max_pu, 0.8, 1.2),
            np.clip(self.max_line_loading_pct / 100.0, 0.0, 2.0),
            1.0 if self.is_safe else 0.0
        ], dtype=np.float32)
