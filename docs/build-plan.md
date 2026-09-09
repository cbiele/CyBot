# Cybot build plan — print and assembly order

**Set 2026-09-09.** One joint at a time, in this order: **1:20 (axis 2) →
both 1:11 units and the wrist (axes 4, 5, 6) → 1:23 (axis 3) → base (axis
1)**, with the body plates and gripper folded in where they are needed. This
file is the standing list; per-part detail lives in `model/parts-list.md`,
`model/bearings.json` and the exploded models in `model/subassemblies/`.

## 1. Phases and gates

| Phase | Folders | Exploded model | Gate to start |
|---|---|---|---|
| **A. 1:20 axis 2** (now) | 3-axis2 | axis2.blend (verified on printed parts) | printer back from maintenance |
| **B. 1:11 ×2 + wrist** (axes 4, 5, 6) | 5-axis4 ×2, 6-axis5-6 | axis4.blend, axis56.blend | A assembled; 1:11 hardware in hand |
| **C. 1:23 axis 3** | 4-axis3 + second set of axis2 shafts and caps | axis3.blend (stack needs re-seat) | B; 1:23 hardware in hand |
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

**Phase B, 1:11 ×2 and wrist — order now**
- 6705zz ×8, 6812zz ×4 (STL seats are Ø78; the author's early 6811 does not fit)
- brass bushings 8×10×6 ×24, pins Ø6×25 ×12
- M4 and M3 threaded rod (cut to length), M5×20 ×16, nuts
- wrist: 6810zz ×2, 6804zz ×2, HK0608 ×4, M6×25 ×2, GT2 belts 232 ×1 and
  308 ×3, GT2 40T pulleys ×2, GT2 20T ×1
- 3× NEMA17 dual-shaft (47 mm class) + 3× MKS SERVO42D (axes 4, 5, 6)

**Phase C, 1:23 — order now, ships with the above**
- 6813zz ×2, 6804zz ×5, 688rs ×18
- M6×50 pins: each axis3 holder has 14 Ø6 holes, buy 28
- M4 threaded rod, M6×70 ×6 with nuts
- 1× NEMA23 dual-shaft ≤41 mm + 1× MKS SERVO57D, 1× Omron E6B2-CWZ6C

**Phase D, base**
- 6816zz ×2, 6804zz ×2, 625zz ×8, 606zz ×4
- M5×20 ×8, M6×50 ×8, M6×40 ×12, M6 nuts ×8
- 3M 30T pulleys ×2 (12 mm), HTD648-3M belts ×2
- NEMA17 dual-shaft + SERVO42D, E6B2-CWZ6C

**Phase E, body**
- 606zz ×8 (tensioners), M6 screws for the arms
- HTD477-3M belts ×4, 3M 20T (15 mm) ×1, 3M 30T (12 mm) ×3
- axis-2 NEMA23 dual-shaft + SERVO57D + E6B2-CWZ6C
- 24 V 10 A PSU, contactor, e-stop, SN65HVD230 daughterboard parts
  (electronics spec §7)

**Phase F, gripper:** hardware list is in the separate Cults gripper
project; the STLs show one 6804 and a T8 lead screw and nut.

## 4. Checks that gate phases

- **Ring-pin count** on the printed axis-2 housing: 12 per STL half vs 21
  in the author's 1:20 render. Settles which joint is 1:20 vs 1:23 and the
  pin quantity. Do at the phase A inventory.
- **Cap fit on axis 3**: confirm `axis2-diskCap` fits the axis-3 disks
  (same Ø80 recess and Ø57 pitch circle) with the first axis-3 disk print,
  before printing three more.
- **MKS board depth**: measure a SERVO57D; decide 41 mm NEMA23 vs a
  mainBody2 recess. Gates phase E. Measure a SERVO42D too for the gripper.
- **Axis-3 stack re-seat** in the model with printed parts in hand (the
  export has OPH1 overlapping the encoder pulley). Gates phase C assembly.
- **Gripper motor**: 34-40 mm pancake NEMA17 or a 10 mm longer
  `OPH_To_Gripper`. Gates phase F.

## 5. In parallel, off the printer

- Founder review of `docs/superpowers/specs/2026-09-06-cybot-electronics-design.md`,
  then the implementation plan for the host-tested MKS CAN codec and planner.
- Single-board bench as soon as the first SERVO42D and NEMA17 arrive:
  Heltec + SN65HVD230 + one motor loose. This is why phase B's motors are
  ordered first.

## 6. Phase A, granular

To be written next: the axis-2 inventory and the step list to finish the
1:20 joint, from `model/subassemblies/axis2-assembly.md`.
