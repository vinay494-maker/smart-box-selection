from django.test import TestCase
from packing.services.packing_engine import Packing3DEngine, Box3D, Item3D, PlacedItem3D


class Packing3DEngineTestCase(TestCase):
    def setUp(self):
        self.box_small = Box3D(
            id=1, code="B-SM", name="Small Box",
            length=25.0, width=20.0, height=12.0,
            max_weight=5.0, cost=1.20
        )
        self.box_medium = Box3D(
            id=2, code="B-MD", name="Medium Box",
            length=35.0, width=28.0, height=20.0,
            max_weight=10.0, cost=2.50
        )

    def test_single_item_fits(self):
        item = Item3D(
            id=1, name="Mouse", sku="M-1",
            length=12.0, width=7.0, height=4.0, weight=0.2
        )
        result = Packing3DEngine.pack(self.box_small, [item])
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.packed_items), 1)
        placement = result.packed_items[0]
        self.assertEqual(placement.x, 0.0)
        self.assertEqual(placement.y, 0.0)
        self.assertEqual(placement.z, 0.0)

    def test_weight_limit_exceeded(self):
        heavy_item = Item3D(
            id=1, name="Anvil", sku="ANV-1",
            length=10.0, width=10.0, height=10.0, weight=6.5 # Exceeds 5.0kg
        )
        result = Packing3DEngine.pack(self.box_small, [heavy_item])
        self.assertFalse(result.is_success)
        self.assertIn("exceeds box capacity", result.failure_reason)

    def test_volume_limit_exceeded(self):
        bulky_item = Item3D(
            id=1, name="Big Foam", sku="BF-1",
            length=25.0, width=20.0, height=15.0, weight=1.0 # 7500 cm³ > 6000 cm³
        )
        result = Packing3DEngine.pack(self.box_small, [bulky_item])
        self.assertFalse(result.is_success)
        self.assertIn("exceeds box volume", result.failure_reason)

    def test_item_too_long_for_box(self):
        long_rod = Item3D(
            id=1, name="Long Rod", sku="ROD-1",
            length=30.0, width=2.0, height=2.0, weight=0.5 # 30cm > 25cm
        )
        result = Packing3DEngine.pack(self.box_small, [long_rod])
        self.assertFalse(result.is_success)

    def test_rotation_allows_fit(self):
        # Box is 25 x 20 x 12
        # Item in original orientation: 18 x 22 x 5 (width 22 > box width 20)
        # But if rotated 90°: 22 x 18 x 5 (length 22 <= 25, width 18 <= 20) -> FITS!
        item = Item3D(
            id=1, name="Wide Tablet", sku="TAB-1",
            length=18.0, width=22.0, height=5.0, weight=0.8
        )
        result = Packing3DEngine.pack(self.box_small, [item])
        self.assertTrue(result.is_success)
        placement = result.packed_items[0]
        self.assertLessEqual(placement.dx, self.box_small.length)
        self.assertLessEqual(placement.dy, self.box_small.width)
        self.assertLessEqual(placement.dz, self.box_small.height)

    def test_keep_upright_constraint(self):
        # Box is 20 x 20 x 15 (Height is 15)
        # Bottle is 8 x 8 x 25.
        # Height 25 > Box height 15.
        # If rotation were allowed, it could lie flat (25 x 8 x 8, length 25 > 20 still, but let's test a box 30 x 15 x 10)
        box = Box3D(id=3, code="FLAT", name="Flat Box", length=30.0, width=20.0, height=10.0, max_weight=5.0, cost=1.0)
        bottle = Item3D(
            id=1, name="Liquid Bottle", sku="BOT-1",
            length=8.0, width=8.0, height=18.0, weight=1.0,
            keep_upright=True # Height 18cm must stay along Z; box height is only 10cm!
        )
        result = Packing3DEngine.pack(box, [bottle])
        # Since it cannot be tilted on its side, it must fail to fit
        self.assertFalse(result.is_success)

        # But if keep_upright is False, it can lie flat (18 x 8 x 8 fits in 30 x 20 x 10)!
        bottle_tilting = Item3D(
            id=2, name="Solid Tube", sku="TUB-1",
            length=8.0, width=8.0, height=18.0, weight=1.0,
            keep_upright=False
        )
        result_tilting = Packing3DEngine.pack(box, [bottle_tilting])
        self.assertTrue(result_tilting.is_success)

    def test_multiple_items_no_3d_overlap(self):
        items = [
            Item3D(id=1, name="Book 1", sku="B1", length=15.0, width=10.0, height=3.0, weight=0.5),
            Item3D(id=2, name="Book 2", sku="B2", length=15.0, width=10.0, height=3.0, weight=0.5),
            Item3D(id=3, name="Boxed Mouse", sku="M1", length=12.0, width=8.0, height=5.0, weight=0.3),
            Item3D(id=4, name="Charger", sku="C1", length=8.0, width=6.0, height=4.0, weight=0.2),
        ]
        result = Packing3DEngine.pack(self.box_small, items)
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.packed_items), 4)

        # Rigorous geometric overlap verification
        packed = result.packed_items
        for i in range(len(packed)):
            for j in range(i + 1, len(packed)):
                self.assertFalse(
                    packed[i].intersects(packed[j]),
                    f"Item {packed[i].item.name} overlaps with {packed[j].item.name}!"
                )
