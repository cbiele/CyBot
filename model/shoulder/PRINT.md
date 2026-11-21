# Shoulder, body and base: print and assembly sheet

For the P2S, 0.4 nozzle, Bambu PLA Basic (the pads in TPU). The STLs are exported in print orientation; don't let the slicer auto-orient them.
- **Spec:** `docs/superpowers/specs/2026-11-20-low-shoulder-flat-stand-design.md`
- **Generator:** `tools/blender/shoulder.py` (dimensions in `shoulder_dims.py`)
- **Whole-arm check:** `tools/blender/head_concept.py -- --shoulder`
- **The upper arm and elbow:** `model/elbow/PRINT.md`

## Plates

The project files in `print/` hold the plates below, arranged and set up. Open, check, slice.

| Plate | File | Parts | Layer | Supports | Sliced (est.) |
|---|---|---|---|---|---|
| 1 | `print/plate-1-wall-A-0.16-supports.3mf` | `body-wall-A` (with the shoulder motor's box), standing on its bottom face | 0.16 | tree, 2 mm brim | 17 h 28, 416 g |
| 2 | `print/plate-2-wall-B-collar-stub-0.16.3mf` | `body-wall-B`, `shoulder-stop-collar`, `shoulder-stub`, `shoulder-stub-spacer` | 0.16 | none | 5 h 46, 152 g |
| 3 | `print/plate-3-hub-B-jig-0.16-supports.3mf` | `shoulder-hub-b`, `plate-drill-jig` | 0.16 | tree | 5 h 57, 152 g |
| 4 | `print/plate-4-turntable-0.16.3mf` | `turntable` | 0.16 | none | 7 h 44, 235 g |
| 5 | `print/plate-5-fixed-base-0.16-supports-15pc.3mf` | `fixed-base` (the drum) | 0.16 | tree, 15% infill | 8 h 13, 296 g |
| 6 | `print/plate-6-shoulder-drive-0.12.3mf` | `shoulder-motor-plate-17`, `shoulder-motor-plate-23`, `shoulder-pulley-80T`, `shoulder-output-plate`, 2 × `elbow/axis3-pulley-20T` (one for each new motor) | 0.12 | none | 9 h 43, 133 g |
| 7 | `print/plate-7-base-drive-0.12.3mf` | `base-ring-130T`, `base-motor-plate`, `spigot-spacer`, `spigot-cap` | 0.12 | none | 8 h 52, 124 g |
| 8 | `print/plate-8-feet-0.16.3mf` | 4 × `foot` | 0.16 | none | 2 h 16, 62 g |
| 9 | `print/plate-9-pads-tpu-0.16.3mf` | 4 × `foot-pad`, in TPU (Generic TPU profile; swap in yours) | 0.16 | none | 0 h 49, 11 g |

All plates: 4 walls, 40% gyroid, Arachne walls, as on the elbow, except the drum at 15%. In all, about 67 h and 1.57 kg of PLA.

- **Three plates need supports:**
  - **Wall A:** it prints standing on its bottom face (its inward foot rules out face down), and the motor box's end and seat overhang. It fills most of the bed (245 × 78), so it's placed by hand with a 2 mm brim. Don't let arrange move it.
  - **Hub B:** the floor under the nose bridges its bore. The supports come out of the bore's open end.
  - **The drum:** a 1.8 mm shell open top and bottom, like V1's ring; the turntable covers it. Ribs run from the spigot's tube down to the wall's foot under each leg's socket, and the stop block and Hall post stand on brackets off the wall, all at 45°, so the only supports are under the base motor's shelf, which bridges over the motor's window. It's light now (296 g), so clamp the feet.
- **The stub prints flange down,** so its bearing land is a clean vertical wall.
- **Hub B prints journal end down,** with a 45° cone under its flange.
- **The motor plates print seat face down,** their pull-screw tabs up.
- **The NEMA23 plate** is printed now, because it's cheap. It stays in the drawer until the shoulder needs the 23.

## Not printed

- **The shoulder compact:** a fresh 20:1 compact from `cycloid_poc.py -- --m25-roll --stub-mount`. Only its housings differ from the elbow's (`model/cycloid-poc/20-1-compact-stub/`):
  - The rear one has 4 inserts on R21.5 for the stub.
  - Its R30 holes are blind: M3 × 5.7 inserts, sunk 7 deep from the split face, take 4 × M3 × 25 from the front face. That keeps the rear face flat: it runs 0.5 from plate A, which turns.
  - Its Ø5 input rod must stand **79.5 mm** out of the housing's rear face, through the stub and its 625 to the top of the 80T. The rod is pressed into the eccentric, so it goes in with the compact, before plate A.
- **Motors:** two 17HS19-2004S1 (48 mm), one for the shoulder and one for the base. The shoulder's plate takes a NEMA17, or the 23 plate a NEMA23 up to 76 mm. The 23 needs its own 20T, bored for its shaft (not made yet).
- **Bearings:**
  - four 6810-2RS: one in plate A's Ø65 shoulder seat, one in wall B, two on the base spigot
  - one 625-2RS in the stub's outer end, for the input rod
- **Belts:** a 3M-420-9 for the shoulder (20T/80T, centres 131.9 at slot middle) and a 3M-477-9 for the base (20T/130T, centres 113.9).
- **Legs:** the four 250 mm lengths of 9 × 7 aluminium tube, uncut.
- **Homing:** two TO-92 Hall sensors (A3144 type) and two Ø6 × 3 magnets.

## Shoulder current cap

**Set the shoulder driver's run current to 0.57 A.** The 17HS19 is rated 0.59 N·m at 2.0 A, so about 47 N·m through 80:1 before losses. That would break the output link and the stops, which are sized for 13.5 N·m. Holding torque scales roughly with current, so 2.0 × 13.5 / 47 ≈ 0.57 A. Confirm it at the bench: the shoulder should slip, not break, against a stop.

## Hardware

Heat-set inserts are M3, Ø4 pilot, 5 deep, unless a row says otherwise.

| Joint | Fasteners |
|---|---|
| Hub B to plate B | 6 × M3 × 12 from inside the plate gap, through the drilled plate holes into 6 inserts in hub B's flange |
| Hub B to the compact's output | the printed `shoulder-output-plate`'s 3 dogs into hub B's nose, plus 3 × M3 × 12 through the nose's counterbored floor (from wall B's side, down hub B's bore) into the carrier's inserts |
| The compact's halves | 4 × **M3 × 25** from the front face into M3 × 5.7 inserts in the rear half (not through-bolts: a nut or head on the rear face would rub plate A) |
| Stub to the compact's housing | 4 × **M3 × 16** down the stub's channels from its outer end, into the 4 inserts in the stub-mount housing's rear face |
| Stub to wall A | 4 × M3 × 10 through the stub's flange into 4 inserts in wall A's outer face |
| Walls to the turntable | 8 × M3 × 12 from under the turntable into inserts in each wall's bottom: 5 in wall A (3 in the wall, 2 in its inward foot, through slots in the turntable so wall A finds its own place on the stub), 3 in wall B |
| Stop collar to hub B | 2 × M3 × 8 into 2 inserts in hub B's journal end |
| Shoulder motor to its plate | 4 × M3 × 10 (NEMA17). The 23 takes M5 through its flange; check the length on the 23HS22. |
| Motor plate onto wall A's seat | 4 × M3 × 10 from outside, through the plate's slots, into 4 inserts in the seat |
| Shoulder belt pull screw | 1 × M3 × 20 through the box's end into an insert in the plate's tab |
| Base ring to the turntable hub | 4 × M3 × 20 into 4 inserts in the hub's underside |
| Spigot cap | 3 × M3 × 8 into 3 inserts in the spigot's top |
| Base motor plate to the shelf | 4 × M3 × 8 through the plate's slots into 4 inserts through the shelf |
| Base motor to its plate | 4 × M3 × 10 |
| Base belt push screw | 1 × M3 × 12 into the insert in the shelf's lug, its head towards the base axis |
| Leg pinch screws | 4 × M3 × 6 into the 4 inserts in the socket bosses, lightly: a leg should still pull out |
| 80T and the 20Ts | 1 × M3 × 3 × 4.5 insert each, pressed in radially, plus an M3 set screw (the 80T on the rod's flat, each 20T on its motor's flat) |

In all: 18 × M3 × 12, 4 × M3 × 25, 4 × M3 × 16, 16 × M3 × 10, 9 × M3 × 8, 5 × M3 × 20, 4 × M3 × 6, and 3 set screws.

Inserts:
- hub B: 8
- the compact's rear housing: 4 for the stub, plus 4 M3 × 5.7 for the clamp
- wall A: 13 (4 for the stub, 5 underneath, 4 in the motor's seat)
- wall B: 3
- each motor plate: 1, in the tab
- the turntable: 4
- the drum: 12 (the cap's 3, the shelf's 4, the push screw's 1 and the 4 pinch inserts)
- plus the three radial pulley inserts

The walls' inserts are checked for 13.5 N·m in the wall's plane plus the arm's weight off it: at most 382 N each, against an allowance of 400 (a third of a typical M3 insert's pull-out in PLA).

## Drilling plate B

The arm plates stay as printed. **Only plate B is drilled:** hub B is locked to it by six M3s through holes drilled with the jig. Plate A isn't drilled; it turns on the stub, on a 6810 in its Ø65 seat.

1. **Seat the jig on plate B's outer face,** its spigot in the Ø65 seat and its fences on the plate's straight sides.
   - It only goes on one way.
   - The key under the jig's round end sits just past the plate's round end.
   - Turned over, the key lands on the plate and the jig won't seat.
2. **Drill Ø3.4 right through** at each of the six guides, on R36.5, in the boss's upper half, towards the elbow. The pattern straddles plate B's index holes.

There's no magnet pocket to drill. The shoulder's magnet rides in the printed stop collar.

## Assembly

The order matters. **The upper arm is built round the compact:** plate B, hub B and the compact first, then plate A over the compact's rod, and the cross members glued last (the elbow sheet's step 6 waits for this). The compact's rod is pressed in, and it can't get into a closed arm.

1. **The drum and legs.**
   - Press the drum's inserts:
     - the cap's 3 in the spigot top
     - the shelf's 4
     - the push screw's 1 in the lug
     - the 4 pinch inserts
   - Push the four tubes 25 mm into the sockets and snug the pinch screws.
   - Glue a TPU pad into each foot's recess (it stands 2 mm proud), then push the feet about 20 mm onto the tube ends, clamp tabs outwards.
   - The drum's underside and the four pads all sit on the bench: five contacts.
   - **Clamp the feet to the bench by their tabs.** Unclamped, the arm tips at full reach (see below).
2. **The turntable and base drive.**
   - Press the 4 ring inserts into the turntable hub's underside.
   - With the turntable upside down, press the upper 6810 into the hub against its lip. Drop the spigot spacer onto that bearing's inner ring, then press in the lower 6810.
   - **Hang the 477 belt round the 130T ring before you fit the ring.** Once the stack is on the spigot, the belt can't get round it.
   - Screw the ring onto the hub's underside with the 4 M3 × 20s. Its lip traps the lower bearing's outer ring.
   - Lower that assembly over the spigot at home, the belt hanging under it. The stop tab under the turntable's rear sits over the drum's Hall post, half a turn from the stop block.
   - Screw the cap onto the spigot's top with the 3 M3 × 8s. That clamps both inner rings through the spacer. The turntable should spin freely.
   - At the bench, stand the base motor on its plate, shaft down through the pilot (4 × M3 × 10). Fit a 20T on the shaft, hub up, so its teeth line up with the ring's.
   - Set the plate on the shelf, the 20T hanging through the window, and loop the belt over the 20T.
   - Turn the push screw (M3 × 12, head towards the base axis) against the plate's inner edge to tension the belt, then tighten the plate's 4 M3 × 8s.
3. **Wall B.**
   - Press wall B's 3 bottom inserts and its 6810, from the inner face against the lip.
   - Bolt it to the turntable from underneath (3 × M3 × 12).
4. **The compact, hub B and the upper arm.**
   - Build the shoulder compact with its rod pressed in, and clamp its halves with the 4 M3 × 25s from the front face.
   - Drill plate B as above. Press hub B's 6 lock inserts and its 2 collar inserts.
   - Fit hub B from plate B's outer face, its spigot in the Ø65 seat against the lip, and lock it with the 6 M3 × 12s from inside the plate.
   - Lay plate B down, inner face up. Put the shoulder output plate on the compact's carrier, its dogs down, and set the compact on hub B's nose, dogs into the nose.
   - Fit the 3 M3 × 12s from underneath, up hub B's bore, through its floor into the carrier's inserts.
   - Lay the spacer on the compact's rear face, centred on the rod.
   - Press a 6810 into plate A's Ø65 seat from its outer face. Lower plate A over the rod, the rod through the 6810's bore, until the bearing's inner ring sits on the spacer.
   - Push the four cross members through both plates, dry. Square the plates and check the arm turns freely on hub B's journal by hand. **Glue the cross members now,** so the frame takes up the stack's tolerances rather than forcing them.
   - Fit the elbow's parts as on the elbow sheet.
5. **The arm, the stub and wall A.**
   - Slide hub B's journal into wall B's 6810, the arm straight up.
   - Press the 625 into the stub's outer end, and wall A's 9 inserts (4 for the stub, 5 underneath).
   - Bolt the stub to wall A through its flange (4 × M3 × 10).
   - Slide wall A in from the side, the rod through the stub and its 625, until the stub's land is through plate A's 6810 and its pilot sits in the housing's rear lip. Wall A's bottom screw holes in the turntable are slotted: leave its screws out for now.
   - **Drive the 4 M3 × 16s down the stub's channels into the housing's inserts first.** That clamps plate A's inner ring between the stub's shoulder and the spacer.
   - Then bolt wall A to the turntable from underneath (5 × M3 × 12 through the slots), where it has settled. The arm should swing freely.
6. **The shoulder motor and belt.**
   - Fit the 80T on the rod, hub towards the stub, 1 mm off the stub's end (use a 1 mm shim while you tighten its set screw).
   - Press the seat's 4 inserts into wall A's box and the tab's insert into the motor plate.
   - At the bench, bolt the motor to the plate's outer face (4 × M3 × 10), shaft through the pilot. Fit a 20T on the shaft, hub towards the motor, 9 mm below the plate's underside, so its teeth line up with the 80T's.
   - Drop the plate into wall A's box from outside, onto the seat, the 20T through the seat's window. Loop the 420 belt round the 80T and the 20T.
   - Fit the 4 M3 × 10s through the plate's slots into the seat, loose.
   - Pull the plate back with the M3 × 20 pull screw through the box's end (±3 of slot), then tighten the 4 screws.
7. **Stops and Hall sensors.**
   - **Shoulder:** push a magnet to the bottom of the stop collar's tab pocket. Slide the collar onto hub B's journal end outside wall B, tab down: its tongues only fit the journal's key slots that way round. Screw it down with the 2 M3 × 8s. Fit a Hall sensor flush in wall B's outer-face pocket.
   - **Base:** push the other magnet into the pocket in the turntable stop tab's foot. Fit the sensor on the drum's sensor post.
   - **Wires:** all in an external loom, sorted out later.

## Range, stops and load

- **Shoulder:**
  - ±91°, with home straight up. The stop collar's tab meets 30° blocks on wall B at ±93°.
  - The turntable's rim is what stops the arm: the axis is 46.5 above it, the lowest that keeps the stops past 92°. Each extra 5–10 mm of axis buys a few degrees: about ±96° at 51.5, ±99° at 56.5, ±105° at 66.5.
  - 80:1 (20T/80T into the 20:1 compact), so 711.11 steps/deg at 16 microsteps.
- **Base:**
  - ±170°, with home at 0. The tab under the turntable meets the block on the drum at ±172°.
  - 6.5:1 (20T/130T), so 57.78 steps/deg at 16 microsteps.
- **Hall:** at home each magnet passes its sensor with a 1.2 mm gap.
- **Height:** the shoulder axis is 219.5 above the bench.
- **Bench reach:** the tool on the wrist touches the bench 157 mm from the base axis, at shoulder 17°, elbow 148°, wrist pitch 30°.
- **Soft limits:**
  - At wrist pitch 0, the arm meets the body, the base, the legs or the bench at 196 (shoulder, elbow) pairs, in 5° steps, over the base turned to every 45°. That's against 182 at base 0 alone: the legs and the base motor add the rest.
  - With the upper arm straight up, the hand meets the body at elbow 132–150° with the wrist pitched 90°.
  - The full tables are in `head_concept.py -- --shoulder`'s report.
- **Shoulder load:**
  - The worst static load is 12.0 N·m: the arm level backwards, elbow 20°, with 500 g at the wrist.
  - The estimate for the 17HS19 is 4.8 N·m: the elbow's bench result scaled by 80:1 over 60:1.
  - **2376 of the 3885 poses checked need more than that.** Bench-test it before trusting it. The NEMA23 plate is the fallback.
  - Under the current cap above, the most it can apply is 13.5 N·m, which the hub lock, link and stops are sized for.
- **Stability:**
  - The pads sit on a square whose edges are 224 mm from the base axis.
  - At full reach, base turned 90°, with 500 g at the wrist, the arm's centre of mass (4.6 kg, with the drum now a light shell) falls 66 mm past that edge.
  - **Clamp the feet.**
