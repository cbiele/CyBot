# Shoulder, body and base: print and assembly sheet

For the P2S, 0.4 nozzle, Bambu PLA Basic (the pads in TPU). The STLs are exported in print orientation; don't let the slicer auto-orient them.
- **Spec:** `docs/superpowers/specs/2026-11-21-arm-mounted-shoulder-v1-base-design.md`
- **Generator:** `tools/blender/shoulder.py` (dimensions in `shoulder_dims.py`)
- **Whole-arm check:** `tools/blender/head_concept.py -- --shoulder`
- **The upper arm and elbow:** `model/elbow/PRINT.md`. Both upper plates are reprinted for this shoulder: plate B carries the shoulder compact and motor, and plate A the shoulder's stop blocks and Hall sensor.

## How it fits together

- **The shoulder is the elbow joint, mirrored.**
  - The shoulder compact's rear face bolts to plate B's inner face, and the NEMA17 sits on plate B above the elbow motor. Both turn with the arm.
  - The 20T/80T belt runs outside plate B, opposite the elbow belt.
  - The compact's output dogs into a **fixed hub**. Plate A turns on that hub's 6810.
  - A keyed **lug** on the hub's outer end clamps that 6810. It carries the stop tab and the magnet, and holds three aluminium tubes. The tubes run to a **socket bracket** bolted on the turntable: two horizontal ones either side of the axis take the torque, and a diagonal takes the weight. The bracket's two towers are bored through and widen towards their feet, which keeps their bending under 10 MPa.
  - A **post** outside the belt carries a 625 on the end of the compact's input rod.
- **The base is V1's.**
  - The turntable, the 130T ring under it and a cylinder hanging from the ring turn on two 6810s in the drum's hub tube.
  - The base motor hangs shaft-up under the drum's shelf, beside a flat in the drum's wall. It's turned 45° on its shaft, so a driver can reach all four of its screws past the belt.

## Plates

The project files in `print/` hold the plates below, arranged and set up. Open, check, slice.

| Plate | File | Parts | Layer | Supports | Sliced (est.) |
|---|---|---|---|---|---|
| 1 | `print/plate-1-turntable-0.16.3mf` | `turntable`, top face down | 0.16 | none | 5 h 10, 148 g |
| 2 | `print/plate-2-fixed-base-0.16-supports-15pc.3mf` | `fixed-base` (the drum) | 0.16 | tree, 15% infill | 7 h 56, 269 g |
| 3 | `print/plate-3-ring-and-cylinder-0.12.3mf` | `base-ring-130T` (the ring and the cylinder, one part) | 0.12 | none | 16 h 27, 216 g |
| 4 | `print/plate-4-shoulder-and-base-parts-0.16.3mf` | `shoulder-hub`, `shoulder-lug`, `shoulder-socket-bracket`, `shoulder-rod-post`, `shoulder-output-plate`, `base-spacer`, `base-retainer`, `base-motor-plate` | 0.16 | none | 6 h 55, 204 g |
| 5 | `print/plate-5-pulleys-0.12.3mf` | `shoulder-pulley-80T`, 2 × `elbow/axis3-pulley-20T` (shoulder and base) | 0.12 | none | 4 h 25, 53 g |
| 6 | `print/plate-6-feet-0.16.3mf` | 4 × `foot` | 0.16 | none | 2 h 16, 62 g |
| 7 | `print/plate-7-pads-tpu-0.16.3mf` | 4 × `foot-pad`, in TPU (Generic TPU profile; swap in yours) | 0.16 | none | 0 h 49, 11 g |

The two upper plates are on the elbow sheet (plates 1 and 2 there: 6 h 45, 191 g).

All plates: 4 walls, 40% gyroid, Arachne walls, as on the elbow, except the drum at 15%. In all, about 44 h and 960 g here, plus the upper plates.

