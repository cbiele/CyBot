# Low Shoulder and Flat Stand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the V2 shoulder, body and stand from the first build (main, up to `94a9a2e`):
- the compact sits inside the arm on a fixed hollow stub from wall A
- the shoulder axis is as low as the parts allow, over a small round turntable
- the motor bracket is built into a wall
- the fixed base is a drum on the bench, with four legs at 15° and the base motor on top, as on V1
- the whole-arm check reports bench reach, soft limits over φ, the capacity count and the current cap

**Architecture:**
- **`tools/blender/shoulder_dims.py` and `tools/blender/shoulder.py` are rewritten in place.** They keep their file names, the `PARTS` / `CHECKS` / `PRINT_POSE` / `REPORT` pattern, `SHOULDER {json}`, then `SHOULDER DONE`, and the outputs in `model/shoulder/` plus `poses.json`.
  - Builders that carry over keep their names:
    - `hub_half("B")`, its plate lock, `output_plate`, `stop_collar`, `stop_blocks`
    - the spigot, spacer and cap stack, `base_ring`, the `foot` and `foot_pad` builders
  - Parts that don't carry over are deleted, with their STLs:
    - hub A
    - `compact-cage`
    - `shoulder-motor-bracket`
    - the square turntable
  - The geometry for the rest changes.
- **`tools/blender/cycloid_poc.py`:** a `--stub-mount` flag, a spin-off of `--m25-roll`, writing to `model/cycloid-poc/20-1-compact-stub/`.
- **`tools/blender/head_concept.py`:** `--shoulder` is updated in place.
- **Checks:** in-script asserts, as in every generator here. A failing assert is the failing test.

**Tech Stack:**
- Blender 5.1 Python: `/Applications/Blender.app/Contents/MacOS/Blender -b -P <script> [-- flags]`
- the libraries: `hand_lib.py` as `L`, `cycloid_math.py` as `C`, `elbow_dims.py` as `E`, `forearm_dims.py` as `F`
- slicing: the Bambu Studio CLI, as in `model/shoulder/PRINT.md`'s first version

**Spec:** `docs/superpowers/specs/2026-11-20-low-shoulder-flat-stand-design.md`. Its predecessor is `docs/superpowers/specs/2026-11-19-shoulder-base-design.md`; where the new spec says "unchanged", the old one's numbers hold.

## Global Constraints

- **The shoulder frame is unchanged.**
  - The origin is on the shoulder axis, at the arm's mid-plane.
  - +y runs toward plate A, z is up, and x is forward.
  - The base axis is the z axis.
  - The elbow frame maps in as (x, y, z + `E.UPPER_L`).
  - `rot_shoulder(psi)` = `Rotation(psi, 'Y')`.
- **Angles:**
  - ψ 0 is the upper arm straight up, +90 is level toward +x.
  - `PSI_STOPS` is computed in Task 3, with `PSI_RANGE` 2° inside it. Both must be past ±90.
  - `PHI_RANGE = (-170.0, 170.0)`, with `PHI_STOPS = (-172.0, 172.0)`.
  - Home is ψ 0, φ 0.
- **Pinned numbers (from the spec):**
  - The 6810: `E.B6810`. The plates are 60 apart inside (`E.PLATE_GAP`), `E.PLATE_T` 8.5 thick, seat Ø65, lip on the inner face, ends r38.
  - The shoulder belt: 3M-420, with a 20T and an 80T, `SHOULDER_BELT_C` 131.89, slot ±3, 80:1.
  - The base belt: 3M-477, with a 20T and the 130T ring, `BASE_BELT_C` 113.89, slot ±3, 6.5:1.
  - The 17HS19-2004S1: 42.3 square, 48 long, M3 on a 31 square, pilot Ø22.
  - The NEMA23 envelope: 57 square, 76 long, M5 on a 47.14 square, pilot Ø38.1.
  - The legs: four 9 × 7 tubes, 250 long, about 15° below horizontal.
  - Holes are as in the first build: M3 clearance r 1.7, insert pilot r 2.0 × 5 deep, M5 clearance r 2.75. Bolts are M3, ≤ 50 long.
