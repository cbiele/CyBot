# Axis 4 Forearm Tube Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Printable parts for a slim forearm: a 20:1 compact at the elbow end turns the 190 mm aluminium tube, which runs inside a fixed printed outer tube and ends in a flange for the future axis 5 fork. The parts are then laid out in the head concept.

**Architecture:**
- A new pure-Python module `forearm_dims.py` holds the axial stack in one frame. Both scripts import it so they can't disagree.
  - `forearm_tube.py` builds, checks and exports the four printed parts.
  - `head_concept.py` gains a `--tube-forearm` variant that imports those STLs.
- Checks are in-script asserts, as in `cycloid_poc.py`. A failing assert is the failing test.

**Tech Stack:** Blender 5.1 Python (bpy, bmesh), `tools/blender/hand_lib.py` helpers, `cycloid_math.py`.

**Spec:** `docs/superpowers/specs/2026-11-15-axis4-forearm-tube-design.md`

## Global Constraints

- **Run Blender with:** `/Applications/Blender.app/Contents/MacOS/Blender -b -P <script> [-- flags]`. Each script prints a `... DONE` line at the end.
- **Units are mm.**
- **Forearm frame:**
  - x runs along the roll axis.
  - x = 0 is the compact housing's rear face, the same as `cycloid_poc.py`'s z.
  - For the parts, x maps to z.
- **Aluminium tube:** 9 ID × 11 OD × 190 long (`TUBE_L = 190.0`, one constant so it can be cut shorter later).
- **Tube sockets:** printed Ø11.0, a press fit plus CA glue (proven with `eccentric-tube-lobes`).
- **6701 bearings:** 12 × 18 × 4.
  - They run on the existing `model/cycloid-poc/20-1-hollow-t8/tube-end-sleeve.stl` (Ø11.95 × Ø11 × 4). Reuse that file and don't regenerate it.
  - Bearing seats are Ø18.0. Outer-ring lips leave a bore of r 7.2, the same as `RELIEF_R` on the T8 carriers.
- **Compact output** (from `cycloid_poc.py`, default build):
  - Housing length 38.6, with the hub face 1.0 proud (x 39.6). The hub is Ø20.
  - Three M3 heat-set inserts on R6.5 at 90°, 210° and 330°.
  - Four M3 housing bolts on R30 at 45° + 90k (clearance hole r 1.7).
- **Fixings:** M3 heat-set insert holes are r 2.0 and 5.0 deep. M3 clearance holes are r 1.7. M3 socket-head counterbores are r 3.0.
- **Build order:** every part is built and checked in the forearm frame. Print orientation is applied only at export, after all checks have run, with `matrix_world` reset first.
- **Every printed part:** zero non-manifold edges (`L.stats(o)["non_manifold"] == 0`). Export with `L.export` into `model/forearm-tube/` in print orientation, flat face on z = 0.
- **Commits:** do not commit without the user's approval. Stage only the files named in the task; the working tree has the user's other uncommitted work. End messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Don't touch:** `cycloid_poc.py`, anything under `model/cycloid-poc/`, the existing `head_concept.py` variants' outputs (`head-concept.blend`, `head-concept-t8.blend`, `head-concept-compact.blend` and their PNG folders).

## Review Focus

1. **Screw access:** all three output-plate screws must be drivable with the plate on the hub. Each counterbore must open to the plate's front face clear of the dogs.
2. **Bearing preload:** each hub must touch only its 6701's inner ring, never the outer ring or shield. Total axial play must be 0.2 to 0.5, not zero; zero binds the roll.
3. **Turning parts against fixed parts:** at any roll angle, the plate, tube hub and wrist hub must not touch the outer tube or the compact's front housing. That includes the housing's bolt heads (3 tall on R30).
4. **Elbow clearance:** everything in axis 4, including the pancake on top and the 40T behind the mount, stays outside the V1 elbow disk (r 69.8 about x = 0, z = 453 in world).
5. **Reach:** the new pitch axis x has to be reported against V1's 250, so the user sees what the 190 tube costs.

The checks for these are in tasks 2, 3 and 4.

---

### Task 1: Axial stack and the outer tube

**Files:**
- Create: `tools/blender/forearm_dims.py`
- Create: `tools/blender/forearm_tube.py`