- **The drum** is the only plate with supports. It's a 1.8 mm shell open top and bottom, like V1's ring. Ribs run from the hub tube to the wall's foot under each leg's socket, and the stop block and Hall post stand on 45° brackets off the wall. The shelf's walls run down to the bench at 45°.
- **The ring and cylinder** print as one part, turntable face down, at 0.12 for the teeth.
- **The lug prints spider face down.** Its tab's far side is cut at 45°, so it needs no support.
- **The hub prints face down,** its floor on the bed. The bore opens above the floor at 45°.
- **The post prints lying on its outer face.** The 625's seat opens on the bed side, and the lip is a 1.0 mm ring printed over it.

## Not printed

- **The shoulder compact:** a fresh 20:1 compact from `cycloid_poc.py -- --m25-roll`, the same as the elbow's. Its Ø5 input rod must stand **43.5 mm** out of the housing's rear face: through plate B and the 80T, into the post's 625. The rod is pressed into the eccentric, so it goes in with the compact.
- **Motors:** two 17HS19-2004S1 (48 mm), one for the shoulder and one for the base.
- **Bearings:**
  - three 6810-2RS: one in plate A's Ø65 shoulder seat, two in the drum's hub tube
  - one 625-2RS in the post
- **Belts:**
  - a 3M-420-9 for the shoulder (20T/80T, centres 131.9 at slot middle)
  - a 3M-477-9 for the base (20T/130T, centres 113.9)
- **Tubes (9 × 7 aluminium):**
  - three for the shoulder's bracket: 2 × **50.7** (front and rear), 1 × **54.6** (diagonal), out of one 250 mm length
  - the four 250 mm legs, uncut
- **Homing:** two TO-92 Hall sensors (A3144 type) and two Ø6 × 3 magnets.

## Shoulder current cap

**Set the shoulder driver's run current to 0.57 A.** The 17HS19 is rated 0.59 N·m at 2.0 A, about 47 N·m through 80:1 before losses. That would break the output link, the lug and the stops, which are sized for 13.5 N·m. Holding torque scales roughly with current, so 2.0 × 13.5 / 47 ≈ 0.57 A. Confirm it at the bench: the shoulder should slip, not break, against a stop.

## Hardware

Heat-set inserts are M3, Ø4 pilot, 5 deep, unless a row says otherwise.

| Joint | Fasteners |
|---|---|
| Shoulder compact to plate B | 4 × **M3 × 50** through plate B and the housing, with plain M3 nuts on the housing's front face, as on the elbow |
| Shoulder motor to plate B | 4 × M3 × 12 in plate B's slots, from its outer face, the motor turned 45° |
| Hub to the compact's output | the printed `shoulder-output-plate`'s 3 dogs into the hub's face, plus 3 × M3 × 12 through the hub's counterbored floor (down its bore) into the carrier's inserts |
| Lug to the hub | 2 × M3 × 10 through the lug's counterbores into 2 inserts in the hub's journal end |
| Socket bracket and post to the turntable | 6 × M3 × 8 down through their feet into 6 inserts in the turntable's top (4 for the bracket, 2 for the post) |
| Ring to the turntable | 4 × M3 × 20 up through the ring's counterbores into 4 inserts in the turntable's underside |
| Retainer to the cylinder | 3 × M3 × 8 up into 3 inserts in the cylinder's end |
| Base motor | 4 × **M3 × 14** down through the clamp plate and the shelf's slots into the motor |
| Leg pinch screws | 4 × M3 × 6 into the 4 inserts in the socket bosses, lightly: a leg should still pull out |
| 80T and the 20Ts | 1 × M3 × 3 × 4.5 insert each, pressed in radially, plus an M3 set screw (the 80T on the rod's flat, each 20T on its motor's flat) |

In all: 4 × M3 × 50 with nuts, 7 × M3 × 12, 2 × M3 × 10, 9 × M3 × 8, 4 × M3 × 20, 4 × M3 × 14, 4 × M3 × 6, and 3 set screws.

Inserts:
- the hub: 2
- the turntable: 10 (4 underneath, 6 on top)
- the cylinder's end: 3
- the drum: 4 pinch inserts
- plus the three radial pulley inserts

## Assembly

The upper arm is built round both compacts, as the elbow sheet says. **Plate B slides on along the axes onto both journals at once,** and the cross members are glued last.

