# Gripper tactile sensing

**Date:** 2026-09-21
**Status:** Draft for founder review
**Decided inputs:** four-finger printed gripper on a T8 lead screw, one stepper
(build plan phase F); Heltec V4 on the PakaNode carrier Rev E is the host and
already runs an I²C sweep over the QWIIC chain (TCA9548A mux, MT6701 encoders,
PCA9615 differential pairs down the arm; build plan §5); the carrier exposes no
ADC-capable pin to Cybot (J_GPIO1 and the GNSS port are GPIO26 and 38-45, all
digital-only on the ESP32-S3); the Octopus Pro is an interim driver and never
reads sensors.

**Assumptions made in this draft, to confirm:** all four fingers get a pad
(not two); the ADC is a 16-bit ADS1115 rather than the 12-bit ADS1015; contact
detection lives on the Heltec only, with no StallGuard on the gripper driver.

---

## 1. Goal

Give the gripper a sense of touch: know which fingers are in contact with an
object and roughly how hard each is pressing, so a close can stop at a chosen
force instead of at a fixed lead-screw position, and so the host can tell an
empty grip from a held object.

## 2. Why this shape

- Analogue signals cannot come back to the node. No pin the carrier gives
  Cybot has an ADC, and the fingers are about 600 mm of cable from the base,
  running beside six stepper leads. A few hundred millivolts from a pad would
  not survive that. I²C over the PCA9615 pair already reaches the wrist.
- The sweep exists. Adding one more device behind the mux costs a driver and
  two fields in host state; it changes nothing on the Octopus or on the
  PakaNode daughterboard that replaces it.
- Force-sensing resistors are the cheapest sensor that gives a graded signal
  on a printed finger. They are not accurate force gauges, and this spec does
  not pretend they are: the output is a per-finger contact flag and a
  normalised pressure, calibrated by tare, good to perhaps 20 %.

## 3. Scope

In: four pads, one ADC at the wrist, the Heltec driver and sweep entry, the
host-state fields, a force-limited `grip` command, bench acceptance.

Out (later specs if wanted): slip detection, absolute grip force from a load
cell on the lead-screw nut, tactile arrays, anything on the Octopus side.

## 4. Architecture

```
finger pad (FSR 402) ×4 ── 10 kΩ divider ×4 ── ADS1115 @0x48 (wrist)
                                                    │  QWIIC, wrist segment
                                          PCA9615 pair (elbow → wrist)
                                                    │
                                     TCA9548A @0x70, channel = wrist
                                                    │
                                     Heltec sweep (~1 kHz frame)
                                                    │
                            host state: touch[4], contact[4], grip_force
                                                    │
                                  grip command with force target
```

The ADS1115 sits on the same wrist QWIIC segment as the axis-5/6 MT6701s, so
it needs no new cable run down the arm, only a short lead from the wrist board
out to the four pads.

## 5. Hardware design

### 5.1 Sensor

Interlink FSR 402 (18.3 mm round active area, 0.1 N to 10 N usable range,
flat flexible tail). Resistance falls from over 1 MΩ open to a few kΩ at full
squeeze. If the printed pad face turns out narrower than 20 mm, the FSR 400
(5.6 mm active) on a smaller dome is the fallback; same electrical treatment.

### 5.2 Mounting on the finger

Each `grip` finger gets a printed pad cap: a shallow pocket for the FSR body
with a 1 mm relief for the tail, and a 3 mm hemispherical dome on the contact
side that sits over the centre of the active area. The dome matters: an FSR
under a flat face reads mostly edge load and drifts; a dome concentrates the
contact into the sensing zone and makes the reading repeatable. The cap is
glued or screwed to the existing pad face; the FSR is held by its own adhesive
backing under the cap. A 1 to 2 mm TPU skin over the dome (printed, or cast
if a mould is handy) spreads the contact, protects the FSR and gives the
finger some grip, the way the Yale OpenHand pads use cast urethane. Tails
route along the inside of the finger to a 4-pin JST at the finger root, then
to the wrist board.

### 5.3 ADC and conditioning

Adafruit ADS1115 breakout with STEMMA QT (QWIIC-compatible) connectors, address
0x48 (ADDR to GND), powered at 3.3 V from the QWIIC bus. Each FSR is the top
half of a divider: 3.3 V → FSR → ADC input, with a 10 kΩ fixed resistor from the
input to ground. Output rises with force, from near 0 V open to about 2.5 V at
full squeeze. Gain ±4.096 V, single-ended on AIN0 to AIN3, one per finger.
Continuous mode is not used; the sweep issues single-shot conversions round
robin so the bus is never held.

### 5.4 Wiring

- Wrist board to pads: one 6-way lead (3.3 V, GND, four signals) with the
  10 kΩ resistors at the ADC end, so only the FSR leads flex. Twist each
  signal with GND where the lead passes the gripper motor.
- Wrist board on the bus: chained on the existing wrist QWIIC segment after the
  MT6701s. No pull-up change; the breakout's 10 kΩ pull-ups are removed if the
  segment already has its own (check on the bench with the PCA9615 in place).

### 5.5 Power

