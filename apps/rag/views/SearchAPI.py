from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rag.serializers import SearchRequestSerializer
from apps.rag.services.SegmentSearchService import SegmentSearchService


class SearchAPI(APIView):
    """POST /api/rag/search/
    {"question": "...", "top_k": 3, "threshold": 0.3, "weights": {"question": 0.5, "summary": 0.5}}
    `weights` is optional."""

    def post(self, request):
        ser = SearchRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        found = SegmentSearchService().search(
            question=d["question"], top_k=d["top_k"], threshold=d["threshold"], weights=d["weights"]
        )
        return Response(
            {
                "question": d["question"],
                "count": len(found["results"]),
                "weights": found["weights"],
                "results": found["results"],
            }
        )
