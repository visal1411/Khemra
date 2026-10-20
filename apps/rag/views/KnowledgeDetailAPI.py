from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.models import Knowledge
from apps.rag.serializers.KnowledgeDetailSerializer import KnowledgeDetailSerializer


class KnowledgeDetailAPI(APIView):
    def get(self, request, id):
        try:
            knowledge = (
                Knowledge.objects.prefetch_related("sources", "segments")
                .get(id=id)
            )
        except Knowledge.DoesNotExist:
            return Response(
                {"error": f"Knowledge with id '{id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = KnowledgeDetailSerializer(knowledge)
        return Response(serializer.data, status=status.HTTP_200_OK)
