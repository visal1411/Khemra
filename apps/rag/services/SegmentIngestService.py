"""SegmentIngestService - JSON segment dicts -> videos / video_segments / segment_embedding.

Idempotent: running it again with the same segment_id replaces that segment's
metadata AND its embeddings.  All texts are embedded in ONE batch (fast).
"""
from django.db import transaction

from apps.rag.encoder.Encoder import get_encoder
from apps.rag.models import SegmentEmbedding, Video, VideoSegment
from apps.rag.services.EmbeddingTextBuilder import EmbeddingTextBuilder
from apps.rag.utils.ListTextCodec import ListTextCodec
from apps.rag.utils.TimeRangeParser import TimeRangeParser


class SegmentIngestService:
    def __init__(self, encoder=None, text_builder=None):
        self.encoder = encoder or get_encoder()
        self.text_builder = text_builder or EmbeddingTextBuilder()

    def upsert_one(self, segment):
        """Returns (VideoSegment, created: bool)."""
        result = self.upsert_many([segment])
        return VideoSegment.objects.get(pk=segment["segment_id"]), result["created"] == 1

    def upsert_many(self, segments):
        """Returns {"created": n, "updated": n}."""
        for seg in segments:
            if not seg.get("video_id"):
                raise ValueError(f"Segment '{seg.get('segment_id')}' has no video_id.")

        # 1) embed everything in one batch
        plan = [
            (seg["segment_id"], content_type, text)
            for seg in segments
            for content_type, text in self.text_builder.build(seg)
        ]
        vectors = self.encoder.encode([p[2] for p in plan]) if plan else []

        # 2) save in one transaction
        with transaction.atomic():
            self._save_videos(segments)
            created = sum(self._save_segment(seg) for seg in segments)

            ids = [seg["segment_id"] for seg in segments]
            SegmentEmbedding.objects.filter(segment_id__in=ids).delete()
            SegmentEmbedding.objects.bulk_create(
                [
                    SegmentEmbedding(segment_id=seg_id, content_type=ctype, embedding=vec.tolist())
                    for (seg_id, ctype, _), vec in zip(plan, vectors)
                ]
            )
        return {"created": created, "updated": len(segments) - created}

    # ---- internals -------------------------------------------------------
    def _save_videos(self, segments):
        """One videos row per video_id; duration = latest end_time seen."""
        durations, titles = {}, {}
        for seg in segments:
            _, end = TimeRangeParser.parse(seg.get("time", ""))
            vid = seg["video_id"]
            durations[vid] = max(durations.get(vid, 0), TimeRangeParser.to_seconds(end))
            if seg.get("video_title"):
                titles[vid] = seg["video_title"]

        for vid, duration in durations.items():
            video, created = Video.objects.get_or_create(
                video_id=vid, defaults={"title": titles.get(vid, ""), "duration_seconds": duration}
            )
            if not created:
                video.duration_seconds = max(video.duration_seconds, duration)
                if vid in titles:
                    video.title = titles[vid]
                video.save()

    def _save_segment(self, seg):
        start, end = TimeRangeParser.parse(seg.get("time", ""))
        _, created = VideoSegment.objects.update_or_create(
            segment_id=seg["segment_id"],
            defaults=dict(
                video_id=seg["video_id"],
                start_time=start,
                end_time=end,
                keyword=ListTextCodec.join(seg.get("keywords")),
                question=ListTextCodec.join(seg.get("possible_questions")),
                topic=seg.get("title", ""),
                summary=seg.get("summary", ""),
            ),
        )
        return created
