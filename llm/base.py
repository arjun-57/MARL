"""Abstract Base Class for LLM Providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract interface for LLM Copilot providers."""

    @abstractmethod
    def generate_response(self, system_prompt: str, user_prompt: str, context: Optional[str] = None) -> str:
        """Generates a text completion given system prompt, query, and retrieved RAG context."""
        pass
