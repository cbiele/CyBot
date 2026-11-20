# Shoulder, body and base: print and assembly sheet

For the P2S, 0.4 nozzle, Bambu PLA Basic (the pads in TPU). The STLs are exported in print orientation; don't let the slicer auto-orient them.
- **Spec:** `docs/superpowers/specs/2026-11-19-shoulder-base-design.md`
- **Generator:** `tools/blender/shoulder.py` (dimensions in `shoulder_dims.py`)
- **Whole-arm check:** `tools/blender/head_concept.py -- --shoulder`
- **The upper arm and elbow:** `model/elbow/PRINT.md`

## Plates

The project files in `print/` hold the plates below, arranged and set up. Open, check, slice.

| Plate | File | Parts | Layer | Supports | Sliced (est.) |
|---|---|---|---|---|---|
| 1 | `print/plate-1-wall-A-cage-0.16.3mf` | `body-wall-A`, `compact-cage` | 0.16 | none | 4 h 22, 129 g |
| 2 | `print/plate-2-wall-B-collar-0.16.3mf` | `body-wall-B`, `shoulder-stop-collar` | 0.16 | none | 3 h 32, 108 g |
| 3 | `print/plate-3-hubs-jig-0.16.3mf` | `shoulder-hub-a`, `shoulder-hub-b`, `plate-drill-jig` | 0.16 | none | 7 h 43, 205 g |
| 4 | `print/plate-4-turntable-0.16.3mf` | `turntable` | 0.16 | none | 13 h 25, 388 g |
| 5 | `print/plate-5-fixed-base-0.16.3mf` | `fixed-base` | 0.16 | none | 10 h 28, 294 g |
| 6 | `print/plate-6-shoulder-drive-0.12.3mf` | `shoulder-motor-bracket`, `shoulder-motor-plate-17`, `shoulder-motor-plate-23`, `shoulder-pulley-80T`, `shoulder-output-plate`, 2 × `elbow/axis3-pulley-20T` (one for each new motor) | 0.12 | none | 13 h 11, 187 g |
| 7 | `print/plate-7-base-drive-0.12.3mf` | `base-ring-130T`, `base-motor-plate`, `spigot-spacer`, `spigot-cap` | 0.12 | none | 8 h 56, 124 g |
| 8 | `print/plate-8-feet-0.16.3mf` | 4 × `foot` | 0.16 | none | 2 h 26, 68 g |
| 9 | `print/plate-9-pads-tpu-0.16.3mf` | 4 × `foot-pad`, in TPU (Generic TPU profile; swap in yours) | 0.16 | none | 0 h 49, 11 g |

All plates: 4 walls, 40% gyroid, Arachne walls, as on the elbow. In all, about 64 h and 1.5 kg of PLA.

- **Nothing needs supports.** Every overhang is 45° or less, apart from short bridges over holes and windows.
  - The hub halves print end down, with a 45° cone under each flange.
  - The leg sockets in the fixed base run at 45°.
  - The foot's Ø30 pad recess is a 2 mm bridge. It can sag a little, and the pad is glued over it anyway.
- **The turntable (248 × 215) and the fixed base (192 × 248)** each fill most of the bed. Don't let arrange push them off.
- **The walls print inner face down,** so their feet turn outwards. Each 6810 seat opens on the bed side, with its lip printed over it.
- **The NEMA23 plate** is printed now, because it's cheap. It stays in the drawer until the shoulder needs the 23.

## Not printed

- **The shoulder compact:** a second 20:1 compact built from `cycloid_poc.py -- --m25-roll`, as the elbow's. Its Ø5 input rod must stand at least 25.5 mm out of the rear face, through the 80T.
- **Motors:** two 17HS19-2004S1 (48 mm), one for the shoulder and one for the base. The shoulder's swap plate takes a NEMA17 up to 60 mm long, or the 23 plate a NEMA23 up to 76 mm. The 23 needs its own 20T, bored for its shaft (not made yet).
- **Bearings:** four 6810-2RS: one in each body wall, two on the base spigot.
- **Belts:** a 3M-420-9 for the shoulder (20T/80T, centres 131.9 at slot middle) and a 3M-477-9 for the base (20T/130T, centres 113.9).
- **Legs:** the four 250 mm lengths of 9 × 7 aluminium tube, uncut.
- **Homing:** two TO-92 Hall sensors (A3144 type) and two Ø6 × 3 magnets.

## Hardware

Heat-set inserts are M3, Ø4 pilot, 5 deep, unless a row says otherwise.

