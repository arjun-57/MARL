"""Physical event and physical disruption attacks."""

import logging
from typing import Dict, Any
from copy import deepcopy

from attacks.base_attack import BaseAttack
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class DemandSpikeAttack(BaseAttack):
    """Simulates a coordinated physical demand surge / cyber-induced industrial load spike."""

    def __init__(self, spike_factor: float = 1.80, start_step: int = 36, end_step: int = 42):
        super().__init__(name="DemandSpikeAttack", start_step=start_step, end_step=end_step)
        self.spike_factor = spike_factor

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        pass

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        if not self.is_triggered(current_step):
            return data_row
        row = deepcopy(data_row)
        orig_load = row["germany_load_mw"]
        row["germany_load_mw"] = orig_load * self.spike_factor
        logger.warning(f"[ATTACK] Demand spike triggered: {orig_load:.1f} MW -> {row['germany_load_mw']:.1f} MW")
        return row


class SolarDropAttack(BaseAttack):
    """Simulates sudden inverter tripping or severe localized storm drop."""

    def __init__(self, drop_factor: float = 0.05, start_step: int = 50, end_step: int = 56):
        super().__init__(name="SolarDropAttack", start_step=start_step, end_step=end_step)
        self.drop_factor = drop_factor

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        pass

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        if not self.is_triggered(current_step):
            return data_row
        row = deepcopy(data_row)
        row["normalized_solar_profile"] *= self.drop_factor
        logger.warning(f"[ATTACK] Solar generation dropped to {self.drop_factor * 100:.1f}%")
        return row
