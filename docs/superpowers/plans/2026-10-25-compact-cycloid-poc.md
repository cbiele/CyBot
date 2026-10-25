# Compact Cycloid POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate, print and bench-test a 1:20 printed cycloid reducer on 6804 main bearings, driven 2:1 by a GT2 belt, as the first step toward a lighter head.

**Architecture:** The cycloid math (outline, meshing, belt centre distance) lives in a plain-Python module, `cycloid_math.py`, that pytest checks outside Blender. A fit coupon picks the press-fit diameters, which go into `model/cycloid-poc/params.json`. One headless Blender generator, `cycloid_poc.py`, reads the math module and the params, and builds every part in the assembly frame. It asserts walls and measured bores, poses the moving parts at four input angles to check that nothing collides, then exports each STL in its print orientation. The bench test on the Octopus is the physical test, and its results go back into `docs/build-plan.md`.

**Tech Stack:** Python 3 with pytest 9 (`python3 -m pytest`), Blender 5.1 headless (`/Applications/Blender.app/Contents/MacOS/Blender -b -P <script>`), `tools/blender/hand_lib.py` primitives (`box`, `cyl_z`, `cyl_between`, `union`, `cut`, `finish`, `stats`, `hole_diameter`, `first_hit_x`, `export`), Bambu P2S in PLA, BTT Octopus Pro under Marlin, driven over USB serial at 250000 baud.

**Spec:** `docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md`

## Global Constraints