- **Loads:**
  - `SHOULDER_DESIGN_NMM = 13.5e3` for the hub lock, the output link and the stops. Printed parts stay ≤ 10 MPa in bearing and in shear.
  - The shoulder current cap: `SHOULDER_CURRENT_CAP_A = 2.0 * 13.5 / (0.59 * 80)`, about 0.57 A. It's reported and printed on the sheet.
- **The printed upper-arm plates stay byte-identical.** Only plate B is drilled, through the keyed jig. Plate A gets a 6810 in its seat and no holes.
- **Do booleans in a part's local frame before posing it,** then `L.finish`. Each part is one island with 0 non-manifold edges, and its print-pose footprint fits inside 220 × 250.
- **Every screw:**
  - its head (or nut) has ≥ 0.5 of clearance round it, and a straight tool path from outside of ≥ the head's height plus 30 mm, at every slot position
  - its length ≤ grip + insert depth − 0.5
  - It's checked by rays against the assembled parts.
- **Running gaps:** every part fixed to the body stays ≥ 0.5 from every part that turns with the arm, at every ψ in `PSI_RANGE`, in 1° steps. That includes the stub, the compact housing, the walls and the stop blocks, against plate A, its lip, hub B, the stop collar and the elbow parts.
- **`head_concept.py` regression:**
  - The HEAD lines for no flag, `--compact-drive`, `--t8-through`, `--tube-forearm`, `--offset-wrist` and `--elbow` stay identical to the baselines taken before Task 6.
  - Restore the PNGs with `git checkout -- model/head-concept/`.
  - Note that zsh doesn't word-split: pass flags as `-- --$v`.
- **Don't commit the user's unrelated work** (as listed in the 2026-11-19 plan, plus `.superpowers/`). Stage files by name.
- **Commit messages say why** and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Ask the user before each commit, and stage the files first.

## Review Focus

1. **A fixed part rubbing a turning one.** This build inverts the first: the compact and stub are fixed inside an arm that turns round them. A stub collar touching plate A's lip, or the housing's rear face on plate A's inner face, would bind the shoulder.
   - Pinned by Task 2's running-gap sweep, and Task 3's for the walls and stops.
2. **Screw heads that can't seat or can't be reached.**
   - In the first build, the motor screws' heads were trapped under the swap plate's bracket, and the base push screw was in a 13 mm gap.
   - Pinned by the Global Constraints' screw rule, with tests in Tasks 2, 3 and 4.
3. **The jig going on the wrong way.** Plate B can't be reprinted.
   - Pinned by Task 2's 180° assert.
4. **Soft limits that miss the fixed obstacles.**
   - The legs and the base motor don't turn with φ, and the arm now dips past level near them.
   - Pinned by Task 6's φ-sweep, compared against a φ-0-only run.
5. **A drum or legs that don't sit on five points.**
   - If the pads end above or below the drum's underside, the stand rocks on four points, or on the drum alone.
   - Pinned by Task 5's coplanarity check.

---

### Task 1: The compact's stub-mount housing

**Files:**
- Modify: `tools/blender/cycloid_poc.py`
- Output: `model/cycloid-poc/20-1-compact-stub/housing-rear.stl` and `housing-front.stl` (the other parts are unchanged from `--m25-roll`)

**Interfaces:**
- **Produces:** the flag `--stub-mount`, which implies `--m25-roll`.
  - The rear housing gains 4 M3 inserts in its rear face: `STUB_SCREW_R = 21.5`, at 0/90/180/270 (between the R30 bolts at 45 + 90k), r 2.0, 5 deep.
  - In `shoulder_dims`, add `STUB_SCREW_R`, `STUB_SCREW_ANGLES`, and `REAR_HUB_PROUD_R = HUB_D / 2 + 1.0`. The stub's inner face must clear the rear carrier's turning hub, which stands 1.0 proud.
- `--m25-roll` alone produces byte-identical housings, so they're diffed.

- [ ] **Step 1: Write the failing checks** in `check_stub_mount()`, run when the flag is set:
  - each insert hole has ≥ 1.2 of wall to the 6804 seat, the R30 bolt holes and the outer face, by `material_round`-style rays copied from `shoulder.py`
  - the insert depth plus 1.0 doesn't reach the first ring-pin hole's z
  - Run: `Blender -b -P tools/blender/cycloid_poc.py -- --m25-roll --stub-mount`. Expected: fails on `NameError: check_stub_mount` (or on the assert, before the cut).
