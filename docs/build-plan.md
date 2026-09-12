# Cybot build plan — print and assembly order

**Set 2026-09-09, ratios corrected 2026-09-10.** One joint at a time, in this order: **1:23 (axis 2) →
both 1:11 units and the wrist (axes 4, 5, 6) → 1:20 (axis 3) → base (axis
1)**, with the body plates and gripper folded in where they are needed. This
file is the standing list; per-part detail lives in `model/parts-list.md`,
`model/bearings.json` and the exploded models in `model/subassemblies/`.

## 1. Phases and gates

| Phase | Folders | Exploded model | Gate to start |
|---|---|---|---|
| **A. 1:23 axis 2** (mostly assembled 2026-09-10; POC proven) | 3-axis2 | axis2.blend (verified on printed parts) | done except final clamp-up |
| **B. 1:11 ×2 + wrist** (axes 4, 5, 6) | 5-axis4 ×2, 6-axis5-6 | axis4.blend, axis56.blend | A assembled; 1:11 hardware in hand |
| **C. 1:20 axis 3** | 4-axis3 + second set of axis2 shafts and caps | axis3.blend (stack needs re-seat) | B; 1:20 hardware in hand |
| **D. Base axis 1** | 2-axis1, plateBall feet | axis1.blend | C |
| **E. Body plates, tensioners, motors** | 1-mainbody (split plates) | mainbody.blend | NEMA23 length decision, MKS board measured |
| **F. Gripper** | 4FingersGripper | gripper.blend | gripper motor length decision |

Phase E is listed last, but the plates are what mount axes 2 and 3 to each
other, so their print slots come right after phase C's parts, before the base.

## 2. Print queue, in the order to send jobs

1. **Axis 2 remainder.** Inventory first: of the 16 files (18 instances,
   three `axis2-diskCap`), the sample joint already covers disks, caps,
   shafts, housings and OPHs; the holders and the two GT2 pulleys are the
   likely gaps. Confirm against the printed pile, then print.
2. **5-axis4, first set** (13 files, 1.0 L): disk1, disk2, diskCap ×2,
   shaft, shaft2, shaft3, housing, housingNema, OPH2 (long, carries the
   tube), 80TGT2-7mm, axis4_axis5_holder, Tube.
3. **5-axis4, second set** for axis 5: same minus the elbow holder and
   tube, with OPH (short) instead of OPH2.
4. **6-axis5-6** (12 files, 1.2 L): holder + holder2 (or holderNoSplit, 209
   mm, if you prefer one piece), axis6holder1, axis6holder2,
   Housing2Attach1/2, 80T-rotor, pulley, pulleySpacer,
   quarterTurnBeltDrive, 80T-7mm.
5. **4-axis3** (9 files, 0.54 L) plus a second set of axis2-shaft1..4 and
   three more axis2-diskCap (fit unverified, see §4).
6. **1-mainbody**: the four split plate pieces in `model/split/` (upper
   pieces are 254 mm: skirt only, no brim), beltTentioner1-3, plateBall ×4.
7. **2-axis1** (6 files, 1.8 L, the heaviest folder).
8. **Gripper** (6 files; grip, Axe, T8_to_Axes ×4 each) after the motor
   decision.

Filament: about 4 kg total at 40 % infill; phases B and C together are
about 2.8 L.

## 3. Hardware to order per phase

From the PDF hardware lists, corrected where the STLs disagree.

