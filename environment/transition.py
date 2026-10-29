"""State transition manager executing physical updates and power flow."""

import logging
from typing import Dict, Any, Tuple
import pandapower as pp
import numpy as np

from grid.bus_manager import BusManager
from grid.power_flow import PowerFlowEngine
from grid.constraints import GridConstraints
from assets.battery import BatteryStorage
from assets.solar import SolarPV
from assets.ev import EVFleetHub
from assets.grid_connection import GridConnection
from environment.profile_mapper import ProfileMapper
from environment.state import EnvironmentState

logger = logging.getLogger(__name__)


class GridTransitionManager:
    """Executes atomic timestep state transitions on the cyber-physical grid."""

    def __init__(
        self,
        net: pp.pandapowerNet,
        battery: BatteryStorage,
        solar: SolarPV,
        ev: EVFleetHub,
        grid_conn: GridConnection,
        mapper: ProfileMapper,
        constraints: GridConstraints
    ):
        self.net = net
        self.battery = battery
        self.solar = solar
        self.ev = ev
        self.grid_conn = grid_conn
        self.mapper = mapper
        self.constraints = constraints
        self.bus_mgr = BusManager(net)

    def execute_transition(
        self,
        step_idx: int,
        timestamp_str: str,
        data_row: Dict[str, Any],
        control_action: Dict[str, Any],
        trust_scores: Dict[str, float] = None,
        active_attacks: list = None
    ) -> Tuple[EnvironmentState, Dict[str, Any]]:
        """
        Applies control action to physical assets, runs AC power flow, and computes telemetry.
        """
        germany_load_mw = float(data_row["germany_load_mw"])
        solar_profile = float(data_row["normalized_solar_profile"])
        price_eur_mwh = float(data_row["price_eur_mwh"])

        # 1. Update load profile on all buses
        load_scale = self.mapper.get_load_scale_factor(germany_load_mw)
        # Check if demand agent shifted load
        load_shift_ratio = float(control_action.get("load_shift_ratio", 0.0))
        effective_load_scale = load_scale * (1.0 + load_shift_ratio)
        self.bus_mgr.scale_all_loads(effective_load_scale)

        # 2. Update solar PV generation
        solar_curtail_mw = float(control_action.get("solar_curtail_mw", 0.0))
        available_solar = self.solar.calculate_generation(solar_profile, curtailment_mw=solar_curtail_mw)
        self.bus_mgr.set_solar_generation(available_solar)

        # 3. Update battery storage injection
        requested_bess_p = float(control_action.get("battery_p_mw", 0.0))
        actual_bess_p, new_soc, deg_cost = self.battery.step(requested_bess_p, dt_hours=1.0)
        self.bus_mgr.set_battery_power(actual_bess_p)

        # 4. Update EV fleet hub
        requested_ev_p = float(control_action.get("ev_p_mw", 0.2))
        actual_ev_p = self.ev.calculate_consumption(requested_ev_p, dt_hours=1.0)
        self.bus_mgr.set_ev_charging_power(actual_ev_p)

        # 5. Run AC Power Flow
        pf_results = PowerFlowEngine.run_power_flow(self.net)
        constraint_eval = self.constraints.evaluate(pf_results)

        # 6. Economics: Grid import/export cost
        grid_import_mw = pf_results["grid_import_mw"]
        elec_cost = self.grid_conn.calculate_cost(grid_import_mw, price_eur_mwh, dt_hours=1.0)

        # Unserved energy if non-converged or extreme undervoltage
        unserved_energy_mwh = 0.0
        if not pf_results["converged"]:
            unserved_energy_mwh = germany_load_mw * 0.0001  # Feeder blackout equivalent

        env_state = EnvironmentState(
            step=step_idx,
            timestamp=timestamp_str,
            price_eur_mwh=price_eur_mwh,
            load_mw=germany_load_mw,
            load_scale_factor=effective_load_scale,
            solar_available_mw=available_solar,
            battery_soc=new_soc,
            battery_power_mw=actual_bess_p,
            ev_power_mw=actual_ev_p,
            ev_connected_count=len(self.ev.connected_evs),
            grid_import_mw=grid_import_mw,
            losses_mw=pf_results["total_loss_mw"],
            v_min_pu=pf_results["v_min_pu"],
            v_max_pu=pf_results["v_max_pu"],
            max_line_loading_pct=pf_results["max_line_loading_pct"],
            is_safe=constraint_eval["safe"],
            violations=constraint_eval["details"],
            agent_trust_scores=trust_scores or {},
            active_attacks=active_attacks or []
        )

        metrics = {
            "electricity_cost_eur": elec_cost,
            "unserved_energy_mwh": unserved_energy_mwh,
            "battery_degradation_cost": deg_cost,
            "solar_utilized_mw": available_solar,
            "constraint_eval": constraint_eval,
            "pf_results": pf_results
        }

        return env_state, metrics