- Ratio 1:20 cycloid (20 lobes, 21 ring pins) × 2:1 belt = 40:1. Steps per output degree = 200 × 16 × 40 / 360 = 355.56.
- Two disks, 180° apart, no caps. Disk A sits on the rear eccentric; disk B, on the front, has its lobes turned half a lobe (9°) against its bushing holes.
- Ring pins: 21 × Ø3 × 18 spring pins on a Ø50 pin circle, slit facing away from the disk.
- Output pins: 6 × Ø4 × 20 spring pins on a Ø32 circle, running in 6 × 8 × 6 brass bushings (bore 6 = pin 4 + 2 × eccentricity) pressed into each disk.
- Eccentricity 1.0 mm. Disk outline held 0.15 mm off the pins for print tolerance.
- Bearings: 2 × 6804 (main, one per side), 2 × 6800 (disks), 2 × 625 (input, one in each carrier, on the Ø5 steel rod).
- Input: one printed eccentric body with both journals, D-bored onto a Ø5 × 55 steel rod with a flat ground 0.5 deep along its length. GT2 40T (5 mm bore) on the rod, GT2 20T on the motor, 232 mm 6 mm GT2 belt.
- Generator walls: at least 1.5 mm, except the eccentric ends (1.3 mm round the rod), which pass through the 6800 bore at 1 mm offset with 0.2 mm to spare. Every mesh manifold.
- Housing in two halves split at the disks' mid-plane, clamped by 4 × M3 bolts that also mount it to the bench upright. This replaces the spec's one-piece housing (see Task 4: the carriers can't pass the 6804 seats).
- Bench: MOTOR5 (G-code B, TMC2209), 17HS8401B, 1200 mA to start. Power both cords off before touching a plug. No `M500`.
- Repo conventions: generators in `tools/blender/` with an absolute `ROOT`, STLs under `model/`, tests adjacent to the code, one logical change per commit, and **ask the user before every commit** (global CLAUDE.md).

## Review Focus

- **The front housing half goes on over 21 standing pins at once.** It should slide on by hand. Generator assert: the slip bore is at least 0.1 mm over the pin (Task 4).
- **Disks swapped or flipped.** A disk on the wrong eccentric must be obvious before it jams. pytest: the wrong phase cuts into the pins (Task 1). Generator: one locator dot on disk A's front face, two on disk B's (Task 3).
- **Belt length off by a few mm.** The ±3 mm motor slot must cover a 226–238 mm belt. pytest (Task 1).
- **A 6800 won't slide over an eccentric end.** Generator assert: end radius + eccentricity ≤ journal radius − 0.2 (Task 3).
- **Output pin engagement.** The stack must leave exactly 3 mm of each 20 mm pin in each carrier. Generator assert (Task 4).

---

## File structure

| File | Responsibility |
|---|---|
| `tools/blender/cycloid_math.py` | Create: lobe outline, disk placement, ring pin and output pin positions, meshing gaps, self-intersection count, belt centre distance, constants |
| `tools/blender/test_cycloid_math.py` | Create: pytest for the above |
| `tools/blender/cycloid_coupon.py` | Create: fit coupon (hole plate and peg strip) |
| `model/cycloid-poc/params.json` | Create: press-fit diameters, nominal first, set from the coupon |
| `tools/blender/cycloid_poc.py` | Create: all POC parts, self-checks, assembly collision check, print-orientation export |
| `model/cycloid-poc/*.stl` | Generated parts |
| `docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md` | Modify (Task 4): split housing, Ø68 size |
| `docs/build-plan.md` | Modify (Task 6): bench results |

---

### Task 1: Cycloid math module

**Files:**
- Create: `tools/blender/cycloid_math.py`
- Test: `tools/blender/test_cycloid_math.py`

**Interfaces:**
- Produces: constants `N, R, RP, E, CLEAR, OUT_PCD_R, OUT_PIN_R, BUSHING_BORE_R, N_OUT, DISK_B_PHASE, DISK_ZONE_BORE_R, STEPS_PER_DEG`, and functions `profile(n=720, phase=0.0, clear=CLEAR) -> list[(x, y)]`, `disk_outline(disk: "A"|"B", theta: float, n=1440) -> list[(x, y)]`, `ring_pins() -> list[(x, y)]`, `pin_gaps(outline) -> list[float]`, `self_intersections(pts) -> int`, `bushing_centres(disk, theta) -> list[(x, y)]`, `output_pins(theta) -> list[(x, y)]`, `belt_centre_distance(z1, z2, length, pitch=2.0) -> float`.

- [ ] **Step 1: Write the failing tests**

`tools/blender/test_cycloid_math.py`:

```python
import math
import pytest
import cycloid_math as C


def test_outline_has_no_undercut():
    assert C.self_intersections(C.profile(n=720, clear=0.0)) == 0


def test_outline_root_and_tip():
    rs = [math.hypot(x, y) for x, y in C.profile()]
    assert min(rs) == pytest.approx(C.R - C.RP - C.CLEAR - C.E, abs=0.02)
    assert max(rs) == pytest.approx(C.R - C.RP - C.CLEAR + C.E, abs=0.02)


@pytest.mark.parametrize("disk", ["A", "B"])
@pytest.mark.parametrize("theta", [0.0, 0.7, 2.1, 3.9, 5.5])
def test_disk_meshes_with_every_pin(disk, theta):
    gaps = C.pin_gaps(C.disk_outline(disk, theta, n=2880))
    assert min(gaps) >= C.CLEAR - 0.03
    assert max(gaps) <= C.CLEAR + 0.03


def test_disk_a_on_the_front_eccentric_cuts_into_the_pins():
    a = C.disk_outline("A", 0.0)
    on_b_eccentric = [(x - 2 * C.E, y) for x, y in a]
    assert min(C.pin_gaps(on_b_eccentric)) < -0.5


@pytest.mark.parametrize("theta", [0.0, 1.3, 4.4])
def test_output_pins_roll_round_the_bushing_bores(theta):
    for disk in ("A", "B"):
        for hole, pin in zip(C.bushing_centres(disk, theta), C.output_pins(theta)):
            assert math.dist(hole, pin) == pytest.approx(C.E, abs=1e-9)
    assert C.BUSHING_BORE_R == C.OUT_PIN_R + C.E


def test_disk_clears_the_housing_bore():
    for theta in (0.0, 0.4, 2.0):
        assert max(math.hypot(x, y) for x, y in C.disk_outline("A", theta)) < C.DISK_ZONE_BORE_R - 0.3


def test_belt_centre_distance_for_the_232_belt():
    assert C.belt_centre_distance(20, 40, 232) == pytest.approx(85.76, abs=0.05)


def test_motor_slot_covers_belt_tolerance():
    c = C.belt_centre_distance(20, 40, 232)
    for length in (226, 238):
        assert abs(C.belt_centre_distance(20, 40, length) - c) <= 3.0


def test_steps_per_output_degree():
    assert C.STEPS_PER_DEG == pytest.approx(355.56, abs=0.01)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools/blender && python3 -m pytest test_cycloid_math.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'cycloid_math'`

- [ ] **Step 3: Write the module**

`tools/blender/cycloid_math.py`:

```python
"""Cycloid geometry for the compact POC (docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md),
in plain Python so pytest runs it outside Blender. Frame: housing axis on z. At input angle theta disk A's
centre is at E(cos theta, sin theta) and the disks and output turn -theta/N. Disk B rides the opposite
eccentric, which is disk A turned half a lobe, so its lobes are cut DISK_B_PHASE round from its holes."""
import math

N = 20                                  # lobes; N + 1 ring pins
R = 25.0                                # ring pin circle radius
RP = 1.5                                # ring pins: 3 x 18 spring pins
E = 1.0                                 # eccentricity
CLEAR = 0.15                            # outline held off the pins for print tolerance
OUT_PCD_R = 16.0                        # output pins and the disks' bushing seats
OUT_PIN_R = 2.0                         # output pins: 4 x 20 spring pins
BUSHING_BORE_R = OUT_PIN_R + E          # 6 x 8 x 6 brass
N_OUT = 6
DISK_B_PHASE = math.pi / N
DISK_ZONE_BORE_R = 25.75                # housing round the disks: lobe tips sweep out to R - RP - CLEAR + 2E
STEPS_PER_DEG = 200 * 16 * 2 * N / 360  # 2:1 belt, then 1:N


def profile(n=720, phase=0.0, clear=CLEAR):
    """Disk outline about its own centre; phase turns the lobes (rad)."""
    np_, rp = N + 1, RP + clear
    c, s = math.cos(phase), math.sin(phase)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        psi = math.atan2(math.sin((1 - np_) * t), R / (E * np_) - math.cos((1 - np_) * t))
        x = R * math.cos(t) - rp * math.cos(t + psi) - E * math.cos(np_ * t)
        y = -R * math.sin(t) + rp * math.sin(t + psi) + E * math.sin(np_ * t)
        pts.append((c * x - s * y, s * x + c * y))
    return pts


def _pose(disk, theta):
    sign = 1 if disk == "A" else -1
    return sign * E * math.cos(theta), sign * E * math.sin(theta), -theta / N


def disk_outline(disk, theta, n=1440):
    cx, cy, rot = _pose(disk, theta)
    c, s = math.cos(rot), math.sin(rot)
    pts = profile(n, phase=0.0 if disk == "A" else DISK_B_PHASE)
    return [(cx + c * x - s * y, cy + s * x + c * y) for x, y in pts]


def ring_pins():
    return [(R * math.cos(2 * math.pi * k / (N + 1)), R * math.sin(2 * math.pi * k / (N + 1))) for k in range(N + 1)]


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _inside(p, poly):
    x, y = p
    hit = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def pin_gaps(outline):
    """Gap from each ring pin's surface to the outline; negative means the pin cuts into the disk."""
    gaps = []
    for p in ring_pins():
        d = min(_seg_dist(p, outline[i], outline[(i + 1) % len(outline)]) for i in range(len(outline)))
        gaps.append((-d if _inside(p, outline) else d) - RP)
    return gaps


def self_intersections(pts):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    n, count = len(pts), 0
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            c, d = pts[j], pts[(j + 1) % n]
            if max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]):
                continue
            if max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]):
                continue
            if ccw(a, b, c) * ccw(a, b, d) < 0 and ccw(c, d, a) * ccw(c, d, b) < 0:
                count += 1
    return count


def bushing_centres(disk, theta):
    cx, cy, rot = _pose(disk, theta)
    return [(cx + OUT_PCD_R * math.cos(2 * math.pi * k / N_OUT + rot), cy + OUT_PCD_R * math.sin(2 * math.pi * k / N_OUT + rot))
            for k in range(N_OUT)]


def output_pins(theta):
    rot = -theta / N
    return [(OUT_PCD_R * math.cos(2 * math.pi * k / N_OUT + rot), OUT_PCD_R * math.sin(2 * math.pi * k / N_OUT + rot))
            for k in range(N_OUT)]


def belt_centre_distance(z1, z2, length, pitch=2.0):
    d1, d2 = z1 * pitch / math.pi, z2 * pitch / math.pi
    lo, hi = (d1 + d2) / 2, length
    for _ in range(80):
        c = (lo + hi) / 2
        if 2 * c + math.pi * (d1 + d2) / 2 + (d2 - d1) ** 2 / (4 * c) < length:
            lo = c
        else:
            hi = c
    return lo
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd tools/blender && python3 -m pytest test_cycloid_math.py -q`
Expected: `20 passed`. The undercut test takes a few seconds.

- [ ] **Step 5: Commit (after the user approves)**

```bash
git add tools/blender/cycloid_math.py tools/blender/test_cycloid_math.py
git commit -m "Add the compact cycloid's lobe and meshing math with tests"
```

---

### Task 2: Fit coupon and params

**Files:**
- Create: `tools/blender/cycloid_coupon.py`
- Create: `model/cycloid-poc/params.json`
- Generated: `model/cycloid-poc/fit-coupon-holes.stl`, `model/cycloid-poc/fit-coupon-pegs.stl`

**Interfaces:**
- Produces: `model/cycloid-poc/params.json` with keys `seat_6804, seat_6800, seat_625, seat_bushing, ring_pin_press, ring_pin_slip, out_pin_press, hub_6804, journal_6800, rod_bore` (diameters, mm). Task 3 onward reads it.

- [ ] **Step 1: Write the nominal params**

`model/cycloid-poc/params.json` (V1's Cults parts press their bearings into nominal seats; the hand's coupon set Ø3.90 for a 4 mm spring pin in PLA):

```json
{"seat_6804": 32.0, "seat_6800": 19.0, "seat_625": 16.0, "seat_bushing": 8.0,
 "ring_pin_press": 2.90, "ring_pin_slip": 3.10, "out_pin_press": 3.90,
 "hub_6804": 20.0, "journal_6800": 10.0, "rod_bore": 5.10}
```

- [ ] **Step 2: Write the coupon generator**

`tools/blender/cycloid_coupon.py`:

```python
"""Fit coupon for the compact cycloid POC: a plate with one row of holes per press fit and a strip of
pegs for the bearing bores, each in three sizes (left to right: nominal - 0.1, nominal, nominal + 0.1;
one notch on the plate's left edge marks the -0.1 end). The print picks the diameters in
model/cycloid-poc/params.json.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_coupon.py"""
import bpy, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT = os.path.join(ROOT, "model", "cycloid-poc")
P = json.load(open(os.path.join(OUT, "params.json")))
STEPS = (-0.1, 0.0, 0.1)
HOLES = ["seat_6804", "seat_6800", "seat_625", "seat_bushing", "ring_pin_press", "ring_pin_slip", "out_pin_press", "rod_bore"]
PEGS = ["hub_6804", "journal_6800"]
PLATE_T, PEG_H, BASE_T, GAP = 7.0, 6.0, 3.0, 4.0
ROD_FLAT = 2.0                                       # the rod's flat sits 2.0 from its axis

def rows(keys):
    """(key, diameter, x, y) for every size, rows stacked along y."""
    out, y = [], 0.0
    for k in keys:
        d_max = P[k] + max(STEPS); y += d_max / 2 + GAP
        for j, s in enumerate(STEPS):
            out.append((k, P[k] + s, GAP + d_max / 2 + j * (d_max + GAP), y))
        y += d_max / 2
    return out, y + GAP

def hole_plate():
    holes, y_top = rows(HOLES)
    x_max = max(x + d / 2 for k, d, x, y in holes) + GAP
    p = L.box("fit-coupon-holes", 0, x_max, 0, y_top, 0, PLATE_T)
    for k, d, x, y in holes:
        c = L.cyl_z("hole", x, y, d / 2, -1, PLATE_T + 1, n=96)
        if k == "rod_bore":
            L.cut(c, L.box("flat", x + ROD_FLAT, x + d, y - d, y + d, -2, PLATE_T + 2))
        L.cut(p, c)
    L.cut(p, L.box("notch", -1, 1.5, y_top / 2 - 1.5, y_top / 2 + 1.5, -1, PLATE_T + 1))
    L.finish(p); return p, holes

def peg_strip():
    pegs, y_top = rows(PEGS)
    x_max = max(x + d / 2 for k, d, x, y in pegs) + GAP
    s = L.box("fit-coupon-pegs", 0, x_max, 0, y_top, 0, BASE_T)
    for k, d, x, y in pegs:
        L.union(s, L.cyl_z("peg", x, y, d / 2, BASE_T - 0.01, BASE_T + PEG_H, n=96))
    L.cut(s, L.box("notch", -1, 1.5, y_top / 2 - 1.5, y_top / 2 + 1.5, -1, BASE_T + 1))
    L.finish(s); return s

bpy.ops.wm.read_factory_settings(use_empty=True)
plate, holes = hole_plate()
st = L.stats(plate); assert st["non_manifold"] == 0, st
for k, d, x, y in holes:
    if k == "rod_bore":
        continue
    got = L.hole_diameter(plate, x, y, PLATE_T / 2)
    assert abs(got - d) < 0.03, (k, d, got)
strip = peg_strip()
st2 = L.stats(strip); assert st2["non_manifold"] == 0, st2
print("COUPON", json.dumps({"holes": st, "pegs": st2}))
L.export(plate, os.path.join(OUT, "fit-coupon-holes.stl"))
L.export(strip, os.path.join(OUT, "fit-coupon-pegs.stl"))
print("COUPON DONE")
```

- [ ] **Step 3: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_coupon.py 2>&1 | grep -E "COUPON|Error|assert"`
Expected: a `COUPON {...}` line with `"non_manifold": 0` for both parts, then `COUPON DONE`.

- [ ] **Step 4: Commit (after the user approves)**

```bash
git add tools/blender/cycloid_coupon.py model/cycloid-poc/params.json model/cycloid-poc/fit-coupon-holes.stl model/cycloid-poc/fit-coupon-pegs.stl
git commit -m "Add a fit coupon to pick the compact cycloid's press fits"
```

- [ ] **Step 5: Bench, the user: print and fit the coupon**

Print both parts flat in PLA at 0.2 mm. For each row, pick the size that presses home with the Knipex and doesn't spin or walk out: 6804, 6800 and 625 outer rings, a brass 6 × 8 × 6, a Ø3 spring pin (press), a Ø4 spring pin, and the Ø5 rod (should slide in with the flat lined up, no play). For the pegs: the 6804 and 6800 inner rings should press on. For `ring_pin_slip`, pick the smallest hole a Ø3 pin slides into by hand, with no play you can feel. Write the chosen diameters into `params.json`. Tasks 3 to 5 can run on the nominal values in the meantime; regenerate once the coupon is settled.

---

### Task 3: Generator, part 1: disks and eccentric body

**Files:**
- Create: `tools/blender/cycloid_poc.py`
- Generated: `model/cycloid-poc/disk-a.stl`, `disk-b.stl`, `eccentric.stl`

**Interfaces:**
- Consumes: `cycloid_math` (Task 1), `params.json` (Task 2), `hand_lib`.
- Produces (used by Tasks 4 and 5, same file): constants `LIP_T, BRG_W, SHOULDER_T, PLATE_T, GAP, DISK_T, COLLAR_T, B625_W, Z_DISK0, Z_MID, L_HOUSING`; helpers `prism(name, pts, z0, z1)`, `copy(o, name)`; part builders `disk(name, phase, dots)` (built at z 0..DISK_T about the origin), `eccentric()` (assembly frame, journal A towards +x); lists `PARTS` (name → object) and `CHECKS` (functions run before export).

- [ ] **Step 1: Write the script**

`tools/blender/cycloid_poc.py`:

```python
"""Compact cycloid POC (docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md): 1:20 on 6804s.
Assembly frame: axis on z, z=0 the housing's rear face, input angle measured from +x; disk A (rear) on the
journal towards +x. Parts are built in the assembly frame, checked, posed at four input angles for
collisions, then exported in print orientation to model/cycloid-poc/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py"""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
from mathutils import Matrix
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT = os.path.join(ROOT, "model", "cycloid-poc")
P = json.load(open(os.path.join(OUT, "params.json")))

LIP_T, BRG_W, SHOULDER_T, PLATE_T, GAP, DISK_T, COLLAR_T = 0.8, 7.0, 0.5, 4.0, 0.5, 6.0, 1.0
B625_W = 5.0
END_R, COLLAR_R = 3.8, 6.0                   # eccentric ends pass the 6800 bore at 1 mm offset, 0.2 to spare
ROD_FLAT = 2.0                               # the rod's flat, 0.5 deep
DOT_R, DOT_DEPTH, DOT_PCD_R = 1.0, 0.4, 12.0 # locator dots: one on disk A, two on disk B
Z_DISK0 = LIP_T + BRG_W + SHOULDER_T + PLATE_T + GAP
Z_MID = Z_DISK0 + DISK_T + COLLAR_T / 2
L_HOUSING = 2 * Z_MID
PARTS, CHECKS = {}, []

def prism(name, pts, z0, z1):
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z0)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)

