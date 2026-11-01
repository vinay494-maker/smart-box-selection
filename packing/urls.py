from django.urls import path, include
from rest_framework.routers import DefaultRouter

from packing.views import (
    RecommendBoxAPIView, BoxViewSet, ProductViewSet,
    OrderViewSet, PackingRecommendationViewSet,
    dashboard_view, boxes_view, products_view, orders_view
)

router = DefaultRouter()
router.register(r'boxes', BoxViewSet, basename='box')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'recommendations', PackingRecommendationViewSet, basename='recommendation')

urlpatterns = [
    # Frontend Warehouse Station
    path('', dashboard_view, name='dashboard'),
    path('boxes/', boxes_view, name='boxes'),
    path('products/', products_view, name='products'),
    path('orders/', orders_view, name='orders'),

    # REST APIs
    path('api/recommend-box/', RecommendBoxAPIView.as_view(), name='api-recommend-box'),
    path('api/', include(router.urls)),
]
