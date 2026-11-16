# Offset Wrist (Axes 5 and 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Printable parts for a UR-style offset wrist on the forearm's wrist flange, with a 6705 support bearing on the outer tube. The parts are then laid out in the head concept with a ±170° pitch sweep and an axis 5 torque check.

**Architecture:**
- **`wrist_dims.py`:** a new pure-Python module that holds the wrist's positions in the forearm frame. Both scripts import it.
- **`wrist.py`:** builds, checks and exports the two new printed parts.
  - Each part is the existing 188 T8 motor mount STL (nut pockets, rails, post holes, `a1e29dc`) unioned with new geometry. The mounts aren't redrawn.
  - The axis 5 output plate is a second print of `model/forearm-tube/ax4-output-plate.stl`, because it's the same compact and the same inserts.
- **`head_concept.py`:** gains an `--offset-wrist` variant that lays out the real parts.
- **Checks:** in-script asserts. A failing assert is the failing test.

**Tech Stack:** Blender 5.1 Python (bpy, bmesh, mathutils.bvhtree), `tools/blender/hand_lib.py`, `forearm_dims.py`, `cycloid_math.py`.

**Spec:** `docs/superpowers/specs/2026-11-16-offset-wrist-axes5-6-design.md`

## Global Constraints

- **Run Blender with:** `/Applications/Blender.app/Contents/MacOS/Blender -b -P <script> [-- flags]`. Each script prints a `... DONE` line at the end.
- **Units are mm.**
- **Frame:** all wrist positions use the forearm frame.
  - x runs along the roll axis. x = 0 is the axis 4 compact housing's rear face, and the wrist flange face is `F.FLANGE_FACE` = 241.6.
  - y and z are the head concept's world y and z: y = 0, z = 0 is the roll axis, and z is up at axis 4's home.
  - The hand is on the **−y** side, so the `head-side` render (looking along +y) sees it in front.
  - World = (`AX4_REAR_X` + x, y, `ROLL_Z` + z), with `AX4_REAR_X` = 36.4 and `ROLL_Z` = 555.
- **Reused STLs, imported read-only and posed:**

  | STL | Stored frame | Role |
  |---|---|---|
  | `model/cycloid-poc/20-1-hollow-t8/motor-mount.stl` | assembly frame, z −6 to 5 (rails 0 to 5 on the housing side), arm along +x to 91.53 | both mounts |
  | `model/cycloid-poc/20-1-hollow-t8/motor7-bracket.stl` | z −56 to −6 | gripper motor bracket |
  | `model/forearm-tube/ax4-output-plate.stl` | print pose, z 0 to 9 (plate 0 to 5, dogs to 9) | axis 5 output plate |
  | `model/forearm-tube/wrist-flange-hub.stl`, `forearm-outer-tube.stl` | print poses | posed as in `head_concept.axis4_tube()` |

  Assert each one's z range on import, so a re-export that moved it fails loudly.
- **Fixings:**
  - M3 clearance holes are r 1.7. The four holes into the wrist flange are r 1.85, giving 0.35 of float so the flange bolts don't fight the 6705.
  - Counterbores are r 3.0. Heat-set insert holes are r 2.0.
- **Every printed part:**
  - zero non-manifold edges (`L.stats(o)["non_manifold"] == 0`)
  - exported with `L.export` into `model/wrist/`, posed for print with the flat face on z = 0
  - `matrix_world` reset, with the print pose applied to the mesh only after all checks have run
- **Commits:**
  - Do not commit without the user's approval.
  - Stage only the files the task names. The working tree has the user's other uncommitted work (hand, base, `hand_lib.py`).
  - End messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Don't touch:**
  - `cycloid_poc.py`, `forearm_tube.py`, `forearm_dims.py`, `hand_lib.py`
  - anything under `model/cycloid-poc/` or `model/forearm-tube/`
  - the other `head_concept.py` variants' outputs (`head-concept*.blend` and their PNG folders)

