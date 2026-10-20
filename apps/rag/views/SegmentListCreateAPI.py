from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.models import VideoSegment
from apps.rag.serializers import SegmentInputSerializer
from apps.rag.services.SegmentIngestService import SegmentIngestService


class SegmentListCreateAPI(APIView):
    """GET  /api/rag/segments/  -> list all
       POST /api/rag/segments/  -> embed (per metadata) + save one segment"""

    def get(self, request):
        return Response([s.to_dict() for s in VideoSegment.objects.all()])

    def post(self, request):
        ser = SegmentInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        if VideoSegment.objects.filter(pk=d["segment_id"]).exists():
            return Response(
                {"error": f"Segment '{d['segment_id']}' already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        seg, _ = SegmentIngestService().upsert_one(d)
        return Response(seg.to_dict(), status=status.HTTP_201_CREATED)
