from django.core.management.base import BaseCommand
from decimal import Decimal
from packing.models import Box, Product, Order, OrderItem


class Command(BaseCommand):
    help = "Seeds database with realistic ecommerce products, shipping boxes, and test orders."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database..."))

        # 1. Seed Shipping Boxes
        boxes_data = [
            {
                "code": "BOX-XS-MAILER",
                "name": "Padded Mailer Box (XS)",
                "inner_length": Decimal("20.0"),
                "inner_width": Decimal("15.0"),
                "inner_height": Decimal("5.0"),
                "max_weight": Decimal("1.50"),
                "empty_weight": Decimal("0.08"),
                "cost": Decimal("0.65"),
            },
            {
                "code": "BOX-S-SMALL",
                "name": "Small Carton (S)",
                "inner_length": Decimal("25.0"),
                "inner_width": Decimal("20.0"),
                "inner_height": Decimal("12.0"),
                "max_weight": Decimal("4.00"),
                "empty_weight": Decimal("0.15"),
                "cost": Decimal("1.10"),
            },
            {
                "code": "BOX-M-STANDARD",
                "name": "Standard Medium Box (M)",
                "inner_length": Decimal("35.0"),
                "inner_width": Decimal("28.0"),
                "inner_height": Decimal("20.0"),
                "max_weight": Decimal("10.00"),
                "empty_weight": Decimal("0.30"),
                "cost": Decimal("2.15"),
            },
            {
                "code": "BOX-L-LARGE",
                "name": "Large Shipping Box (L)",
                "inner_length": Decimal("48.0"),
                "inner_width": Decimal("38.0"),
                "inner_height": Decimal("30.0"),
                "max_weight": Decimal("20.00"),
                "empty_weight": Decimal("0.65"),
                "cost": Decimal("3.85"),
            },
            {
                "code": "BOX-XL-HEAVY",
                "name": "Extra Large Heavy-Duty Box (XL)",
                "inner_length": Decimal("60.0"),
                "inner_width": Decimal("45.0"),
                "inner_height": Decimal("40.0"),
                "max_weight": Decimal("32.00"),
                "empty_weight": Decimal("1.10"),
                "cost": Decimal("5.90"),
            },
            {
                "code": "BOX-TALL-TUBE",
                "name": "Tall Slim Box",
                "inner_length": Decimal("18.0"),
                "inner_width": Decimal("18.0"),
                "inner_height": Decimal("50.0"),
                "max_weight": Decimal("8.00"),
                "empty_weight": Decimal("0.35"),
                "cost": Decimal("2.75"),
            },
        ]

        created_boxes = {}
        for b in boxes_data:
            box_obj, created = Box.objects.update_or_create(
                code=b["code"],
                defaults=b
            )
            created_boxes[b["code"]] = box_obj
            self.stdout.write(f"  Box: {box_obj.code} ({box_obj.dimensions_display}) - ${box_obj.cost}")

        # 2. Seed Products
        products_data = [
            {
                "sku": "ELEC-MOUSE",
                "name": "Wireless Ergonomic Mouse",
                "category": "ELECTRONICS",
                "length": Decimal("12.0"),
                "width": Decimal("7.5"),
                "height": Decimal("4.5"),
                "weight": Decimal("0.22"),
                "is_fragile": False,
                "keep_upright": False,
            },
            {
                "sku": "ELEC-KBD",
                "name": "RGB Mechanical Keyboard",
                "category": "ELECTRONICS",
                "length": Decimal("36.0"),
                "width": Decimal("14.0"),
                "height": Decimal("4.0"),
                "weight": Decimal("1.10"),
                "is_fragile": False,
                "keep_upright": False,
            },
            {
                "sku": "ELEC-HDPHN",
                "name": "Noise Cancelling Headphones",
                "category": "ELECTRONICS",
                "length": Decimal("20.0"),
                "width": Decimal("18.0"),
                "height": Decimal("8.5"),
                "weight": Decimal("0.55"),
                "is_fragile": True,
                "keep_upright": False,
            },
            {
                "sku": "GLASS-MUG",
                "name": "Ceramic Artisan Coffee Mug",
                "category": "GLASSWARE",
                "length": Decimal("12.0"),
                "width": Decimal("10.0"),
                "height": Decimal("11.0"),
                "weight": Decimal("0.45"),
                "is_fragile": True,
                "keep_upright": False,
            },
            {
                "sku": "GLASS-WINE",
                "name": "Crystal Wine Glasses (Set of 2)",
                "category": "GLASSWARE",
                "length": Decimal("24.0"),
                "width": Decimal("16.0"),
                "height": Decimal("25.0"),
                "weight": Decimal("0.85"),
                "is_fragile": True,
                "keep_upright": True,
            },
            {
                "sku": "BOOK-PYTHON",
                "name": "Designing Data-Intensive Applications",
                "category": "BOOKS",
                "length": Decimal("23.5"),
                "width": Decimal("18.0"),
                "height": Decimal("3.2"),
                "weight": Decimal("0.95"),
                "is_fragile": False,
                "keep_upright": False,
            },
            {
                "sku": "APP-SHOES",
                "name": "Pro Running Shoes (Boxed)",
                "category": "APPAREL",
                "length": Decimal("32.0"),
                "width": Decimal("21.0"),
                "height": Decimal("12.0"),
                "weight": Decimal("1.25"),
                "is_fragile": False,
                "keep_upright": False,
            },
            {
                "sku": "HOME-OIL",
                "name": "Extra Virgin Olive Oil 750ml",
                "category": "HOME",
                "length": Decimal("8.5"),
                "width": Decimal("8.5"),
                "height": Decimal("30.0"),
                "weight": Decimal("1.35"),
                "is_fragile": True,
                "keep_upright": True,
            },
            {
                "sku": "ELEC-STAND",
                "name": "Aluminum Laptop Riser Stand",
                "category": "ELECTRONICS",
                "length": Decimal("27.0"),
                "width": Decimal("24.0"),
                "height": Decimal("5.0"),
                "weight": Decimal("0.78"),
                "is_fragile": False,
                "keep_upright": False,
            },
            {
                "sku": "FIT-DUMBBELL",
                "name": "Cast Iron Kettlebell 16kg",
                "category": "OTHER",
                "length": Decimal("22.0"),
                "width": Decimal("22.0"),
                "height": Decimal("28.0"),
                "weight": Decimal("16.00"),
                "is_fragile": False,
                "keep_upright": False,
            },
        ]

        created_prods = {}
        for p in products_data:
            prod_obj, _ = Product.objects.update_or_create(sku=p["sku"], defaults=p)
            created_prods[p["sku"]] = prod_obj
            self.stdout.write(f"  Product: [{prod_obj.sku}] {prod_obj.name}")

        # 3. Seed Sample Orders
        orders_data = [
            {
                "order_number": "ORD-101",
                "customer_name": "Alice Morgan",
                "customer_email": "alice@example.com",
                "status": "PENDING",
                "notes": "Standard delivery - single compact electronic item.",
                "items": [
                    ("ELEC-MOUSE", 1),
                ]
            },
            {
                "order_number": "ORD-102",
                "customer_name": "Brian Chen",
                "customer_email": "brian@example.com",
                "status": "PENDING",
                "notes": "Workstation setup bundle. Contains keyboard and book.",
                "items": [
                    ("ELEC-KBD", 1),
                    ("BOOK-PYTHON", 1),
                    ("ELEC-MOUSE", 1),
                ]
            },
            {
                "order_number": "ORD-103",
                "customer_name": "Chloe Vance",
                "customer_email": "chloe@example.com",
                "status": "PENDING",
                "notes": "Gift order with delicate glassware and headphones.",
                "items": [
                    ("GLASS-MUG", 2),
                    ("ELEC-HDPHN", 1),
                    ("HOME-OIL", 1),
                ]
            },
            {
                "order_number": "ORD-104",
                "customer_name": "David Miller",
                "customer_email": "david@example.com",
                "status": "PENDING",
                "notes": "Multiple bulky items: running shoes, laptop stand, keyboard, and book.",
                "items": [
                    ("APP-SHOES", 1),
                    ("ELEC-STAND", 1),
                    ("ELEC-KBD", 1),
                    ("BOOK-PYTHON", 1),
                ]
            },
            {
                "order_number": "ORD-105",
                "customer_name": "Elena Rostova",
                "customer_email": "elena@example.com",
                "status": "PENDING",
                "notes": "Heavy fitness load + multiple shoes (tests weight boundaries and potential multi-box).",
                "items": [
                    ("FIT-DUMBBELL", 1),
                    ("APP-SHOES", 2),
                    ("ELEC-KBD", 1),
                ]
            },
        ]

        for ord_data in orders_data:
            order_obj, _ = Order.objects.update_or_create(
                order_number=ord_data["order_number"],
                defaults={
                    "customer_name": ord_data["customer_name"],
                    "customer_email": ord_data["customer_email"],
                    "status": ord_data["status"],
                    "notes": ord_data["notes"],
                }
            )
            # Clear and re-add items
            order_obj.items.all().delete()
            for sku, qty in ord_data["items"]:
                OrderItem.objects.create(
                    order=order_obj,
                    product=created_prods[sku],
                    quantity=qty
                )
            self.stdout.write(f"  Order: #{order_obj.order_number} ({len(ord_data['items'])} lines)")

        self.stdout.write(self.style.SUCCESS("Database successfully seeded with realistic sample data!"))
