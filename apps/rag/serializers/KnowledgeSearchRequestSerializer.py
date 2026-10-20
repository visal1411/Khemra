from rest_framework import serializers


class KnowledgeSearchRequestSerializer(serializers.Serializer):
    question = serializers.CharField(required=True, min_length=1)
    language = serializers.CharField(required=False, default="en", max_length=10)
    top_k = serializers.IntegerField(required=False, default=3, min_value=1, max_value=50)
    threshold = serializers.FloatField(required=False, default=0.30, min_value=0.0, max_value=1.0)
    weights = serializers.DictField(
        child=serializers.FloatField(min_value=0.0),
        required=False,
        allow_null=True,
    )

    def validate_question(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Search question cannot be empty or whitespace only.")
        return value.strip()

    def validate_weights(self, value):
        if value is not None:
            if not isinstance(value, dict) or not value:
                raise serializers.ValidationError("Weights must be a non-empty dictionary mapping metadata types to positive numbers.")
            if sum(value.values()) <= 0:
                raise serializers.ValidationError("At least one weight must be greater than zero.")
        return value
