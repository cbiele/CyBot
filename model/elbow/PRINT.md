# Elbow and upper arm: print and assembly sheet

For the P2S, 0.4 nozzle, Bambu PLA Basic. The STLs are exported in print orientation; don't let the slicer auto-orient them.
- **Spec:** `docs/superpowers/specs/2026-11-17-elbow-upper-arm-design.md`
- **Generator:** `tools/blender/elbow.py`
- **Layout and range check:** `tools/blender/head_concept.py -- --elbow`
- **Shoulder:** the shoulder (plate A turns on a fixed stub; hub B locks to plate B), drilling plate B for it, and the body that replaced the bench stand are on `model/shoulder/PRINT.md`.

## Plates

The project files in `print/` hold the plates below, arranged and set up. Open, check, slice.

| Plate | File | Parts | Layer | Supports | Sliced (est.) |
|---|---|---|---|---|---|
| 1 | `print/plate-1-upper-plate-A-0.16.3mf` | `upper-plate-A`, at 45° | 0.16 | none | 3 h 20, 95 g |
| 2 | `print/plate-2-upper-plate-B-0.16.3mf` | `upper-plate-B`, at 45° | 0.16 | none | 2 h 27, 74 g |
| 3 | `print/plate-3-hubs-collar-0.16-supports.3mf` | `elbow-hub`, `elbow-stop-collar`, `elbow-key-wedge`, `elbow-collar-lower`, `elbow-collar-upper` | 0.16 | tree (auto), build plate only | 6 h 02, 120 g |
| 4 | `print/plate-4-pulleys-idler-0.12.3mf` | `axis3-pulley-20T`, `axis3-pulley-60T`, `belt-idler`, `forearm-tube/ax4-output-plate` (the elbow compact's, same part) | 0.12 | none | 3 h 04, 36 g |
| 6 | `print/plate-6-reprint-stop-collar-wedge-0.16-supports.3mf` | `elbow-stop-collar`, `elbow-key-wedge` | 0.16 | tree (auto), build plate only | 0 h 44, 16 g |

All plates: 4 walls, 40% gyroid, Arachne walls, as on the wrist. There's no plate 5: the bench stand was dropped for the shoulder and body.

**Plate 6** is for a build whose plate 3 was printed before 2026-11-18. Its stop collar had a tongue that reached only 0.3 mm into the hub's key slot, and that plate had no wedge. You can keep a hub printed then: drill the rear tube's socket through with a Ø9 drill, guided by the socket. Its 2 mm floor is the only thing in the way.

- **The plates are 296 mm long.** They only fit the 256 bed on the diagonal, so they're placed at 45°. Don't let arrange rotate them back.
- **Plates 1 and 2 print inner face down.**
  - The shoulder 6810 seats open upwards from a lip on the bed.
  - Plate B's elbow seat opens on the bed side, and its lip is a 4 mm ring printed over it. It prints without support.
- **Plate 3:**
  - The elbow hub prints journal end down. Its disc and lug overhang that journal, so they need supports.
  - **Keep supports out of the holes.** Paint them off:
    - the tube sockets in the hub and the lower collar (the hub's rear socket runs right through its lug)
    - the hub's Ø36 wire bore and its dog holes

## Not printed

- **The elbow compact:** a fourth 20:1 compact, built like axis 5's, with the short eccentric and the lip between the disk bearings. Its Ø5 input rod must stand at least 31 mm out of the rear face (8.5 plate, 1 gap, 21.5 pulley).
- **Motor:** a 17HS8401B (48 mm). Plate B has a window, so a NEMA17 up to 60 mm long drops in without reprinting.
- **Bearings:** one 6810-2RS, in plate B at the elbow. The shoulder's are on the shoulder sheet: one goes in plate A's Ø65 shoulder seat, one in wall B.
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
| 20T and 60T | 1 × M3 × 3 × 4.5 heat-set insert each, pressed in radially, plus an M3 set screw (the 20T on the motor's flat, the 60T on the rod's flat) |
| Stop collar to hub | 2 × M3 × 8 into 2 × M3 heat-set inserts in the hub's journal end face; its tongue keys into the journal's slot, and the printed `elbow-key-wedge` keys it through the wire windows |
| Hall | a TO-92 Hall sensor (A3144 type) flush in plate B's outer-face pocket (leads out radially), plus a Ø6 × 3 magnet pushed to the bottom of the stop collar's tab pocket (1.2 mm gap at home) |

The idler's stack is 30.5 mm plus the nut, so it takes an M3 × 40. Its tail stands about 7 mm into the space between the plates, where nothing runs.

## Assembly

Plate B slides on along the elbow axis onto both journals at once, so the order matters.

1. **Collar on the forearm.** Fit the two halves round the outer tube's Ø36 section, with their keys over axis 4's four bolt heads. Clamp them with the M3 × 20s. Nothing on the forearm comes apart.
2. **Plate A.**
   - Bolt the compact's rear face to plate A's inner face with the M3 × 50s and nuts.
   - Mount the motor on the inner face, its shaft through the slot.
   - Fit the 60T on the rod and the 20T on the shaft, hubs towards the plate. Set the 60T 1 mm off plate A's outer face (a 1 mm shim while you tighten its set screw), clear of the compact's bolt heads.
   - Fit the idler on its boss.
3. **Hub and bracket.**
   - Put the printed output plate on the compact's carrier, then the hub over its dogs.
   - Fit the M3 × 12s through the hub's bore into the carrier's inserts.
   - Glue the front and middle tubes into the hub's and the collar's sockets (epoxy or CA, 15 deep), with the forearm held in place.
   - Feed the rear (78.1) tube in from outside the hub, through its lug's open socket, and 15 into the collar. It ends flush with the lug's outer face. It's 45° off the other two, so it can't go in with them. Glue both ends.
4. **Plate B.**
   - Press the elbow 6810 into plate B from the inner face, against the lip.
   - Leave the plates' Ø65 shoulder seats empty for now: plate A's takes a 6810 and plate B's takes hub B (shoulder sheet).
   - Slide plate B along the elbow axis onto the hub's journal, until the 6810's inner ring sits on the hub's land.
5. **Stop collar.**
   - Slide it onto the journal end outside plate B, its tongue in the journal's slot.
   - Screw it down with the two M3 × 8s. That clamps the 6810's inner ring against the hub.
   - Push the wedge in from outside through the collar's and the journal's wire windows, its curved faces matching theirs. Fix it with a drop of CA. The wires leave through the open Ø36 bore at the journal's end, not the window.
6. **Cross members.** Push the four tubes through both plates and glue them, with the plates square and parallel. **Not yet if the shoulder's going on:** the shoulder's compact goes between the plates first, so leave the tubes dry until the shoulder sheet's step 4.
7. **Belt.** Fit the belt, tension it by sliding the motor along its slots, then set the idler.
8. **Hall.** Fit the Hall sensor.
9. **Shoulder.** Drill plate B's lock holes (plate A isn't drilled) and fit the shoulder, as on `model/shoulder/PRINT.md`.

## Range, stops and load

- **Range:** −20° (back past vertical) to +150°, with home straight up. The stop collar's tab meets 30° blocks on plate B at −22.4° and +152.4°. The blocks are sized to take a motor stall across their layers.
- **Hall:** at home the magnet passes over the sensor with a 1.2 mm gap.
- **Load:** worst static load 5.16 N·m, with the forearm 20° below level, the hand on and a 200 g tool. The estimate for the 48 mm NEMA17 at 60:1 is 7.0 N·m, so 1.36×. Bench-test it before trusting it.
