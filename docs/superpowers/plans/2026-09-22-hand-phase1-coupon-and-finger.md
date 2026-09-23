# Three-Finger Hand, Phase 1: Pin Coupon and One Finger — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print-validate the knuckle: find the cheek bore that grips an ISO 8752 4 × 20 spring pin in PLA, then print one pair finger on a bench fixture that curls on a string, springs back on its TPU skin, and carries a sensor wire through both pins for 100 cycles. The skin is one TPU part: return spring along the back, wrap around the tip, grip pad over the sensor pocket on the inside.

**Architecture:** Geometry is generated headlessly in Blender from one shared library (`hand_lib.py`) so the palm in later phases reuses the same fork, tongue, bore and groove definitions. Each generator script is also its own test: it measures the bores it cut and asserts manifold meshes, and a separate check script assembles the finger at a sweep of angles and asserts zero interference between the stops and contact beyond them. The bench steps are the physical tests and their results are written back into the repo.

**Tech Stack:** Blender 5.1 headless (`/Applications/Blender.app/Contents/MacOS/Blender -b -P <script>`), Python 3 inside Blender (bmesh, exact booleans, BVH ray casts), STL export, Bambu P2S at 0.2 mm in PLA; Bambu A1 for the TPU (Polymaker PolyFlex TPU95A).

**Spec:** `docs/superpowers/specs/2026-09-22-three-finger-hand-design.md` (sections 5.1, 5.5, 7, 10 items 1 and 2, 11 phase 1). The tactile spec `docs/superpowers/specs/2026-09-21-gripper-tactile-sensing-design.md` is referenced only for the wire.

## Global Constraints

- Finger frame: x along the finger from base to tip, +y dorsal, z across the width; knuckle axes run along z.
- Finger width across the pin 20 mm: two 5 mm cheeks, 9 mm tongue, 0.5 mm clearance each side. Height 12 mm. Phalanges 40 mm proximal, 30 mm distal.
- Pin ISO 8752 4 × 20 mm stainless 1.4310. Cheek bore 3.85 mm nominal, coupon at 3.80, 3.85, 3.90. Tongue bore 4.2 mm.
- Tendon channel 2 mm on the palm side, 6 mm off each knuckle axis (it rides the R6 rounded tongue end). Wire channel 1.5 mm. Wire chamber 4 mm.
- Return and grip are one TPU part: an 8 × 1.8 mm dorsal run, a 14 mm wide wrap and palmar pad with a moulded dome over the sensor, a 20 mm T bar with two M2 holes. Printed flat. Wire 30 AWG PTFE, two per sensor.
- Distal phalanx carries the FSR 400 pocket on its palmar face (phase 5 fits the sensor; phase 1 prints the pocket).
- Proximal phalanx carries a snap-on TPU grip pad on its inside face: 14 mm long, 1.8 mm plate with a 2.6 mm through-slot for the tendon, 2 mm wings up the sides and 1 mm lips into side grooves at y −4 to −2.5, plus two Ø2.4 snap dots standing 1 mm proud of its inner face on a diagonal, into Ø2.7 dimples in the phalanx's palmar face.
- Flexion stop about 87°, extension stop about 3° of hyperextension, both printed (spec 5.1 says "printed stop").
- Print rule (spec 7): phalanges print lying on a cheek so the pin bores are vertical; no supports anywhere.
- Repo conventions: scripts in `tools/blender/`, one `ROOT`-style absolute path, exports under `model/`, PNG renders gitignored, one logical change per commit, ask before committing.

---

## File structure

| File | Responsibility |
|---|---|
| `tools/blender/hand_lib.py` | Create: the shared knuckle geometry — constants, primitives, `fork`, `tongue`, bores, grooves, pockets, mesh stats, bore measurement, STL export |
| `tools/blender/hand_coupon.py` | Create: the two pin-fit coupons and their self-check |
| `tools/blender/hand_finger.py` | Create: proximal, distal, bench fixture and the TPU skin, self-check, reads `model/hand/params.json` for the chosen bore |
| `tools/blender/hand_check.py` | Create: assembles the finger at a sweep of knuckle angles, asserts interference, renders |
| `model/hand/*.stl` | Generated parts (committed, like the other STLs) |
| `model/hand/params.json` | Create by hand after the coupon test: `{"cheek_bore": <mm>}` |
| `.gitignore` | Modify: add `model/hand/*.png` |
| `model/parts-list.md` | Modify: rows for the phase 1 parts |
| `docs/build-plan.md` | Modify: bench log entry with the coupon and finger results |

---

### Task 1: Geometry library and pin coupons

**Files:**
- Create: `tools/blender/hand_lib.py`
- Create: `tools/blender/hand_coupon.py`
- Create: `model/hand/coupon-forks.stl`, `model/hand/coupon-tongues.stl` (generated)

