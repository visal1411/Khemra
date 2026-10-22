from django.urls import path
from .views import (
    KnowledgeUploadAPI,
    KnowledgeSearchAPI,
    KnowledgeDetailAPI,
    PresignedUrlAPI,
    AIOverviewAPI,
)

urlpatterns = [
    path("storage/presigned-url/", PresignedUrlAPI.as_view(), name="storage-presigned-url"),
    path("knowledge/", KnowledgeUploadAPI.as_view(), name="knowledge-upload"),
    path("knowledge/<uuid:id>/", KnowledgeDetailAPI.as_view(), name="knowledge-detail"),
    path("knowledge/search/", KnowledgeSearchAPI.as_view(), name="knowledge-search"),
    path("knowledge/search/ai-overview/", AIOverviewAPI.as_view(), name="knowledge-search-ai-overview"),
]

