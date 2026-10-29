"""Tests for Battery Electrochemical Physical Dynamics."""

import pytest
from assets.battery import BatteryStorage


def test_battery_charge_discharge():
    battery = BatteryStorage(capacity_mwh=2.0, initial_soc=0.50, max_charge_mw=0.8, max_discharge_mw=0.8)

    # Test Charging
    act_p, new_soc, deg = battery.step(requested_p_mw=0.4, dt_hours=1.0)
    assert act_p > 0
    assert new_soc > 0.50
    assert deg > 0

    # Test Discharging
    act_p2, new_soc2, deg2 = battery.step(requested_p_mw=-0.4, dt_hours=1.0)
    assert act_p2 < 0
    assert new_soc2 < new_soc


def test_battery_limits():
    battery = BatteryStorage(capacity_mwh=2.0, initial_soc=0.94, soc_max=0.95)
    # Request massive charge
    act_p, new_soc, _ = battery.step(requested_p_mw=0.8, dt_hours=1.0)
    assert new_soc <= 0.95
