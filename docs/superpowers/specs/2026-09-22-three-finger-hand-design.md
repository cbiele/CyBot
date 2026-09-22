# Three-finger hand

**Date:** 2026-09-22
**Status:** Draft for founder review
**Decided inputs (design conversation 2026-09-22):** three fingers, two opposed
by a thumb; two motors, a gear-driven NEMA11 for the pair and a direct-drive
28BYJ-48 for the thumb, both on the Octopus Pro; fingers 20 mm wide on
ISO 8752 4 × 20 mm stainless slotted spring pins with the sensor wires routed
through the pins; PLA body, TPU skins, stainless where a printed part would
fail; four FSR channels per the tactile spec
(`2026-09-21-gripper-tactile-sensing-design.md`), three fingertips and a palm
pad; target objects from a marker pen to a coffee mug, up to 500 g. Replaces
the Cults four-finger gripper from the `OPH_To_Gripper` adapter forward.

---

## 1. Goal

A printable hand that grasps everyday objects with a self-locking power
grasp, positions a thumb precisely enough to probe and pinch, and carries the
tactile sensing already specified, all controlled from the Octopus Pro today
and the Heltec host later.

## 2. Why this shape

- **Two motors split the job.** The pair delivers force through a worm, so
  the grasp holds unpowered. The thumb is direct-driven for exact position
  and a light touch. Neither has to do the other's work.
- **Underactuation without electronics.** A whiffletree between the two
  pair tendons lets the fingers close unequally around an odd shape and still
  share the load. That is what makes a grasp forgiving before any sensor
  fires.
- **Print-in-place ideas only where they pay.** The articulated-dragon trick
  of clearance joints is used for nothing load-bearing. Knuckles that carry
  the pinch get stainless pins in printed bores.
- **Wires through the pins.** A wire crossing a joint on the axis of rotation
  twists a few degrees instead of bending, so it never fatigues. Slotted
  spring pins are hollow, self-retaining and open at both ends, which makes
  them the conduit as well as the hinge.

## 3. Scope

In: fingers, thumb, palm, both drives, wiring to the ADC, Marlin axes,
print rules, bench acceptance, phases.

Out: the tactile firmware and force loop (already specified), slip detection,
any change to the wrist joints. The Cults `OPH_To_Gripper` adapter is reused,
not redesigned; one drilling note applies (§5.6).

## 4. Architecture

```
wrist  ── OPH_To_Gripper (Cults, 55 mm tube) ── palm flange Ø62
                    NEMA11 inside the tube ──▶ worm ──▶ 20T wheel + spool
                                                   └─▶ whiffletree ─▶ two pair tendons
           28BYJ-48 on the palm wall ──▶ thumb hub, hard stop at pinch
           FSR ×3 tips + palm pad ──▶ wires through pins ──▶ ADS1115 in the palm
                                                   └─▶ one QWIIC cable down the arm
```

## 5. Hardware design

### 5.1 Pair fingers

| Item | Value |
|---|---|
| Phalanges | proximal 40 mm, distal 30 mm, 20 mm wide, 12 mm tall, PLA |
| Knuckles | two per finger, 90° curl each, printed stop |
| Fork / tongue | two 5 mm cheeks, 9 mm tongue, 0.5 mm clearance each side |
| Pin | ISO 8752 4 × 20 mm, stainless 1.4310, slot toward the tongue |
| Cheek bore | 3.85 mm nominal; coupon at 3.80, 3.85, 3.90 sets the build value |
| Tongue bore | 4.2 mm |
| Tendon channel | 2 mm, on the palm side, 6 mm off each knuckle axis |
| Wire channel | 1.5 mm, beside the tendon channel |
| Return | TPU strip 8 × 2 mm along the back, printed flat, clipped into a slot on each phalanx; length sets the open pretension |

Tendon: 0.5 mm stainless leader wire, crimped with a fishing ferrule into a
pocket at the fingertip and to the whiffletree at the other end. Full curl of
both knuckles takes about 19 mm of tendon.

### 5.2 Thumb

One rigid curved segment, 60 mm long, 20 mm wide, PLA, no knuckle. Its hub
takes the 28BYJ-48's 5 mm D-shaft on one side and carries a hollow Ø6 stub on
the other, running in a bore in the far palm wall, through which the thumb's
sensor wire passes on the axis. A printed boss on the palm wall is the hard
stop at the pinch angle: the thumb drives to the stop, the pair closes against
it, and the pinch load goes into PLA instead of the motor's plastic gears.

### 5.3 Palm

Two PLA halves split on the spool axis, closed with two M3 × 20 and nuts.
About 60 mm wide, 50 mm deep, 50 mm tall on a Ø62 rear flange. Contents:

- worm, wheel, spool and whiffletree on the pair side (§5.4)
- the 28BYJ-48 by its two ear tabs on the inside of the thumb-side wall, M4
  × 8 into printed bosses, shaft through the wall
