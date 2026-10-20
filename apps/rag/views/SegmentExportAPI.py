from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.models import VideoSegment


class SegmentExportAPI(APIView):
    """GET /api/rag/segments/export/ -> all segments as JSON (same shape as video_segments.json)"""

    def get(self, request):
        return Response([s.to_dict() for s in VideoSegment.objects.all()])