- [ ] **Step 2: Cut the inserts and route the output folder.**
- [ ] **Step 3: Run with both flags.**
  - Expected: the script's DONE line, with the new folder written.
  - Then run with `--m25-roll` alone. Expected: `git status` shows no change under `20-1-compact-m25/`.
- [ ] **Step 4: Commit** (ask first).

### Task 2: The fixed stub, plate A's bearing, hub B's nose, the output link, and the keyed jig

**Files:**
- Modify: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`
- Delete: `model/shoulder/shoulder-hub-a.stl`, `compact-cage.stl`
- Output: `model/shoulder/shoulder-stub.stl`, `shoulder-hub-b.stl` (rebuilt), `shoulder-output-plate.stl`, `plate-drill-jig.stl` (rebuilt), `poses.json`

**Interfaces:**
- **Consumes:** Task 1's `STUB_SCREW_R`, `STUB_SCREW_ANGLES`, `REAR_HUB_PROUD_R`.
- **Produces in `shoulder_dims`:**
  - `COMPACT_REAR_Y`: the housing's rear face, ≤ `E.Y_REAR` − 0.5.
  - `COMPACT_Y = COMPACT_REAR_Y - F.HUB_FACE`: the output face.
  - `STUB`: a dict with these keys:
    - `bore_r`: the rod passes with ≥ 0.5, and at the inner face it's ≥ `REAR_HUB_PROUD_R`
    - `bearing_r = B6810[0]`
    - `y`: (inner face, outer end)
    - `screw_l` from stock, driven from the outer end through counterbored channels
  - `HUB_B_NOSE`: (r ≤ `E.LIP_IN_R` − 0.5, y0 = `COMPACT_Y` − `OUT_PLATE_T`, y1 = plate B's lip face).
  - `ROD_OUT`: the input rod past the housing's rear face, through the stub, wall A and the 80T.
- **Produces in `shoulder.py`:**
  - `stub() -> Object`
  - `hub_half("B")`, now with the nose and the output plate's dogs and screws at its inner end. Hub B's bore is open from wall B's side for the screwdriver.
  - `drill_jig()`, for plate B only
  - `fixed_shoulder() -> list[Object]` (the stub and the compact housings)
  - `turning_shoulder(psi) -> list[Object]` (both plates, the elbow motor at both slot ends, the elbow belt envelope, hub B, the output plate and the 6810's outer-ring zone)

- [ ] **Step 1: Write the failing checks** in `check_shoulder_core()`:
  - **Parts:** one island each, 0 non-manifold, on the bed.
  - **Bearing:** the stub's bearing land is r 25.0 +0.0/+0.1 across the 6810's width in plate A's seat. The inner ring is clamped axially on both faces by fixed parts (≥ 0.3 of contact ring each side). Nothing fixed comes within 0.5 of the outer ring's or the lip's radius band, r ≥ 27.5.
  - **Running gaps:** `fixed_shoulder()` against `turning_shoulder(psi)` is ≥ 0.5 at every ψ from −180 to +180 in 1° steps. The compact and stub must clear a full turn, so the range found later can't be limited by them. Include the lowest cross members and the elbow motor at both slot ends; the expected minimum is about 7 to the motor.
  - **Link:**
    - the output plate's dogs sit in hub B's nose
    - its M3 × 12s reach 3.0–4.0 into the carrier's inserts
    - the nose stays r ≤ `E.LIP_IN_R` − 0.5 through plate B's lip
    - the dog bearing and nose shear are ≤ 10 MPa at 13.5 N·m
  - **Hub B's lock:** carried over from the first build: ray wall ≥ 1.2 per hole and shear ≤ 10 MPa.
  - **Jig:**
    - it seats on plate B the right way: overlap < 0.05 mm³, touching, guides clear
    - **turned 180° about the seat axis, it overlaps plate B by ≥ 1.0 mm³ and can't seat** (new: the first build's jig seated both ways)
  - **Screws:** the Global Constraints' screw rule for the stub screws, the hub-floor screws and the lock screws.
  - Run `shoulder.py`. Expected: fails on `NameError: stub`.
- [ ] **Step 2: Build** the parts. Delete hub A, the cage, their builders and their checks, and the outboard compact pose.
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE`. The report has `stub`, `rod_out_mm`, `shoulder_core_min_gap_mm`, `jig_180_overlap_mm3`, `link_mpa`.
- [ ] **Step 4: Commit** (ask first).

