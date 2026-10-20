from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),

    # Catalog API
    path('api/', include('apps.catalog.urls')),

    # RAG video-segment search API
    path('api/rag/', include('apps.rag.urls')),
]
