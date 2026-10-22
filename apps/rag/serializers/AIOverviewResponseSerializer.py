from rest_framework import serializers

from apps.rag.serializers.KnowledgeSearchResponseSerializer import SearchResultItemSerializer


class AIOverviewStepSerializer(serializers.Serializer):
    """
    Serializer for individual procedural action steps linked to a supporting segment.
    """
    step_number = serializers.IntegerField(min_value=1)
    title = serializers.CharField()
    instruction = serializers.CharField()
    segment_id = serializers.UUIDField()


class AIOverviewResponseSerializer(serializers.Serializer):
    """
    Response serializer for AI Overview search.
    Provides synthesized summary and steps alongside the unchanged vector search results array.
    """
    question = serializers.CharField()
    language = serializers.CharField()
    summary = serializers.CharField(allow_null=True, required=False)
    steps = serializers.ListField(child=AIOverviewStepSerializer(), default=list)
    count = serializers.IntegerField()
    weights_used = serializers.DictField(child=serializers.FloatField())
    results = serializers.ListField(child=SearchResultItemSerializer())
