# Wrist: In-line Axis 5 Motor and Merged Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the head bracket so it glues straight onto the drive tube in place of the wrist hub, and turn axis 5's pancake to point straight back along the forearm, outboard of its belt.

**Architecture:**
- **What it follows on from:** this changes the parts built by `docs/superpowers/plans/2026-11-16-offset-wrist.md`, after that plan's work is committed.
- **`wrist.py`:**
  - `head_bracket()` is rebuilt as one part with three pieces: a boss glued onto the tube, a fill joining the boss to the slab, and the T8 mount's disc with a wider arm pointing back (−x).
  - The new `motor_plate()` builds a U channel that bolts onto the arm's belt face and carries the pancake outboard.
  - The L-bracket follows the new pitch axis unchanged.
- **`head_concept.py`:**
  - Under `--offset-wrist`, the forearm's wrist hub is no longer drawn.
  - The axis 5 pancake is drawn outboard.
  - The motor plate is placed in "Wrist fixed".
- **Checks:** in-script asserts, as before. A failing assert is the failing test.

**Tech Stack:** Blender 5.1 Python, `hand_lib.py`, `forearm_dims.py`, `cycloid_math.py`, `wrist_dims.py`.

**Spec:** `docs/superpowers/specs/2026-11-16-offset-wrist-axes5-6-design.md` (amended 2026-11-16: in-line pancake, merged hub)

## Global Constraints

- Everything in the previous plan's Global Constraints still holds: the frame, the run command, the `... DONE` lines, the r 1.7 / 3.0 / 2.0 hole sizes, and booleans done in the local frame before posing.
- **Do not change the earlier forearm work:** `forearm_tube.py`, `forearm_dims.py`, `cycloid_poc.py` and their STLs stay as they are. The old `wrist-flange-hub.stl` stays in the repo; it is simply no longer used by the wrist.
- **The tube interface copies the old wrist hub exactly**, using `F.*` values with no new numbers:
  - socket r `F.TUBE_R`, from `F.WRIST_X[0] - 1` to `F.WRIST_X[0] + F.SOCKET_DEPTH + F.TUBE_SPARE`
  - the land on the 6701's inner ring: `F.LAND_R0`–`F.LAND_R1`, standing `F.LAND_T` proud of `F.WRIST_X[0]`
  - the 0.3 shim at glue-up

## Review Focus

1. **Pancake against the plate's screw heads:** with the motor at either end of its slot, the M3 heads at v ±24.5 clear the pancake's 42.3 square by only about 0.6 mm. Expect no overlap at either end.
2. **The head rolling around the fixed outer tube:** every part of the head behind the tube's end (x < `F.OUTER_X[1]`) must stay at least r 13.5 from the roll axis, or it rubs as axis 4 turns.
3. **6705 shoulder:** the shoulder may bear only on the outer ring. The inner ring is fixed and the bracket turns.
4. **Belt against the U walls and the slab:** check the full belt envelope between the 20T and the 60T, not just at the motor.
5. **Socket printed sideways:** the bracket prints belt face down, as the old skirt did, so the Ø11 socket and the 6705 seat print on their sides. Both are glued, so the fit is not critical. The tube must still not bottom in the socket, so that the shim sets the play.

---

### Task 1: Merged head bracket, axis 5 motor plate, L-bracket at the new pitch

**Files:**
- Modify: `tools/blender/wrist_dims.py`, `tools/blender/wrist.py`
- Output: `model/wrist/head-bracket.stl`, `model/wrist/ax5-motor-plate.stl` (new), `model/wrist/ax6-l-bracket.stl`

**Interfaces:**
- **Produces in `wrist_dims`:**
  - `PITCH_X = round(F.FLANGE_FACE + 1.0 + math.sqrt(HOUSING_R**2 - SKIRT_R**2), 2)`, which is 271.13
  - `AX5_MOTOR_ANGLE = 180.0`
  - `BOSS_X = (BRG5_X[0], F.FLANGE_FACE)`
  - `SHOULDER_R = 14.0`
  - `FILL_HALF_Z = 16.0`
  - `ARM_HALF_W = 27.5`
  - `MP_WALL_V = (21.5, 27.5)`
  - `MP_SCREW_V = 24.5`
  - `MP_LOCAL_Z = {"plate": (-23.5, -17.5), "walls": (-17.5, -6.0)}`, in axis 5's assembly frame, mirrored from the old mount about the belt plane at −11.75
  - `PANCAKE_OUTBOARD = True`
- **Removes from `wrist_dims`:** `PLATE_X`, `PLATE_R`, `PLATE_HALF_Z`, `BRIDGE_X1`, `FLANGE_HOLE_R`, `FLANGE_CB_R`, `FLANGE_CB_DEPTH`, `SKIRT_BORE_R`.
- **Produces in `wrist.py`:**
  - `ax5_pancake(x)`: the body at local z −23.5 to −46.5, which is world y 42.8 to 65.8
  - `motor_plate() -> Object`
  - `MOTOR_PLATE_U = (MOTOR5_X - SLOT - 23.15, MOTOR5_X + SLOT + 23.15)`
  - `head-bracket` exported with the same print pose as before (belt face on the bed)
  - `ax5-motor-plate` printed outer face down

