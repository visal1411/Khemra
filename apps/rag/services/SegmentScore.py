"""SegmentScore - result object: how well ONE segment matched a question."""
from dataclasses import dataclass, field


@dataclass
class SegmentScore:
    segment_id: str
    similarities: dict = field(default_factory=dict)  # content_type -> cosine similarity
    score: float = 0.0                                # combined, 0..1
    best_match: str = ""                              # content_type with the highest similarity

    @staticmethod
    def _confidence(similarity):
        """cosine similarity -> percent (negative similarity counts as 0%)."""
        return round(max(0.0, min(1.0, similarity)) * 100, 2)

    @property
    def confidence(self):
        return round(self.score * 100, 2)

    @property
    def confidence_by_type(self):
        return {t: self._confidence(s) for t, s in self.similarities.items()}

    def to_dict(self):
        return {
            "score": round(self.score, 4),
            "confidence": self.confidence,
            "best_match": self.best_match,
            "confidence_by_type": self.confidence_by_type,
        }
