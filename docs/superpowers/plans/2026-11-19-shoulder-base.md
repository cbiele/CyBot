# Shoulder (Axis 2), Body and Turning Base (Axis 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and check the printable V2 shoulder and base:
- a new shoulder hub locked to the printed upper-arm plates
- two body walls on 6810s, with the compact cycloid and the 80T on wall A
- a swappable NEMA17/NEMA23 shoulder motor plate
- a turntable on two 6810s with a 130T ring
- a fixed base with the base motor and four aluminium tube leg sockets, and the feet

Then lay out the whole V2 arm in the head concept, and check:
- that the shoulder sweeps clear
- the shoulder torque against the measured elbow figure
- that the arm won't tip on its legs

**Architecture:**
- **`tools/blender/shoulder_dims.py`** (new): the shoulder frame and every pinned number.
- **`tools/blender/shoulder.py`** (new), in `elbow.py`'s pattern:
  - `PARTS`, `CHECKS`, `PRINT_POSE`, `REPORT`, then `SHOULDER {json}`, then `SHOULDER DONE`
  - it writes STLs in print pose to `model/shoulder/`, plus `poses.json`
  - the built upper arm comes in from `model/elbow/*.stl` through `model/elbow/poses.json`. Never `import elbow`, because it runs on import.
- **`tools/blender/htd3m_pulley.py`:** one new `PULLEYS` entry, the 80T. The two 20Ts are reprints of `axis3-pulley-20T`, since the 17HS19-2004S1 has the same Ø5 D shaft.
- **`tools/blender/elbow.py`:** loses the superseded `shoulder-hub`, `shoulder-hub-clamp` and `bench-stand`. The plates stay byte-identical.
- **`tools/blender/head_concept.py`:** a new `--shoulder` flag, which implies `--elbow`. It places the shoulder, body, base and legs under the elbow layout, then:
  - sweeps the shoulder against the elbow
  - reports the shoulder torque
  - reports the tipping margin
- **Checks:** in-script asserts, as in every generator here. A failing assert is the failing test.

**Tech Stack:** Blender 5.1 Python (`/Applications/Blender.app/Contents/MacOS/Blender -b -P <script> [-- flags]`), `hand_lib.py` (as `L`), `cycloid_math.py` (as `C`), `elbow_dims.py` (as `E`), `forearm_dims.py` (as `F`).

**Spec:** `docs/superpowers/specs/2026-11-19-shoulder-base-design.md`

## Global Constraints

- **The shoulder frame (`shoulder_dims.py`):**
  - The origin is on the shoulder axis, at the upper arm's mid-plane.
  - y runs along the shoulder axis toward plate A (+y), as in the elbow frame.
  - z is up, and x is forward, the direction the forearm reaches.
  - The base axis is the z axis (x = y = 0). The arm's mid-plane passes through it.
  - The elbow frame maps in as (x, y, z + `E.UPPER_L`). The built parts in `model/elbow/` are already in the pose where the upper arm stands straight up from the shoulder.
- **Angles:**
  - Shoulder pitch ψ: 0 is the upper arm straight up, and +90 is level toward +x. `PSI_RANGE = (-90.0, 90.0)`, with the stops at ±92. That's the user's 0 to 180 in V1's convention, which counts 90 as straight up.
  - Base angle φ about +z: `PHI_RANGE = (-170.0, 170.0)`, with the stops at ±172.
  - Home is ψ 0 and φ 0.