**Interfaces:**
- Produces (`forearm_dims.py`, plain constants in the forearm frame, no bpy):
  - Compact and fixings: `HOUSING_L = 38.6`, `HUB_FACE = 39.6`, `HOUSING_R = 34.0`, `BOLT_R = 30.0`, `BOLT_ANGLES = [45, 135, 225, 315]`, `INSERT_PCD_R = 6.5`, `INSERT_ANGLES = [90, 210, 330]`.
  - Tube and bearings: `TUBE_L = 190.0`, `TUBE_R = 5.5`, `SOCKET_DEPTH = 15.0`, `BRG_W = 4.0`, `BRG_SEAT_R = 9.0`, `LIP_R = 7.2`, `BRG_PLAY = 0.2`, `LAND_T = 0.3`, `LAND_R0, LAND_R1 = 6.0, 6.9`.
  - Plate: `PLATE_X = (39.6, 44.6)`, `PLATE_R = 14.0`, `DOG_PCD_R = 10.5`, `DOG_R = 2.5`, `DOG_H = 4.0`, `DOG_ANGLES = [30, 150, 270]`.
  - Tube hub: `HUB_X = (45.1, 62.1)`, `HUB_R = 14.0`.
  - Tube: `TUBE_X = (HUB_X[1] - SOCKET_DEPTH, HUB_X[1] - SOCKET_DEPTH + TUBE_L)`, which is (47.1, 237.1).
  - Rear 6701: `REAR_BRG_X = (HUB_X[1] + LAND_T + BRG_PLAY, ... + BRG_W)`, which is (62.6, 66.6).
  - Wrist hub: `WRIST_X = (TUBE_X[1] - SOCKET_DEPTH, TUBE_X[1] + 3.0)`, which is (222.1, 240.1). `WRIST_R = 15.0`, `FLANGE_INSERT_R = 11.0`, `FLANGE_ANGLES = [45, 135, 225, 315]`. `FLANGE_FACE = WRIST_X[1]`.
  - Front 6701: `FRONT_BRG_X = (WRIST_X[0] - LAND_T - BRG_PLAY - BRG_W, WRIST_X[0] - LAND_T - BRG_PLAY)`, which is (217.6, 221.6).
  - Outer tube: `OUTER_X = (HOUSING_L, FRONT_BRG_X[1])`, `OUTER_FLANGE_T = 5.0`, `OUTER_REAR_R = 18.0` (the wall round the hubs), `OUTER_R = 12.5` (the body, Ø25), `OUTER_HUB_BORE_R = 15.0`.
- Produces (`forearm_tube.py`): `outer_tube() -> bpy.types.Object`, built in the forearm frame (x along z), and `PARTS: dict[str, Object]`, `CHECKS: list[callable]`, following `cycloid_poc.py`'s pattern.

- [ ] **Step 1: Write the check first.** In `forearm_tube.py`, add `check_outer_tube()` with these asserts:

```python
o = PARTS["forearm-outer-tube"]
assert L.stats(o)["non_manifold"] == 0
assert abs(L.hole_diameter(o, 0, 0, sum(REAR_BRG_X) / 2) - 2 * BRG_SEAT_R) < 0.05, "rear 6701 seat"
assert abs(L.hole_diameter(o, 0, 0, sum(FRONT_BRG_X) / 2) - 2 * BRG_SEAT_R) < 0.05, "front 6701 seat"
assert abs(L.hole_diameter(o, 0, 0, 150.0) - 2 * LIP_R) < 0.05, "middle bore = lips"
assert LIP_R - TUBE_R >= 1.5, "tube rubs the middle bore"
assert abs(L.hole_diameter(o, 0, 0, HUB_X[0] + 5) - 2 * OUTER_HUB_BORE_R) < 0.05, "bore round the turning hubs"
assert OUTER_HUB_BORE_R - HUB_R >= 1.0 and OUTER_HUB_BORE_R - PLATE_R >= 1.0
assert OUTER_R - BRG_SEAT_R >= 3.0, "front seat wall under 3"
assert abs(L.stats(o)["dims"][2] - (OUTER_X[1] - OUTER_X[0])) < 0.01
```

