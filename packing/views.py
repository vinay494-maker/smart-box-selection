from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action

from packing.models import Box, Product, Order, OrderItem, PackingRecommendation, PackedBox, PlacedItem
from packing.serializers import (
    BoxSerializer, ProductSerializer, OrderSerializer,
    PackingRecommendationSerializer, RecommendBoxRequestSerializer
)
from packing.services.box_recommender import BoxRecommender


# ==========================================
# REST API Endpoints
# ==========================================

class RecommendBoxAPIView(APIView):
    """
    Core AI-assisted box recommendation API.
    Accepts either an existing 'order_id' or an ad-hoc 'items' payload.
    Returns the recommended box, 3D placement coordinates, and AI analysis.
    """
    def post(self, request, *args, **kwargs):
        serializer = RecommendBoxRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = serializer.validated_data.get('order_id')
        items_data = serializer.validated_data.get('items')

        if order_id:
            result = BoxRecommender.recommend_for_order(order_id, save_to_db=True)
        else:
            result = BoxRecommender.recommend_for_items(items_data)

        if not result.get('success'):
            return Response(result, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(result, status=status.HTTP_200_OK)


class BoxViewSet(viewsets.ModelViewSet):
    """CRUD operations for shipping boxes."""
    queryset = Box.objects.all().order_by('cost', 'inner_length')
    serializer_class = BoxSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD operations for ecommerce products."""
    queryset = Product.objects.all().order_by('name')
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """CRUD operations for orders, plus packing trigger action."""
    queryset = Order.objects.prefetch_related('items__product').all().order_by('-created_at')
    serializer_class = OrderSerializer

    @action(detail=True, methods=['post'], url_path='recommend-box')
    def recommend_box(self, request, pk=None):
        order = self.get_object()
        result = BoxRecommender.recommend_for_order(order.id, save_to_db=True)
        if not result.get('success'):
            return Response(result, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-packed')
    def mark_packed(self, request, pk=None):
        order = self.get_object()
        order.status = 'PACKED'
        order.save()
        return Response({"success": True, "message": f"Order #{order.order_number} marked as PACKED."})


class PackingRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for past packing recommendations."""
    queryset = PackingRecommendation.objects.prefetch_related('packed_boxes__placements').all()
    serializer_class = PackingRecommendationSerializer


# ==========================================
# Frontend HTML Views (Warehouse Station)
# ==========================================

def dashboard_view(request):
    """Main Warehouse Packing Station & Live 3D Packing Simulator."""
    pending_orders = Order.objects.filter(status='PENDING').prefetch_related('items__product')
    all_boxes = Box.objects.filter(is_active=True).order_by('cost')
    all_products = Product.objects.all().order_by('category', 'name')
    recent_recs = PackingRecommendation.objects.select_related('order').all()[:5]

    context = {
        'pending_orders': pending_orders,
        'boxes': all_boxes,
        'products': all_products,
        'recent_recommendations': recent_recs,
        'active_nav': 'dashboard'
    }
    return render(request, 'dashboard.html', context)


def boxes_view(request):
    """Shipping box inventory and configuration view."""
    boxes = Box.objects.all().order_by('cost')
    return render(request, 'boxes.html', {'boxes': boxes, 'active_nav': 'boxes'})


def products_view(request):
    """Product catalog with dimensions, weights, and handling rules."""
    products = Product.objects.all().order_by('category', 'name')
    return render(request, 'products.html', {'products': products, 'active_nav': 'products'})


def orders_view(request):
    """Orders packing queue view."""
    orders = Order.objects.prefetch_related('items__product', 'recommendations').all().order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders, 'active_nav': 'orders'})
