import uuid
from django.db import models


class KnowledgeSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge = models.ForeignKey(
        "rag.Knowledge",
        on_delete=models.CASCADE,
        related_name="segments",
        db_column="knowledge_id",
    )
    segment_index = models.IntegerField(
        default=0,
        help_text="Order index of segment within knowledge",
    )
    transcript = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    keywords = models.JSONField(default=list, blank=True, null=True)
    possible_questions = models.JSONField(default=list, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    start_time_seconds = models.FloatField(null=True, blank=True)
    end_time_seconds = models.FloatField(null=True, blank=True)
    page_start = models.IntegerField(null=True, blank=True)
    page_end = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_segments"
        ordering = ["knowledge", "segment_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["knowledge", "segment_index"],
                name="unique_knowledge_segment_index",
            )
        ]

    def __str__(self):
        return f"{self.knowledge_id} - Segment {self.segment_index}: {self.title or 'Untitled'}"

    def to_dict(self):
        return {
            "id": str(self.id),
            "knowledge_id": str(self.knowledge_id),
            "segment_index": self.segment_index,
            "title": self.title,
            "summary": self.summary,
            "transcript": self.transcript,
            "keywords": self.keywords or [],
            "possible_questions": self.possible_questions or [],
            "start_time_seconds": self.start_time_seconds,
            "end_time_seconds": self.end_time_seconds,
            "page_start": self.page_start,
            "page_end": self.page_end,
        }
