# Three-Finger Hand, Phase 2: Palm Front Plate and the Pair on One Base — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put both pair fingers on one printed base: the palm's front plate with two forks on 45 mm centres, a bench foot that bolts to the plate on the rear shell's bolt pattern, and a whiffletree bar, so a hand-pulled line closes both fingers and one blocked finger lets the other keep closing (spec acceptance 3 without the spool).

**Architecture:** One new generator, `tools/blender/hand_palm.py`, builds the plate, the foot and the bar from `hand_lib.py` with the same fork, bore, channel and flare calls the finger and fixture use, so a finger that fits the fixture fits the plate. Two small library changes let the fork and the line-of-sight check be placed off the z=0 plane. The generator measures what it cut and asserts it, like the finger generator; the bench steps are the physical test and their results go back into the repo.

**Tech Stack:** Blender 5.1 headless (`/Applications/Blender.app/Contents/MacOS/Blender -b -P <script>`), Python 3 inside Blender (bmesh, exact booleans, BVH ray casts), STL export, Bambu P2S at 0.2 mm in PLA.

**Spec:** `docs/superpowers/specs/2026-09-22-three-finger-hand-design.md` §5.3 (amended 2026-09-24), §5.1 for the fork, §5.4 whiffletree row, §10 item 3, §11 phase 2.

## Global Constraints

