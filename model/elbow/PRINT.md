# Elbow and upper arm: print and assembly sheet

For the P2S, 0.4 nozzle, Bambu PLA Basic. The STLs are exported in print orientation; don't let the slicer auto-orient them.
- **Spec:** `docs/superpowers/specs/2026-11-17-elbow-upper-arm-design.md`
- **Generator:** `tools/blender/elbow.py`
- **Layout and range check:** `tools/blender/head_concept.py -- --elbow`

## Plates

The project files in `print/` hold the plates below, arranged and set up. Open, check, slice.

| Plate | File | Parts | Layer | Supports | Sliced (est.) |
|---|---|---|---|---|---|
| 1 | `print/plate-1-upper-plate-A-0.16.3mf` | `upper-plate-A`, at 45° | 0.16 | none | 3 h 20, 95 g |
| 2 | `print/plate-2-upper-plate-B-0.16.3mf` | `upper-plate-B`, at 45° | 0.16 | none | 2 h 28, 73 g |
| 3 | `print/plate-3-hubs-collar-0.16-supports.3mf` | `elbow-hub`, `elbow-collar-lower`, `elbow-collar-upper`, `shoulder-hub`, `shoulder-hub-clamp` | 0.16 | tree (auto), build plate only | 7 h 40, 203 g |
| 4 | `print/plate-4-pulleys-idler-0.12.3mf` | `axis3-pulley-20T`, `axis3-pulley-60T`, `belt-idler`, `forearm-tube/ax4-output-plate` (the elbow compact's, same part) | 0.12 | none | 3 h 04, 36 g |
| 5 | `print/plate-5-bench-stand-0.16-supports.3mf` | `bench-stand` | 0.16 | tree (auto), build plate only | 6 h 38, 185 g |

All plates: 4 walls, 40% gyroid, Arachne walls, as on the wrist.

- **The plates are 296 mm long.** They only fit the 256 bed on the diagonal, so they're placed at 45°. Don't let arrange rotate them back.
- **Plates 1 and 2 print inner face down.**
  - The shoulder 6810 seats open upwards from a lip on the bed.
  - Plate B's elbow seat opens on the bed side, and its lip is a 4 mm ring printed over it. It prints without support.
- **Plate 3:**
  - The elbow hub prints journal end down. Its disc and lug overhang that journal, so they need supports.
  - **Keep supports out of the holes.** Paint them off:
    - the tube sockets in the hub and the lower collar
    - the hub's Ø36 wire bore and its dog holes
    - the shoulder hub's bore and its inserts
- **Plate 5:** the stand's Ø44 wire holes and its bolt holes run sideways through the cheeks, so let supports in there.

## Not printed

- **The elbow compact:** a fourth 20:1 compact, built like axis 5's, with the short eccentric and the lip between the disk bearings. Its Ø5 input rod must stand at least 31 mm out of the rear face (8.5 plate, 1 gap, 21.5 pulley).
- **Motor:** a 17HS8401B (48 mm). Plate B has a window, so a NEMA17 up to 60 mm long drops in without reprinting.
- **Bearings:** three 6810-2RS, two at the shoulder and one in plate B at the elbow.
- **Belt:** a 420-3M-9.
- **Aluminium tube, 9 × 7:** see the cut list.

## Tube cut list

Total tube needed is about 530 mm, so three 250 mm lengths.

| Use | Length | Qty |
|---|---|---|
| Bracket, front | 93.1 | 1 |
| Bracket, rear | 78.1 | 1 |
| Bracket, middle | 49.9 | 1 |
| Cross members (through both plates, flush) | 77.0 | 4 |

Suggested cuts (allow about 1 mm per cut):
- **First length:** 93.1 + 77 + 77
- **Second length:** 78.1 + 77 + 77
- **Third length:** 49.9

## Hardware

| Joint | Fasteners |
|---|---|
| Elbow compact to plate A | 4 × **M3 × 50**, through plate A and the housing, with plain M3 nuts on the housing's front face (grip 47.1 + nut) |
| Motor to plate A | 4 × M3 × 12 in the slots |
| Hub to the compact's output | the printed `ax4-output-plate`'s 3 dogs into the hub, plus 3 × M3 × 12 through the hub's counterbored floor, 3.3 into the carrier's inserts as on the wrist |
| Collar halves | 2 × M3 × 20, plus nuts in the lower half's side slots |
| Idler | 1 × **M3 × 40** as the axle, head on the roller, nut on plate A's inner face; the roller turns on it |
| Shoulder clamp pinch | 1 × M3 × 20, plus a nut |
| Hub end flanges (shoulder hub and clamp) | 8 × M3 heat-set inserts (Ø4 pilot, 5 deep), for the stand now and the body later |
| Stand to hub ends | 8 × M3 × 12 |
| Stand index pin | an M4 × 40 bolt or a Ø4 rod, through the stand's cheek into plate B's index hole |
| 20T and 60T | 1 × M3 × 3 × 4.5 heat-set insert each, pressed in radially, plus an M3 set screw (the 20T on the motor's flat, the 60T on the rod's flat) |
| Hall | a TO-92 Hall sensor (A3144 type) in plate B's pocket, plus a Ø6 × 3 magnet in the hub's tab |

The idler's stack is 30.5 mm plus the nut, so it takes an M3 × 40. Its tail stands about 7 mm into the space between the plates, where nothing runs.

## Assembly

1. **Collar on the forearm.** Fit the two halves round the outer tube's Ø36 section, with their keys over axis 4's four bolt heads. Clamp them with the M3 × 20s. Nothing on the forearm comes apart.
2. **Glue the bracket tubes.** Set the hub in place on the compact's output plate first, so the tubes go in at the right angle. Then glue the three tubes into the collar's and hub's sockets with epoxy or CA. Each socket is 15 deep.
3. **Plate A.**
   - Bolt the compact's rear face to plate A's inner face with the M3 × 50s and nuts.
   - Mount the motor on the inner face, its shaft through the slot.
   - Fit the 60T on the rod and the 20T on the shaft, hubs towards the plate.
   - Fit the idler on its boss.
4. **Shoulder.**
   - Press a 6810 into each plate's shoulder seat from the outer face, against the lip.
   - Slide the shoulder hub through from plate A's side, its shoulder on plate A's inner ring.
   - Push the clamp onto the hub's other end against plate B's inner ring, then tighten the pinch screw.
5. **Elbow.**
   - Press the elbow 6810 into plate B from the inner face.
   - Bring plate B up so the hub's journal enters it and the stop tab sits outside.
   - Bolt the hub to the output with the M3 × 12s through its bore.
6. **Cross members.** Push the four tubes through both plates and glue them, with the plates square and parallel.
7. **Belt.** Fit the belt, tension it by sliding the motor along its slots, then set the idler.
8. **Hall and stand.**
   - Fit the Hall sensor and the magnet.
   - Bolt the stand's cheeks to both hub ends, then pin the arm at home, 45° or 90°.
   - Clamp the stand to the bench.

## Range, stops and load

- **Range:** −20° (back past vertical) to +150°, with home straight up. The tab meets the stops at −22.5° and +152.5°.
- **Hall:** at home the magnet faces the sensor across 1.5 mm.
- **Load:** worst static load 5.16 N·m, with the forearm 20° below level, the hand on and a 200 g tool. The estimate for the 48 mm NEMA17 at 60:1 is 7.0 N·m, so 1.36×. Bench-test it before trusting it.
- **On the stand:** with the upper arm vertical, the hand reaches the stand's base past 140° of elbow when pitched down.