- [ ] **Step 2: Run it before `outer_tube()` exists.**
  - Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/forearm_tube.py`
  - Expected: it fails with a `NameError` or `KeyError` for `forearm-outer-tube`.

- [ ] **Step 3: Write `forearm_dims.py` with the values above.** In `forearm_tube.py`, write `outer_tube()`:
  - **Flange:** `OUTER_X[0]` to `+OUTER_FLANGE_T`. Its outer edge is r `HOUSING_R` and its bore is r `OUTER_HUB_BORE_R`. It has four r 1.7 holes on `BOLT_R` at `BOLT_ANGLES`, for longer M3 bolts through the mount, housing and flange.
  - **Rear section:** r `OUTER_REAR_R` with bore r `OUTER_HUB_BORE_R`, up to `REAR_BRG_X[0]`.
  - **Rear seat:** r `BRG_SEAT_R`, `REAR_BRG_X`, with the lip at its front.
  - **Transition:** a 45° cone from `OUTER_REAR_R` down to `OUTER_R`.
  - **Body:** r `OUTER_R` with bore r `LIP_R`, up to `FRONT_BRG_X[0]`.
  - **Front seat:** r `BRG_SEAT_R`, `FRONT_BRG_X`, open to the front face.
  - **Print orientation:** flange down. That means translating by `-OUTER_X[0]` in z; no flip is needed. Export to `model/forearm-tube/forearm-outer-tube.stl`.
  - **End of script:** run `CHECKS`, print `FOREARM` with a JSON report of the dims of each part, export, then print `FOREARM DONE`.

- [ ] **Step 4: Run it again.**
  - Expected: `FOREARM DONE`, no assertion errors, and `model/forearm-tube/forearm-outer-tube.stl` about 183 tall.

- [ ] **Step 5: Ask the user, then commit** `tools/blender/forearm_dims.py`, `tools/blender/forearm_tube.py` and `model/forearm-tube/forearm-outer-tube.stl`. Message: why the forearm structure is a fixed printed tube carrying the bending, with the aluminium only turning.

---

### Task 2: Output plate and tube hub (the dog coupling)

**Files:**
- Modify: `tools/blender/forearm_tube.py`

**Interfaces:**
- Consumes: the Task 1 constants and `PARTS`/`CHECKS`.
- Produces: `output_plate() -> Object` (`"ax4-output-plate"`) and `tube_hub() -> Object` (`"ax4-tube-hub"`), both built in the forearm frame. Also `overlap(a, b) -> float`: the shared volume in mm³ of two objects at their current `matrix_world`, worked on copies with `L.boolean(..., 'INTERSECT')`, the same as `cycloid_poc.overlap`.

- [ ] **Step 1: Write `check_coupling()`.**

```python
p, h = PARTS["ax4-output-plate"], PARTS["ax4-tube-hub"]
for o in (p, h):
    assert L.stats(o)["non_manifold"] == 0
assert abs(L.hole_diameter(h, 0, 0, HUB_X[1] - SOCKET_DEPTH / 2) - 2 * TUBE_R) < 0.03, "Ø11.0 socket"
assert L.bore_floor_z(h, 0, 0, HUB_X[1] + 1) is not None, "socket has a floor"
for a in INSERT_ANGLES:                      # screw heads reachable from the front
    x, y = polar(INSERT_PCD_R + 2.3, a)      # inside the counterbore, outside the clearance hole
    assert abs(L.bore_floor_z(p, x, y, PLATE_X[1] + 10) - (PLATE_X[1] - 3.2)) < 0.05, "counterbore not open to the front"
    assert min(math.dist(polar(INSERT_PCD_R, a), polar(DOG_PCD_R, d)) for d in DOG_ANGLES) - 3.0 - DOG_R >= 1.0, "dog over a screw head"
