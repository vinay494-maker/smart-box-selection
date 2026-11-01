from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from packing.models import Box, Product, Order, OrderItem


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.box = Box.objects.create(
            code="B-TEST", name="Test Box",
            inner_length=Decimal("30.0"), inner_width=Decimal("20.0"), inner_height=Decimal("15.0"),
            max_weight=Decimal("5.0"), cost=Decimal("1.50")
        )
        self.product = Product.objects.create(
            sku="P-TEST", name="Test Product", category="ELECTRONICS",
            length=Decimal("10.0"), width=Decimal("10.0"), height=Decimal("5.0"),
            weight=Decimal("0.5")
        )
        self.order = Order.objects.create(
            order_number="ORD-V-01", customer_name="View Tester"
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def test_dashboard_view_status_code(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Packing Station")
        self.assertContains(response, "ORD-V-01")

    def test_boxes_view_status_code(self):
        response = self.client.get(reverse('boxes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "B-TEST")

    def test_products_view_status_code(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "P-TEST")

    def test_orders_view_status_code(self):
        response = self.client.get(reverse('orders'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ORD-V-01")
