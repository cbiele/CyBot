# Arm-mounted shoulder drive and V1-style base bearing: design

**Date:** 2026-11-21
**Changes:** the shoulder drive, the body and the base bearing of `docs/superpowers/specs/2026-11-20-low-shoulder-flat-stand-design.md`, built on main up to `de9edf8`. The stand (the drum shell, the 15° legs, the feet) and the elbow stay as built.

## Why

Looking at the built model in Blender, the user saw two things they didn't want.

- **The turntable sits on a riser.** The hub between the turntable and the drum stands about 98 mm above the drum's top. It lifts the whole arm away from the bench the design was meant to reach.
- **The shoulder drive is bulky and in the way.** The motor box on wall A, the fixed stub and the walls take space, and the base motor stands up on its shelf where the turning arm can meet it.

The user's fix uses joints they already trust:
- the base bearing as V1 had it
- the shoulder built like the elbow, which is built and works, mirrored

## Goals

- **The turntable sits low on the drum, with no riser.** The arm comes down by about the riser's height, so it reaches closer to the bench.
- **Nothing fixed stands in the turning arm's path.** In particular, that means the base motor.
- **The shoulder is the elbow joint, mirrored.** It uses the same compact, the same kind of belt drive inside the arm, and the same kind of aluminium-tube bracket. That keeps it slim, with no step-out.
- **Both sides of the arm are carried at the shoulder.**

## Non-goals

- **The NEMA23.** The user's call (2026-11-21): NEMA17 only. The 23's drop-in plate and the box sized for it go.
- **Wiring.** It runs in an external loom, as before.
- **Changes to the stand.** The legs and the feet stay. The drum changes only at its centre and in a flat at 270° for the base motor.
- **Changes to the elbow, forearm or wrist.**

## Anti-goals

- **A belt or bracket that steps out from the arm plates.** The user rejected it. The shoulder belt hugs the outside of its plate, as the elbow belt does.
- **Anything fixed that the arm, the base motor or its belt can meet inside the working range.**
- **A turntable that has to be reprinted to fix or re-angle the shoulder bracket.**

## Constraints

- **The compact:** the 20:1 compact (`cycloid_poc.py -- --m25-roll`), Ø68 × 38.6 (39.6 to the output face).
  - Its rear face mounts to a plate's inner face, as the elbow compact does on plate A.
  - Its output face is the shoulder build's: three M3 inserts on R6.5 and the bigger dogs (`OUT_PLATE_R`, `DOG_R` 3.5, `DOG_H` 6 in `shoulder_dims.py`).
  - The Ø5 input rod comes out of its rear face, and its length is free.
  - The `--stub-mount` housing isn't needed any more.
- **The shoulder motor:** a 48 mm 17HS19-2004S1 NEMA17 (1.8°).
- **The shoulder belt:** 3M 20T/80T on the 3M-420, 80:1 overall, centres 131.9 (`SHOULDER_BELT_C`). This belt is in hand.
- **The base:** another 17HS19-2004S1, the 3M-477, the 20T and the printed 130T ring, 6.5:1, centres 113.9. Range ±170°.
- **Bearings:**
  - 6810-2RS (50 × 65 × 7). Four are in use: two in the base, one in plate A at the shoulder, and one in the elbow's plate B. Count the spares before adding more.
  - 625s, as in the compact.
- **Tube:** 9 × 7 aluminium in 250 mm lengths. The shoulder bracket needs three more pieces; the user has them.
- **Nothing on the base is printed yet** (the user, 2026-11-21). The drum, the 130T ring and the turntable are all fresh prints, so they can be redesigned freely.
- **The upper arm plates are reprinted** (the user, 2026-11-21). This reverses the 2026-11-20 anti-goal.
  - They keep the elbow end as built: the elbow compact, the elbow motor on plate A's inner face, the elbow belt outside plate A, the elbow's 6810 in plate B, and 220 mm between the axes.
  - They also keep the 60 mm gap and the 8.5 mm thickness.
- **Printers:** P2S or A1, bed 256. PLA, and TPU for the pads. M3 bolts up to 50 mm, heat-set inserts for short screws.
- **Homing:** a TO-92 Hall sensor and a Ø6 × 3 magnet per axis.
- **The shoulder driver's current cap stays,** recomputed for the new layout, so a stall can't pass 13.5 N·m at the output.