- [ ] **Step 1: Write the failing checks.**
  - In `check_head_bracket()`, replace the flange-screw, counterbore, plate-gap and skirt-bore asserts with these:
    - **Socket:** `L.hole_diameter` along x at `F.WRIST_X[0] + F.SOCKET_DEPTH/2` is `2*F.TUBE_R` ±0.03. At `F.TUBE_X[1] + 0.75`, the bore is still open, so the tube doesn't bottom.
    - **Land:** a ray from x = `F.WRIST_X[0] - 1` at r = (`F.LAND_R0`+`F.LAND_R1`)/2, cast +x, first hits at `F.WRIST_X[0] - F.LAND_T` ±0.05.
    - **6705 seat and shoulder:**
      - the radial bore at the 6705 seat is `2*BRG5_R_OUT`
      - the radial bore at `BRG5_X[1] + 0.5` is `2*SHOULDER_R`
      - `SHOULDER_R >= BRG5_R_IN + 1.0`, so it clears the inner ring
      - `SHOULDER_R < BRG5_R_OUT - 1.0`, so it bears on the outer ring
    - **Roll clearance:** every bracket vertex with x < `F.OUTER_X[1]` is at radius ≥ `F.OUTER_R + 1.0`.
    - **Boss against the housing:** `min_gap(boss region, ax5)` ≥ 1.0. In practice: `overlap(b, ax5) == 0`, and `PITCH_X - math.sqrt(HOUSING_R**2 - SKIRT_R**2) - BOSS_X[1] >= 1.0`.
    - **No old hub:** the scene check no longer imports `wrist-flange-hub.stl`.
    - **Pilot slot:** the arm keeps a pilot slot at `MOTOR5_X ± SLOT`, checked with `through_mount(b, u, 0)` is None at both ends. The shaft tip reaches local z −3.5, into the slab.
    - **Inserts:** four insert holes, r 2.0 and 5.0 deep from the slab's belt face (local z −6), at (u0+5, ±24.5) and (u1−5, ±24.5), where (u0, u1) = `MOTOR_PLATE_U`.
  - Add `check_motor_plate()`:
    - non-manifold == 0
    - the pilot slot and four NEMA slots are open at both slot ends. These are rays along the local −z axis through the plate.
    - counterbores r 3.0, 2.0 deep on the outer face, over r 1.7 holes at the four screw positions
    - an M3 × 20 from the counterbore floor ends inside the slab's insert hole: tip ≥ the insert floor, and the screw reaches ≥ 4.0 into the slab
    - `overlap(plate, pancake near/far) == 0` and `touching(pancake, plate)`
    - `overlap(screw heads, pancake near/far) == 0`
    - **Belt envelope:** the hull of a circle of r (20/π + 1.5) at u = MOTOR5_X ± SLOT and a circle of r 60/π + 1.5 at u = 0, at local z −11.75 ± 3.5. It has no overlap with the plate or the bracket.
    - the pancake (near/far) has no overlap with the bracket, outer tube, 6705, ax5 housing or L-bracket
  - **Run:** `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/wrist.py`
  - **Expected:** an assert fails, with no `WRIST DONE`, because `motor_plate` is not defined or the socket is missing.

- [ ] **Step 2: Rebuild `head_bracket()`.**
  - **Mount, in its own frame, before posing:**
    1. Cut the old arm past `ARM_CUT_X`.
    2. Add an arm |v| ≤ `ARM_HALF_W` from `ARM_CUT_X - 1` to `MOTOR_PLATE_U[1]`, local z −6 to 0. Add rails as now.
    3. Cut the pilot slot only. There are no NEMA slots in the arm now.
    4. `L.finish`, then cut the insert holes in one tool.
  - **Pose:** with `ax5_matrix()`, now at 180°.
  - **Union:**
    - the boss: `cyl_x` r `SKIRT_R` over `BOSS_X`
    - the fill box: x from `BOSS_X[0]` to `PITCH_X - math.sqrt(HOUSING_R**2 - FILL_HALF_Z**2) - 1.0`, y 0 to `AX5_REAR_Y + 0.01`, z ±`FILL_HALF_Z`
    - the land
  - **Then cut:**
    - the 6705 seat r `BRG5_R_OUT` from `BRG5_X[0] - 1` to `BRG5_X[1]`
    - the shoulder bore r `SHOULDER_R` from `BRG5_X[1] - 0.01` to `F.WRIST_X[0]`
    - the socket
  - Remove the plate, the bridge, the flange screws and the hub hole that was cut for the old plate. Keep the r14 hub clearance at the pitch axis on the housing side, as now.

