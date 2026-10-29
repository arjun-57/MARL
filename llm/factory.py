"""LLM Provider Factory supporting Gemini, OpenAI, and Mock offline copilot."""

import os
import logging
from typing import Optional
from llm.base import BaseLLMProvider
from llm.gemini_provider import GeminiProvider
from llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class MockOfflineProvider(BaseLLMProvider):
    """Deterministic local copilot that synthesizes answers from retrieved RAG context without API keys."""

    def generate_response(self, system_prompt: str, user_prompt: str, context: Optional[str] = None) -> str:
        reply = [
            "### Grid Operations & Research Copilot (Local Expert)",
            f"**Query**: {user_prompt}",
            "\n**Analysis based on RAG & System Telemetry**:"
        ]
        if "discharge" in user_prompt.lower() or "battery" in user_prompt.lower():
            reply.append(
                "- **BESS Dispatch Decision**: The Battery Agent commands active discharge when wholesale "
                "electricity prices peak above 70-75 EUR/MWh, or when feeder voltage drops below 0.94 p.u. to provide voltage support. "
                "Discharge is strictly gated by the Safety Agent to preserve the 10% SOC minimum buffer."
            )
        elif "solar" in user_prompt.lower() or "untrusted" in user_prompt.lower() or "fdi" in user_prompt.lower():
            reply.append(
                "- **Cyber-Physical Security & Trust Analysis**: The Solar Agent was flagged and quarantined "
                "due to [Check 1 Physical] reporting power exceeding its 1.5 MW rated inverter capacity, and [Check 3 Cross-Clock] "
                "reporting non-zero solar generation during nighttime hours. The Coordinator subsequently discounted its telemetry."
            )
        else:
            reply.append(
                "- **Multi-Agent Coordination State**: All agents operate on the IEEE 33-bus test feeder. "
                "Proposals from Solar, Demand, Battery, EV, and Market are filtered through the 4-tier cyber-physical verification checks "
                "and reconciled by the Coordinator before the Safety Agent enforces physical constraint limits."
            )

        if context:
            reply.append("\n**Retrieved RAG Excerpts**:")
            for line in context.split("\n")[:8]:
                reply.append(f"> {line}")

        return "\n".join(reply)


class LLMFactory:
    """Factory to instantiate provider-independent LLM Copilot."""

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
        provider = (provider_name or os.getenv("LLM_PROVIDER", "gemini")).lower()
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "your_gemini_api_key_here":
                return GeminiProvider()
            else:
                logger.info("GEMINI_API_KEY not set; using MockOfflineProvider for Copilot.")
                return MockOfflineProvider()
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your_openai_api_key_here":
                return OpenAIProvider()
            else:
                logger.info("OPENAI_API_KEY not set; using MockOfflineProvider for Copilot.")
                return MockOfflineProvider()
        else:
            return MockOfflineProvider()
