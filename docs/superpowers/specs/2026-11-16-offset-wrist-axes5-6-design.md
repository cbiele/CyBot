# Offset wrist: axes 5 and 6 on the forearm tube

Date: 2026-11-16. Status: approved by the user, 2026-11-16.

## Intent

The forearm (axis 4, see the forearm tube spec) is built and spins clean down to 400 mA. It ends in a Ø30 wrist flange on the rotating aluminium tube. This design puts axes 5 (pitch) and 6 (roll) on that flange and carries the three-finger hand.

The arm is for light work: holding a soldering iron, a small camera or a paint brush, on a horizontal surface (tool pointing down) or a vertical one (tool pointing forward), from many forearm angles. The user's priority is articulation over power. The torque test (red compact plus pancake at 40:1 held about 1.2 N·m) showed there is little power to spare, so the wrist is built for range and low weight.

## Goals

- Axis 5 pitch range of about ±170°, limited only by cables, so the tool can face down or forward from most arm poses.
- Axis 6 rolls without limit; no wires cross it.
- The three-finger hand mounts on axis 6's output, driven through axis 6's bore by the gripper motor's lead screw.
- As light as practical: every gram here loads axis 4, the elbow and the shoulder.
- The head's weight is carried into the fixed outer tube by a support bearing, not only through the wrist hub.

## Non-goals

- The hand itself and its palm interface. This design ends at axis 6's output face and the T8 screw end; the hand side is the hand's design.
- The detachable tool adapter on the end of the lead screw (a later swap for the hand).
- Wire routing. Wires run outside, with a loose loop across axis 5, as on the forearm.
- Changes to the forearm parts already printed (outer tube, drive tube), apart from adding the support bearing to the outer tube's outside. The wrist hub is replaced by the head bracket (see "Decided by the user").
- The elbow, which resumes after this.

## Anti-goals

- An inline fork wrist. It was considered (layout A) and rejected: the gripper motor's tail swings into the fork, so it needs a long, wide fork for about ±110°.
- A wrist sized for a 500 g payload held out level. It would need bigger motors and add weight the elbow can't carry.

## Constraints

- **Wrist flange** (`tools/blender/forearm_dims.py`): Ø30 hub on the 9 × 11 drive tube, face at forearm x 241.6, four M3 heat-set inserts on R11 at 45° + 90k. It rotates with axis 4.
- **Outer tube** (fixed, printed, already built): Ø25 (OUTER_R 12.5), ends at forearm x 221.6. The front 6701 sits in it at x 217.6–221.6. The wrist hub (Ø30) spans x 222.1–241.6.
- **Support bearing:** 6705-2RS (25 × 32 × 4), six in hand. Its bore fits the outer tube's Ø25.
- **Axis 5 gearbox:** a 20:1 compact (`cycloid_poc.py`, no flags): housing Ø68 × 38.6, four M3 holes on R30, output carrier with three M3 × 3 × 4.5 inserts on R6.5 at 90°, 210°, 330°. The red unit is the reference (clean at 200 mA unloaded).
- **Axis 6 gearbox:** the hollow T8 compact (`cycloid_poc.py --hollow-t8`): ran clean both ways at 600 mA after the carrier trim. Output inserts on R8.5. Its 188 motor mount has M3 nut pockets (a1e29dc). The T8 screw runs right through; it is held by the motor's coupler and a 608 in the hand and comes out forward.
- **Motors:** pancakes at 40:1 on 188 GT2 belts (20T/40T, centres 63.68), as on axis 4. The 188 mount `20-1-hollow/motor-mount.stl` fits the plain compact.
- **Measured torque:** pancake at 40:1 on a compact, about 1.2 N·m at 1000 mA (torque test, 2026-11-15). Use this, not datasheet figures.
- **Printers:** Bambu A1 or P2S, bed 225 × 255. Printed press fits and bearing seats as in the print-fits notes. The user fit-tests printed parts on real hardware.

## Decided by the user

