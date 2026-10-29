"""IEEE 33-Bus Radial Distribution Network Builder using pandapower."""

import logging
import pandapower as pp
import pandapower.networks as pn

logger = logging.getLogger(__name__)


class IEEE33Network:
    """Manages the standard Baran & Wu 33-bus radial distribution network."""

    def __init__(self):
        self.net = pn.case33bw()
        self._cache_base_values()

    def _cache_base_values(self):
        """Cache baseline bus loads and topology for normalized profile scaling."""
        self.base_loads = self.net.load[["bus", "p_mw", "q_mvar"]].copy()
        self.total_base_load_mw = float(self.net.load["p_mw"].sum())
        self.total_base_load_mvar = float(self.net.load["q_mvar"].sum())
        self.num_buses = len(self.net.bus)
        self.num_lines = len(self.net.line)
        logger.info(
            f"IEEE 33-Bus initialized: {self.num_buses} buses, {self.num_lines} lines, "
            f"Total base active load: {self.total_base_load_mw:.3f} MW"
        )

    def get_base_network(self) -> pp.pandapowerNet:
        """Returns a deep copy of the pristine 33-bus network."""
        return pn.case33bw()
