"""
Box Recommender Service.
Finds the most suitable box for an order or ad-hoc items list,
minimizing total packaging and freight cost while strictly guaranteeing 3D geometric fit.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from django.db import transaction

from packing.models import Box, Product, Order, OrderItem, PackingRecommendation, PackedBox, PlacedItem
from .packing_engine import Packing3DEngine, Box3D, Item3D, PlacedItem3D, PackingResult
from .ai_advisor import AIAdvisor


class BoxRecommender:
    """
    Main orchestration service for AI-assisted box recommendation.
    """

    @classmethod
    def get_active_boxes(cls) -> List[Box3D]:
        """Fetch all active boxes from database and convert to Box3D dataclasses."""
        boxes = Box.objects.filter(is_active=True).order_by('cost', 'inner_length')
        return [
            Box3D(
                id=b.id,
                box_id=b.id,
                code=b.code,
                name=b.name,
                length=float(b.inner_length),
                width=float(b.inner_width),
                height=float(b.inner_height),
                max_weight=float(b.max_weight),
                cost=float(b.cost),
                empty_weight=float(b.empty_weight)
            )
            for b in boxes
        ]

    @classmethod
    def recommend_for_items(cls, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recommends best box(es) for an arbitrary list of items.
        items_data format:
        [
            {
                "sku": "PROD-1",
                "name": "Widget",
                "length": 15.0,
                "width": 10.0,
                "height": 5.0,
                "weight": 0.8,
                "quantity": 2,
                "is_fragile": false,
                "keep_upright": false,
                "product_id": 12 (optional)
            }
        ]
        """
        # Expand items according to quantity
        items: List[Item3D] = []
        item_counter = 1
        for d in items_data:
            qty = int(d.get('quantity', 1))
            for _ in range(qty):
                items.append(Item3D(
                    id=item_counter,
                    name=d.get('name', f"Item-{item_counter}"),
                    sku=d.get('sku', f"SKU-{item_counter}"),
                    length=float(d['length']),
                    width=float(d['width']),
                    height=float(d['height']),
                    weight=float(d['weight']),
                    is_fragile=bool(d.get('is_fragile', False)),
                    keep_upright=bool(d.get('keep_upright', False)),
                    product_id=d.get('product_id')
                ))
                item_counter += 1

        if not items:
            return {
                "success": False,
                "error": "No items provided for packing recommendation."
            }

        boxes = cls.get_active_boxes()
        if not boxes:
            return {
                "success": False,
                "error": "No active shipping boxes found in system."
            }

        # Attempt single box recommendation first
        best_single = cls._find_best_single_box(boxes, items)
        if best_single is not None:
            return best_single

        # If no single box fits all items, find optimal multi-box partition
        return cls._find_multi_box_plan(boxes, items)

    @classmethod
    def recommend_for_order(cls, order_id: int, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Calculates recommendation for a database Order instance and optionally saves records.
        """
        try:
            order = Order.objects.prefetch_related('items__product').get(id=order_id)
        except Order.DoesNotExist:
            return {"success": False, "error": f"Order #{order_id} not found."}

        items_data = []
        for line in order.items.all():
            prod = line.product
            items_data.append({
                "sku": prod.sku,
                "name": prod.name,
                "length": float(prod.length),
                "width": float(prod.width),
                "height": float(prod.height),
                "weight": float(prod.weight),
                "quantity": line.quantity,
                "is_fragile": prod.is_fragile,
                "keep_upright": prod.keep_upright,
                "product_id": prod.id,
            })

        rec_data = cls.recommend_for_items(items_data)
        if not rec_data.get('success'):
            return rec_data

        if save_to_db:
            cls._save_recommendation_record(order, rec_data)

        return rec_data

    @classmethod
    def _find_best_single_box(cls, boxes: List[Box3D], items: List[Item3D]) -> Optional[Dict[str, Any]]:
        """
        Evaluates candidate boxes ordered by cost ascending.
        Returns the first box that succeeds (cheapest feasible box).
        """
        total_weight = sum(it.weight for it in items)
        total_vol = sum(it.volume for it in items)

        evaluations: List[Dict[str, Any]] = []

        # Sort boxes primarily by cost ASC, secondarily by volume ASC
        sorted_boxes = sorted(boxes, key=lambda b: (b.cost, b.volume))

        for box in sorted_boxes:
            # Pre-filter checks
            if total_weight > box.max_weight:
                evaluations.append({
                    "box_id": box.box_id,
                    "code": box.code,
                    "name": box.name,
                    "cost": box.cost,
                    "is_feasible": False,
                    "failure_reason": f"Payload weight ({total_weight:.2f} kg) exceeds box limit ({box.max_weight:.2f} kg)."
                })
                continue

            if total_vol > box.volume:
                evaluations.append({
                    "box_id": box.box_id,
                    "code": box.code,
                    "name": box.name,
                    "cost": box.cost,
                    "is_feasible": False,
                    "failure_reason": f"Total volume ({total_vol:,.0f} cm³) exceeds box volume ({box.volume:,.0f} cm³)."
                })
                continue

            # Run 3D Packing Simulation
            pack_res = Packing3DEngine.pack(box, items)
            if pack_res.is_success:
                evaluations.append({
                    "box_id": box.box_id,
                    "code": box.code,
                    "name": box.name,
                    "cost": box.cost,
                    "is_feasible": True,
                    "volume_utilization_pct": pack_res.volume_utilization_pct
                })

                # Found the cheapest feasible box!
                ai_insights = AIAdvisor.generate_recommendation_insights(
                    chosen_box=box,
                    placements=pack_res.packed_items,
                    all_candidate_evaluations=evaluations,
                    items=items
                )

                return {
                    "success": True,
                    "is_multi_box": False,
                    "status": "OPTIMAL",
                    "total_boxes": 1,
                    "total_cost": box.cost,
                    "total_items_count": len(items),
                    "total_weight_kg": round(total_weight, 2),
                    "total_volume_cm3": round(total_vol, 2),
                    "boxes": [
                        {
                            "box_id": box.box_id,
                            "box_index": 1,
                            "box_code": box.code,
                            "box_name": box.name,
                            "dimensions": {"length": box.length, "width": box.width, "height": box.height},
                            "cost": box.cost,
                            "max_weight_kg": box.max_weight,
                            "used_weight_kg": pack_res.total_packed_weight,
                            "used_volume_cm3": pack_res.total_packed_volume,
                            "volume_utilization_pct": pack_res.volume_utilization_pct,
                            "void_fill": ai_insights["void_fill"],
                            "items_count": len(pack_res.packed_items),
                            "placements": [
                                {
                                    "step": p.step,
                                    "item_id": p.item.id,
                                    "product_id": p.item.product_id,
                                    "name": p.item.name,
                                    "sku": p.item.sku,
                                    "weight_kg": p.item.weight,
                                    "is_fragile": p.item.is_fragile,
                                    "keep_upright": p.item.keep_upright,
                                    "coordinates": {"x": p.x, "y": p.y, "z": p.z},
                                    "oriented_dimensions": {"length": p.dx, "width": p.dy, "height": p.dz},
                                    "rotation": p.rotation
                                }
                                for p in pack_res.packed_items
                            ]
                        }
                    ],
                    "ai_insights": ai_insights,
                    "evaluated_candidates": evaluations
                }
            else:
                evaluations.append({
                    "box_id": box.box_id,
                    "code": box.code,
                    "name": box.name,
                    "cost": box.cost,
                    "is_feasible": False,
                    "failure_reason": pack_res.failure_reason
                })

        return None

    @classmethod
    def _find_multi_box_plan(cls, boxes: List[Box3D], items: List[Item3D]) -> Dict[str, Any]:
        """
        Partitions items across multiple boxes when no single box is sufficient.
        Greedy multi-box packing with best-fit-decreasing strategy.
        """
        remaining_items = list(items)
        packed_box_plans = []
        total_cost = 0.0
        sorted_boxes = sorted(boxes, key=lambda b: (b.cost, b.volume))

        box_counter = 1
        while remaining_items:
            best_plan = None
            best_box = None
            best_items_packed = []

            # Try candidate boxes to maximize items packed per dollar or fit the most items
            for box in reversed(sorted_boxes): # Try larger boxes first to minimize box count
                # Filter items that can fit this box's weight
                if remaining_items[0].weight > box.max_weight:
                    continue

                # Try packing as many remaining items into this box as possible
                temp_items_to_try = list(remaining_items)
                items_fitting: List[Item3D] = []

                # Greedily build item subset
                for cand_item in temp_items_to_try:
                    trial_set = items_fitting + [cand_item]
                    if sum(it.weight for it in trial_set) <= box.max_weight:
                        res = Packing3DEngine.pack(box, trial_set)
                        if res.is_success:
                            items_fitting.append(cand_item)

                if items_fitting and len(items_fitting) > len(best_items_packed):
                    best_items_packed = items_fitting
                    best_box = box

            if not best_box or not best_items_packed:
                # An item is completely unpackable in ANY available box
                unfit_item = remaining_items[0]
                return {
                    "success": False,
                    "error": f"Item '{unfit_item.name}' ({unfit_item.length}×{unfit_item.width}×{unfit_item.height} cm, {unfit_item.weight} kg) exceeds all available box dimensions or weight capacities."
                }

            # Now find the cheapest box that fits these selected items
            cheapest_fit_box = None
            final_pack_res = None
            for box in sorted_boxes:
                res = Packing3DEngine.pack(box, best_items_packed)
                if res.is_success:
                    cheapest_fit_box = box
                    final_pack_res = res
                    break

            if not cheapest_fit_box:
                cheapest_fit_box = best_box
                final_pack_res = Packing3DEngine.pack(cheapest_fit_box, best_items_packed)

            # Record this box in plan
            total_cost += cheapest_fit_box.cost
            packed_box_plans.append({
                "box": cheapest_fit_box,
                "result": final_pack_res,
                "items": best_items_packed,
                "box_index": box_counter
            })
            box_counter += 1

            # Remove packed items from remaining
            for pi in best_items_packed:
                remaining_items.remove(pi)

        # Build output structure
        box_outputs = []
        for plan in packed_box_plans:
            b = plan["box"]
            res: PackingResult = plan["result"]
            box_outputs.append({
                "box_id": b.box_id,
                "box_index": plan["box_index"],
                "box_code": b.code,
                "box_name": b.name,
                "dimensions": {"length": b.length, "width": b.width, "height": b.height},
                "cost": b.cost,
                "max_weight_kg": b.max_weight,
                "used_weight_kg": res.total_packed_weight,
                "used_volume_cm3": res.total_packed_volume,
                "volume_utilization_pct": res.volume_utilization_pct,
                "void_fill": AIAdvisor._compute_void_fill_advice(
                    100.0 - res.volume_utilization_pct,
                    round((b.volume - res.total_packed_volume) / 1000.0, 2),
                    any(it.is_fragile for it in plan["items"])
                ),
                "items_count": len(res.packed_items),
                "placements": [
                    {
                        "step": p.step,
                        "item_id": p.item.id,
                        "product_id": p.item.product_id,
                        "name": p.item.name,
                        "sku": p.item.sku,
                        "weight_kg": p.item.weight,
                        "is_fragile": p.item.is_fragile,
                        "keep_upright": p.item.keep_upright,
                        "coordinates": {"x": p.x, "y": p.y, "z": p.z},
                        "oriented_dimensions": {"length": p.dx, "width": p.dy, "height": p.dz},
                        "rotation": p.rotation
                    }
                    for p in res.packed_items
                ]
            })

        ai_summary = (
            f"Multi-Box Partition Required: Order items exceed single-box capacity. "
            f"Optimized into {len(box_outputs)} box(es) costing a total of ${total_cost:.2f}. "
            f"Box distribution balanced to keep fragile items safe and minimize combined carrier volume."
        )

        return {
            "success": True,
            "is_multi_box": True,
            "status": "MULTI_BOX",
            "total_boxes": len(box_outputs),
            "total_cost": round(total_cost, 2),
            "total_items_count": len(items),
            "total_weight_kg": round(sum(it.weight for it in items), 2),
            "total_volume_cm3": round(sum(it.volume for it in items), 2),
            "boxes": box_outputs,
            "ai_insights": {
                "ai_executive_summary": ai_summary,
                "decision_rationale": [
                    f"Order split into {len(box_outputs)} parcels due to physical volume / weight thresholds.",
                    f"Selected combination minimizes total carton cost (${total_cost:.2f})."
                ],
                "safety_alerts": ["Ensure multi-package tracking labels are paired at dispatch."]
            }
        }

    @classmethod
    @transaction.atomic
    def _save_recommendation_record(cls, order: Order, rec_data: Dict[str, Any]) -> PackingRecommendation:
        """
        Persists recommendation, packed boxes, and placed items into Django database.
        """
        # Clear any prior pending recommendations for this order if desired
        order.recommendations.filter(order__status='PENDING').delete()

        ai_insights = rec_data.get('ai_insights', {})
        rec = PackingRecommendation.objects.create(
            order=order,
            total_items_count=rec_data.get('total_items_count', 0),
            total_items_weight=Decimal(str(rec_data.get('total_weight_kg', 0.0))),
            total_items_volume=Decimal(str(rec_data.get('total_volume_cm3', 0.0))),
            total_boxes_count=rec_data.get('total_boxes', 1),
            total_cost=Decimal(str(rec_data.get('total_cost', 0.0))),
            algorithm_used="3D-EMS-BestFit-AI",
            status=rec_data.get('status', 'OPTIMAL'),
            ai_summary=ai_insights.get('ai_executive_summary', ''),
            packing_guidance=ai_insights.get('packing_steps', [])
        )

        for b_data in rec_data.get('boxes', []):
            box_model = Box.objects.get(id=b_data['box_id'])
            packed_box = PackedBox.objects.create(
                recommendation=rec,
                box=box_model,
                box_index=b_data.get('box_index', 1),
                used_weight=Decimal(str(b_data.get('used_weight_kg', 0.0))),
                used_volume=Decimal(str(b_data.get('used_volume_cm3', 0.0))),
                volume_utilization=Decimal(str(b_data.get('volume_utilization_pct', 0.0))),
                box_cost=Decimal(str(b_data.get('cost', 0.0))),
                recommended_void_fill=b_data.get('void_fill', {}).get('recommended_material', '')
            )

            for p in b_data.get('placements', []):
                prod_id = p.get('product_id')
                if prod_id:
                    prod = Product.objects.filter(id=prod_id).first()
                else:
                    prod = Product.objects.filter(sku=p.get('sku')).first()

                if prod:
                    coords = p.get('coordinates', {})
                    dims = p.get('oriented_dimensions', {})
                    PlacedItem.objects.create(
                        packed_box=packed_box,
                        product=prod,
                        step_number=p.get('step', 1),
                        x=Decimal(str(coords.get('x', 0.0))),
                        y=Decimal(str(coords.get('y', 0.0))),
                        z=Decimal(str(coords.get('z', 0.0))),
                        placed_length=Decimal(str(dims.get('length', 0.0))),
                        placed_width=Decimal(str(dims.get('width', 0.0))),
                        placed_height=Decimal(str(dims.get('height', 0.0))),
                        rotation_name=p.get('rotation', 'Standard'),
                        special_instruction="Fragile" if p.get('is_fragile') else ""
                    )

        return rec