- Layout B, the offset wrist (UR-style): the axis 5 compact sits across the end of the forearm, and its output carries axis 6 and the hand off to one side, so they swing past the forearm instead of into it. Chosen mostly to save weight.
- Payload: light tools of about 100–200 g. Articulation over power.
- Keep the three-finger hand and design the wrist around it. A detachable adapter on the screw end that swaps the hand for a tool mount comes later.
- A support bearing on the forearm's outer tube carrying a shell around the head, so the weight doesn't all hang off the wrist hub. In from the start.
- Axis 6 is the hollow T8, with the gripper motor fixed behind it.
- **Axis 5 at 60:1 (2026-11-16, after the layout check):** the layout put the hand's centre about 149 mm and the tool about 229 mm past the pitch axis, not the 90 and 150 estimated below, so axis 5 needed 1.07 N·m at 40:1. Axis 5 now runs a 20T/60T GT2 on a 234 belt (60:1, about 1.75 N·m by the measured figure). The fallback, if that fails, is moving axis 6 back about 25 mm so the module counterweights the hand (about 0.76 N·m at 40:1).
- **Axis 5 pancake in line with the forearm (2026-11-16, after seeing the renders):** the pancake points straight back along the forearm instead of hanging back and down. It rolls with axis 4 around the fixed outer tube, so it can't sit across the tube. Its body faces outboard (+y), on a separate motor plate on the far side of the belt.
- **The wrist hub merges into the head bracket (2026-11-16, the user's idea):** one printed part is glued onto the drive tube's front end, with the old hub's Ø11 socket, 6701 land and 0.3 shim. It carries the 6705 skirt and axis 5's housing. This drops the flange screws and the 8 mm plate, so the pitch axis comes about 9 mm closer (the tube's end, fixed by its glue depth, sits where the axis 5 housing comes nearest). It also solves fitting the 6705: the old hub comes off, the 6705 goes onto the outer tube, then the new part is glued on. The gearbox's own case is unchanged.
- **Axis 4 at 60:1 too (2026-11-16):** with the wrist pitched about 90° and the hand rolled out sideways, axis 4 needs about 1.28 N·m, over the 1.17 measured at 40:1. It now runs the same 20T/60T on a 234 as axis 5 (about 1.75 N·m, 1.37× at that worst pose), on `ax4-motor-mount-60T`, the 188 mount with its arm lengthened. The compact, tube and glued parts are unchanged.
- No wired parts on the hand for now: the T8 drives all the fingers. The hand spec's thumb motor and sensors (28BYJ-48, FSRs, ADS1115) come later, and how their wires cross axis 6 is decided then. Until then axis 6 has no hard stop and no slip ring.

## My calls (the user has not reviewed these)

- **Load:** about 0.7 N·m on axis 5 at full pitch, against the measured 1.2 (about 1.7×). The figure has a 400 g hand (the user's number) with its centre about 90 mm past the pitch axis, a 200 g tool held in the hand at about 150 mm, and the axis 6 module (T8 compact, its pancake, gripper motor, L-bracket, about 0.5 kg) with its centre within about 10 mm of the pitch axis. The module only stays that cheap if it straddles the pitch axis, with the gripper motor's tail behind the pitch axis as a counterweight. The offset layout lets it do that: the module swings in its own plane, clear of the forearm and axis 5. So **the axis 6 module's centre of mass sits on or near the pitch axis**, and the layout check reports the axis 5 torque at full pitch. If it comes out above about 0.8 N·m, stop and bring it to the user rather than changing motors. Roll load on axis 4 from the about 60 mm offset is about 0.6 N·m. Both stay on pancakes.
- **Axis 5 placement:** the compact's axis is across the forearm, centred on it, with the pitch axis about 40 mm past the wrist flange face. *(Superseded: about 30 mm past the old flange face, now the front of the glued socket.)*
- **Support:** the user's "outer shell holding axis 5's motor et al." is read as the structural head bracket, which may be shell-shaped for stiffness, not a separate cosmetic cover. The head bracket bolts to the wrist flange's four inserts *(superseded: it is glued onto the drive tube in the wrist hub's place)* and has a skirt reaching back over the wrist hub. The skirt holds the 6705's outer ring; the 6705's inner ring sits on the outer tube's front end, just behind x 221.6. The bracket also carries the axis 5 housing on its R30 holes.
- **Axis 5 motor:** under the forearm end, back and down at about 45°, on the 188 belt. Folded straight back along the forearm it would hit the tube. *(Superseded by the user's in-line decision above.)*
- **Axis 6 mounting:** an L-bracket bolts to axis 5's output (M3 × 5 into the three inserts, with dogs as on the forearm's output plate). It holds axis 6's housing with its axis parallel to the forearm at home, offset about 60 mm along the pitch axis, so the whole axis 6 module, gripper motor included, clears the forearm and axis 5 at any pitch.
- **Axis 6 motor:** pancake beside its housing on the 188, on the side that keeps the offset smallest.
- **Gripper motor:** inline behind axis 6 on `motor7-bracket`, driving the T8 through the 5 to 8 coupler, as in the head concept's T8-through version.
- **Home:** axis 5 with the hand straight out along the forearm; axis 6 at a mark. Homing by Hall sensor and magnet, like the elbow. Sensor mounting is the builder's.
- **Hand interface:** axis 6's output face (three M3 inserts on R8.5) is the hand's mounting point. If that pattern is too small for the hand's lever, a bolt-on output plate with dogs, like the forearm's, spreads it.
- **Order:** generate the printable parts first, then lay them out in the head concept model (`head_concept.py`, with the tube forearm), so the layout shows real parts and can be checked for clashes through ±170° of pitch. Nothing is printed until the user has seen the layout.

## Left to the builder

- Exact bracket shapes, wall thicknesses and how the skirt meets the bracket.
- How the 6705's inner ring is held on the outer tube (slip fit plus CA glue, or a printed collar) and its exact position.
- Avoiding a fight between the two load paths (the flange bolts and the 6705), for example by clearance in the flange bolt holes.
- The exact pitch-axis distance and offset, from the clash checks.
- Belt tensioning for both 188s.
- Hard stops on axis 5 just past ±170°, if needed to protect the cable loop.
- Checks in the generator script, following the existing scripts' style (non-manifold, bore diameters, clearances, clash checks through the pitch range).
