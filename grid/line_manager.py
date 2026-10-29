"""Line Manager for monitoring branch status and line contingencies."""

import logging
import pandapower as pp
import pandas as pd

logger = logging.getLogger(__name__)


class LineManager:
    """Manages transmission/distribution line parameters, statuses, and ratings."""

    def __init__(self, net: pp.pandapowerNet):
        self.net = net

    def get_overloaded_lines(self, threshold_pct: float = 100.0) -> pd.DataFrame:
        """Returns lines currently exceeding thermal capacity."""
        if "loading_percent" not in self.net.res_line:
            return pd.DataFrame()
        return self.net.res_line[self.net.res_line["loading_percent"] > threshold_pct]

    def set_line_status(self, line_idx: int, in_service: bool):
        """Simulate line trip or switching operation."""
        if line_idx in self.net.line.index:
            self.net.line.at[line_idx, "in_service"] = in_service
