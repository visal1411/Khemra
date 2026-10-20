"""ContentType - the kinds of metadata that get their OWN embedding.

Each value is stored in segment_embedding.content_type, so every metadata
field of a segment is vectorised and scored separately.
"""
from django.db import models


class ContentType(models.TextChoices):
    KEYWORD = "keyword", "Keyword"
    QUESTION = "question", "Question"
    TOPIC = "topic", "Topic"
    SUMMARY = "summary", "Summary"
