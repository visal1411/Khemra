"""KnowledgeIngestService - atomic multi-source, multi-segment, and multi-facet embedding ingestion pipeline."""
import base64
from django.db import transaction

from apps.rag.encoder.Encoder import get_encoder
from apps.rag.models import (
    Knowledge,
    KnowledgeSource,
    KnowledgeSegment,
    MetadataType,
    KnowledgeEmbedding,
    ProcessingStatus,
)
from apps.rag.services.EmbeddingTextBuilder import EmbeddingTextBuilder


class KnowledgeIngestService:
    def __init__(self, encoder=None):
        self.encoder = encoder or get_encoder()
        self.text_builder = EmbeddingTextBuilder()

    def ingest(self, validated_data):
        """
        Ingest knowledge, multi-language sources, segments, and facet embeddings atomically.
        Returns the created Knowledge instance.
        """
        with transaction.atomic():
            knowledge = Knowledge.objects.create(
                title=validated_data["title"],
                description=validated_data.get("description") or "",
                source_type=validated_data["source_type"],
                processing_status=ProcessingStatus.PROCESSING,
            )

            # 1. Create Sources (Multi-Language)
            for src in validated_data.get("sources", []):
                raw_bytes = b""
                file_str = src.get("file_data")
                if file_str:
                    if isinstance(file_str, bytes):
                        raw_bytes = file_str
                    else:
                        raw_bytes = base64.b64decode(file_str)

                KnowledgeSource.objects.create(
                    knowledge=knowledge,
                    language=src["language"],
                    file_data=raw_bytes if raw_bytes else None,
                    file_url=src.get("file_url") or "",
                    duration_seconds=src.get("duration_seconds"),
                    page_count=src.get("page_count"),
                )

            # 2. Create Segments
            segments = []
            for seg_data in validated_data.get("segments", []):
                seg = KnowledgeSegment.objects.create(
                    knowledge=knowledge,
                    segment_index=seg_data["segment_index"],
                    title=seg_data.get("title") or "",
                    summary=seg_data.get("summary") or "",
                    transcript=seg_data.get("transcript") or "",
                    keywords=seg_data.get("keywords") or [],
                    possible_questions=seg_data.get("possible_questions") or [],
                    start_time_seconds=seg_data.get("start_time_seconds"),
                    end_time_seconds=seg_data.get("end_time_seconds"),
                    page_start=seg_data.get("page_start"),
                    page_end=seg_data.get("page_end"),
                )
                segments.append((seg, seg_data))

            # 3. Extract metadata items per segment
            metadata_type_cache = {m.name: m for m in MetadataType.objects.all()}
            all_facet_items = []
            for seg, seg_data in segments:
                items = self.text_builder.build(seg_data)
                for item in items:
                    mtype_name = item["metadata_type"]
                    mtype = metadata_type_cache.get(mtype_name)
                    if not mtype:
                        mtype, _ = MetadataType.objects.get_or_create(
                            name=mtype_name,
                            defaults={"weight": 0.25, "is_active": True},
                        )
                        metadata_type_cache[mtype_name] = mtype

                    all_facet_items.append({
                        "segment": seg,
                        "metadata_type": mtype,
                        "item_index": item["item_index"],
                        "text": item["text"],
                        "field_kwargs": item["field_kwargs"],
                    })

            # 4. Batch vector generation
            if all_facet_items:
                texts = [item["text"] for item in all_facet_items]
                vectors = self.encoder.encode(texts, normalize_embeddings=True)

                embeddings_to_create = []
                for idx, item in enumerate(all_facet_items):
                    vec = vectors[idx]
                    vec_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)
                    embeddings_to_create.append(
                        KnowledgeEmbedding(
                            segment=item["segment"],
                            metadata_type=item["metadata_type"],
                            item_index=item["item_index"],
                            embedding_vector=vec_list,
                            model_name="fastembed/model",
                            model_version="1.0",
                            **item["field_kwargs"],
                        )
                    )

                KnowledgeEmbedding.objects.bulk_create(embeddings_to_create)

            knowledge.processing_status = ProcessingStatus.COMPLETED
            knowledge.save(update_fields=["processing_status", "updated_at"])

            return knowledge
