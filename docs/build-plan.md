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
3. **5-axis4, second set** for axis 5 (corrected 2026-09-15): only disk1,
   disk2, diskCap ×2, shaft, shaft2, shaft3 and OPH (short). Its housing
   halves are Housing2Attach1/2, its output plate is axis6holder2 and its
   pulley is 80T-7mm, all in 6-axis5-6. No housing, housingNema or OPH2.
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
  **In hand 2026-09-15:** 40T ×2 and 20T ×2 (5 mm bore) and 232 belts ×5.
  308 belts ×3 ordered from AliExpress, 1-2 weeks. See the pulley table
  after phase E.
- ZZ or 2RS on any bearing: same dimensions, seal type is the only difference
- ~~3× NEMA17 dual-shaft (47 mm class) + 3× MKS SERVO42D (axes 4, 5, 6)~~
  **Bought 2026-09-11:** 4× 17HS8401B (42×42×48 mm, 1.8 A, 52 N·cm, Ø5
  front shaft 24 mm, Ø5 rear stub 10-13 mm, bare leads) for axes 4, 5, 6
  and 1, plus 1× MKS SERVO42C kit (board + matched motor). The 42C is the
  UART/step-dir board, not CAN: it is the mechanical reference for the
  rear-stub length and magnet gap, not the CAN bench unit. ~~Still to buy:
  3× SERVO42D boards~~ (dropped, see the driver pivot in §5).
  **Received 2026-09-15:** all four 17HS8401B. Rear stub measures 10 mm,
  the short end of the listed range, so no trimming is expected. Coil pairs
  by meter: green + red = phase A, yellow + blue = phase B (same on all
  four; keep that assignment when wiring the Octopus headers, one pair on
  each end of the 4-pin connector).

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
  plan is dropped pending that design. Coil pairs confirmed by meter
  2026-09-15: black + green = phase A, red + blue = phase B.

**Phase D, base**
- 6816zz ×2, 6804zz ×2, 625zz ×8, 606zz ×4
- M5×20 ×8, M6×50 ×8, M6×40 ×12, M6 nuts ×8
- 3M 30T pulley (5 mm bore) and belt. Settled 2026-09-28: the rotating
  base's band measures 175 teeth at 3 mm pitch in the Cults STL, the spider
  motor arm puts the motor axis at 139 mm, and that computes to 620 mm of
  belt, so a **621-3M, 10 mm wide** was ordered (the arm's slots cover 618
  to 627). The PDF's 648 was never bought; the 477-3M in hand is a phase E
  body belt and cannot reach round the ring at any centre distance.
  **Corrected 2026-10-22:** the printed band has 179 teeth, not 175. One
  commanded base turn at 175/27 landed 4 teeth short and 179/27 held TDC
  over five turns. The extra 4 teeth are why the belt was tight at 139:
  the 621 sits at 136.2 mm with the printed 27T (134.5 with a 30T), inside
  the tensioner arm's 134 to 138 travel.
- NEMA17: one of the four 17HS8401B already bought; driver channel on the daughterboard

**Phase E, body**
- 606zz ×8 (tensioners), M6 screws for the arms
- HTD477-3M belts ×4, 3M 20T (15 mm) ×1, 3M 30T (12 mm) ×3
  **Ordered 2026-09-15 (AliExpress, 1-2 weeks):** 3M 30T ×2 with 6.35 mm
  bore and 477-3M belts ×2. The other two 30T, the 20T and two belts were
  for the Omron encoders and are dropped.
- axis-2 NEMA23: bought, see phase C
- 24 V PSU and e-stop: see the Octopus bench notes in §5 (shore first,
  DeWalt 20 V pack as the mobile option)

**Pulleys and belt ratios (measured from the STLs, 2026-09-15).** Tooth
counts come from the printed pulleys' meshes (the three 80T files read
exactly 80, validating the method). The body pulleys are HTD 3M despite
their "GT2" file names. Motor pulley assignments for axes 2, 3 and 6 are
by inference (tensioners absorb the body belt length; axes 4 and 5 are
identical drives, so the 20T is the odd one out on axis 6); confirm on
the bench.

