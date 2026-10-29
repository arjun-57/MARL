"""Tests for Multi-Agent Communication, Safety, and Security Checks."""

import pytest
from communication.message_bus import SimulatedMessageBus
from communication.message import AgentMessage
from agents.solar_agent import SolarAgent
from agents.battery_agent import BatteryAgent
from agents.safety_agent import SafetyAgent
from security.physical_checker import PhysicalConsistencyChecker
from security.temporal_checker import TemporalConsistencyChecker
from security.trust_score import TrustScoreEngine


def test_agent_proposals_and_bus():
    bus = SimulatedMessageBus()
    solar = SolarAgent(bus=bus)
    battery = BatteryAgent(bus=bus)

    env_state = {"solar_available_mw": 1.2, "v_max_pu": 1.0, "v_min_pu": 0.98, "battery_soc": 0.5, "price_eur_mwh": 25.0}

    s_res = solar.step(0, env_state)
    b_res = battery.step(0, env_state)

    assert s_res["solar_available_mw"] == 1.2
    assert b_res["proposed_power_mw"] > 0  # Should propose charging on cheap power

    # Check bus delivered messages
    msgs = bus.receive_messages("coordinator_agent")
    assert len(msgs) == 2


def test_safety_agent_overrides():
    safety = SafetyAgent(bess_max_p_mw=0.8, soc_max=0.95)

    # 1. Test BESS charge clamp
    action, status, mods = safety.filter_actions(
        proposed_actions={"battery_p_mw": 1.5, "ev_p_mw": 0.2},
        current_env_state={"battery_soc": 0.5, "v_min_pu": 1.0, "v_max_pu": 1.0}
    )
    assert action["battery_p_mw"] == 0.8
    assert status == "MODIFY"

    # 2. Test Undervoltage Emergency Throttle
    action2, status2, mods2 = safety.filter_actions(
        proposed_actions={"battery_p_mw": 0.5, "ev_p_mw": 0.4},
        current_env_state={"battery_soc": 0.5, "v_min_pu": 0.90, "v_max_pu": 1.0}
    )
    assert action2["battery_p_mw"] == 0.0  # Stopped charging
    assert action2["ev_p_mw"] == 0.2  # Throttled by 50%
    assert status2 == "EMERGENCY"


def test_security_physical_check_fdi():
    checker = PhysicalConsistencyChecker(solar_capacity_mw=1.5)
    fdi_msg = AgentMessage(
        sender="solar_agent",
        receiver="coordinator_agent",
        message_type="solar_generation_report",
        timestamp=0.0,
        step=10,
        payload={"generation_mw": 3.5}  # Impossible 3.5 MW on 1.5 MW inverter
    )
    is_valid, penalty, reason = checker.check(fdi_msg)
    assert not is_valid
    assert penalty > 0
    assert "exceeds physical rating" in reason


def test_trust_score_decay_and_quarantine():
    trust_engine = TrustScoreEngine(quarantine_threshold=0.40)
    assert trust_engine.get_trust("solar_agent") == 1.0

    # Repeated faults
    for _ in range(4):
        trust_engine.update_agent_trust("solar_agent", penalty=0.8)

    assert trust_engine.is_quarantined("solar_agent")
    assert trust_engine.get_trust("solar_agent") < 0.40
