# Three-finger hand

**Date:** 2026-09-22
**Status:** Draft for founder review
**Decided inputs (design conversation 2026-09-22):** three fingers, two opposed
by a thumb; two motors, a gear-driven NEMA11 for the pair and a direct-drive
28BYJ-48 for the thumb, both on the Octopus Pro; fingers 23 mm wide on
pairs of ISO 8752 4 × 10 mm stainless spring pins with the sensor wires and
the tendon in straight channels down the finger (amended 2026-09-24, see
§5.1 and §5.5); PLA body, TPU skins, stainless where a printed part would
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
- **Wires on the axis, tendon straight (amended 2026-09-24).** Each knuckle
  is two short pins pressed in from either cheek with a 3 mm gap between
  their ends, and the sensor pair crosses the joint on the axis line through
  that gap, bending about the axis in an open pocket instead of flexing over
  an edge. The tendon runs in an enclosed straight channel 4 mm below the
  axis line, so with the finger straight both are one straight push from
  the fixture to the tip and nothing zig-zags.

## 3. Scope

In: fingers, thumb, palm, both drives, wiring to the ADC, Marlin axes,
print rules, bench acceptance, phases.

Out: the tactile firmware and force loop (already specified), slip detection,
any change to the wrist joints. The Cults `OPH_To_Gripper` adapter is reused,
not redesigned; one drilling note applies (§5.6).

## 4. Architecture

```
wrist  ── OPH_To_Gripper (Cults, 55 mm tube) ── palm flange Ø62
        NEMA11 worm-gear unit, motor in the tube ──▶ 20:1 gearbox in the palm ──▶ spool
                                                   └─▶ whiffletree ─▶ two pair tendons
           28BYJ-48 on the palm wall ──▶ thumb hub, hard stop at pinch
           FSR ×3 tips + palm pad ──▶ wires through the knuckles ──▶ ADS1115 in the palm
                                                   └─▶ one QWIIC cable down the arm
```

## 5. Hardware design

### 5.1 Pair fingers

| Item | Value |
|---|---|
| Phalanges | proximal 40 mm, distal 30 mm, 23 mm wide (amended 2026-09-24, was 20), 12 mm tall, PLA |
| Knuckles | two per finger, 90° curl each, printed stop |
| Fork / tongue | two 5 mm cheeks, 12 mm tongue, 0.5 mm clearance each side |
| Pins (amended 2026-09-24) | two ISO 8752 4 × 8 mm stainless spring pins per knuckle, one pressed flush from each cheek face, reaching 2.5 mm into the tongue; and two Ø2 × 8 stainless dowels pressed into the tongue's core, standing 6.5 mm proud inside the spring pins. The spring pin turns on the dowel, steel on steel; the tongue never touches the spring pin |
| Cheek bore | 3.90 mm through (the 2026-09-23 coupon value) |
| Tongue bores | Ø4.7 clearance from each face, 2.5 deep, round the spring pin; then Ø2.0 press for the dowel, from 3.5 to 2.0 mm off the centre plane. The 3 mm between the dowel ends is the wire gap |
| Wire channel | Ø1.8 enclosed, on the axis line down the centre of the finger, straight from the tip to the base; it crosses each knuckle through the gap between the pin ends |
| Tendon channel | Ø2 enclosed, on the centre plane 4 mm below the axis line, straight the length of each phalanx; at each tongue it opens into a 3 mm slot between the pin ends that runs from the rounded end to a flared mouth 4 mm past the axis |
| Return | TPU strip 8 × 2 mm along the back, printed flat, clipped into a slot on each phalanx; length sets the open pretension |
| Grip pad (added 2026-09-22) | snap-on TPU pad on the proximal's inside face, 14 mm long, lips into side grooves and two front dots into dimples; the distal's grip surface is the skin's wrap (§5.5) |

Tendon (amended 2026-09-24): 0.5 mm stainless leader or 20 lb braided line.
It enters the fixture or palm at the back and runs in one straight line to
the distal, where the channel ends in an open pocket in the palm face 8 to
15.5 mm past the knuckle; a knot or crimp bigger than the channel stops
against the pocket's rear wall. At each knuckle the tendon crosses the fork
gap free, then enters the tongue's flared mouth 4 mm past the axis. The
mouth sits that far past the axis so the free span stays at least 4 mm palmar
of the axis at every angle, which keeps the tendon curling the joint right up
to 90°, where it turns the full 90° over the mouth's cone. Full curl of both
knuckles takes about 16 mm of tendon.

