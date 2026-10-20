from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.serializers.KnowledgeSearchRequestSerializer import KnowledgeSearchRequestSerializer
from apps.rag.serializers.KnowledgeSearchResponseSerializer import KnowledgeSearchResponseSerializer
from apps.rag.services.KnowledgeSearchService import KnowledgeSearchService


class KnowledgeSearchAPI(APIView):
    def post(self, request):
        serializer = KnowledgeSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = KnowledgeSearchService()
        result = service.search(**serializer.validated_data)

        response_serializer = KnowledgeSearchResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
