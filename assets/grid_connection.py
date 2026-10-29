"""Point of Common Coupling (PCC) Grid Connection Asset."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GridConnection:
    """Represents the external transmission substation / PCC (Bus 0)."""

    def __init__(self, pcc_bus: int = 0, max_import_mw: float = 10.0, max_export_mw: float = 5.0):
        self.pcc_bus = pcc_bus
        self.max_import_mw = max_import_mw
        self.max_export_mw = max_export_mw

    def calculate_cost(self, net_import_mw: float, price_eur_mwh: float, dt_hours: float = 1.0) -> float:
        """
        Calculates electricity procurement cost or feed-in revenue.
        net_import_mw > 0: purchasing from grid
        net_import_mw < 0: selling back to grid (subject to feed-in tariff discount, e.g., 0.85)
        """
        energy_mwh = net_import_mw * dt_hours
        if energy_mwh >= 0:
            return energy_mwh * price_eur_mwh
        else:
            # Export revenue (export tariff is 85% of spot wholesale price)
            feed_in_price = max(0.0, price_eur_mwh * 0.85)
            return energy_mwh * feed_in_price  # Returns negative cost (revenue)
