"""SearchRequestSerializer - body of POST /api/rag/search/

weights (optional) e.g. {"question": 0.6, "summary": 0.4} - replaces the default weights.
"""
from rest_framework import serializers

from apps.rag.constants.ContentType import ContentType


class SearchRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, default=3, min_value=1, max_value=50)
    threshold = serializers.FloatField(required=False, default=0.30, min_value=0.0, max_value=1.0)
    weights = serializers.DictField(
        child=serializers.FloatField(min_value=0.0), required=False, allow_null=True, default=None
    )

    def validate_weights(self, value):
        if value is None:
            return None
        unknown = set(value) - set(ContentType.values)
        if unknown:
            raise serializers.ValidationError(
                f"Unknown keys {sorted(unknown)}; allowed: {sorted(ContentType.values)}"
            )
        if sum(value.values()) <= 0:
            raise serializers.ValidationError("At least one weight must be > 0.")
        return value
