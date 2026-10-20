"""SegmentInputSerializer - body of POST /api/rag/segments/ (same shape as video_segments.json)."""
from rest_framework import serializers

from apps.rag.utils.TimeRangeParser import TimeRangeParser


class SegmentInputSerializer(serializers.Serializer):
    segment_id = serializers.CharField(max_length=50)
    video_id = serializers.CharField(max_length=50)
    video_title = serializers.CharField(required=False, allow_blank=True, default="")  # optional
    time = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    title = serializers.CharField(max_length=255)
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    keywords = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    possible_questions = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_time(self, value):
        try:
            TimeRangeParser.parse(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return value