def copy(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c); return c

def disk(name, phase, dots):
    d = prism(name, C.profile(720, phase), 0, DISK_T)
    L.cut(d, L.cyl_z("6800", 0, 0, P["seat_6800"] / 2, -1, DISK_T + 1, n=96))
    for k in range(C.N_OUT):
        a = 2 * math.pi * k / C.N_OUT
        L.cut(d, L.cyl_z("bushing", C.OUT_PCD_R * math.cos(a), C.OUT_PCD_R * math.sin(a), P["seat_bushing"] / 2, -1, DISK_T + 1, n=64))
    for j in range(dots):
        a = math.radians(30 + 10 * j)        # between two bushing seats
        L.cut(d, L.cyl_z("dot", DOT_PCD_R * math.cos(a), DOT_PCD_R * math.sin(a), DOT_R, DISK_T - DOT_DEPTH, DISK_T + 1, n=24))
    L.finish(d); return d

def eccentric():
    jr = P["journal_6800"] / 2
    za0, za1 = Z_DISK0, Z_DISK0 + DISK_T
    zb0, zb1 = za1 + COLLAR_T, za1 + COLLAR_T + DISK_T
    b = L.cyl_z("eccentric", 0, 0, END_R, Z_DISK0 - GAP, zb1 + GAP, n=96)
    L.union(b, L.cyl_z("journal_a", C.E, 0, jr, za0, za1, n=128))
    L.union(b, L.cyl_z("collar", 0, 0, COLLAR_R, za1 - 0.01, zb0 + 0.01, n=96))
    L.union(b, L.cyl_z("journal_b", -C.E, 0, jr, zb0, zb1, n=128))
    rod = L.cyl_z("rod", 0, 0, P["rod_bore"] / 2, -1, L_HOUSING + 1, n=64)
    L.cut(rod, L.box("flat", ROD_FLAT, 5, -5, 5, -2, L_HOUSING + 2))
    L.cut(b, rod); L.finish(b); return b