| Joint | Motor pulley | Driven pulley (printed) | Belt | Belt ratio | Reducer | Total |
|---|---|---|---|---|---|---|
| 1 | 3M 27T printed (`htd3m_pulley.py`), 5 mm D bore | 179T ring on rotatingBase1/2 | 621-3M | 6.63 | none | 6.63 |
| 2 | 3M 30T, 6.35 mm bore (printed, `htd3m_pulley.py`; the bought one was GT2 and skipped on the 3M belt) | axis2-GT2-stepper, 120T | 477-3M (462 without tensioner) | 4.0 | 1:23 | 92 |
| 3 | 3M 30T, 6.35 mm bore (printed, the axis 2 part) | axis3-GT2-stepper, 108T | 420-3M-9 (ordered 2026-10-26; centre distance measured 100, which computes 420.9. The 477 was 56 mm long, more than a tensioner can take up) | 3.6 | 1:20 | 72 |
| 4 | GT2 20T (fitted in place of the 40T) | axis4_80TGT2-7mm (80T counted, same as axis5-80T-7mm) | 308-2GT-6 | 4.0 | 1:11 (counted) | 88 measured, 44 expected (§4) |
| 5 | GT2 40T, 5 mm bore | axis5-80T-7mm | 308-2GT-6 | 2.0 | 1:11 | 22 |
| 6 | GT2 20T, 5 mm bore | axis5-pulley 72T, then 80T rotor | 308-2GT-6 + 232-2GT-6 | 3.6 x 80/72 = 4.0 | none | 4.0 |

Body belts are 9 or 10 mm wide (12 mm between the printed flanges); wrist
belts 6 mm. Centre distances from the plate geometry: axis 2 motor pocket
to joint 110 mm, axis 3 100 mm, matched by the two encoder pilots.

**Phase F, gripper:** hardware list is in the separate Cults gripper
project; the STLs show one 6804 and a T8 lead screw and nut.

## 4. Checks that gate phases

- ~~Ring-pin count~~ **Settled 2026-09-10:** the axis-2 housing halves have
  12 pin holes and the axis-3 holders 7 each (14). The PDF's "12 for 1:23,
  14 for 1:20" makes axis 2 the 1:23 and axis 3 the 1:20 (the profile is cut
  for 24 or 21 pin positions and only every other one, or two of three, is
  populated). The videos' "1:24" is this same joint.
  **The 1:11s (axes 4, 5, 6), counted 2026-10-26:** 11 lobes on the disk and 6 ring pins in a ring
  cut for 12 positions, every other one fitted. The ratio comes from the positions: 11 ÷ (12 − 11) =
  11:1, so axis 5 is 22:1 and axis 6 is 4:1. Open: axis 4 measured 88:1 against the 4 × 11 = 44
  expected. The belt is not the cause: `axis4_80TGT2-7mm` and `axis5-80T-7mm` both count 80 teeth,
  OD 50.42 (GT2), so a 20T gives 4:1. That leaves a factor of 2 in the motor or driver. Either MOTOR4
  runs 32 microsteps, not 16 (check MRES in `M122`), or axis 4's motor is a 0.9° (400 step) motor. It is a
  surplus-lot motor, so 0.9° is the likely answer.
  Check every axis before the POC run on MOTOR5.
- **Cap fit on axis 3**: confirm `axis2-diskCap` fits the axis-3 disks
  (same Ø80 recess and Ø57 pitch circle) with the first axis-3 disk print,
  before printing three more.
- **MKS board depth**: measure a SERVO57D; decide 41 mm NEMA23 vs a
  mainBody2 recess. Gates phase E. Measure a SERVO42D too for the gripper.
