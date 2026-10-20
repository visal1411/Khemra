from rest_framework import serializers


class MatchedSourceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    language = serializers.CharField()
    duration_seconds = serializers.FloatField(allow_null=True)
    page_count = serializers.IntegerField(allow_null=True)
    is_fallback = serializers.BooleanField(default=False)


class SearchResultItemSerializer(serializers.Serializer):
    segment_id = serializers.UUIDField()
    knowledge_id = serializers.UUIDField()
    knowledge_title = serializers.CharField()
    source_type = serializers.CharField()
    segment_index = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True, allow_null=True)
    summary = serializers.CharField(allow_blank=True, allow_null=True)
    transcript = serializers.CharField(allow_blank=True, allow_null=True)
    start_time_seconds = serializers.FloatField(allow_null=True)
    end_time_seconds = serializers.FloatField(allow_null=True)
    page_start = serializers.IntegerField(allow_null=True)
    page_end = serializers.IntegerField(allow_null=True)
    keywords = serializers.ListField(child=serializers.CharField(), default=list)
    score = serializers.FloatField()
    confidence = serializers.FloatField()
    best_match = serializers.CharField(allow_blank=True)
    confidence_by_type = serializers.DictField(child=serializers.FloatField())
    matched_source = MatchedSourceSerializer(allow_null=True)


class KnowledgeSearchResponseSerializer(serializers.Serializer):
    question = serializers.CharField()
    language = serializers.CharField()
    count = serializers.IntegerField()
    weights_used = serializers.DictField(child=serializers.FloatField())
    results = serializers.ListField(child=SearchResultItemSerializer())
