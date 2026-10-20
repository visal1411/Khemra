from django.contrib import admin
from apps.rag.models import KnowledgeEmbedding


@admin.register(KnowledgeEmbedding)
class KnowledgeEmbeddingAdmin(admin.ModelAdmin):
    list_display = ("id", "segment", "metadata_type", "item_index", "model_name", "created_at")
    list_filter = ("metadata_type", "model_name")
    search_fields = ("segment__title", "title", "summary")
