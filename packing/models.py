from django.db import models
from decimal import Decimal


class Box(models.Model):
    """
    Represents an available shipping box in the warehouse.
    """
    code = models.CharField(max_length=50, unique=True, help_text="Unique box code or SKU (e.g., BOX-S, BOX-M)")
    name = models.CharField(max_length=100, help_text="Human-readable box name (e.g., Small Shipping Carton)")
    
    # Internal dimensions in cm
    inner_length = models.DecimalField(max_digits=8, decimal_places=2, help_text="Internal length in cm")
    inner_width = models.DecimalField(max_digits=8, decimal_places=2, help_text="Internal width in cm")
    inner_height = models.DecimalField(max_digits=8, decimal_places=2, help_text="Internal height in cm")
    
    # Weight capacity in kg
    max_weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Maximum weight capacity in kg")
    empty_weight = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.10'), help_text="Tare weight of the empty box in kg")
    
    # Cost to company (USD / currency units)
    cost = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cost of box in USD")
    
    is_active = models.BooleanField(default=True, help_text="Whether this box is available for order packing")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cost', 'inner_length']
        verbose_name = "Shipping Box"
        verbose_name_plural = "Shipping Boxes"

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.inner_length}x{self.inner_width}x{self.inner_height}cm, Max {self.max_weight}kg, ${self.cost}"

    @property
    def volume(self) -> float:
        """Volume in cubic centimeters (cm³)."""
        return float(self.inner_length * self.inner_width * self.inner_height)

    @property
    def volume_liters(self) -> float:
        return round(self.volume / 1000.0, 2)

    @property
    def volumetric_weight(self) -> float:
        """Standard carrier dimensional weight: L*W*H / 5000 (kg)."""
        return round(self.volume / 5000.0, 2)

    @property
    def dimensions_display(self) -> str:
        return f"{self.inner_length} × {self.inner_width} × {self.inner_height} cm"


class Product(models.Model):
    """
    Represents an ecommerce product with physical dimensions and weight.
    """
    CATEGORY_CHOICES = [
        ('ELECTRONICS', 'Electronics & Gadgets'),
        ('APPAREL', 'Apparel & Fashion'),
        ('BOOKS', 'Books & Media'),
        ('HOME', 'Home & Kitchen'),
        ('GLASSWARE', 'Fragile & Glassware'),
        ('COSMETICS', 'Cosmetics & Beauty'),
        ('OTHER', 'General Merchandise'),
    ]

    sku = models.CharField(max_length=64, unique=True, help_text="Unique product SKU")
    name = models.CharField(max_length=150, help_text="Product title")
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='OTHER')
    
    # Dimensions in cm
    length = models.DecimalField(max_digits=8, decimal_places=2, help_text="Length in cm")
    width = models.DecimalField(max_digits=8, decimal_places=2, help_text="Width in cm")
    height = models.DecimalField(max_digits=8, decimal_places=2, help_text="Height in cm")
    
    # Weight in kg
    weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Weight in kg")
    
    # Handling constraints
    is_fragile = models.BooleanField(default=False, help_text="Requires padding and top placement")
    keep_upright = models.BooleanField(default=False, help_text="Must be kept right-side-up (no sideways tilting)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.sku}] - {self.length}x{self.width}x{self.height}cm ({self.weight}kg)"

    @property
    def volume(self) -> float:
        """Volume in cubic centimeters (cm³)."""
        return float(self.length * self.width * self.height)

    @property
    def dimensions_display(self) -> str:
        return f"{self.length} × {self.width} × {self.height} cm"


class Order(models.Model):
    """
    Customer order to be packed by the warehouse team.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Packing'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
    ]

    order_number = models.CharField(max_length=64, unique=True, help_text="Order ID/Number (e.g., ORD-10023)")
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text="Special shipping or handling notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} ({self.customer_name}) - {self.get_status_display()}"

    @property
    def total_items_count(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def total_weight(self) -> float:
        return sum(float(item.product.weight * item.quantity) for item in self.items.all())

    @property
    def total_volume(self) -> float:
        return sum(item.product.volume * item.quantity for item in self.items.all())

    @property
    def has_fragile_items(self) -> bool:
        return any(item.product.is_fragile for item in self.items.all())


class OrderItem(models.Model):
    """
    An item line within an Order.
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.order.order_number}"

    @property
    def line_weight(self) -> float:
        return float(self.product.weight * self.quantity)

    @property
    def line_volume(self) -> float:
        return self.product.volume * self.quantity


class PackingRecommendation(models.Model):
    """
    Generated recommendation for how to pack an order into one or more boxes.
    """
    order = models.ForeignKey(Order, null=True, blank=True, related_name='recommendations', on_delete=models.SET_NULL)
    
    total_items_count = models.PositiveIntegerField(default=0)
    total_items_weight = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_items_volume = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    total_boxes_count = models.PositiveIntegerField(default=1)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    algorithm_used = models.CharField(max_length=64, default="3D-EMS-BestFit")
    status = models.CharField(max_length=32, default="OPTIMAL", help_text="OPTIMAL, MULTI_BOX, NO_FIT")
    
    ai_summary = models.TextField(blank=True, help_text="AI reasoning, void fill suggestions, and hazard advisory")
    packing_guidance = models.JSONField(default=list, blank=True, help_text="Step-by-step instructions for packing team")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Packing Recommendation #{self.id} for Order {self.order.order_number if self.order else 'Ad-hoc'} (${self.total_cost})"


class PackedBox(models.Model):
    """
    A specific box allocated in a packing recommendation, along with metrics and contents.
    """
    recommendation = models.ForeignKey(PackingRecommendation, related_name='packed_boxes', on_delete=models.CASCADE)
    box = models.ForeignKey(Box, on_delete=models.PROTECT)
    box_index = models.PositiveIntegerField(default=1, help_text="Box 1, Box 2, etc.")
    
    used_weight = models.DecimalField(max_digits=8, decimal_places=2)
    used_volume = models.DecimalField(max_digits=12, decimal_places=2)
    volume_utilization = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of box volume used")
    box_cost = models.DecimalField(max_digits=8, decimal_places=2)
    
    recommended_void_fill = models.CharField(max_length=150, blank=True, help_text="E.g., Air pillows (30% void), Kraft paper")

    class Meta:
        ordering = ['box_index']

    def __str__(self):
        return f"Box {self.box_index}: {self.box.name} ({self.volume_utilization}% filled)"


class PlacedItem(models.Model):
    """
    Represents an item placed at a specific (x, y, z) coordinate inside a PackedBox.
    """
    packed_box = models.ForeignKey(PackedBox, related_name='placements', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    
    step_number = models.PositiveIntegerField(default=1, help_text="Packing sequence step")
    
    # Coordinate of lower-left-bottom corner in cm (0,0,0 is box bottom-left-front)
    x = models.DecimalField(max_digits=8, decimal_places=2)
    y = models.DecimalField(max_digits=8, decimal_places=2)
    z = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Placed dimensions (may be rotated)
    placed_length = models.DecimalField(max_digits=8, decimal_places=2)
    placed_width = models.DecimalField(max_digits=8, decimal_places=2)
    placed_height = models.DecimalField(max_digits=8, decimal_places=2)
    
    rotation_name = models.CharField(max_length=32, default="Original (L×W×H)")
    special_instruction = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.product.name} at ({self.x}, {self.y}, {self.z})"