- **Pinned numbers:**
  - The 6810: `E.B6810 = (25.0, 32.5, 7.0)`. The seats are nominal Ø65.00, a proven fit.
  - The 17HS19-2004S1:
    - 42.3 square and 48 long, with M3 on a 31 square
    - pilot Ø22 × 2
    - Ø5 shaft with a D flat 0.5 deep, 24 long
    - the motor plate leaves room for 60 long
  - The NEMA23 plate: 57 square, M5 on a 47.14 square, pilot Ø38.1, up to 76 long. Its outer pattern and slots are the same as the NEMA17 plate's.
  - The shoulder belt: 3M-420 with a 20T and an 80T. `SHOULDER_BELT_C = C.belt_centre_distance(20, 80, 420, pitch=3.0)` (131.89), with ±3 of slot. `SHOULDER_RATIO = 80`.
  - The base belt: 3M-477 with a 20T and a 130T ring. `BASE_BELT_C = C.belt_centre_distance(20, 130, 477, pitch=3.0)` (113.9), with ±3 of slot. `BASE_RATIO = 6.5`.
  - The compact: the `--m25-roll` housings (`model/cycloid-poc/20-1-compact-m25/`), Ø68 × 38.6, with R30 bolt holes. The output face is 39.6 from the rear face. It has three M3 inserts on R6.5 and the dogs on `F.DOG_PCD_R`/`F.DOG_R`/`F.DOG_ANGLES`. The Ø5 input rod comes out of the rear face.
  - The tube: 9 × 7 (`E.TUBE_OR`, `E.TUBE_IR`), four of them, 250 long.
  - Holes:
    - M3 clearance r 1.7
    - M3 heat-set insert pilot r 2.0, 5 deep
    - M3 nut pocket 5.8 AF × 2.6
    - M5 clearance r 2.75
  - Bolts come from `M3_STOCK = (40, 45, 50)` or shorter. A through-bolt into a nut has grip ≤ length ≤ grip + 2. Reuse `elbow.py`'s `bolt_for_nut` logic by copying it, not importing it.
- **The loads used for sizing:**
  - `SHOULDER_DESIGN_NMM = 13.5e3`: 1.5 times the spec's 9 N·m estimate. Task 6 replaces the estimate with the model's figure. If that comes out higher than 9, raise this to 1.5× the new figure and rerun Tasks 1–2's checks.
  - Printed parts carrying it must stay ≤ 10 MPa bearing and ≤ 10 MPa shear.
- **Don't touch the printed upper arm:**
  - `upper-plate-A.stl` and `upper-plate-B.stl` must stay byte-identical (`git diff --stat` empty for them).
  - The plates may only be drilled, using a printed drill jig that the generator outputs.
  - The elbow's parts and the forearm's are read, not changed.
- **Do booleans in a part's local frame before posing it.** `L.finish` each part. Each exported part must be one island with 0 non-manifold edges.
- **The bed is 225 × 255.** Each part's print-pose footprint must fit inside 220 × 250, on the diagonal if needed.
- **Regression for `head_concept.py`:**
  - The HEAD lines for no flag, `--t8-through`, `--tube-forearm`, `--offset-wrist` and `--elbow` must be the same as before Task 6. The one exception is `--elbow` keys that Task 1's part removal changes; record those as a ruling.
  - Restore the other variants' PNGs and blends with `git checkout --`.
- **Don't commit the user's unrelated work:**
  - the hand files
  - the base/spider files (`spider_base.py`, `model/base/spider-arm-motor.stl`)
  - `hand_lib.py`
  - the 2026-09 docs
  - "CyBoT notes.pages"
  - `exploded.png`
  - `finger-coupon-scene.blend`
  - `result.json`
  - `.superpowers/`
  
  Stage files by name.
- **Commit messages say why** and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Ask the user before each commit, and stage the files first.

## Review Focus

1. **The elbow's belt side sweeping past wall A.** The elbow motor (71 from the shoulder axis), its 20T, the idler and the belt stand out to `E.BELT_ENVELOPE_Y` and swing about the shoulder. Wall A, the compact, the 80T and the shoulder belt must clear that swept volume at every ψ in `PSI_RANGE`, in 1° steps, and at both elbow-motor slot ends.
2. **The torque lock between the hub and the printed plates.**
   - The plates are thin, and the shoulder bosses are only about r 38.
   - Every drilled hole must land in plate material with ≥ 1.2 of wall to the seat, the boss edge and the lightening windows. Check by ray against the plate STLs, not by arithmetic.
   - The lock must carry `SHOULDER_DESIGN_NMM` within the stress limits.
3. **The folded forearm against the body and the base.**
   - At ψ 0, every elbow angle in `E.RANGE` must clear the walls, the turntable and the legs.
   - At other ψ, collisions are allowed, but they must be reported as a soft-limit table, not dropped.