**Phase B, 1:11 ×2 and wrist — ordered 2026-09-10**
- 6705 ×8, 6812 ×6 (four for the two gearboxes, two for the wrist; STL
  seats are Ø78 so the author's early 6811 does not fit)
- brass bushings 8×10×6 ×24, pins Ø6×25 ×12
- M4 rod 1 m (output rods), M3 rod 1 m (cam lock rods), M5×20 ×16, nuts
- wrist: 6810 ×2, 6804 ×2, HK0608 ×4, M6×25 ×2, GT2 belts 232 ×1 and
  308 ×3 (6 mm wide), GT2 40T ×2 and 20T ×1 with 5 mm bore
- ZZ or 2RS on any bearing: same dimensions, seal type is the only difference
- ~~3× NEMA17 dual-shaft (47 mm class) + 3× MKS SERVO42D (axes 4, 5, 6)~~
  **Bought 2026-09-11:** 4× 17HS8401B (42×42×48 mm, 1.8 A, 52 N·cm, Ø5
  front shaft 24 mm, Ø5 rear stub 10-13 mm, bare leads) for axes 4, 5, 6
  and 1, plus 1× MKS SERVO42C kit (board + matched motor). The 42C is the
  UART/step-dir board, not CAN: it is the mechanical reference for the
  rear-stub length and magnet gap, not the CAN bench unit. Still to buy:
  3× SERVO42D boards for the phase B motors (+1 for axis 1). Expect to trim
  each 17HS8401B rear stub to match the kit motor before gluing the magnet.

**Phase C, 1:20 — order now, ships with the above**
- 6813zz ×2, 6804zz ×5, 688rs ×18
- M6×50 pins: each axis3 holder has 14 Ø6 holes, buy 28
- M4 threaded rod, M6×70 ×6 with nuts
- ~~1× NEMA23 dual-shaft ≤41 mm + 1× MKS SERVO57D, 1× Omron E6B2-CWZ6C~~
  **Bought 2026-09-12:** 2× STEPPERONLINE 23HS22-2804S (56 mm, 2.8 A,
  1.26 N·m, single shaft 6.35 mm) for axes 2 and 3. Fits the 61 mm pocket
  because the MKS board is gone: drivers move to a PakaNode daughterboard
  (TMC5160-class SPI chain, MT6701 output encoders) being designed in the
  Chopaka session. No SERVO42D/57D boards will be bought; the Omron E6B2
  plan is dropped pending that design.

**Phase D, base**
- 6816zz ×2, 6804zz ×2, 625zz ×8, 606zz ×4
- M5×20 ×8, M6×50 ×8, M6×40 ×12, M6 nuts ×8
- 3M 30T pulleys ×2 (12 mm), HTD648-3M belts ×2
- NEMA17: one of the four 17HS8401B already bought; driver channel on the daughterboard

**Phase E, body**
- 606zz ×8 (tensioners), M6 screws for the arms
- HTD477-3M belts ×4, 3M 20T (15 mm) ×1, 3M 30T (12 mm) ×3
- axis-2 NEMA23: bought, see phase C
- 24 V 10 A PSU, contactor, e-stop, SN65HVD230 daughterboard parts
  (electronics spec §7)

**Phase F, gripper:** hardware list is in the separate Cults gripper
project; the STLs show one 6804 and a T8 lead screw and nut.

## 4. Checks that gate phases

- ~~Ring-pin count~~ **Settled 2026-09-10:** the axis-2 housing halves have
  12 pin holes and the axis-3 holders 7 each (14). The PDF's "12 for 1:23,
  14 for 1:20" makes axis 2 the 1:23 and axis 3 the 1:20 (the profile is cut
  for 24 or 21 pin positions and only every other one, or two of three, is
  populated). The videos' "1:24" is this same joint.
- **Cap fit on axis 3**: confirm `axis2-diskCap` fits the axis-3 disks
  (same Ø80 recess and Ø57 pitch circle) with the first axis-3 disk print,
  before printing three more.
- **MKS board depth**: measure a SERVO57D; decide 41 mm NEMA23 vs a
  mainBody2 recess. Gates phase E. Measure a SERVO42D too for the gripper.
- **Rear-stub length**: measure the SERVO42C kit motor's rear stub and
  magnet gap, then cut the four 17HS8401B stubs to match. Gates the first
  42D board mount.
- **Axis-3 stack re-seat** in the model with printed parts in hand (the
  export has OPH1 overlapping the encoder pulley). Gates phase C assembly.
- **Gripper motor**: 34-40 mm pancake NEMA17 or a 10 mm longer
  `OPH_To_Gripper`. Gates phase F.

## 5. In parallel, off the printer

- Founder review of `docs/superpowers/specs/2026-09-06-cybot-electronics-design.md`,
  then the implementation plan for the host-tested MKS CAN codec and planner.
- **Driver pivot 2026-09-12:** MKS smart-steppers dropped (~$70 per axis).
  A PakaNode daughterboard (seven TMC5160-class drivers on SPI, MT6701
  output encoders over J_QWIIC1, own fused 24 V entry, lives in the Cybot
  base beside the node) is being designed in the Chopaka session; the Cybot
  electronics spec is rewritten once its interface contract is published.
- Single-board bench once a first driver channel exists:
  Heltec + SN65HVD230 + one motor loose. This is why phase B's motors are
  ordered first.

## 6. Phase A, granular: finishing the 1:23 joint (axis 2)

Source: `model/subassemblies/axis2-assembly.md` and `axis2-exploded.png`.
Tick the printed column against the pile; the sample joint from `quartit/`
covers the parts marked (sample) if those prints are being reused.

### 6.1 Print inventory

| # | Part | Qty | Printed | Notes |
|---|---|---|---|---|
| 1 | axis2-GT2-stepper | 1 | [ ] | 118 mm pulley, motor side |
| 2 | axis2-holder1 | 1 | [ ] | motor-side holder, 6 × Ø8 rod holes |
| 3 | axis2-housing2 | 1 | [ ] (sample) | ring-pin half, Ø85 step |
| 4 | axis2-OPH1 | 1 | [ ] (sample) | Ø65 boss, Ø32 bore |
| 5 | axis2-shaft4 | 1 | [ ] (sample) | eccentric, coaxial journal outboard |
| 6 | axis2-diskCap | 3 | [ ] [ ] [ ] (sample ×1) | one per disk |
| 7 | axis2-disk3 | 1 | [ ] (sample) | disks are identical files; phase by orientation |
| 8 | axis2-shaft3 | 1 | [ ] (sample) | |
| 9 | axis2-disk2 | 1 | [ ] (sample) | |
| 10 | axis2-shaft2 | 1 | [ ] (sample) | |
| 11 | axis2-disk1 | 1 | [ ] (sample) | |
| 12 | axis2-shaft1 | 1 | [ ] (sample) | |
| 13 | axis2-OPH2 | 1 | [ ] (sample) | |
| 14 | axis2-housing1 | 1 | [ ] (sample) | |
| 15 | axis2-holder2 | 1 | [ ] | encoder-side holder |
| 16 | axis2-GT2-encoder | 1 | [ ] | 118 mm pulley with the Ø20 blind hub |