- [ ] **Step 3: Write `motor_plate()` in axis 5's local frame, then pose it with `ax5_matrix()`.**
  - The plate spans u over `MOTOR_PLATE_U`, |v| ≤ `MP_WALL_V[1]`, z over `MP_LOCAL_Z["plate"]`.
  - The two walls span |v| over `MP_WALL_V`, z over `MP_LOCAL_Z["walls"]`.
  - Cut the pilot and NEMA slots as one tool, as in `lengthen_arm`.
  - Cut the screw holes and counterbores.
  - Print pose: the outer face (local z −23.5) on the bed.
- [ ] **Step 4: Flip `ax5_pancake()` outboard.**
  - Update the pancake/tube and pancake/housing asserts in `check_head_bracket` to the new position.
  - **Remove** `assert MOTOR5_X - SLOT - 42.3/2 >= HOUSING_R + 2.0`. Replace it with an overlap check against the housing (included in Step 1).

- [ ] **Step 5: Run and confirm the checks pass.**
  - **Run:** the same command as Step 1.
  - **Expected:**
    - `WRIST {...}` reports `head-bracket nm 0`, `ax5-motor-plate nm 0` and `ax6-l-bracket nm 0`.
    - The L-bracket's existing checks still pass at the new `PITCH_X`: post gap 1.7, dog depth, screws, and nut-pocket walls ≥ 2.85.
    - Then `WRIST DONE`.
  - Add `pitch_x` and `pancake_y` (min, max) to the report.

- [ ] **Step 6: Ask before committing (CLAUDE.md).**
  - Proposed message: "Glue the head bracket onto the drive tube and run axis 5's pancake straight back"
  - Files: `wrist_dims.py`, `wrist.py`, the three `model/wrist/*.stl`.

### Task 2: Head concept layout

**Files:**
- Modify: `tools/blender/head_concept.py`
- Output: `model/head-concept/offset-wrist/*.png`

**Interfaces:**
- **Consumes:** `W.PITCH_X`, `W.AX5_MOTOR_ANGLE`, `W.PANCAKE_OUTBOARD`, and `model/wrist/ax5-motor-plate.stl` (print pose: outer face on the bed).
- **Produces:**
  - `belted_drive(..., outboard=False)`: when True, the pancake's face sits at `2 * BELT_PLANE` and its body runs −1.
  - `FIXED_HEAD_MASSES` gains `"ax5-motor-plate": 25`, and `"head-bracket"` goes from 45 to 70. These are estimates; the merged part now includes the hub.

- [ ] **Step 1: Write the failing check.**
  - In `offset_wrist_report()`, assert that the axis 5 pancake's world bounding box has min y ≥ 40 (the roll axis is at y 0), and that its z range sits within `ROLL_Z` ± 25. In other words, it lies beside the forearm and in line with it.
  - Assert that no object named "wrist-flange-hub" exists in the scene.
  - **Run:** `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/head_concept.py -- --offset-wrist`
  - **Expected:** an assert fails.
- [ ] **Step 2: Implement.**
  - Skip the hub in `axis4_tube()` when `OFFSET_WRIST`.
  - Add `outboard` to `belted_drive`, and have `axis5()` pass `outboard=W.PANCAKE_OUTBOARD`.
  - Place the motor plate in "Wrist fixed" with `unprint` at the plate's outer face.
  - Update the masses.
- [ ] **Step 3: Run and confirm the checks pass.**
  - **Run:** the same command as Step 1.
  - **Expected:**
    - `pitch_x` is 307.53 (was 322).
    - `sweep []`, so nothing clashes from −170° to +170°.
    - Axis 5's torque stays ≤ its limit. Its levers are unchanged to within about 1 mm, because the hand and tool are measured from the pitch axis.
    - `HEAD DONE`.
    - Record the new axis 4 roll figures, at pitch 0 and the worst case, for the user.
  - Also run the other variants (no flag, `--t8-through`, `--tube-forearm`) and diff their HEAD lines against `scratchpad/hc-baseline/baseline.txt`. Expected: identical.
- [ ] **Step 4: Ask before committing.**
  - Proposed message: "Lay out the in-line axis 5 motor and the glued head bracket"
  - Files: `head_concept.py` and the renders.

## Assembly notes (for the user, not code)

1. Free the old wrist hub with heat, or soak it in acetone, and clean the tube end.
2. Slide the 6705's inner ring onto the outer tube's Ø25 end. It's a slip fit; don't glue it yet.
3. Seat the 6705's outer ring in the bracket.
4. Slide the bracket onto the drive tube with the 0.3 shim against the 6701's inner ring. CA the socket, then wick CA into the 6705's inner ring.
5. Pre-fit the 60T on axis 5's input, then bolt axis 5's housing on.
6. Put the belt over the 60T and into the channel.
7. Push the pancake, with its 20T already fixed, through the motor plate's pilot slot into the belt loop. Then screw the plate onto the arm's inserts and tension the belt with the motor slots.
