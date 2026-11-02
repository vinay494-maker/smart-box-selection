# Test Cases - Box Selection System

Here is a summary of the test cases I wrote to test the box selection and packing logic.

---

### Test Cases Table

| # | Test Scenario | Input / Order | Expected Output | Result |
|---|---|---|---|:---:|
| 1 | **Single small item** | 1 Wireless Mouse ($12 \times 7 \times 4$ cm, 0.2 kg) | Picks XS Mailer (\$0.65) because it is the cheapest box that fits. | **PASS** |
| 2 | **Long item** | 1 Keyboard (36 cm long) | Skips Small Box (25 cm) and picks Medium Box (35+ cm). | **PASS** |
| 3 | **Item too heavy** | 1 Heavy Anvil (6.5 kg) into a 5 kg max box | Rejects the box with a weight limit error. | **PASS** |
| 4 | **Item too big for volume** | Foam block bigger than total box volume | Rejects the box with volume exceeded error. | **PASS** |
| 5 | **Fits only after rotation** | Item is 22 cm wide, box is 20 cm wide and 25 cm long | Code rotates the item 90 degrees so it fits inside. | **PASS** |
| 6 | **Liquid / Upright item** | Olive oil bottle with `keep_upright=True` in a short box | Does not tilt sideways; fails if height is too small. | **PASS** |
| 7 | **Multiple items together** | 2 Books + 1 Mouse + 1 Charger | All 4 items fit, and coordinates $(x, y, z)$ do not overlap. | **PASS** |
| 8 | **Order too big for 1 box** | 2 Heavy boxes (16 kg total, max box is 12 kg) | Splits order into 2 separate boxes (`is_multi_box = True`). | **PASS** |
| 9 | **API Endpoint** | `POST /api/recommend-box/` with order ID | Returns HTTP 200 with recommended box and 3D coordinates. | **PASS** |
| 10 | **UI Page loads** | Open `http://localhost:8000/` in browser | Dashboard loads with order queue and 3D box view. | **PASS** |

---

### How to run the tests

Run this command in the project folder:

```bash
python manage.py test packing
```

**Output:**
```
Ran 20 tests in 0.18s
OK
```

All 20 unit tests passed.
