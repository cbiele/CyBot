# Compact cycloid POC — design

Date: 2026-10-25. Status: draft for review.

## 1. Why

Bench work on 2026-10-24 showed the head is the arm's mass problem. Estimates from the model
(printed volume at 40 % infill, catalogue hardware weights):

| Head item | Approx. mass |
|---|---|
| 3 × NEMA17 (axis 5, axis 6, gripper) | ~1,000 g |
| Printed axis 5/6 holders and gripper (1,100 cm³ solid) | ~700 g |
| Bearings (2 × 6812, 2 × 6810, 2 × 6705, 2 × 6804, HK0608) | ~370 g |
| Steel pins and brass bushings | ~60 g |

Axis 5's 1:11 drive is Ø100 because it is built around two 6812s (60 × 78, ~100 g each). V2 aims to
cut the head's weight and cost. The path agreed on 2026-10-25 is: first a compact cycloid around
6804 main bearings, then the motor choice (leaning towards 20 mm pancake NEMA17s), and later a head
case sized for two pancakes and two cardsort motor node boards. The Octopus Pro stays the
controller until then.

This POC is a standalone bench reducer, sized from the start to become the axis 5/6 module of a
smaller head. It does not bolt into the V1 head.

## 2. What it must prove

1. A 1:20 printed cycloid built on 6804s assembles with press fits only and turns smoothly by hand.
2. Its friction is low. Friction, more than load, is what stalled the V1 shoulder.
3. Together with a 2:1 belt it holds and lifts the axis 5 design load: about 1.7 N·m (gripper, axis 6
   and a 200 g payload, about 0.8 kg centred 150 mm out).
4. It is much smaller and lighter than V1's 1:11: about Ø60 × 35 mm, with about 90 g of hardware
   against about 300 g.

## 3. Layout

Input → 20T GT2 on the motor → 6 mm GT2 belt → 40T GT2 on the input core → two eccentrics → two
disks → 21 ring pins in the housing → 6 output pins → output carrier.

| Item | Choice | Why |
|---|---|---|
| Ratio | 1:20 cycloid (20 lobes, 21 ring pins) × 2:1 belt = 40:1 | Coarse enough lobes for a 0.4 nozzle (about 7 mm apart); 40:1 is what a 20 mm pancake would need |
| Disks | Two, 180° apart, no caps | Two cancel the eccentric forces at wrist speeds; bushings and bearings press straight into the disk, so a cap adds nothing |
| Eccentricity | 1.0 mm nominal | Generator checks it against undercut; see §5 |
| Ring pins | 21 × Ø3 × 18 spring pins, slit facing away from the disk | On hand. Needle rollers Ø3 are the alternative (§7) |
| Output pins | 6 × Ø4 × 18 spring pins through 6 × 8 × 6 brass bushings in each disk | Bushing bore 8 = pin 4 + 2 × eccentricity. Brass is cheap and pressed in holds without slipping (V1 experience) |
| Disk bearings | 6800 (10 × 19 × 5), one per disk | Small enough for a Ø50 disk |
| Input shaft | One printed eccentric body on a Ø5 steel core rod | V1's four-piece shaft is where tolerance slop builds up first; see §4 |
| Input bearings | 625ZZ (5 × 16 × 5), one in each carrier, on the steel rod | In hand (phase B order) |
| Main bearings | 2 × 6804 (20 × 32 × 7), one per side | One alone can't resist the gripper's moment. ~36 g against ~200 g for 2 × 6812 |
| Input pulley | GT2 40T, 5 mm bore, set screw on a flat ground on the core rod | In hand |
| Motor pulley | GT2 20T, 5 mm bore | In hand |

## 4. Parts

All printed parts come from one parametric generator, `tools/blender/cycloid_poc.py`, in the same
style as the other generators (`hand_lib`, self-test asserts, STLs to `model/cycloid-poc/`).

1. **Housing** (one piece): a ring with 21 Ø3 pin holes through its full width on the pin circle,
   and a 6804 outer-ring seat at each face. Pins are pushed in last, through the faces, once the disks
   are in. Mounting flange with four M3 holes for the bench base and, later, the head.