4. **Tipping.** At the worst reach (ψ ±90, elbow and wrist out, the hand plus 500 g) in eight φ directions, the whole arm's centre of mass must stay inside the polygon of the feet's pad centres. Report the margin. A margin under 15 mm is reported as "clamp the feet", not asserted.
5. **The tension slots' direction.** Each motor slot must run along its belt's centre line. Otherwise tensioning changes the centre distance less than the slot's length suggests, and the ±3 can't be reached. Check both slot ends' centre distance at `*_BELT_C` ± 3 ± 0.1.

---

### Task 1: The shoulder frame, the posed upper arm, the new hub, its plate lock and drill jig

**Files:**
- Create: `tools/blender/shoulder_dims.py`, `tools/blender/shoulder.py`
- Modify: `tools/blender/elbow.py`: remove `shoulder_hub`, `shoulder_clamp`, `bench_stand`, `check_shoulder` and their `PARTS` entries. Keep `index_holes` on plate B, so plate B stays byte-identical.
- Delete: `model/elbow/shoulder-hub.stl`, `shoulder-hub-clamp.stl`, `bench-stand.stl`
- Output: `model/shoulder/shoulder-hub-a.stl`, `shoulder-hub-b.stl`, `plate-drill-jig.stl`, `poses.json`

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - everything pinned in Global Constraints
  - `PLATE_FACES`: the four y faces of the two plates, from `E.Y_REAR`, `E.PLATE_T`
  - `WALL_Y`: the inner and outer faces of walls A and B
    - Wall A's inner face is ≥ `E.BELT_ENVELOPE_Y` + 4.
    - Wall B's inner face is ≤ −(`E.Y_REAR` + `E.PLATE_T`) − 4.
  - `WALL_6810_Y`: one 6810 in each wall
  - `HUB_Y`: the hub's span, from wall B's 6810 to its A-end face, just outboard of wall A
- **Produces in `shoulder.py`:**
  - `elbow_part(name) -> Object`: a `model/elbow` STL posed into the shoulder frame
  - `rot_shoulder(psi) -> Matrix`: about +y through the origin. +ψ tips the upper arm toward +x.
  - `upper_arm_moving() -> dict[str, Object]`: the plates, the elbow motor box at both slot ends (60 long), and the elbow belt envelope (rebuilt as a box from `E.BELT_ENVELOPE_Y`, `E.MOTOR_Z`, `E.R60_OD`)
  - `hub() -> Object`, `drill_jig() -> Object`
  - `polar`, `cyl_y`, `overlap`, `min_gap`, `islands` and `ray_len`, copied from `elbow.py`
- **The hub:** one printed part.
  - It has a journal of r `B6810[0]` in each wall's 6810, and inner-ring shoulders ≤ r 27.5.
  - Through each plate's Ø65 seat it has a spigot of r 32.5 −0.0/+0.1, filling the seat against the lip, plus a flange on each plate's outer face.
  - The wire bore is r ≥ 18. It's open at B's end and stops at the A-end face.
  - The A-end face carries:
    - three dog holes for the compact's dogs (r `F.DOG_R` + 0.15)
    - three r 1.7 screw holes on R6.5, counterbored, as in `elbow.py`'s `hub()`
  - The A-end clears wall A's 6810 inner ring only.
  - It has to go into the plates' seats, so the hub is two parts joined inside the plate gap: `shoulder-hub-a` and `shoulder-hub-b`, each with its spigot and flange. They're bolted together through the gap with M3s into nut pockets on the axis-parallel R22–R24 ring. Record the bolt choice.
- **The plate lock:**
  - Each flange is pinned to its plate by at least 3 axial M3s through holes drilled in the plate's shoulder boss, outside the Ø65 seat, into nuts in the flange.
  - The radius and angles are yours to set to satisfy Review Focus 2. Record them in `LOCK_R` and `LOCK_ANGLES`.
  - `plate-drill-jig` locates on the Ø65 seat with a spigot and has Ø3.4 guide holes at `LOCK_R`/`LOCK_ANGLES`, 10 deep, plus a key so it can't be put on rotated. One jig serves both plates.