| Joint | Fasteners |
|---|---|
| Hub halves to the arm plates | 12 × M3 × 12 (6 per plate) from inside the plate gap, through the drilled plate holes into 12 inserts in the hub flanges |
| Hub A to the compact's output | the printed `shoulder-output-plate`'s 3 dogs into hub A's end, plus 3 × M3 × 12 through hub A's counterbored floor into the carrier's inserts |
| Compact cage to wall A | 4 × M3 × 12 into 4 inserts in wall A's outer face |
| Compact to the cage | 4 × **M3 × 45** through the housing on R30 into 4 inserts in the cage |
| Wall feet to the turntable | 8 × M3 × 12 (4 per wall) into inserts in the turntable |
| Stop collar to hub B | 2 × M3 × 8 into 2 inserts in hub B's journal end |
| Motor bracket foot to the turntable | 3 × M3 × 12 into inserts in the turntable |
| Shoulder motor to its swap plate | 4 × M3 × 10 (NEMA17). The 23 takes M5 through its flange; check the length on the 23HS22. |
| Swap plate to the bracket | 4 × M3 × 12 through the bracket's slots into 4 inserts in the swap plate |
| Shoulder belt push screw | 1 × M3 × 20 into an insert in the bracket's lug |
| Base ring to the turntable hub | 4 × M3 × 20 into 4 inserts in the hub's underside |
| Spigot cap | 3 × M3 × 8 into 3 inserts in the spigot's top |
| Base motor plate to the fixed base | 4 × M3 × 10 through the plate's slots into 4 inserts |
| Base motor to its plate | 4 × M3 × 10 |
| Base belt push screw | 1 × M3 × 16 into an insert in the fixed base's lug |
| Leg pinch screws | 4 × M3 × 6 into the 4 inserts in the socket bosses, lightly: a leg should still pull out |
| 80T and the 20Ts | 1 × M3 × 3 × 4.5 insert each, pressed in radially, plus an M3 set screw (the 80T on the rod's flat, each 20T on its motor's flat) |
| Electronics area (optional) | 7 inserts on the turntable, between the walls: four corners of the 150 × 100 area plus a row of three down its middle |

In all: 34 × M3 × 12, 4 × M3 × 45, 5 × M3 × 20, 5 × M3 × 8, 12 × M3 × 10, 1 × M3 × 16, 4 × M3 × 6, and 3 set screws. The turntable takes 22 inserts (7 of them for the electronics), the fixed base 12, the hub halves 14, the cage 4, wall A 4, the swap plate 4 and the bracket 1, plus the three radial pulley inserts.

## Drilling the arm plates

The arm plates stay as printed. Each hub half is locked to its plate by six M3s through holes drilled with the jig.

1. **Leave the plates' Ø65 shoulder seats empty.** No 6810 goes in them now: the hub halves go there.
2. **Seat the jig on plate A's outer face**, its spigot in the Ø65 seat and its fences on the plate's straight sides. It only goes on one way round.
3. **Drill Ø3.4 right through** at each of the six guides, on R36.5, in the boss's upper half, towards the elbow.
4. **Turn the jig half round about the vertical axis for plate B,** then do the same. The pattern straddles plate B's index holes.

There's no magnet pocket to drill. The shoulder's magnet rides in the printed stop collar.

## Assembly

1. **Fixed base and legs.**
   - Press the inserts into the fixed base: the cap's 3 in the spigot top, the motor plate's 4, the push screw's 1 and the 4 pinch inserts.
   - Push the four tubes 25 mm into the sockets and snug the pinch screws.
   - Glue a TPU pad into each foot's recess (it stands 2 mm proud), then push the feet about 20 mm onto the tube ends, clamp tabs outwards.
   - **Clamp the feet to the bench by their tabs.** Unclamped, the arm tips over at full reach (see Range below).
2. **Turntable and base drive.**
   - Press the turntable's inserts, including the 4 for the ring in its hub's underside.
   - Press the upper 6810 into the turntable's hub from below, up against its lip. Drop the spigot spacer in under it, then press in the lower 6810.
   - Screw the 130T ring onto the hub's underside with the 4 M3 × 20s. Its lip traps the lower bearing's outer ring.
   - Lower that assembly over the spigot at home. The stop tab under the turntable's rear sits over the fixed base's Hall post, half a turn from the stop block. The lower bearing's inner ring lands on the spigot's shoulder.
   - Screw the cap onto the spigot's top with the 3 M3 × 8s. That clamps both inner rings through the spacer. The turntable should spin freely.
   - Hang the base motor under the motor plate with the 4 M3 × 10s, its shaft up through the plate. Fit a 20T on the shaft at the ring's height.
   - Put the plate on the fixed base's arm over its 4 inserts, the motor through the window. Loop the 477 belt round the ring and the 20T.
   - Tension it with the M3 × 16 push screw against the plate's edge, then tighten the plate's 4 M3 × 10s.
