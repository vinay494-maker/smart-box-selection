from django.test import TestCase
from decimal import Decimal
from packing.models import Box, Product, Order, OrderItem
from packing.services.box_recommender import BoxRecommender


class BoxRecommenderTestCase(TestCase):
    def setUp(self):
        # Create boxes with different sizes and costs
        self.box_xs = Box.objects.create(
            code="B-XS", name="XS Mailer",
            inner_length=Decimal("20.0"), inner_width=Decimal("15.0"), inner_height=Decimal("5.0"),
            max_weight=Decimal("1.5"), cost=Decimal("0.50"), is_active=True
        )
        self.box_s = Box.objects.create(
            code="B-S", name="Small Box",
            inner_length=Decimal("25.0"), inner_width=Decimal("20.0"), inner_height=Decimal("12.0"),
            max_weight=Decimal("5.0"), cost=Decimal("1.20"), is_active=True
        )
        self.box_m = Box.objects.create(
            code="B-M", name="Medium Box",
            inner_length=Decimal("35.0"), inner_width=Decimal("28.0"), inner_height=Decimal("20.0"),
            max_weight=Decimal("12.0"), cost=Decimal("2.50"), is_active=True
        )

        # Create products
        self.mouse = Product.objects.create(
            sku="M-01", name="Mouse", category="ELECTRONICS",
            length=Decimal("10.0"), width=Decimal("6.0"), height=Decimal("4.0"),
            weight=Decimal("0.2"), is_fragile=False
        )
        self.keyboard = Product.objects.create(
            sku="K-01", name="Keyboard", category="ELECTRONICS",
            length=Decimal("32.0"), width=Decimal("14.0"), height=Decimal("4.0"),
            weight=Decimal("1.0"), is_fragile=False
        )
        self.heavy_load = Product.objects.create(
            sku="H-01", name="Heavy Block", category="OTHER",
            length=Decimal("15.0"), width=Decimal("15.0"), height=Decimal("15.0"),
            weight=Decimal("15.0"), is_fragile=False
        )

    def test_cheapest_box_selected_for_small_item(self):
        # Mouse should fit in XS Mailer ($0.50), not unnecessarily in Small ($1.20) or Medium ($2.50)
        items = [{
            "sku": self.mouse.sku, "name": self.mouse.name,
            "length": float(self.mouse.length), "width": float(self.mouse.width), "height": float(self.mouse.height),
            "weight": float(self.mouse.weight), "quantity": 1
        }]
        res = BoxRecommender.recommend_for_items(items)
        self.assertTrue(res['success'])
        self.assertEqual(res['boxes'][0]['box_code'], "B-XS")
        self.assertEqual(res['total_cost'], 0.50)
        self.assertFalse(res['is_multi_box'])

    def test_cheaper_box_rejected_when_item_too_large(self):
        # Keyboard length (32cm) > XS box (20cm) and Small box (25cm).
        # Must choose Medium Box (35cm) despite higher cost ($2.50)
        items = [{
            "sku": self.keyboard.sku, "name": self.keyboard.name,
            "length": float(self.keyboard.length), "width": float(self.keyboard.width), "height": float(self.keyboard.height),
            "weight": float(self.keyboard.weight), "quantity": 1
        }]
        res = BoxRecommender.recommend_for_items(items)
        self.assertTrue(res['success'])
        self.assertEqual(res['boxes'][0]['box_code'], "B-M")
        self.assertEqual(res['total_cost'], 2.50)
        
        # Verify AI insights explain the decision
        ai = res['ai_insights']
        self.assertIn("ai_executive_summary", ai)
        self.assertIn("void_fill", ai)

    def test_order_recommendation_persists_to_db(self):
        order = Order.objects.create(order_number="ORD-TEST-1", customer_name="Test User")
        OrderItem.objects.create(order=order, product=self.mouse, quantity=2)

        res = BoxRecommender.recommend_for_order(order.id, save_to_db=True)
        self.assertTrue(res['success'])

        # Check DB records
        self.assertEqual(order.recommendations.count(), 1)
        rec = order.recommendations.first()
        self.assertEqual(rec.packed_boxes.count(), 1)
        packed_box = rec.packed_boxes.first()
        self.assertEqual(packed_box.placements.count(), 2)

    def test_multi_box_partition_when_weight_exceeds_single_box(self):
        # 2 heavy blocks of 8kg each: total 16kg > Medium box limit of 12kg
        items = [
            {"sku": "HB-1", "name": "Heavy 1", "length": 15.0, "width": 15.0, "height": 10.0, "weight": 8.0, "quantity": 1},
            {"sku": "HB-2", "name": "Heavy 2", "length": 15.0, "width": 15.0, "height": 10.0, "weight": 8.0, "quantity": 1},
        ]
        res = BoxRecommender.recommend_for_items(items)
        self.assertTrue(res['success'])
        self.assertTrue(res['is_multi_box'])
        self.assertEqual(res['total_boxes'], 2)