The base goes together in this order, and `shoulder.py` checks it (`BASE_ORDER`): each part slides home past the ones already in. The spacer, the lower 6810, the retainer and the motor all come up from under the drum, so the legs go on after them and the feet are clamped last.

1. **The turntable and base bearing.** The drum on its own, no legs yet.
   - Press the turntable's 10 inserts and the cylinder's 3.
   - Screw the ring and cylinder onto the turntable's underside with the 4 M3 × 20s, up through the ring's counterbores.
   - **Hang the 477 belt round the ring now.** Once the cylinder is in the drum, the belt can't get round it.
   - Press the upper 6810 into the drum's hub tube from the top, down onto the lip.
   - Lower the turntable's cylinder down through it at home: the stop tab under the turntable sits over the drum's Hall post, half a turn from the stop block. The cylinder's shoulder lands on the upper inner ring.
   - Lift the drum onto blocks, or tip it on its side, holding the turntable on. Slide the spacer up the cylinder from below, onto the upper inner ring. **The spacer goes in before the lower 6810:** it's wider than a 6810's bore.
   - Press the lower 6810 up onto the cylinder's end and into its seat, onto the lip. Its inner ring meets the spacer.
   - Screw the retainer onto the cylinder's end with the 3 M3 × 8s. That clamps both inner rings through the spacer. The turntable should spin freely.
2. **The base motor.** The drum still up on its blocks: the motor's shaft goes up through the shelf from below, and on the bench there's only 8.5 mm under the motor.
   - From under the shelf, offer the motor up against the shelf's underside, turned 45° so its screws line up with the shelf's slots: one inboard, one outboard and one each side. Its shaft goes up through the shelf's window.
   - Lay the clamp plate on the shelf and fit the 4 M3 × 14s down through it into the motor, loose.
   - Fit a 20T on the shaft, hub down towards the plate and 1 mm off it, so its teeth line up with the ring's. Loop the belt over it.
   - Push the motor out along the slots to tension the belt by hand, then tighten the 4 screws.
3. **The legs and feet.**
   - Press the drum's 4 pinch inserts.
   - Push the four tubes 25 mm into the sockets and snug the pinch screws. The turntable's ear covers the 45° and 135° legs' screws at home, so turn the turntable until its ear is opposite the leg you're tightening.
   - Glue a TPU pad into each foot's recess (it stands 2 mm proud), then push the feet about 20 mm onto the tube ends, clamp tabs outwards.
   - Stand the drum on the bench. Its underside and the four pads all sit on the bench: five contacts. That's true in the CAD; tube lengths and print tolerances decide it on the bench. If the drum rocks or a pad hangs, loosen that leg's pinch screw, slide the tube a little in or out until all five touch, and snug it again.
   - **Clamp the feet to the bench by their tabs,** before the arm goes on. Unclamped, the arm tips at full reach (see below).
4. **The arm** (with the elbow sheet).
   - Build the shoulder compact with its rod pressed in.
   - Bolt it to plate B's inner face at the shoulder end with the 4 M3 × 50s and nuts, the rod out through plate B.
   - Put the shoulder output plate on the compact's carrier, dogs out, then the hub over its dogs. Fit the 3 M3 × 12s down the hub's bore into the carrier's inserts.
   - Bolt the shoulder motor to plate B's inner face with its 4 M3 × 12s in the slots, its shaft out through plate B. It's **turned 45° on its shaft**, so its screws line up with the slots: one towards the shoulder, one away from it, one each side.
   - Press a 6810 into plate A's Ø65 shoulder seat from its outer face, against the lip.
   - With plate A built as on the elbow sheet, slide plate B along the axes onto both journals at once: the elbow hub into plate B's 6810, and the shoulder hub through plate A's 6810.
   - Push the four cross members through both plates, dry. Square the plates and check the elbow turns freely by hand. **Glue the cross members now.**
5. **The lug.**
   - Press the 2 inserts into the hub's journal end.
   - Push a magnet to the bottom of the lug tab's pocket.
   - Slide the lug onto the journal end outside plate A, tab down: its tongues only fit the hub's key slots that way round. Screw it on with the 2 M3 × 10s. That clamps plate A's 6810's inner ring against the hub's shoulder.
   - Fit a Hall sensor flush in plate A's outer-face pocket, under the tab.
