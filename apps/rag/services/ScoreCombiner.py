"""ScoreCombiner - merges the per-metadata similarities into ONE score per segment.

    score = sum(weight[t] * similarity[t]) / sum(weight[t])      (only for types the segment has)

Weights come from (highest priority first):
  1. the `weights` argument (per request)  - replaces the defaults entirely
  2. settings.RAG_WEIGHTS                  - optional
  3. DEFAULT_WEIGHTS below
Types with weight 0 / not listed are still REPORTED in confidence_by_type
but do not influence the combined score.
"""
from django.conf import settings

from apps.rag.constants.ContentType import ContentType
from apps.rag.services.SegmentScore import SegmentScore


class ScoreCombiner:
    DEFAULT_WEIGHTS = {
        ContentType.KEYWORD.value: 0.20,
        ContentType.QUESTION.value: 0.35,
        ContentType.TOPIC.value: 0.20,
        ContentType.SUMMARY.value: 0.25,
    }

    def __init__(self, weights=None):
        raw = weights or getattr(settings, "RAG_WEIGHTS", None) or self.DEFAULT_WEIGHTS
        self.weights = self._validate(raw)

    def combine(self, segment_id, similarities):
        """similarities: {content_type: cosine similarity} -> SegmentScore"""
        used = {t: w for t, w in self.weights.items() if t in similarities and w > 0}
        total = sum(used.values())
        score = (
            sum(w * max(0.0, similarities[t]) for t, w in used.items()) / total if total else 0.0
        )
        best = max(similarities, key=similarities.get) if similarities else ""
        return SegmentScore(
            segment_id=segment_id, similarities=dict(similarities), score=score, best_match=best
        )

    @staticmethod
    def _validate(raw):
        valid = set(ContentType.values)
        unknown = set(raw) - valid
        if unknown:
            raise ValueError(f"Unknown weight keys {sorted(unknown)}; allowed: {sorted(valid)}")
        weights = {t: float(raw.get(t, 0.0)) for t in valid}
        if any(w < 0 for w in weights.values()) or sum(weights.values()) <= 0:
            raise ValueError("Weights must be >= 0 and at least one must be > 0.")
        return weights
