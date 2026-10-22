from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseLLMService(ABC):
    """
    Abstract base interface for LLM synthesis services.
    Enables swapping Groq with a custom self-hosted LLM (e.g. vLLM, Ollama, TGI)
    without modifying API views or serialization logic.
    """

    @abstractmethod
    def generate_ai_overview(
        self,
        question: str,
        language: str,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesize a revised answer summary and ordered procedural steps
        strictly grounded in the provided candidate segments.

        :param question: The user's original query string.
        :param language: Target output language (e.g., 'en' or 'km').
        :param segments: List of candidate segment dictionaries retrieved from vector search.
        :return: Dict containing 'summary' (str) and 'steps' (list of dicts).
        """
        pass