- [ ] **Step 1: Write the failing checks** in `check_hub()`:
  - **Parts:** each hub part and the jig is one island with 0 non-manifold edges.
  - **Fits:**
    - both journals are r 25.0 +0.0/+0.1, by `seat_diameter`-style rays
    - both spigots are r 32.5 +0.0/+0.1
    - the bore is r ≥ 18, and a ray along +y from B's end runs ≥ `HUB_Y` span − 10 before it hits anything
  - **Clearance:** `overlap(hub, plate) == 0` for both plates. The spigot touches the lip: `min_gap` ≤ 0.05.
  - **Plate lock:**
    - For each lock hole, rays from the hole's edge along ±radial and ±tangential directions hit the plate STL's surface ≥ 1.2 away, and nothing is drilled into the seat, a window or the edge.
    - Report `lock_shear_mpa` = `SHOULDER_DESIGN_NMM` / `LOCK_R` / n / (π · 1.5²) and `lock_bearing_mpa` = `SHOULDER_DESIGN_NMM` / `LOCK_R` / n / (3.0 · `E.PLATE_T`). Both must be ≤ 10.
    - The worst plate carries all the torque.
  - **Dogs:** report `dog_bearing_mpa` as in the elbow plan, with `SHOULDER_DESIGN_NMM`. It must be ≤ 10. If it isn't, add three more dogs at 60° offsets on the hub and on a new `shoulder-output-plate` replacing the compact's, then record a ruling.
  - **Elbow script:** after the edit, run `elbow.py`. Expected: `ELBOW DONE`, and `git diff --stat model/elbow/upper-plate-*.stl` is empty.
  - **Run** `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/shoulder.py`. Expected: fails on a `NameError` or the first assert, with no `SHOULDER DONE`.
- [ ] **Step 2: Write `shoulder_dims.py`.** Its docstring cites the spec. Pick `WALL_Y`, `WALL_6810_Y` and `HUB_Y` so that Step 1's checks can pass. It doesn't print anything.
- [ ] **Step 3: Write `elbow_part`, `rot_shoulder`, `upper_arm_moving`, `hub` (both parts) and `drill_jig`.** Print poses:
  - each hub part prints flange face down
  - the jig prints spigot up
- [ ] **Step 4: Run both scripts.** Expected: `SHOULDER {...}` with `lock_shear_mpa`, `lock_bearing_mpa`, `dog_bearing_mpa` and `LOCK_R`, then `SHOULDER DONE`. `ELBOW DONE` with the plates unchanged.
- [ ] **Step 5: Commit** (ask first):
  - `shoulder_dims.py`, `shoulder.py`, `elbow.py`
  - `model/shoulder/shoulder-hub-a.stl`, `shoulder-hub-b.stl`, `plate-drill-jig.stl`, `poses.json`
  - the three deleted elbow STLs, and `model/elbow/poses.json`

### Task 2: Body walls, the compact on wall A, shoulder stops and Hall

**Files:**
- Modify: `tools/blender/shoulder.py`, `tools/blender/shoulder_dims.py`
- Output: `model/shoulder/body-wall-A.stl`, `body-wall-B.stl`, `compact-cage.stl` (if the compact needs standoffs)

**Interfaces:**
- **Consumes:** Task 1's frame, `hub()`, `upper_arm_moving()` and `rot_shoulder`.
- **Produces in `shoulder_dims`:**
  - `COMPACT_Y`: the compact's output face on the hub's A-end. The housing is fixed to wall A by its four R30 holes through standoffs, or through the cage, with nuts.
  - `PULLEY80_Y`: the 80T's inside face, ≥ 1.0 from the compact's rear face and its bolt heads. The input rod must reach through the 80T's hub; report `rod_out_mm`, the rod length needed.
  - `SHOULDER_BELT_PLANE_Y`
  - `WALL_FOOT`: each wall's bolt pattern onto the turntable, M3 into heat-set inserts in the turntable, ≥ 4 per wall
  - `SHOULDER_AXIS_Z`: the shoulder axis's height above the turntable's top face
  - `PSI_STOPS = (-92.0, 92.0)`
  - `SHOULDER_HALL`: the sensor pocket in wall B's inner face and the magnet pocket in plate B's outer face. The magnet goes in a pocket drilled into the printed plate through a second jig hole, so `plate-drill-jig` gains that hole. Rerun Task 1's checks.
