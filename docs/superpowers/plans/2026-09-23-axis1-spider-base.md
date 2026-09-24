# Axis-1 Spider Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate the printable spider base (ring, plain arm, motor arm, pad plug) from one Blender script with assertion self-tests, then print and prove it on the bench in the spec's four phases.

**Architecture:** One headless Blender script, `tools/blender/spider_base.py`, reuses the mesh primitives in `tools/blender/hand_lib.py` (box, cyl_z, cyl_between, union, cut, finish, stats, hole_diameter, export) and adds a hexahedron helper for tapered rails and web bars. It builds each part in the spider frame (z up, ground at z=0, ring top at z=35, arm along +x from the ring facet), asserts the spec's checks, exports STLs to `model/base/`, and renders the assembly with the Cults base holder placed on the ring.

**Tech Stack:** Blender 5.1 headless (`/Applications/Blender.app/Contents/MacOS/Blender -b -P`), bmesh, EXACT booleans, BVH ray casts, Workbench renders. No Python outside Blender.

**Spec:** `docs/superpowers/specs/2026-09-23-axis1-spider-base-design.md`

## Global Constraints

- Ring Ø200 outside, Ø50 centre, 35 mm tall, 4 mm top plate, 3 mm walls, eight ribs, open underneath (spec §5.1).
- Base holder bolts: 8 × Ø5.5 on Ø141 at the Cults angles, pairs at 11.3° and 33.7° from each 90° step, M5 nut pocket under each (spec §5.1).
- Arms at 0°, 90°, 180°, 270°, motor arm at 180° (spec §4). Arm length 260 mm, one constant `ARM_LEN` (spec §5.2).
- Rails 5 mm thick, 35 mm tall at the root tapering to 15 at the foot, 60 mm apart at the root spreading to 90 at the foot; Warren web 3 mm, four bays; 2 mm skin; foot 90 × 25 × 8 with Ø5.5 and a Ø10 × 3 counterbore (spec §5.2).
- Tenon and mortise differ by 0.3 mm in width and height; two radial M5 × 30 per facet, 36 mm apart at mid-height (spec §5.1, §5.2).
- Motor axis 139 mm from the base axis; plate top 53 mm above the ring top; NEMA17 31 mm pattern as 3.4 × 8 mm radial slots; Ø23 pilot; pulley teeth 30 to 42 mm above the ring top (spec §5.3).
- Each arm's bounding box on the bed diagonal under 250 mm; every part manifold; no supports (spec §6, §7).
- Output STLs `model/base/spider-ring.stl`, `spider-arm.stl`, `spider-arm-motor.stl`, `spider-pad.stl`; renders are gitignored (spec §6).
- Git: stage, summarise, wait for approval before each commit (user CLAUDE.md).

**Spec deviations locked in here, all geometric consequences of the spec's own numbers:**
- A 60 mm wide flat on a Ø200 ring sits at 95.4 mm from the axis, not 97. `FACET_X = 95.39`.
- The mortise keeps a 4 mm sill at the bottom of the boss so the tenon bears top and bottom: mortise 40 × 27 (z 4 to 31), tenon 39.7 × 26.7.
- The bracket walls stand on the rails, following the rails' plan taper, and the belt clearance is a window through both walls (x 108 to 136, z 58 to 84 in the ground frame) instead of a cut-down near wall, because the belt runs cross the wall plane between 108 and 125 mm radius.

**Found during execution (the code below is as written; these are what changed while running it):**
- Radial bolts cannot pass through an open mortise, the boss has no material there. The mortise is blind with a 4 mm back wall (boss 18 deep, mortise 14), the bolts go through that wall and sit 28 mm apart (y ±14) so their holes stay inside it, and they shorten to M5 × 20. Tenon 13.7 long, nut slots 6.5 mm from its end.
- Tools placed by `cyl_between` carry a world matrix, so `turned()` composes the facet rotation onto the matrix rather than setting `rotation_euler`.
- The ring's bounding box is 190.8 across the flats, not 200.
- Any face of a tool lying exactly on an existing face breaks the exact boolean: ribs start 1 mm inside the hub wall, the bracket walls are inset 0.3 mm from the rail faces and start 1 mm below the rail top, the plate overhangs the walls by 0.3 mm.
- `hand_lib.hole_diameter` averages 24 rays and a ray that lands on a polygon vertex passes through; the generator has its own `bore()` using a median over half-step-offset rays.
- (2026-09-24, from the first arm print) The tenon was unioned to the arm's root face, where only the skin and the rails exist, so it came out as a second shell and printed loose. The arm now starts with a 6 mm root plate the tenon grows out of, rails, skin and web start 1 mm inside it, and every part asserts one connected shell.

---

## File structure

| File | Responsibility |
|---|---|
| `tools/blender/spider_base.py` | Create: constants, hexahedron helper, ring, arm, motor arm, pad, self-tests, export, assembly render |
| `model/base/spider-*.stl` | Generated |
| `.gitignore` | Modify: add `model/base/*.png` |
| `model/parts-list.md` | Modify: add the four base rows |
| `docs/build-plan.md` | Modify: bench log lines for the spider |

