from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),

    # RAG video-segment search API
    path('api/rag/', include('apps.rag.urls')),
]