- **Produces in `shoulder.py`:** `wall_a()`, `wall_b()`, `compact_posed() -> Object`, `swept_upper_arm(psis) -> list[Object]`.

- [ ] **Step 1: Write the failing checks** in `check_body()`:
  - **Parts:** each wall is one island, 0 non-manifold edges, and its footprint fits the bed.
  - **Seats:** each wall's 6810 seat is r 32.5 +0.0/+0.1, 7 deep, with a lip that bears on the outer ring only (lip inner r ≤ 31.0, ≥ the journal shoulder r + 0.5).
  - **Sweep:** for ψ from −92 to +92 in 1° steps, `rot_shoulder(ψ)` applied to `upper_arm_moving()` (both elbow slot ends) doesn't overlap wall A, wall B, the compact, the 80T envelope or the shoulder belt envelope. Report `shoulder_min_gap_mm`. It must be ≥ 2.0.
  - **Stops:**
    - a tab on hub flange B or plate B's lock ring touches a block on wall B at ψ = ±92, ±0.3
    - at ±90 they're ≥ 1.0 apart
    - the blocks span ≥ 30° of arc, as on the elbow
  - **Hall:** at ψ 0 the magnet faces the sensor across a 1.0–2.0 gap.
  - **Compact:** the compact housing, as posed, doesn't overlap wall A or the hub, and its output face touches the hub's A-end (`min_gap` ≤ 0.05).
  - **Height:** `SHOULDER_AXIS_Z` ≥ 32.5 + 3 + the turntable's top. Report it.
  - **Run.** Expected: fails on `NameError: wall_a`.