### Task 3: Low walls, the shoulder range and stops, the motor bracket in the wall, the 80T and belt

**Files:**
- Modify: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`, `tools/blender/htd3m_pulley.py` (only if the 80T's bore or hub changes for the rod's length; otherwise untouched)
- Delete: `model/shoulder/shoulder-motor-bracket.stl`
- Output: `body-wall-A.stl`, `body-wall-B.stl`, `shoulder-stop-collar.stl`, `shoulder-motor-plate-17.stl`, `shoulder-motor-plate-23.stl`

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - `SHOULDER_AXIS_Z`: the smallest value, in 0.5 steps, that leaves every part at or under the axis ≥ 3.0 above the turntable's top at ψ 0. Report it, and assert ≤ 60 (the spec's estimate is 50–60).
  - `PSI_STOPS`: the largest |ψ| in 1° steps at which `turning_shoulder(psi)` stays ≥ 1.0 from the walls, the bracket, the motor envelopes (17 and 23, both slot ends) and the turntable's top disc, minus 2°, symmetric. Assert both are > 92.
  - `PSI_RANGE`: 2° inside the stops.
  - `MOTOR_WALL`: "A" or "B", your call; record it.
  - `SHOULDER_MOTOR_AT`: `SHOULDER_BELT_C` from the 80T's axis at slot-mid, along a direction of your choice that keeps the motor off the turntable's swept disc. The belt runs roughly level; record the direction.
  - `MOTOR_SLOT = 3.0`, along the belt's centre line.
  - `PLATE_MOUNT`: the drop-in plate's seat in the wall's bracket, the same for the 17 and the 23.
  - the push-screw tensioner
  - `TURNTABLE_R`, provisional: the smallest r that carries both walls' feet with ≥ 2 of edge. Task 4 consumes it.
- **Produces in `shoulder.py`:** `wall_a()`, `wall_b()` (one of them with the bracket), `motor_plate(kind)`, `shoulder_motor_box(kind, slot)`, `shoulder_belt_envelope(slot)`, `stop_collar()`, `stop_blocks()`.

- [ ] **Step 1: Write the failing checks** in `check_body()` and `check_shoulder_drive()`:
  - **Carried over from the first build:**
    - parts, the fits of the walls' 6810s and the stub's fixing in wall A
    - the elbow belt envelope against wall A, the 80T and the belt in 1° steps over `PSI_RANGE` at both elbow slot ends
    - the belt centres at slot −3, 0 and +3 = `SHOULDER_BELT_C` + slot ± 0.1
    - the plates' identical outer patterns
    - the stops touching at `PSI_STOPS` ± 0.3 and ≥ 1.0 apart 2° inside them
    - the Hall gap 1.0–2.0 at ψ 0
  - **The bracket's screws:** for both kinds, at slot −3, 0 and +3, every motor-screw head has room (≥ 0.5 all round) and a tool path. This is the first build's Critical review finding: test it by placing an M3 head cylinder (r 2.75 × 3) and an M5 one (r 4.25 × 5) at each head position, against the bracket and the wall.
  - **The push screw:** a straight tool path of ≥ 33 mm from its head.
  - **The stop collar:**
    - it fits only one way round: turned 180° about the axis, it overlaps hub B's key slots or doesn't seat
    - or it's symmetric in function, with the magnet in both tabs and blocks for both. Your call; record it.
  - **The axis:** `SHOULDER_AXIS_Z` ≤ 60, and `PSI_STOPS` past ±92.
  - Run. Expected: fails on the first missing name.
- [ ] **Step 2: Build.**
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE`. The report has `shoulder_axis_z`, `psi_stops`, `motor_wall` and `shoulder_motor_at`.
- [ ] **Step 4: Commit** (ask first).

### Task 4: The round turntable, the drum, the 130T, and the base motor on top