- palm pad pocket on the front face between the finger roots, FSR 402 under
  2 mm TPU
- ADS1115 slot behind the palm pad, with a cavity where all four sensor pairs
  and the 3.3 V and ground gather
- rear cavity for the NEMA11 leads, the thumb leads and the QWIIC cable to
  exit together through a Ø14 hole in the flange, which lines up with the
  Ø14 hole already in the adapter's rear wall

### 5.4 Pair drive

| Item | Value |
|---|---|
| Motor | NEMA11, 32 mm long class, about 120 mN·m, 0.67 A |
| Worm | printed, module 1, single start, Ø10 pitch, 20 mm long, grub-screw hub on the 5 mm shaft |
| Wheel | printed, 20 teeth, module 1, 20:1 |
| Self-locking | lead angle about 6°, below the PLA friction angle, so the grasp holds unpowered |
| Spool | Ø16, on the wheel's axis, parallel to the finger knuckles; one tendon |
| Whiffletree | 20 mm floating bar on a 4 × 20 spring pin; spool tendon at the centre, finger tendons at the ends |
| Close time | about 1.5 s at 300 rpm (a third of a spool turn) |
| Tension | up to about 50 N per finger at full current; the current setting is the force limit |

The motor sits inside the `OPH_To_Gripper` tube, which is 55 mm deep and
about Ø60 inside (it held a NEMA17), bolted to the palm's back wall on the NEMA11 pattern (23 mm
square, M2.5). Its 20 mm shaft passes through the wall into the palm where
the worm meshes with the wheel.

### 5.5 Sensors and wiring

- Fingertip caps: PLA, two M2 into the distal phalanx, FSR 400 in a pocket
  with tail relief, 3 mm dome over its centre, 1.5 mm TPU skin snapped over a
  lip. Same cap on the thumb.
- Palm pad: FSR 402 under 2 mm TPU in the front-face pocket.
- Wire: 30 AWG PTFE, two per sensor, through the pins. At each knuckle the
  wire enters the pin's open end from a channel in the cheek, runs inside to
  mid-length, exits through the slot into a 4 mm chamber in the tongue where
  the twist happens, then up the 1.5 mm channel. Chamfer the slot exit; the
  wire must never be pinched between slot and bore.
- ADS1115 breakout (Adafruit 1085) in the palm slot, address 0x48, four 10 kΩ
  dividers soldered on its pins, one QWIIC cable out the back. This moves the
  ADC from the wrist (tactile spec §5.3) into the palm; the spec's electrical
  design is otherwise unchanged.

### 5.6 Wrist interface (measured from the STLs)

`OPH_To_Gripper` runs 77 mm along the hand axis. Its rear face carries the
6812 boss and six Ø4.2 holes on a 22 mm radius for the wrist; that end is
untouched. Its front face is a Ø62.6 ring; the tube behind it is 55 mm deep,
where the Cults NEMA17 sat. The Cults `mainHolder` met it with a Ø62 back
face carrying the NEMA17 pattern (Ø3 on a 31.6 mm square) and a Ø30 centre.

The palm's rear flange copies that Ø62 face. It is fixed to the adapter by
four M3 × 12 through the adapter's front ring at a 27 mm radius, 45° off the
finger plane. The adapter has no holes there: drill four Ø3.2 on assembly, or
reprint the adapter with them. The NEMA11 inside the tube bolts to the flange
from the tube side, so the adapter must be fitted before the motor.

### 5.7 Stainless and other non-printed parts

| Part | Qty | Approx. |
|---|---|---|
| ISO 8752 4 × 20 stainless spring pins (4 knuckles + whiffletree + 1 spare) | 6 | $5 |
| 0.5 mm stainless leader wire and crimp ferrules | 1 m, 10 | $8 |
| NEMA11, 32 mm, 0.67 A | 1 | $20 |
| 28BYJ-48 (in hand), converted to bipolar | 1 | — |
| TMC2209 with UART jumper | 2 | $20 |
| FSR 400 ×3, FSR 402 ×1, ADS1115 breakout, 10 kΩ ×4 | 1 set | $45 |
| 30 AWG PTFE wire, QWIIC cable, M2/M3/M4 stainless hardware, two microswitches | 1 set | $15 |

About $115 beyond filament.

## 6. Firmware (Marlin on the Octopus, then the Heltec)

Two new axes, both TMC2209 in UART mode, added through `configure.py`:

| | Pair | Thumb |
|---|---|---|
| Socket | MOTOR7 (Marlin's E3 slot, taken by the next free axis) | MOTOR3, Z2 pins reassigned to the axis |
| Axis, G-code letter | U | V |
| Current | 600 mA | 250 mA |
| Unit and steps | mm of tendon, about 1270 steps/mm (200 × 16 × 20 / 16π) | thumb degrees, 91 steps/deg (bipolar 28BYJ-48 at 16 microsteps) |
| Travel | 0 to 20 mm | 0 to 90° |
| Homing | microswitch at open, spare endstop input | microswitch at the open stop, spare endstop input |
| Max speed | 15 mm/s | 90°/s |

The 28BYJ-48 conversion is the one in the firmware README: cut the trace to
the red centre-tap wire; orange and pink one coil, yellow and blue the other.

On the Heltec, `grip` maps to a U move with the force stop from the tactile
spec, and a `thumb` field or a separate command sets V. The thumb parks on
its hard stop before a pinch so the pair loads the stop, not the motor.

## 7. Print rules

- Phalanges and thumb print lying on a cheek so every pin bore is vertical
  and round. Tendon and wire channels are then horizontal and get a teardrop
  top.
- Palm halves print open face up; the worm prints standing on its hub with a
  brim; the wheel and spool print flat.
- PLA at 0.2 mm, four walls, 40 % infill in phalanges and palm; 100 % in the
  worm and wheel.
- TPU parts (three skins, four return strips, palm pad) print separately at
  0.2 mm, 95A.
- No supports anywhere by design; a part that needs them is a design error.

## 8. Risks

- **Pin press fit in PLA.** Too tight splits a cheek, too loose walks out.
  The coupon in phase 1 exists for this, and a 4 mm pin in 5 mm cheeks is the
  most forgiving version of the joint.
- **Printed worm wear.** PLA on PLA at 50 N tendon loads will wear; 100 %
  infill and a little PTFE grease. If it wears fast, the wheel becomes the
  sacrificial part, one gram to reprint.
- **Thumb gearbox.** The 28BYJ-48's plastic train strips near 0.1 N·m. The
  hard stop and the tactile force limit are the protection; a pinch
  without the thumb on its stop is a firmware bug.
- **Wire twist at the pins.** Rated for the 90° twist, but the chamber must
  give the wire room. Verified on the phase 1 finger with a hundred cycles.
- **Adapter drilling.** Four holes in a Cults part; a reprinted adapter with
  the holes removes the risk of a misdrilled one.

## 9. Rejected alternatives

- **Two 28BYJ-48s.** The pair would take over a minute to close through a
  self-locking worm and hold about 1 N per fingertip.
- **NEMA17 for the pair.** Torque to spare, but 340 g at the wrist and no
  room inside the adapter tube alongside the thumb motor.
- **Hobby servo for the thumb.** Simpler control, but not a stepper on the
  Octopus, and no better force than the 28BYJ-48 at the tip.
- **Print-in-place knuckle pins.** Fine for a dragon, not for a joint that
  carries a pinch and has a wire through it.
- **Single spool without a whiffletree.** Couples the pair rigidly; the hand
  would only ever touch an object with one finger.
- **ADC at the wrist.** The palm has the room, and one cable across the wrist
  beats five.

## 10. Acceptance (bench)

1. Coupon: one bore size holds a 4 × 20 pin under a 5 kg pull without
   splitting; that size goes into the finger files.
2. One pair finger on a string: curls fully, returns to open on its own,
   100 cycles with a sensor wire through both pins and continuity intact.
3. Pair on the palm shell, hand-turned spool: wraps an 80 mm mug, pinches a
   10 mm pen, one finger blocked by a wedge and the other still closes.
4. NEMA11 drive on Marlin U: closes in under 2 s, holds a 500 g mug with the
   motor disabled, current at 400 mA does not crush an empty drink can.
5. Thumb on Marlin V: homes, reaches the stop, pinch of a pen against the
   stop with the pair at 400 mA, no gear slip after 20 pinches.
6. Sensors: the tactile spec's acceptance 1 to 3 on the finished hand.
7. Mounted on the wrist: full wrist roll at speed with the mug held.

## 11. Phasing

1. Coupon, then one pair finger with TPU return and a wire through the pins.
2. Both pair fingers, palm shell, whiffletree, hand-turned spool.
3. NEMA11, worm and wheel, U axis in `configure.py`, close and hold.
4. 28BYJ-48 conversion, thumb, hard stop, V axis, pinch.
5. Caps, skins, palm pad, ADS1115 in the palm, tactile spec phases.
6. Adapter drilled or reprinted, hand on the wrist.

## 12. Open items

- NEMA11 part choice: the 32 mm, 0.67 A class; confirm shaft length is
  20 mm so the worm clears the palm wall.
- Whether to reprint `OPH_To_Gripper` with the four flange holes instead of
  drilling.
- Palm pad thickness versus the mug wrap: 2 mm TPU is a starting point.
- The Heltec `thumb` command shape, to be added to the electronics spec when
  that spec is rewritten for the PakaNode.
