from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import Product
from ..serializers import ProductSerializer


class ProductAPI(APIView):

    def get(self, request):
        """Get all products."""

        products = Product.objects.all()

        serializer = ProductSerializer(
            products,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )