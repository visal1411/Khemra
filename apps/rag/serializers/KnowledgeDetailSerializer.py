from rest_framework import serializers
from apps.rag.models import Knowledge, KnowledgeSource, KnowledgeSegment


class KnowledgeSourceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeSource
        fields = ["id", "language", "duration_seconds", "page_count"]


class KnowledgeSegmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeSegment
        fields = [
            "id",
            "segment_index",
            "title",
            "summary",
            "transcript",
            "keywords",
            "possible_questions",
            "start_time_seconds",
            "end_time_seconds",
            "page_start",
            "page_end",
        ]


class KnowledgeDetailSerializer(serializers.ModelSerializer):
    sources = KnowledgeSourceDetailSerializer(many=True, read_only=True)
    segments = KnowledgeSegmentDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Knowledge
        fields = [
            "id",
            "title",
            "description",
            "source_type",
            "processing_status",
            "created_at",
            "updated_at",
            "sources",
            "segments",
        ]
