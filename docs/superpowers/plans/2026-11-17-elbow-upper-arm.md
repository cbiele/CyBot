# Elbow (Axis 3) and Upper Arm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate the printable elbow and upper arm parts (forearm collar, aluminium tube V, elbow hub, two side plates, idler, shoulder hub, bench stand and two 3M pulleys), check them in their own script, then lay them out in the head concept and check the elbow's range and torque.

**Architecture:**
- **`tools/blender/elbow_dims.py`** (new): the elbow frame and every pinned number.
- **`tools/blender/elbow.py`** (new): builds each part in the elbow frame and runs its checks against posed copies of the parts it meets: axis 4's housing, outer tube and 60T mount; the elbow compact; the 17HS8401B; the 6810s; and the tubes. It exports STLs in print pose to `model/elbow/`. It follows `wrist.py`'s pattern: `PARTS`, `CHECKS`, `PRINT_POSE`, `REPORT`, then `ELBOW {json}`, then `ELBOW DONE`.
- **`tools/blender/htd3m_pulley.py`:** two new entries in `PULLEYS`, a 20T and a 60T.
- **`tools/blender/head_concept.py`:** a new `--elbow` flag, which implies `--offset-wrist`. It places the upper arm, the elbow compact, the motor and the belt, sweeps the elbow through its range, and reports the elbow torque.
- **Checks:** in-script asserts, as in every generator here. A failing assert is the failing test.

**Tech Stack:** Blender 5.1 Python (`/Applications/Blender.app/Contents/MacOS/Blender -b -P <script> [-- flags]`), plus `hand_lib.py` (as `L`), `cycloid_math.py` (as `C`), `forearm_dims.py` (as `F`) and `wrist_dims.py` (as `W`).

**Spec:** `docs/superpowers/specs/2026-11-17-elbow-upper-arm-design.md`

## Global Constraints

