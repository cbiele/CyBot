# Offset wrist: print and assembly sheet

For the P2S, 0.4 nozzle, Bambu PLA Basic. The STLs are exported already in print orientation (flat face down); don't let the slicer auto-orient them.
Spec: `docs/superpowers/specs/2026-11-16-offset-wrist-axes5-6-design.md`.

## Plates

The project files in `print/` hold the plates below, arranged, with the settings shown. Open, check, slice.

| Plate | File | Parts | Layer | Supports | Sliced (est.) |
|---|---|---|---|---|---|
| A | `print/plate-A-brackets-0.12.3mf` | `head-bracket`, `ax5-motor-plate`, `forearm-tube/ax4-output-plate` (axis 5's output plate, same as axis 4's) | 0.12 | none | 5 h 17, 74 g |
| B | `print/plate-B-l-bracket-0.16-supports.3mf` | `ax6-l-bracket` | 0.16 | tree (auto), build plate only | 3 h 24, 77 g |
| C | `print/plate-C-60T-drives-0.12.3mf` | `pulley-60T` × 2 (axes 4 and 5), `forearm-tube/ax4-motor-mount-60T` | 0.12 | none | 3 h 45, 50 g |

All plates: 4 walls, 40% gyroid, Arachne walls. Those are my calls; everything else is Bambu's stock profile.

- **0.12 on A and C:** the head bracket holds the 6705's outer ring and the Ø11 glued socket. 0.12 with Arachne is what the proven fits used (`tube-end-sleeve`, the eccentric lobes). The 60Ts' teeth also print better fine.
- **B needs supports:** the base disc is on the bed, so the axis 6 mount's motor arm (its lower edge about 14 mm up, about 90 mm long) and the mount disc's lower rim (4 mm up) overhang. The far bar's flat underside bridges the 45 mm between the discs without support.
  - **Keep supports out of the holes.** Before slicing, paint them off the nut pockets, the three dog holes and the gripper motor's pilot.
- **The head bracket's small bridges print unsupported:** the shim window, the counterbore floors and the insert holes.

## Not printed

- **Axis 5's compact:** the one you have built, with the short eccentric and the lip between the disk bearings. Its 188 motor mount and 40T aren't used.
- **Axis 6:** the built hollow T8. Its 188 `motor-mount` and the `motor7-bracket` are replaced by `ax6-l-bracket`.
- **The old `wrist-flange-hub`:** it comes off the drive tube. The head bracket takes its place.

## Hardware

Your M3 stock goes up to 50. Each long through-bolt ends in a hex nut pressed into a pocket; the short screws go into heat-set inserts. The generator checks that each long bolt passes right through its nut by 2 mm or less (`wrist.py`, `check_bolts`).

| Joint | Fasteners |
|---|---|
| Axis 5 housing to head bracket | 4 × **M3 × 45**, 4 × M3 nut in the bracket's belt-face pockets (grip 44.6) |
| Axis 6 housing to L-bracket | 4 × **M3 × 40**, 4 × M3 nut in the mount's pockets inside the frame (grip 38.6) |
| L-bracket and output plate to axis 5's carrier | 3 × M3 × 12 into the carrier's inserts; the plate's 3 dogs into the bracket |
| Motor plate to head bracket arm | 4 × M3 × 20, 4 × M3 heat-set insert in the arm (Ø4 pilot, 5 deep) |
| Axis 5 pancake to motor plate | 4 × M3 × 10 (6 mm plate, about 4 mm into the motor) |
| Axis 6 pancake to L-bracket arm | 4 × M3 × 10 |
| Gripper motor to L-bracket disc | 4 × M3 × 8 (5 mm disc); M3 × 10 if the motor's threads are 5 deep or more |
| 60T on the compact's Ø5 rod (each) | 1 × M3 × 3 × 4.5 heat-set insert, pressed in radially, and 1 M3 set screw on the rod's flat |
| Axis 4 pancake to `ax4-motor-mount-60T` | the screws from the 188 mount it replaces |

Bought parts:
- **6705-2RS:** one, on the outer tube.
- **GT2-6 234 belts:** two, one each for axes 4 and 5.
- **20T pulleys:** axes 4 and 5 keep their 20Ts.
- **Glue-up:** the 0.3 U-shaped shim from the old hub's glue-up, and CA glue.

## Assembly

**Axis 4, now 60:1:**
1. Take off the axis 4 pancake, its 188 mount and the 40T.
2. Fit the printed 60T on the compact's rod.
3. Bolt `ax4-motor-mount-60T` on in the old mount's place.
4. Fit the 234 belt, then slide the pancake along the slots to tension it.

**Head bracket (from the inline-motor plan's notes):**
1. Free the old wrist hub with heat, or soak it in acetone, then clean the tube end.
2. Slide the 6705's inner ring onto the outer tube's Ø25 end. It's a slip fit; don't glue it yet.
3. Seat the 6705's outer ring in the bracket.
4. Slide the bracket onto the drive tube with the U-shaped 0.3 shim against the 6701's inner ring. CA the socket, then wick CA into the 6705's inner ring. Once it has set, pull the shim out downwards through the slot in the bracket's wall just in front of the 6705.
5. Press the 4 M3 nuts into the bracket's belt-face pockets.
6. Pre-fit the 60T on axis 5's input, then bolt axis 5's housing on with the M3 × 45s.
7. Put the belt over the 60T and into the channel.
8. Bolt the pancake to the motor plate with its 20T already fixed. Push the 20T into the belt loop, then screw the plate onto the arm's inserts. To tension the belt, slide the whole plate along its four slotted holes; the screw heads are on the outside.

**L-bracket. The order matters, because the frame hides the base disc's screws once things are in it:**
1. Put the output plate on axis 5's carrier, then the empty L-bracket over its dogs. Drive the 3 M3 × 12s from the far side, through the open frame. Two of them sit behind the far bar, so they need a 2.5 ball-end hex key tilted about 3°.
2. Press the 4 M3 nuts into the mount's pockets from inside the frame.
3. Fit the gripper motor on the rear disc with an L-key from the side, its coupler on.
4. Bolt axis 6's housing on with the M3 × 40s.
5. Fit axis 6's pancake, its 20T and the 188.
6. Fit the T8 and the coupler.