- Palm frame: x along the fingers (+x toward the fingertips), +y dorsal, z across the hand. Finger axes at x = 0, y = 0, z = ±22.5 (pitch 45).
- Fork exactly as `hand_lib.fork` builds it for the fixture: two 5 mm cheeks 8 mm long with heels, 0.5 mm clearance to a 12 mm tongue, finger width 23. Cheek bore from `model/hand/params.json` (`cheek_bore`, 3.90).
- Front plate 68 wide (z) × 50 tall (y, −25 to +25) × 12 deep (x, −20 to −8); the fork cheeks stand from x = −8 to 0. Outer cheeks flush with the plate's ends at z = ±34.
- Tendon channel Ø2.5 at y = −5 (1 mm below the finger's channel line, as on the fixture) and wire channel Ø1.8 at y = 0, each on its finger's z, straight through the plate, flared at the front (web) face with `hand_lib.flare`.
- Palm pad pocket Ø19 × 0.6 on the front face at y = −2, z = 0; tail slot 7 wide (z) × 1.2 tall (y) through the plate, its top at y = −11.6.
- Rear shell bolts: four Ø3.2 through the plate along x at y = ±20, z = ±28, counterbored Ø6 × 3 from the front face.
- Thumb cradle pilots: four Ø2.8 × 8 deep into the front face at y = −12 and −22, z = ±20.
- Bench foot: 10 mm block on the plate's rear face with Ø2.8 pilots on the shell pattern, Ø4 pass-throughs for the tendons and Ø3 for the wires, and a sole under the plate (x −30 to −8, y −33 to −25) with four Ø4.4 clamp holes. The sole never reaches past x = −8, where the curled fingers sweep.
- Whiffletree bar: 50 × 8 × 4, Ø1.5 holes at z = ±22.5, Ø2 in the middle, all along x.
- Coincident or tangent faces break the exact boolean (found on the spider base and the finger): every tool overlaps or clears the faces it meets by at least 0.2 mm.
- Print rule (spec §7): pin bores vertical, so the plate prints standing on one end face; the foot on its rear face; the bar flat.
- Repo conventions: scripts in `tools/blender/`, exports under `model/hand/`, PNG renders gitignored, one logical change per commit, ask before committing.

---

## File structure

| File | Responsibility |
|---|---|
| `tools/blender/hand_lib.py` | Modify: `fork`, `bore_cheeks` take a `zc` offset; `first_hit_x` takes a `z` |
| `tools/blender/hand_palm.py` | Create: constants, plate, foot, bar, checks, export, assembly render |
| `model/hand/palm-front.stl`, `palm-bench-foot.stl`, `palm-whiffletree-bar.stl` | Generated |
| `docs/build-plan.md` | Modify: bench log line for the pair test |

---

### Task 1: Library — forks and line checks off the centre plane

**Files:**
- Modify: `tools/blender/hand_lib.py` (`fork`, `bore_cheeks`, `first_hit_x`)

**Interfaces:**
- Produces: `fork(target, xa, with_heels=True, zc=0.0)`, `bore_cheeks(target, xa, d=CHEEK_BORE, zc=0.0)`, `first_hit_x(o, y, x_start, r=0.4, z=0.0)`. Defaults keep every existing caller's output byte-for-byte identical.

- [ ] **Step 1: Add the `zc` offset to `fork` and `bore_cheeks`**

Replace the two functions with:

```python
def fork(target, xa, with_heels=True, zc=0.0):
    """Add a fork whose axis is at x=xa, centred on z=zc: two cheeks from the web at xa-FORK_LEN,
    rounded R about the axis, plus the palmar heel stops. Cheek bore left to bore_cheeks()."""
    for zs in (1, -1):
        z0, z1 = sorted((zc + zs * (TONGUE / 2 + GAP), zc + zs * W / 2))
        union(target, box("cheek", xa - FORK_LEN, xa, -R, R, z0, z1))
        union(target, cyl_z("cheek_end", xa, 0, R, z0, z1))
        if with_heels:
            union(target, box("heel", xa + HEEL_X0, xa + HEEL_X1, HEEL_Y, -R + 0.01, z0, z1))

def bore_cheeks(target, xa, d=CHEEK_BORE, zc=0.0):
    cut(target, cyl_z("cheek_bore", xa, 0, d / 2, zc - W / 2 - 1, zc + W / 2 + 1))
```

- [ ] **Step 2: Add the `z` argument to `first_hit_x`**

Change its signature to `def first_hit_x(o, y, x_start, r=0.4, z=0.0):` and the ray origins to `Vector((x_start, y + dy, z + dz))`.

- [ ] **Step 3: Prove nothing else moved**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_finger.py 2>&1 | grep -E "^FINGER|Assertion"`
Expected: the FINGER line with every assert passing, and `git status` shows no change to any STL under `model/hand/` (the finger and fixture regenerate identically). If an STL changed, the offset default is wrong; fix before going on.

- [ ] **Step 4: Commit**

Stage `tools/blender/hand_lib.py` only. Proposed message: `Let a fork be placed off the centre plane` with a body saying the palm plate needs two forks on 45 mm centres from the same call the fixture uses.

---

### Task 2: Palm front plate, bench foot and whiffletree bar

**Files:**
- Create: `tools/blender/hand_palm.py`
- Generated: `model/hand/palm-front.stl`, `model/hand/palm-bench-foot.stl`, `model/hand/palm-whiffletree-bar.stl`, `model/hand/palm-iso.png` (gitignored)

**Interfaces:**
- Consumes: `hand_lib` — `box, cyl_z, cyl_between, union, cut, fork(zc=), bore_cheeks(zc=), channel, flare, finish, stats, hole_diameter, first_hit_x(z=), export`, constants `W, R, FORK_LEN, CHEEK_BORE, TENDON_Y, WIRE_D`.
- Produces: the three STLs above and a `PALM` report line.

- [ ] **Step 1: Write the generator**

```python
"""Phase 2 palm front: the plate both pair fingers hinge on, a bench foot that bolts to its rear
face on the rear shell's bolt pattern, and a whiffletree bar for a hand-pulled test. Palm frame =
the finger frame of a finger on the centre line: x along the fingers, +y dorsal, z across the hand;
finger axes at x=0, y=0, z=+-PITCH/2.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_palm.py"""
import bpy, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
from mathutils import Vector
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
_params = json.load(open(os.path.join(OUT, "params.json"))) if os.path.exists(os.path.join(OUT, "params.json")) else {}
CHEEK_BORE = _params.get("cheek_bore", L.CHEEK_BORE)

PITCH = 45.0                                    # finger axis to finger axis
FINGERS = (-PITCH / 2, PITCH / 2)
PLATE_T, PLATE_H = 12.0, 50.0
PLATE_W = PITCH + L.W                           # 68: outer cheeks flush with the ends
X_WEB, X_BACK = -L.FORK_LEN, -L.FORK_LEN - PLATE_T
Y0, Y1, Z0, Z1 = -PLATE_H / 2, PLATE_H / 2, -PLATE_W / 2, PLATE_W / 2
TENDON_Y = L.TENDON_Y - 1.0                     # as the fixture: 1 mm below the finger's channel line
TENDON_D = 2.5
PAD_D, PAD_DEPTH, PAD_Y = 19.0, 0.6, -2.0       # FSR 402 body 18.3
TAIL_W, TAIL_H, TAIL_Y1 = 7.0, 1.2, -11.6       # its tail, through to the rear face
SHELL_BOLTS = [(y, z) for y in (-20.0, 20.0) for z in (-28.0, 28.0)]
BOLT_D, BOLT_CB_D, BOLT_CB_DEPTH = 3.2, 6.0, 3.0
CRADLE_PILOTS = [(y, z) for y in (-12.0, -22.0) for z in (-20.0, 20.0)]
PILOT_D, PILOT_DEPTH = 2.8, 8.0
FOOT_T, SOLE_X0, SOLE_Y0, CLAMP_D = 10.0, -30.0, -33.0, 4.4
BAR_L, BAR_H, BAR_T = 50.0, 8.0, 4.0

def pilot(target, x_face, y, z, direction, d=PILOT_D, depth=PILOT_DEPTH):
    """Thread-forming M3 pilot into the face at x_face; direction is the way it goes into the part."""
    L.cut(target, L.cyl_between("pilot", (x_face - direction * 0.5, y, z), (x_face + direction * depth, y, z), d / 2))

# ---- front plate
plate = L.box("palm-front", X_BACK, X_WEB, Y0, Y1, Z0, Z1)
for zc in FINGERS:
    L.fork(plate, 0.0, zc=zc)
    L.bore_cheeks(plate, 0.0, CHEEK_BORE, zc=zc)
    L.cut(plate, L.cyl_between("tendon", (X_WEB + 1, TENDON_Y, zc), (X_BACK - 1, TENDON_Y, zc), TENDON_D / 2))
    L.cut(plate, L.cyl_between("wire", (X_WEB + 1, 0, zc), (X_BACK - 1, 0, zc), L.WIRE_D / 2))
    L.cut(plate, L.cyl_between("tendon_flare", (X_WEB + 0.05, TENDON_Y, zc), (X_WEB - 1.5, TENDON_Y, zc), 2.25, r_end=TENDON_D / 2))
    L.cut(plate, L.cyl_between("wire_flare", (X_WEB + 0.05, 0, zc), (X_WEB - 1.5, 0, zc), 1.4, r_end=L.WIRE_D / 2))
L.cut(plate, L.cyl_between("pad_pocket", (X_WEB + 1, PAD_Y, 0), (X_WEB - PAD_DEPTH, PAD_Y, 0), PAD_D / 2, n=64))
L.cut(plate, L.box("pad_tail", X_BACK - 1, X_WEB + 1, TAIL_Y1 - TAIL_H, TAIL_Y1, -TAIL_W / 2, TAIL_W / 2))
for y, z in SHELL_BOLTS:
    L.cut(plate, L.cyl_between("shell_bolt", (X_WEB + 1, y, z), (X_BACK - 1, y, z), BOLT_D / 2))
    L.cut(plate, L.cyl_between("shell_cb", (X_WEB + 1, y, z), (X_WEB - BOLT_CB_DEPTH, y, z), BOLT_CB_D / 2))
for y, z in CRADLE_PILOTS:
    pilot(plate, X_WEB, y, z, -1)
L.finish(plate)

# ---- bench foot: a block on the plate's rear face, bolted through the shell holes, with a sole
# under the plate that clamps to the bench. The sole stops at the web line so the curled fingers
# never sweep into it.
foot = L.box("palm-bench-foot", X_BACK - FOOT_T, X_BACK - 0.01, Y0, Y1, Z0, Z1)
L.union(foot, L.box("sole", SOLE_X0, X_WEB, SOLE_Y0, Y0 + 0.01, Z0, Z1))
for y, z in SHELL_BOLTS:
    pilot(foot, X_BACK, y, z, -1)
for zc in FINGERS:
    L.cut(foot, L.cyl_between("tendon_pass", (X_BACK + 1, TENDON_Y, zc), (X_BACK - FOOT_T - 1, TENDON_Y, zc), 2.0))
    L.cut(foot, L.cyl_between("wire_pass", (X_BACK + 1, 0, zc), (X_BACK - FOOT_T - 1, 0, zc), 1.5))
for x in (SOLE_X0 + 5, X_WEB - 5):
    for z in (-25.0, 25.0):
        L.cut(foot, L.cyl_between("clamp", (x, SOLE_Y0 - 1, z), (x, Y0 + 1, z), CLAMP_D / 2))
L.finish(foot)

# ---- whiffletree bar, modelled behind the foot where it floats in use
bar = L.box("palm-whiffletree-bar", X_BACK - FOOT_T - 20 - BAR_T, X_BACK - FOOT_T - 20, TENDON_Y - BAR_H / 2, TENDON_Y + BAR_H / 2, -BAR_L / 2, BAR_L / 2)
for z, d in ((-PITCH / 2, 1.5), (PITCH / 2, 1.5), (0.0, 2.0)):
    L.cut(bar, L.cyl_between("hole", (X_BACK - FOOT_T - 20 + 1, TENDON_Y, z), (X_BACK - FOOT_T - 20 - BAR_T - 1, TENDON_Y, z), d / 2))
L.finish(bar)

# ---- checks and export
report = {}
for o in (plate, foot, bar):
    report[o.name] = L.stats(o); L.export(o, os.path.join(OUT, o.name + ".stl"))
    assert report[o.name]["non_manifold"] == 0, o.name
report["cheek_bores"] = [L.hole_diameter(plate, 0, 0, zc + L.W / 2 - 2.5) for zc in FINGERS]
report["tendon_lines"] = [L.first_hit_x(plate, TENDON_Y, -40.0, z=zc) for zc in FINGERS]
report["wire_lines"] = [L.first_hit_x(plate, 0.0, -40.0, z=zc) for zc in FINGERS]
report["foot_tendon_lines"] = [L.first_hit_x(foot, TENDON_Y, -60.0, z=zc) for zc in FINGERS]
report["foot_wire_lines"] = [L.first_hit_x(foot, 0.0, -60.0, z=zc) for zc in FINGERS]
report["plate_dims"] = report["palm-front"]["dims"]
print("PALM", json.dumps(report))
for d in report["cheek_bores"]: assert abs(d - CHEEK_BORE) < 0.02, d
for key in ("tendon_lines", "wire_lines", "foot_tendon_lines", "foot_wire_lines"):
    assert report[key] == [None, None], (key, report[key])
assert report["plate_dims"] == [PLATE_T + L.FORK_LEN + L.R, PLATE_H, PLATE_W], report["plate_dims"]   # rounded cheek ends reach x=+R

# ---- assembly render: plate, foot, bar and both fingers straight
scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; sh = scene.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = 'OBJECT'
scene.render.resolution_x = 1600; scene.render.resolution_y = 1000
plate.color = (0.85, 0.85, 0.85, 1); foot.color = (0.75, 0.75, 0.7, 1); bar.color = (0.9, 0.6, 0.2, 1)
for zc in FINGERS:
    for name, x in (("finger-proximal", 0.0), ("finger-distal", 40.0)):
        path = os.path.join(OUT, name + ".stl")
        if not os.path.exists(path): continue
        bpy.ops.wm.stl_import(filepath=path); f = bpy.context.selected_objects[0]
        f.location = (x, 0, zc); f.color = (0.55, 0.7, 0.9, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = 150; cam.clip_end = 10000
co = bpy.data.objects.new("c", cam); scene.collection.objects.link(co); scene.camera = co
co.rotation_euler = (math.radians(60), 0, math.radians(35)); bpy.context.view_layer.update()
d = co.matrix_world.to_quaternion() @ Vector((0, 0, -1)); co.location = Vector((10, -5, 0)) - d * 600
scene.render.filepath = os.path.join(OUT, "palm-iso.png"); bpy.ops.render.render(write_still=True)
print("PALM DONE")
```

- [ ] **Step 2: Run it**

Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_palm.py 2>&1 | grep -E "^PALM|Assertion|Traceback|line [0-9]+, in"`
Expected: a `PALM` line with `cheek_bores` both within 0.02 of 3.90, all four line lists `[null, null]`, `plate_dims [26.0, 50.0, 68.0]`, then `PALM DONE`. A non-manifold plate almost always means a tool face landed on an existing face; move that tool by 0.2 mm and rerun. If a tendon line reports a hit inside the plate, the flare cone or the counterbore overlaps the channel; check the hit's x against the constants.

- [ ] **Step 3: Look at the render**

Open `model/hand/palm-iso.png`. Both fingers sit in their forks with the tabs over the cheeks, the pad pocket is between the inner cheeks, the four counterbores are on the front face, the foot's sole is behind the web line and the bar floats behind the foot.

- [ ] **Step 4: Parts list and commit**

Add three rows to `model/parts-list.md` under the hand group (dims from the PALM line). Stage `tools/blender/hand_palm.py`, the three STLs and `model/parts-list.md`. Proposed message: `Generate the palm front plate with both pair forks` with a body on why the plate carries the shell's bolt pattern now (the bench foot bolts to it, so the pair test proves the interface before the shell exists).

---

### Task 3: Bench — the pair on one base

**Files:**
- Modify: `docs/build-plan.md` (bench log)

- [ ] **Step 1: Print**

PLA, 0.2 mm, four walls, 40 % infill. `palm-front` standing on one end face (z = ±34 face down) so the cheek bores are vertical; the two inner cheeks overhang their fork slots by 8 mm exactly as the fixture's upper cheek does, so use whatever the fixture needed there. `palm-bench-foot` on its rear face. `palm-whiffletree-bar` flat. A second proximal and distal in the current geometry, and the skin and pad for the second finger in TPU.

- [ ] **Step 2: Assemble**

1. Foot to the plate: four M3 × 20 from the front counterbores through the plate into the foot's pilots. Clamp the sole to the bench edge, forks overhanging.
2. Each finger onto the plate exactly as onto the fixture (phase 1 plan Task 2 step 8): dowels into the tongue, tongue into the fork, 4 × 8 spring pins flush from each cheek.
3. Both wire pairs and both tendons pushed in from the tips with the fingers straight, straight through the plate and out through the foot.
4. Each tendon through a Ø1.5 end hole of the bar and knotted behind it; a pull line through the centre hole, knotted.
5. Skins: the plate has no strip pockets, so for this test glue each skin's dorsal end to the plate's top face at its finger's z, 10 mm behind the web line, with CA. The rear shell plan decides the permanent pocket.

- [ ] **Step 3: Test (spec acceptance 3 without the spool)**

- Pull the centre line: both fingers curl together, both return when released.
- Hold one finger straight by hand and pull: the other still curls to its stops, the bar tilts, and nothing binds at the bar's end holes.
- Mug: wrap an 80 mm mug with the fingers, note the pull needed by feel.
- Note the pull-line travel for full curl of both (expected about 16 mm at the bar) — this sets the spool's turn in phase 3.

- [ ] **Step 4: Record**

Add a bench log line to `docs/build-plan.md` after the 2026-09-24 finger entry: what the whiffletree did with one finger blocked, the travel, and anything that rubbed at the plate's flares. Stage and propose: `Log the pair on the palm front plate`.

---

## Bill of materials

| Item | Qty | Note |
|---|---|---|
| M3 × 20 stainless, socket head | 4 | plate to foot; the same four fix the plate to the rear shell in phase 3 |
| M3 × 8 stainless | 4 | thumb cradle, later |
| 20 lb braided line | have | two tendons and the pull line |
| ISO 8752 4 × 8 spring pins, Ø2 × 8 dowels | 4 + 4 | second finger, from the phase 1 order |
| FSR 402 | 1 | phase 5 fits it; the pocket is printed now |

## Self-review

- Spec coverage: §5.3 front plate items (forks, channels, pad pocket, shell bolts, cradle pilots) → Task 2 constants and cuts; bench foot and bar → Task 2; §11 phase 2 → Task 3. The rear shell and thumb cradle are deliberately not in this plan.
- Types: `fork(zc=)` and `bore_cheeks(zc=)` in Task 1 match every call in Task 2; `first_hit_x(z=)` likewise; `cyl_between(r_end=)` already exists in the library.
- Known gap: the plate has no strip pockets for the skins' dorsal ends; Task 3 glues them to the top face for the bench and the rear shell plan decides the permanent detail.