- **The elbow frame (`elbow_dims.py`):**
  - The origin is on the elbow axis, at the plates' mid-plane. y runs along the elbow axis, towards plate A at +y.
  - The parts are built in the head concept's pose: the forearm level along +x and the upper arm hanging along −z, so the shoulder axis is at (0, 0, −220).
  - The forearm frame (`forearm_dims`: x from axis 4's housing rear face, roll axis on y = z = 0) maps into the elbow frame as (x − `ELBOW_FX`, y, z + `OFFSET`).
  - The elbow angle θ is 0 with the forearm straight up and +90 in this pose. Its range is −20 to +150.
- **Pinned numbers:**
  - `OFFSET = 80.0`
  - `UPPER_L = 220.0`
  - `ELBOW_FX = 40.0`: the elbow axis sits just in front of axis 4's housing (x 0–38.6), so the axis 4 compact, motor and mount sit behind it. That's my call, adjustable only if a clearance check forces it. Record any change as a ruling.
  - `RANGE = (-20.0, 150.0)`, with the hard stops at −22 and +152.
  - The 6810: `B6810 = (25.0, 32.5, 7.0)`, which is (bore r, OD r, width).
  - The 17HS8401B: 42.3 square, 48 long, M3 on a 31 square, pilot Ø22, shaft Ø5 with its D flat 0.5 deep, 24 long.
  - The tube: `TUBE = (4.5, 3.5)` (OD r, ID r), with sockets 15 deep (`F.SOCKET_DEPTH`) and r 4.6.
  - The compact: housing Ø68 × 38.6, R30 bolt holes, output face at 39.6 from the rear face, three inserts on R6.5 at 90/210/330, and the dog pattern on `F.DOG_PCD_R`/`F.DOG_R`/`F.DOG_ANGLES`.
  - The belt: the 420-3M, `C.belt_centre_distance(20, 60, 420, pitch=3.0)` (about 148.8), 9 wide.
  - Hole sizes: M3 clearance r 1.7, M3 heat-set insert pilot r 2.0 and 5 deep, M3 nut pocket 5.8 AF × 2.6.
  - Bolts come from `M3_STOCK = (40, 45, 50)` or shorter, with grip ≤ length ≤ grip + 2 for through-bolts into nuts.
- **Don't touch the built forearm and wrist:** `forearm_tube.py`, `forearm_dims.py`, `cycloid_poc.py`, `wrist.py` and `wrist_dims.py`, and their STLs, are read, not changed. The collar must not change axis 4's bolt stack (49.6 mm on an M3 × 50).
- **Do booleans in a part's local frame before posing it, as `wrist.py` does.** `L.finish` each part. Each exported part must be one island with 0 non-manifold edges.
- **The bed is 225 × 255.** Each part's print-pose footprint must fit inside 220 × 250, a plate's on the diagonal if needed.
- **Regression for `head_concept.py`:** the HEAD lines for no flag, `--t8-through`, `--tube-forearm` and `--offset-wrist` must stay the same as before the change. Capture them in Task 5, Step 1. Afterwards restore the other variants' PNGs and blends with `git checkout --` on the files under `model/head-concept*` that aren't yours.
- **Don't commit the user's unrelated work:** hand files, base/spider files, `hand_lib.py`, the 2026-09 docs, "CyBoT notes.pages", `exploded.png`, `finger-coupon-scene.blend`, `result.json`. Stage files by name.
- **Commit messages say why** and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Ask the user before each commit, and stage the files first, as their CLAUDE.md requires.

## Review Focus

1. **The forearm against the upper arm through the whole range.** At θ = −20 the axis 4 pancake and the 60T mount swing back over the plates' elbow ends. At +150 the outer tube, the collar and the wrist come down towards the plates and the cross members. Expect no overlap anywhere from −20 to +150 in 2° steps, with the wrist at pitch 0 and at ±90.
2. **The tube V inside the plate gap.** The tubes leave the hub between the plates, so the elbow-end cross member must lie outside their sweep, and the tubes must stay at least 1.0 clear of both plates' inner faces.
3. **The collar over the outer tube.** The clamp may only bear on the Ø36 section in front of the flange, x from `F.OUTER_X[0] + F.OUTER_FLANGE_T` to `F.REAR_BRG_X[0] - 1.0`, never over the rear 6701's seat. Its keys must fit over the bolt ends without touching the flange's bolt holes.
4. **The belt-side envelope at the shoulder.** The 20T, the idler and the belt must stay inside the declared envelope, and the shoulder hub must reach out past it, at every elbow-motor slot position.
5. **The 60T's inside face against plate A.** The compact's input rod comes out of plate A, and the 60T sits on it outside. A 60T rubbing on plate A or the motor's screw heads would load the elbow and show up as reverse-direction stalls.

---

### Task 1: Elbow frame, posed context, and the forearm bracket (collar, tubes, hub)

**Files:**
- Create: `tools/blender/elbow_dims.py`, `tools/blender/elbow.py`
- Output: `model/elbow/elbow-collar.stl`, `model/elbow/elbow-hub.stl`

**Interfaces:**
- **Produces in `elbow_dims`:** everything pinned in Global Constraints, plus:
  - `PLATE_GAP`: the plates' inner faces at ±`PLATE_GAP/2`. Plate A's inner face is the compact's rear face: the compact spans y from `PLATE_GAP/2` down to `PLATE_GAP/2 − 38.6`. Its output face is at `PLATE_GAP/2 − 39.6`. The hub runs from there to plate B's 6810.
  - `PLATE_T`: the plate thickness. It holds the 6810 (7) plus a 1.5 lip.
  - `HUB_6810_Y`: the 6810's centre in plate B.
  - `TUBE_ENDS`: four (collar point, hub point) pairs, in the elbow frame, at y = ±`TUBE_Y`. Each side has one tube landing in front of the elbow axis and one behind it.
  - `COLLAR_X`: the forearm-frame x range of the collar's clamp.
- **Produces in `elbow.py`:**
  - `forearm_matrix() -> Matrix`, mapping the forearm frame into the elbow frame
  - `rot_elbow(theta) -> Matrix`, about the y axis through the origin, with θ = 90 as identity
  - `posed_context() -> dict[str, Object]`, holding `ax4 housing`, `outer tube`, `ax4 60T mount`, `ax4 pancake` (a 42.3 × 42.3 × 23 box at its posed place), `elbow compact` (the housing STL posed), `bolt ends` (the R30 bolt tails and nuts at the flange face) and `6810 B`
  - `collar() -> Object`, `hub() -> Object`, `tubes() -> list[Object]`
  - `tube_lengths() -> list[float]`, the cut lengths, each ≤ 125 (half a 250 stock length)

- [ ] **Step 1: Write the failing checks** in `check_bracket()`, appended to `CHECKS`:
  - Each of the collar, the hub and the tubes taken together has `islands(o) == 1`, and the collar and hub have 0 non-manifold edges.
  - **Collar grip:** `L.hole_diameter` along x at the clamp's middle is `2 * F.OUTER_REAR_R` + 0.0/+0.2. The clamp bore is empty from `F.REAR_BRG_X[0] - 1.0` onwards, so nothing bears over the seat. `overlap(collar, outer tube) == 0`.
  - **Keys:** for each R30 bolt end, the key pocket's radius is at least the bolt-end radius + 0.2, and `overlap(collar, bolt ends) == 0`. The collar's rear face touches the flange's front face, so `touching(collar, outer tube)` is true.
  - **The bolt stack is unchanged:** no collar vertex has x below `F.OUTER_X[0] + F.OUTER_FLANGE_T`, in the forearm frame.
  - **Sockets:** each tube end has a socket of r 4.6 and 15 ±0.05 deep, measured with a ray along the tube's axis. The socket wall is ≥ 2.0.
  - **Hub:** its journal is r `B6810[0]` −0.0/+0.1 across the 6810's width. It has a shoulder on the inner ring only, r ≤ `B6810[0] + 2.5`. Its bore for wires is r ≥ 18.
  - **Hub on the output:** a dog hole at each of the compact's three dogs (r `F.DOG_R` + 0.15) and r 1.7 screw holes on R6.5 with counterbores. Report `dog_bearing_mpa` = (9.0e3 / `F.DOG_PCD_R`) / 3 / (2·`F.DOG_R` · `F.DOG_H`). Assert it is ≤ 15. If it isn't, enlarge the dogs on the hub and the compact's output plate. Those are new parts, not the forearm's.
  - **Clearances in this pose:** `overlap(x, y) == 0` for every pair among the collar, the hub, the tubes, the `ax4 housing`, the `ax4 60T mount`, the `ax4 pancake` and the `elbow compact`. Every tube stays ≥ 1.0 from |y| = `PLATE_GAP/2`.
  - **Tube loads,** with a 9 N·m elbow torque shared over the four tubes, from their geometry. Report `tube_axial_n` for each tube and `socket_bending_nmm`, the moment at the socket if one V carries the full torque in bending. Assert that every axial load is ≤ 600 N (my call: well under the glued joint's shear over a 15 deep r 4.5 socket).
  - Each `tube_lengths()` ≤ 125.
  - **Run:** `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/elbow.py`
  - **Expected:** fails on a `NameError` or the first assert, and no `ELBOW DONE`.

- [ ] **Step 2: Write `elbow_dims.py`** with the frame and the values above. Its docstring cites the spec. Pick `TUBE_Y`, `TUBE_ENDS`, `PLATE_GAP` and `PLATE_T` so that Step 1's asserts can pass. Don't print anything from the dims file.

- [ ] **Step 3: Write `posed_context()`, `collar()`, `tubes()` and `hub()`.**
  - The context comes from the built STLs: `model/forearm-tube/forearm-outer-tube.stl` and `ax4-motor-mount-60T.stl`, and `model/cycloid-poc/20-1-compact/` for the housings. Pose them as `head_concept.axis4_tube()` does, then apply `forearm_matrix()`.
  - The collar is a split ring: two halves joined by M3 × 12 screws into nut pockets, with a 1.0 split gap. Its rear face carries the four key pockets. The tube sockets sit on two lugs below it.
  - The hub is a disc on the compact's output, plus the 6810 journal, plus four socket lugs.
  - Print poses: the collar halves split face down, as one STL with both halves. The hub prints output face down.

- [ ] **Step 4: Run it.** Expected: `ELBOW {...}` with `dog_bearing_mpa`, `tube_axial_n` and `tube_lengths`, then `ELBOW DONE`. Read the numbers. If `dog_bearing_mpa` came in over 15 and you enlarged the dogs, add `ax3-output-plate` to the outputs and record a ruling.

- [ ] **Step 5: Commit** (ask first): `elbow_dims.py`, `elbow.py`, `model/elbow/elbow-collar.stl`, `model/elbow/elbow-hub.stl`.

### Task 2: The 3M 20T and 60T

**Files:**
- Modify: `tools/blender/htd3m_pulley.py` (the `PULLEYS` list)
- Output: `model/elbow/axis3-pulley-20T.stl`, `model/elbow/axis3-pulley-60T.stl`

**Interfaces:**
- **Produces:** `("axis3-pulley-20T", 20, 2.6, 1.6, 7.0, True, "elbow")`, for the 17HS8401B's D shaft as on axis 1, with an insert for the set screw. Also `("axis3-pulley-60T", 60, 2.6, 2.1, 7.0, True, "elbow")`, for the compact's Ø5 rod with its flat 2.1 off the axis, as the GT2 60Ts.
- **Consumed by** Task 3 (the belt plane and the pulley outside faces) and Task 5 (placement). Each pulley's teeth band is z from `FLANGE_T` to `FLANGE_T + TEETH_W` in its own frame.

- [ ] **Step 1:** Add the two entries. The script's existing `check()` is the test: groove count = teeth, the bore across its flat, and the insert hole.
- [ ] **Step 2: Run** `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/htd3m_pulley.py`. Expected: a report line for each of the four pulleys, with the two new ones at 20 and 60 grooves. axis1 and axis2's numbers must be unchanged, so diff them against a run before the edit. Then `git status` shows only the two new STLs, plus axis1 and axis2's STLs if the export rewrote them byte-identical. Restore those if they aren't.
- [ ] **Step 3: Commit** (ask first).

### Task 3: Side plates A and B, cross members, idler and hard stops

**Files:**
- Modify: `tools/blender/elbow.py`, `tools/blender/elbow_dims.py`
- Output: `model/elbow/upper-plate-A.stl`, `model/elbow/upper-plate-B.stl`, `model/elbow/belt-idler.stl`

**Interfaces:**
- **Consumes:** Task 1's frame, `PLATE_GAP`, `PLATE_T`, `posed_context()` and the hub; Task 2's pulley dimensions.
- **Produces in `elbow_dims`:**
  - `MOTOR_Z`: the motor's axis on the upper arm, at about z −148.8, adjustable along its slot.
  - `MOTOR_SLOT`: half-length, enough for ±3 mm of belt tension and fitting a motor up to 60 long.
  - `IDLER_AT`
  - `BELT_PLANE_Y`: the belt's mid-plane, outside plate A.
  - `BELT_ENVELOPE_Y`: the outermost y of the 20T, the 60T, the idler and the belt, plus 2.0.
  - `SHOULDER_6810_Y`: one 6810 in each plate at the shoulder.
  - `CROSS_MEMBERS`: a list of (x, z) for aluminium tube spacers, each length `PLATE_GAP + 2 * PLATE_T` or less.
  - `STOPS`: the hard stops' angles, −22 and +152.
  - `HALL_AT`: the sensor's pocket on plate B and the magnet's pocket on the hub, both at the same radius.
- **Produces in `elbow.py`:** `plate_a()`, `plate_b()`, `idler()`, `belt_envelope(slot_pos) -> Object`, `motor_posed(slot_pos, length=48) -> Object`.

- [ ] **Step 1: Write the failing checks** in `check_plates()`:
  - Both plates: one island, 0 non-manifold edges, and the print-pose footprint fits 220 × 250. Report `plate_mass_g` at 1.24 g/cm³ with 40% infill. That's a rough figure, a report only.
  - **Plate A:**
    - the compact's four R30 holes take M3s through plate A into nut pockets on the compact's front face side, with grip and bolt chosen by `bolt_for`, as in `wrist.py`
    - a pilot clearance of r ≥ 14 for the compact's hub
    - the input rod's exit is open
    - the motor's pilot slot and four M3 slots are open at both slot ends
  - **Plate B:**
    - the 6810 seat is r `B6810[1]` +0.0/+0.1 and 7 deep, with a lip
    - the lip's inner edge is ≤ `B6810[1] - 1.5`, so it bears on the outer ring only, and ≥ the hub's shoulder r + 0.5
  - **The shoulder end of both plates:** a 6810 seat as above at (0, 0, −220).
  - **Belt geometry:** the centre distance from the motor to the compact, at the slot's middle, is `C.belt_centre_distance(20, 60, 420, pitch=3.0)` ±0.1. The slot covers ±3 around it. The idler's position deflects the belt at least 2 mm at slot-mid.
  - **Clearances:** the belt envelope at both slot ends doesn't overlap plate A, the motor's screw heads or the cross members. The 60T's inside flange is ≥ 1.0 from plate A's outer face (Review Focus 5). A 60 mm motor box at both slot ends doesn't overlap plate B, the cross members or the hub.
  - **Cross members:** each has holes of r 4.5 +0.0/+0.15 through both plates, coaxial, and is clear of the tube V's sweep from −20 to +150 in 2° steps. That sweep is `rot_elbow(θ)` applied to the tubes and hub.
  - **Hard stops:** at θ = −22 and +152 the hub's stop face touches the plate's stop, within ±0.3. At −20 and +150 they are ≥ 1.0 apart.
  - **Hall:** at θ = 0 the magnet pocket (Ø6 × 3) on the hub faces the sensor pocket on plate B (TO-92: 4.6 × 3.6 × 1.6, leads out) across a gap of 1.0–2.0.
  - **Run** `elbow.py`. Expected: fails on `NameError: plate_a`.

- [ ] **Step 2: Build the plates and the idler.** Each plate is one part: a web from the elbow boss (r 38) to the shoulder boss (r 38), with lightening cut-outs that leave ≥ 6 around every hole and seat. The idler is a printed boss on plate A's outside, carrying a 623 or an M3 shoulder screw; your call, so record it. It sits in a slot with a tension screw.
- [ ] **Step 3: Run.** Expected: `ELBOW DONE`, and the report gains `belt_centre_mm`, `plate_mass_g` and `bolts`.
- [ ] **Step 4: Commit** (ask first).

### Task 4: The shoulder hub and the bench stand

**Files:**
- Modify: `tools/blender/elbow.py`, `tools/blender/elbow_dims.py`
- Output: `model/elbow/shoulder-hub.stl`, `model/elbow/shoulder-hub-clamp.stl`, `model/elbow/bench-stand.stl`

**Interfaces:**
- **Produces in `elbow_dims`:**
  - `SHOULDER_HUB_Y`: the hub's span. On plate A's side it reaches past `BELT_ENVELOPE_Y` by at least 8. On plate B's side it reaches past the plate's outer face by at least 8.
  - `HUB_END`: each end face has four M3 heat-set inserts on R20 at 45° + 90k and a Ø44 open bore for the wires. This is the shoulder drive's and the body's interface, and the next design builds on it.
  - `INDEX_HOLES`: Ø4 holes through plate B on R45 around the shoulder axis, at θ_shoulder 0 (home), 45 and 90. The stand pins one of them with an M4 bolt or a Ø4 pin.
- **The hub:** the 6810 inner rings sit on a Ø50 journal at each plate. A fixed shoulder on plate A's side and the separate `shoulder-hub-clamp` on plate B's side take the axial play. A spacer between the bearings bears on the inner rings only.

- [ ] **Step 1: Write the failing checks** in `check_shoulder()`:
  - both journals are r 25.0 +0.0/+0.1
  - the inner-ring shoulders are r ≤ 27.5
  - the bore is r ≥ 22
  - the inserts are at `HUB_END`
  - the hub's end on plate A's side is past `BELT_ENVELOPE_Y` + 8
  - one island each, and 0 non-manifold edges
  - **The stand:**
    - it bolts to both hub ends
    - it has a pin hole that lines up with each `INDEX_HOLES` entry at its angle
    - its base has two clamp pads, 40 × 60 and ≥ 8 thick
    - at each index angle, from home (upper arm straight up) to 90, the stand doesn't overlap the plates, the motor at both slot ends or the belt envelope
    - its footprint fits the bed
  - **Run.** Expected: fails on `NameError`.
- [ ] **Step 2: Build** the hub, the clamp and the stand. The stand is two cheeks joined by a base, one cheek on each hub end, with the pads under the base.
- [ ] **Step 3: Run.** Expected: `ELBOW DONE`.
- [ ] **Step 4: Commit** (ask first).

### Task 5: Layout in the head concept: range sweep and elbow torque

**Files:**
- Modify: `tools/blender/head_concept.py`
- Output: `model/head-concept/elbow/*.png`, `model/head-concept-elbow.blend`

**Interfaces:**
- **Consumes:** the STLs in `model/elbow/` and `elbow_dims`.
- **`--elbow` implies `OFFSET_WRIST`.**
  - The elbow axis in world is (`AX4_REAR_X + ELBOW_FX`, 0, `ROLL_Z - OFFSET`), which is (76.4, 0, 475).
  - `ROLL_Z` stays 555, so no other variant moves.
  - The V1 arm and V1 head collections, and the checks against them, are skipped under `--elbow`.
  - New collections: `Elbow and upper arm` (plates, hub, collar, tubes, idler, shoulder hub, motor box, pulleys, belt placeholder) and `Elbow compact` (`cycloid("20-1-compact", "ax3", ...)`).

- [ ] **Step 1: Capture the baseline.** Run the four existing variants and save their `HEAD` lines to the scratchpad.
- [ ] **Step 2: Write the failing checks** in a new `elbow_report(report)`, called from `check()` under `ELBOW`:
  - **Range sweep:**
    - for θ from −20 to +150 in 2° steps, and wrist pitch in (−90, 0, 90), there is no overlap between the moving set (everything past the elbow: axis 4's collection, the wrist, the head, the collar, the tubes and the hub) and the fixed set (the plates, the cross members, the motor, the pulleys on plate A, the idler and the shoulder hub)
    - rotate the moving set with the elbow about the world elbow axis, and the wrist pitch with `pitch_matrix` first
    - report `elbow_sweep_clash` as a list of (θ, pitch), and assert it is empty
  - **Torque:**
    - `ELBOW_MASSES`: `PITCH_MASSES` + `FIXED_HEAD_MASSES` + `{"Axis 4 remainder": 1300 - (their sum - 400)}`. The remainder sits at the centre of `AX4_COL`. So the masses past the elbow, without the hand, total the user's measured 1300 g.
    - add the collar, the tubes and the hub at 60 g at their centre, as my estimate
    - add `TOOL_KG` at the fingertip
    - the torque about the elbow axis is the worst over θ and pitch (−90, 0, 90). Report `elbow_torque_worst_nm` and the pose where it happens.
  - **Capacity:** `ELBOW_CAPACITY_NM = MEASURED_NM_AT_40 * (0.52 / 0.13) * 60 / 40`, from the 17HS8401B's holding torque over the pancake's (build-plan §7), so 7.02. Report `elbow_margin`.
    - Assert `elbow_torque_worst_nm <= ELBOW_CAPACITY_NM`. If it fails, stop and bring it to the user, as the spec says.
    - Don't assert the 1.5× margin: the spec accepts about 1.2× until the bench test.
  - **Run** `Blender -b -P tools/blender/head_concept.py -- --elbow`. Expected: fails with `NameError: elbow_report`, or a missing-STL error.
- [ ] **Step 3: Place the parts and write `elbow_report`.** Renders:
  - `elbow-side` at θ 90
  - `elbow-side-up` at 0
  - `elbow-side-back` at −20
  - `elbow-side-down` at 150
  - `elbow-iso`
- [ ] **Step 4: Run `--elbow`.** Expected: `HEAD {...}` with `elbow_sweep_clash: []`, `elbow_torque_worst_nm`, `elbow_capacity_nm` 7.02 and `elbow_margin`, then `HEAD DONE`.
  - Rerun the four baseline variants and diff their HEAD lines. They must be identical.
  - Restore their PNGs and blends with `git checkout --`.
- [ ] **Step 5: Commit** (ask first): `head_concept.py`, `model/head-concept/elbow/`, `model/head-concept-elbow.blend`.

### Task 6: Print sheet

**Files:**
- Create: `model/elbow/PRINT.md`
- Create: `model/elbow/print/*.3mf` (Bambu P2S PLA), by the method in `model/wrist/PRINT.md`: flattened system profiles and `--outputdir`. The flatten script is recreated in the scratchpad if it's gone.

- [ ] **Step 1:** Arrange the plates:
  - plate A alone, on the diagonal if needed
  - plate B alone
  - the hub, the collar, the idler and the pulleys at 0.12
  - the stand and the shoulder hub at 0.16
  
  Slice each once to get the time and grams, then export unsliced.
- [ ] **Step 2: Write `PRINT.md`** in the wrist sheet's shape: the plates table, what isn't printed (the compact, the motor, the 6810s, the tubes), the hardware table (each through-bolt from `REPORT["bolts"]`), the tube cut list (from `tube_lengths()` and `CROSS_MEMBERS`), and the assembly order. The assembly order is:
  1. the collar on the built forearm
  2. the tubes glued into the collar and hub
  3. the compact and motor on plate A
  4. the hub onto the output and into plate B's 6810
  5. the cross members
  6. the belt and idler
  7. the shoulder hub and the stand
- [ ] **Step 3: Commit** (ask first).