## Review Focus

1. **Pitch sweep:** nothing that turns with axis 5 may touch anything that doesn't, at any pitch from −170° to +170°.
   - Turns with axis 5: the L-bracket, output plate, axis 6, gripper drive and hand.
   - Doesn't turn: the head bracket, the axis 5 housing and its pancake, the forearm and the 6705.
   - Task 3 sweeps this in 10° steps. Tasks 1 and 2 keep the two sets in separate y slabs, the first line of defence.
2. **Axis 5 torque:** it must come out ≤ 0.8 N·m with a 200 g tool at the fingertips. If it doesn't, **stop and bring it to the user**, as the spec requires. Don't move parts or change motors to make it pass.
3. **Screw access:** each part gets its screws at its own stage of the build, and every hole must be drivable at that stage:
   1. the flange screws, before axis 5 goes on
   2. the axis 5 housing bolts, from the hand side before the output plate
   3. the axis 6 housing bolts and the motor7 posts, before the L-bracket meets axis 5
4. **6705 load path:** the skirt touches only the 6705's outer ring, and the wrist hub turns inside the skirt bore with clearance. Nothing else in the head bracket touches the outer tube.
5. **Gripper bracket posts:** they sit next to the L-bracket's base disc. The 64 mm offset (rather than the spec's "about 60") exists because of them, and the check must prove ≥ 1 mm of clearance.

---

### Task 1: Wrist positions and the head bracket

**Files:**
- Create: `tools/blender/wrist_dims.py`
- Create: `tools/blender/wrist.py`
- Output: `model/wrist/head-bracket.stl`

**Interfaces:**
- Produces (`wrist_dims.py`, plain constants with `import forearm_dims as F`, no bpy):
  - Pitch axis and axis 5:
    - `PITCH_X = F.FLANGE_FACE + 44.0`, which is 285.6. It is the axis 5 compact's axis, along y at z = 0.
    - `AX5_REAR_Y = 19.3`: axis 5's housing rear face (mount side), so the housing spans y 19.3 to −19.3 and its hub face is at −20.3.
    - `AX5_MOTOR_ANGLE = 225.0`: the direction from the pitch axis to the axis 5 pancake in the x-z plane, measured from +x towards +z, so back and down.
  - Head bracket plate: `PLATE_X = (F.FLANGE_FACE, F.FLANGE_FACE + 8.0)`, `PLATE_R = 20.0`, `PLATE_HALF_Z = 20.0`, `FLANGE_HOLE_R = 1.85`, `FLANGE_CB_R, FLANGE_CB_DEPTH = 3.0, 4.0` (M3 × 8 then sits 4.0 into the inserts).
  - 6705: `BRG5_W = 4.0`, `BRG5_R_OUT, BRG5_R_IN = 16.0, 12.5`, `BRG5_X = (F.OUTER_X[1] - 5.0, F.OUTER_X[1] - 1.0)`, which is (216.6, 220.6).
  - Skirt: `SKIRT_R = 18.5`, `SKIRT_BORE_R = 15.5`.
  - Axis 5 output plate: `OUT_PLATE_Y = (-20.3, -25.3)`. Its dogs reach −29.3.
  - L-bracket: `LB_Y = (-25.8, -31.8)`, `LB_R = 24.0`.
  - Axis 6:
    - `AX6_Y = -64.0`. It is the axis 6 axis, parallel to x at z = 0.
    - `AX6_REAR_X = PITCH_X + 25.0`, which is 310.6. It is the T8 housing's rear face, and its housing runs from there to +32.6.
    - `AX6_MOTOR_UP = True`: the axis 6 mount's arm points +z.
  - Housings: `HOUSING_R = 34.0`, `BOLT_R = 30.0`, `T8_HOUSING_L = 32.6`.
