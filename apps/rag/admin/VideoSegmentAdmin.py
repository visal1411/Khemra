from django.contrib import admin

from apps.rag.models import VideoSegment


@admin.register(VideoSegment)
class VideoSegmentAdmin(admin.ModelAdmin):
    list_display = ("segment_id", "video", "start_time", "end_time", "topic")
    list_filter = ("video",)