def check_disks():
    root = C.R - C.RP - C.CLEAR - C.E
    assert C.OUT_PCD_R - P["seat_bushing"] / 2 - P["seat_6800"] / 2 >= 1.5, "bushing seat too close to the 6800"
    assert root - C.OUT_PCD_R - P["seat_bushing"] / 2 >= 1.5, "bushing seat too close to the lobe root"
    assert 2 * C.OUT_PCD_R * math.sin(math.pi / C.N_OUT) - P["seat_bushing"] >= 1.5, "bushing seats too close"
    for name in ("disk-a", "disk-b"):
        o = PARTS[name]
        assert L.stats(o)["non_manifold"] == 0, name
        assert abs(L.hole_diameter(o, 0, 0, DISK_T / 2) - P["seat_6800"]) < 0.03, name

def check_eccentric():
    jr = P["journal_6800"] / 2
    assert END_R + C.E <= jr - 0.2, "a 6800 won't slide over the eccentric end"
    assert END_R - P["rod_bore"] / 2 >= 1.2, "eccentric end too thin round the rod"
    assert jr - C.E - P["rod_bore"] / 2 >= 1.5, "journal too thin round the rod"
    o = PARTS["eccentric"]
    assert L.stats(o)["non_manifold"] == 0
    za, zb = Z_DISK0 + DISK_T / 2, Z_MID + COLLAR_T / 2 + DISK_T / 2
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=za) - (C.E - jr)) < 0.05, "journal A not towards +x"
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=zb) - (-C.E - jr)) < 0.05, "journal B not towards -x"

bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["disk-a"] = disk("disk-a", 0.0, 1)
PARTS["disk-b"] = disk("disk-b", C.DISK_B_PHASE, 2)
PARTS["eccentric"] = eccentric()
CHECKS += [check_disks, check_eccentric]

# --- Task 4 adds the housing and carriers here; Task 5 the bench parts and the assembly check ---

for check in CHECKS:
    check()
print("POC", json.dumps({n: L.stats(o) for n, o in PARTS.items()}))
for n, o in PARTS.items():
    L.export(o, os.path.join(OUT, n + ".stl"))
print("POC DONE")
```

- [ ] **Step 2: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py 2>&1 | grep -E "POC|Error|assert"`
Expected: `POC {...}` with `"non_manifold": 0` and dims about 48.7 × 48.7 × 6 for each disk, then `POC DONE`. If `first_hit_x` misses (None), the journal is not where the frame says it is: fix the journal centres, not the assert.

- [ ] **Step 3: Commit (after the user approves)**

```bash
git add tools/blender/cycloid_poc.py model/cycloid-poc/disk-a.stl model/cycloid-poc/disk-b.stl model/cycloid-poc/eccentric.stl
git commit -m "Generate the compact cycloid's disks and one-piece eccentric"
```

---

### Task 4: Generator, part 2: housing halves and carriers

**Files:**
- Modify: `tools/blender/cycloid_poc.py` (replace the `# --- Task 4 adds ...` comment line)
- Modify: `docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md` §4 item 1 and §2 item 4
- Generated: `housing-rear.stl`, `housing-front.stl`, `carrier-rear.stl`, `carrier-front.stl`

**Interfaces:**
- Consumes: Task 3's constants, `copy`, `PARTS`, `CHECKS`.
- Produces: `housing()` → `(rear, front)`, `carrier(front: bool)`, `mirror_to_front(o)`, constants `HOUSING_R, BOLT_R, BOLT_HOLE_R, BOLT_ANGLES, CARRIER_R, HUB_PROUD, INSERT_R, INSERT_PCD_R, INSERT_ANGLES`; `PARTS` gains `housing-rear, housing-front, carrier-rear, carrier-front`.

The spec's housing was one piece, but each carrier plate (Ø44, needed to hold the output pins on the Ø32 circle) can't pass through a Ø32 bearing seat. So the housing splits at the disks' mid-plane: each half takes its 6804 from the inside, against a lip at the face. The ring pins press into the rear half and slide into the front half, and 4 × M3 bolts clamp the halves to the bench upright.

- [ ] **Step 1: Add the housing and carriers**

Replace the line `# --- Task 4 adds the housing and carriers here; Task 5 the bench parts and the assembly check ---` with:

