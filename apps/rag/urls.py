from django.urls import path
from .views import SearchAPI, SegmentDetailAPI, SegmentExportAPI, SegmentListCreateAPI

urlpatterns = [
    path("segments/", SegmentListCreateAPI.as_view(), name="segment-list-create"),
    path("segments/export/", SegmentExportAPI.as_view(), name="segment-export"),  # before <segment_id>
    path("segments/<str:segment_id>/", SegmentDetailAPI.as_view(), name="segment-detail"),
    path("search/", SearchAPI.as_view(), name="search"),
]