- [ ] **Step 2: Build the walls and the cage.**
  - Each wall is a plate standing on the turntable, with the 6810 boss at `SHOULDER_AXIS_Z`, lightened, and ≥ 6 of material round every seat and hole.
  - Keep each wall's top below the upper arm's swept envelope, which the sweep check enforces.
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE`, with `shoulder_min_gap_mm`, `rod_out_mm` and `SHOULDER_AXIS_Z` in the report.
- [ ] **Step 4: Commit** (ask first).

### Task 3: The 80T, and the shoulder motor plates (NEMA17, NEMA23)

**Files:**
- Modify: `tools/blender/htd3m_pulley.py`: add `("shoulder-pulley-80T", 80, 2.6, 2.1, 7.0, True, "shoulder")`, for the compact's Ø5 rod with its flat 2.1 off the axis, as the 60T
- Modify: `tools/blender/shoulder.py`, `shoulder_dims.py`
- Output: `model/shoulder/shoulder-pulley-80T.stl`, `shoulder-motor-plate-17.stl`, `shoulder-motor-plate-23.stl`

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - `SHOULDER_MOTOR_AT`: the motor's axis, at `SHOULDER_BELT_C` from the shoulder axis at slot-mid, in the shoulder belt plane. The direction is your call, below the axis and inside the turntable's footprint. Record it.
  - `MOTOR_SLOT = 3.0`, along the belt's centre line
  - `PLATE_MOUNT`: the swap plate's outer pattern on wall A's outside, or a bracket on the turntable
  - the push-screw tensioner: M3 into an insert, as on the spider base's slotted arm
- **Produces in `shoulder.py`:**
  - `motor_plate(kind) -> Object`, where `kind` is "17" or "23"
  - `shoulder_motor_box(kind, slot) -> Object`: 60 long for the 17 and 76 for the 23
  - `shoulder_belt_envelope(slot) -> Object`

- [ ] **Step 1: Write the failing checks** in `check_shoulder_drive()`:
  - **Plates:** both are one island, 0 non-manifold edges. Their outer patterns are identical: the same hole centres to 0.01.
  - **Fits:** the 17's M3 holes are on a 31 square and its pilot clears Ø22.4. The 23's M5 holes are on a 47.14 square and its pilot clears Ø38.5.
  - **Belt centres:** at slot −3, 0 and +3, the centre distance is `SHOULDER_BELT_C` + slot ± 0.1 (Review Focus 5).
  - **Clearances,** for each `kind` at both slot ends:
    - the motor box doesn't overlap the walls, the turntable, the hub or the upper arm's sweep
    - the belt envelope doesn't overlap wall A, the compact or the upper arm's sweep
    - the 80T's inside flange is ≥ 1.0 from the compact and its bolt heads
  - **Pulley:** `htd3m_pulley.py` reports 80 grooves for the 80T, and the other pulleys' report lines are unchanged. Diff them against a run before the edit.
  - **Run** both scripts. Expected: `shoulder.py` fails on `NameError: motor_plate`.
- [ ] **Step 2: Build** the plates and the tensioner.
- [ ] **Step 3: Run.** Expected: `PULLEY DONE` with `shoulder-pulley-80T` at 80 grooves, and `SHOULDER DONE`. `git status` shows no changes to the other pulleys' STLs; restore them if they were rewritten.
- [ ] **Step 4: Commit** (ask first).

### Task 4: The turntable, the fixed base, the 130T ring and the base stops

**Files:**
- Modify: `tools/blender/shoulder.py`, `shoulder_dims.py`
- Output: `model/shoulder/turntable.stl`, `base-ring-130T.stl` (if printed separately), `fixed-base.stl` (split if it won't fit the bed), `base-motor-plate.stl`

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - `SPIGOT`: a Ø50 −0.0/+0.1 spigot rising from the fixed base, with two 6810 inner rings on it spaced 40–60 apart (`BASE_6810_Z`), clamped by a printed nut or a screwed cap
  - `TURNTABLE_Z`: the turntable's top face, `-SHOULDER_AXIS_Z`
  - `RING_Z`: the 130T's teeth band, under the turntable. It's built with htd3m_pulley's profile: copy `PITCH`, `GROOVE_R`, `GROOVE_DEPTH` and `od_r` with a comment citing the file, because importing it runs the script.
  - `BASE_MOTOR_AT`: upside down on a slotted plate on the fixed base, at `BASE_BELT_C` at slot-mid, slot ±3 along the belt line, push-screw tensioner
  - `PHI_STOPS = (-172.0, 172.0)`: one block on the fixed base and one tab on the turntable
  - `BASE_HALL`: the sensor in the fixed base, the magnet in the turntable, facing at φ 0
  - `ELECTRONICS_AREA`: a flat 100 × 150 on the turntable, clear of the walls and the motor, with M3 insert pilots on a 10 mm grid, or four corner pilots plus a centre row. Your call; record it.
- **Produces in `shoulder.py`:** `turntable()`, `fixed_base()`, `base_motor_plate()`, `rot_base(phi) -> Matrix`.

- [ ] **Step 1: Write the failing checks** in `check_base()`:
  - **Parts:** each is one island, 0 non-manifold edges, and fits the bed.
  - **Fits:**
    - the spigot is r 25.0 +0.0/+0.1 across both 6810 widths
    - the turntable's seats are r 32.5 +0.0/+0.1, with lips on the outer rings only
    - the clamp bears on the inner rings only
  - **Ring:** a radial ray count at the teeth band's middle gives 130 grooves, and the OD is 2·`od_r(130)` ± 0.05.
  - **Belt centres:** at slot −3, 0 and +3, the centre distance is `BASE_BELT_C` + slot ± 0.1.
  - **Base motor:** the motor box (60 long, upside down) and its belt envelope don't overlap the fixed base, the leg sockets or the turntable at any φ, checked in 10° steps.
  - **Stops:** they touch at ±172 ± 0.3 and are ≥ 1.0 apart at ±170. The 340° travel means the tab must pass the block's back on the short way round: check there's no overlap at φ 0 and at ±90.
  - **Hall:** the gap is 1.0–2.0 at φ 0.
  - **Wall feet:** every insert pilot in `WALL_FOOT` lands in the turntable with ≥ 2.0 of wall.
  - **Electronics:** `ELECTRONICS_AREA` doesn't overlap the walls, the motor plate envelopes (17 and 23) or the shoulder belt at any ψ.
  - **Run.** Expected: fails on `NameError: turntable`.
- [ ] **Step 2: Build** the parts.
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE`.
- [ ] **Step 4: Commit** (ask first).

### Task 5: Leg sockets and feet

