from django.contrib import admin
from packing.models import Box, Product, Order, OrderItem, PackingRecommendation, PackedBox, PlacedItem


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dimensions_display', 'max_weight', 'cost', 'volume_liters', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('cost',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'dimensions_display', 'weight', 'is_fragile', 'keep_upright')
    list_filter = ('category', 'is_fragile', 'keep_upright')
    search_fields = ('sku', 'name')
    ordering = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'status', 'total_items_count', 'total_weight', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer_name')
    inlines = [OrderItemInline]


class PlacedItemInline(admin.TabularInline):
    model = PlacedItem
    extra = 0
    readonly_fields = ('step_number', 'product', 'x', 'y', 'z', 'placed_length', 'placed_width', 'placed_height', 'rotation_name')


@admin.register(PackedBox)
class PackedBoxAdmin(admin.ModelAdmin):
    list_display = ('recommendation', 'box_index', 'box', 'volume_utilization', 'used_weight', 'box_cost')
    inlines = [PlacedItemInline]


@admin.register(PackingRecommendation)
class PackingRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'total_boxes_count', 'total_cost', 'total_items_weight', 'algorithm_used', 'created_at')
    list_filter = ('status', 'algorithm_used', 'created_at')
    search_fields = ('order__order_number',)
