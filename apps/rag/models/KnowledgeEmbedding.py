import uuid
from django.db import models
from pgvector.django import VectorField


class KnowledgeEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    segment = models.ForeignKey(
        "rag.KnowledgeSegment",
        on_delete=models.CASCADE,
        related_name="embeddings",
        db_column="segment_id",
    )
    metadata_type = models.ForeignKey(
        "rag.MetadataType",
        on_delete=models.CASCADE,
        related_name="embeddings",
        db_column="metadata_type_id",
    )
    item_index = models.IntegerField(
        default=0,
        help_text="0 for title/summary/content; 0,1,2... for keywords/questions",
    )
    title = models.TextField(
        blank=True,
        null=True,
        help_text="filled only when this row embeds the title",
    )
    summary = models.TextField(
        blank=True,
        null=True,
        help_text="filled only when this row embeds the summary",
    )
    keywords = models.JSONField(
        blank=True,
        null=True,
        help_text='[{"text": "HR portal", "vector": [0.027, ...]}]',
    )
    questions = models.JSONField(
        blank=True,
        null=True,
        help_text='[{"text": "How do I apply for leave?", "vector": [...]}]',
    )
    embedding_vector = VectorField(
        dimensions=384,
        help_text="vector of this one item",
    )
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_embeddings"
        indexes = [
            models.Index(
                fields=["segment", "metadata_type"],
                name="k_emb_seg_mtype_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["segment", "metadata_type", "item_index", "model_name", "model_version"],
                name="unique_k_emb_item_model",
            ),
        ]

    def __str__(self):
        return f"{self.segment_id} [{self.metadata_type_id} #{self.item_index}] ({self.model_name})"
