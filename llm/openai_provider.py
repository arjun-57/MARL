"""OpenAI LLM Provider."""

import os
import logging
from typing import Optional
from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Copilot provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI Client: {e}")

    def generate_response(self, system_prompt: str, user_prompt: str, context: Optional[str] = None) -> str:
        if not self.client:
            return (
                "[OpenAI Copilot Notice] OPENAI_API_KEY is not configured. "
                "Retrieved RAG Context and simulation tools are available."
            )

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"Relevant Context:\n{context}"})
        messages.append({"role": "user", "content": user_prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"Error contacting OpenAI API: {e}"
