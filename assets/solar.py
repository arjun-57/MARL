"""Solar Photovoltaic (PV) Generation Asset Model."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SolarPV:
    """Represents a solar photovoltaic generation plant with curtailment support."""

    def __init__(self, capacity_mw: float = 1.5, bus_id: int = 18):
        self.capacity_mw = capacity_mw
        self.bus_id = bus_id
        self.current_generation_mw = 0.0
        self.curtailed_mw = 0.0

    def calculate_generation(self, normalized_solar_profile: float, curtailment_mw: float = 0.0) -> float:
        """
        Calculates active generation based on normalized solar profile.
        P_solar = capacity_mw * profile - curtailment
        """
        raw_available_mw = self.capacity_mw * max(0.0, float(normalized_solar_profile))
        curtailment = max(0.0, min(curtailment_mw, raw_available_mw))
        self.current_generation_mw = max(0.0, raw_available_mw - curtailment)
        self.curtailed_mw = curtailment
        return self.current_generation_mw

    def get_state(self) -> Dict[str, Any]:
        """Returns PV telemetry."""
        return {
            "capacity_mw": self.capacity_mw,
            "bus_id": self.bus_id,
            "generation_mw": self.current_generation_mw,
            "curtailed_mw": self.curtailed_mw
        }
