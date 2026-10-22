from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.serializers.AIOverviewResponseSerializer import AIOverviewResponseSerializer
from apps.rag.serializers.KnowledgeSearchRequestSerializer import KnowledgeSearchRequestSerializer
from apps.rag.services.AIOverviewSearchService import AIOverviewSearchService


class AIOverviewAPI(APIView):
    """
    POST /api/rag/knowledge/search/ai-overview/

    Performs vector similarity search against knowledge segments and returns
    a revised answer summary and step-by-step instructions grounded in the
    retrieved segments, alongside the complete, unchanged search results.
    """

    def post(self, request):
        serializer = KnowledgeSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = AIOverviewSearchService()
        result = service.search_with_overview(**serializer.validated_data)

        response_serializer = AIOverviewResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