### 5.2 Thumb

One rigid curved segment, 60 mm long, 20 mm wide, PLA, no knuckle. Its hub
takes the 28BYJ-48's 5 mm D-shaft on one side and carries a hollow Ø6 stub on
the other, running in a bore in the far palm wall, through which the thumb's
sensor wire passes on the axis. A printed boss on the palm wall is the hard
stop at the pinch angle: the thumb drives to the stop, the pair closes against
it, and the pinch load goes into PLA instead of the motor's plastic gears.

### 5.3 Palm

Two PLA halves split on the spool axis, closed with two M3 × 20 and nuts.
About 60 mm wide, 65 mm deep, 50 mm tall on a Ø62 rear flange. Contents:

- the pair drive's gearbox on a web, with the spool and whiffletree in
  front of it (§5.4)
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
| Motor | JUGETEK 28H51-WG20 (amended 2026-09-23, two bought): NEMA11, 51 mm body, 98 mN·m holding, 3.1 Ω, 1.9 mH, with an integral metal 20:1 worm gearbox |
| Gearbox | 46 × 32 × 30 mm; output at right angles to the motor: Ø8 shaft with a 7 mm flat, 20 mm long, on a Ø15.3 × 2 boss; 4 × M3, 5 deep, on 33 × 20 around the shaft |
| Self-locking | single-start steel worm at 20:1, so the grasp holds unpowered (checked in acceptance 4) |
| Spool | Ø16, on the output shaft with an M3 grub screw on the flat, parallel to the finger knuckles; one tendon |
| Whiffletree | 20 mm floating bar on a 4 × 20 spring pin; spool tendon at the centre, finger tendons at the ends |
| Close time | about 1.5 s at 300 rpm (a third of a spool turn) |
| Tension | about 0.8 N·m at the shaft, so up to about 50 N per finger at full current; the current setting is the force limit |

The gearbox sits in the palm, bolted from behind to a 4 mm web in the
pair-side half by four M3 × 8, the boss in a Ø15.5 hole; the spool runs on the
front of the web. The motor points back through a 30 mm square opening in the
flange into the `OPH_To_Gripper` tube, which is 55 mm deep and about Ø60
inside (it held a NEMA17); the 51 mm body and its rear shaft reach about
52 mm past a 4 mm flange, so the rear wall clears by about 3 mm. The printed
worm and wheel this replaces were a wear risk and a mesh-alignment risk; a
Ø12 spool is the fallback if the gearbox turns out less efficient than the
40 % assumed.

### 5.5 Sensors and wiring

- Fingertip skin (amended 2026-09-22): the return strip and the fingertip
  skin are one TPU part. Its dorsal run is the return spring, it wraps the
  R6 tip, and its palmar pad covers an FSR 400 pocket on the distal's inside
  face, with a 1.5 mm dome moulded into the pad over the sensor, ending in a
  T bar held by two M2 screws either side of the tendon's anchor pocket. No
  PLA cap.
  Same arrangement on the thumb.
- Palm pad: FSR 402 under 2 mm TPU in the front-face pocket.
- Wire (amended 2026-09-24): 30 AWG PTFE, two per sensor, as a pair in one
  Ø1.8 channel on the axis line, straight from a solder pocket at the very
  tip of the distal to the back of the fixture or palm. The sensor's tail
  runs to that pocket in a 0.6 mm groove round the tip, and the pair is
  pushed in at the tip, knotted there and soldered to the tail last, all
  under the skin's tip wrap. At each knuckle the channel passes through the
  3 mm gap between the two pin ends. On the tongue side it opens into a
  pocket that takes up the rear palm-side quarter of the tongue between the
  pin ends; that quarter faces the fork web from full extension to 90° of
  curl, so the pair has about 8 mm of free length there to bend about the
  axis at a radius near 3 mm, and nothing pinches it. Channel mouths are
  flared to a cone. Threading order no longer matters: with the finger
  straight the channel is one line, so the pair goes in with the pins
  already pressed.
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
reprint the adapter with them. The gearbox is bolted inside the palm first and
the motor slides into the tube as the palm goes on, so the adapter can be
fitted in either order.

### 5.7 Stainless and other non-printed parts