ADS1115 draws about 150 µA. Each divider draws at most 0.33 mA at full
squeeze. Total is under 2 mA from the 3.3 V QWIIC rail, well inside what the
PCA9615 segment already carries.

## 6. Firmware design (ESP-IDF, on the Heltec)

- **Driver.** `ads1115.c`: config-register write, single-shot start, ready
  poll or fixed 1.2 ms wait at 860 SPS, conversion read. Host-testable codec
  for the register packing; I²C exercised on hardware only, like the MT6701.
- **Sweep entry.** The existing mux sweep gains a wrist-channel step that
  starts one ADS1115 conversion and collects the previous one, cycling AIN0 to
  AIN3. Four channels at 860 SPS gives each finger about 200 readings per
  second, more than the grip loop needs, without stealing time from the
  encoders.
- **Calibration.** Tare: on every open-limit hit the current reading of each
  finger is stored as its zero. Scale: one per-finger full-scale count stored
  in NVS via `set` (`"key":"touch_fs"`), taken by squeezing each finger to the
  reference load once at commissioning. `touch[i]` = (raw − zero) / fs,
  clamped 0 to 1. `contact[i]` = `touch[i]` above a per-finger threshold
  (default 0.05) for 3 consecutive readings.
- **Host state.** `status` and telemetry gain `"touch":[t0,t1,t2,t3]`,
  `"contact":[b0,b1,b2,b3]` and `"grip_force"`, the mean of the two highest
  `touch` values (a held object loads at least two opposing fingers).
- **Command.** `{"cmd":"grip","pos":1,"force":0.4}`: close toward `pos`, but
  stop and hold when `grip_force` reaches `force`. Reply carries
  `"held":true` if at least two fingers report contact at the stop, else
  `"held":false` (closed on nothing). `force` omitted keeps today's
  position-only behaviour. Any finger over 0.95 aborts a close regardless.
- **Interim on the Octopus.** The Heltec streams the gripper close as short
  relative moves and stops issuing them when the force target is met. No
  Marlin change and no StallGuard.

## 7. Bill of materials

| Item | Qty | Approx. |
|---|---|---|
| Interlink FSR 402 | 4 | $28 |
| Adafruit ADS1115 STEMMA QT breakout (#1085) | 1 | $15 |
| 10 kΩ 1 % resistors | 4 | — |
| JST XH 4-pin pairs for finger roots, 6-way lead, QWIIC cable | 1 set | $10 |
| Printed pad caps | 4 | filament |

Roughly $55.

## 8. Risks

- **FSR drift and hysteresis.** Readings creep under sustained load and depend
  on temperature. Mitigated by re-taring at every open and by treating
  `touch` as relative, not as newtons.
- **Pad geometry.** Without the dome the signal is unrepeatable. The cap is
  printed, so this is cheap to iterate, but it is on the critical path.
- **Cable flex at the finger joints.** FSR tails are not rated for repeated
  flexing. The flex section is the JST lead, and the tail is fixed along the
  finger.
- **Bus loading at the wrist.** One more device on the far end of a PCA9615
  segment; expected fine at 400 kHz but the pull-up total must be checked.

## 9. Rejected alternatives

- **Analogue into a Heltec pin.** No ADC on any pin Cybot gets from the
  carrier, and 600 mm of analogue beside stepper leads regardless.
- **StallGuard on the gripper TMC2209.** Free, but binary, and a lead screw
  stalls hard: it slams the object before it reports. Kept as a fallback if
  the pads are ever unavailable.
- **Load cell on the nut holder.** Gives real force, but needs a flexure in
  a printed part and reports only the total, not which finger. Deferred.
- **Capacitive touch.** Needs the S3 touch pins (GPIO1 to 14), none available,
  and gives no force.

## 10. Acceptance (bench)

1. ADS1115 answers at 0x48 behind the mux; four channels read with the pads
   open; `status` shows `touch` all under 0.02 after tare.
2. Pressing one finger raises only its channel; crosstalk under 0.02.
3. Tare drift under 0.02 over ten minutes at rest.
4. `grip` with `"force":0.3` on a 40 mm foam block stops with `"held":true`
   and no visible crush; the same on nothing returns `"held":false` at the
   closed limit.
5. `"force":0.2` holds a raw egg without breaking it; `"force":0.8` holds a
   200 g wrench through a full-speed wrist roll.

## 11. Phasing

- **A.** ADS1115 and one FSR on the bench Heltec over USB: driver, sweep
  entry, `touch` in `status`.
- **B.** Pad caps printed and fitted, all four pads wired to the wrist board.
- **C.** Tare, thresholds, `grip` with `force`, `held` reply.
- **D.** Acceptance runs 4 and 5, thresholds tuned, values into NVS.

## 12. Open items

- Measure the `grip` pad face on a printed finger: FSR 402 needs about 20 mm
  of flat; otherwise FSR 400.
- Whether the PakaNode V2 daughterboard puts its own board at the wrist; if
  so the ADS1115 can live on it instead of a breakout.
- Gripper axis on the Octopus (MOTOR7 as U, TMC2209, T8 steps) is a separate
  configure.py change and is not part of this spec.
