"""Bus Manager for dynamically setting bus injections and extractions."""

import logging
import pandapower as pp
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BusManager:
    """Manages load, generation, and storage bus injections in the pandapower network."""

    def __init__(self, net: pp.pandapowerNet):
        self.net = net
        # Map original bus loads
        self.base_p_loads = self.net.load["p_mw"].copy()
        self.base_q_loads = self.net.load["q_mvar"].copy()

    def scale_all_loads(self, scale_factor: float):
        """Scales all standard bus active and reactive loads by a time-varying factor."""
        # Scale active power
        self.net.load["p_mw"] = self.base_p_loads * scale_factor
        # Scale reactive power maintaining original power factor
        self.net.load["q_mvar"] = self.base_q_loads * scale_factor

    def set_solar_generation(self, solar_p_mw: float, solar_idx: int = 0):
        """Sets active generation from PV at specified sgen element."""
        if solar_idx in self.net.sgen.index:
            self.net.sgen.at[solar_idx, "p_mw"] = max(0.0, float(solar_p_mw))

    def set_battery_power(self, p_mw: float, battery_idx: int = 0):
        """Sets BESS active power. p_mw > 0 = charging (load), p_mw < 0 = discharging (generator)."""
        if battery_idx in self.net.storage.index:
            self.net.storage.at[battery_idx, "p_mw"] = float(p_mw)

    def set_ev_charging_power(self, p_mw: float, ev_load_idx: int = 0):
        """Sets EV fleet active consumption (p_mw >= 0)."""
        # Find EV load by name or index
        ev_matches = self.net.load[self.net.load["name"] == "EV_Hub_Agent_24"]
        if not ev_matches.empty:
            idx = ev_matches.index[0]
            self.net.load.at[idx, "p_mw"] = max(0.0, float(p_mw))
        elif ev_load_idx in self.net.load.index:
            self.net.load.at[ev_load_idx, "p_mw"] = max(0.0, float(p_mw))
