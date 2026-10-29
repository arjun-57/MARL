"""Electric Vehicle Hub Agent managing EV fleet charging schedules."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class EVAgent(BaseAgent):
    """Manages EV fleet charging station at Bus 24, balancing user deadlines and grid stress."""

    def __init__(self, agent_id: str = "ev_agent", bus: SimulatedMessageBus = None, max_power_mw: float = 0.5):
        super().__init__(agent_id=agent_id, bus=bus)
        self.max_power_mw = max_power_mw

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        self.receive_messages()

        ev_count = int(env_state.get("ev_connected_count", 0))
        price = float(env_state.get("price_eur_mwh", 50.0))
        v_min = float(env_state.get("v_min_pu", 1.0))

        # Base nominal charging demand proportional to connected EVs (50 kW each)
        nominal_demand = min(self.max_power_mw, ev_count * 0.05)

        # Flexibility modulation:
        # If severe undervoltage (< 0.93) or very high price, throttle back to 30% trickle charge
        if v_min < 0.93 or price > 90.0:
            proposed_ev_p = nominal_demand * 0.3
            urgency = "throttled_due_to_grid_stress"
        elif price < 35.0:
            # Cheap price: boost charging
            proposed_ev_p = nominal_demand
            urgency = "accelerated_due_to_cheap_price"
        else:
            proposed_ev_p = nominal_demand * 0.7
            urgency = "standard"

        self.send_message(
            receiver="coordinator_agent",
            message_type="ev_charging_proposal",
            payload={
                "charging_power_mw": proposed_ev_p,
                "ev_connected_count": ev_count,
                "urgency": urgency
            },
            step=current_step,
            confidence=0.90
        )

        return {
            "agent": self.agent_id,
            "charging_power_mw": proposed_ev_p,
            "ev_connected_count": ev_count,
            "urgency": urgency
        }
