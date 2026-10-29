"""Power Flow Execution Engine wrapping pandapower AC Power Flow."""

import logging
from typing import Dict, Any
import pandapower as pp

logger = logging.getLogger(__name__)


class PowerFlowEngine:
    """Executes AC power flow and extracts physical grid state metrics."""

    @staticmethod
    def run_power_flow(net: pp.pandapowerNet) -> Dict[str, Any]:
        """Runs AC power flow with convergence handling and telemetry extraction."""
        converged = False
        try:
            pp.runpp(
                net,
                algorithm="nr",
                enforce_q_lims=False,
                calculate_voltage_angles=True,
                max_iteration=30,
                tolerance_mva=1e-5,
                numba=False
            )
            converged = bool(net["converged"])
        except Exception as e:
            logger.warning(f"Standard NR power flow failed: {e}. Trying robust Newton-Raphson with flat start...")
            try:
                pp.runpp(net, algorithm="bfsw", max_iteration=50)
                converged = bool(net["converged"])
            except Exception as e2:
                logger.error(f"Power flow failed to converge: {e2}")
                converged = False

        if not converged:
            return {
                "converged": False,
                "v_min_pu": 0.0,
                "v_max_pu": 0.0,
                "v_mean_pu": 0.0,
                "min_v_bus": -1,
                "max_line_loading_pct": 999.0,
                "total_loss_mw": 0.0,
                "grid_import_mw": 999.0,
                "bus_voltages": {},
                "line_loadings": {}
            }

        # Extract telemetry
        vm_pu = net.res_bus["vm_pu"]
        v_min = float(vm_pu.min())
        v_max = float(vm_pu.max())
        v_mean = float(vm_pu.mean())
        min_v_bus = int(vm_pu.idxmin())

        line_loading = net.res_line["loading_percent"]
        max_loading = float(line_loading.max()) if len(line_loading) > 0 else 0.0

        total_loss_mw = float(net.res_line["pl_mw"].sum()) if "pl_mw" in net.res_line else 0.0
        grid_import_mw = float(net.res_ext_grid["p_mw"].sum()) if len(net.res_ext_grid) > 0 else 0.0

        return {
            "converged": True,
            "v_min_pu": v_min,
            "v_max_pu": v_max,
            "v_mean_pu": v_mean,
            "min_v_bus": min_v_bus,
            "max_line_loading_pct": max_loading,
            "total_loss_mw": total_loss_mw,
            "grid_import_mw": grid_import_mw,
            "bus_voltages": vm_pu.to_dict(),
            "line_loadings": line_loading.to_dict()
        }
