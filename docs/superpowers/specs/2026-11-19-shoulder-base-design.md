# Shoulder (axis 2), body and turning base (axis 1)

Date: 2026-11-19. Status: draft with the user's answers folded in, awaiting their read.

## Intent

The V2 elbow, forearm and offset wrist are built, and the elbow passed its bench test on 2026-11-19. It lifted the whole head (about 1346 g) plus a 500 g water jug at the wrist, 30° at 800 mA, and returned to its mark. This design adds what's left to make V2 a whole arm: the shoulder drive, a body that holds it, and a new turning base on removable tube legs.

V1's biggest mistake was carrying its heavy NEMA23 out on the arm. Here every motor below the elbow stays off the moving arm: the shoulder motor rides on the turntable, and the base motor sits on the fixed base. Motor weight then costs almost nothing, so the shoulder can step up to a NEMA23 later without penalty.

## Goals

- **Axis 2 (shoulder)** pitches the upper arm through 180°, from level forward to level back.
- **Axis 1 (base)** turns the whole arm through ±170° (340° total) between end stops.
- **Stability:** the arm stands on its own on the bench and doesn't tip or sway at full reach with the 500 g test load. The user favours stability over compactness.
- **Packing up:** the four legs pull out so the arm can be moved.
- **Motor swaps:** the shoulder motor can go from a large NEMA17 to a NEMA23 by swapping one mount plate.
- **Cycloid swaps:** the shoulder's compact can be taken off and replaced, for later backlash work, without taking the arm apart.

## Non-goals

- **The electronics.** The user plans to drive the arm from their own CardSort driver PCBs (one TMC driver per NEMA17), tied together by an ESP32, instead of the Octopus. That's a separate design. This one only leaves room for it (see Constraints).
- **Backlash reduction.** It's mostly in the cycloids, and it's a later effort.
- **Encoders.** Homing is by Hall sensor, as on the elbow.
- **A counterbalance spring.**
- **A slip ring or continuous base rotation.**

## Anti-goals

- **No motor on the moving upper arm** other than the elbow's own.
- **No cycloid in the base.** The user's call: V1's direct belt turns about 20 lb with power to spare.
- **No wires through the base's centre.** The user's call: they can run outside, with a service loop.

## Constraints

- **Upper arm (built, printed):** `tools/blender/elbow_dims.py`, `elbow.py`; spec `2026-11-17-elbow-upper-arm-design.md`.
  - Two side plates, 60 mm apart (inner faces), 8.5 thick, 220 mm from the shoulder axis to the elbow axis.
  - Each plate has a 6810 seat at the shoulder (Ø65, lip on the inner face).
  - **The plates are printed. Don't reprint them.** Drilling or adding screw holes to them is fine.