- Produces (`wrist.py`):
  - `head_bracket() -> Object` (`"head-bracket"`)
  - `PARTS`, `CHECKS`, `PRINT_POSE`, following `forearm_tube.py`
  - `overlap(a, b) -> float`, copied from `forearm_tube.py` (that script runs on import, so it can't be imported)
  - `posed_stl(path, name, matrix, z_range) -> Object`: imports the STL, asserts its z range to within 0.01, then applies `matrix` to the mesh

- [ ] **Step 1: Write `check_head_bracket()` first.**

```python
b = PARTS["head-bracket"]
assert L.stats(b)["non_manifold"] == 0
seat_x = sum(BRG5_X) / 2
assert abs(radial_bore(b, seat_x) - 2 * BRG5_R_OUT) < 0.05, "6705 seat"
assert abs(radial_bore(b, F.WRIST_X[0] + 5) - 2 * SKIRT_BORE_R) < 0.05, "skirt bore over the wrist hub"
assert SKIRT_BORE_R - F.WRIST_R >= 0.5 and SKIRT_BORE_R < BRG5_R_OUT, "hub rubs the skirt, or the shoulder misses the outer ring"
for a in F.FLANGE_ANGLES:
    y, z = polar(F.FLANGE_INSERT_R, a)
    assert abs(x_floor(b, y, z, PLATE_X[1] + 10) - (PLATE_X[1] - FLANGE_CB_DEPTH)) < 0.05, "flange screw counterbore"
assert PITCH_X - HOUSING_R - PLATE_X[1] >= 1.5, "plate hits the axis 5 housing"
motor_top_z = -BELT_C * math.sin(math.radians(45)) + 42.3 / 2
assert motor_top_z <= -PLATE_HALF_Z - 3.0 and motor_top_z <= -SKIRT_R - 3.0, "axis 5 pancake hits the bracket"
ax5 = ax5_housing()                     # 20-1-compact housings in this frame, front-face bolt heads added (r 2.75 x 3, on the -y face)
hub, tube, brg = forearm_parts()        # wrist-flange-hub, forearm-outer-tube and a 6705 ring at BRG5_X, posed
bad = {k: round(v, 3) for k, v in {"ax5": overlap(b, ax5), "hub": overlap(b, hub), "tube": overlap(b, tube),
                                   "6705/tube": overlap(brg, tube)}.items() if v > 0.05}
assert not bad, bad
assert overlap(b, brg) > 0.0 or touching(b, brg), "skirt not on the 6705"
assert max(v.co.y for v in b.data.vertices) <= AX5_REAR_Y + 6.0 + 1e-3 and min(v.co.y for v in b.data.vertices) >= -PLATE_R - 1e-3, "bracket leaves its y slab"
```

`BELT_C` is `round(C.belt_centre_distance(20, 40, 188), 2)` (63.68). Helpers, all in `wrist.py`:
- `radial_bore(o, x)`: the bore diameter about the roll axis at x. Build it like `L.hole_diameter` but cast along the y-z plane; the simplest way is `L.hole_diameter` on a copy rotated so x maps to z.
- `x_floor(o, y, z, x_start)`: the first hit casting −x from `x_start`.
- `touching(a, b)`: true when the two are within 0.05.

- [ ] **Step 2: Run it before `head_bracket()` exists.**
  - Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/wrist.py`
  - Expected: it fails with a `NameError` or `KeyError` on `head-bracket`.

- [ ] **Step 3: Write `wrist_dims.py` with the values above.** Then write `head_bracket()` in `wrist.py` as the union of:
  - **The T8 motor mount STL, posed:**
    - Its z axis → −y, so the housing face is at y = `AX5_REAR_Y` and the mount is at y 19.3 to 25.3.
    - Its +x (arm) points along `AX5_MOTOR_ANGLE` in the x-z plane.
    - Its origin goes on the pitch axis.
    - Axis 5's housing bolts (M3 × 45, heads on the hand side) run through housing and mount into its nut pockets: 44.6 of stack, so they end 0.4 past.
  - **Plate:** spans `PLATE_X`. In y-z it is a disc of r `PLATE_R` about the roll axis, unioned with the box y 0 to `AX5_REAR_Y + 6`, z ±`PLATE_HALF_Z`. It has four r `FLANGE_HOLE_R` holes on `F.FLANGE_INSERT_R` at `F.FLANGE_ANGLES`, with r 3.0 counterbores `FLANGE_CB_DEPTH` deep from the +x face.
  - **Bridge:** box x `PLATE_X[0]` to `PITCH_X`, y `AX5_REAR_Y` to `AX5_REAR_Y + 6`, z ±`PLATE_HALF_Z`. It joins the plate to the mount's disc. Keep it clear of the mount's r 14 hub hole: cut that hole again after the union.
  - **Skirt:** a tube about the roll axis from `BRG5_X[0]` to `PLATE_X[0]`.
    - Outside r `SKIRT_R`, bore r `SKIRT_BORE_R`.
    - The 6705 seat is r `BRG5_R_OUT` over `BRG5_X`, open to the rear: the bearing goes in from behind before the bracket slides on.
  - **Print pose:** the mount's belt face (y = 25.3) on the bed, which means y → −z after translating by −25.3. Tree supports go under the skirt; the seat prints sideways, so the user checks it on a real 6705.
  - **End of script:** run `CHECKS`, print `WRIST` with a JSON report of each part's dims, export, then print `WRIST DONE`.

- [ ] **Step 4: Run it again.**
  - Expected: `WRIST DONE`, no assertion errors, and `model/wrist/head-bracket.stl`.

- [ ] **Step 5: Ask the user, then commit** `wrist_dims.py`, `wrist.py` and `model/wrist/head-bracket.stl`. Message: why one part carries the flange, the 6705 skirt and axis 5's mount (the head's weight goes into the outer tube, and there's no separate fork).

---

### Task 2: The L-bracket (axis 5 output to axis 6)

**Files:**
- Modify: `tools/blender/wrist.py`
- Output: `model/wrist/ax6-l-bracket.stl`

**Interfaces:**
- Consumes: the Task 1 constants, `overlap`, `posed_stl`, `PARTS`, `CHECKS`.
- Produces: `l_bracket() -> Object` (`"ax6-l-bracket"`) and `ax5_output_plate_posed() -> Object`. The second is the forearm's `ax4-output-plate.stl` with its z → −y, its plate face on y = −20.3, and its dog angles matching Task 2's dog holes. It's used for checks only, not exported.

- [ ] **Step 1: Write `check_l_bracket()`.**

```python
lb = PARTS["ax6-l-bracket"]
assert L.stats(lb)["non_manifold"] == 0
plate = ax5_output_plate_posed()
t8 = t8_housings_posed()                # 20-1-hollow-t8 housing-rear/front at AX6_REAR_X, AX6_Y
posts = posed_stl(T8 + "/motor7-bracket.stl", "motor7", ax6_mount_matrix(), (-56.0, -6.0))
heads = ax5_front_bolt_heads()          # r 2.75 x 3 on R30 at 45 + 90k, y -19.3 to -22.3
bad = {k: round(v, 3) for k, v in {"plate": overlap(lb, plate), "t8": overlap(lb, t8), "posts": overlap(lb, posts),
                                   "heads": overlap(lb, heads)}.items() if v > 0.05}
assert not bad, bad
assert min_gap(posts, lb) >= 1.0, "gripper bracket post within 1 mm of the base disc"
assert max(v.co.y for v in lb.data.vertices) <= LB_Y[0] + 1e-3, "L-bracket reaches into axis 5's slab"
assert LB_Y[0] - (-22.3) <= -3.0, "base disc within 3 of axis 5's bolt heads"
for a in F.DOG_ANGLES:
    assert dog_hole_depth(lb, a) >= F.DOG_H + 0.5 - 0.05, "dog hole too shallow"
assert AX6_Y + HOUSING_R <= -25.0, "axis 6 housing reaches axis 5's slab"
assert -45.0 >= AX6_Y + 40 / math.pi + 3.0, "gusset within 3 of axis 6's 40T / belt"
```

Helpers:
- `min_gap(a, b)`: the smallest distance from a's vertices to b's surface, using a BVH `find_nearest`.
- `dog_hole_depth`: casts into the base disc at each dog position on `F.DOG_PCD_R`.

- [ ] **Step 2: Run it.** Expected: it fails with a `KeyError` on `ax6-l-bracket`.

- [ ] **Step 3: Write `l_bracket()` as the union of:**
  - **The T8 motor mount STL, posed by `ax6_mount_matrix()`:**
    - Its z → +x, with the housing face at x = `AX6_REAR_X`, so the mount is at x 304.6 to 310.6.
    - Its +x (arm) → +z.
    - Its origin goes on (x, `AX6_Y`, 0).
    - The T8 housing bolts are M3 × 40: 38.6 of stack, so they end 1.4 past the nut pockets.
  - **Base disc:** about the pitch axis (x = `PITCH_X`, z = 0), r `LB_R`, spanning `LB_Y`. It overlaps the mount's disc only in x 304.6–309.6, y −30 to −31.8, which is too thin a joint on its own.
  - **Two gusset ribs:** boxes at x `PITCH_X + 5` to `AX6_REAR_X`, y `LB_Y[0]` to −45, with z from 8 to 20 and from −20 to −8. They tie the base disc into the mount. The z gap between them clears the motor7 post at y −38, z 0. Stopping at y −45 keeps them clear of axis 6's 40T and belt strand at y ≈ −51.
  - **Dog holes:** r `F.DOG_R + 0.25`, `F.DOG_H + 0.5` deep, from the +y face, on `F.DOG_PCD_R` at `F.DOG_ANGLES`. Use the same angle convention as `ax5_output_plate_posed()`, so the two agree by construction.
  - **Centre hole:** r 4.0 through the base disc, as a sight hole onto the output plate's centre.
  - **Print pose:** the base disc's +y face (y = −25.8) on the bed. The mount stands up as a wall. This means −y → +z after translating by +25.8.

- [ ] **Step 4: Run it.**
  - Expected: `WRIST DONE` and both STLs.
  - The `WRIST` report includes `"ax6_offset_y": AX6_Y` and `"post_gap_mm"`.

- [ ] **Step 5: Ask the user, then commit** `wrist.py` and `model/wrist/ax6-l-bracket.stl`. Message:
  - why the L-bracket *is* axis 6's mount, which keeps the module rigid and saves a part
  - why the offset is 64 and not 60 (the motor7 posts)

---

### Task 3: `--offset-wrist` layout, pitch sweep and torque

**Files:**
- Modify: `tools/blender/head_concept.py`
- Output: `model/head-concept-wrist.blend`, `model/head-concept/offset-wrist/*.png`

**Interfaces:**
- Consumes:
  - `wrist_dims` (import it as `W`)
  - the two `model/wrist/` STLs, the forearm STLs and `ax4-output-plate.stl`
  - the existing `axis4_tube()`, `belted_drive()`, `screw_drive()`, `adapter()`, `hand()`
- Produces:
  - a `HEAD` JSON line that adds `pitch_x`, `ax6_offset_y`, `pitch_sweep_clash_deg` (an empty list), `axis5_torque_nm`, `axis4_roll_torque_nm` and `head_mass_g`
  - renders `head-side`, `head-top`, `head-iso`, `head-side-pitch-down` (−90°, tool pointing down) and `head-side-pitch-up` (+90°)

- [ ] **Step 1: Write `offset_wrist_report()`, called from `check()` under the flag.**

```python
hits = pitch_sweep(range(-170, 171, 10))
assert not hits, ("pitch body clashes", hits)
t5 = torque_about(pitch_axis_world(), PITCH_MASSES, tool_at=fingertip_world())
assert t5 <= 0.8, f"axis 5 needs {t5:.2f} N·m with a 200 g tool, over 0.8: bring it to the user (spec)"
report.update({"pitch_x": AX4_REAR_X + W.PITCH_X, "ax6_offset_y": W.AX6_Y, "pitch_sweep_clash_deg": hits,
               "axis5_torque_nm": round(t5, 2), "axis4_roll_torque_nm": round(roll_torque(), 2),
               "head_mass_g": sum(PITCH_MASSES.values()) + sum(FIXED_HEAD_MASSES.values())})
```

The pieces:
- **`pitch_sweep(degs)`:** returns the angles where anything clashes.
  - At each angle, rotate the world vertices of every pitch-body object about the pitch axis, a line along y through (`AX4_REAR_X + W.PITCH_X`, ·, `ROLL_Z`).
  - Build a BVH from them and `overlap` it against a BVH of every fixed object.
  - **Pitch body:**
    - the `"Wrist pitch body"` collection (the L-bracket and output plate)
    - `"Axis 6 hollow, gripper motor behind"`, `"Gripper drive, past axis 6"` and `"Three-finger hand"`
    - the placeholders whose names start with `adapter`, `screw bulkhead` or `palm rear shell`
  - **Fixed:**
    - the `"Wrist fixed"` collection (the head bracket and the 6705 ring)
    - `AX4_COL`
    - `"Axis 5 belted, 40:1"` minus its `carrier`, `disk` and `eccentric` objects, which turn inside the housing
- **`torque_about(axis, masses, tool_at)`:** returns 9.81 × |Σ mᵢ (cᵢ − p)ₓ_z| in N·m, with m in kg and distances in metres.
  - cᵢ is each group's bounding-box centre, and p is the pitch axis.
  - The tool adds 0.2 kg at `tool_at`.
  - The result is the worst-case static torque, with the lever horizontal.
- **`PITCH_MASSES`, grams, estimates:**

  | Group | Grams |
  |---|---|
  | `"ax6 cycloid"` (the T8 housings, carriers, disks, eccentric) | 150 |
  | `"ax6 pancake"` | 120 |
  | `"ax7 gripper motor"` | 230 |
  | `"Gripper drive, past axis 6"` | 80 |
  | `"Three-finger hand"` plus the palm rear shell | 400 |
  | `"Wrist pitch body"` | 50 |

- **`FIXED_HEAD_MASSES`:** `"ax5 cycloid"` 150, `"ax5 pancake"` 120, `"head-bracket"` 45.
- **`roll_torque()`:** the same formula about the roll axis (y and z distances), over both mass tables plus the tool.

- [ ] **Step 2: Run it before the variant exists.**
  - Run: `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/head_concept.py -- --offset-wrist`
  - Expected: it fails, because the flag isn't used yet (`KeyError` on `"Wrist fixed"` or a fork-root assert).

- [ ] **Step 3: Add the flag and constants.**
  - `OFFSET_WRIST = "--offset-wrist" in sys.argv`. It implies `TUBE_FOREARM` and `T8_THROUGH`, so set those with `or OFFSET_WRIST`.
  - `OUT` becomes `head-concept/offset-wrist`, and `BLEND` becomes `head-concept-wrist.blend`. Check this flag first in both chains.
  - When the flag is set:
    - `PITCH_X = AX4_REAR_X + W.PITCH_X`
    - `AX6_REAR_X = AX4_REAR_X + W.AX6_REAR_X`
    - a new global `AX6_Y = W.AX6_Y`
  - Every other variant uses `AX6_Y = 0.0`.
  - `tube_axis4_report()` skips its fork-root assert under the flag.

- [ ] **Step 4: Move axis 6 and the hand off the roll axis.**
  - `ax6_frame()` and the frame in `axis6()` use origin (`AX6_REAR_X`, `AX6_Y`, `ROLL_Z`).
  - In `hand()`, the frame origin's y and the shell box's y range shift by `AX6_Y`.
  - With `AX6_Y = 0.0` the other variants are unchanged.

- [ ] **Step 5: Lay out the wrist under the flag.**
  - **`axis5()`:**
    - Frame: origin (`PITCH_X`, `W.AX5_REAR_Y`, `ROLL_Z`), axis (0, −1, 0), and xdir the unit vector at `W.AX5_MOTOR_ANGLE` in the x-z plane, so the pancake lands back and down.
    - Give `belted_drive()` a `plate=True` parameter, and pass `plate=False` here and in `axis6()` under the flag. The real mounts are inside the two brackets.
  - **`structure()`:** under the flag, call a new `wrist_parts()` instead of `fork_and_cheeks()`. It:
    - imports `head-bracket.stl` into `"Wrist fixed"` (`fixed`), undoing its print pose, plus a 6705 `ring` at `W.BRG5_X` (r 16 / 12.5, material `cycloid`)
    - imports `ax6-l-bracket.stl` and `ax4-output-plate.stl` into `"Wrist pitch body"` (`moving`), undoing their print poses
    - turns the whole wrist into world coordinates with `Matrix.Translation((AX4_REAR_X, 0, ROLL_Z))`
  - **`check()`:** skip `pitch_limit`, `swing_clear_of_fork_root_mm` and `fork_inner_half_width_mm` under the flag, and call `offset_wrist_report()`.
  - **Collections:** add `"Wrist fixed"` and `"Wrist pitch body"` to the `new` set in `main()`.

- [ ] **Step 6: Add the pitched renders.** After the normal renders, rotate every pitch-body object's mesh by −90° about the pitch axis and render `head-side-pitch-down`. Then do the same at +90° for `head-side-pitch-up`, and rotate back by −90° before saving the `.blend`.

- [ ] **Step 7: Run it with the flag.**
  - Expected:
    - `HEAD DONE` and no assertion errors
    - `pitch_sweep_clash_deg: []`
    - `axis5_torque_nm` ≤ 0.8 (around 0.7)
    - `pitch_x` about 322.0
  - **If the torque assert fires, stop.** Report the figure and the mass table to the user. Don't move parts or change masses to make it pass.
  - Then run the default, `--t8-through` and `--tube-forearm` variants. Each `HEAD` line must match what it printed before this task.

- [ ] **Step 8: Show the user and ask about committing.**
  - Show them `head-side.png`, `head-iso.png` and the two pitched sides, along with the torque and roll numbers.
  - Remind them nothing is printed until they've seen this layout: the spec's order.
  - Ask before committing `head_concept.py`, `model/head-concept-wrist.blend` and `model/head-concept/offset-wrist/`.
  - Message: why the wrist is checked through its whole pitch range and for torque before printing.

---

## Plan-level calls (not in the spec)

- **Offset 64 mm, not "about 60":** the gripper motor bracket's post on R26 would cut into the L-bracket's base disc at 60.
- **Pitch axis 44 mm past the flange, not about 40:** the plate has to be 8 thick to sink the flange screw heads, plus a 2 mm gap to the housing.
- **Reuse over redraw:**
  - Both brackets union the existing T8 188 mount, nut pockets included, so axis 5 takes M3 × 45 and axis 6 takes M3 × 40.
  - The axis 5 output plate is a second print of `ax4-output-plate.stl`.
- **Load path:** the 6705's inner ring is CA-glued onto the outer tube 1 mm behind its end. The flange holes are r 1.85, so the two load paths don't fight.
- **Hall homing:** deferred. The spec leaves sensor mounting to the builder, and no sensor has been chosen, so it waits for the wiring pass.
- **Hard stops:** none on axis 5 for now. Software limits protect the cable loop.
