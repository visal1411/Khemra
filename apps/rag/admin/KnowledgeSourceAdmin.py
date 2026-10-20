from django.contrib import admin
from apps.rag.models import KnowledgeSource


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "knowledge", "language", "file_url", "duration_seconds", "page_count", "created_at")
    list_filter = ("language", "created_at")
    search_fields = ("knowledge__title", "language", "file_url")
