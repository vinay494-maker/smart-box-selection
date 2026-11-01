# AI-Assisted Box Selection & 3D Packing System

> **Python/Django Hiring Assignment Submission**  
> An intelligent, production-ready Django application that recommends the optimal, cost-minimizing shipping box for ecommerce orders using 3D Bin Packing heuristics, physical warehouse constraints, and an AI advisory engine.

---

##  Key Features

1. **3D Bin Packing Engine (EMS Heuristic)**:
   - Implements **Empty Maximal Spaces (EMS)** decomposition with 6-DOF geometric rotations.
   - Guarantees physical non-overlap across all 3 spatial axes $(X, Y, Z)$.
   - Enforces **weight capacity** constraints ($\sum \text{weight} \le \text{box.max\_weight}$).
   - Respects **handling constraints**:
     - *Fragile items*: Prioritized to be placed on top of rigid products; never crushed under heavy items.
     - *Upright items*: Constrained to vertical orientation only (yaw rotation around $Z$-axis; no horizontal tipping).

2. **Cost-Minimizing Box Optimization**:
   - Evaluates all active warehouse shipping boxes ordered by ascending unit cost.
   - Selects the provably cheapest box that geometrically and physically fits the order payload.
   - Bypasses unnecessarily large boxes, reducing both carton costs and carrier freight surcharges.

3. **Multi-Box Partitioning Fallback**:
   - When an order exceeds the physical dimensions or weight capacity of the largest single box, the system automatically partitions items across the most cost-effective combination of boxes.

4. **AI-Assisted Packaging & Logistics Advisory**:
   - **Decision Rationale**: Human-readable explanation of why the winning box was selected and why cheaper boxes failed (e.g., dimension mismatch or weight limit exceeded).
   - **Void Fill & Cushioning Recommendation**: Calculates void volume in Liters and recommends specific materials (air pillows, 2-ply bubble wrap, recycled kraft crinkle paper).
   - **Carrier Dimensional Weight Analysis**: Computes IATA/FedEx/UPS volumetric weight ($L \times W \times H / 5000$) and warns if dimensional freight surcharges apply.
   - **Safety & Handling Alerts**: Center of gravity analysis and load balancing.

5. **Interactive Warehouse Packing Station (UI)**:
   - **Live 3D Viewport (Three.js)**: 360° interactive 3D box model with transparent carton boundaries, color-coded item cuboids, and coordinate inspection.
   - **Step-by-Step Packing Guide**: Numbered sequence of placement instructions for warehouse staff.
   - **Custom Order Simulator**: Ad-hoc simulator allowing packers to test arbitrary product dimensions.

6. **REST API (Django REST Framework)**:
   - Full RESTful endpoints for microservice integration (`/api/recommend-box/`, `/api/boxes/`, `/api/products/`, `/api/orders/`).

---

## Algorithmic Design & Mathematical Formulation

### 1. Problem Formulation
Given an order with a set of items $I = \{i_1, i_2, \dots, i_n\}$, where each item $i$ has dimensions $(l_i, w_i, h_i)$ and weight $m_i$, and a warehouse box catalog $\mathcal{B} = \{B_1, B_2, \dots, B_m\}$, where each box $B$ has inner dimensions $(L_B, W_B, H_B)$, weight limit $M_B$, and unit cost $C_B$:

$$\min_{B \in \mathcal{B}} C_B$$

Subject to:
1. **Weight Constraint**: $\sum_{i \in I} m_i \le M_B$
2. **Volume Necessary Condition**: $\sum_{i \in I} (l_i \cdot w_i \cdot h_i) \le (L_B \cdot W_B \cdot H_B)$
3. **Geometric Boundary**: $x_i + l'_i \le L_B, \quad y_i + w'_i \le W_B, \quad z_i + h'_i \le H_B$
4. **Non-Intersection (3D Collision Free)**:
   $$\forall i \ne j, \quad \left[x_i, x_i + l'_i\right) \cap \left[x_j, x_j + l'_j\right) = \emptyset \quad \lor \quad \left[y_i, y_i + w'_i\right) \cap \left[y_j, y_j + w'_j\right) = \emptyset \quad \lor \quad \left[z_i, z_i + h'_i\right) \cap \left[z_j, z_j + h'_j\right) = \emptyset$$