**Interfaces:**
- Produces: `hand_lib` module — constants `W, H, CHEEK, TONGUE, GAP, R, FORK_LEN, TONGUE_LEN, CHEEK_BORE, TONGUE_BORE, TAB_Y0, TAB_Y1, TAB_BACK, HEEL_X0, HEEL_X1, HEEL_Y, TENDON_W, TENDON_DEPTH, WIRE_D, CHAMBER, STRIP_W, STRIP_T, PAD_L`; functions `box(name,x0,x1,y0,y1,z0,z1)`, `cyl_z(name,x,y,r,z0,z1)`, `cyl_between(name,a,b,r)`, `boolean(target,tool,op)`, `union(target,tool)`, `cut(target,tool)`, `fork(target,xa,with_heels=True)`, `bore_cheeks(target,xa,d=CHEEK_BORE)`, `tongue(target,xa,direction=1)`, `bore_tongue(target,xa,direction=1)`, `tendon_groove(target,x0,x1)`, `strip_pocket(target,x0,x1)`, `sphere(name,x,y,z,r)`, `dot_positions(x0,x1)`, `snap_dimples(target,x0,x1)`, `snap_grooves(target,x0,x1)`, `snap_pad(name,length,thickness=1.8,wing=2.0,slot=2.6) -> object`, `finish(o)`, `stats(o) -> dict(dims, faces, non_manifold)`, `hole_diameter(o,x,y,z_probe) -> float`, `export(o,path)`. All geometry functions take a Blender object and modify it in place with exact booleans; `direction` is +1 when the phalanx body lies on the +x side of the tongue axis.

- [ ] **Step 1: Write the library**

`tools/blender/hand_lib.py`:

```python
"""Shared geometry for the three-finger hand (spec 2026-09-22). Finger frame: x along the
finger from base to tip, +y dorsal, z across the width. Knuckle axes run along z."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

W, H = 20.0, 12.0            # finger width across the pin, height
CHEEK, TONGUE, GAP = 5.0, 9.0, 0.5
R = H / 2                    # rounded knuckle ends
FORK_LEN = 8.0               # web to axis
TONGUE_LEN = 7.0             # axis to the wide body
CHEEK_BORE, TONGUE_BORE = 3.85, 4.2
TAB_Y0, TAB_Y1, TAB_BACK = 6.3, 7.8, 3.0          # dorsal extension stop over the cheeks
HEEL_X0, HEEL_X1, HEEL_Y = -8.0, -3.5, -7.2       # palmar flexion stop under the cheeks (~87 deg)
TENDON_W, TENDON_DEPTH = 2.0, 2.0
WIRE_D, CHAMBER = 1.5, 4.0
STRIP_W, STRIP_T, PAD_L = 8.0, 2.0, 8.0            # TPU return strip
SNAP_Y0, SNAP_Y1, SNAP_DEPTH = -4.0, -2.5, 1.0      # side grooves that a snap-on grip pad's lips engage
DOT_R, DOT_H, DOT_Z = 1.2, 1.0, 5.5                 # front snap dots on the pad, dimples in the palmar face

def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

def box(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return _obj(name, bm)

def cyl_z(name, x, y, r, z0, z1, n=64):
    """Cylinder along z (a knuckle axis or bore)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(x, y, (z0 + z1) / 2), verts=bm.verts)
    return _obj(name, bm)

def cyl_between(name, a, b, r, n=32):
    """Cylinder from point a to point b (wire channels)."""
    a, b = Vector(a), Vector(b); d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=d.length + 0.02)
    o = _obj(name, bm)
    o.matrix_world = Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    return o

def boolean(target, tool, op):
    m = target.modifiers.new(op, "BOOLEAN"); m.operation = op; m.solver = 'EXACT'; m.object = tool
    bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(tool)

def union(target, tool): boolean(target, tool, 'UNION')
def cut(target, tool): boolean(target, tool, 'DIFFERENCE')

def fork(target, xa, with_heels=True):
    """Add a fork whose axis is at x=xa: two cheeks from the web at xa-FORK_LEN, rounded R
    about the axis, plus the palmar heel stops. Cheek bore left to bore_cheeks()."""
    for zs in (1, -1):
        z0, z1 = sorted((zs * (TONGUE / 2 + GAP), zs * W / 2))
        union(target, box("cheek", xa - FORK_LEN, xa, -R, R, z0, z1))
        union(target, cyl_z("cheek_end", xa, 0, R, z0, z1))
        if with_heels:
            union(target, box("heel", xa + HEEL_X0, xa + HEEL_X1, HEEL_Y, -R + 0.01, z0, z1))

def bore_cheeks(target, xa, d=CHEEK_BORE):
    cut(target, cyl_z("cheek_bore", xa, 0, d / 2, -W / 2 - 1, W / 2 + 1))

def tongue(target, xa, direction=1):
    """Add a tongue whose axis is at x=xa, body side toward +x*direction. Rounded end R about
    the axis, a taller dorsal section joining the full-width tab that stops hyperextension.
    Bore, chamber and tendon ring are cut afterwards by bore_tongue()."""
    s = direction
    x_body = xa + s * TONGUE_LEN
    x0, x1 = sorted((xa, x_body))
    union(target, box("tongue", x0, x1, -R, TAB_Y1, -TONGUE / 2, TONGUE / 2))
    union(target, cyl_z("tongue_end", xa, 0, R, -TONGUE / 2, TONGUE / 2))
    tx0, tx1 = sorted((xa - s * TAB_BACK, x_body + s * 0.01))
    union(target, box("tab", tx0, tx1, TAB_Y0, TAB_Y1, -W / 2, W / 2))

def bore_tongue(target, xa, direction=1):
    s = direction
    cut(target, cyl_z("tongue_bore", xa, 0, TONGUE_BORE / 2, -W / 2 - 1, W / 2 + 1))
    # wire chamber: where the wire leaves the pin slot and twists
    cx0, cx1 = sorted((xa + s * 1.5, xa + s * (1.5 + CHAMBER)))
    cut(target, box("chamber", cx0, cx1, -CHAMBER / 2, CHAMBER / 2, -CHAMBER / 2, CHAMBER / 2))
    # tendon ring: 2 mm wide groove around the palmar half of the rounded end
    ring = cyl_z("ring", xa, 0, R + 0.5, -TENDON_W / 2, TENDON_W / 2)
    boolean(ring, cyl_z("ring_in", xa, 0, R - TENDON_DEPTH, -TENDON_W / 2 - 1, TENDON_W / 2 + 1), 'DIFFERENCE')
    boolean(ring, box("ring_clip", xa - R - 1, xa + R + 1, -R - 1, 0.0, -2, 2), 'INTERSECT')
    cut(target, ring)

def tendon_groove(target, x0, x1):
    cut(target, box("groove", x0, x1, -R - 0.1, -R + TENDON_DEPTH, -TENDON_W / 2, TENDON_W / 2))

def strip_pocket(target, x0, x1):
    """Dorsal pocket for the glued end of the TPU skin (its return-spring run)."""
    cut(target, box("pocket", x0, x1, R - STRIP_T - 0.2, R + 0.1, -(STRIP_W + 2.2) / 2, (STRIP_W + 2.2) / 2))

def sphere(name, x, y, z, r, n=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=n // 2, radius=r)
    bmesh.ops.translate(bm, vec=(x, y, z), verts=bm.verts)
    return _obj(name, bm)

def dot_positions(x0, x1):
    """Two front snap dots on a diagonal so the pad is located lengthwise as well."""
    return ((x0 + (x1 - x0) * 0.25, DOT_Z), (x0 + (x1 - x0) * 0.75, -DOT_Z))

def snap_dimples(target, x0, x1):
    """Dimples in the palmar face that the pad's front dots snap into."""
    for x, z in dot_positions(x0, x1):
        cut(target, sphere("dimple", x, -R - (DOT_R - DOT_H) , z, DOT_R + 0.15))

def snap_grooves(target, x0, x1):
    """Grooves along both side faces near the palmar edge for a snap-on TPU grip pad."""
    for zs in (1, -1):
        z0, z1 = sorted((zs * (W / 2 - SNAP_DEPTH), zs * (W / 2 + 1)))
        cut(target, box("snap", x0, x1, SNAP_Y0, SNAP_Y1, z0, z1))

def snap_pad(name, length, thickness=1.8, wing=2.0, slot=2.6):
    """Snap-on TPU grip pad: a palmar plate with a through-slot for the tendon, two wings up
    the side faces and inward lips that drop into snap_grooves(). Modelled in place on a
    phalanx whose palmar face is y=-R, from x=0 to x=length."""
    y_face = -R
    pad = box(name, 0, length, y_face - thickness, y_face, -W / 2 - wing, W / 2 + wing)
    for zs in (1, -1):
        z0, z1 = sorted((zs * (W / 2 + 0.1), zs * (W / 2 + wing)))
        union(pad, box("wing", 0, length, y_face - thickness, SNAP_Y1, z0, z1))
        l0, l1 = sorted((zs * (W / 2 - SNAP_DEPTH + 0.1), zs * (W / 2 + 0.1 + 0.01)))
        union(pad, box("lip", 0, length, SNAP_Y0 + 0.1, SNAP_Y1 - 0.1, l0, l1))
    cut(pad, box("tendon_slot", -1, length + 1, y_face - thickness - 1, y_face + 1, -slot / 2, slot / 2))
    for x, z in dot_positions(0, length):
        union(pad, sphere("dot", x, y_face - (DOT_R - DOT_H), z, DOT_R))   # hemisphere standing DOT_H proud of the plate
    return pad

def finish(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bm.to_mesh(o.data); bm.free()

def stats(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold); bm.free()
    d = o.dimensions
    return {"dims": [round(d.x, 2), round(d.y, 2), round(d.z, 2)], "faces": len(o.data.polygons), "non_manifold": nm}

def hole_diameter(o, x, y, z_probe):
    """Measure a z-axis bore at (x, y) by casting rays outward in the plane z=z_probe."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    import mathutils
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); ds = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        hit = tree.ray_cast(Vector((x, y, z_probe)), Vector((math.cos(a), math.sin(a), 0)))
        if hit[0] is not None: ds.append((hit[0] - Vector((x, y, z_probe))).length)
    bm.free()
    return round(2 * sum(ds) / len(ds), 3) if ds else None

def export(o, path):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
```