## Decided

### 1. The base: V1's bearing arrangement

The user, 2026-11-21: "just like V1. We have the T130 ring, and it has the cylinder attached out the bottom that sit in the drum. The two pieces (base drum and T130 with inner cylinder ride on the 6810's. The Motor mounted out and facing up."

- **The turning part:** the turntable, the 130T ring and a cylinder hanging from the ring's underside turn together. The cylinder drops into the drum.
- **The bearings:** two 6810s inside the drum carry the cylinder. Their outer rings sit in seats in the drum's centre, and the cylinder runs through their inner rings.
- **What goes:**
  - the fixed spigot
  - the spigot spacer and cap
  - the turntable's hub, which was the riser
- **The turntable sits just above the drum's top,** with the ring under it.
- **The base motor:** it stays outboard on the drum's shelf, flipped, with its body under the shelf and its shaft up. Its 20T sits level with the ring, so only the pulley stands above the shelf, under the turntable's level.
- **The drum's wall gets a flat at 270°** (the user, 2026-11-21), as V1's ring had flats on its Ø200 wall. On the 3M-477 (centres 113.9) the motor's inner face is at r92.75, inside the drum's r96. The flat lets the motor hang beside the drum and keeps the belt in hand. The flat clears the motor at both ends of the tension slot.
- **Unchanged:** the stop block and the Hall post on the drum, the tab under the turntable or ring, and ±170°.

### 2. The shoulder: the elbow joint, mirrored

The user, 2026-11-21: "do the same joint as the elbow, just opposite."

- **The motor:** the shoulder NEMA17 sits inside the arm, between the plates, just above the elbow motor (further from the shoulder axis than the elbow motor). It turns with the arm.
- **The belt:** the motor drives the compact's input through the 20T/80T, on the outside of plate B. That's the side opposite the elbow belt: "a flipped, mirror of the elbow belt". The belt hugs the plate, as the elbow's does.
- **Which way round the compact goes:**
  - It sits between the plates at the shoulder end, its rear face on plate B's inner face, and its input rod out through plate B to the 80T.
  - The housing turns with the arm.
  - Its output faces plate A.
- **The shoulder hub:**
  - It bolts and dogs to the compact's output, like the elbow hub.
  - Its journal runs out through plate A's 6810. Plate A turns on it.
  - It runs on past the elbow belt's envelope (`E.BELT_ENVELOPE_Y`) to the tube sockets.
  - The hub is fixed to the base, and the arm turns round it.
- **The base bracket:** three 9 × 7 aluminium tubes, splayed like the elbow's V, run from the hub down into a printed socket bracket.
  - The socket bracket bolts to the turntable, so a broken or re-angled bracket is a small reprint, not the whole turntable.
  - It's on plate A's side, the side away from the shoulder belt.
- **The outboard bearing:** a 625 on a post bolted to the turntable carries the end of the compact's 5 mm input rod, outboard of the 80T. The user wants it "so both sides of the arm plates are supported."
  - **What it's for** (the user, 2026-11-21): the 625 steadies the rod against the belt's pull. The arm's weight is carried mainly on plate A's side, by the 6810 on the fixed hub.
  - A structural support on plate B's side would need a journal past the 80T's plane, which is the step-out the user ruled out.
  - The rod's side load is reported, not a gate.
- **What goes:**
  - walls A and B
  - the fixed stub and its spacer
  - hub B
  - wall A's motor box, the drop-in motor plate and its pull screw
  - the drill jig, because the plates are reprinted
- **The plates are reprinted with the extra mount holes** that the new layout needs.

### My calls (not yet reviewed by the user)

- **The 80:1 stays**, on the 3M-420 and 20T/80T already in hand. So the motor's axis sits 131.9 from the shoulder axis along the arm. The elbow motor sits at about 71 and the elbow compact at 220, so the shoulder motor fits between them.
- **Tensioning:** slotted motor holes in plate B and a screw-adjusted idler, as on the elbow.
- **The outboard bearing is a 625** (Ø5 bore), because the rod is Ø5 and 625s are already in the parts list.
- **The stops and the Hall** follow the elbow's pattern. A tab and the magnet ride on the turning side, and the block and the sensor sit on the fixed hub or bracket. Where exactly is the builder's call, but the stops must be keyed so they only fit one way.
- **The shoulder axis height** goes as low as the new parts allow. The arm plates' r38 ends, the 80T's r37.8 and the bracket set it.
- **The current cap is recomputed for 80:1**, giving the same 13.5 N·m limit.