### 2. Empty Maximal Spaces (EMS) Heuristic
The warehouse packing algorithm tracks 3D free cuboid spaces inside the carton:
1. **Item Sorting (Best-Fit Decreasing)**: Items are sorted by $( \text{is\_fragile ASC}, -\text{weight}, -\text{volume} )$. Non-fragile, heavier, and bulkier items are placed first at the base of the box.
2. **Orientation Permutations**: For each item, up to 6 orientations are tested:
   $$\mathcal{O} = \{(l,w,h), (l,h,w), (w,l,h), (w,h,l), (h,l,w), (h,w,l)\}$$
   *(Restricted to 2 yaw orientations if `keep_upright` is enabled).*
3. **Space Splitting**: When an item is placed at $(x, y, z)$, every intersecting empty space is split into up to 5 non-overlapping cuboid spaces (Right, Left, Back, Front, Top).
4. **Pruning**: Degenerate and subsumed spaces are pruned to maintain high computational performance ($O(n \cdot s)$).

---

## System Architecture

```
box_selection_system/
├── manage.py
├── box_system/                 # Django Project Core
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── packing/                    # Main Application
│   ├── models.py               # Box, Product, Order, OrderItem, PackingRecommendation, PackedBox, PlacedItem
│   ├── serializers.py          # DRF Serializers
│   ├── views.py                # REST API views + UI views
│   ├── urls.py                 # API and Web routes
│   ├── admin.py                # Django Admin configuration
│   ├── services/               # Core Algorithmic & AI Engine
│   │   ├── packing_engine.py   # 3D Bin Packing heuristic (EMS, 6-DOF, non-overlap)
│   │   ├── ai_advisor.py       # AI reasoning, void fill, carrier freight analysis
│   │   └── box_recommender.py  # Orchestrator & multi-box partitioner
│   ├── static/
│   │   └── js/
│   │       └── packing_visualizer.js # Three.js interactive 3D visualizer
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html      # Warehouse Packing Station & Live Simulator
│   │   ├── boxes.html          # Box inventory
│   │   ├── products.html       # Product catalog
│   │   └── orders.html         # Orders queue
│   └── tests/
│       ├── test_packing_engine.py # Geometric fit, rotation, weight, collision tests
│       ├── test_recommender.py    # Box cost minimization, multi-box partition tests
│       ├── test_api.py            # DRF endpoints & order actions
│       └── test_views.py          # Template views & HTTP status codes
└── requirements.txt
```

---

## Quickstart Guide

### 1. Requirements
- Python 3.10+
- Django 5.0+ or 6.0+
- djangorestframework 3.14+

### 2. Setup & Installation

```bash
# Clone or navigate to the project directory
cd box_selection_system

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed realistic warehouse data (boxes, products, sample orders)
python manage.py seed_data

# Start the development server
python manage.py runserver
```