- **Rear-stub length**: measured 10 mm on the 17HS8401B (2026-09-15).
  Whether the stub carries an MT6701 magnet at all is decided by the
  daughterboard design (output encoders are the current plan), so leave
  the stubs uncut until Chopaka's interface contract says otherwise.
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
  base beside the node) is being designed in the Chopaka session as their
  PakaNode V2 board (DECISIONS.md D-087, 2026-09-12: MT6701 encoders,
  external-MOSFET TMC5160-class for the 2.8 A axes, our pin plan adopted,
  24 V entry with a local buck feeding the node's J2). The Cybot
  electronics spec is rewritten once its interface contract is published.
- **Interim bench driver: BTT Octopus Pro (2026-09-12).** Until the
  Chopaka daughterboard exists, the arm runs from an Octopus Pro in Marlin
  6-axis mode (X, Y, Z, I, J, K = joints 1-6), with the Heltec as G-code
  host keeping the planner, kinematics, host protocol and the encoder
  loop. Needs no J_GPIO1: the Heltec's GNSS port (8-pin SH1.25, buy a
  pre-crimped pigtail) supplies the GPIOs and the carrier's QWIIC jack the
  I2C.
  - GNSS port: GPIO39 TX / GPIO40 RX to an Octopus UART header at 250 kbaud,
    GND; GPIO41 e-stop status; GPIO38/42 spare (motion-done or sync line).
    Never use GPIO34 (GNSS power FET). No L76K plugged in.
  - QWIIC: TCA9548A at 0x70, seven MT6701 at 0x06 behind it, PCA9615
    differential I2C pair down the arm (base after the mux, elbow feeding
    the wrist). BME688 stays; addresses do not collide. ~1 kHz sweep.
  - Octopus: TMC5160 Plus with heatsinks for the two 2.8 A NEMA23 slots,
    TMC2209 for the NEMA17s; limit switches on Octopus endstop inputs and
    StallGuard via Marlin, not the carrier expander; 24 V in behind the
    e-stop copper; Octopus 5 V out to the carrier's J2 by pigtail.
  - Steps per degree per joint = motor steps x microsteps x total ratio /
    360, with the total ratios from the pulley table in §3 (6.63, 92, 72,
    88, 22, 4.0). At 200 steps and 16 microsteps: 58.9, 817.8, 640, 782.2,
    195.6, 35.6. `firmware/marlin/configure.py` has J1 at 58.93 (bench-checked
    2026-10-22) and J4 at 782.22 (2026-10-24: at 44:1 a commanded full turn
    came out a half, and 88:1 then held the mark over three turns; the belt
    and reducer stages multiply to 88, one of them is double the table's
    figure). J2, J3, J5 and J6 still carry the earlier placeholders
    (1.5 x 23, 1.5 x 20, 11, 1:10) until their motion tests.
  - Power, shore (bench, first): a 19.5 V 9.3 A laptop brick on a 5.5x2.5
    barrel-to-screw-terminal adapter (ordered 2026-09-14; meter the polarity,
    centre positive, and watch the barrel for heat above ~5 A). Same operating
    point as the DeWalt pack below. Upgrade: Mean Well LRS-350-24 (24 V,
    14.6 A; LRS-200-24 at 8.8 A is the floor). Expected draw with every
    axis moving is ~7 A. Feed the Octopus main input and the driver-power input from the
    same 24 V, but route only the driver input through the e-stop so a stop
    kills the motors and leaves the MCU, USB, encoder mux and node alive
    (verify the driver-power jumper and input labels on the board's
    silkscreen). E-stop contacts rated 24 V DC, 10 A+, in the positive lead.
    IEC inlet with fuse and switch; cover the open-frame supply's mains
    terminals.
  - Power, battery (mobile option, later): one DeWalt 20 V / FlexVolt pack on
    the 20 V tap (16-20.5 V) into both Octopus inputs, driver jumper on VIN.
    Same holding and low-speed torque, ~25 % less torque headroom at speed,
    not noticed on 30:1 joints; 9 Ah = ~160 Wh, over an hour of continuous
    motion. Pack has no cutoff: add a low-voltage disconnect at ~16.5 V, a
    20-30 A fuse on 14 AWG leads at a printed DeWalt adapter, and the e-stop
    in the driver lead. Upgrade path is a 300 W boost to 24 V, not a second
    pack: two packs in series (32-41 V) exceed the TMC2209s' 29 V and the
    main input's 24 V, and the 60 V tap sits above 62 V at full charge.
  - When Rev E arrives the pigtail moves to J_GPIO1; when the daughterboard
    arrives the Octopus goes and only the Heltec driver layer changes.
  - **Bench log 2026-09-21.** Board flashed from the SD card (21 Sep build)
    and driven from the Mac over USB-C at 250 kbaud. Quarter-turn tests at
    1.2 A, 1 unit = 1 motor degree, 10 deg/s, nothing saved with M500:
    all six sockets pass on the final crimped cables: MOTOR0/4/5/6
    (X/I/J/K) TMC2209 + 17HS8401B, MOTOR1 and MOTOR2_1 (Y/Z) TMC5160 +
    23HS22-2804S, clean both ways with the coil pairs from §3, each run
    twice. One MOTOR0 stutter cleared after a reseat and power cycle and
    did not return. Lessons:
    a TMC2209 socket needs UART mode (one jumper on the far-left two-pin
    position, nothing else; SPI mode is the row of four) or M122 reads
    "All LOW"; power both cords off before touching a motor plug or driver;
    TMC_DEBUG is off because its M122 table overran the 4 s watchdog on
    empty sockets. Next on the bench: direction per joint (INVERT_*_DIR)
    and steps/deg once each motor is on its belt. The board sits in the
    printed tray `model/electronics/octopus-pro-plate.stl`.
  - **Hand pin coupon 2026-09-23.** ISO 8752 4 × 20 spring pins (black
    steel) in the PLA fork coupon: the 3.90 bore is the fit, so
    `model/hand/params.json` carries `cheek_bore 3.90` and the phase 1
    finger parts were regenerated with it. The pin held the 5 kg axial
    pull in that bore without moving. Tongue coupon on a pin held in the
    3.90 fork: 4.1 felt too stiff for a knuckle, and the first printed
    proximal and distal at 4.3 still had to be drilled out to 11/64 in
    (4.37 mm) for free movement, so the params file carries
    `tongue_bore 4.37` (the library defaults stay 3.85/4.2). Sweep
    unchanged after regeneration.
  - **Axis 2 belt run 2026-09-30.** Axis 2's NEMA23 on MOTOR1 (Y, TMC5160)
    with the belt to the cycloid input: full turns at 1.2 A (`M906 Y1200`,
    `M92 Y8.89`, `G91`, `G1 Y360 F600`) showed too much belt slack; after
    tensioning it ran clean for 2 turns at 10 rpm and 5 turns in reverse at
    20 rpm. The firmware caps Y at 20 units/s (3.3 rpm in degrees); the
    fast runs used `M203 Y120` for the session, not saved. Put the cap in
    the config once the joint's test speed is settled.
  - **Spider arm first print 2026-09-24.** `spider-arm.stl` printed
    overnight on the A1 and came off the plate as two pieces: the tenon
    was a separate shell in the STL. The generator had unioned it to the
    arm's root face, where the section is only the 2 mm skin and the two
    rails at the edges, so nothing touched it, and the manifold check
    cannot see two clean shells. Fixed with a 6 mm root plate that the
    tenon grows out of and a one-shell assertion on every base part.
    Reprint the arm before the tenon dry-fit.
  - **Finger with straight channels 2026-09-24.** The tendon pulls
    cleanly through the new channels and the pulley motion works, but the
    knuckles, PLA turning on the 4 mm spring pins, need finesse and are
    not consistent joint to joint. Next print turns each knuckle on a
    Ø2 × 8 stainless dowel pressed into the tongue's core with 4 × 8
    spring pins sliding over it (steel on steel); the tongue bore becomes
    a 4.7 clearance. Dowels ordered, fit to be checked when they arrive.
  - **Dowel knuckles 2026-09-24 (later).** Test print of the proximal and
    distal: one Ø2 × 18 dowel per knuckle instead of two 8 mm ones. The
    tongue was drilled Ø2 right through, the dowel pushed in with the
    knuckle assembled, then a 4 × 8 spring pin driven in from each cheek
    over the dowel's ends. Very smooth movement. The model changes to a
    through bore and an 18 mm dowel; the sensor wire can no longer cross on
    the axis and moves to a slot over the dowel (see the wire entry that
    follows). Next: the palm front plate and the pair test (phase 2 plan
    Task 3).

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