- [ ] **Step 2: Write the coupon generator with its assertions**

`tools/blender/hand_coupon.py`. The assertions at the end are the test: every mesh manifold and every measured bore within 0.02 mm of nominal. The notches on the dorsal face label the bores (one notch = smallest).

```python
"""Pin-fit coupons for the three-finger hand: three forks with 3.80/3.85/3.90 mm cheek bores
and three tongues with 4.1/4.2/4.3 mm bores, for ISO 8752 4 x 20 spring pins.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_coupon.py"""
import bpy, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
PITCH = 30.0
FORK_BORES = (3.80, 3.85, 3.90)
TONGUE_BORES = (4.1, 4.2, 4.3)

forks = L.box("coupon-forks", -14, PITCH * 2 + 1, -L.R, L.R, -L.W / 2, L.W / 2)   # common bar, the "web"
for i, d in enumerate(FORK_BORES):
    xa = i * PITCH
    L.fork(forks, xa)
    L.bore_cheeks(forks, xa, d)
    L.cut(forks, L.box("label", xa - 12 + 0.0, xa - 12 + 2 * (i + 1), L.R - 0.6, L.R + 0.1, 6, 8))  # i+1 notches on the dorsal face
L.finish(forks)

tongues = L.box("coupon-tongues", 1, PITCH * 2 + 13, -L.R, L.R, -L.W / 2, L.W / 2)
for i, d in enumerate(TONGUE_BORES):
    xa = i * PITCH + 7
    # a tongue pointing -x out of the bar, body side +x
    L.tongue(tongues, xa, direction=1)
    L.cut(tongues, L.cyl_z("tb", xa, 0, d / 2, -L.W, L.W))
    L.cut(tongues, L.box("label", xa + 10, xa + 10 + 2 * (i + 1), L.R - 0.6, L.R + 0.1, 6, 8))
L.finish(tongues)

report = {}
for o, bores, ys in ((forks, FORK_BORES, 7.5), (tongues, TONGUE_BORES, 0.0)):
    st = L.stats(o); measured = []
    for i, d in enumerate(bores):
        xa = i * PITCH + (0 if o is forks else 7)
        measured.append(L.hole_diameter(o, xa, 0, ys))
    report[o.name] = {**st, "bores_nominal": list(bores), "bores_measured": measured}
    L.export(o, os.path.join(OUT, o.name + ".stl"))
for name, r in report.items():
    assert r["non_manifold"] == 0, name
    for nom, meas in zip(r["bores_nominal"], r["bores_measured"]):
        assert abs(nom - meas) < 0.02, (name, nom, meas)
print("COUPON", json.dumps(report))
```

