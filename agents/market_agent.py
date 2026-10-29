"""Market Agent responsible for economic signals and arbitrage proposals."""

import logging
from typing import Dict, Any

from agents.base_agent import BaseAgent
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """
    Analyzes wholesale day-ahead electricity prices from Ember and formulates BUY/SELL/HOLD proposals.
    """

    def __init__(
        self,
        agent_id: str = "market_agent",
        bus: SimulatedMessageBus = None,
        cheap_price_threshold: float = 35.0,
        high_price_threshold: float = 75.0
    ):
        super().__init__(agent_id=agent_id, bus=bus)
        self.cheap_price_threshold = cheap_price_threshold
        self.high_price_threshold = high_price_threshold

    def step(self, current_step: int, env_state: Dict[str, Any]) -> Dict[str, Any]:
        self.receive_messages()

        price = float(env_state.get("price_eur_mwh", 50.0))

        if price <= self.cheap_price_threshold:
            action = "BUY"
            power_mw = 0.5
            reason = "low_spot_price"
        elif price >= self.high_price_threshold:
            action = "SELL"
            power_mw = -0.5
            reason = "high_peak_price"
        else:
            action = "HOLD"
            power_mw = 0.0
            reason = "neutral_price_regime"

        self.send_message(
            receiver="coordinator_agent",
            message_type="market_signal_proposal",
            payload={
                "action": action,
                "power_mw": power_mw,
                "spot_price_eur": price,
                "reason": reason
            },
            step=current_step,
            confidence=0.94
        )

        return {
            "agent": self.agent_id,
            "action": action,
            "power_mw": power_mw,
            "reason": reason
        }
