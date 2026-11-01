"""
3D Bin Packing Engine using Maximal Empty Spaces (EMS) heuristic with 6-DOF rotation
and physical warehouse stability constraints.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import copy


@dataclass
class Item3D:
    id: Any
    name: str
    sku: str
    length: float  # cm (X)
    width: float   # cm (Y)
    height: float  # cm (Z)
    weight: float  # kg
    is_fragile: bool = False
    keep_upright: bool = False
    product_id: Optional[int] = None

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class PlacedItem3D:
    item: Item3D
    x: float
    y: float
    z: float
    dx: float  # Oriented length
    dy: float  # Oriented width
    dz: float  # Oriented height
    rotation: str
    step: int = 1

    @property
    def x2(self) -> float:
        return self.x + self.dx

    @property
    def y2(self) -> float:
        return self.y + self.dy

    @property
    def z2(self) -> float:
        return self.z + self.dz

    def intersects(self, other: 'PlacedItem3D') -> bool:
        """Check if 3D bounding boxes intersect (exclusive of touching borders)."""
        eps = 1e-4
        return not (
            self.x2 <= other.x + eps or self.x >= other.x2 - eps or
            self.y2 <= other.y + eps or self.y >= other.y2 - eps or
            self.z2 <= other.z + eps or self.z >= other.z2 - eps
        )


@dataclass
class EmptySpace:
    x: float
    y: float
    z: float
    lx: float
    ly: float
    lz: float

    @property
    def volume(self) -> float:
        return self.lx * self.ly * self.lz

    @property
    def x2(self) -> float:
        return self.x + self.lx

    @property
    def y2(self) -> float:
        return self.y + self.ly

    @property
    def z2(self) -> float:
        return self.z + self.lz

    def contains_space(self, other: 'EmptySpace') -> bool:
        """Check if this space completely envelopes another space."""
        eps = 1e-4
        return (
            self.x <= other.x + eps and self.x2 >= other.x2 - eps and
            self.y <= other.y + eps and self.y2 >= other.y2 - eps and
            self.z <= other.z + eps and self.z2 >= other.z2 - eps
        )


@dataclass
class Box3D:
    id: Any
    code: str
    name: str
    length: float  # cm
    width: float   # cm
    height: float  # cm
    max_weight: float  # kg
    cost: float        # USD / Currency
    empty_weight: float = 0.1
    box_id: Optional[int] = None

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class PackingResult:
    box: Box3D
    is_success: bool
    packed_items: List[PlacedItem3D] = field(default_factory=list)
    unpacked_items: List[Item3D] = field(default_factory=list)
    total_packed_weight: float = 0.0
    total_packed_volume: float = 0.0
    volume_utilization_pct: float = 0.0
    failure_reason: str = ""


class Packing3DEngine:
    """
    Solves 3D bin packing using Empty Maximal Spaces (EMS) heuristic.
    """

    @staticmethod
    def get_candidate_orientations(item: Item3D) -> List[Tuple[float, float, float, str]]:
        """
        Returns list of (dx, dy, dz, rotation_name).
        If item must be kept upright (e.g. liquids, delicate orientation), height (dz) cannot change.
        """
        l, w, h = item.length, item.width, item.height

        if item.keep_upright:
            # Only 2 rotations allowed: yaw around Z axis
            orientations = [
                (l, w, h, "Upright (L×W×H)"),
                (w, l, h, "Upright Rotated 90° (W×L×H)"),
            ]
        else:
            # All 6 3D orientations
            orientations = [
                (l, w, h, "Standard (L×W×H)"),
                (l, h, w, "On Side (L×H×W)"),
                (w, l, h, "Rotated 90° (W×L×H)"),
                (w, h, l, "Rotated on Side (W×H×L)"),
                (h, l, w, "Upright Flat (H×L×W)"),
                (h, w, l, "Upright Turned (H×W×L)"),
            ]

        # Deduplicate orientations (e.g. for cubes or identical dimensions)
        unique_orientations = []
        seen = set()
        for dx, dy, dz, name in orientations:
            dims = (round(dx, 2), round(dy, 2), round(dz, 2))
            if dims not in seen:
                seen.add(dims)
                unique_orientations.append((dx, dy, dz, name))

        return unique_orientations

    @classmethod
    def pack(cls, box: Box3D, items: List[Item3D]) -> PackingResult:
        """
        Attempts to pack the given list of items into the target box.
        Returns a PackingResult detailing placements and efficiency.
        """
        total_item_weight = sum(it.weight for it in items)
        total_item_volume = sum(it.volume for it in items)

        # Quick check 1: Weight limit
        if total_item_weight > box.max_weight:
            return PackingResult(
                box=box,
                is_success=False,
                unpacked_items=items,
                failure_reason=f"Total weight ({total_item_weight:.2f} kg) exceeds box capacity ({box.max_weight:.2f} kg)."
            )

        # Quick check 2: Volume limit
        if total_item_volume > box.volume:
            return PackingResult(
                box=box,
                is_success=False,
                unpacked_items=items,
                failure_reason=f"Total items volume ({total_item_volume:,.0f} cm³) exceeds box volume ({box.volume:,.0f} cm³)."
            )

        # Quick check 3: Any single item dimension exceeds box largest dimension
        box_max_dim = max(box.length, box.width, box.height)
        for it in items:
            it_min_dim = min(it.length, it.width, it.height)
            if it_min_dim > box_max_dim:
                return PackingResult(
                    box=box,
                    is_success=False,
                    unpacked_items=items,
                    failure_reason=f"Item '{it.name}' smallest dimension ({it_min_dim} cm) exceeds box maximum dimension ({box_max_dim} cm)."
                )

        # Sort items:
        # 1. Non-fragile first (fragile on top / later)
        # 2. Heavier first (base support)
        # 3. Larger volume first
        sorted_items = sorted(
            items,
            key=lambda it: (1 if it.is_fragile else 0, -it.weight, -it.volume)
        )

        free_spaces: List[EmptySpace] = [
            EmptySpace(x=0.0, y=0.0, z=0.0, lx=box.length, ly=box.width, lz=box.height)
        ]
        placed_items: List[PlacedItem3D] = []
        unpacked_items: List[Item3D] = []

        for step_idx, item in enumerate(sorted_items, start=1):
            orientations = cls.get_candidate_orientations(item)
            best_placement = None
            best_score = float('inf')
            best_space_idx = -1

            # Search available empty spaces
            for s_idx, space in enumerate(free_spaces):
                for dx, dy, dz, rot_name in orientations:
                    if dx <= space.lx + 1e-4 and dy <= space.ly + 1e-4 and dz <= space.lz + 1e-4:
                        # Candidate position
                        cand_x, cand_y, cand_z = space.x, space.y, space.z

                        # Scoring heuristic:
                        # 1. Primary: minimize Z coordinate (gravity/stability, items settle at bottom)
                        # 2. Secondary: minimize Y, then X (pack tightly towards corner)
                        # 3. Tertiary: minimize leftover unused volume in this space (Best-Fit)
                        leftover_vol = space.volume - (dx * dy * dz)
                        score = (cand_z * 100000.0) + (cand_y * 1000.0) + (cand_x * 10.0) + (leftover_vol / 1000.0)

                        if score < best_score:
                            best_score = score
                            best_placement = PlacedItem3D(
                                item=item,
                                x=cand_x,
                                y=cand_y,
                                z=cand_z,
                                dx=dx,
                                dy=dy,
                                dz=dz,
                                rotation=rot_name,
                                step=step_idx
                            )
                            best_space_idx = s_idx

            if best_placement is None:
                # Could not fit this item
                unpacked_items.append(item)
                # Early exit for single-box fit check
                return PackingResult(
                    box=box,
                    is_success=False,
                    packed_items=placed_items,
                    unpacked_items=sorted_items[step_idx - 1:],
                    failure_reason=f"Item '{item.name}' could not physically fit into remaining free space in {box.name}."
                )

            # Item placed successfully!
            placed_items.append(best_placement)

            # Update empty spaces by carving out the occupied cuboid
            new_spaces: List[EmptySpace] = []
            for space in free_spaces:
                new_spaces.extend(cls._split_space(space, best_placement))

            # Prune invalid and redundant spaces
            free_spaces = cls._prune_spaces(new_spaces)

        # All items packed!
        packed_weight = sum(p.item.weight for p in placed_items)
        packed_volume = sum(p.item.volume for p in placed_items)
        utilization = (packed_volume / box.volume * 100.0) if box.volume > 0 else 0.0

        return PackingResult(
            box=box,
            is_success=True,
            packed_items=placed_items,
            unpacked_items=[],
            total_packed_weight=round(packed_weight, 2),
            total_packed_volume=round(packed_volume, 2),
            volume_utilization_pct=round(utilization, 2),
        )

    @staticmethod
    def _split_space(space: EmptySpace, item: PlacedItem3D) -> List[EmptySpace]:
        """
        Splits an empty space into up to 3 non-overlapping maximal spaces
        if the placed item intersects it.
        """
        # Check intersection
        eps = 1e-4
        if (item.x2 <= space.x + eps or item.x >= space.x2 - eps or
            item.y2 <= space.y + eps or item.y >= space.y2 - eps or
            item.z2 <= space.z + eps or item.z >= space.z2 - eps):
            # No intersection, space remains untouched
            return [space]

        generated = []

        # 1. Space to the Right (along X)
        if item.x2 < space.x2 - eps:
            generated.append(EmptySpace(
                x=item.x2,
                y=space.y,
                z=space.z,
                lx=space.x2 - item.x2,
                ly=space.ly,
                lz=space.lz
            ))

        # 2. Space to the Left (along X)
        if item.x > space.x + eps:
            generated.append(EmptySpace(
                x=space.x,
                y=space.y,
                z=space.z,
                lx=item.x - space.x,
                ly=space.ly,
                lz=space.lz
            ))

        # 3. Space to the Back (along Y)
        if item.y2 < space.y2 - eps:
            generated.append(EmptySpace(
                x=space.x,
                y=item.y2,
                z=space.z,
                lx=space.lx,
                ly=space.y2 - item.y2,
                lz=space.lz
            ))

        # 4. Space to the Front (along Y)
        if item.y > space.y + eps:
            generated.append(EmptySpace(
                x=space.x,
                y=space.y,
                z=space.z,
                lx=space.lx,
                ly=item.y - space.y,
                lz=space.lz
            ))

        # 5. Space on Top (along Z)
        if item.z2 < space.z2 - eps:
            generated.append(EmptySpace(
                x=space.x,
                y=space.y,
                z=item.z2,
                lx=space.lx,
                ly=space.ly,
                lz=space.z2 - item.z2
            ))

        return generated

    @staticmethod
    def _prune_spaces(spaces: List[EmptySpace]) -> List[EmptySpace]:
        """
        Filters out degenerate (zero/negative volume) spaces and
        removes any space that is strictly enclosed within another space.
        """
        valid = [s for s in spaces if s.lx > 0.1 and s.ly > 0.1 and s.lz > 0.1]
        
        # Sort descending by volume so larger spaces come first
        valid.sort(key=lambda s: s.volume, reverse=True)
        
        pruned: List[EmptySpace] = []
        for cand in valid:
            is_subsumed = False
            for existing in pruned:
                if existing.contains_space(cand):
                    is_subsumed = True
                    break
            if not is_subsumed:
                pruned.append(cand)
                
        return pruned