**Files:**
- Modify: `tools/blender/shoulder.py`, `shoulder_dims.py`
- Output: `model/shoulder/foot.stl` (PLA, ×4), `foot-pad.stl` (TPU, ×4)

**Interfaces:**
- **Produces in `shoulder_dims`:**
  - `LEG_DEG`: the down angle, 45–60. Pick it for the widest footprint that keeps every foot pad centre ≥ 20 below the fixed base's lowest point.
  - `LEG_PHI`: four directions at 45° + 90k, between the motor and the belt
  - `SOCKET`: r 4.6, 25 deep, with an M3 pinch screw into an insert
  - `LEGS`: (socket mouth, foot point) pairs, with the tube's full 250 length
  - `FOOT_PADS`: the pad centres on the bench plane
  - `CLAMP_TAB`: each foot has a flat tab of at least 30 × 30 × 6 for a bench clamp
- **The foot:** a sleeve of r 4.6, 20 deep, over the tube end. The pad face is level when the leg is at `LEG_DEG`, with a recess for a Ø30 × 4 TPU pad (`foot-pad`).

- [ ] **Step 1: Write the failing checks** in `check_legs()`:
  - **Sockets:** each is r 4.6 +0.0/+0.1 and 25 ± 0.1 deep, measured with a ray along the leg's axis. The wall is ≥ 2.0. The pinch insert lands in ≥ 2.0 of wall.
  - **Clearances:** no leg overlaps the base motor box (17), its belt envelope or the turntable at any φ.
  - **Feet:** the pad face is level to within 0.5°, and all four pad centres are on one plane (z equal ± 0.1).
  - **Footprint:** report `footprint_r_mm`, the smallest distance from the base axis to an edge of the pad polygon.
  - **Parts:** one island and 0 non-manifold edges each. `foot-pad` is a TPU part and stays simple.
  - **Run.** Expected: fails on `NameError`.
- [ ] **Step 2: Build** the sockets on the fixed base, then the foot and the pad.
- [ ] **Step 3: Run.** Expected: `SHOULDER DONE` with `footprint_r_mm`.
- [ ] **Step 4: Commit** (ask first).

### Task 6: Whole-arm layout: shoulder sweep, shoulder torque, tipping

**Files:**
- Modify: `tools/blender/head_concept.py`
- Output: `model/head-concept/shoulder/*.png`, `model/cybot-v2.blend` (`save_v2_only` now includes the shoulder and base)

**Interfaces:**
- **Consumes:** `model/shoulder/*.stl`, its `poses.json` and `shoulder_dims`.
- **`--shoulder` implies `--elbow`.**
  - The shoulder axis in world is `ELBOW_AT - (0, 0, E.UPPER_L)`.
  - The shoulder frame maps in by translation to that point.
  - The fixed base, legs and turntable are placed at φ 0.
  - New collections: `Shoulder and body`, `Base and legs`.

- [ ] **Step 1: Capture the baseline.** Run the five existing variants and save their HEAD lines to the scratchpad.
- [ ] **Step 2: Write the failing checks** in `shoulder_report(report)`, called from `check()` under `SHOULDER`:
  - **Sweep at home:** at ψ 0, for θ over `E.RANGE` in 2° steps and wrist pitch in (−90, 0, 90), the moving set (everything above the shoulder) doesn't overlap the walls, the compact, the 80T, the turntable, the legs or the shoulder motor (both plates). Assert it.
  - **Soft-limit table:** for ψ in 5° steps over `PSI_RANGE` and θ in 5° steps, list the (ψ, θ) pairs that collide with the body, the base, the legs or the bench plane. Report it as `shoulder_soft_limits`, a report only.
  - **Shoulder torque:**
    - the masses: the elbow layout's masses, plus the upper arm parts (the STLs' volumes at 1.24 g/cm³ and 40% infill, as `plate_mass_g`), plus the elbow motor at 350 g, the elbow compact at 120 g and the 500 g payload at the fingertip
    - report `shoulder_torque_worst_nm` over ψ, θ and the wrist pitch
  - **Elbow capacity from the bench:**
    - `ELBOW_DEMO_NM`: the torque about the elbow axis with the forearm level, the head at the user's 1346 g (spread like `ELBOW_MASSES`, but scaled to 1346 with the pancakes and T8 on) and 500 g at the wrist pitch axis, no hand
    - this lifted cleanly at 800 mA (2026-11-19)
    - `SHOULDER_CAPACITY_NM = ELBOW_DEMO_NM * 80 / 60`. Both motors are 48 mm NEMA17s. Take their holding torque as equal, and record that as a ruling, since the KL17H248's datasheet figure isn't confirmed.
    - report `shoulder_margin`
    - if it's under 1.2, report `"shoulder: bench test at higher current, NEMA23 plate ready"`. Don't assert it; the spec makes it the user's decision.
  - **Tipping:**
    - the whole arm's centre of mass, including the body, the base, the motors at 350 g each and the legs, at the worst reach (ψ ±90, θ and wrist set for the longest reach, 500 g on) for φ in 45° steps
    - report `tip_margin_mm`, the smallest distance from the projected centre of mass to the edge of the pad polygon
    - assert it's > 0, so the arm is stable unclamped
    - if it's under 15, the report says `"clamp the feet"`
  - **Run** `head_concept.py -- --shoulder`. Expected: fails on `NameError: shoulder_report`, or a missing STL.