Not in this folder but needed to mount the joint: the split mainBody plates
(phase E) and the NEMA23 + SERVO57D + E6B2 (phase E hardware).

### 6.2 Hardware for this joint

| Item | Qty | Have | Where it goes |
|---|---|---|---|
| 6813zz 65×85×10 | 2 | [ ] | housing Ø85 step + plate pocket / OPH Ø65 boss |
| 6804zz 20×32×7 | 5 | [ ] | three disk bores, two OPH bores |
| 688rs 8×16×5 | 18 | [ ] | six Ø16 pockets per disk |
| M6×50 pins | 12 (PDF says 14) | [ ] | Ø6 holes in the housing halves; count the printed housing |
| M4 threaded rod 3.85 mm | 6 lengths | [ ] | through the 688s and the Ø8 holes in holders and pulleys |
| M4 nuts | 12+ | [ ] | pulley counterbores both ends |
| M6×70 + nuts | 6 | [ ] | holder-to-housing clamp |

### 6.3 Assembly order (stepper side first, along the joint axis)

1. **Disks.** For each of the three disks, from the recessed side: press
   the 6804 into the Ø32 centre bore (it stands 2.5 mm proud), press six
   688s into the Ø16 pockets (1.5 mm proud), drop a diskCap into the Ø84
   recess so its counterbores sit over the bearings. Do this three times.
2. **Eccentric shaft.** Assemble shaft4 → shaft3 → shaft2 → shaft1 so the
   three eccentric sections fall 120° apart. Slide a capped disk onto each
   eccentric: disk3 on the shaft4/shaft3 section, disk2 on shaft3/shaft2,
   disk1 on shaft2/shaft1, caps facing the stepper side. Check the six
   pockets of all three disks line up on the same six rod lines.
3. **Ring pins.** Push the M6×50 pins into housing2, then set the disk
   stack into it so the lobes engage the pins, then close with housing1.
4. **Output side.** Fit a 6804 into each OPH's Ø32 bore; slide OPH1 onto
   the shaft4 journal and OPH2 onto the shaft1 journal. Seat a 6813 on each
   OPH's Ø65 boss and into the housing's Ø85 step (5 mm engages here, the
   other 5 mm sits in the body plate later).
5. **Rods.** Pass the six M4 rods through OPH → 688 columns → OPH. Bolt
   holder1 to OPH1 and holder2 to OPH2 face to face (the Ø65 boss on each
   holder meets the OPH boss), rods through the holders' Ø8 holes.
6. **Pulleys.** GT2-stepper over the rods on the holder1 side, GT2-encoder
   on the holder2 side with its Ø20 blind hub over the shaft1 end. Nuts in
   the pulley counterbores; snug evenly so the disks stay free.
7. **Check.** Turn the shaft by hand: one input turn should move the output
   1/20 turn with no tight spots. Tight spots mean a disk is mis-phased or
   a cap is not fully down.

### 6.4 What assembly taught us (2026-09-10, joint mostly built, POC proven)

- **Cam lock.** The four shaft pieces are locked together and phased by
  three M4 rods pushed cold through the three small holes that run the length
  of the train; the rods' ends are the studs the two big pulleys bolt onto.
  The stepper pulley is held by those studs and rides on the 6804 in OPH1;
  the motor only pulls the belt.
- **Output rods.** Six more M4 lengths (same stock, about 68 mm) run through
  the six 688s of all three disks and the rim holes of both OPHs. They must
  float: 8 mm bore minus 3.85 mm rod is twice the 1.9 mm cam throw. Not
  glued, not heated, nuts only snug. The M6×70 ×12 are the clamp bolts
  (holder + plate + housing half, six per side), not the rods.
- **Ring pins** are the twelve smooth Ø6 × 50 pins in the housing slots.
- **Holders** are a mirrored pair: `axis2-holder2` is holder1 mirrored, and
  differs from a flipped holder1 by a 31 × 4 mm feature at the bore, so
  both files print.
- **Rod stock:** one metre of M4 covers the nine pieces for one joint.
- PDF figure crops for this joint are in `reference/pdf-figures/`.

### 6.5 Open on this joint

- Whether the sample-joint parts are the same v5 geometry as the current
  STLs (the quartit folder is dated earlier); measure one disk's pocket
  circle at 57 mm if in doubt.