Frame: z up, ground z=0, ring top z=`RING_H`=35 (the mounting plane). Arms are generated along +x, root face at x=`FACET_X`, foot end at `FACET_X + ARM_LEN`. Radii in the motor arm are measured from the base axis, so "139 mm radius" is x=139 in the arm's own frame.

---

### Task 1: Ring

**Files:**
- Create: `tools/blender/spider_base.py`
- Create: `model/base/spider-ring.stl` (generated)

**Interfaces:**
- Consumes: `hand_lib.box(name, x0, x1, y0, y1, z0, z1)`, `cyl_z(name, x, y, r, z0, z1, n=64)`, `cyl_between(name, a, b, r)`, `union(target, tool)`, `cut(target, tool)`, `finish(o)`, `stats(o) -> {"dims", "faces", "non_manifold"}`, `hole_diameter(o, x, y, z_probe)`, `export(o, path)`.
- Produces: constants `RING_H, RING_R, FACET_X, FACET_W, BOSS_D, MORTISE_W, MORTISE_Z0, MORTISE_Z1, FIT, JOINT_BOLT_Y, JOINT_BOLT_Z, JOINT_BOLT_D, ARM_ANGLES`; helpers `hull8(name, bottom, top)`, `slab(name, x0, x1, ylo0, yhi0, ylo1, yhi1, z0, zt0, zt1)`, `bar(name, a, b, w, z0, ztop_a, ztop_b)`, `hex_z(name, x, y, af, z0, z1)`, `probe(o, p, d)`, `diagonal_extent(o)`; `ring() -> object`; `report` dict and the `SPIDER {...}` print.

- [ ] **Step 1: Write the generator with the ring and its assertions**

`tools/blender/spider_base.py`:

