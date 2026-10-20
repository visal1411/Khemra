import uuid
from django.db import models

from .enums import ProcessingStatus, SourceType


class Knowledge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
