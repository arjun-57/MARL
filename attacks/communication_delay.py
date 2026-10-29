"""Communication network attacks and Agent Failure attack."""

import logging
from typing import Dict, Any, Optional

from attacks.base_attack import BaseAttack
from communication.message import AgentMessage
from communication.message_bus import SimulatedMessageBus

logger = logging.getLogger(__name__)


class CommunicationDelayAttack(BaseAttack):
    """Enforces network propagation latency on inter-agent communication."""

    def __init__(self, delay_steps: int = 2, start_step: int = 20, end_step: int = 60):
        super().__init__(name="CommunicationDelayAttack", start_step=start_step, end_step=end_step)
        self.delay_steps = delay_steps

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        bus.delay_active = self.is_triggered(current_step)
        bus.latency_channel.delay_steps = self.delay_steps

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        return data_row


class PacketLossAttack(BaseAttack):
    """Causes high stochastic packet loss on the communication bus."""

    def __init__(self, drop_probability: float = 0.40, start_step: int = 20, end_step: int = 60):
        super().__init__(name="PacketLossAttack", start_step=start_step, end_step=end_step)
        self.drop_probability = drop_probability

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        bus.loss_active = self.is_triggered(current_step)
        bus.loss_channel.drop_probability = self.drop_probability

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        return data_row


class AgentFailureAttack(BaseAttack):
    """Simulates an agent hardware crash or silent dropout (e.g. BESS agent drops offline)."""

    def __init__(self, target_agent: str = "battery_agent", start_step: int = 30, end_step: int = 70):
        super().__init__(name="AgentFailureAttack", start_step=start_step, end_step=end_step)
        self.target_agent = target_agent

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        if not self.is_triggered(current_step):
            return

        def failure_interceptor(msg: AgentMessage) -> Optional[AgentMessage]:
            if msg.sender == self.target_agent:
                logger.warning(f"[ATTACK] Agent {self.target_agent} failed - message suppressed")
                return None
            return msg

        bus.register_interceptor(failure_interceptor)

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        return data_row


class CombinedAttack(BaseAttack):
    """Multi-vector attack combining FDI, Communication Delay, and Packet Loss."""

    def __init__(self, start_step: int = 24, end_step: int = 72):
        super().__init__(name="CombinedAttack", start_step=start_step, end_step=end_step)
        from attacks.false_data import FalseDataInjectionAttack
        self.fdi = FalseDataInjectionAttack(target_agent="solar_agent", bias_mw=1.8, start_step=start_step, end_step=end_step)
        self.delay = CommunicationDelayAttack(delay_steps=2, start_step=start_step, end_step=end_step)
        self.loss = PacketLossAttack(drop_probability=0.25, start_step=start_step, end_step=end_step)

    def apply_cyber(self, bus: SimulatedMessageBus, current_step: int):
        if not self.is_triggered(current_step):
            return
        self.fdi.apply_cyber(bus, current_step)
        self.delay.apply_cyber(bus, current_step)
        self.loss.apply_cyber(bus, current_step)

    def apply_physical(self, data_row: Dict[str, Any], current_step: int) -> Dict[str, Any]:
        return data_row
