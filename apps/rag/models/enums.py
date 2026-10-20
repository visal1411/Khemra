from django.db import models


class ProcessingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class SourceType(models.TextChoices):
    VIDEO = "video", "Video"
    PDF = "pdf", "Pdf"
    TEXT = "text", "Text"
