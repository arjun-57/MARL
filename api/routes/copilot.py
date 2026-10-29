"""Copilot Assistant API Route integrating RAG and LLM."""

from fastapi import APIRouter
from api.schemas import CopilotQueryRequest, CopilotQueryResponse
from rag.rag_agent import RAGCopilotContext
from llm.factory import LLMFactory
from llm.prompts import COPILOT_SYSTEM_PROMPT
from llm.tools import CopilotTools

router = APIRouter(prefix="/copilot", tags=["copilot"])
rag_context = RAGCopilotContext()
copilot_tools = CopilotTools()


@router.post("/query", response_model=CopilotQueryResponse)
def query_copilot(req: CopilotQueryRequest):
    """Answers operator queries using RAG domain retrieval and LLM reasoning."""
    telemetry = copilot_tools.get_current_state(run_id=req.run_id or "resilient_false_data")
    context = rag_context.build_context(req.query, live_telemetry=telemetry)

    llm = LLMFactory.get_provider()
    response_text = llm.generate_response(
        system_prompt=COPILOT_SYSTEM_PROMPT,
        user_prompt=req.query,
        context=context
    )

    snippets = [line for line in context.split("\n") if line.startswith("[") or line.startswith(">")]

    return CopilotQueryResponse(
        query=req.query,
        response=response_text,
        rag_context_snippets=snippets[:6]
    )