**Files:**
- Modify: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`
- Output: `turntable.stl`, `fixed-base.stl`, `base-ring-130T.stl`, `spigot-spacer.stl`, `spigot-cap.stl`, `base-motor-plate.stl`

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - `TURNTABLE_R`: from Task 3, ≤ the provisional value + 5.
  - `TURNTABLE_Z = -SHOULDER_AXIS_Z`.
  - `BASE_MOTOR_AT`: the motor stands shaft-down on a raised arm of the drum, beside the turntable, as on V1 (`tools/blender/spider_base.py`). Its 20T sits under the arm at the 130T's tooth band. The motor's body is ≥ 3 from the turntable's disc at every φ.
  - `DRUM`: (r, top z, bottom z = `BENCH_Z`).
  - `BENCH_Z`: the bench plane, which the drum's underside sits on.
  - `PHI_STOPS` blocks and tab, and `BASE_HALL`.
- **Produces in `shoulder.py`:** `turntable()`, `fixed_base()`, `base_motor_plate()`, `base_motor_box()`, `base_belt_envelope(slot)`.

- [ ] **Step 1: Write the failing checks** in `check_base()`:
  - **Carried over from the first build:**
    - the spigot is r 25.0 +0/+0.1, the seats are r 32.5 +0/+0.1
    - the clamp bears on the inner rings only
    - the ring has 130 grooves, with OD 2·`od_r(130)` ± 0.05
    - the base belt centres at slot ±3 are ± 0.1
    - the stops are at ±172 and clear at ±170, 0 and ±90
    - the Hall gap is 1.0–2.0
    - the wall-foot inserts have ≥ 2.0 of wall
  - **The base motor and its belt envelope** clear the turntable, the walls, the shoulder bracket and its motor envelopes at every φ in 10° steps.
  - **The base push screw** has a straight tool path ≥ 33 mm from its head, with the head ≥ 0.5 above every surface (the first build's push screw was unreachable).
  - **Base motor screws** follow the Global Constraints' screw rule.
  - **The drum's underside** is flat at `BENCH_Z` (every vertex at z ≤ `BENCH_Z` + 0.01 lies on one plane), and it fits the bed.
  - Run. Expected: fails on the first missing name.
- [ ] **Step 2: Build.** Delete `ELECTRONICS_AREA`, its pilots and its check: the spec drops the area.
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE`.
- [ ] **Step 4: Commit** (ask first).

### Task 5: Flat legs, sockets, feet and pads

**Files:**
- Modify: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`
- Output: `foot.stl`, `foot-pad.stl`, `fixed-base.stl` (with sockets)

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - `LEG_DEG`: 15.0, or within 12–18 if the socket and drum height need it. Record it.
  - `LEG_PHI`: 45 + 90k, unless the base motor's arm sits there. If so, rotate the set and record it.
  - `leg(phi)`, `LEGS`, `FOOT_PADS`.
- **Produces in `shoulder.py`:** `foot_part()`, `foot_pad()` and `leg_sockets(f)`, carried over with the new angle.

- [ ] **Step 1: Write the failing checks** in `check_legs()`:
  - **Carried over from the first build:**
    - socket wall ≥ 2.0
    - the pinch insert's wall
    - the foot's clamp tab is ≥ 30 × 30 × 6
    - pads level to 0.5°
  - **Five contact points:** every pad's bottom and the drum's underside lie on `BENCH_Z` ± 0.2.
  - **The legs** don't touch the base motor, its belt or the turntable at any φ in 10° steps.
  - **The socket pinch screws** follow the screw rule.
  - **Report:**
    - `footprint_r_mm`, the inscribed radius of the pads' polygon
    - the drum's height
  - Run. Expected: fails on the coplanarity assert, or on a missing name.
- [ ] **Step 2: Build.**
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE`.
- [ ] **Step 4: Commit** (ask first).

### Task 6: The whole arm: bench reach, soft limits over φ, capacity, current cap

**Files:**
- Modify: `tools/blender/head_concept.py` (the `--shoulder` block)
- Output: `model/head-concept/shoulder/*.png`

