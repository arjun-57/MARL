"""RAG Agent integrating domain knowledge retrieval with live telemetry."""

import logging
from typing import Dict, Any, List

from rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class RAGCopilotContext:
    """Constructs enriched prompt context with relevant engineering rules and current telemetry."""

    def __init__(self, doc_dir: str = "rag/documents"):
        self.retriever = KnowledgeRetriever(doc_dir=doc_dir)

    def build_context(self, user_query: str, live_telemetry: Dict[str, Any] = None) -> str:
        """Retrieves top docs and formats context block for LLM."""
        matched_chunks = self.retriever.retrieve(user_query, top_k=3)

        context_lines = ["=== RELEVANT ENGINEERING RULES & SYSTEM DOCUMENTATION ==="]
        for c in matched_chunks:
            context_lines.append(f"[{c['title']} > {c['section']}] (Relevance: {c['score']:.2f})")
            context_lines.append(c["content"])
            context_lines.append("---")

        if live_telemetry:
            context_lines.append("\n=== CURRENT LIVE SYSTEM TELEMETRY ===")
            for k, v in live_telemetry.items():
                context_lines.append(f"{k}: {v}")

        return "\n".join(context_lines)