```python
"""Standalone spider base for axis 1 (spec docs/superpowers/specs/2026-09-23-axis1-spider-base-design.md).
Frame: base axis on z, ground at z=0, ring top (the mounting plane) at z=RING_H. Arms are generated
along +x with the ring facet at x=FACET_X; the assembly render turns copies to 0/90/180/270 deg.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/spider_base.py
Writes model/base/spider-*.stl and renders; SPIDER_OUT overrides the output folder."""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
from mathutils import Vector, Matrix
import mathutils
OUT = os.environ.get("SPIDER_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "base"))
os.makedirs(OUT, exist_ok=True)
CULTS = "/Users/claytonbiele/dev/Claude/Projects/cybot/Cults3d_v5/2-axis1"

# ---- ring
RING_R, RING_H, RING_PLATE_T, WALL, CENTRE_R = 100.0, 35.0, 4.0, 3.0, 25.0
HOLE_R, HOLE_D = 70.6, 5.5                                   # Cults base holder pattern, measured from its STL
HOLE_ANGLES = [11.3, 33.7, 101.3, 123.7, 191.3, 213.7, 281.3, 303.7]
NUT_AF, NUT_H, NUT_BOSS_D = 8.4, 4.5, 14.0                   # M5 nut, pocket open downward under the top plate
RIB_ANGLES = [22.5 + 45 * k for k in range(8)]
ARM_ANGLES = [0, 90, 180, 270]; MOTOR_ARM_ANGLE = 180
FACET_W = 60.0; FACET_X = math.sqrt(RING_R ** 2 - (FACET_W / 2) ** 2)   # 95.39: a 60 mm flat on the Ø200 wall
BOSS_D = 15.0
MORTISE_W, MORTISE_Z0, MORTISE_Z1, FIT = 40.0, 4.0, RING_H - RING_PLATE_T, 0.3
JOINT_BOLT_Y, JOINT_BOLT_Z, JOINT_BOLT_D = 18.0, 17.5, 5.5

def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

def hull8(name, bottom, top):
    """Hexahedron from four bottom corners (counter-clockwise seen from above) and the four top
    corners above them, so rails and web bars can taper in plan and in height at once."""
    bm = bmesh.new()
    b = [bm.verts.new(p) for p in bottom]; t = [bm.verts.new(p) for p in top]
    bm.faces.new(b[::-1]); bm.faces.new(t)
    for i in range(4):
        j = (i + 1) % 4; bm.faces.new((b[i], b[j], t[j], t[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm)

def slab(name, x0, x1, ylo0, yhi0, ylo1, yhi1, z0, zt0, zt1):
    """Block between x0 and x1 whose y extent and top height vary linearly along x."""
    return hull8(name, [(x0, ylo0, z0), (x1, ylo1, z0), (x1, yhi1, z0), (x0, yhi0, z0)],
                       [(x0, ylo0, zt0), (x1, ylo1, zt1), (x1, yhi1, zt1), (x0, yhi0, zt0)])

def bar(name, a, b, w, z0, ztop_a, ztop_b):
    """Bar in plan from a to b, w wide, bottom at z0, top rising from ztop_a to ztop_b."""
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy); px, py = -dy / n * w / 2, dx / n * w / 2
    return hull8(name, [(ax - px, ay - py, z0), (bx - px, by - py, z0), (bx + px, by + py, z0), (ax + px, ay + py, z0)],
                       [(ax - px, ay - py, ztop_a), (bx - px, by - py, ztop_b), (bx + px, by + py, ztop_b), (ax + px, ay + py, ztop_a)])

def hex_z(name, x, y, af, z0, z1):
    return L.cyl_z(name, x, y, af / 2 / math.cos(math.radians(30)), z0, z1, n=6)

def turned(o, deg):
    o.rotation_euler = (0, 0, math.radians(deg)); bpy.context.view_layer.update(); return o

def probe(o, p, d):
    """Distance from point p to the surface of o along direction d, or None."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    hit = mathutils.bvhtree.BVHTree.FromBMesh(bm).ray_cast(Vector(p), Vector(d).normalized()); bm.free()
    return None if hit[0] is None else round((hit[0] - Vector(p)).length, 3)

def diagonal_extent(o):
    """Bounding box of o measured along the bed diagonals (the part is printed turned 45 deg)."""
    c = math.cos(math.radians(45))
    u = [v.co.x * c + v.co.y * c for v in o.data.vertices]; w = [-v.co.x * c + v.co.y * c for v in o.data.vertices]
    return round(max(u) - min(u), 1), round(max(w) - min(w), 1)

def polar(r, deg):
    a = math.radians(deg); return r * math.cos(a), r * math.sin(a)

def facet(r, deg):
    """Flatten the outer wall at 60 mm width, thicken it into a boss, cut the mortise and the two
    radial bolt holes; everything generated along +x then turned to the arm angle."""
    L.cut(r, turned(L.box("flat", FACET_X, RING_R + 1, -FACET_W / 2 - 1, FACET_W / 2 + 1, -1, RING_H + 1), deg))
    L.union(r, turned(L.box("boss", FACET_X - BOSS_D, FACET_X, -FACET_W / 2, FACET_W / 2, 0, RING_H), deg))
    L.cut(r, turned(L.box("mortise", FACET_X - BOSS_D - 0.1, FACET_X + 0.1, -MORTISE_W / 2, MORTISE_W / 2, MORTISE_Z0, MORTISE_Z1), deg))
    for y in (-JOINT_BOLT_Y, JOINT_BOLT_Y):
        L.cut(r, turned(L.cyl_between("bolt", (FACET_X - BOSS_D - 1, y, JOINT_BOLT_Z), (FACET_X + 1, y, JOINT_BOLT_Z), JOINT_BOLT_D / 2), deg))

def ring():
    r = L.cyl_z("spider-ring", 0, 0, RING_R, 0, RING_H, n=180)
    L.cut(r, L.cyl_z("hollow", 0, 0, RING_R - WALL, -1, RING_H - RING_PLATE_T))
    L.union(r, L.cyl_z("hub", 0, 0, CENTRE_R + WALL, 0, RING_H))
    for deg in RIB_ANGLES:
        L.union(r, bar("rib", polar(CENTRE_R, deg), polar(RING_R - 1, deg), WALL, 0, RING_H - 1, RING_H - 1))
    for deg in HOLE_ANGLES:
        x, y = polar(HOLE_R, deg); z_plate = RING_H - RING_PLATE_T
        L.union(r, L.cyl_z("nut_boss", x, y, NUT_BOSS_D / 2, z_plate - NUT_H, z_plate + 0.01))
        L.cut(r, hex_z("nut", x, y, NUT_AF, z_plate - NUT_H - 0.1, z_plate + 0.5))
        L.cut(r, L.cyl_z("hole", x, y, HOLE_D / 2, z_plate - NUT_H - 1, RING_H + 1))
    for deg in ARM_ANGLES:
        facet(r, deg)
    L.cut(r, L.cyl_z("centre", 0, 0, CENTRE_R, -1, RING_H + 1))
    L.finish(r); return r

def check_ring(r, report):
    st = L.stats(r); assert st["non_manifold"] == 0, st
    holes = [L.hole_diameter(r, *polar(HOLE_R, d), RING_H - 1) for d in HOLE_ANGLES]
    assert all(abs(h - HOLE_D) < 0.05 for h in holes), holes
    pockets = [L.hole_diameter(r, *polar(HOLE_R, d), RING_H - RING_PLATE_T - 2) for d in HOLE_ANGLES]
    assert all(NUT_AF <= p <= NUT_AF / math.cos(math.radians(30)) + 0.05 for p in pockets), pockets
    mid = (FACET_X - BOSS_D / 2, 0, JOINT_BOLT_Z)
    mortise_w = probe(r, mid, (0, 1, 0)) + probe(r, mid, (0, -1, 0))
    mortise_h = probe(r, mid, (0, 0, 1)) + probe(r, mid, (0, 0, -1))
    assert abs(mortise_w - MORTISE_W) < 0.05 and abs(mortise_h - (MORTISE_Z1 - MORTISE_Z0)) < 0.05, (mortise_w, mortise_h)
    assert abs(L.hole_diameter(r, 0, 0, RING_H - 1) - 2 * CENTRE_R) < 0.1
    report["spider-ring"] = {**st, "holes": holes, "mortise": [round(mortise_w, 2), round(mortise_h, 2)]}

bpy.ops.wm.read_factory_settings(use_empty=True)
report = {}
r = ring(); check_ring(r, report); L.export(r, os.path.join(OUT, "spider-ring.stl"))
print("SPIDER", json.dumps(report))
```

