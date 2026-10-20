from django.contrib import admin
from apps.rag.models import KnowledgeSegment


@admin.register(KnowledgeSegment)
class KnowledgeSegmentAdmin(admin.ModelAdmin):
    list_display = ("id", "knowledge", "segment_index", "title", "created_at")
    list_filter = ("knowledge", "created_at")
    search_fields = ("title", "summary", "transcript", "keywords")
