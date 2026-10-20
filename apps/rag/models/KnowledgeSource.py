import uuid
from django.db import models


class KnowledgeSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge = models.ForeignKey(
        "rag.Knowledge",
        on_delete=models.CASCADE,
        related_name="sources",
        db_column="knowledge_id",
    )
    language = models.CharField(max_length=10)
    file_data = models.BinaryField(null=True, blank=True, help_text="the actual file bytes")
    file_url = models.CharField(max_length=1000, null=True, blank=True, help_text="URL to file in S3/CDN/external storage")
    duration_seconds = models.FloatField(null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_sources"
        constraints = [
            models.UniqueConstraint(
                fields=["knowledge", "language"],
                name="unique_knowledge_source_language",
            )
        ]

    def __str__(self):
        return f"{self.knowledge_id} [{self.language}]"