- [ ] **Step 3: Place the parts and write `shoulder_report`.** Renders:
  - `shoulder-side` at ψ 0
  - `shoulder-forward` at +90
  - `shoulder-back` at −90
  - `shoulder-iso`
  - `shoulder-top`
- [ ] **Step 4: Run `--shoulder`.** Expected: a `HEAD {...}` line with:
  - `shoulder_torque_worst_nm`, `elbow_demo_nm`, `shoulder_capacity_nm`, `shoulder_margin`
  - `tip_margin_mm` (> 0)
  - `shoulder_soft_limits`
  
  then `HEAD DONE`. Rerun the five baseline variants and diff their HEAD lines. Restore their PNGs and blends.
  - If `shoulder_torque_worst_nm` × 1.5 > `SHOULDER_DESIGN_NMM` / 1000, raise `SHOULDER_DESIGN_NMM`, rerun Tasks 1–2's checks in `shoulder.py`, and record a ruling.
- [ ] **Step 5: Commit** (ask first): `head_concept.py`, `model/head-concept/shoulder/`. Don't commit the blend (`model/*.blend` is git-ignored).

### Task 7: Print sheets

**Files:**
- Create: `model/shoulder/PRINT.md`, `model/shoulder/print/*.3mf`, made by the method in `model/elbow/PRINT.md`: flattened system profiles in the scratchpad's `bambu/` folder, `--outputdir`, and bash for the word-split file list
- Modify: `model/elbow/PRINT.md`:
  - plate 3 and plate 6 lose `shoulder-hub` and `shoulder-hub-clamp`
  - plate 5 (the bench stand) is removed
  - re-export plates 3 and 6, and delete plate 5's 3mf
  - a line points to `model/shoulder/PRINT.md` for the shoulder

- [ ] **Step 1: Arrange the plates**, slicing each once for its time and grams, then export unsliced:
  - the walls
  - the hub parts and the jig
  - the turntable
  - the fixed base
  - the motor plates, the 80T and the reprinted 20Ts (two more `axis3-pulley-20T`), at 0.12
  - the feet (PLA)
  - the pads (TPU), on their own plate
- [ ] **Step 2: Write `PRINT.md`** in the elbow sheet's shape:
  - the plates table
  - **what isn't printed:** the second compact (`--m25-roll`, with its input rod at `rod_out_mm`), the two 17HS19-2004S1s, four 6810s, the 420 and 477 belts, and the four tubes
  - the hardware from `REPORT["bolts"]`
  - **the drilling step:** jig on the seat, Ø3.4 through, then the magnet pocket
  - **the assembly order:**
    1. the fixed base and legs
    2. the turntable on its 6810s, then the base belt and motor
    3. the walls and their 6810s
    4. drill the plates, then fit the hub halves through the plates, then bolt the hub into the walls' bearings
    5. the compact on wall A, then the 80T
    6. the shoulder motor plate and belt, then tension
    7. stops, Hall sensors, wires
- [ ] **Step 3: Commit** (ask first).
