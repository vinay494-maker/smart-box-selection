"""
AI-Assisted Packing Advisor.
Provides intelligent reasoning, void fill recommendations, carrier freight analysis,
hazard/fragility safeguards, and warehouse packing manifest instructions.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from .packing_engine import Box3D, Item3D, PlacedItem3D, PackingResult


class AIAdvisor:
    """
    AI-driven advisory system for warehouse packaging optimization.
    """

    @classmethod
    def generate_recommendation_insights(
        cls,
        chosen_box: Box3D,
        placements: List[PlacedItem3D],
        all_candidate_evaluations: List[Dict[str, Any]],
        items: List[Item3D]
    ) -> Dict[str, Any]:
        """
        Synthesizes complete AI reasoning and operational guidance.
        """
        total_weight = sum(it.weight for it in items)
        total_vol = sum(it.volume for it in items)
        box_vol = chosen_box.volume
        vol_utilization = (total_vol / box_vol * 100.0) if box_vol > 0 else 0.0
        void_vol_cm3 = max(0.0, box_vol - total_vol)
        void_vol_liters = round(void_vol_cm3 / 1000.0, 2)
        void_ratio_pct = max(0.0, 100.0 - vol_utilization)

        # 1. Dimensional weight / Carrier Freight analysis
        carrier_volumetric_weight = round(box_vol / 5000.0, 2)
        billable_weight = max(round(total_weight + chosen_box.empty_weight, 2), carrier_volumetric_weight)
        is_dim_weight_dominant = carrier_volumetric_weight > (total_weight + chosen_box.empty_weight)

        # 2. Void fill & Cushioning recommendation
        has_fragile = any(it.is_fragile for it in items)
        void_fill_advice = cls._compute_void_fill_advice(void_ratio_pct, void_vol_liters, has_fragile)

        # 3. Decision Rationale (Why this box?)
        decision_rationale = cls._generate_rationale(
            chosen_box=chosen_box,
            candidates=all_candidate_evaluations,
            total_weight=total_weight,
            vol_utilization=vol_utilization,
            items_count=len(items)
        )

        # 4. Warehouse Step-by-Step Packing Manifest
        packing_steps = cls._generate_packing_manifest(placements)

        # 5. Safety & Handling Alerts
        safety_alerts = cls._generate_safety_alerts(placements, items)

        # 6. Comprehensive AI Executive Summary
        executive_summary = (
            f"AI Recommendation: {chosen_box.name} ({chosen_box.code}) selected. "
            f"Achieves {vol_utilization:.1f}% volume utilization with payload of {total_weight:.2f} kg "
            f"(Box limit: {chosen_box.max_weight:.1f} kg). "
            f"Packaging cost: ${chosen_box.cost:.2f}. "
            f"Estimated void volume: {void_vol_liters} L. "
            f"{void_fill_advice['summary']}"
        )

        return {
            "box_code": chosen_box.code,
            "box_name": chosen_box.name,
            "cost": float(chosen_box.cost),
            "volume_utilization_pct": round(vol_utilization, 2),
            "void_ratio_pct": round(void_ratio_pct, 2),
            "void_volume_liters": void_vol_liters,
            "actual_total_weight_kg": round(total_weight, 2),
            "carrier_volumetric_weight_kg": carrier_volumetric_weight,
            "billable_weight_kg": billable_weight,
            "is_dim_weight_dominant": is_dim_weight_dominant,
            "void_fill": void_fill_advice,
            "decision_rationale": decision_rationale,
            "packing_steps": packing_steps,
            "safety_alerts": safety_alerts,
            "ai_executive_summary": executive_summary,
        }

    @staticmethod
    def _compute_void_fill_advice(void_ratio_pct: float, void_vol_liters: float, has_fragile: bool) -> Dict[str, Any]:
        """
        Determines appropriate void fill material and quantity.
        """
        if void_ratio_pct < 15.0:
            material = "Kraft Paper Liners / Minimal Cushioning"
            summary = "Tight space fit (< 15% void). Line edges with thin kraft paper."
            cushion_rating = "Light"
        elif void_ratio_pct <= 35.0:
            if has_fragile:
                material = "Bubble Wrap + Recycled Air Pillows"
                summary = f"Moderate void ({void_vol_liters} L). Wrap fragile units in 2-ply bubble wrap and fill top void with air pillows."
                cushion_rating = "Medium-High"
            else:
                material = "Standard Biodegradable Air Pillows"
                summary = f"Moderate void ({void_vol_liters} L). Fill top void with 2-4 air pillow pouches to prevent transit shifting."
                cushion_rating = "Medium"
        else:
            if has_fragile:
                material = "Heavy-Duty Bubble Wrap + Expanding Foam Bags / Honeycomb Paper"
                summary = f"High void space ({void_vol_liters} L / {void_ratio_pct:.0f}%). Intensive padding mandatory to absorb drops."
                cushion_rating = "Maximum Protection"
            else:
                material = "Recycled Kraft Crinkle Paper or Molded Pulp Inserts"
                summary = f"Spacious void ({void_vol_liters} L). Dense paper fill recommended to stabilize heavy payload."
                cushion_rating = "Substantial Fill"

        return {
            "recommended_material": material,
            "void_ratio_pct": void_ratio_pct,
            "void_liters": void_vol_liters,
            "summary": summary,
            "cushion_rating": cushion_rating
        }

    @staticmethod
    def _generate_rationale(
        chosen_box: Box3D,
        candidates: List[Dict[str, Any]],
        total_weight: float,
        vol_utilization: float,
        items_count: int
    ) -> List[str]:
        """
        Explains why this box won against alternatives.
        """
        rationale = []

        # Why chosen
        rationale.append(
            f"Selected '{chosen_box.name}' as the lowest-cost option (${chosen_box.cost:.2f}) "
            f"that physically accommodates all {items_count} item(s) without exceeding the "
            f"{chosen_box.max_weight:.1f} kg weight threshold."
        )

        cheaper_rejected = [c for c in candidates if c['cost'] < chosen_box.cost]
        for rej in cheaper_rejected:
            reason = rej.get('failure_reason', 'Geometric 3D placement failed.')
            rationale.append(f"Excluded cheaper box '{rej['name']}' (${rej['cost']:.2f}): {reason}")

        more_expensive_bypassed = [c for c in candidates if c['cost'] > chosen_box.cost and c.get('is_feasible')]
        if more_expensive_bypassed:
            min_exp = more_expensive_bypassed[0]
            cost_diff = min_exp['cost'] - chosen_box.cost
            rationale.append(
                f"Bypassed larger '{min_exp['name']}' (${min_exp['cost']:.2f}) saving ${cost_diff:.2f} per order "
                f"and avoiding unnecessary dimensional freight surcharges."
            )

        return rationale

    @staticmethod
    def _generate_packing_manifest(placements: List[PlacedItem3D]) -> List[Dict[str, Any]]:
        """
        Converts 3D coordinates into step-by-step warehouse packer instructions.
        """
        steps = []
        for idx, p in enumerate(placements, start=1):
            pos_desc = []
            if p.z == 0:
                pos_desc.append("at box base")
            else:
                pos_desc.append(f"stacked at height {p.z:.1f} cm")

            if p.x == 0 and p.y == 0:
                pos_desc.append("flush with front-left corner")
            else:
                pos_desc.append(f"at position (X: {p.x:.1f} cm, Y: {p.y:.1f} cm)")

            note = ""
            if p.item.is_fragile:
                note = "FRAGILE: Wrap in protective film before placement; do not place heavy loads on top."
            elif p.item.keep_upright:
                note = "UPRIGHT ONLY: Maintain vertical orientation (arrows pointing up)."

            steps.append({
                "step": idx,
                "item_name": p.item.name,
                "sku": p.item.sku,
                "weight_kg": p.item.weight,
                "placement_coords": {"x": p.x, "y": p.y, "z": p.z},
                "oriented_dimensions": {"length": p.dx, "width": p.dy, "height": p.dz},
                "rotation": p.rotation,
                "location_description": f"Place {', '.join(pos_desc)}.",
                "handling_note": note,
                "is_fragile": p.item.is_fragile
            })
        return steps

    @staticmethod
    def _generate_safety_alerts(placements: List[PlacedItem3D], items: List[Item3D]) -> List[str]:
        """
        Identifies potential safety or handling risks.
        """
        alerts = []
        fragile_items = [p for p in placements if p.item.is_fragile]
        upright_items = [p for p in placements if p.item.keep_upright]

        if fragile_items:
            # Check if any non-fragile item is stacked above a fragile item
            for frag in fragile_items:
                for other in placements:
                    if not other.item.is_fragile and other.z > frag.z:
                        # Check horizontal overlap
                        if not (other.x2 <= frag.x or other.x >= frag.x2 or
                                other.y2 <= frag.y or other.y >= frag.y2):
                            alerts.append(
                                f"Warning: '{other.item.name}' ({other.item.weight} kg) is resting on top of "
                                f"fragile item '{frag.item.name}'. Add rigid divider or adjust packing order."
                            )

        if upright_items:
            for up in upright_items:
                alerts.append(f"Orientation Notice: '{up.item.name}' must remain upright during sealing and transit.")

        # Center of gravity check
        total_w = sum(p.item.weight for p in placements)
        if total_w > 0:
            cg_z = sum(p.item.weight * (p.z + p.dz / 2.0) for p in placements) / total_w
            box_height = max((p.z + p.dz) for p in placements) if placements else 1.0
            if cg_z > (box_height * 0.65):
                alerts.append("Top-heavy load detected: Center of mass is in upper half of box. Handle with care.")

        return alerts
