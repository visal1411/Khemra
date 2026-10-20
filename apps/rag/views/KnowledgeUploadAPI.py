from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.serializers.KnowledgeInputSerializer import KnowledgeInputSerializer
from apps.rag.services.KnowledgeIngestService import KnowledgeIngestService


class KnowledgeUploadAPI(APIView):
    def post(self, request):
        serializer = KnowledgeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = KnowledgeIngestService()
        knowledge = service.ingest(serializer.validated_data)

        return Response(
            {
                "id": str(knowledge.id),
                "title": knowledge.title,
                "source_type": knowledge.source_type,
                "processing_status": knowledge.processing_status,
                "segments_count": knowledge.segments.count(),
                "created_at": knowledge.created_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )
