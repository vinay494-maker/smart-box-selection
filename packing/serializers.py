from rest_framework import serializers
from decimal import Decimal
from packing.models import Box, Product, Order, OrderItem, PackingRecommendation, PackedBox, PlacedItem


class BoxSerializer(serializers.ModelSerializer):
    volume_liters = serializers.ReadOnlyField()
    volumetric_weight = serializers.ReadOnlyField()
    dimensions_display = serializers.ReadOnlyField()

    class Meta:
        model = Box
        fields = [
            'id', 'code', 'name', 'inner_length', 'inner_width', 'inner_height',
            'max_weight', 'empty_weight', 'cost', 'is_active',
            'volume', 'volume_liters', 'volumetric_weight', 'dimensions_display'
        ]


class ProductSerializer(serializers.ModelSerializer):
    dimensions_display = serializers.ReadOnlyField()
    volume = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'category', 'length', 'width', 'height',
            'weight', 'is_fragile', 'keep_upright', 'volume', 'dimensions_display'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    line_weight = serializers.ReadOnlyField()
    line_volume = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'line_weight', 'line_volume']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_items_count = serializers.ReadOnlyField()
    total_weight = serializers.ReadOnlyField()
    total_volume = serializers.ReadOnlyField()
    has_fragile_items = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'status', 'notes', 'created_at', 'updated_at',
            'total_items_count', 'total_weight', 'total_volume', 'has_fragile_items', 'items'
        ]


class PlacedItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')

    class Meta:
        model = PlacedItem
        fields = [
            'id', 'product_name', 'product_sku', 'step_number',
            'x', 'y', 'z', 'placed_length', 'placed_width', 'placed_height',
            'rotation_name', 'special_instruction'
        ]


class PackedBoxSerializer(serializers.ModelSerializer):
    box_code = serializers.ReadOnlyField(source='box.code')
    box_name = serializers.ReadOnlyField(source='box.name')
    placements = PlacedItemSerializer(many=True, read_only=True)

    class Meta:
        model = PackedBox
        fields = [
            'id', 'box_index', 'box', 'box_code', 'box_name',
            'used_weight', 'used_volume', 'volume_utilization',
            'box_cost', 'recommended_void_fill', 'placements'
        ]


class PackingRecommendationSerializer(serializers.ModelSerializer):
    packed_boxes = PackedBoxSerializer(many=True, read_only=True)
    order_number = serializers.ReadOnlyField(source='order.order_number')

    class Meta:
        model = PackingRecommendation
        fields = [
            'id', 'order', 'order_number', 'total_items_count',
            'total_items_weight', 'total_items_volume', 'total_boxes_count',
            'total_cost', 'algorithm_used', 'status', 'ai_summary',
            'packing_guidance', 'packed_boxes', 'created_at'
        ]


class AdHocItemInputSerializer(serializers.Serializer):
    sku = serializers.CharField(required=False, default="")
    name = serializers.CharField(required=False, default="Item")
    length = serializers.FloatField(min_value=0.1)
    width = serializers.FloatField(min_value=0.1)
    height = serializers.FloatField(min_value=0.1)
    weight = serializers.FloatField(min_value=0.01)
    quantity = serializers.IntegerField(min_value=1, default=1)
    is_fragile = serializers.BooleanField(required=False, default=False)
    keep_upright = serializers.BooleanField(required=False, default=False)
    product_id = serializers.IntegerField(required=False, allow_null=True)


class RecommendBoxRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=False, allow_null=True)
    items = AdHocItemInputSerializer(many=True, required=False)

    def validate(self, data):
        if not data.get('order_id') and not data.get('items'):
            raise serializers.ValidationError("Either 'order_id' or a non-empty 'items' list must be provided.")
        return data
