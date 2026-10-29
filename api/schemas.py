"""Pydantic Request and Response Schemas for API endpoints."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    controller: str = Field(default="resilient", description="centralized, independent, coordinated, or resilient")
    attack_scenario: Optional[str] = Field(default="false_data", description="none, false_data, communication_delay, packet_loss, agent_failure, combined")
    episode_length: int = Field(default=72, ge=12, le=720)
    start_idx: int = Field(default=1000, ge=0)


class CopilotQueryRequest(BaseModel):
    query: str
    run_id: Optional[str] = "resilient_false_data"


class CopilotQueryResponse(BaseModel):
    query: str
    response: str
    rag_context_snippets: List[str] = []
