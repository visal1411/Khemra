from rest_framework import serializers
from ..models import Product


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product

        fields = [
            'id',
            'name',
            'description',
            'price',
            'stock_quantity',
            'image_url',
            'is_available',
            'created_at',
            'updated_at',
        ]

        # These fields should not be modified directly by API clients
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]