- [ ] **Step 2: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/spider_base.py 2>&1 | grep "^SPIDER\|Assertion\|Error\|Traceback"`

Expected: one `SPIDER {...}` line with `"non_manifold": 0`, `"dims": [200.0, 200.0, 35.0]`, eight `holes` near 5.5 and `mortise` near `[40.0, 27.0]`. `model/base/spider-ring.stl` appears. If `non_manifold` is not 0 the culprit is almost always a coplanar face between a cut tool and an existing face: nudge the tool 0.1 mm past the face, never onto it.

- [ ] **Step 3: Break test, proving the mortise measurement is live**

Change `MORTISE_W / 2` in the mortise cut inside `facet()` to `MORTISE_W / 2 + 0.25` (both occurrences on that line) and rerun. Expected: `AssertionError: (40.5, 27.0)`. Restore the line and rerun to green.

- [ ] **Step 4: Stage and propose the commit**

```bash
git add tools/blender/spider_base.py model/base/spider-ring.stl
```

Proposed message: `Generate the spider base ring` with a body saying the ring carries the Cults base holder's bolt pattern on a shell that prints open side up, and why the facet sits at 95.4 mm. Wait for approval.

---

### Task 2: Plain arm

**Files:**
- Modify: `tools/blender/spider_base.py` (add constants, `rail_outer`, `rail_top`, `arm`, `check_arm`; extend the bottom block)
- Create: `model/base/spider-arm.stl` (generated)

**Interfaces:**
- Consumes: Task 1 constants and helpers.
- Produces: `ARM_LEN, RAIL_T, RAIL_H0, RAIL_H1, HALF_W0, HALF_W1, SKIN_T, WEB_T, BAYS, FOOT_L, FOOT_T, FOOT_HOLE_D, FOOT_CB_D, FOOT_CB_DEPTH, BED_DIAG_MAX`; `rail_outer(x) -> float`, `rail_top(x) -> float`, `arm(name) -> object`, `check_arm(a, report)`.

- [ ] **Step 1: Add the arm**

Insert after the `JOINT_BOLT_*` line:

```python
# ---- arms
ARM_LEN, RAIL_T, RAIL_H0, RAIL_H1 = 260.0, 5.0, 35.0, 15.0
HALF_W0, HALF_W1 = 30.0, 45.0                                 # outer faces: 60 wide at the root, 90 at the foot
SKIN_T, WEB_T, BAYS = 2.0, 3.0, 4
FOOT_L, FOOT_T, FOOT_HOLE_D, FOOT_CB_D, FOOT_CB_DEPTH = 25.0, 8.0, 5.5, 10.0, 3.0
NUT_SLOT_X0, NUT_SLOT_W, NUT_SLOT_Z0 = 9.0, 4.5, 12.5          # cross pocket in the tenon for the joint nut; nut corners span 12.65 to 22.35
BED_DIAG_MAX = 250.0
```

Insert after `check_ring`:

```python
def rail_outer(x):
    return HALF_W0 + (HALF_W1 - HALF_W0) * (x - FACET_X) / ARM_LEN

def rail_top(x):
    return RAIL_H0 + (RAIL_H1 - RAIL_H0) * (x - FACET_X) / ARM_LEN

def arm(name):
    """Two tapered rails on a 2 mm skin with a Warren web, a wide foot with one hole, and the
    tenon that plugs into a ring facet. Root face at x=FACET_X, foot end at FACET_X + ARM_LEN."""
    x0, x1 = FACET_X, FACET_X + ARM_LEN; xf = x1 - FOOT_L
    a = slab(name, x0, xf, -rail_outer(x0), rail_outer(x0), -rail_outer(xf), rail_outer(xf), 0, SKIN_T, SKIN_T)
    for s in (-1, 1):
        yo0, yo1 = s * rail_outer(x0), s * rail_outer(xf); yi0, yi1 = yo0 - s * RAIL_T, yo1 - s * RAIL_T
        L.union(a, slab("rail", x0, xf, min(yo0, yi0), max(yo0, yi0), min(yo1, yi1), max(yo1, yi1), 0, rail_top(x0), rail_top(xf)))
    nodes = []
    for k in range(BAYS + 1):
        x = x0 + (xf - x0) * k / BAYS; s = -1 if k % 2 == 0 else 1
        nodes.append((x, s * (rail_outer(x) - RAIL_T + 1.5)))         # 1.5 mm into the rail so the union is solid
    for (xa, ya), (xb, yb) in zip(nodes, nodes[1:]):
        L.union(a, bar("web", (xa, ya), (xb, yb), WEB_T, 0, rail_top(xa), rail_top(xb)))
    L.union(a, L.box("foot", xf - 0.01, x1, -HALF_W1, HALF_W1, 0, FOOT_T))
    L.cut(a, L.cyl_z("foot_hole", x1 - FOOT_L / 2, 0, FOOT_HOLE_D / 2, -1, FOOT_T + 1))
    L.cut(a, L.cyl_z("foot_cb", x1 - FOOT_L / 2, 0, FOOT_CB_D / 2, FOOT_T - FOOT_CB_DEPTH, FOOT_T + 1))
    L.union(a, L.box("tenon", x0 - BOSS_D, x0 + 0.01, -(MORTISE_W - FIT) / 2, (MORTISE_W - FIT) / 2, MORTISE_Z0 + FIT / 2, MORTISE_Z1 - FIT / 2))
    for y in (-JOINT_BOLT_Y, JOINT_BOLT_Y):
        L.cut(a, L.cyl_between("bolt", (x0 - BOSS_D - 1, y, JOINT_BOLT_Z), (x0 + 3, y, JOINT_BOLT_Z), JOINT_BOLT_D / 2))
        L.cut(a, L.box("nut_slot", x0 - BOSS_D + NUT_SLOT_X0, x0 - BOSS_D + NUT_SLOT_X0 + NUT_SLOT_W, y - NUT_AF / 2, y + NUT_AF / 2, NUT_SLOT_Z0, MORTISE_Z1 + 1))
    L.finish(a); return a