2. **Disk** ×2 (one STL, the second flipped and turned by half a lobe at assembly): 20-lobe
   cycloid profile with a print clearance offset, a Ø19 press seat for the 6800, and six Ø8 press seats
   for the brass bushings. Thickness 6, the bushing length.
3. **Eccentric body**: one print carrying both journals (Ø10, 1.0 mm offset, 180° apart), bored for the
   Ø5 rod and pinned to it with a cross pin or a D-flat. A thin spacer ring between the journals keeps the
   disks apart. Each 6800 slides on from its own end, so the ends must stay within Ø8 (bearing bore 10
   minus twice the eccentricity).
4. **Output carrier** (front): a hub that rides the front 6804's inner ring, a Ø16 seat for one 625,
   six Ø4 press holes for the output pins, and an output face with an M3 bolt pattern for the test arm.
5. **Rear carrier**: same hub and 625 seat, and six Ø4 press holes. Pressing the output pins into both
   carriers ties them into one rigid output.
6. **Bench base**: holds the housing flange and a NEMA17 on a slotted plate, which tensions the belt
   at the centre distance the stocked belt gives (about 86 mm for a 232 belt on 20T/40T; the generator
   computes it).
7. **Test arm**: bolts to the output face, with holes for a weight at a few known radii.

Hardware for one reducer: 2 × 6804, 2 × 6800, 2 × 625, 12 × brass 6 × 8 × 6, 21 × Ø3 × 18 and
6 × Ø4 × 18 spring pins, Ø5 rod about 50 mm, GT2 20T + 40T, 6 mm GT2 belt, M3 screws.

## 5. Generator checks (asserts before export)

- Every mesh is manifold.
- Cycloid: no undercut. The profile's smallest radius of curvature exceeds the pin radius plus
  margin, and K1 = e·N/R stays under 1.
- Disk: the 6800 seat and the bushing seats each keep at least 1.5 mm wall to each other and to
  the lobe root.
- Eccentric body: the ends stay within Ø8, the wall around the Ø5 rod is at least 1.5 mm, and the
  journals are exactly 180° apart.
- Carrier hubs: at least 1.5 mm wall between the 625 seat (Ø16) and the 6804 bore (Ø20).
- The stack's total width fits the 18 mm pins with at least 2 mm engaged in the housing at each end.

Press-fit diameters (the 6800, 6804, 625 and bushing seats, plus the Ø3/Ø4 pin holes) start from V1's
proven offsets. Before the full print they are checked with a fit coupon: one ring of each seat and
pin hole.

## 6. Bench test

Driven from the Octopus on MOTOR5 (B, the wrist pitch slot, TMC2209) with a 17HS8401B, since it is
in hand. Steps per output degree = 200 × 16 × 40 / 360 = 355.56. Current starts at 1200 mA.

1. **Hand turn**: with the belt off, turning the 40T by hand is smooth, with no tight spots over a full
   output turn (20 turns of the 40T).
2. **Ratio**: mark the output; commanded 360° lands on the mark over three turns.
3. **Friction**: unloaded, step the driver current down to find the lowest current that still turns it
   reliably. Compare it with the same test on axis 4 (V1 1:11).
4. **Load**: hold, then lift, the test arm with weights up to 1.7 N·m, at 1200 mA and then lower.
   Record the stall point.
5. **Backlash**: pointer on the test arm; play at the output with the motor holding, in degrees.
6. **Mass**: weigh the assembled reducer without the motor.

Results go to `docs/build-plan.md` under the bench notes, one entry per run.

## 7. Alternatives held for later

- **Needle rollers Ø3** as ring pins, if the spring pins' slits wear or click.
- **683ZZ rollers** on the output pins, if the brass bushings show too much friction.
- **The motor choice** (20, 23, 34 or 40 mm pancake): decided from the friction and load results above.
- **Head case** for two pancakes and two node boards: after the motor choice.

## 8. Out of scope

Fitting the POC into the V1 head, motor relocation, encoders, node boards and axis 6's design.
