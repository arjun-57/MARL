"""Tests for IEEE 33-Bus Grid and Power Flow."""

import pytest
from grid.network_builder import DERNetworkBuilder
from grid.power_flow import PowerFlowEngine
from grid.bus_manager import BusManager
from grid.constraints import GridConstraints


def test_ieee33_network_power_flow():
    builder = DERNetworkBuilder()
    net = builder.build_network()
    assert len(net.bus) == 33
    assert len(net.sgen) >= 1  # Solar
    assert len(net.storage) >= 1  # BESS

    bus_mgr = BusManager(net)
    bus_mgr.scale_all_loads(1.0)
    bus_mgr.set_solar_generation(1.0)
    bus_mgr.set_battery_power(-0.2)  # Discharging 0.2 MW

    res = PowerFlowEngine.run_power_flow(net)
    assert res["converged"]
    assert 0.85 < res["v_min_pu"] <= 1.05
    assert res["total_loss_mw"] > 0

    constraints = GridConstraints()
    eval_res = constraints.evaluate(res)
    assert "safe" in eval_res
    assert eval_res["converged"]
