from django.urls import path
from .api.productAPI_ import ProductAPI


urlpatterns = [
    path('products/', ProductAPI.as_view(), name='product-list'),
]