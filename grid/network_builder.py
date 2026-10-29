"""Instrument IEEE 33-Bus with DERs: Solar PV, Battery Storage, and EV Fleet Hub."""

import logging
import pandapower as pp
import pandapower.networks as pn

logger = logging.getLogger(__name__)


class DERNetworkBuilder:
    """Configures the IEEE 33-bus system with Solar PV, Battery (BESS), and EV Charging."""

    def __init__(
        self,
        solar_bus: int = 18,
        solar_capacity_mw: float = 1.5,
        battery_bus: int = 14,
        battery_capacity_mwh: float = 2.0,
        battery_max_p_mw: float = 0.8,
        ev_bus: int = 24,
        ev_max_p_mw: float = 0.5,
        slack_vm_pu: float = 1.035,
    ):
        self.solar_bus = solar_bus
        self.solar_capacity_mw = solar_capacity_mw
        self.battery_bus = battery_bus
        self.battery_capacity_mwh = battery_capacity_mwh
        self.battery_max_p_mw = battery_max_p_mw
        self.ev_bus = ev_bus
        self.ev_max_p_mw = ev_max_p_mw
        self.slack_vm_pu = slack_vm_pu

    def build_network(self) -> pp.pandapowerNet:
        """Instantiates pandapower case33bw network and attaches DER elements."""
        net = pn.case33bw()
        if len(net.ext_grid) > 0:
            net.ext_grid.at[0, "vm_pu"] = self.slack_vm_pu

        # 1. Attach Solar PV as Static Generator (sgen)
        # In pandapower sgen: p_mw > 0 produces active power
        solar_idx = pp.create_sgen(
            net,
            bus=self.solar_bus,
            p_mw=0.0,
            q_mvar=0.0,
            sn_mva=self.solar_capacity_mw,
            name="Solar_PV_Agent_18",
            type="PV",
            controllable=True
        )

        # 2. Attach Battery Energy Storage System (storage)
        # In pandapower storage: p_mw > 0 is consumption (charging), p_mw < 0 is generation (discharging)
        battery_idx = pp.create_storage(
            net,
            bus=self.battery_bus,
            p_mw=0.0,
            max_e_mwh=self.battery_capacity_mwh,
            sn_mva=self.battery_max_p_mw,
            name="BESS_Agent_14",
            controllable=True
        )

        # 3. Attach EV Fast Charging Hub as Controllable Load
        # In pandapower load: p_mw > 0 is consumption
        ev_idx = pp.create_load(
            net,
            bus=self.ev_bus,
            p_mw=0.0,
            q_mvar=0.0,
            name="EV_Hub_Agent_24",
            controllable=True
        )

        logger.info(
            f"Built DER network: Solar at Bus {self.solar_bus} (idx {solar_idx}), "
            f"BESS at Bus {self.battery_bus} (idx {battery_idx}), "
            f"EV at Bus {self.ev_bus} (idx {ev_idx})"
        )
        return net
