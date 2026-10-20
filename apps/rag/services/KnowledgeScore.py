"""KnowledgeScore - data container representing the multi-signal score of one segment."""
from dataclasses import dataclass, field


@dataclass
class KnowledgeScore:
    segment_id: str
    similarities: dict = field(default_factory=dict)  # metadata_type_name -> cosine similarity (0..1)
    score: float = 0.0                                # combined weighted score (0..1)
    best_match: str = ""                              # metadata_type_name with the highest similarity

    @staticmethod
    def _confidence(similarity):
        """cosine similarity -> percent (clamps between 0% and 100%)."""
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
