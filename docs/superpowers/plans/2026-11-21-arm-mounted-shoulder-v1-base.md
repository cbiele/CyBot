# Arm-Mounted Shoulder and V1-Style Base Bearing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the V2 shoulder drive and base bearing from `de9edf8`:
- the shoulder is the elbow joint mirrored: the NEMA17 and the compact ride in the arm, the belt runs outside plate B, and a fixed hub turns in plate A's 6810 and is held by three splayed tubes into a socket bracket on the turntable
- a 625 on a post steadies the input rod
- the base is V1's: the turntable, 130T ring and a cylinder turn on two 6810s inside the drum
- the base motor hangs shaft-up beside a flat in the drum's wall

**Architecture:**
- **`tools/blender/elbow_dims.py` and `elbow.py` own the upper-arm plates.** They gain the shoulder end of plate B: the compact's mount, the shoulder motor's slots and the shoulder idler. Plate A gains the shoulder stop blocks and the Hall pocket.
- **`tools/blender/shoulder_dims.py` and `shoulder.py` are rewritten in place.** They keep the `PARTS` / `CHECKS` / `PRINT_POSE` / `REPORT` pattern, the `SHOULDER {json}` line, then `SHOULDER DONE`, and the outputs in `model/shoulder/` plus `poses.json`.
- **`tools/blender/head_concept.py -- --shoulder`** is updated in place.
- **Checks:** in-script asserts, as in every generator here. A failing assert is the failing test.

