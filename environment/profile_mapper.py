"""Profile Mapper translating bulk national figures into realistic IEEE 33-Bus feeder quantities."""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ProfileMapper:
    """
    Translates real-world bulk German time-series (OPSD and Ember)
    into localized electrical variables for the IEEE 33-bus distribution system.
    
    Formula:
    L_{bus, i, t} = L_{bus, i}^{base} * (L_t^{Germany} / L_{reference}^{Germany})
    PV_{out, t} = PV_{capacity} * SolarProfile_t
    """

    def __init__(
        self,
        reference_load_mw: float = 75000.0,
        solar_capacity_mw: float = 1.5
    ):
        self.reference_load_mw = reference_load_mw
        self.solar_capacity_mw = solar_capacity_mw

    def get_load_scale_factor(self, germany_load_mw: float) -> float:
        """Computes ratio L_t / L_ref clipped to physically sensible feeder ranges (0.4 to 1.8)."""
        scale = germany_load_mw / self.reference_load_mw
        return float(np.clip(scale, 0.35, 1.85))

    def get_solar_generation(self, normalized_solar_profile: float) -> float:
        """Computes PV power injection at bus in MW."""
        return float(np.clip(self.solar_capacity_mw * normalized_solar_profile, 0.0, self.solar_capacity_mw))