6. **The arm onto the base.**
   - Fit the 80T on the rod, hub towards plate B, 1 mm off it (use a 1 mm shim while you tighten its set screw).
   - Fit a 20T on the shoulder motor's shaft, hub towards plate B, so its teeth line up with the 80T's. Loop the 420 belt round both.
   - Tension the belt by sliding the motor along plate B's slots, then tighten its 4 screws from outside plate B. The one towards the shoulder sits between the belt's spans and the side ones outside them, so a driver reaches all four with the belt on.
   - Press the 625 into the post's seat from its outer face, and slide the post onto the rod's end, its 625 over the rod.
   - Set the arm on the turntable, straight up, on an 8 mm block under each plate's round lower end (they stand 8.5 above it), the post's foot on its pair of inserts. Bolt the post down with its 2 M3 × 8s, from above.
   - Slide the socket bracket in along the shoulder axis from outside, its towers either side of the lug, onto the turntable's ear. Bolt it down with its 4 M3 × 8s, from above.
   - Turn the lug until its sockets line up with the towers' bores. The towers are bored through, so each tube goes in from outside: coat its ends with epoxy and push it in through its tower until it bottoms in the lug's socket, 15 deep. The two 50.7s go in level, one from each side, and the 54.6 diagonal goes up through the front tower's upper bore. Push the last few mm with a rod under Ø9: each tube's outer end stops 15 inside its tower, short of the outer face. `shoulder.py` checks that each tube slides in with the others already in.
   - Pull the blocks once the epoxy has set.
7. **Base Hall.** Push the other magnet into the pocket in the foot of the turntable's stop tab. Fit the sensor on the drum's sensor post.
   - **Wires:** all in an external loom, sorted out later.

## Range, stops and load

- **Shoulder:**
  - ±91°, with home straight up. The lug's tab meets 30° blocks on plate A's outer face at ±93°.
  - The turntable's rim is what stops the arm: the axis is 46.5 above it, the lowest that keeps the stops past 92°.
  - 80:1 (20T/80T into the 20:1 compact), so 711.11 steps/deg at 16 microsteps.
- **Base:**
  - ±170°, with home at 0. The tab under the turntable meets the block on the drum at ±172°.
  - 6.5:1 (20T/130T), so 57.78 steps/deg at 16 microsteps.
- **Hall:** at home each magnet passes its sensor with a 1.2–1.3 mm gap.
- **Height:** the shoulder axis is 156.5 above the bench (it was 219.5 on the riser).
- **Bench reach:** the tool on the wrist touches the bench 161 mm from the base axis at base 0 (shoulder 5°, elbow 142°, wrist pitch 50°), and 219 mm at the worst base angle (60°).
- **Soft limits:**
  - At wrist pitch 0, the arm meets the body, the base, the legs or the bench at 270 (shoulder, elbow) pairs, in 5° steps, over every 15° of base angle. That's against 243 at base 0 alone.
  - With the upper arm straight up, the hand meets the body at elbow 132–150° with the wrist pitched 90°.
  - The full tables are in `head_concept.py -- --shoulder`'s report.
- **Shoulder load:**
  - The worst static load is 12.5 N·m: the arm level backwards, elbow 20°, with 500 g at the wrist. The shoulder motor now rides on the arm, so it adds to the load.
  - The estimate for the 17HS19 is 4.8 N·m: the elbow's bench result scaled by 80:1 over 60:1.
  - **2449 of the 3885 poses checked need more than that.** Bench-test it before trusting it.
  - Under the current cap above, the most it can apply is 13.5 N·m, which the link, the lug and the stops are sized for.
  - The input rod's side load from the belt is about 70 N at the 625 and 50 N at the compact.
- **Stability:**
  - The pads sit on a square whose edges are 224 mm from the base axis.
  - At full reach, base turned 270°, with 500 g at the wrist, the arm's centre of mass (4.3 kg) falls 79 mm past that edge.
  - **Clamp the feet.**