**Tech Stack:**
- Blender 5.1 Python: `/Applications/Blender.app/Contents/MacOS/Blender -b -P <script> [-- flags]`. `shoulder.py` takes about 6 min.
- the libraries: `hand_lib.py` as `L`, `cycloid_math.py` as `C`, `elbow_dims` as `E`, `forearm_dims` as `F`
- slicing: the Bambu Studio CLI, by the method in the last `model/shoulder/PRINT.md` session (profiles flattened in the scratchpad's `bambu/` folder)

**Spec:** `docs/superpowers/specs/2026-11-21-arm-mounted-shoulder-v1-base-design.md`. Where it says "as now", the 2026-11-20 spec and plan hold.

## Global Constraints

- **The shoulder frame is unchanged.**
  - The origin is on the shoulder axis, at the arm's mid-plane.
  - +y runs toward plate A, z is up, and x is forward.
  - The base axis is the z axis.
  - The elbow frame maps in as (x, y, z + `E.UPPER_L`).
  - ψ 0 is the arm straight up. `PHI_RANGE = (-170.0, 170.0)`, `PHI_STOPS = (-172.0, 172.0)`.
- **What turns and what doesn't** (this inverts the current build):
  - **Turning with the arm:** both plates, the shoulder compact's housing, the shoulder motor, its 20T, the shoulder idler, the input rod and the 80T.
  - **Fixed to the turntable:** the shoulder hub, the output plate (it's on the compact's output, which the hub holds), the hub's collar and lug, the tubes, the socket bracket and the post.
- **Pinned numbers (from the spec):**
  - The compact: the `--m25-roll` housing, Ø68 × 38.6, output face at 39.6 from the rear face, its R30 bolts at `F.BOLT_ANGLES`, the Ø5 rod. Its rear face sits on plate B's inner face.
  - The shoulder belt: 3M-420, 20T/80T, centres `round(C.belt_centre_distance(20, 80, 420, pitch=3.0), 2)` = 131.89, slot ±3. The motor's axis is at elbow-frame z = `E.SHOULDER_Z + 131.89`.
  - The 17HS19-2004S1: 42.3 square, 48 long, M3 on a 31 square, pilot Ø22.
  - The base belt: 3M-477, 20T/130T, centres 113.89, slot ±3, 6.5:1.
  - The 6810: `E.B6810`. The 625: `S.B625`. The tubes are 9 × 7 (`E.TUBE_OR`, `E.SOCKET_R`, `E.SOCKET_DEPTH`).
  - Holes: M3 clearance r 1.7, insert pilot r 2.0 × 5. Bolts are M3, ≤ 50 long.
- **Loads:** `SHOULDER_DESIGN_NMM = 13.5e3` for the output link, the hub, the lug and the stops, ≤ 10 MPa in printed parts. `SHOULDER_CURRENT_CAP_A = 2.0 * 13.5 / (0.59 * 80)` is unchanged.
- **Geometry hygiene:**
  - Do booleans in the part's local frame, then `L.finish`.
  - Each part is one island with 0 non-manifold edges, and fits 220 × 250 in its print pose.
  - No coincident faces: use hulls for stepped bores, and start features 1 below a face, then trim.
- **The screw rule (as now):** every head (or nut) has ≥ 0.5 of clearance round it and a straight tool path from outside of ≥ its height + 30 mm at every slot position, and its length is ≤ grip + insert depth − 0.5. It's checked with rays.
- **Running gaps:** every fixed part stays ≥ 0.5 from every turning one at every ψ in `PSI_RANGE`, in 1° steps, at both slot ends of both arm motors.
- **`head_concept.py` regression:**
  - The HEAD lines for no flag, `--compact-drive`, `--t8-through`, `--tube-forearm` and `--offset-wrist` stay identical to baselines taken in Task 0.
  - `--elbow` may change only in plate-derived values. Diff it and report the diff.
  - Restore the PNGs of those variants with `git checkout -- model/head-concept/` (except `shoulder/`). In zsh, pass flags as `-- --$v`.
- **Don't commit the user's unrelated work:** the hand files, `spider_base.py`, `model/base/spider-arm-motor.stl`, `hand_lib.py`, the 2026-09 docs, `CyBoT notes.pages`, `exploded.png`, `finger-coupon-scene.blend`, `result.json` and `.superpowers/`. Stage files by name.
- **Commits:** the message says why and ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Ask the user before each commit, and stage first.

## Review Focus

1. **A fixed part in a turning band.** The hub, the lug and the tubes sit on plate A's side, where the elbow 20T and its belt sweep an annulus round the shoulder axis (y up to `E.BELT_ENVELOPE_Y`). The post sits outside the shoulder belt's envelope on B's side.
   - In those y bands a fixed part must stay inside the swept annulus' inner radius, or outboard of the band.
   - The hub's shoulder on the 6810's inner ring must stay clear of plate A's turning lip (r `E.LIP_IN_R`).
   - Pinned by Task 2's running-gap sweep.
2. **Plate B's new features colliding with the elbow's.** The shoulder motor's slots, its idler and the reshaped window sit beside the elbow motor's window, the cross members at z −95, the sensor pocket and the index holes.
   - Pinned by Task 1's wall-thickness rays and the unchanged elbow checks.
3. **The flipped base motor.**
   - Its body must clear the drum's flat at slot ±3, and the leg sockets at 225° and 315°.
   - Its screws and push screw must be reachable from above, past the turntable's rim.
   - Pinned by Task 3.
4. **The base bearings.**
   - The clamp bears on the inner rings only.
   - The retainer's screws are reachable from under the open drum.
   - The cylinder's land fits r 25.0 +0/+0.1.
   - Pinned by Task 3.
5. **The capacity sum after the move.** The shoulder motor and compact now turn with the arm.
   - A stale entry that still counts them as fixed, or counts them twice, would understate or overstate the load.
   - Pinned by Task 4's assert that each mass is counted once, in the turning group.

---

### Task 0: Housekeeping and baselines

**Files:**
- Revert: `tools/blender/shoulder.py`, `tools/blender/shoulder_dims.py`, `model/shoulder/PRINT.md`, `model/shoulder/shoulder-stub.stl`. These are my uncommitted review minors on the stub and spacer, which the spec drops. Check that `git diff` on them shows only those edits before reverting.
- Keep: the uncommitted `tools/blender/head_concept.py` bench-reach sweep (φ every 15°, `bench_reach_worst_phi`).

- [ ] **Step 1:** Revert the four files with `git checkout --`.
- [ ] **Step 2:** Run `head_concept.py -- --shoulder`. Expected: `HEAD DONE`, with `bench_reach_worst_phi` in the report.
- [ ] **Step 3:** Take the six HEAD-line baselines (no flag, `--compact-drive`, `--t8-through`, `--tube-forearm`, `--offset-wrist`, `--elbow`) into the scratchpad. Restore the PNGs.
- [ ] **Step 4: Commit** `head_concept.py` alone (ask first): the bench-reach sweep over every 15° of φ.

### Task 1: The upper-arm plates for the arm-mounted shoulder

**Files:**
- Modify: `tools/blender/elbow_dims.py`, `tools/blender/elbow.py`
- Output: `model/elbow/upper-plate-A.stl`, `upper-plate-B.stl`, `poses.json`. `belt-idler.stl` is unchanged and is reused for the shoulder.

**Interfaces:**
- **Produces in `elbow_dims`** (elbow frame):
  - `SH_BELT_C = round(C.belt_centre_distance(20, 80, 420, pitch=3.0), 2)`
  - `SH_MOTOR_Z = SHOULDER_Z + SH_BELT_C`
  - `SH_MOTOR_SLOT = 3.0`, along z
  - `SH_COMPACT_REAR_Y = -Y_REAR`: the shoulder compact's rear face, on plate B's inner face
  - `SH_PULLEY_Y0 = -(Y_REAR + PLATE_T + PULLEY_GAP)`
  - `SH_TEETH_Y`, `SH_BELT_PLANE_Y`: the elbow's, mirrored to −y
  - `SH_IDLER_AT`: (x, z) on the belt's back, slotted along x, your call. Its boss is ≥ 2.0 from the elbow motor's window, and its roller clears the belt's opposite span.
  - `SH_BELT_ENVELOPE_Y = -BELT_ENVELOPE_Y`: the same build-up, on the −y side
- **Produces in `elbow.py`:**
  - `plate_b()` and `plate_a()`, rebuilt
  - `sh_belt_envelope(slot) -> Object` and `sh_motor_posed(slot) -> Object`, mirroring `belt_envelope` and `motor_posed`
- **Plate B at `SHOULDER_Z`:** no 6810 seat. Instead:
  - the compact's hub clearance r 14
  - the four R30 bolt holes, as plate A has at the elbow
  - the shoulder motor's pilot slot and four screw slots at `SH_MOTOR_Z`, ±3 along z
  - the idler boss and slot on the outer face
  - `WINDOW` reshaped on plate B to leave ≥ 3.0 round the shoulder motor's slots. Plate A's window stays unless it fouls the motor's body.
- **Plate A at `SHOULDER_Z`:** the 6810 seat as now. Plus:
  - two stop blocks on its outer face, at r 31–42, the elbow's `stop_blocks()` pattern
  - a Hall sensor pocket under the fixed tab's path at ψ 0
  - Task 2 sets the angles through `S.PSI_STOPS`. Until then, use ±93, and Task 2 re-runs `elbow.py`.

- [ ] **Step 1: Write the failing checks** in `check_plates()`. Every existing elbow assert stays. Update the shoulder seats list at line 555 to plate A only. Add:
  - **The shoulder motor:** at slot −3, 0 and +3, it is ≥ 1.0 from the elbow motor (at its slot −3 and +3), from both compacts (Ø68 at z 0 and at `SHOULDER_Z`), from the cross members, and from plate A's inner face.
  - **Belt centres:** the 20T axis to the shoulder axis = `SH_BELT_C` + slot ± 0.1, at slot −3, 0 and +3.
  - **Plate B's wall:** ≥ 2.0 between every pair of plate B's cuts: the motor slots, the R30 holes, the window, the elbow motor window, the idler slot, the cross-member holes and the index holes. Check it with the existing `material_round`-style rays.
  - **The shoulder belt envelope:** at slot ±3, it clears the elbow parts on plate B's outer face (stop blocks, sensor pocket) by ≥ 1.0. Report `sh_belt_envelope_y`.
  - **Screws:** the screw rule for the shoulder motor's four M3s and the idler's axle, from inside the arm.
  - Run `elbow.py`. Expected: fails on `NameError: SH_BELT_C` or `sh_motor_posed`.
- [ ] **Step 2: Build** the constants and the plates.
- [ ] **Step 3: Run `elbow.py`.** Expected: its DONE line and the existing report, plus `sh_motor_z`, `sh_belt_envelope_y`, and the minimum gap from the shoulder motor to the elbow motor.
- [ ] **Step 4:** Run `head_concept.py -- --elbow`. Diff against the Task 0 baseline: only plate-derived numbers may change. Report the diff.
- [ ] **Step 5: Commit** (ask first).

### Task 2: The fixed shoulder hub, the lug, the tubes, the socket bracket and the post

**Files:**
- Modify: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`
- `git rm`:
  - `model/shoulder/shoulder-stub.stl`, `shoulder-stub-spacer.stl`, `shoulder-hub-b.stl`
  - `body-wall-A.stl`, `body-wall-B.stl`
  - `shoulder-motor-plate-17.stl`, `shoulder-motor-plate-23.stl`
  - `plate-drill-jig.stl`
- Delete their builders and checks: `stub`, `stub_spacer`, `hub_half`, `drill_jig`, `check_jig`, `wall*`, `bracket`, `motor_plate`, `shoulder_motor_box`, `MOTORS["23"]`, the `BOX`/`TAB`/`SEAT` dicts, and `STUB*`.
- Output:
  - `shoulder-hub.stl`
  - `shoulder-lug.stl` (the collar, the tab, the magnet and the sockets in one part, my call: see Step 2)
  - `shoulder-output-plate.stl`, as now
  - `shoulder-socket-bracket.stl`, `shoulder-rod-post.stl`
  - `poses.json`

**Interfaces:**
- **Consumes:** Task 1's `E.SH_*` constants and `sh_belt_envelope`, `sh_motor_posed`. `upper_arm_moving()` loads the new plates.
- **Produces in `shoulder_dims`:**
  - `COMPACT_REAR_Y = E.SH_COMPACT_REAR_Y`, `COMPACT_Y = COMPACT_REAR_Y + F.HUB_FACE` (the output face)
  - `SHOULDER_BELT_C = E.SH_BELT_C`
  - `HUB`: a dict with these keys:
    - `land_r = B6810[0]` across plate A's 6810
    - `shoulder_r` ≤ `E.LIP_IN_R − 0.5` (the inner ring's face, inside the turning lip)
    - `y`: (the output plate's face, the journal's end)
    - `bore_r`: open for a screwdriver to the output plate's M3s
  - `LUG`: a dict:
    - `y0`: on the 6810's inner ring, clamping it
    - `tube_plane_y`: ≥ `E.BELT_ENVELOPE_Y` + 1.0 + `E.SOCKET_R` + `E.SOCKET_WALL`
    - key slots not 180° apart, so it fits one way only
  - `TUBE_ENDS`: three tubes' (x, z) socket mouths, lug end first, in the plane `tube_plane_y`, splayed fore and aft like `E.TUBE_ENDS`. Each open span is ≥ 20.
  - `POST`: the 625's seat (`B625`) on the axis at y ≤ `E.SH_BELT_ENVELOPE_Y` − 1.0 − the post's half-width
  - `ROD_OUT`: the input rod past the housing's rear face, through plate B and the 80T into the 625
  - `SHOULDER_AXIS_Z`, `PSI_STOPS`, `PSI_RANGE`, by the current searches (`psi_limits`, the 3.0 rule at ψ 0). Assert `PSI_STOPS` past ±92.
  - `TURNTABLE_R`, provisional: the smallest r that carries the bracket's and the post's feet with ≥ 2 of edge
- **Produces in `shoulder.py`:**
  - `shoulder_hub()`, `lug()`, `output_plate()` (as now), `socket_bracket()`, `rod_post()`
  - `fixed_shoulder() -> list[Object]`: the hub, the lug, the output plate, the tubes, the bracket and the post
  - `turning_shoulder(psi) -> list[Object]`: both plates, both compacts' housings, both motors at both slot ends, both belt envelopes, the 80T, and plate A's turning outer-ring zone and lip

- [ ] **Step 1: Write the failing checks** in `check_shoulder_core()` and `check_shoulder_drive()`:
  - **Parts:** one island each, 0 non-manifold, on the bed.
  - **Bearing:**
    - the hub's land is r 25.0 +0/+0.1 across plate A's 6810
    - its inner ring is clamped by the hub's shoulder and the lug, with ≥ 0.3 of contact each face
    - nothing fixed comes within 0.5 of r ≥ 27.5 there
  - **Running gaps:** `fixed_shoulder()` against `turning_shoulder(psi)` is ≥ 0.5 at every ψ in `PSI_RANGE`, in 1° steps. Report the minimum and where it falls.
  - **The link:**
    - the output plate's dogs sit in the hub's face
    - its M3 × 12s reach 3.0–4.0 into the carrier's inserts
    - the dogs' bearing stress and the hub's shear are ≤ 10 MPa at 13.5 N·m
  - **The lug:**
    - it fits only one way: turned 180°, it overlaps the hub's keys by ≥ 1.0 mm³
    - its sockets have ≥ 2.0 of wall
    - the stops touch at `PSI_STOPS` ± 0.3 and are ≥ 1.0 apart 2° inside
    - the Hall gap is 1.0–2.0 at ψ 0
  - **The tubes:** report each tube's axial load and the bending at its sockets at 13.5 N·m plus the arm's weight, with `truss_loads()` as on the elbow. The socket wall is ≥ 2.0.
  - **The post:**
    - the 625's seat is coaxial with the shoulder axis to 0.05
    - the post is ≥ 1.0 outside `sh_belt_envelope(±3)`
    - report `rod_out_mm` and the rod's side load: the belt's tension, at 2× the rated pull of a 9 mm 3M belt (your stated figure), plus half the arm's weight, split between the compact's input bearing and the 625
  - **The axis:** `SHOULDER_AXIS_Z` is reported, with everything turning ≥ 3.0 above the turntable at ψ 0.
  - **Screws:** the screw rule for the link's M3s, the lug's screws, and the bracket's and post's bolts. Those bolts go down from above into inserts in the turntable (my call: under the turntable is unreachable on the drum).
  - Run `shoulder.py`. Expected: fails on `NameError: shoulder_hub`.
- [ ] **Step 2: Build.**
  - The lug is one part: the collar keyed onto the journal's end, the tab and magnet, and the tube sockets.
  - If it can't go on past plate A's 6810 that way, split the sockets into a part bolted to the lug, and ledger it.
  - Re-run `elbow.py` once `PSI_STOPS` is set, so plate A's blocks match.
- [ ] **Step 3: Run `shoulder.py`.** Expected: `SHOULDER DONE`. The report has `shoulder_axis_z`, `psi_stops`, `shoulder_core_min_gap_mm`, `link_mpa`, `tube_loads`, `rod_out_mm`, `rod_side_load_n`.
- [ ] **Step 4: Commit** (ask first), with Task 1's re-run plate STLs.

### Task 3: The base: turntable, ring and cylinder on two 6810s in the drum, the flipped base motor, the flat

**Files:**
- Modify: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`
- `git rm`: `model/shoulder/spigot-spacer.stl`, `spigot-cap.stl`
- Output:
  - `turntable.stl`, `base-ring-130T.stl` (with the cylinder, or joined to it: your call, ledger it)
  - `base-retainer.stl`, `fixed-base.stl`, `base-motor-plate.stl` (adapted, or dropped for slots in the shelf: your call, ledger it)
  - `foot.stl` and `foot-pad.stl` are rebuilt at the new `BENCH_Z`

**Interfaces:**
- **Consumes:** Task 2's `SHOULDER_AXIS_Z`, `TURNTABLE_R`, and the bracket's and post's insert positions.
- **Produces in `shoulder_dims`** (heights top-down from `TURNTABLE_Z = -SHOULDER_AXIS_Z`):
  - `RING_Z`: the teeth band, just under the turntable
  - `CYL`: a dict:
    - `r = B6810[0]`, the land under both inner rings
    - `z`: (the ring's lower face, the cylinder's end)
  - `BASE_6810_Z`: the two bearings' lower faces, outer rings in the drum's seats r `B6810[1]` + 0.05
  - `BASE_6810_SPACING`: reported, ≥ 40
  - `RETAINER`: on the cylinder's end, clamping the lower inner ring, with M3s up into inserts in the cylinder
  - `DRUM_TOP`: under the ring's lowest turning feature by ≥ 1.5. `DRUM_R` and `DRUM_H` are 96 and 75, as now.
  - `BENCH_Z = DRUM_TOP - DRUM_H`
  - `BASE_MOTOR_AT`: at 270°, `BASE_BELT_C` from the axis
    - the motor's body is under the shelf, its shaft up
    - its 20T's teeth band is `RING_Z`
  - `SHELF`: its top under the 20T's hub by 1.0
  - `FLAT`: the drum's wall at 270° is cut back to a plane at r ≤ (`BASE_BELT_C` − 3 − 21.15 − 1.0). The wall stays `DRUM_WALL` thick there, and the flat is ≥ 42.3 + 4 wide.
  - `PHI_TAB`/`PHI_BLOCK`/`BASE_HALL`: as now, at the new heights
- **Produces in `shoulder.py`:** `turntable()`, `base_ring()`, `base_retainer()`, `fixed_base()`, `base_motor_box(slot)`, `base_belt_envelope(slot)`.

- [ ] **Step 1: Write the failing checks** in `check_base()` and `check_legs()`. Keep every current assert that still applies. Delete the spigot, spacer and cap asserts. Add or change:
  - **Bearings:**
    - the cylinder's land is r 25.0 +0/+0.1 across both inner rings
    - the seats are r 32.5 +0/+0.1
    - the inner rings are clamped (the ring's shoulder above, the retainer below, a spacer between), with ≥ 0.3 of contact
    - nothing turning comes within 0.5 of the outer rings' faces, and nothing fixed comes within 0.5 of the inner rings'
  - **The motor:**
    - at slot −3 and +3, its body is ≥ 1.0 from the drum's flat, the leg sockets and the legs
    - its 20T band is `RING_Z` ± 0.05
    - nothing that turns with φ (the turntable, the ring, the bracket, the post, and the tubes' lower ends) comes within 1.0 of the motor, its 20T or its belt envelope, at every φ in 5° steps over `PHI_RANGE`
  - **Screws:**
    - the motor's screws and the push screw have a straight tool path from above, ≥ head + 30, clear of the turntable's rim at the φ where they're reached (report it)
    - the retainer's screws have one from below the open drum
    - the screw rule for both
  - **The drum:**
    - its underside is flat at `BENCH_Z`
    - the volume cap stays at `FIXED_BASE_MAX_CM3`; if the flat and the bearing seats push it over, raise it with a ledgered ruling and the new sliced grams
  - **The legs:** the five contacts lie on `BENCH_Z` ± 0.2, as now.
  - **Report:** `bench_to_shoulder_axis_mm` (219.5 today), `base_6810_spacing`.
  - Run `shoulder.py`. Expected: fails on `NameError: base_retainer` or `CYL`.
- [ ] **Step 2: Build.**
- [ ] **Step 3: Run `shoulder.py`.** Expected: `SHOULDER DONE`. Note `bench_to_shoulder_axis_mm`: about 150, if the drum stays 75 tall.
- [ ] **Step 4: Commit** (ask first).

### Task 4: The whole arm on the new shoulder and base

**Files:**
- Modify: `tools/blender/head_concept.py` (the `--shoulder` block)
- Output: `model/head-concept/shoulder/*.png`, `model/head-concept-shoulder.blend`

**Interfaces:**
- **Consumes:** every STL and `poses.json` above, plus `S.PSI_RANGE`, `S.BENCH_Z`, `S.LEG_PHI`, `S.BASE_MOTOR_AT`, `E.SH_MOTOR_Z` and `E.SH_PULLEY_Y0`.
- **Changes:**
  - `SH_MOVING_STL` becomes the parts that turn with ψ:
    - the shoulder compact's housing, from `model/cycloid-poc/20-1-compact-m25/`, posed rear face at `S.COMPACT_REAR_Y`
    - the shoulder motor, its 20T and its idler, posed on plate B
    - the 80T on the rod
  - The hub, the lug, the output plate, the tubes, the bracket and the post become fixed, and turn with φ.
  - `PHI_TURNING_STL` gains `shoulder-hub`, `shoulder-lug`, `shoulder-output-plate`, `shoulder-socket-bracket`, `shoulder-rod-post` and the tubes.
  - `SH_SKIP_STL` loses the jig and the 23's plate.

- [ ] **Step 1: Write the failing checks:**
  - **Capacity masses:** the turning group holds exactly one `MOTOR_G` and one `COMPACT_G` for the shoulder, and one each for the elbow. Assert by name count. No shoulder motor stays in `shoulder_fixed()`.
  - **Carried over:** bench reach over every 15° of φ (assert `reaches`, report the worst φ), the soft-limit table over φ, the capacity count (reported), the current cap, and tipping.
  - **New:** `bench_to_shoulder_axis_mm` is reported, and equals the shoulder report's to 0.1.
  - Run `-- --shoulder`. Expected: fails on a missing STL (`shoulder-hub-b`) or on the mass assert.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Run `--shoulder`.** Expected: `HEAD DONE`. Then rerun the five unchanged baselines: identical HEAD lines. Restore their PNGs, and run `--shoulder` last.
- [ ] **Step 4: Commit** (ask first).

### Task 5: Print sheets and plates

**Files:**
- Rewrite: `model/shoulder/PRINT.md` and `model/shoulder/print/*.3mf`, by the last session's method: export then slice each 3mf once, and use bash for the file list.
- Modify: `model/elbow/PRINT.md`. Both upper plates are now a reprint. Drop the drilling step, and point to the shoulder sheet for the shoulder end.
- Delete: obsolete plates (`git rm`).

- [ ] **Step 1: Arrange the plates.** The pulleys and the ring print at 0.12, the pads in TPU on their own plate, the two upper plates on their own plate(s). Slice each once for its time and grams.
- [ ] **Step 2: Write `PRINT.md`** in the current shape:
  - **Not printed:**
    - the `--m25-roll` compact, with input rod `rod_out_mm`
    - two 17HS19-2004S1s
    - three 6810s: plate A, and two in the drum
    - one 625
    - the 420 and 477 belts
    - three tubes for the bracket, cut to `TUBE_ENDS`' lengths, and four 250s for the legs
  - **Hardware,** from `REPORT["bolts"]`.
  - **The shoulder current cap,** in bold.
  - **Assembly order:**
    1. the drum and legs
    2. the 6810s into the drum, the ring and cylinder down through them, the retainer
    3. the turntable
    4. the base motor from under the shelf, and the belt
    5. the arm round the shoulder compact: compact on plate B, the hub on its output, plate A over the hub's 6810, the lug keyed on (one way only), the cross members glued last
    6. the shoulder motor, the idler and the belt
    7. the tubes into the lug and the bracket
    8. the bracket and the post onto the turntable
  - **Range and load:** ψ range and stops, φ ±170, bench reach, the shoulder axis height above the bench, the soft limits, the capacity count, the rod's side load, and tipping (clamp the feet).
- [ ] **Step 3: Commit** (ask first).
- [ ] **Step 4: Update the memory** `cybot-shoulder-base-design.md` and its `MEMORY.md` line.
