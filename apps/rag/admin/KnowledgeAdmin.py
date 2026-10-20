from django.contrib import admin
from apps.rag.models import Knowledge


@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "source_type", "processing_status", "created_at")
    list_filter = ("source_type", "processing_status", "created_at")
    search_fields = ("title", "description")