```python
LIP_R = 15.0                                 # holds each 6804's outer ring at the housing face
CARRIER_R, CARRIER_BORE_R = 22.0, 22.5
HOUSING_R, BOLT_R, BOLT_HOLE_R = 34.0, 30.0, 1.7
BOLT_ANGLES = [45 + 90 * k for k in range(4)]
SHOULDER_R = 11.5                            # bears on the 6804 inner ring only
HUB_PROUD = 1.0
ROD_CLEAR_R = 2.75
INSERT_R, INSERT_DEPTH, INSERT_PCD_R = 2.0, 3.5, 6.5   # M3 x 3 x 4.5 heat-set inserts for the test arm
INSERT_ANGLES = [90 + 120 * k for k in range(3)]
PIN_DEPTH = 3.0                              # output pin holes, blind from each plate's inner face
RING_PIN_L, OUT_PIN_L = 18.0, 20.0

def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

def mirror_to_front(o):
    """Reflect a part built on the rear side through the mid-plane."""
    o.matrix_world = Matrix.Translation((0, 0, 2 * Z_MID)) @ Matrix.Scale(-1, 4, (0, 0, 1))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()

def housing():
    rear_bores = [(-1, LIP_T, LIP_R), (LIP_T, LIP_T + BRG_W, P["seat_6804"] / 2),
                  (LIP_T + BRG_W, Z_DISK0, CARRIER_BORE_R), (Z_DISK0, Z_MID, C.DISK_ZONE_BORE_R)]
    h = L.cyl_z("housing", 0, 0, HOUSING_R, 0, L_HOUSING, n=160)
    for z0, z1, r in rear_bores + [(L_HOUSING - b, L_HOUSING - a, r) for a, b, r in rear_bores]:
        L.cut(h, L.cyl_z("bore", 0, 0, r, z0 - 0.01, z1 + 0.01, n=160))
    for a in BOLT_ANGLES:
        L.cut(h, L.cyl_z("bolt", *polar(BOLT_R, a), BOLT_HOLE_R, -1, L_HOUSING + 1, n=32))
    rear, front = copy(h, "housing-rear"), copy(h, "housing-front")
    bpy.data.objects.remove(h)
    L.cut(rear, L.box("split", -50, 50, -50, 50, Z_MID, L_HOUSING + 5))
    L.cut(front, L.box("split", -50, 50, -50, 50, -5, Z_MID))
    for k in range(C.N + 1):
        x, y = polar(C.R, 360 * k / (C.N + 1))
        L.cut(rear, L.cyl_z("pin", x, y, P["ring_pin_press"] / 2, Z_MID - RING_PIN_L / 2, Z_MID + 1, n=24))
        L.cut(front, L.cyl_z("pin", x, y, P["ring_pin_slip"] / 2, Z_MID - 1, Z_MID + RING_PIN_L / 2, n=24))
    L.finish(rear); L.finish(front); return rear, front

def carrier(front):
    """Built as the rear carrier; the output (front) carrier is mirrored and gets insert holes instead of a rod hole."""
    z_in = Z_DISK0 - GAP
    z_plate, z_hub_end = z_in - PLATE_T, -HUB_PROUD
    z_sh = z_plate - SHOULDER_T
    c = L.cyl_z("carrier-front" if front else "carrier-rear", 0, 0, CARRIER_R, z_plate, z_in, n=160)
    L.union(c, L.cyl_z("shoulder", 0, 0, SHOULDER_R, z_sh, z_plate + 0.01, n=120))
    L.union(c, L.cyl_z("hub", 0, 0, P["hub_6804"] / 2, z_hub_end, z_sh + 0.01, n=120))
    L.cut(c, L.cyl_z("625", 0, 0, P["seat_625"] / 2, z_in - B625_W, z_in + 1, n=96))
    for k in range(C.N_OUT):
        L.cut(c, L.cyl_z("pin", *polar(C.OUT_PCD_R, 360 * k / C.N_OUT), P["out_pin_press"] / 2, z_in - PIN_DEPTH, z_in + 1, n=32))
    if front:
        for a in INSERT_ANGLES:
            L.cut(c, L.cyl_z("insert", *polar(INSERT_PCD_R, a), INSERT_R, z_hub_end - 1, z_hub_end + INSERT_DEPTH, n=32))
    else:
        L.cut(c, L.cyl_z("rod", 0, 0, ROD_CLEAR_R, z_hub_end - 1, z_in - B625_W + 0.01, n=48))
    L.finish(c)
    if front:
        mirror_to_front(c)
    return c

def check_housing_and_carriers():
    z_in = Z_DISK0 - GAP
    assert CARRIER_BORE_R - CARRIER_R >= 0.5, "carrier rubs the housing"
    assert C.R - P["ring_pin_press"] / 2 - CARRIER_BORE_R >= 0.8, "ring pin hole breaks into the carrier bore"
    assert BOLT_R - BOLT_HOLE_R - (C.R + C.RP) >= 1.5, "bolt hole too close to the ring pins"
    assert HOUSING_R - BOLT_R - BOLT_HOLE_R >= 1.5, "bolt hole too close to the outside"
    assert Z_DISK0 - (Z_MID - RING_PIN_L / 2) >= 2.0, "ring pins engage less than 2 mm"
    assert abs(2 * (Z_MID - z_in) + 2 * PIN_DEPTH - OUT_PIN_L) < 1e-6, "output pins don't fill both plates' holes"
    assert P["ring_pin_slip"] - 2 * C.RP >= 0.1, "front half won't slide over the ring pins"
    assert P["hub_6804"] / 2 - P["seat_625"] / 2 >= 1.5, "carrier hub too thin round the 625"
    assert INSERT_PCD_R + INSERT_R <= P["hub_6804"] / 2 - 1.0, "insert breaks out of the hub"
    assert PIN_DEPTH <= PLATE_T - 1.0, "output pin holes break through the plate"
    for name in ("housing-rear", "housing-front", "carrier-rear", "carrier-front"):
        assert L.stats(PARTS[name])["non_manifold"] == 0, name
    rear = PARTS["housing-rear"]
    assert abs(L.hole_diameter(rear, 0, 0, LIP_T + BRG_W / 2) - P["seat_6804"]) < 0.03
    assert abs(L.hole_diameter(rear, 0, 0, LIP_T + BRG_W + 2) - 2 * CARRIER_BORE_R) < 0.05
    assert abs(L.hole_diameter(PARTS["carrier-rear"], 0, 0, z_in - B625_W / 2) - P["seat_625"]) < 0.03

PARTS["housing-rear"], PARTS["housing-front"] = housing()
PARTS["carrier-rear"] = carrier(False)
PARTS["carrier-front"] = carrier(True)
CHECKS.append(check_housing_and_carriers)

# --- Task 5 adds the bench parts and the assembly check here ---
```

- [ ] **Step 2: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py 2>&1 | grep -E "POC|Error|assert"`
Expected: `POC {...}` listing seven parts, all with `"non_manifold": 0`. The housing halves are 68 × 68 × 19.3, then `POC DONE`.

- [ ] **Step 3: Update the spec for the split housing**

In `docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md` §4, replace item 1's first sentence, `**Housing** (one piece): a ring with 21 Ø3 pin holes through its full width on the pin circle, and a 6804 outer-ring seat at each face. Pins are pushed in last, through the faces, once the disks are in. Mounting flange with four M3 holes for the bench base and, later, the head.`, with:

`**Housing**, two halves split at the disks' mid-plane, Ø68: the carrier plates can't pass a 6804 seat, so each half takes its 6804 from the inside, against a lip at the face. The 21 ring pins press into the rear half and slide into the front half. Four M3 bolts through both halves clamp them and mount the housing to the bench upright and, later, the head.`

In §2 item 4, change `about Ø60 × 35 mm` to `about Ø68 × 39 mm`.

- [ ] **Step 4: Commit (after the user approves)**

```bash
git add tools/blender/cycloid_poc.py model/cycloid-poc/housing-rear.stl model/cycloid-poc/housing-front.stl model/cycloid-poc/carrier-rear.stl model/cycloid-poc/carrier-front.stl docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md
git commit -m "Split the compact cycloid's housing so the carriers can go in"
```

---

### Task 5: Generator, part 3: bench parts, assembly check, print orientation

**Files:**
- Modify: `tools/blender/cycloid_poc.py` (replace the `# --- Task 5 adds ...` line; replace the export loop)
- Generated: `bench-upright.stl`, `test-arm.stl`; all STLs re-exported in print orientation