- **The shoulder hub and its clamp are not printed** (plate 6 in `model/elbow/PRINT.md`), so they can be redesigned freely. The same goes for the bench stand, which the user has dropped.
- **Elbow belt envelope:** the elbow motor sits about 71 mm from the shoulder axis, on plate A's outer side. Its 20T, idler and belt stand out to `BELT_ENVELOPE_Y` (about 20 mm past plate A) and sweep round the shoulder axis as the arm pitches. Nothing on the body may enter that swept volume over the shoulder's range.
- **Gearbox:** the 20:1 compact, built from `cycloid_poc.py -- --m25-roll` (housings in `model/cycloid-poc/20-1-compact-m25/`), as the elbow's. It's Ø68 × 38.6, with three M3 × 4.5 inserts on R6.5 and three Ø5 × 4 dogs on R10.5 on its output face, and a Ø5 input rod.
- **Motors:**
  - Shoulder: a 17HS19-2004S1, 48 mm long, 1.8° (200 steps), 2.0 A, about 0.59 N·m holding (StepperOnline's figure, from memory, not checked against a datasheet). 42.3 square, M3 on a 31 mm square, Ø22 pilot, Ø5 shaft. The mount leaves room for up to 60 mm.
  - NEMA23 fallback: 57 square, 47.14 hole square, Ø38.1 pilot, Ø6.35 or Ø8 shaft, up to 76 mm long. Check the user's 23HS22 for shaft and length.
  - Base: the same 17HS19-2004S1 type (48 mm).
  - Both NEMA17s are 1.8° (200 steps). The elbow's KL17H248 is 0.9°.
- **Belts in hand:**
  - Shoulder: 3M-420 (140 teeth, 9 mm), 20T on the motor and a printed 80T on the compact's input rod. That's **80:1** in all and 711.11 steps/deg at 16 microsteps. Centres are 131.9 mm (`cycloid_math.belt_centre_distance(20, 80, 420)`).
  - Base: a 3M-477 (159 teeth; the smudged label was first read as 427), the same belt as V1's shoulder. 20T on the motor and a printed 130T ring on the turntable: 6.5:1 (V1 ran 6.6:1), 57.78 steps/deg at 16 microsteps, centres 113.9 mm (`cycloid_math.belt_centre_distance(20, 130, 477)`).
- **Bearings in hand:** 7 × 6810-2RS (50 × 65 × 7): the five spares plus the two that were meant for the upper arm's shoulder seats. 8 were bought; the elbow uses 1.
- **Aluminium tube:** 4 × 250 mm lengths of 9 OD × 7 ID, for the legs.
- **Pulleys:**
  - The 20Ts are bought, or printed with `htd3m_pulley.py` (the user's pulley strategy: print first).
  - The 80T and the base ring are printed.
  - The 80T fixes to the compact's input rod like the elbow's 60T.
- **Printers:** Bambu P2S or A1, bed 225 × 255 (A1 256). PLA, TPU for pads.
  - M3 bolts up to 50 mm. Heat-set inserts for short screws, nut pockets for long ones.
  - Proven fits: `cybot-print-fits` memory and `model/elbow/PRINT.md` (6810 seats nominal Ø65.00).
- **Loads, estimated** (the layout check computes them from the parts):
  - Shoulder: about 8–9 N·m static with the arm level forward, the head (1.35 kg), the hand (0.4 kg) and 500 g.
  - Base: the arm's tipping moment at full reach, about the same plus any reach-out dynamics.
  - **Measured elbow figure:** the 48 mm 0.9° motor at 60:1 lifted the head plus 500 g at 800 mA. The lever wasn't measured.
- **Room for electronics:** a flat, accessible area on the turntable (or the fixed base) for a few driver boards, about 100 × 150 mm in total, with M3 standoff holes. The board sizes aren't known yet, so it's a reserved space, not a fitted mount.

## Decided by the user

- **New base**, on V1's principle: a motor on the fixed base belt-drives a toothed ring on the turntable directly. No cycloid. The 3M-477 belt, a 17HS19-2004S1.
- **Base range ±170°**, with end stops. Wires run outside the centre with a service loop; no slip ring.
- **The shoulder motor sits on the turntable** (turns with the base, doesn't pitch with the arm). It belt-drives a compact cycloid on the shoulder axis: a 20T/80T on the 3M-420, 80:1. Large NEMA17 first, on a mount plate that can be swapped for a NEMA23.
- **Shoulder range: 180°.** In V1's convention, 90° is straight up and 0° and 180° are level, forward and back. In the V2 frame (`elbow_dims.py`: shoulder pitch 0 = upper arm straight up), that's −90° to +90°.
- **Legs:** the four 250 mm 9 × 7 aluminium tubes push into sockets in the fixed base, angled down like a tripod. Printed slip-on feet with TPU pads go over their ends. The legs come out to move the arm.
- **Two of the spare 6810s** carry the base.
- **The shoulder layout in My calls (hub turns with the arm, 6810s in the body walls, compact outboard of wall A) is approved** (2026-11-19).
- **Feet:** if the footprint margin comes out thin, the feet take a bench clamp. No ballast unless the clamped arm still isn't stable.

## My calls (the user has not reviewed these)

- **The shoulder hub turns with the arm.**
  - The upper arm's spec had the hub held still by the body, with the arm turning on it. That leaves nowhere coaxial for the cycloid to drive the arm.
  - So the new hub is fixed to both arm plates: through the plates' Ø65 seats, held against turning by screws or pins drilled through the plates into the hub's flanges. It turns on two 6810s in the two body walls, which carry the arm's bending load.
  - The compact sits on the axis, outboard of body wall A, on plate A's side. Its housing is fixed to wall A, and its output bolts to the hub's end. It carries torque only.
  - The 80T sits outboard of the compact, on its input rod, and the belt runs down outside wall A to the motor on the turntable.
  - The 6810s then sit in the body walls, not in the arm plates' seats. The arm plates' seats hold the hub's flanges instead.
- **Shoulder wires:** the compact caps the hub on side A. The hub's bore stays open to side B, so the arm's wires can still pass through the hub and out past wall B's 6810.
- **The arm sits over the base axis.** The upper arm's mid-plane (between its plates) passes through axis 1, so the kinematics have no sideways offset. The compact and 80T on side A make the body lopsided. The turntable and the base motor's position balance that where they can, and the check reports the combined centre of mass.
- **Clearance poses:**
  - The shoulder's full range must clear at every elbow angle that keeps the forearm and head above the turntable's top face.
  - Poses where the folded forearm would reach below that are reported as a forbidden zone for the controller's soft limits. They don't drive the body taller.
- **Torque check:**
  - The shoulder load comes from the model, as `head_concept.py` computes the elbow's.
  - Capacity: the elbow's test pose is recomputed from the model (the head at 1346 g plus 500 g at the wrist, the forearm level), giving the elbow's demonstrated N·m at 800 mA. That's scaled by 80/60 and by the motors' rated holding torques.
  - The compact's output joint (the dogs) is checked for bearing stress at 1.5× the static shoulder load. If the dogs fail that, the hub end gets more dogs.
  - If the margin comes out under 1.2×, the report says so. Then the user decides on the NEMA23 at the bench; it isn't designed in as the primary.
- **Body walls stand outside everything that sweeps:** on plate A's side outside the elbow's belt envelope, with a clear gap; on plate B's side just outside plate B. Their tops stop below the swept envelope of the upper arm and its elbow motor at the two level positions. The upper arm swinging to ±90° must clear the walls and the turntable.
- **Body layout:** the walls join the turntable as one assembly, bolted. The shoulder motor sits low on wall A's outer side, under the 80T. A slotted mount plate (the NEMA17 plate, or a NEMA23 plate with the same outer pattern) gives belt tension. A screw tensioner pushes it, as on the spider base's slotted arm.
- **Shoulder axis height:** set by the 131.9 mm belt centres and the motor's position. The belt can run at an angle to vertical if that keeps the body lower. I'm guessing at about 150–170 mm above the turntable.
- **Base:**
  - A Ø50 fixed spigot, rising from the fixed base, carries the turntable on two 6810s spaced about 40–60 mm apart. The spigot's bore stays open for lightness but carries no wires.
  - The 130T toothed ring (6.5:1) is on the turntable's underside, at the belt's height.
  - The base motor is upside down on a slotted plate on the fixed base, with a push-screw tensioner, as on the V1 spider base.
- **Stops:**
  - Base: one fixed block on the fixed base and one tab on the turntable, at ±170° from home with a degree or two of overrun.
  - Shoulder: blocks on a body wall and a tab on the hub's end, or on the arm, at −92° and +92°.
  - Both are sized to take a stall across the layers, as the elbow's are.
- **Homing:** a TO-92 Hall sensor and a Ø6 × 3 magnet per axis, as on the elbow's stop collar. Home is the middle of each range: base at 0°, shoulder straight up.
- **Legs:**
  - Four sockets in the fixed base at 90° spacing, angled 45–60° below horizontal so the legs work mostly in compression. Each socket is about 25 mm deep with a light pinch screw (M3, heat-set insert), so a leg is firm but pulls out.
  - The feet slip over the tube ends about 20 mm, with a TPU pad on a flat, level face.
  - The footprint must keep the arm's centre of mass inside it at full reach with 500 g in any base direction. The check reports the margin. If the four 250 mm legs can't give that margin, that's a finding to bring back, not something to fix by shortening the reach.
- **Wires:** a service loop beside the base for axis 1, and clips on the body for the arm's wires. They're routed by the builder.
- **Generator and checks:** a new script pair in `tools/blender/` in the style of `elbow.py` and `elbow_dims.py`. STLs go in `model/shoulder/` and `model/base-v2/` (or one folder), with a `PRINT.md` and P2S plates. The checks:
  - non-manifold
  - bearing seats
  - belt centres
  - clearances through both full ranges (the upper arm, elbow motor and belt against the body; the body against the base and legs)
  - the stops
  - the shoulder torque at the worst pose against the measured elbow figure scaled to 80:1
  - the base's tipping margin with the legs on
  
  Then lay it out in `head_concept.py` with the whole V2 arm.

## Left to the builder

- The hub's exact form, how it locks to the plates, and the 6810 spacing in the walls.
- The wall, turntable, fixed base and foot shapes, and their lightening.
- The leg angle within 45–60°, the socket depth, and the pinch screw.
- Pulley and ring tooth counts within the stated ratios, the tensioner and the slot lengths.
- The exact positions of the stops and Hall sensors.
- Print orientations and a print sheet.