def check_arm(a, report):
    st = L.stats(a); assert st["non_manifold"] == 0, st
    diag = diagonal_extent(a); assert max(diag) <= BED_DIAG_MAX, diag
    x0, x1 = FACET_X, FACET_X + ARM_LEN
    ys = [v.co.y for v in a.data.vertices if v.co.x < x0 - 1]
    tenon_w = round(max(ys) - min(ys), 2); assert abs(MORTISE_W - tenon_w - FIT) < 0.02, tenon_w
    zs = [v.co.z for v in a.data.vertices if v.co.x < x0 - 1]
    tenon_h = round(max(zs) - min(zs), 2); assert abs((MORTISE_Z1 - MORTISE_Z0) - tenon_h - FIT) < 0.02, tenon_h
    foot_hole = L.hole_diameter(a, x1 - FOOT_L / 2, 0, 2.0); assert abs(foot_hole - FOOT_HOLE_D) < 0.05, foot_hole
    cb = L.hole_diameter(a, x1 - FOOT_L / 2, 0, FOOT_T - 1.0); assert abs(cb - FOOT_CB_D) < 0.05, cb
    report[a.name] = {**st, "diagonal": diag, "tenon": [tenon_w, tenon_h], "foot_hole": foot_hole}
```

Replace the bottom block with:

```python
bpy.ops.wm.read_factory_settings(use_empty=True)
report = {}
r = ring(); check_ring(r, report); L.export(r, os.path.join(OUT, "spider-ring.stl"))
a = arm("spider-arm"); check_arm(a, report); L.export(a, os.path.join(OUT, "spider-arm.stl"))
print("SPIDER", json.dumps(report))
```

- [ ] **Step 2: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/spider_base.py 2>&1 | grep "^SPIDER\|Assertion\|Error\|Traceback"`

Expected: `spider-arm` with `"non_manifold": 0`, `"dims"` about `[275.0, 90.0, 35.0]` (260 plus the 15 mm tenon), `"diagonal"` both values under 250 (about 247 and 240), `"tenon": [39.7, 26.7]`, `"foot_hole"` near 5.5.

- [ ] **Step 3: Break test on the tenon fit**

Change `FIT` in the tenon box only (not the constant) to `FIT + 0.5` in the width terms and rerun. Expected: `AssertionError: 39.2`. Restore and rerun to green.

- [ ] **Step 4: Stage and propose the commit**

```bash
git add tools/blender/spider_base.py model/base/spider-arm.stl
```

Proposed message: `Generate the spider base arm`, body: rails taper in height with the bending moment and the arm is sized to the A1 bed diagonal; the tenon clearance is the value the first print will test. Wait for approval.

---

### Task 3: Motor arm

**Files:**
- Modify: `tools/blender/spider_base.py` (add constants, `motor_arm`, `check_motor_arm`; extend the bottom block)
- Create: `model/base/spider-arm-motor.stl` (generated)

**Interfaces:**
- Consumes: `arm(name)`, `slab`, `rail_outer`, `rail_top`, `probe`, Task 1 and 2 constants.
- Produces: `MOTOR_R, BR_X0, BR_X1, PLATE_X0, PLATE_X1, BR_PLATE_T, PLATE_TOP, WIN_X0, WIN_X1, WIN_Z0, WIN_Z1, NEMA_PITCH, SLOT_W, SLOT_L, PILOT_D, PULLEY_R, PULLEY_TEETH_W, HUB_L, SHAFT_L, BIG_R, BAND`; `motor_arm() -> object`, `check_motor_arm(m, report)`.

- [ ] **Step 1: Add the motor arm**

Insert after `BED_DIAG_MAX`:

```python
# ---- motor arm bracket: motor on top of a plate, shaft down, pulley on the rotating base's band
MOTOR_R = 139.0                                                # Cults centre distance
BR_X0, BR_X1, PLATE_X0, PLATE_X1 = 108.0, 177.0, 110.0, 170.0
BR_PLATE_T, PLATE_TOP = 5.0, RING_H + 53.0
WIN_X0, WIN_X1, WIN_Z0, WIN_Z1 = 108.0, 136.0, RING_H + 23.0, PLATE_TOP - BR_PLATE_T + 1.0
NEMA_PITCH, SLOT_W, SLOT_L, PILOT_D = 31.0, 3.4, 8.0, 23.0
PULLEY_R, PULLEY_TEETH_W, HUB_L, SHAFT_L, BIG_R = 14.3, 12.0, 6.0, 24.0, 83.0
BAND = (30.0, 42.0)                                            # pulley teeth above the ring top, matching the base's band
```

Insert after `check_arm`:

```python
def motor_arm():
    m = arm("spider-arm-motor")
    for s in (-1, 1):
        yo0, yo1 = s * rail_outer(BR_X0), s * rail_outer(BR_X1); yi0, yi1 = yo0 - s * RAIL_T, yo1 - s * RAIL_T
        L.union(m, slab("wall", BR_X0, BR_X1, min(yo0, yi0), max(yo0, yi0), min(yo1, yi1), max(yo1, yi1), 0, PLATE_TOP - BR_PLATE_T + 0.01, PLATE_TOP - BR_PLATE_T + 0.01))
    L.union(m, slab("plate", PLATE_X0, PLATE_X1, -rail_outer(PLATE_X0), rail_outer(PLATE_X0), -rail_outer(PLATE_X1), rail_outer(PLATE_X1), PLATE_TOP - BR_PLATE_T, PLATE_TOP, PLATE_TOP))
    L.cut(m, L.box("window", WIN_X0 - 1, WIN_X1, -60, 60, WIN_Z0, WIN_Z1))
    L.cut(m, L.cyl_z("pilot", MOTOR_R, 0, PILOT_D / 2, PLATE_TOP - BR_PLATE_T - 1, PLATE_TOP + 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = MOTOR_R + sx * NEMA_PITCH / 2, sy * NEMA_PITCH / 2; half = (SLOT_L - SLOT_W) / 2
            L.cut(m, L.box("slot", cx - half, cx + half, cy - SLOT_W / 2, cy + SLOT_W / 2, PLATE_TOP - BR_PLATE_T - 1, PLATE_TOP + 1))
            for ex in (cx - half, cx + half):
                L.cut(m, L.cyl_z("slot_end", ex, cy, SLOT_W / 2, PLATE_TOP - BR_PLATE_T - 1, PLATE_TOP + 1, n=32))
    L.finish(m); return m

def check_motor_arm(m, report):
    check_arm(m, report)
    zp = PLATE_TOP - BR_PLATE_T / 2
    pilot = L.hole_diameter(m, MOTOR_R, 0, zp); assert abs(pilot - PILOT_D) < 0.05, pilot
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (MOTOR_R + sx * NEMA_PITCH / 2, sy * NEMA_PITCH / 2, zp)
            w = probe(m, c, (0, 1, 0)) + probe(m, c, (0, -1, 0)); l = probe(m, c, (1, 0, 0)) + probe(m, c, (-1, 0, 0))
            assert abs(w - SLOT_W) < 0.05 and abs(l - SLOT_L) < 0.05, (c, w, l)
    teeth_top = PLATE_TOP - BR_PLATE_T - HUB_L; teeth_bot = teeth_top - PULLEY_TEETH_W
    assert (teeth_bot - RING_H, teeth_top - RING_H) == BAND, (teeth_bot, teeth_top)
    assert PLATE_TOP - SHAFT_L <= teeth_bot, "shaft too short for the pulley"
    for s in (-1, 1):
        for z in (teeth_bot, (teeth_bot + teeth_top) / 2, teeth_top):
            p0 = Vector((MOTOR_R, s * PULLEY_R, z)); p1 = Vector((0, s * BIG_R, z))
            d = probe(m, p0, p1 - p0)
            assert d is None or d > (p1 - p0).length, ("belt run hits the arm", s, z, d)
    report[m.name].update({"pilot": pilot, "teeth_above_ring": [teeth_bot - RING_H, teeth_top - RING_H]})
```

Extend the bottom block with, after the plain arm line:

```python
m = motor_arm(); check_motor_arm(m, report); L.export(m, os.path.join(OUT, "spider-arm-motor.stl"))
```