**Interfaces:**
- Consumes: everything from Tasks 3 and 4.
- Produces: `upright()`, `test_arm()`, `overlap(a, b) -> float` (mm³), `pose(theta)`, `PRINT_FLIP` (set of part names exported upside down).

- [ ] **Step 1: Add the bench parts and the assembly check**

Replace the line `# --- Task 5 adds the bench parts and the assembly check here ---` with:

```python
UPRIGHT_T, UPRIGHT_HALF_H, FOOT_T, FOOT_L = 5.0, 40.0, 6.0, 70.0
MOTOR_X = round(C.belt_centre_distance(20, 40, 232), 2)
SLOT = 3.0                                   # motor travel each way along x, for belt tension
NEMA_HOLE_OFF, NEMA_HOLE_R, NEMA_PILOT_R = 15.5, 1.7, 11.75
HUB_CLEAR_R = 12.0
CLAMP_R = 3.25
ARM_L, ARM_W, ARM_T = 150.0, 20.0, 6.0
WEIGHT_X = (50.0, 100.0, 140.0)              # 1.7 N·m is about 1.25 kg on the 140 hole
THETAS = (0.0, 0.9, 2.3, 4.0)
PRINT_FLIP = {"housing-front", "carrier-rear"}

def slot(name, x, y, r, half, z0, z1):
    s = L.cyl_z(name, x - half, y, r, z0, z1, n=32)
    L.union(s, L.cyl_z(name + "_b", x + half, y, r, z0, z1, n=32))
    L.union(s, L.box(name + "_m", x - half, x + half, y - r, y + r, z0, z1))
    return s

def upright():
    u = L.box("bench-upright", -40, MOTOR_X + 30, -UPRIGHT_HALF_H, UPRIGHT_HALF_H, -UPRIGHT_T, 0)
    L.union(u, L.box("foot", -40, MOTOR_X + 30, -UPRIGHT_HALF_H - FOOT_T, -UPRIGHT_HALF_H + 0.01, -UPRIGHT_T, FOOT_L))
    L.cut(u, L.cyl_z("hub", 0, 0, HUB_CLEAR_R, -UPRIGHT_T - 1, 1, n=96))
    for a in BOLT_ANGLES:
        L.cut(u, L.cyl_z("bolt", *polar(BOLT_R, a), BOLT_HOLE_R, -UPRIGHT_T - 1, 1, n=32))
    L.cut(u, slot("pilot", MOTOR_X, 0, NEMA_PILOT_R, SLOT, -UPRIGHT_T - 1, 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.cut(u, slot("nema", MOTOR_X + sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, NEMA_HOLE_R, SLOT, -UPRIGHT_T - 1, 1))
    for x in (0.0, MOTOR_X):
        y0 = -UPRIGHT_HALF_H - FOOT_T - 1
        L.cut(u, L.cyl_between("clamp", (x, y0, FOOT_L - 20), (x, -UPRIGHT_HALF_H + 1, FOOT_L - 20), CLAMP_R, n=32))
    L.finish(u); return u

def test_arm():
    z0 = L_HOUSING + HUB_PROUD
    a = L.box("test-arm", -15, ARM_L, -ARM_W / 2, ARM_W / 2, z0, z0 + ARM_T)
    for ang in INSERT_ANGLES:
        L.cut(a, L.cyl_z("screw", *polar(INSERT_PCD_R, ang), 1.7, z0 - 1, z0 + ARM_T + 1, n=32))
    for x in WEIGHT_X:
        L.cut(a, L.cyl_z("weight", x, 0, 2.8, z0 - 1, z0 + ARM_T + 1, n=32))
    L.finish(a); return a

def pose(theta):
    """Place the moving parts at input angle theta (rad); disks are built at z 0..DISK_T."""
    out = Matrix.Rotation(-theta / C.N, 4, 'Z')
    PARTS["disk-a"].matrix_world = Matrix.Translation((C.E * math.cos(theta), C.E * math.sin(theta), Z_DISK0)) @ out
    PARTS["disk-b"].matrix_world = Matrix.Translation((-C.E * math.cos(theta), -C.E * math.sin(theta), Z_DISK0 + DISK_T + COLLAR_T)) @ out
    PARTS["eccentric"].matrix_world = Matrix.Rotation(theta, 4, 'Z')
    for n in ("carrier-rear", "carrier-front", "test-arm"):
        PARTS[n].matrix_world = out

def overlap(a, b):
    """Volume (mm³) a and b share, worked out on copies."""
    ca, cb = copy(a, "ov_a"), copy(b, "ov_b")
    ca.matrix_world, cb.matrix_world = a.matrix_world.copy(), b.matrix_world.copy()
    L.boolean(ca, cb, 'INTERSECT')
    bm = bmesh.new(); bm.from_mesh(ca.data); bm.transform(ca.matrix_world); v = abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(ca); return v

PAIRS = [("disk-a", "housing-rear"), ("disk-a", "housing-front"), ("disk-b", "housing-rear"), ("disk-b", "housing-front"),
         ("disk-a", "disk-b"), ("disk-a", "carrier-rear"), ("disk-b", "carrier-front"), ("disk-a", "eccentric"), ("disk-b", "eccentric"),
         ("eccentric", "carrier-rear"), ("eccentric", "carrier-front"), ("carrier-rear", "housing-rear"),
         ("carrier-front", "housing-front"), ("test-arm", "housing-front"), ("bench-upright", "housing-rear")]

def check_assembly():
    worst = {}
    for th in THETAS:
        pose(th)
        for a, b in PAIRS:
            worst[(a, b)] = max(worst.get((a, b), 0.0), overlap(PARTS[a], PARTS[b]))
    pose(0.0)
    bad = {f"{a}/{b}": round(v, 3) for (a, b), v in worst.items() if v > 0.05}
    assert not bad, bad
    assert MOTOR_X - SLOT - 21.2 > HOUSING_R + 2, "motor body (42.3 square) hits the housing"

PARTS["bench-upright"] = upright()
PARTS["test-arm"] = test_arm()
CHECKS.append(check_assembly)
```

