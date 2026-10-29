"""Battery Storage Agent responsible for BESS dispatch and SOC management."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class BatteryAgent(BaseAgent):
    """
    Manages BESS at Bus 14. Proposes charging during cheap/solar-surplus periods
    and discharging during expensive peak periods while preserving degradation limits.
    """

    def __init__(
        self,
        agent_id: str = "battery_agent",
        bus: SimulatedMessageBus = None,
        max_p_mw: float = 0.8,
        target_soc_min: float = 0.20,
        target_soc_max: float = 0.90
    ):
        super().__init__(agent_id=agent_id, bus=bus)
        self.max_p_mw = max_p_mw
        self.target_soc_min = target_soc_min
        self.target_soc_max = target_soc_max

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        self.receive_messages()

        soc = float(env_state.get("battery_soc", 0.5))
        price = float(env_state.get("price_eur_mwh", 50.0))
        solar = float(env_state.get("solar_available_mw", 0.0))
        v_min = float(env_state.get("v_min_pu", 1.0))

        proposed_p_mw = 0.0
        reason = "idle"

        # 1. Voltage Support Priority: If grid suffers undervoltage, inject power (discharge)
        if v_min < 0.94 and soc > self.target_soc_min:
            discharge_need = min(self.max_p_mw, (0.95 - v_min) * 5.0)
            proposed_p_mw = - discharge_need
            reason = "voltage_support_discharge"

        # 2. Solar Absorption: If high solar (> 0.8 MW) and SOC < 0.9, charge
        elif solar > 0.8 and soc < self.target_soc_max:
            charge_power = min(self.max_p_mw, solar * 0.6)
            proposed_p_mw = charge_power
            reason = "solar_surplus_charge"

        # 3. Economic Arbitrage:
        elif price < 30.0 and soc < self.target_soc_max:
            # Low price -> charge
            proposed_p_mw = 0.5 * self.max_p_mw
            reason = "economic_low_price_charge"
        elif price > 75.0 and soc > self.target_soc_min:
            # High price -> discharge
            proposed_p_mw = - 0.7 * self.max_p_mw
            reason = "economic_high_price_discharge"

        self.send_message(
            receiver="coordinator_agent",
            message_type="battery_proposal",
            payload={
                "proposed_power_mw": proposed_p_mw,
                "soc": soc,
                "reason": reason
            },
            step=current_step,
            confidence=0.96
        )

        return {
            "agent": self.agent_id,
            "proposed_power_mw": proposed_p_mw,
            "soc": soc,
            "reason": reason
        }
