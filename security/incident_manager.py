"""Cyber-Physical Security Incident Manager and Coordinator."""

import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
import time

from communication.message import AgentMessage
from security.physical_checker import PhysicalConsistencyChecker
from security.temporal_checker import TemporalConsistencyChecker
from security.consistency_checker import CrossAgentConsistencyChecker
from security.anomaly_detector import StatisticalAnomalyDetector
from security.trust_score import TrustScoreEngine

logger = logging.getLogger(__name__)


@dataclass
class SecurityIncident:
    """Security alert event logged during simulation."""
    step: int
    timestamp_str: str
    agent_id: str
    check_type: str
    penalty: float
    description: str
    quarantined: bool


class IncidentManager:
    """Orchestrates all 4 security checks, maintains trust scores, and generates security audits."""

    def __init__(self):
        self.physical_checker = PhysicalConsistencyChecker()
        self.temporal_checker = TemporalConsistencyChecker()
        self.cross_checker = CrossAgentConsistencyChecker()
        self.anomaly_detector = StatisticalAnomalyDetector()
        self.trust_engine = TrustScoreEngine()

        self.incident_history: List[SecurityIncident] = []

    def evaluate_incoming_message(
        self,
        msg: AgentMessage,
        step: int,
        timestamp_str: str,
        grid_load_mw: float = 0.0,
        hour_of_day: int = 12
    ) -> float:
        """
        Runs message through all 4 checks, logs any anomalies, and updates agent trust.
        Returns final trust score of sender.
        """
        agent_id = msg.sender
        total_penalty = 0.0
        reasons = []

        # 1. Physical Consistency Check
        p_ok, p_pen, p_reason = self.physical_checker.check(msg)
        if not p_ok:
            total_penalty += p_pen
            reasons.append(f"[Check 1 Physical] {p_reason}")

        # 2. Temporal Consistency Check
        t_ok, t_pen, t_reason = self.temporal_checker.check(msg)
        if not t_ok:
            total_penalty += t_pen
            reasons.append(f"[Check 2 Temporal] {t_reason}")

        # 3. Cross-Agent / Clock Checks
        if agent_id == "solar_agent":
            reported_solar = msg.payload.get("generation_mw", 0.0)
            c_ok, c_pen, c_reason = self.cross_checker.check_solar_vs_clock(reported_solar, hour_of_day)
            if not c_ok:
                total_penalty += c_pen
                reasons.append(f"[Check 3 Cross-Clock] {c_reason}")

        # 4. Statistical Anomaly Check
        for key, val in msg.payload.items():
            if isinstance(val, (int, float)):
                s_ok, s_pen, s_reason = self.anomaly_detector.evaluate_metric(agent_id, key, float(val))
                if not s_ok:
                    total_penalty += s_pen * 0.5  # statistical is softer evidence
                    reasons.append(f"[Check 4 Stats] {s_reason}")

        # Update Trust
        self.trust_engine.update_agent_trust(agent_id, total_penalty)
        quarantined = self.trust_engine.is_quarantined(agent_id)

        if total_penalty > 0:
            for r in reasons:
                incident = SecurityIncident(
                    step=step,
                    timestamp_str=timestamp_str,
                    agent_id=agent_id,
                    check_type="MultiCheck",
                    penalty=float(total_penalty),
                    description=r,
                    quarantined=quarantined
                )
                self.incident_history.append(incident)
                logger.warning(f"Security Alert @ step {step} ({timestamp_str}) [{agent_id}]: {r}")

        return self.trust_engine.get_trust(agent_id)

    def get_trust_scores(self) -> Dict[str, float]:
        return self.trust_engine.get_all_scores()

    def get_recent_incidents(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [
            {
                "step": inc.step,
                "timestamp": inc.timestamp_str,
                "agent_id": inc.agent_id,
                "check_type": inc.check_type,
                "penalty": inc.penalty,
                "description": inc.description,
                "quarantined": inc.quarantined
            }
            for inc in self.incident_history[-limit:]
        ]