- [ ] **Step 2: Export in print orientation**

Replace the export loop at the bottom (`for n, o in PARTS.items(): L.export(...)`) with:

```python
for n, o in PARTS.items():
    o.matrix_world = Matrix.Rotation(math.pi, 4, 'X') if n in PRINT_FLIP else Matrix()
    L.export(o, os.path.join(OUT, n + ".stl"))
```

(The housing halves print outer face down, so every step in the bore widens going up. Carriers print inner face down, so the pin holes and the 625 seat open onto the bed. Disks, test arm and upright print flat. The eccentric prints standing, rear end down, and its ledges overhang at most 2.2 mm.)

- [ ] **Step 3: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py 2>&1 | grep -E "POC|Error|assert"`
Expected: `POC {...}` with nine parts, all `"non_manifold": 0`, then `POC DONE`. An `AssertionError` with a dict names the colliding pairs and their volumes: fix the geometry, never the threshold.

- [ ] **Step 4: Render a check image for the user**

Run in Blender (or MCP): import the nine STLs back, pose at θ = 0, section at y = 0, and render. Or read `L.stats` dims and the assert output instead if rendering is slow. Show the user the section before the print.

- [ ] **Step 5: Commit (after the user approves)**

```bash
git add tools/blender/cycloid_poc.py model/cycloid-poc/*.stl
git commit -m "Add the cycloid bench parts and check the assembly for collisions"
```

---

### Task 6: Print, assemble and bench-test

**Files:**
- Modify: `docs/build-plan.md` (bench notes in §5, after the axis 4 entries)
- Modify: memory `octopus-bench-state.md` (one line on the POC result)

- [ ] **Step 1: Order the hardware**

2 × 6800-2RS, 2 × 6804 (if short), 2 × 625ZZ (in hand), 12 × brass 6 × 8 × 6, Ø5 × 55 hardened rod, 3 × M3 × 3 × 4.5 inserts (in hand), 4 × M3 × 50 bolts + nuts, M3 × 10 × 3. Spring pins Ø3 × 18 × 21 and Ø4 × 20 × 6 are in hand. Grind a 0.5 mm flat along the rod's full length.

- [ ] **Step 2: Print**

All nine STLs in PLA, 0.2 mm, 40 % infill, 4 walls (press seats need solid walls).

- [ ] **Step 3: Assemble (the user, with the Knipex)**

1. Rear housing half: 6804 from the inside against the lip. Rear carrier hub into it from the inside. 625 into the carrier's seat.
2. Disks: press a 6800 and six bushings into each (dot face forward).
3. Eccentric on the rod (flat to flat). Disk A onto journal A from the rear end, disk B onto journal B from the front.
4. Output pins: press six Ø4 × 20 into the rear carrier's holes. Lower the rod and disks in: the rod into the rear 625, the bushings over the pins, disk A rearmost.
5. Ring pins: push 21 Ø3 × 18 into the rear half's holes, slit facing outward, past the disks' lobes. Turn the rod slightly so the lobes let each pin in.
6. Front half: 6804 from the inside, front carrier hub through it, 625 in its seat. Slide it over the ring pins and output pins together. Bolt through both halves and the upright with the 4 M3 × 50.
7. 40T on the rod behind the upright, set screw on the flat. Motor on the upright, 20T aligned with the 40T, belt on, push the motor along the slot to tension it.
8. Heat-set the 3 inserts into the front hub. Bolt on the test arm.

- [ ] **Step 4: Hand turn**

Belt off: turn the 40T by hand through 20 turns (one output turn). Expected: smooth, no tight spot. A tight spot repeating twice per input turn means a disk's 6800 or bushings are off; once per output turn means a ring pin is proud.

- [ ] **Step 5: Ratio (driven)**

Power off, plug the motor into MOTOR5, power on. Send: `M92 B355.56`, `M906 B1200`, `M203 B60`, `G91`, `M17 B`, then `G1 B360 F1800` three times with a mark on the output. Expected: back on the mark each turn. The output should turn the way the input belt runs, divided by 40.

- [ ] **Step 6: Friction**

Unloaded, step `M906 B` down from 1200 in 100 mA steps, with a `G1 B90 F1800` / `G1 B-90 F1800` pair at each step. Record the lowest current that still turns it with no skipped steps. Run the same on axis 4 (`M906 A`, `G1 A90`) for comparison.

- [ ] **Step 7: Load**

At 1200 mA, hang weights on the test arm (arm horizontal): 0.5, 1.0, then 1.25 kg on the 140 hole (about 1.7 N·m). At each one: hold 10 s, then lift 30° and return at F600. Record the first weight that stalls. Repeat at the friction-test current + 300 mA.

- [ ] **Step 8: Backlash and mass**

With the motor holding, rock the test arm by hand and read the play at the 140 hole with a ruler (play in mm / 140 × 57.3 = degrees). Weigh the reducer without the motor, upright or arm.

- [ ] **Step 9: Log the results**

Add an entry to `docs/build-plan.md` §5 bench notes, in the form of the axis 2 belt-run entry:

```markdown
  - **Compact cycloid POC bench run YYYY-MM-DD.** 1:20 on 6804s, 2:1 belt, MOTOR5 (B) at 355.56
    steps/deg with a 17HS8401B. Hand turn: <smooth / tight spots>. Ratio: <held the mark over three
    turns / drifted N°>. Friction: lowest current that turns it <mA> (axis 4: <mA>). Load: held
    <kg> on the 140 hole (<N·m>) at 1200 mA, stalled at <kg>. Backlash <°>. Mass <g> without motor.
```

Update the memory file `octopus-bench-state.md` with one line on the result, and update `MEMORY.md` if the hook changes.

- [ ] **Step 10: Commit (after the user approves)**

```bash
git add docs/build-plan.md
git commit -m "Log the compact cycloid's first bench run"
```
