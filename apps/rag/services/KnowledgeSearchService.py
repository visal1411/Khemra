"""KnowledgeSearchService - vector similarity search, multi-signal scoring, and multi-language source resolution."""
from collections import defaultdict
from django.db.models import Min
from pgvector.django import CosineDistance

from apps.rag.encoder.Encoder import get_encoder
from apps.rag.models import KnowledgeSegment, KnowledgeEmbedding
from apps.rag.services.ScoreCombiner import ScoreCombiner


class KnowledgeSearchService:
    def __init__(self, encoder=None):
        self.encoder = encoder or get_encoder()

    def search(self, question, language="en", top_k=3, threshold=0.30, weights=None):
        combiner = ScoreCombiner(weights)
        raw_vec = self.encoder.encode(question, normalize_embeddings=True)
        q_vec = raw_vec.tolist() if hasattr(raw_vec, "tolist") else list(raw_vec)

        # 1. Cosine distance query per segment and metadata type
        rows = (
            KnowledgeEmbedding.objects.values("segment_id", "metadata_type__name")
            .annotate(distance=Min(CosineDistance("embedding_vector", q_vec)))
        )

        per_segment = defaultdict(dict)
        for row in rows:
            per_segment[str(row["segment_id"])][row["metadata_type__name"]] = 1.0 - float(row["distance"])

        # 2. Combine scores per segment
        scores = [combiner.combine(seg_id, sims) for seg_id, sims in per_segment.items()]
        scores = [s for s in scores if s.score >= threshold]
        scores.sort(key=lambda s: s.score, reverse=True)

        if not scores:
            return {
                "question": question,
                "language": language,
                "count": 0,
                "weights_used": combiner.weights,
                "results": [],
            }

        # 3. Bulk fetch candidate segments (fetch extra candidates to allow room for deduplication)
        candidate_pool_size = max(top_k * 5, 25)
        candidate_scores = scores[:candidate_pool_size]
        target_ids = [s.segment_id for s in candidate_scores]
        segments = (
            KnowledgeSegment.objects.filter(id__in=target_ids)
            .select_related("knowledge")
            .prefetch_related("knowledge__sources")
        )
        seg_map = {str(seg.id): seg for seg in segments}

        # 4. Resolve multi-language sources and assemble deduplicated results
        results = []
        seen_segments = set()

        for s in candidate_scores:
            seg = seg_map.get(s.segment_id)
            if not seg:
                continue

            knowledge = seg.knowledge

            # Deduplication key:
            # 1. Same knowledge title + segment index (re-uploaded document)
            # 2. Same segment title + content snippet (identical text chunk across documents)
            k_title = (knowledge.title or "").strip().lower()
            s_title = (seg.title or "").strip().lower()
            content_snippet = (seg.summary or seg.transcript or "")[:120].strip().lower()

            dedup_key_index = (k_title, seg.segment_index)
            dedup_key_content = (s_title, content_snippet) if (s_title and content_snippet) else None

            if dedup_key_index in seen_segments:
                continue
            if dedup_key_content and dedup_key_content in seen_segments:
                continue

            seen_segments.add(dedup_key_index)
            if dedup_key_content:
                seen_segments.add(dedup_key_content)

            sources = list(knowledge.sources.all())

            matched_source = None
            if sources:
                # Priority 1: Match requested language
                lang_match = next((src for src in sources if src.language.lower() == language.lower()), None)
                if lang_match:
                    matched_source = {
                        "id": lang_match.id,
                        "language": lang_match.language,
                        "file_url": lang_match.file_url or "",
                        "duration_seconds": lang_match.duration_seconds,
                        "page_count": lang_match.page_count,
                        "is_fallback": False,
                    }
                else:
                    # Fallback priority: English or first available source
                    fallback = next((src for src in sources if src.language.lower() == "en"), sources[0])
                    matched_source = {
                        "id": fallback.id,
                        "language": fallback.language,
                        "file_url": fallback.file_url or "",
                        "duration_seconds": fallback.duration_seconds,
                        "page_count": fallback.page_count,
                        "is_fallback": True,
                    }

            results.append({
                "segment_id": seg.id,
                "knowledge_id": knowledge.id,
                "knowledge_title": knowledge.title,
                "source_type": knowledge.source_type,
                "segment_index": seg.segment_index,
                "title": seg.title,
                "summary": seg.summary,
                "transcript": seg.transcript,
                "start_time_seconds": seg.start_time_seconds,
                "end_time_seconds": seg.end_time_seconds,
                "page_start": seg.page_start,
                "page_end": seg.page_end,
                "keywords": seg.keywords or [],
                "score": round(s.score, 4),
                "confidence": s.confidence,
                "best_match": s.best_match,
                "confidence_by_type": s.confidence_by_type,
                "matched_source": matched_source,
            })

            if len(results) >= top_k:
                break

        return {
            "question": question,
            "language": language,
            "count": len(results),
            "weights_used": combiner.weights,
            "results": results,
        }
