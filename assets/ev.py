"""Electric Vehicle (EV) Charging Hub and Flexible Fleet Model."""

import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


class EVFleetHub:
    """Simulates an EV charging hub with stochastic arrivals, departures, and flexibility."""

    def __init__(
        self,
        num_chargers: int = 10,
        charger_rating_kw: float = 50.0,
        battery_capacity_kwh: float = 60.0,
        bus_id: int = 24,
        random_seed: int = 42
    ):
        self.num_chargers = num_chargers
        self.charger_rating_mw = (charger_rating_kw * num_chargers) / 1000.0  # e.g., 0.5 MW total
        self.charger_unit_mw = charger_rating_kw / 1000.0
        self.battery_capacity_mwh = battery_capacity_kwh / 1000.0
        self.bus_id = bus_id
        self.rng = np.random.default_rng(random_seed)

        # Vehicles currently connected: list of dicts {id, arrival_h, departure_h, soc, target_soc}
        self.connected_evs: List[Dict[str, Any]] = []
        self.current_charging_p_mw = 0.0

    def reset(self):
        """Resets the fleet state."""
        self.connected_evs = []
        self.current_charging_p_mw = 0.0

    def step_arrivals_and_departures(self, hour_of_day: int):
        """Simulate realistic diurnal arrival patterns (morning commute / evening return)."""
        # Remove departing vehicles
        self.connected_evs = [ev for ev in self.connected_evs if ev["departure_h"] > hour_of_day]

        # Inflow probability peaks at morning (08:00 - 10:00) and evening (17:00 - 19:00)
        p_arrive = 0.6 if (8 <= hour_of_day <= 10 or 17 <= hour_of_day <= 19) else 0.2
        num_new = self.rng.binomial(n=max(0, self.num_chargers - len(self.connected_evs)), p=p_arrive)

        for i in range(num_new):
            initial_soc = float(self.rng.uniform(0.2, 0.5))
            parking_duration = int(self.rng.integers(3, 8))
            self.connected_evs.append({
                "id": f"ev_{hour_of_day}_{len(self.connected_evs)}",
                "arrival_h": hour_of_day,
                "departure_h": min(23, hour_of_day + parking_duration),
                "soc": initial_soc,
                "target_soc": 0.85
            })

    def calculate_consumption(self, requested_p_mw: float, dt_hours: float = 1.0) -> float:
        """Applies requested charging power across connected EVs and updates SOC."""
        if not self.connected_evs:
            self.current_charging_p_mw = 0.0
            return 0.0

        max_absorbable_mw = len(self.connected_evs) * self.charger_unit_mw
        actual_power = max(0.0, min(requested_p_mw, max_absorbable_mw))

        # Distribute power equally among connected cars needing charge
        needing_charge = [ev for ev in self.connected_evs if ev["soc"] < ev["target_soc"]]
        if needing_charge and actual_power > 0:
            power_per_ev = actual_power / len(needing_charge)
            for ev in needing_charge:
                delta_soc = (power_per_ev * dt_hours) / self.battery_capacity_mwh
                ev["soc"] = min(ev["target_soc"], ev["soc"] + delta_soc)

        self.current_charging_p_mw = actual_power
        return self.current_charging_p_mw

    def get_state(self) -> Dict[str, Any]:
        """Returns fleet occupancy and energy requirements."""
        total_evs = len(self.connected_evs)
        avg_soc = float(np.mean([ev["soc"] for ev in self.connected_evs])) if total_evs > 0 else 0.0
        return {
            "bus_id": self.bus_id,
            "connected_evs": total_evs,
            "num_chargers": self.num_chargers,
            "current_power_mw": self.current_charging_p_mw,
            "max_available_power_mw": total_evs * self.charger_unit_mw,
            "average_soc": avg_soc
        }