## What the checks must show

The current checks carry over where the parts carry over: non-manifold, the bearing seats, belt centres at both slot ends, bed size, the bench reach over every φ, the soft-limit table and the tipping report. New or changed:

- **The shoulder motor inside the arm:**
  - it clears the elbow motor, the elbow belt's idler, the cross members, both compacts and the plates' windows
  - its 20T and the idler sit within the shoulder belt's envelope outside plate B
- **The fixed parts against the turning arm:** through the shoulder's whole range at enough φ, the hub, tubes, socket bracket and outboard post clear:
  - plate A, the elbow belt's envelope and the elbow motor's 20T
  - plate B, the shoulder belt, the 80T and the shoulder motor's 20T
  - the forearm and the wrist
- **Range:** report how far past ±90° the arm swings before anything meets it, and set the stops there.
- **The base motor:** at every φ, nothing that turns meets it, its 20T or its belt. Its body clears the drum's flat at both slot ends, and clears the legs and their sockets.
- **The base bearing:** the cylinder's two 6810s are clamped (inner rings on the cylinder, outer rings in the drum), and the spacing between them is reported.
- **The arm's new height:** report the shoulder axis above the bench (219.5 today), and the bench reach at the new height.
- **Capacity:** the shoulder motor now rides on the arm, so its mass loads the shoulder.
  - Count the poses over the NEMA17's estimated capacity (4.76 N·m) again, and report the worst.
  - This is reported, not a gate, as now.
- **The input rod's support:**
  - report the rod's length between the compact and the 625
  - report the side load on it from belt tension and the arm's weight on plate B's side
- **The tube bracket:** each tube's axial load and the bending at its sockets at the worst pose, as the elbow check does.
- **Tipping:** report the margin, now with the arm lower.

## Lessons carried over

- **Screw heads must be reachable and seat at every slot position.**
- **Tension screws need tool access.**
- **Parts that only work one way round need a key or a note on the print sheet.**
- **Avoid coincident faces in the generators** (`shoulder.py` notes): use hulls for stepped bores, and start features 1 mm below the bench, then trim.

## What's reusable

- **The drum shell's outside** (plus the flat), the legs and sockets, the feet, the stop block and the Hall post. Only the drum's centre changes: the hub tube becomes the two 6810 seats.
- **The 130T ring's teeth,** the base motor's plate and its push-screw tensioning, adapted to the flipped motor.
- **The round turntable,** without walls. It gains bolt patterns for the socket bracket and the outboard post.
- **The shoulder output plate** with the bigger dogs, the 80T, and the stop collar's keyed pattern.
- **`head_concept.py -- --shoulder`,** the whole-arm check and the renders.
- **The elbow's hub, tube sockets, idler and motor slots**, as the pattern to mirror (`elbow.py`, `elbow_dims.py`).

## Housekeeping

- **The uncommitted review minors on the fixed stub and the spigot spacer are dropped,** because both parts go. The `head_concept.py` bench-reach sweep (every 15° of φ, worst φ reported) stays.
- **`model/shoulder/PRINT.md` is rewritten** for the new parts and plates.

## Left to the builder

- **The cylinder:** its diameter, length and wall, the 6810s' spacing in the drum, and how their inner rings are clamped (a retainer on the cylinder's bottom end is the likely form).
- **How the ring, the cylinder and the turntable join,** or whether two of them are one print.
- **The base motor:** the flat's exact width and depth, and the shelf's new form.
- **The plate shapes,** windows, cross members and the extra holes, within the constraints above.
- **The hub's form,** its output link, its length past the elbow belt, and the tube sockets' angles.
- **The socket bracket's form** and its bolts to the turntable.
- **The outboard post's form** and its bolts to the turntable.
- **The stops' and the Hall's exact places.**
- **The shoulder axis height,** the stops and the turntable's radius.
- **Print orientations,** the plates on the print sheet and the print sheet itself.