## 7. V2 motor sizing, theoretical (2026-10-26)

Estimates for a lighter V2 built on the compact cycloid, scaled up joint by joint going down the
arm. Not measured: the 0.33 factor and the V2 masses are guesses until the POC bench run
(`docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md` §6) gives friction and stall
numbers.

**Method.** Usable output torque ≈ holding torque × ratio × 0.33: about half the holding torque is
left at working speed, and a printed belt plus cycloid runs at about 65 %. Joint loads are static,
arm held out flat. Shoulder to elbow is 249 mm (V1 model, joint centres z 204 and 453); elbow to
wrist 230 mm is a guess. V2 head about 1.1 kg: axis 5 module 300 g at the wrist axis, axis 6 module
300 g at 50 mm, gripper 300 g at 110 mm, payload 200 g at 150 mm.

| Motor | Holding | Mass | Usable at 40:1 | Usable at 60:1 (3:1 belt) |
|---|---|---|---|---|
| 20–23 mm pancake | ~0.13 N·m | ~130 g | ~1.7 N·m | ~2.6 N·m |
| 34 mm | ~0.28 | ~220 g | ~3.7 | ~5.5 |
| 40 mm | ~0.45 | ~280 g | ~5.9 | ~8.9 |
| 48 mm (17HS8401B, in hand) | ~0.52 | ~360 g | ~6.9 | ~10.3 |
| 60 mm | ~0.70 | ~500 g | ~9.2 | ~13.9 |
| NEMA23 56 mm (23HS22, in hand) | 1.26 | ~700 g | ~16.6 | ~25 |