assert DOG_PCD_R + DOG_R <= PLATE_R - 1.0 and DOG_PCD_R - DOG_R - 0.25 - TUBE_R >= 1.5, "dog hole breaks into the socket or the rim"
assert PLATE_X[1] - PLATE_X[0] - 3.2 >= 1.8, "too little plate under the screw heads"
housing = import_stl(COMPACT + "/housing-front.stl", flipped_to_assembly=True)
assert overlap(p, housing) < 0.05 and overlap(h, PARTS["forearm-outer-tube"]) < 0.05 and overlap(p, PARTS["forearm-outer-tube"]) < 0.05
assert overlap(p, h) < 0.05, "dogs bind in their holes"
```

`COMPACT` is `model/cycloid-poc/20-1-compact`. `housing-front.stl` was exported flipped (`PRINT_FLIP`). Undo that with `Matrix.Diagonal((1, -1, -1, 1))` and a translation by `2 * Z_MID = 38.6` (the mid-plane mirror in `cycloid_poc.mirror_to_front`). Then confirm its z range is about 19.3 to 38.6 and assert that range. Model the bolt heads on the housing's front face as four r 2.75 × 3 cylinders on `BOLT_R` and include them in the `overlap(p, ...)` check.

- [ ] **Step 2: Run it.** Expected: it fails with a `KeyError` on `ax4-output-plate`.

- [ ] **Step 3: Write `output_plate()`.**
  - A disc r `PLATE_R` spanning `PLATE_X`.
  - Three M3 r 1.7 through holes on `INSERT_PCD_R` at `INSERT_ANGLES`, with r 3.0 counterbores 3.2 deep from the front face.
  - Three dogs r `DOG_R` × `DOG_H` on its front face on `DOG_PCD_R` at `DOG_ANGLES`.
  - Print it with the hub face down; no flip needed.

- [ ] **Step 4: Write `tube_hub()`.**
  - A disc r `HUB_R` spanning `HUB_X`.
  - Dog holes r `DOG_R + 0.25`, `DOG_H + 0.5` deep, from the rear face.
  - The Ø11.0 socket, `SOCKET_DEPTH` deep, from the front face.
  - An inner-ring land on the front face: a ring from r `LAND_R0` to `LAND_R1`, `LAND_T` proud.
  - Print it with the socket opening up, which means the rear face down.

- [ ] **Step 5: Run it.** Expected: `FOREARM DONE`, plus the two new STLs.

- [ ] **Step 6: Ask the user, then commit** `forearm_tube.py` and the two STLs. Message: why the plate drives through dogs (screw heads on R6.5 overlap an Ø11 socket, and the proven carrier stays unchanged).

---

### Task 3: Wrist flange hub and bearing play

**Files:**
- Modify: `tools/blender/forearm_tube.py`

**Interfaces:**
- Consumes: the Task 1 and 2 constants, `overlap`, `PARTS`.
- Produces: `wrist_hub() -> Object` (`"wrist-flange-hub"`). Its flange pattern (r `WRIST_R`, four M3 inserts on R `FLANGE_INSERT_R` at `FLANGE_ANGLES`, face at `FLANGE_FACE`) is the interface the axis 5 fork adopts later.

- [ ] **Step 1: Write `check_wrist_and_play()`.**

```python
w = PARTS["wrist-flange-hub"]
assert L.stats(w)["non_manifold"] == 0
assert abs(L.hole_diameter(w, 0, 0, WRIST_X[0] + SOCKET_DEPTH / 2) - 2 * TUBE_R) < 0.03
for a in FLANGE_ANGLES:
    x, y = polar(FLANGE_INSERT_R, a)
    assert abs(L.bore_floor_z(w, x, y, FLANGE_FACE + 1) - (FLANGE_FACE - 5.0)) < 0.05, "flange insert depth"
