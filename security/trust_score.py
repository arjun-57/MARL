"""Dynamic Agent Trust Score Engine based on multi-criteria verification."""

import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class TrustScoreEngine:
    """
    Maintains and dynamically updates a cyber-physical trust score T_i in [0, 1]
    for each agent in the multi-agent system.
    """

    def __init__(
        self,
        decay_factor: float = 0.35,      # Trust drops quickly on fault
        recovery_factor: float = 0.05,   # Trust recovers gradually
        quarantine_threshold: float = 0.40,
        warning_threshold: float = 0.70
    ):
        self.decay_factor = decay_factor
        self.recovery_factor = recovery_factor
        self.quarantine_threshold = quarantine_threshold
        self.warning_threshold = warning_threshold

        # Default trust initialized to 1.0 (fully trusted)
        self.trust_scores: Dict[str, float] = {
            "solar_agent": 1.0,
            "demand_agent": 1.0,
            "battery_agent": 1.0,
            "ev_agent": 1.0,
            "market_agent": 1.0
        }

    def update_agent_trust(self, agent_id: str, penalty: float):
        """
        Updates trust score:
        If penalty > 0: T_{new} = T_{old} * (1 - decay * penalty)
        If penalty == 0: T_{new} = min(1.0, T_{old} + recovery)
        """
        current_trust = self.trust_scores.get(agent_id, 1.0)
        if penalty > 0:
            new_trust = current_trust * (1.0 - self.decay_factor * min(1.0, penalty))
            new_trust = max(0.05, new_trust)  # floor at 0.05
            logger.warning(f"Agent {agent_id} penalized {penalty:.2f}: Trust {current_trust:.2f} -> {new_trust:.2f}")
        else:
            new_trust = min(1.0, current_trust + self.recovery_factor)

        self.trust_scores[agent_id] = float(new_trust)

    def get_trust(self, agent_id: str) -> float:
        """Returns trust score of specific agent."""
        return self.trust_scores.get(agent_id, 1.0)

    def is_quarantined(self, agent_id: str) -> bool:
        """Returns True if agent is below quarantine threshold."""
        return self.get_trust(agent_id) < self.quarantine_threshold

    def get_all_scores(self) -> Dict[str, float]:
        """Returns snapshot of all agent trust scores."""
        return {k: round(v, 4) for k, v in self.trust_scores.items()}