| Part | Qty | Approx. |
|---|---|---|
| ISO 8752 4 × 10 stainless spring pins (two per knuckle, 8, + 2 spare) | 10 | $5 |
| ISO 8752 4 × 20 stainless spring pin (whiffletree + 1 spare) | 2 | $2 |
| 0.5 mm stainless leader wire and crimp ferrules | 1 m, 10 | $8 |
| NEMA11 worm-gear unit 28H51-WG20 (in hand, two) | 1 | $49 |
| 28BYJ-48 (in hand), converted to bipolar | 1 | — |
| TMC2209 with UART jumper | 2 | $20 |
| FSR 400 ×3, FSR 402 ×1, ADS1115 breakout, 10 kΩ ×4 | 1 set | $45 |
| 30 AWG PTFE wire, QWIIC cable, M2/M3/M4 stainless hardware, two microswitches | 1 set | $15 |

About $145 beyond filament.

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
- Palm halves print open face up; the spool prints flat.
- PLA at 0.2 mm, four walls, 40 % infill in phalanges and palm; 100 % in the
  spool.
- TPU parts (three skins, four return strips, palm pad) print separately at
  0.2 mm, 95A.
- No supports anywhere by design; a part that needs them is a design error.

## 8. Risks

- **Pin press fit in PLA.** Too tight splits a cheek, too loose walks out.
  The coupon in phase 1 exists for this, and a 4 mm pin in 5 mm cheeks is the
  most forgiving version of the joint.
- **Gearbox efficiency.** The 40 % worm efficiency is an assumption; the
  tendon target has a 2× margin on it and the Ø12 spool is the fallback.
  Backlash does not matter, the tendon only pulls.
- **Thumb gearbox.** The 28BYJ-48's plastic train strips near 0.1 N·m. The
  hard stop and the tactile force limit are the protection; a pinch
  without the thumb on its stop is a firmware bug.
- **Tendon over the mouth cone.** At full curl the tendon turns 90° over
  the flared mouth of the distal's channel, so that PLA cone takes the
  tendon's full tension on a small radius. Wear there is what the phase 1
  hundred cycles look for; a stainless or PTFE liner in the mouth is the
  fix if it grooves.
- **Dowel grip.** Each Ø2 dowel is held by only 1.5 mm of PLA between the
  clearance bore's floor and its own; that is the whole of its retention,
  and the bore prints about 0.1 mm under size, so 2.0 may need a 5/64 in
  drill. The dowel cannot leave the joint while the spring pin is in, and
  the spring pin's bore is about 2.3 mm, so expect about 0.15 mm of play at
  the tongue. A dowel that spins in the tongue instead of the spring pin
  still turns steel on PLA and still beats the old bore.
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
   100 cycles with a sensor wire through both knuckles and continuity intact.
3. Pair on the palm shell, hand-turned spool: wraps an 80 mm mug, pinches a
   10 mm pen, one finger blocked by a wedge and the other still closes.
4. NEMA11 drive on Marlin U: closes in under 2 s, holds a 500 g mug with the
   motor disabled, current at 400 mA does not crush an empty drink can.
5. Thumb on Marlin V: homes, reaches the stop, pinch of a pen against the
   stop with the pair at 400 mA, no gear slip after 20 pinches.
6. Sensors: the tactile spec's acceptance 1 to 3 on the finished hand.
7. Mounted on the wrist: full wrist roll at speed with the mug held.

## 11. Phasing

1. Coupon, then one pair finger with TPU return and a wire through the knuckles.
2. Both pair fingers, palm shell, whiffletree, hand-turned spool.
3. Worm-gear NEMA11 on the palm web, spool, U axis in `configure.py`, close
   and hold.
4. 28BYJ-48 conversion, thumb, hard stop, V axis, pinch.
5. Caps, skins, palm pad, ADS1115 in the palm, tactile spec phases.
6. Adapter drilled or reprinted, hand on the wrist.

## 12. Open items

- Rated current of the 28H51 is not on the listing; read it off the motor
  label for the U axis `M906` (3.1 Ω suggests 0.67 A).
- Whether to reprint `OPH_To_Gripper` with the four flange holes instead of
  drilling.
- Palm pad thickness versus the mug wrap: 2 mm TPU is a starting point.
- The Heltec `thumb` command shape, to be added to the electronics spec when
  that spec is rewritten for the PakaNode.