assert FLANGE_INSERT_R - 2.0 - TUBE_R >= 2.0 and WRIST_R - FLANGE_INSERT_R - 2.0 >= 1.5
assert overlap(w, PARTS["forearm-outer-tube"]) < 0.05
play_rear = REAR_BRG_X[0] - (HUB_X[1] + LAND_T)
play_front = (WRIST_X[0] - LAND_T) - FRONT_BRG_X[1]
assert 0.2 <= play_rear + play_front <= 0.5, "roll binds or rattles"
assert LAND_R1 < LIP_R and LAND_R0 >= 6.0, "a land reaches the outer ring or misses the inner ring"
assert TUBE_X[1] - TUBE_X[0] == TUBE_L
```

- [ ] **Step 2: Run it.** Expected: it fails with a `KeyError` on `wrist-flange-hub`.

- [ ] **Step 3: Write `wrist_hub()`.**
  - A disc r `WRIST_R` spanning `WRIST_X`.
  - The Ø11.0 socket, `SOCKET_DEPTH` deep, from the rear face.
  - The inner-ring land on the rear face, matching the tube hub's.
  - Four r 2.0 × 5.0 insert holes in the front face.
  - Print it flange face down: flip it with `Matrix.Diagonal((1, -1, -1, 1))` on the mesh (not as an object rotation, which `cycloid_poc.py` notes tilts the face), then translate so the minimum z = 0.

- [ ] **Step 4: Run it.** Add a `"reach"` entry to the `FOREARM` report: `FLANGE_FACE` plus the play sums. Expected: `FOREARM DONE` and four STLs in `model/forearm-tube/`.

- [ ] **Step 5: Ask the user, then commit** `forearm_tube.py` and `wrist-flange-hub.stl`. Message: why the wrist end is a flange (the fork isn't designed yet, so it adopts this pattern).

---

### Task 4: `--tube-forearm` layout in the head concept

**Files:**
- Modify: `tools/blender/head_concept.py`

**Interfaces:**
- Consumes: `forearm_dims` (import it as `F`) and the four STLs in `model/forearm-tube/`.
- Produces:
  - `model/head-concept-tube.blend`
  - `model/head-concept/tube-forearm/*.png`
  - A `HEAD` JSON line with `pitch_x`, `reach_vs_v1_mm`, `axis4_min_to_elbow_axis_mm` and `axis4_clash_tris_with_v1_arm`.

- [ ] **Step 1: Add the asserts to `check()` under `if TUBE_FOREARM:`.**

```python
ax4 = world_verts(col="Axis 4 compact, 188 belt, drives the tube")
elbow = min(math.hypot(p.x, p.z - 453.0) for p in ax4)
assert elbow >= 69.8 + 2.0, "axis 4 hits the elbow disk"
assert all(v == 0 for v in clashes_with_v1_arm(ax4_objects).values()), "axis 4 hits the V1 arm"
assert abs(FORK_ROOT_X - (AX4_REAR_X + F.FLANGE_FACE)) < 1e-6 and abs(PITCH_X - FORK_ROOT_X - 104.0) < 1e-6
report.update({"pitch_x": PITCH_X, "reach_vs_v1_mm": round(PITCH_X - 250.0, 1), "axis4_min_to_elbow_axis_mm": round(elbow, 1)})
```

`clashes_with_v1_arm` runs `clashes()` from every axis 4 object against every object in `"V1 arm kept"`. Skip the holder-based items and the 34 mm motor items (`axis4_deepest_into_holder_mm`, `axis4_motor_*`, `axis4_clash_tris_with_holder`) in this variant.

- [ ] **Step 2: Run it before the variant exists.**
  - Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/head_concept.py -- --tube-forearm`
  - Expected: it fails, because the flag isn't used yet and the old axis 4 collection name is missing.

- [ ] **Step 3: Add the flag and constants.**
  - `TUBE_FOREARM = "--tube-forearm" in sys.argv`.
  - `OUT` becomes `head-concept/tube-forearm`, and `BLEND` becomes `head-concept-tube.blend`.
  - When the flag is set: `FORK_ROOT_X = AX4_REAR_X + F.FLANGE_FACE`, `PITCH_X = FORK_ROOT_X + 104.0`, `AX6_REAR_X = PITCH_X + 20.0`.
  - `AX4_REAR_X` stays 36.4 and `ROLL_Z` stays 555.
  - Every other variant keeps its current values.

- [ ] **Step 4: Write `axis4_tube()`, which replaces `axis4()` under the flag.**
  - Collection: `"Axis 4 compact, 188 belt, drives the tube"`.
  - Frame: `frame((AX4_REAR_X, 0, ROLL_Z), (1, 0, 0), (0, 0, 1))`, so the belt and pancake land on top.
  - Contents:
    - `cycloid("20-1-compact", "ax4", col, m)`
    - `belted_drive("ax4", col, m, "20-1-compact")`
    - the Ø5 rod, as in `axis5()`
    - the four forearm STLs. Re-pose each from print orientation into the frame; the outer tube is `fixed`, the rest are `moving`.
    - the aluminium tube as a `steel` ring (r 5.5 / 4.5, `F.TUBE_X`)
    - two 6701s as `cycloid` rings (r 9 / 6) at `F.REAR_BRG_X` and `F.FRONT_BRG_X`
  - The fork, cheeks, axes 5 and 6, and the hand follow automatically from the new `PITCH_X`, `FORK_ROOT_X` and `AX6_REAR_X`.
  - In `structure()`, skip the 6810 shell, the old roll tube and the coupling under the flag.

- [ ] **Step 5: Move the V1 holder to the comparison collection.** In `v1_parts()`, under the flag, put `axis4/axis4_axis5_holder` in `"V1 head (for comparison)"` (ghost) instead of `"V1 arm kept"`.
  - Skip the `axis4-without-holder` render.
  - Use `max(PITCH_X, 250)` to centre the head renders, so the longer reach stays in frame.

- [ ] **Step 6: Run it with the flag.**
  - Expected: `HEAD DONE`, no assertion errors. The `HEAD` line has `pitch_x` about 380.5 and `reach_vs_v1_mm` about +130.5.
  - Then run the default variant (no flags). Its `HEAD` JSON line must match what it printed before this task, and the default `head-concept.blend` is unchanged.

- [ ] **Step 7: Show the user** `head-side.png` and `head-iso.png` from `model/head-concept/tube-forearm/`, and the reach number.
  - Ask them before committing `head_concept.py`, `model/head-concept-tube.blend` and `model/head-concept/tube-forearm/`.
  - Message: why the forearm layout is checked against the elbow and V1 before printing.
