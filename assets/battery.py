"""Battery Energy Storage System (BESS) Physical Model."""

import logging
from typing import Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class BatteryStorage:
    """Simulates electrochemical battery dynamics, SOC state transitions, and degradation."""

    def __init__(
        self,
        capacity_mwh: float = 2.0,
        initial_soc: float = 0.50,
        soc_min: float = 0.10,
        soc_max: float = 0.95,
        max_charge_mw: float = 0.8,
        max_discharge_mw: float = 0.8,
        charge_efficiency: float = 0.95,
        discharge_efficiency: float = 0.95,
        degradation_cost_per_mwh: float = 25.0
    ):
        self.capacity_mwh = capacity_mwh
        self.soc = initial_soc
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.max_charge_mw = max_charge_mw
        self.max_discharge_mw = max_discharge_mw
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.degradation_cost_per_mwh = degradation_cost_per_mwh

        self.total_energy_cycled_mwh = 0.0

    def reset(self, initial_soc: float = 0.50):
        """Resets battery to initial state."""
        self.soc = np.clip(initial_soc, self.soc_min, self.soc_max)
        self.total_energy_cycled_mwh = 0.0

    def step(self, requested_p_mw: float, dt_hours: float = 1.0) -> Tuple[float, float, float]:
        """
        Executes battery charging or discharging for dt_hours.

        Parameters
        ----------
        requested_p_mw : float
            Positive (+) = Charging (consuming power from grid/solar)
            Negative (-) = Discharging (injecting power into grid)
        dt_hours : float
            Timestep duration in hours.

        Returns
        -------
        Tuple[actual_p_mw, new_soc, degradation_cost]
        """
        if requested_p_mw > 0:
            # Charging logic
            p_charge = min(requested_p_mw, self.max_charge_mw)
            # Max power that can be absorbed before hitting soc_max
            max_p_by_soc = ((self.soc_max - self.soc) * self.capacity_mwh) / (self.charge_efficiency * dt_hours)
            actual_p = max(0.0, min(p_charge, max_p_by_soc))

            delta_soc = (actual_p * dt_hours * self.charge_efficiency) / self.capacity_mwh
            self.soc = float(np.clip(self.soc + delta_soc, self.soc_min, self.soc_max))
            cycled_mwh = actual_p * dt_hours

        elif requested_p_mw < 0:
            # Discharging logic
            p_discharge = min(abs(requested_p_mw), self.max_discharge_mw)
            # Max power that can be delivered before hitting soc_min
            max_p_by_soc = ((self.soc - self.soc_min) * self.capacity_mwh * self.discharge_efficiency) / dt_hours
            actual_discharge = max(0.0, min(p_discharge, max_p_by_soc))
            actual_p = -actual_discharge

            delta_soc = (actual_discharge * dt_hours) / (self.discharge_efficiency * self.capacity_mwh)
            self.soc = float(np.clip(self.soc - delta_soc, self.soc_min, self.soc_max))
            cycled_mwh = actual_discharge * dt_hours

        else:
            actual_p = 0.0
            cycled_mwh = 0.0

        self.total_energy_cycled_mwh += cycled_mwh
        degradation_cost = cycled_mwh * self.degradation_cost_per_mwh

        return actual_p, self.soc, degradation_cost

    def get_state(self) -> Dict[str, Any]:
        """Returns current battery telemetry."""
        return {
            "soc": self.soc,
            "capacity_mwh": self.capacity_mwh,
            "soc_min": self.soc_min,
            "soc_max": self.soc_max,
            "max_charge_mw": self.max_charge_mw,
            "max_discharge_mw": self.max_discharge_mw,
            "total_cycled_mwh": self.total_energy_cycled_mwh
        }
