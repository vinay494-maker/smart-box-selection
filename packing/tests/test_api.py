from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from packing.models import Box, Product, Order, OrderItem


class PackingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.box = Box.objects.create(
            code="BOX-STD", name="Standard Box",
            inner_length=Decimal("30.0"), inner_width=Decimal("20.0"), inner_height=Decimal("15.0"),
            max_weight=Decimal("5.0"), cost=Decimal("1.50"), is_active=True
        )

        self.product = Product.objects.create(
            sku="ITEM-01", name="Gadget", category="ELECTRONICS",
            length=Decimal("10.0"), width=Decimal("8.0"), height=Decimal("5.0"),
            weight=Decimal("0.5")
        )

        self.order = Order.objects.create(
            order_number="ORD-API-99", customer_name="API Customer"
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)

    def test_get_boxes_api(self):
        response = self.client.get('/api/boxes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], 'BOX-STD')

    def test_get_products_api(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], 'ITEM-01')

    def test_recommend_box_for_order_api(self):
        payload = {"order_id": self.order.id}
        response = self.client.post('/api/recommend-box/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertTrue(data['success'])
        self.assertEqual(data['total_boxes'], 1)
        self.assertEqual(data['boxes'][0]['box_code'], 'BOX-STD')
        self.assertIn('ai_insights', data)
        self.assertIn('placements', data['boxes'][0])

    def test_recommend_box_for_adhoc_items_api(self):
        payload = {
            "items": [
                {
                    "sku": "CUSTOM-1",
                    "name": "Custom Product",
                    "length": 12.0,
                    "width": 10.0,
                    "height": 6.0,
                    "weight": 0.8,
                    "quantity": 1
                }
            ]
        }
        response = self.client.post('/api/recommend-box/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertTrue(data['success'])
        self.assertEqual(data['boxes'][0]['box_code'], 'BOX-STD')

    def test_order_mark_packed_action(self):
        url = f'/api/orders/{self.order.id}/mark-packed/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PACKED')