| Joint | Load, arm flat | Suggested motor | Margin |
|---|---|---|---|
| 6, wrist roll | almost no gravity load | pancake, 40:1 | plenty |
| 5, wrist pitch | ~0.8 N·m | pancake, 40:1 | ~2× |
| 4, forearm roll | small | pancake, 40:1 | plenty |
| 3, elbow | ~4.1 N·m | 48 mm, 40:1 | ~1.7× |
| 2, shoulder | ~10.6 N·m | NEMA23, 40:1 (or 60 mm at 60:1, ~1.3×) | ~1.6× |

- Every 100 g off the head takes about 0.3 N·m off the elbow and 0.5 N·m off the shoulder. The V1
  head alone (about 2.1 kg, about 0.5 m out) puts about 10 N·m on the shoulder, which is the whole
  V2 shoulder load.
- Moving the elbow motor down to the shoulder, belted up to the elbow, takes about 0.9 N·m off the
  shoulder.
- Pancakes on axes 4–6 hold only if the POC's friction comes in low. If a pancake can't turn the
  unloaded POC at low current, step up to 34 mm.
- Speed: a motor at 300 rpm gives about 45°/s at 40:1 and 30°/s at 60:1. Fast moves add inertial
  load on top of these static figures.
- Bigger joints need a scaled cycloid: more lobes or bigger pins, and 6806 or 6808 in place of the
  6804. Each is a new parameter set for the same generator.
- **Axis 4 roll, V2:** use 2 × 6810 (50 × 65 × 7, about 50 g each) in place of V1's 2 × 6812zz
  (60 × 78 × 10, about 105 g each), saving about 110 g. These are the wrist-pulley bearings already in
  hand (2RS). The 50 mm bore leaves a hollow roll axis for the axis 5, axis 6 and gripper cables.
- **Wrist modules, V2:** 6 × 6705-2RS in hand (25 × 32 × 4, about 8 g each) can replace the POC's
  6804 main bearings. They share the 6804's Ø32 OD, so the proven Ø32.00 seat stays. The hub grows to
  Ø25 and the housing shortens by about 6 mm. Check the ring lands for the lip and shoulder first.
