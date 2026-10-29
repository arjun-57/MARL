"""False Data Injection (FDI) Attack."""

import logging
from typing import Dict, Any, Optional
from copy import deepcopy

from attacks.base_attack import BaseAttack
from communication.message import AgentMessage
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class FalseDataInjectionAttack(BaseAttack):
    """
    Injects false telemetry or false bids into inter-agent communication.
    E.g., Solar Agent claims it is producing 3.5 MW when physical capacity is 1.5 MW,
    or Demand Agent reports artificially reduced demand to mislead coordinator.
    """

    def __init__(
        self,
        target_agent: str = "solar_agent",
        bias_mw: float = 2.0,
        start_step: int = 24,
        end_step: int = 72
    ):
        super().__init__(name="FalseDataInjectionAttack", start_step=start_step, end_step=end_step)
        self.target_agent = target_agent
        self.bias_mw = bias_mw

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        if not self.is_triggered(current_step):
            return

        def fdi_interceptor(msg: AgentMessage) -> Optional[AgentMessage]:
            if msg.sender == self.target_agent and "generation_mw" in msg.payload:
                tampered_msg = deepcopy(msg)
                tampered_msg.payload["generation_mw"] += self.bias_mw
                tampered_msg.tampered = True
                logger.warning(
                    f"[ATTACK] Injected FDI on {msg.sender}: "
                    f"Orig {msg.payload['generation_mw']:.2f} -> Tampered {tampered_msg.payload['generation_mw']:.2f} MW"
                )
                return tampered_msg
            elif msg.sender == self.target_agent and "forecast_mw" in msg.payload:
                tampered_msg = deepcopy(msg)
                tampered_msg.payload["forecast_mw"] += self.bias_mw
                tampered_msg.tampered = True
                return tampered_msg
            return msg

        bus.register_interceptor(fdi_interceptor)

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        return data_row