**Interfaces:**
- **Consumes:** every STL and `poses.json` above, `S.PSI_RANGE`, `S.BENCH_Z`, `S.LEG_PHI`, `S.BASE_MOTOR_AT`.
- **Produces report keys:**
  - `bench_reach`: `{"reaches": bool, "closest_r_mm": float, "pose": [psi, theta, pitch]}`
  - `shoulder_soft_limits`: the union over φ
  - `shoulder_soft_limits_phi0`
  - `shoulder_over_capacity`: a count, and the worst pose
  - `shoulder_current_cap_a`
  - `psi_range`
  - `tip_margin_mm`, `tip_note`

- [ ] **Step 0: Take the six regression baselines** (Global Constraints) before editing.
- [ ] **Step 1: Write the failing checks:**
  - **Bench reach:** the tool point (`tip`) reaches z ≤ `BENCH_Z` + 2 at some pose in `PSI_RANGE` × `E.RANGE` × the wrist pitch range, with no clash against the body, the base or the legs. Assert `reaches`. Report the smallest horizontal distance from the base axis at which it touches.
  - **Soft limits:**
    - Compute them at φ ∈ {0, 45, …, 315} ∪ {the base motor's φ, relative}, and report the union. The fixed parts (legs, drum, base motor) are rotated by −φ about z; the turntable and body aren't.
    - Assert the union is a superset of the φ-0 table, and report both. The review's finding was that the first build checked φ 0 only.
  - **Home sweep:** ψ 0 across every elbow angle reports clashes in `shoulder_soft_limits`. It's no longer an assert, because the spec makes the folded forearm a soft limit at a low axis.
  - **Capacity:**
    - `shoulder_capacity_nm = min(elbow_demo × 80 / 60, 13.5)`
    - count the poses whose static load is over it
    - this is reported, not asserted
  - **Current cap:** report `shoulder_current_cap_a`, which must equal `S.SHOULDER_CURRENT_CAP_A`.
  - **Tipping:** as now: report it, with "clamp the feet" under 15 mm.
  - Run `-- --shoulder`. Expected: fails on a `KeyError`, or on `bench_reach`, before the new code.
- [ ] **Step 2: Implement.**
- [ ] **Step 3: Run `--shoulder`.** Expected: `HEAD DONE`. Then rerun the six baselines: identical HEAD lines. Restore the PNGs for those variants, then run `--shoulder` last.
- [ ] **Step 4: Commit** (ask first).

### Task 7: Print sheet and plates

**Files:**
- Rewrite: `model/shoulder/PRINT.md`, and `model/shoulder/print/*.3mf`, by the first version's method. That's flattened profiles in the scratchpad's `bambu/` folder, export then slice each 3mf once, and bash for the file list.
- Delete: the obsolete plates and STLs (`git rm`).
- Modify: `model/elbow/PRINT.md`, only where it points to the shoulder sheet for drilling: now plate B only.

**Steps:**
- [ ] **Step 1: Arrange the plates.** Group them as you see fit, with the pulleys and the ring at 0.12 and the pads in TPU on their own plate. Slice each once for its time and grams. Every part sits on one plate per 3mf.
- [ ] **Step 2: Write `PRINT.md`** in the first version's shape:
  - **Not printed:**
    - the stub-mount compact (`cycloid_poc.py -- --m25-roll --stub-mount`, input rod `rod_out_mm`)
    - two 17HS19-2004S1s
    - the 6810s: plate A, wall B, two on the spigot
    - the 420 and 477 belts, and the four tubes, uncut
  - **Hardware** from `REPORT["bolts"]`, with counts.
  - **The shoulder current cap,** in bold, with its basis. Confirm it at the bench.
  - **Drilling:** plate B only, with the jig, which only goes on one way.
  - **Assembly order:**
    1. the drum and legs
    2. the turntable stack, then the base motor and belt
    3. the walls and their bearings
    4. plate A's 6810, the stub through it, then the compact on the stub
    5. hub B into plate B and wall B, then the link
    6. the 80T, the motor plate and the belt
    7. the stops and Hall, with "tab down" if the collar is keyed
  - **Range, stops and load:**
    - ψ range and stops
    - φ ±170
    - bench reach
    - the soft-limit summary, over φ
    - the capacity count
    - tipping: clamp the feet
- [ ] **Step 3: Commit** (ask first).
