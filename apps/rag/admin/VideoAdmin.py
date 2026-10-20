from django.contrib import admin

from apps.rag.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("video_id", "title", "duration_seconds")
