"""Google Gemini LLM Provider using the new google-genai SDK."""

import os
import logging
from typing import Optional
from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Copilot provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client: {e}")

    def generate_response(self, system_prompt: str, user_prompt: str, context: Optional[str] = None) -> str:
        if not self.client:
            return (
                "[Gemini Copilot Notice] GEMINI_API_KEY is not configured or client initialization failed. "
                "Retrieved RAG Context and simulation tools are available."
            )

        full_prompt = f"{system_prompt}\n\n"
        if context:
            full_prompt += f"{context}\n\n"
        full_prompt += f"Operator Question: {user_prompt}"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return f"Error contacting Gemini API: {e}"