Open your browser at:
- **Warehouse Packing Station**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Orders Queue**: [http://127.0.0.1:8000/orders/](http://127.0.0.1:8000/orders/)
- **Box Inventory**: [http://127.0.0.1:8000/boxes/](http://127.0.0.1:8000/boxes/)
- **REST API Browser**: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Running the Test Suite

Run the full automated test suite (20 unit and integration tests):

```bash
python manage.py test packing
```

### Test Coverage Highlights:
- **`test_single_item_fits`**: Confirms baseline single item placement.
- **`test_weight_limit_exceeded`**: Verifies rejection when payload exceeds box capacity.
- **`test_volume_limit_exceeded`**: Verifies rejection when total item volume exceeds box volume.
- **`test_rotation_allows_fit`**: Tests that an item that fails in default orientation fits when rotated 90°.
- **`test_keep_upright_constraint`**: Confirms items flagged `keep_upright=True` cannot be tipped sideways.
- **`test_multiple_items_no_3d_overlap`**: Rigorously verifies all placed items have zero 3D collision intersections.
- **`test_cheapest_box_selected`**: Confirms cost-minimization logic selects lowest-cost feasible box.
- **`test_multi_box_partition`**: Confirms heavy/oversized payloads are split across multiple boxes.
- **`test_api_endpoints`**: End-to-end tests for REST API endpoints and payload validation.

---

## REST API Documentation

### 1. Recommend Box for an Existing Order
**Endpoint**: `POST /api/recommend-box/`  
**Request**:
```json
{
  "order_id": 1
}
```

**Response**:
```json
{
  "success": true,
  "is_multi_box": false,
  "status": "OPTIMAL",
  "total_boxes": 1,
  "total_cost": 0.65,
  "total_items_count": 1,
  "total_weight_kg": 0.22,
  "total_volume_cm3": 405.0,
  "boxes": [
    {
      "box_id": 1,
      "box_index": 1,
      "box_code": "BOX-XS-MAILER",
      "box_name": "Padded Mailer Box (XS)",
      "dimensions": { "length": 20.0, "width": 15.0, "height": 5.0 },
      "cost": 0.65,
      "max_weight_kg": 1.5,
      "used_weight_kg": 0.22,
      "used_volume_cm3": 405.0,
      "volume_utilization_pct": 27.0,
      "void_fill": {
        "recommended_material": "Standard Biodegradable Air Pillows",
        "void_ratio_pct": 73.0,
        "void_liters": 1.1,
        "summary": "Fill top void with 2-4 air pillow pouches to prevent transit shifting."
      },
      "placements": [
        {
          "step": 1,
          "sku": "ELEC-MOUSE",
          "name": "Wireless Ergonomic Mouse",
          "weight_kg": 0.22,
          "coordinates": { "x": 0.0, "y": 0.0, "z": 0.0 },
          "oriented_dimensions": { "length": 12.0, "width": 7.5, "height": 4.5 },
          "rotation": "Standard (L×W×H)"
        }
      ]
    }
  ],
  "ai_insights": {
    "box_code": "BOX-XS-MAILER",
    "box_name": "Padded Mailer Box (XS)",
    "cost": 0.65,
    "volume_utilization_pct": 27.0,
    "void_volume_liters": 1.1,
    "carrier_volumetric_weight_kg": 0.3,
    "billable_weight_kg": 0.3,
    "decision_rationale": [
      "Selected 'Padded Mailer Box (XS)' as the lowest-cost option ($0.65) that physically accommodates all 1 item(s).",
      "Bypassed larger 'Small Carton (S)' ($1.10) saving $0.45 per order."
    ],
    "ai_executive_summary": "AI Recommendation: Padded Mailer Box (XS) (BOX-XS-MAILER) selected. Achieves 27.0% volume utilization with payload of 0.22 kg. Packaging cost: $0.65."
  }
}
```

### 2. Ad-hoc Item Recommendation (Simulator / Cart)
**Endpoint**: `POST /api/recommend-box/`  
**Request**:
```json
{
  "items": [
    {
      "name": "Mechanical Keyboard",
      "sku": "KB-01",
      "length": 36.0,
      "width": 14.0,
      "height": 4.0,
      "weight": 1.1,
      "quantity": 1,
      "is_fragile": false,
      "keep_upright": false
    },
    {
      "name": "Fragile Wine Glass",
      "sku": "GL-01",
      "length": 10.0,
      "width": 10.0,
      "height": 22.0,
      "weight": 0.4,
      "quantity": 2,
      "is_fragile": true,
      "keep_upright": true
    }
  ]
}
```

---

## Business & Logistics Value

- **Direct Material Cost Reduction**: Minimizes box spend by choosing the smallest possible box that safely holds the goods.
- **Freight & Dim-Weight Protection**: Calculates carrier volumetric weight ($L \times W \times H / 5000$) to prevent unexpected oversized parcel charges.
- **Reduced Damage Rates**: Automated fragility detection ensures glassware and upright items are placed at the top and never placed under heavy loads.
- **Warehouse Operator Efficiency**: Provides an interactive 3D packing preview and step-by-step packing instructions, reducing packer hesitation and training time.
