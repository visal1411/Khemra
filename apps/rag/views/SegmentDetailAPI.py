from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.models import VideoSegment


class SegmentDetailAPI(APIView):
    """GET / DELETE /api/rag/segments/<segment_id>/   (delete also removes its embeddings)"""

    def _get(self, segment_id):
        return VideoSegment.objects.filter(pk=segment_id).first()

    def get(self, request, segment_id):
        seg = self._get(segment_id)
        if seg is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(seg.to_dict())

    def delete(self, request, segment_id):
        seg = self._get(segment_id)
        if seg is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        seg.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
