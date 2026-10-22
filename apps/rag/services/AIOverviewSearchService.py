import logging
import uuid
from typing import Any, Dict, List, Optional

from apps.rag.services.GroqLLMService import GroqLLMService
from apps.rag.services.KnowledgeSearchService import KnowledgeSearchService

logger = logging.getLogger(__name__)


class AIOverviewSearchService:
    """
    Orchestrates multi-signal vector search and LLM overview generation.
    Preserves the exact segment results array while enriching the response
    with a revised natural summary and grounded procedural steps.
    """

    def __init__(
        self,
        search_service: Optional[KnowledgeSearchService] = None,
        llm_service=None,
    ):
        self.search_service = search_service or KnowledgeSearchService()
        self.llm_service = llm_service or GroqLLMService()

    def search_with_overview(
        self,
        question: str,
        language: str = "en",
        top_k: int = 3,
        threshold: float = 0.30,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Executes vector search and conditionally triggers LLM synthesis.
        Guarantees that segment_id references in steps map to retrieved segments.
        """
        search_result = self.search_service.search(
            question=question,
            language=language,
            top_k=top_k,
            threshold=threshold,
            weights=weights,
        )

        results = search_result.get("results", [])
        if not results:
            return {
                "question": question,
                "language": language,
                "summary": None,
                "steps": [],
                "count": 0,
                "weights_used": search_result.get("weights_used", {}),
                "results": [],
            }

        # Synthesize overview and grounded steps via LLM provider
        try:
            llm_output = self.llm_service.generate_ai_overview(
                question=question,
                language=language,
                segments=results,
            )
        except Exception as e:
            logger.error(f"Unexpected error calling LLM service: {e}")
            llm_output = {"summary": None, "steps": []}

        summary = llm_output.get("summary")
        raw_steps = llm_output.get("steps") or []

        # Validate and enforce referential integrity for steps
        valid_segment_ids = {str(r.get("segment_id")) for r in results}
        default_segment_id = str(results[0].get("segment_id"))

        validated_steps: List[Dict[str, Any]] = []
        for idx, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue

            seg_id = str(step.get("segment_id", "")).strip()
            # If LLM hallucinates an unknown ID or invalid UUID, fallback to top match
            try:
                uuid.UUID(seg_id)
                if seg_id not in valid_segment_ids:
                    seg_id = default_segment_id
            except (ValueError, TypeError, AttributeError):
                seg_id = default_segment_id

            validated_steps.append({
                "step_number": int(step.get("step_number") or idx),
                "title": str(step.get("title") or f"Step {idx}"),
                "instruction": str(step.get("instruction") or ""),
                "segment_id": seg_id,
            })

        return {
            "question": question,
            "language": language,
            "summary": summary,
            "steps": validated_steps,
            "count": search_result.get("count", len(results)),
            "weights_used": search_result.get("weights_used", {}),
            "results": results,
        }