- [ ] **Step 3: Run it and confirm the assertions pass**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_coupon.py 2>&1 | grep "^COUPON\|Assertion\|Error"`

Expected: one `COUPON {...}` line with `"non_manifold": 0` for both parts and `bores_measured` of about `[3.797, 3.847, 3.897]` and `[4.097, 4.197, 4.297]`; no `AssertionError`. Two STLs appear in `model/hand/`.

- [ ] **Step 4: Break it on purpose, then restore**

Change the fork loop's `L.bore_cheeks(forks, xa, d)` to `L.bore_cheeks(forks, xa, d + 0.5)` so the cut no longer matches the nominal, and rerun. Expected: `AssertionError: ('coupon-forks', 3.8, 4.297)` or similar, proving the measurement is live. (Changing `FORK_BORES` itself does not break it, because the cut and the expectation move together.) Restore the line and rerun to green.

- [ ] **Step 5: Stage and propose the commit** (the user approves commits)

```bash
git add tools/blender/hand_lib.py tools/blender/hand_coupon.py model/hand/coupon-forks.stl model/hand/coupon-tongues.stl
```

Proposed message: `Add the knuckle geometry library and pin-fit coupons for the hand` with a body saying why a coupon exists (spring pin grip in PLA is print-dependent and sets the bore for every knuckle).

- [ ] **Step 6: Bench — print and test the coupons**

Print both coupons in PLA, 0.2 mm, four walls, lying on a cheek face so the bores are vertical (the STL's z axis is the bore axis: slice with z up). No supports.

For each fork, press a 4 × 20 pin through both cheeks with a vice or arbor press, slot facing the open side:
- record whether the cheek split, and whether the pin holds a 5 kg pull (hang a filament spool from a string through the pin, or pull with a luggage scale)
- the smallest bore that neither splits nor lets the pin walk is the build value; if two pass, take the larger

For each tongue, slide a pin through: it must rotate freely by hand with no felt slop at 4.2; note if 4.1 binds or 4.3 rattles.

- [ ] **Step 7: Record the result**

Create `model/hand/params.json`:

```json
{"cheek_bore": 3.85}
```

with the value you chose. Also note in `docs/build-plan.md` under the Octopus bench log a line: "Hand pin coupon <date>: 3.80 split / 3.85 held 5 kg / 3.90 walked" (whatever was observed) and the tongue result. Stage both and propose a commit: `Record the spring pin bore that holds in PLA`.

---

### Task 2: One finger, fixture and skin, with the angle sweep check

**Files:**
- Create: `tools/blender/hand_finger.py`
- Create: `tools/blender/hand_check.py`
- Create: `model/hand/finger-proximal.stl`, `finger-distal.stl`, `finger-fixture.stl`, `finger-skin.stl`, `finger-pad-proximal.stl` (generated)
- Modify: `.gitignore` (add `model/hand/*.png`)

**Interfaces:**
- Consumes: everything in `hand_lib` listed in Task 1; `model/hand/params.json` from Task 1 step 7 (falls back to `hand_lib.CHEEK_BORE` if absent).
- Produces: the four STLs; the environment variable `HAND_OUT` overrides the output folder for scratch runs.

- [ ] **Step 1: Write the finger generator with its assertions**

`tools/blender/hand_finger.py`:

```python
"""Phase 1 finger for the three-finger hand: proximal and distal phalanges, a bench fixture
that stands in for the palm fork, and the one-piece TPU skin. Frame per hand_lib.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_finger.py"""
import bpy, os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
PARAMS = os.path.join(OUT, "params.json")          # written after the coupon test: {"cheek_bore": 3.85}
CHEEK_BORE = json.load(open(PARAMS))["cheek_bore"] if os.path.exists(PARAMS) else L.CHEEK_BORE
PROX_LEN, DIST_LEN = 40.0, 30.0
W2, R = L.W / 2, L.R

# ---- proximal phalanx: base tongue at x=0, tip fork axis at x=PROX_LEN
prox = L.box("finger-proximal", L.TONGUE_LEN, PROX_LEN - L.FORK_LEN, -R, R, -W2, W2)
L.tongue(prox, 0.0, direction=1)
L.fork(prox, PROX_LEN)
L.bore_tongue(prox, 0.0, direction=1)
L.bore_cheeks(prox, PROX_LEN, CHEEK_BORE)
L.tendon_groove(prox, 0.0, PROX_LEN - L.FORK_LEN + 0.1)
L.strip_pocket(prox, PROX_LEN - L.FORK_LEN - 2 - L.PAD_L, PROX_LEN - L.FORK_LEN - 2)
PAD_X0, PAD_X1 = 12.0, 26.0                        # snap-on grip pad on the inside of the proximal
L.snap_grooves(prox, PAD_X0, PAD_X1)
L.snap_dimples(prox, PAD_X0, PAD_X1)
# wire: external groove on the +z face from the tip pin end back 12 mm, then a channel
# diving to the base chamber
L.cut(prox, L.box("wire_groove", PROX_LEN - 12, PROX_LEN + 0.1, -L.WIRE_D / 2, L.WIRE_D / 2, W2 - L.WIRE_D, W2 + 0.1))
L.cut(prox, L.cyl_between("wire_dive", (PROX_LEN - 12, 0, W2 - L.WIRE_D / 2), (L.TONGUE_LEN - 2, 0, 0), L.WIRE_D / 2))
L.finish(prox)

# ---- distal phalanx: base tongue at x=0, rounded tip at x=DIST_LEN. The TPU skin wraps the
# tip and covers the palmar face, so the sensor pocket, its tail cavity and the skin's two
# M2 anchor holes are on the palmar side; the tendon anchors just past the knuckle.
dist = L.box("finger-distal", L.TONGUE_LEN, DIST_LEN - R, -R, R, -W2, W2)
L.union(dist, L.cyl_z("tip", DIST_LEN - R, 0, R, -W2, W2))
L.tongue(dist, 0.0, direction=1)
L.bore_tongue(dist, 0.0, direction=1)
TENDON_ANCHOR_X = 14.0
L.tendon_groove(dist, 0.0, TENDON_ANCHOR_X + 1.0)
L.cut(dist, L.cyl_between("anchor_hole", (TENDON_ANCHOR_X, -R - 1, 0), (TENDON_ANCHOR_X, R + 1, 0), 0.75))
L.cut(dist, L.box("ferrule", TENDON_ANCHOR_X - 1.5, TENDON_ANCHOR_X + 1.5, R - 2.0, R + 0.5, -1.5, 1.5))
# skin anchor: two M2 pilot holes on the palmar face, either side of the tendon groove
SKIN_EAR_X, SKIN_EAR_Z = 10.0, 6.0
for z in (-SKIN_EAR_Z, SKIN_EAR_Z):
    L.cut(dist, L.cyl_between("ear_pilot", (SKIN_EAR_X, -R - 1, z), (SKIN_EAR_X, -R + 4, z), 0.8))
# FSR 400 pocket on the palmar face (7.6 mm body), tail slot up into a solder cavity, and the
# wire channel from that cavity to the tongue chamber, offset in z to miss the tendon hole
SENSOR_X = 21.0
L.cut(dist, L.cyl_between("fsr_pocket", (SENSOR_X, -R - 1, 0), (SENSOR_X, -R + 0.6, 0), 4.0))
L.cut(dist, L.box("tail_slot", SENSOR_X - 4.5, SENSOR_X - 3.0, -R + 0.5, -R + 1.6, -2.0, 2.0))
L.cut(dist, L.box("solder_cavity", SENSOR_X - 4.5, SENSOR_X + 3.5, -R + 1.5, -R + 4.5, -2.5, 2.5))
L.cut(dist, L.cyl_between("wire_run", (SENSOR_X - 4.0, -R + 3.0, 2.5), (L.TONGUE_LEN - 2.0, 0.0, 1.5), L.WIRE_D / 2))
L.finish(dist)

# ---- snap-on TPU grip pad for the proximal's inside face, modelled in place then exported
pad = L.snap_pad("finger-pad-proximal", PAD_X1 - PAD_X0)
pad.location.x = PAD_X0
L.finish(pad)

# ---- bench fixture: a block with the palm-side fork for the proximal base, a tendon exit
# hole, a strip pocket, and a foot to clamp to the bench
fix = L.box("finger-fixture", -30, -L.FORK_LEN, -R, R, -W2, W2)
L.fork(fix, 0.0)
L.bore_cheeks(fix, 0.0, CHEEK_BORE)
# the foot stays behind the fork (x <= -8.5) so the curling finger never sweeps into it
L.union(fix, L.box("foot", -30, -8.5, -R - 12, -R + 0.01, -W2 - 10, W2 + 10))
L.cut(fix, L.cyl_between("tendon_exit", (-8, -R + 1, 0), (-31, -R + 1, 0), 1.5))
L.strip_pocket(fix, -8 - 2 - L.PAD_L, -8 - 2)
L.cut(fix, L.box("wire_groove", -30.1, 0.1, -L.WIRE_D / 2, L.WIRE_D / 2, W2 - L.WIRE_D, W2 + 0.1))
for x in (-24, -14):
    for z in (-W2 - 5, W2 + 5):
        L.cut(fix, L.cyl_between("clamp", (x, -R - 12.1, z), (x, -R + 0.1, z), 2.2))
L.finish(fix)

# ---- TPU skin: one flat part. Dorsal run (return spring) from the fixture pocket over both
# knuckles to the start of the tip round, then the wrap around the R6 tip, then the palmar pad
# over the sensor with a moulded dome, ending in a T bar with two M2 holes. Printed flat.
TIP_START = PROX_LEN + DIST_LEN - R                    # world x where the tip round begins
DORSAL = TIP_START - (-8 - 2 - L.PAD_L)                # fixture pad start to tip start
WRAP = math.pi * (R + L.STRIP_T / 2)                    # half circumference at mid-thickness
PAD_W, PAD_END = 14.0, TIP_START - (PROX_LEN + SKIN_EAR_X)   # pad runs back to the ears
T_W, T_L = 20.0, 4.0
x_wrap0, x_pad0 = DORSAL, DORSAL + WRAP
skin = L.box("finger-skin", 0, x_wrap0, 0, L.STRIP_T - 0.2, -L.STRIP_W / 2, L.STRIP_W / 2)
L.union(skin, L.box("wrap", x_wrap0 - 0.01, x_pad0 + 0.01, 0, L.STRIP_T - 0.2, -PAD_W / 2, PAD_W / 2))
L.union(skin, L.box("pad", x_pad0 - 0.01, x_pad0 + PAD_END, 0, L.STRIP_T - 0.2, -PAD_W / 2, PAD_W / 2))
L.union(skin, L.box("tbar", x_pad0 + PAD_END - T_L, x_pad0 + PAD_END, 0, L.STRIP_T - 0.2, -T_W / 2, T_W / 2))
dome_x = x_pad0 + (TIP_START - (PROX_LEN + SENSOR_X))   # over the sensor centre
L.union(skin, L.cyl_between("dome", (dome_x, -0.01, 0), (dome_x, -1.5, 0), 2.5, n=48))   # bump on the inside face
for z in (-SKIN_EAR_Z, SKIN_EAR_Z):
    L.cut(skin, L.cyl_between("ear_hole", (x_pad0 + PAD_END - T_L / 2, -2, z), (x_pad0 + PAD_END - T_L / 2, 3, z), 1.1))
L.finish(skin)
span = round(x_pad0 + PAD_END, 1)

report = {}
for o in (prox, dist, fix, skin, pad):
    report[o.name] = L.stats(o); L.export(o, os.path.join(OUT, o.name + ".stl"))
report["cheek_bore_measured"] = L.hole_diameter(prox, PROX_LEN, 0, 7.5)
report["tongue_bore_measured"] = L.hole_diameter(dist, 0, 0, 3.5)
report["skin_flat_length"] = span
report["skin_dorsal_run"] = round(DORSAL, 1); report["skin_wrap"] = round(WRAP, 1)
for name in ("finger-proximal", "finger-distal", "finger-fixture", "finger-skin", "finger-pad-proximal"):
    assert report[name]["non_manifold"] == 0, name
assert abs(report["cheek_bore_measured"] - CHEEK_BORE) < 0.02
assert abs(report["tongue_bore_measured"] - L.TONGUE_BORE) < 0.02
print("FINGER", json.dumps(report))
```

- [ ] **Step 2: Run it and confirm the assertions pass**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_finger.py 2>&1 | grep "^FINGER\|Assertion\|Error"`

Expected: one `FINGER {...}` line, all four parts `"non_manifold": 0`, `finger-proximal` dims about `[52.0, 15.0, 20.0]`, `finger-distal` about `[36.0, 13.8, 20.0]`, `finger-fixture` about `[36.0, 24.0, 40.0]`, `finger-skin` about `[118.0, 3.3, 20.0]` (flat length 118: 82 dorsal run, 22 wrap, 14 pad), `finger-pad-proximal` `[14.0, 5.3, 24.0]`, `cheek_bore_measured` within 0.02 of the params value, `tongue_bore_measured` about 4.197.

- [ ] **Step 3: Write the angle sweep check**

`tools/blender/hand_check.py`. This is the test for the stops: it places the distal on the proximal's tip axis and the proximal on the fixture's axis at a list of flexion angles (positive curls toward the palm) and measures the intersection volume in mm³. Free travel must be exactly zero from 3° of hyperextension through 87° of flexion; 90° and 6° of hyperextension must interfere, which is the stop engaging. It also renders two views.

```python
"""Assemble the phase 1 finger at a sweep of knuckle angles and measure interference volume,
then render. Positive flexion curls toward the palm (-y)."""
import bpy, bmesh, os, sys, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ["HAND_OUT"]
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, name + ".stl")); o = bpy.context.selected_objects[0]; o.name = name; return o
def volume(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); v = bm.calc_volume(); bm.free(); return v
def interference(a, b):
    """Volume of a AND b, using a copy of a."""
    c = a.copy(); c.data = a.data.copy(); bpy.context.scene.collection.objects.link(c)
    m = c.modifiers.new("i", "BOOLEAN"); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = b
    bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier=m.name)
    v = volume(c) if len(c.data.polygons) else 0.0
    bpy.data.objects.remove(c); return v
prox, dist, fix = load("finger-proximal"), load("finger-distal"), load("finger-fixture")
PROX_LEN = 40.0
def place(o, xa, deg):
    o.matrix_world = Matrix.Translation((xa, 0, 0)) @ Matrix.Rotation(math.radians(-deg), 4, 'Z')
    bpy.context.view_layer.update()
res = {}
for deg in (-6, -3, 0, 20, 45, 70, 80, 85, 87, 90, 95):
    place(dist, PROX_LEN, deg); place(prox, 0, 0)
    res[f"distal@{deg}"] = round(interference(dist, prox), 2)
for deg in (-3, 0, 45, 85, 90, 95):
    place(prox, 0, deg); place(dist, PROX_LEN, 0)   # distal rides along; only fixture/prox checked
    res[f"proximal@{deg}"] = round(interference(prox, fix), 2)
    if 0 < res[f"proximal@{deg}"] < 5:
        c = prox.copy(); c.data = prox.data.copy(); bpy.context.scene.collection.objects.link(c)
        m = c.modifiers.new("i", "BOOLEAN"); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = fix
        bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier=m.name)
        pts = [c.matrix_world @ v.co for v in c.data.vertices]
        if pts: res[f"proximal@{deg}_bbox"] = [[round(min(p[i] for p in pts),2), round(max(p[i] for p in pts),2)] for i in range(3)]
        bpy.data.objects.remove(c)
free = [k for k in res if k.endswith(("@-3", "@0", "@20", "@45", "@70", "@80", "@85", "@87"))]
assert all(res[k] == 0.0 for k in free), {k: res[k] for k in free if res[k]}
assert res["distal@90"] > 0 and res["distal@-6"] > 0 and res["proximal@90"] > 0
print("CHECK", json.dumps(res))
# render: straight and curled
scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; sh = scene.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = 'OBJECT'
prox.color = (0.2, 0.6, 0.95, 1); dist.color = (0.95, 0.5, 0.1, 1); fix.color = (0.6, 0.6, 0.6, 1)
scene.render.resolution_x = 1600; scene.render.resolution_y = 900
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = 130; cam.clip_end = 1000
co = bpy.data.objects.new("c", cam); scene.collection.objects.link(co); scene.camera = co
for tag, pd, dd in (("straight", 0, 0), ("curled", 85, 85)):
    place(prox, 0, pd)
    # distal axis is at the proximal tip after the proximal rotates
    tip = Vector((PROX_LEN, 0, 0)); tipw = prox.matrix_world @ tip
    dist.matrix_world = Matrix.Translation(tipw) @ Matrix.Rotation(math.radians(-(pd + dd)), 4, 'Z')
    bpy.context.view_layer.update()
    co.rotation_euler = (math.radians(60), 0, math.radians(30)); bpy.context.view_layer.update()
    d = co.matrix_world.to_quaternion() @ Vector((0, 0, -1)); co.location = Vector((25, -10, 0)) - d * 400
    scene.render.filepath = os.path.join(OUT, f"finger-{tag}-iso.png"); bpy.ops.render.render(write_still=True)
    co.rotation_euler = (math.radians(90), 0, 0); co.location = (25, -10, 400) if False else (25, -400, 0)
    co.rotation_euler = (math.radians(90), 0, 0); bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUT, f"finger-{tag}-side.png"); bpy.ops.render.render(write_still=True)
print("CHECK DONE")
```

- [ ] **Step 4: Run the check**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_check.py 2>&1 | grep "^CHECK\|Assertion\|Error"`

Expected: `CHECK {...}` with `distal@-3` through `distal@87` all `0.0`, `distal@90` about `5.0`, `distal@-6` about `0.11`, `proximal@-3` through `proximal@85` all `0.0`, `proximal@90` about `5.0`; then `CHECK DONE`. Two PNGs per pose appear in `model/hand/`.

- [ ] **Step 5: Break it on purpose, then restore**

In `hand_lib.py` change `HEEL_X1 = -3.5` to `-1.5` (heel reaches further under the joint), regenerate with `hand_finger.py`, rerun `hand_check.py`. Expected: `AssertionError` listing `distal@85` or `distal@87` with a non-zero volume, because the stop now engages early. Restore `-3.5`, regenerate, rerun to green.

- [ ] **Step 6: Ignore the renders and stage**

Append `model/hand/*.png` to `.gitignore`. Then:

```bash
git add .gitignore tools/blender/hand_finger.py tools/blender/hand_check.py model/hand/finger-proximal.stl model/hand/finger-distal.stl model/hand/finger-fixture.stl model/hand/finger-skin.stl model/hand/finger-pad-proximal.stl
```

Proposed message: `Generate the phase 1 finger, fixture and one-piece skin` with a body on why the check exists (the two printed stops are the only thing keeping the pinch load off the pins' bores and the thumb gears).

- [ ] **Step 7: Bench — print**

PLA, 0.2 mm, four walls, 40 % infill: `finger-proximal`, `finger-distal`, `finger-fixture`, each lying on a cheek face (STL z up), no supports. The fixture's clamp holes are 4.4 mm for M4.
TPU, on the A1 with PolyFlex TPU95A: `finger-skin`, flat as exported (dome side up), 0.2 mm, 100 % infill, 25 mm/s, retraction 1 mm or off, 220 to 230 °C, filament dried. The dome is a 1.5 mm bump on the inside face; print with that face up so it needs no support.
Also in TPU on the A1: `finger-pad-proximal`, plate face down, wings up; the 1 mm inward lips at the top of the wings are a short overhang TPU bridges without support.

- [ ] **Step 8: Bench — assemble**

1. Thread two 30 AWG PTFE wires through a 4 × 20 pin; repeat for a second pin.
2. Distal onto the proximal: tongue into the fork, wires from the distal's wire channel into the chamber; push the pin through with the slot toward the tongue, wires exiting the slot into the chamber, wire ends out the pin end on the +z face. Press the pin flush.
3. Proximal onto the fixture the same way; the proximal's wires run in the +z face groove from the tip pin end, down the diving channel into the base chamber, through the base pin's slot, and out that pin's end at the fixture.
4. Tendon: 0.5 mm stainless leader (or 20 lb braided line for the first try) from the fixture's exit hole, along the palmar groove, over both rounded tongue ends, up the anchor hole at the distal tip, crimped or knotted in the ferrule pocket.
5. Skin: seat the dorsal end in the fixture pocket with CA and let it cure. With the finger straight, lay the run over both tabs and along the distal's back, wrap it around the tip, and bring the pad back along the inside so the dome sits over the sensor pocket. Fix the T bar with two M2 × 4 screws into the pilot holes either side of the tendon groove. The wrap should be just taut with the finger straight; if it is slack, shorten the dorsal end by 2 mm and re-glue.
6. Snap the proximal pad on: the two dots are on a diagonal, so it only fits one way round; line them up with the dimples, spread the wings over the phalanx sides with the slot over the tendon groove, and press until the dots seat and both lips drop into the side grooves. It should need a fingernail to remove and not peel off the front when you push a thumb across it.
7. Clamp the fixture to the bench edge, finger overhanging.

- [ ] **Step 9: Bench — test (spec acceptance 1 and 2)**

- Pull the tendon: both knuckles curl, distal first is fine, to the stops; release: the finger returns to straight within a second. If it does not return, the skin is too long: shorten the dorsal end by 2 mm and re-glue, or print it 0.4 mm thicker by editing `STRIP_T`. Check the wrap has not crept off the tip after curling.
- 100 pull-and-release cycles. Afterwards: pins have not walked (flush both sides), no cracks at the cheeks, the wires show continuity end to end with a meter and no visible chafe at the pin ends.
- Hyperextension: push the distal back by hand; it stops within a few degrees, on the tab.
- Record: chosen skin trim, the return time, anything that rubbed, whether the pad stays centred on the sensor pocket, and whether the proximal pad stayed snapped on through the 100 cycles.

- [ ] **Step 10: Record**

Add the five parts and both coupons to `model/parts-list.md` under a `hand` group (dimensions from the FINGER and COUPON report lines). Add the bench results to the build-plan bench log line started in Task 1. Stage and propose: `Log the first finger's bench results`.

---

## Bill of materials

**Phase 1, order now.** Quantities cover the coupon, one finger, and spares.

| Item | Qty | Note |
|---|---|---|
| ISO 8752 slotted spring pin 4 × 20, stainless (A2 / 1.4310) | 10 | you may already have some; 6 go into the full hand |
| 30 AWG PTFE-insulated wire, silver-plated, two colours | 5 m each | must be PTFE; PVC is too thick for the pin bore |
| Stainless leader wire, 1×7, 0.45 to 0.5 mm (about 20 lb) | 5 m | nylon-coated is fine |
| Crimp sleeves for that leader (single barrel, 0.8 mm ID) | 20 | |
| TPU filament | have | Polymaker PolyFlex TPU95A, printed on the A1 |
| 3 mm pin punch | 1 | to remove pins from coupons and rejects |
| Thin CA glue | 1 | skin end into the fixture pocket |
| M2 × 4 screws | 4 | skin T bar, phase 1 |
| M4 × 25 bolts and nuts | 4 | clamp the fixture, or use a bench clamp |
| Luggage scale or 5 kg weight | 1 | coupon pull test |

**Full hand, order once.** Everything else from spec §5.7, so a single order covers phases 2 to 5.

| Item | Qty | Note |
|---|---|---|
| NEMA11 stepper, 0.67 A, 45 mm (e.g. STEPPERONLINE 11HS18-0674S, about 95 mN·m) | 1 | corrects the spec's "32 mm class": 32 mm bodies are 60 mN·m; 45 mm fits the 55 mm adapter tube with the shaft length 20 mm |
| TMC2209 driver modules for the Octopus, with UART jumper | 2 | MOTOR7 and MOTOR3 |
| FSR 400 (7.6 mm) | 3 | fingertips |
| FSR 402 (18 mm) | 1 | palm pad |
| ADS1115 breakout with STEMMA QT / QWIIC (Adafruit 1085) | 1 | lives in the palm |
| 10 kΩ 1 % resistors | 4 | dividers |
| QWIIC cable 500 mm | 1 | palm to wrist segment |
| Microswitch with lever, 12 × 6 mm | 2 | U and V homing |
| M2 × 4 screws | 8 | skin T bars (2 per finger) |
| M2.5 × 6 screws | 4 | NEMA11 to the palm |
| M3 × 12 and M3 × 20 stainless, nuts | 4 + 2 | flange and palm halves |
| M3 grub screws | 2 | worm hub |
| M4 × 8 | 2 | 28BYJ-48 ears |
| PTFE grease, small tube | 1 | worm |

---

## Self-review

- **Spec coverage.** 5.1 fingers: Task 2 geometry, all numbers match the Global Constraints. 5.5 wire route through the pins: Task 2 (groove, diving channel, chambers, exits) and bench step 8. 7 print rules: steps 7 in Task 2, orientation and no supports. 10 acceptance 1 and 2: Task 1 step 6 and Task 2 step 9. 11 phase 1: whole plan. Not in phase 1 by design: fingertip caps (phase 5), palm (phase 2), which is why the distal tip is a plain rounded end with the wire exit and tendon anchor only.
- **Placeholders.** None: every step has its file contents or its exact bench procedure.
- **Consistency.** `hand_check.py` uses `PROX_LEN = 40.0` matching `hand_finger.py`; both use the fixture's fork axis at x = 0 and the proximal tip axis at x = 40; the skin's flat length 118 mm printed by `hand_finger.py` is the dorsal run (fixture pad start x = −18 to the tip round at x = 64), the half-circumference wrap at mid-thickness (22 mm), and the pad back to the T bar at x = 50 (14 mm).
- **Known weak point, stated.** The skin's dorsal end is glued into the fixture pocket; if CA on TPU fails on the bench, the fix is a keeper bar screwed over the pad, a small edit to `strip_pocket` and a new part. The far end is screwed, not glued, on purpose: that is the end under wrap tension.
- **Spec deviation, deliberate.** Spec 5.5 had a separate PLA cap with a snap-on skin; this plan builds the wrap-around one-piece skin agreed on 2026-09-22, and the spec has been amended to match.