- [ ] **Step 2: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/spider_base.py 2>&1 | grep "^SPIDER\|Assertion\|Error\|Traceback"`

Expected: `spider-arm-motor` with `"non_manifold": 0`, `"dims"` about `[275.0, 90.0, 88.0]`, `"diagonal"` under 250, `"pilot"` near 23, `"teeth_above_ring": [30.0, 42.0]`, and no belt assertion.

- [ ] **Step 3: Break test on the belt line**

Change `WIN_Z0` to `RING_H + 33.0` (the window then starts inside the belt band) and rerun. Expected: `AssertionError: ('belt run hits the arm', ...)`. Restore and rerun to green.

- [ ] **Step 4: Stage and propose the commit**

```bash
git add tools/blender/spider_base.py model/base/spider-arm-motor.stl
```

Proposed message: `Generate the spider base motor arm`, body: the walls carry a plate 53 mm up so the pulley hangs on the belt band, and the window exists because the belt runs cross the wall plane. Wait for approval.

---

### Task 4: Pad plug, assembly render, housekeeping

**Files:**
- Modify: `tools/blender/spider_base.py` (add `pad`, `render`; extend the bottom block)
- Create: `model/base/spider-pad.stl` (generated)
- Modify: `.gitignore` (add `model/base/*.png`)
- Modify: `model/parts-list.md` (four rows)

**Interfaces:**
- Consumes: everything above; Cults STLs `axis1-baseHolder.stl` and `axis-1-rotatingBase1.stl` (bottom of the base holder at z=32.5 in their own frame).
- Produces: `pad() -> object`, `render(r, a, m)`; PNGs `model/base/spider-iso.png`, `spider-side.png`.

- [ ] **Step 1: Add the pad and the render**

Insert after `BAND`:

```python
# ---- TPU foot pad plug
PAD_D, PAD_T, PEG_D, PEG_L, HEAD_D, HEAD_T = 24.0, 6.0, 5.8, 5.5, 6.5, 1.5    # head lands inside the foot counterbore
```

Insert after `check_motor_arm`:

```python
def pad():
    p = L.cyl_z("spider-pad", 0, 0, PAD_D / 2, 0, PAD_T)
    L.union(p, L.cyl_z("peg", 0, 0, PEG_D / 2, PAD_T - 0.01, PAD_T + PEG_L))
    L.union(p, L.cyl_z("head", 0, 0, HEAD_D / 2, PAD_T + PEG_L - 0.01, PAD_T + PEG_L + HEAD_T))
    L.finish(p); return p

def check_pad(p, report):
    st = L.stats(p); assert st["non_manifold"] == 0, st
    assert PAD_T + PEG_L + HEAD_T < PAD_T + FOOT_T and PAD_T + PEG_L > PAD_T + FOOT_T - FOOT_CB_DEPTH, "head must sit inside the counterbore"
    report["spider-pad"] = st

def render(r, a, m):
    """Assembly: ring, three plain arms, the motor arm at 180 deg, the Cults base holder and first
    rotating stage sitting on the ring top, a motor block and its pulley."""
    def instance(src, deg):
        o = src.copy(); o.data = src.data; bpy.context.scene.collection.objects.link(o)
        o.rotation_euler = (0, 0, math.radians(deg)); o.color = src.color; return o
    r.color = (0.85, 0.85, 0.85, 1); a.color = (0.6, 0.75, 0.9, 1); m.color = (0.9, 0.75, 0.5, 1)
    for deg in ARM_ANGLES:
        instance(m if deg == MOTOR_ARM_ANGLE else a, deg)
    a.hide_render = m.hide_render = True
    for name, color in (("axis1-baseHolder", (0.6, 0.6, 0.6, 1)), ("axis-1-rotatingBase1", (0.4, 0.6, 0.9, 1))):
        bpy.ops.wm.stl_import(filepath=os.path.join(CULTS, name + ".stl")); o = bpy.context.selected_objects[0]
        o.location.z = RING_H - 32.5; o.color = color
    mx = -MOTOR_R
    motor = L.box("motor", mx - 21.15, mx + 21.15, -21.15, 21.15, PLATE_TOP, PLATE_TOP + 48); motor.color = (0.2, 0.2, 0.2, 1)
    teeth_top = PLATE_TOP - BR_PLATE_T - HUB_L
    pulley = L.cyl_z("pulley", mx, 0, PULLEY_R, teeth_top - PULLEY_TEETH_W, teeth_top + HUB_L); pulley.color = (0.8, 0.7, 0.2, 1)
    scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; sh = scene.display.shading
    sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = 'OBJECT'
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1100
    cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.clip_end = 10000
    co = bpy.data.objects.new("c", cam); scene.collection.objects.link(co); scene.camera = co
    for name, rot, scale, target in (("spider-iso", (58, 0, 35), 900, (0, 0, 40)), ("spider-side", (88, 0, 90), 800, (0, 0, 60))):
        cam.ortho_scale = scale; co.rotation_euler = tuple(math.radians(v) for v in rot); bpy.context.view_layer.update()
        d = co.matrix_world.to_quaternion() @ Vector((0, 0, -1)); co.location = Vector(target) - d * 2000
        scene.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)
```

Extend the bottom block so it reads:

```python
bpy.ops.wm.read_factory_settings(use_empty=True)
report = {}
r = ring(); check_ring(r, report); L.export(r, os.path.join(OUT, "spider-ring.stl"))
a = arm("spider-arm"); check_arm(a, report); L.export(a, os.path.join(OUT, "spider-arm.stl"))
m = motor_arm(); check_motor_arm(m, report); L.export(m, os.path.join(OUT, "spider-arm-motor.stl"))
p = pad(); check_pad(p, report); L.export(p, os.path.join(OUT, "spider-pad.stl")); bpy.data.objects.remove(p)
print("SPIDER", json.dumps(report))
render(r, a, m)
print("SPIDER DONE")
```

- [ ] **Step 2: Run it and look at the renders**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/spider_base.py 2>&1 | grep "^SPIDER\|Assertion\|Error\|Traceback"`

Expected: the `SPIDER {...}` line now includes `spider-pad`, then `SPIDER DONE`. Open `model/base/spider-iso.png` and `spider-side.png`: four arms, the base holder centred on the ring, the motor block on the 180° arm, the pulley under its plate level with the rotating base's toothed band. If the pulley is not level with the band in the side view, the band height in the spec is wrong and the fix is `PLATE_TOP`, nothing else.

- [ ] **Step 3: Housekeeping**

Append `model/base/*.png` to `.gitignore`. Add to `model/parts-list.md` under the electronics row, taking dimensions from the `SPIDER` report:

```
| base | spider-ring (tools/blender/spider_base.py) | 200 x 200 x 35 | ~300 | fits |
| base | spider-arm ×3 | 275 x 90 x 35 | ~185 each | A1 on the diagonal |
| base | spider-arm-motor | 275 x 90 x 88 | ~230 | A1 on the diagonal |
| base | spider-pad ×4 (TPU) | 24 x 24 x 13 | ~3 each | A1 |
```

- [ ] **Step 4: Stage and propose the commit**

```bash
git add tools/blender/spider_base.py model/base/spider-pad.stl .gitignore model/parts-list.md
```

Proposed message: `Add the spider base pad plug and assembly render`. Wait for approval.

---

### Task 5: Bench, phase 1 — ring and one arm

**Files:**
- Modify: `docs/build-plan.md` (bench log line under the Octopus block)

- [ ] **Step 1: Print**

Ring: `spider-ring.stl` top plate down, PLA, 0.2 mm, four walls, 30 % gyroid, no supports. One plain arm: `spider-arm.stl` flat on its skin, turned 45° on the A1 bed, five walls, 30 %.

- [ ] **Step 2: Dry-fit**

Push the tenon into any facet by hand. It should seat to the boss face with light pressure and come out again by hand. Record: seated freely / needed sanding / would not enter. If it would not enter, measure the printed mortise with calipers, set `FIT` to the measured shortfall plus 0.3, regenerate, reprint the arm only.

- [ ] **Step 3: Nuts and bolts**

Drop an M5 nut into each cross pocket of the tenon, slide it home, drive two M5 × 30 from inside the ring. Both should pull the root face flat against the facet. Push eight M5 nuts into the top plate pockets from below; each should stay by friction.

- [ ] **Step 4: Log and propose the commit**

Add under the Octopus bench log in `docs/build-plan.md`:

```
  - **Spider base phase 1 <date>.** Ring and one arm printed. Tenon: <result>,
    FIT <value>. Joint bolts pull the root flat: <yes/no>. Nut pockets hold: <yes/no>.
```

`git add docs/build-plan.md`; proposed message `Log the spider base tenon fit`. Wait for approval.

---

### Task 6: Bench, phases 2 to 4 — full spider, stiffness, motor

**Files:**
- Modify: `docs/build-plan.md` (same log line extended)

- [ ] **Step 1: Print the rest**

Two more plain arms, `spider-arm-motor.stl` the same way as the plain arm, four `spider-pad.stl` in PolyFlex TPU95A on the A1 disc down.

- [ ] **Step 2: Bolt up and check flatness**

All four arms in, eight M5 × 30. Lay a straightedge across opposite arms over the ring top: the ring top should be within 0.5 mm of flat. Push a pad into each foot.

- [ ] **Step 3: Base on, stiffness, tipping**

Set `axis1-baseHolder` on the ring with eight M5 × 20 into the pocket nuts, then the rotating stages. Hook the luggage scale to a foot, pull sideways to 60 N, and measure the ring's movement against a fixed reference: under 1.5 mm passes. With the arm folded it should stand on its pads; with 2 kg held at 500 mm reach note whether it stays or needs a clamp on the far foot.

- [ ] **Step 4: Motor and belt**

Motor on the plate, shaft down, four M3 × 10 through the slots at mid-travel. 3M 30T pulley on the shaft, hub against the plate underside, grub screw on the flat. Belt round the pulley and the rotating base's band; slide the motor outward in its slots to tension, tighten. Check with a straightedge that the belt is centred on the band and does not touch the walls at the window. On the Octopus, with the axis-1 motor on MOTOR0 as X: `M906 X1200`, `M92 X8.89`, `G91`, `G1 X360 F600` and back, for a minute, and confirm no belt walk. Record the measured belt length.

- [ ] **Step 5: Log and propose the commit**

Extend the log line with the flatness, stiffness, tipping and belt results and the belt length. `git add docs/build-plan.md`; proposed message `Log the spider base bench results`. Wait for approval.

---

## Bill of materials

| Item | Qty | Note |
|---|---|---|
| M5 × 30 socket head + nut | 8 | arm joints |
| M5 × 20 + nut | 8 | base holder to ring, on the Cults list already |
| M3 × 10 | 4 | motor |
| 3M 30T pulley, 5 mm bore, 12 mm | 1 | confirm one is in hand from phase D |
| HTD 3M belt, about 620 mm | 1 | measure on the built base before buying |
| M5 × 25 | 4 | only for a plate |
| PLA | ~1.1 kg | ring 300 g, arms 185 g × 3, motor arm 230 g |
| PolyFlex TPU95A | ~15 g | four pads |

---

## Self-review

- Spec coverage: §5.1 ring (Task 1), §5.2 arm (Task 2), §5.3 motor arm (Task 3), §5.4 pad and §5.5 cables (Task 4, the cavity is open by construction), §5.6 hardware (BOM), §6 generator and every listed self-test (Tasks 1 to 3: manifold, diagonal, pattern, band arithmetic, belt ray cast, tenon clearance), §7 print rules (Tasks 5 and 6), §10 acceptance 1 to 5 (Tasks 5 and 6), §11 phasing (Tasks 5 and 6).
- Deviations from the spec are listed under Global Constraints with the reason for each.
- Names used across tasks: `slab`, `bar`, `hull8`, `probe`, `rail_outer`, `rail_top`, `arm`, `check_arm`, `motor_arm`, `check_motor_arm`, `pad`, `check_pad`, `render`, and the constants, are defined where the Interfaces blocks say.
