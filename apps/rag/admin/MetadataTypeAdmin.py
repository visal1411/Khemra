from django.contrib import admin
from apps.rag.models import MetadataType


@admin.register(MetadataType)
class MetadataTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "weight", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
