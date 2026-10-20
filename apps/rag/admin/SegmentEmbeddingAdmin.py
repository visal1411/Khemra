from django.contrib import admin

from apps.rag.models import SegmentEmbedding


@admin.register(SegmentEmbedding)
class SegmentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ("id", "segment", "content_type")
    list_filter = ("content_type",)
    exclude = ("embedding",)  # 384 floats are not human-readable