3. **The walls and their 6810s.**
   - Press a 6810 into each wall from its inner face, against the lip on the outer side.
   - Press wall A's 4 cage inserts, and the turntable's wall-foot inserts if not done.
   - Bolt wall B's feet to the turntable (4 × M3 × 12). Leave wall A loose for now.
4. **The hub and the arm.**
   - Drill the arm plates as above.
   - Press the 6 lock inserts into each hub flange, and the 2 collar inserts into hub B's journal end.
   - Fit hub A from plate A's outer face, its spigot in the Ø65 seat against the lip and its flange flat on the plate. Lock it with the 6 M3 × 12s from inside the plate gap. Do the same for hub B on plate B.
   - Slide hub B's journal into wall B's 6810, the arm straight up.
   - Slide wall A onto hub A's journal, then bolt its feet to the turntable (4 × M3 × 12).
5. **The compact and the 80T.**
   - Screw the compact cage to wall A's outer face (4 × M3 × 12).
   - Put the shoulder output plate on the compact's carrier, its dogs outwards.
   - Offer the compact up to the cage, the output plate's dogs into hub A's end. Bolt the housing to the cage's inserts with the 4 M3 × 45s.
   - From between the arm plates, reach through hub A's bore and fit the 3 M3 × 12s through its floor into the carrier's inserts.
   - Fit the 80T on the input rod, hub towards the compact, 1 mm clear of the compact's bolt heads (a 1 mm shim while you tighten its set screw).
6. **The shoulder motor and belt.**
   - Bolt the motor bracket's foot to the turntable (3 × M3 × 12).
   - Press the swap plate's 4 inserts. Bolt the motor to the plate's far side (4 × M3 × 10), shaft through the pilot.
   - Bolt the plate to the bracket through its slots (4 × M3 × 12, loose). Fit the 20T on the shaft, its hub 1 mm off the bracket's face, in line with the 80T.
   - Fit the 420 belt. Tension it with the M3 × 20 push screw on the plate's chamfered corner (±3 of slot), then tighten the 4 screws.
7. **Stops, Hall sensors and wires.**
   - **Shoulder:** push a magnet to the bottom of the stop collar's tab pocket. Slide the collar onto hub B's journal end outside wall B, its tongues in the journal's key slots. Screw it down with the 2 M3 × 8s. Fit a Hall sensor flush in wall B's outer-face pocket.
   - **Base:** push the other magnet into the pocket in the turntable stop tab's foot. Fit the sensor on the fixed base's sensor post.
   - **Wires:** the arm's wires come down through hub B's open bore and out past wall B's 6810. The driver boards go on the turntable's electronics area, between the walls.

## Range, stops and load

- **Shoulder:** ±90°, with home straight up. The stop collar's tab meets 30° blocks on wall B at ±92°. 80:1 (20T/80T into the 20:1 compact), so 711.11 steps/deg at 16 microsteps.
- **Base:** ±170°, with home at 0. The tab under the turntable meets the block on the fixed base at ±172°. 6.5:1 (20T/130T), so 57.78 steps/deg at 16 microsteps.
- **Hall:** at home each magnet passes its sensor with a 1.2 mm gap.
- **Shoulder load:**
  - The worst static load is 12.0 N·m: the arm level, elbow nearly straight, with 500 g at the wrist.
  - The estimate for the 17HS19 is 4.8 N·m. That's the elbow's bench result scaled by 80:1 over 60:1, so 0.40×.
  - The model flags 61 poses beyond it, all at shoulder angles of 50° and more or at −90°.
  - Bench-test it before trusting it, at higher current if needed. The NEMA23 plate is the fallback.
- **Hub:** the hub lock and dogs are sized for 13.5 N·m, which covers what the 17HS19 can apply through 80:1.
- **Stability:**
  - The pads sit on a square whose edges are 183 mm from the base axis.
  - At full reach, base turned 90°, with 500 g at the wrist, the arm's centre of mass (4.7 kg) is 281 mm out, so 98 mm past that edge.
  - **Clamp the feet.**
