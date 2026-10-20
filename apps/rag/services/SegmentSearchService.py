"""SegmentSearchService - question -> ranked segments.

Steps
  1. embed the question once
  2. for every (segment, content_type) take the BEST cosine similarity
     (SQL: MIN(cosine_distance) grouped in Postgres)
  3. ScoreCombiner merges the per-type similarities into one score per segment
  4. drop below `threshold`, sort, keep `top_k`
"""
from collections import defaultdict

from django.db.models import Min
from pgvector.django import CosineDistance

from apps.rag.encoder.Encoder import get_encoder
from apps.rag.models import SegmentEmbedding, VideoSegment
from apps.rag.services.ScoreCombiner import ScoreCombiner


class SegmentSearchService:
    def __init__(self, encoder=None):
        self.encoder = encoder or get_encoder()

    def search(self, question, top_k=3, threshold=0.30, weights=None):
        """Returns {"weights": {...}, "results": [ {segment fields + score info}, ... ]}"""
        combiner = ScoreCombiner(weights)
        q_vec = self.encoder.encode(question, normalize_embeddings=True).tolist()

        rows = SegmentEmbedding.objects.values("segment_id", "content_type").annotate(
            distance=Min(CosineDistance("embedding", q_vec))
        )
        per_segment = defaultdict(dict)
        for row in rows:
            per_segment[row["segment_id"]][row["content_type"]] = 1.0 - float(row["distance"])

        scores = [combiner.combine(seg_id, sims) for seg_id, sims in per_segment.items()]
        scores = [s for s in scores if s.score >= threshold]
        scores.sort(key=lambda s: s.score, reverse=True)
        scores = scores[:top_k]

        segments = VideoSegment.objects.in_bulk([s.segment_id for s in scores])
        results = [{**segments[s.segment_id].to_dict(), **s.to_dict()} for s in scores]
        return {"weights": combiner.weights, "results": results}
