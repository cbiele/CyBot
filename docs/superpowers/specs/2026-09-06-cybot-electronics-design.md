# Cybot electronics and firmware architecture

**Date:** 2026-09-06
**Status:** Draft for founder review
**Decided inputs:** MKS SERVO42D/57D bus smart-steppers on CAN (founder, 2026-09-06);
Heltec WiFi LoRa 32 V4 on the PakaNode carrier Rev E with `J_GPIO1` (Chopaka D-086);
motors not yet purchased; host link = USB serial + WiFi; homing = encoder Z-index on
axes 1-3, limit switches on axes 4-6.

---

## 1. Goal

Firmware written natively on ESP-IDF v5.4 for the Heltec V4 that fully controls the
Cybot 6-axis cycloidal arm plus its gripper: homing, joint-space moves, jogging, an
e-stop, and a command protocol a laptop, the PakaNtrol-style app, or a camera board
can drive. Cartesian kinematics and the Seeed XIAO ESP32-S3 Sense camera come after the
arm moves reliably in joint space.

## 2. Why this shape

The Heltec plus carrier offers eight fast GPIOs to the arm (`J_GPIO1` and the GNSS port
duplicate GPIO38-42, so they do not add up). Seven step/dir motors need fifteen. Putting
the step generation and the closed loop on the motors, and talking to all seven over
one CAN pair, fits the pin budget with room to spare, removes real-time step timing
from the Heltec, and gives every joint a 16384-count encoder and stall protection for
free. The original author's ROS-plus-STM32 stack is replaced, not ported; only the
mechanical facts (ratios, motor sizes, encoder placement) carry over.

## 3. Scope

**In:** motor and driver selection, the CAN bus and daughterboard, power and e-stop,
encoder and switch wiring, homing, the Heltec pin map, the firmware component layout,
the host command protocol, calibration, bring-up acceptance.

**Out (later specs):** Cartesian FK/IK from the URDF, trajectory blending, the camera
board and object training, an enclosure for the electronics, gripper force control.

---

## 4. System architecture

```
 laptop / app / camera board
        │ USB-Serial-JTAG (bench)  or  WiFi TCP (standalone)
        ▼
 ┌──────────────────────────────┐
 │ Heltec V4 (ESP32-S3, IDF 5.4)│  cmd parser · motion planner · homing · safety
 │ on PakaNode carrier Rev E    │
 └──┬───────────┬──────────┬────┘
    │ J_GPIO1   │ J_EXP1   │ J2 / USB-C
    │ (CAN,Z,ES)│ (I²C exp)│ (5 V in)
    ▼           ▼          ▼
 ┌──────────────────────────────┐   24 V ──[E-STOP contactor]──┐
 │ Cybot daughterboard          │◄──────────── 5 V buck ◄──────┤
 │ SN65HVD230 · Z pull-ups ·    │                              │
 │ 24V→5V buck · connectors     │                              │
 └──┬───────────────────────────┘                              │
    │ CAN 500 kbit/s, one twisted pair, 120 Ω both ends         │
    ├── SERVO42D #1 axis 1 (base yaw)      NEMA17 ─────────────┤
    ├── SERVO57D #2 axis 2 (shoulder)      NEMA23 ─────────────┤
    ├── SERVO57D #3 axis 3 (elbow)         NEMA23 ─────────────┤
    ├── SERVO42D #4 axis 4 (forearm roll)  NEMA17 ─────────────┤
    ├── SERVO42D #5 axis 5 (wrist pitch)   NEMA17 ─────────────┤
    ├── SERVO42D #6 axis 6 (wrist roll)    NEMA17 ─────────────┤
    └── SERVO42D #7 gripper                NEMA17 ─────────────┘
```

Three independent loops:
- **Motor loop** (20 kHz torque, 10 kHz position) lives on each MKS board.
- **Motion loop** on the Heltec issues position targets over CAN and watches arrival.
- **Safety loop** is copper: the e-stop breaks 24 V ahead of every smart part; the
  MKS heartbeat timer stops motors if the Heltec goes silent.

---

## 5. Hardware design

### 5.1 Motors and drivers

| Axis | Joint | Reduction | Motor | Driver | CAN ID |
|---|---|---|---|---|---|
| 1 | base yaw | 1:23 cycloid + HTD 3M belt | NEMA17 dual-shaft | SERVO42D CAN | 1 |
| 2 | shoulder | 1:20 cycloid + HTD 3M belt | NEMA23 dual-shaft | SERVO57D CAN | 2 |
| 3 | elbow | 1:20 cycloid + HTD 3M belt | NEMA23 dual-shaft | SERVO57D CAN | 3 |
| 4 | forearm roll | 1:11 cycloid | NEMA17 dual-shaft | SERVO42D CAN | 4 |
| 5 | wrist pitch | 1:11 cycloid + GT2 belt | NEMA17 dual-shaft | SERVO42D CAN | 5 |
| 6 | wrist roll | 1:11 cycloid + GT2 quarter-turn belt | NEMA17 dual-shaft | SERVO42D CAN | 6 |
| 7 | gripper | T8 leadscrew | NEMA17 dual-shaft | SERVO42D CAN | 7 |

**Motor requirements.** The MKS board mounts on the motor's rear face and reads a
magnet glued to the rear shaft, so every motor must be a **dual-shaft** part. Front
shafts must match the pulleys the STLs assume: **6.35 mm** on the NEMA23s (3M 30T
pulleys) and **5 mm** on the NEMA17s (GT2 and 3M pulleys, T8 coupler). Current: NEMA23
at or under 3.2 A per phase (57D default working current), NEMA17 at or under 1.7 A
(42D default 1.6 A). Torque targets follow the assembly guide: 1.2-1.9 N·m for the
NEMA23s, 0.4-0.5 N·m for the NEMA17s.

**Motor count corrected from the geometry (2026-09-06).** The assembly guide says three
NEMA23 and four NEMA17, but the v5 STLs carry a 31 mm NEMA17 bolt pattern with a Ø32
bore on the base holder, so the build is **two NEMA23 (axes 2, 3) and five NEMA17
(axes 1, 4, 5, 6, gripper)**. See `docs/2026-09-06-stl-reconstruction.md` §4.

**Length, measured from the STLs (reconstruction report §5).** The NEMA23s sit between
the body plates with **61.0 mm** from the pocket floor to the opposite plate. The MKS
boards add an estimated 15-20 mm (not published; measure the first unit). Resolution,
decided after the boards are measured:

1. 41 mm dual-shaft NEMA23s if the board measures under about 18 mm, or
2. a 6-8 mm recess in `mainBody2`'s inner face behind each motor, stopping short of
   the adjacent encoder pockets. Everything printed is ours to change; motors are not.

The gripper NEMA17 has **55 mm** between its mounting face and the adapter: use a
34-40 mm pancake NEMA17, or lengthen the printed adapter by 10 mm. Axes 1, 4, 5 and 6
are in open air.

Prefer buying the MKS "MB" board-only variants plus separately chosen motors so length
can be picked; the "MT" motor bundles ship fixed lengths (the 57D bundles seen are
56 mm and 76 mm, both over the space available).

### 5.2 CAN bus

- **Physical:** one twisted pair, 500 kbit/s (MKS default), standard 11-bit IDs.
  120 Ω termination at the daughterboard and at the last MKS board (the daisy chain
  ends at the gripper). Verify whether the MKS boards carry a termination jumper; if
  not, a resistor in the last connector.
- **Transceiver on the Heltec side:** SN65HVD230, 3.3 V, RS pin to GND (high-speed
  mode). MKS boards use a TJA1051T at 5 V; CAN bus levels are compatible.
- **ESP32-S3 side:** TWAI peripheral, TX = GPIO40, RX = GPIO41. Both are boot-safe;
  neither is a strapping pin. GPIO45 is excluded: its carrier pulldown would hold CAN
  TX dominant through every reset and jam the bus.
- **Frame format** (from the MKS CAN manual V1.0.9): `ID, DLC, code, data…, CRC` with
  `CRC = (ID + all bytes) & 0xFF`. ID 0 is broadcast (slaves do not reply). Replies
  come back on the slave's own ID.
- **Bring-up commands used:** `0x82` work mode = 5 (SR_vFOC), `0x83` working current,
  `0x8B` set CAN ID (done once per board on the bench, one board at a time), `0x8C`
  respond-active, `0x98` heartbeat protection = 500 ms, `0x95` arrival threshold,
  `0xF3` enable, `0xF5` absolute move by axis (int24 in 0x4000 counts per motor rev,
  speed 0-3000 RPM, acc 0-255), `0x4A`/`0x4B` synchronous-execute flag and trigger,
  `0xF7` emergency stop, `0x31` read multi-turn encoder, `0x01` periodic auto-report,
  `0x90`/`0x91` homing parameters and go-home, `0x92` set current position as zero.

### 5.3 Daughterboard

A small board that either **stacks on `J_GPIO1`** (vertical header) or **sits beside
the carrier on shared M3 standoffs** (right-angle header). The Chopaka session sends
the frozen `J_GPIO1` coordinates and orientation; until then the layout is designed
for both. Carrier M3 pattern (board-relative, mm, y down): H4 (5, 5), H1 (70, 5),
H3 (5, 60), H2 (70, 61). It is not a perfect rectangle.

Contents:
| Block | Part | Notes |
|---|---|---|
| CAN transceiver | SN65HVD230 + 120 Ω jumper | TX GPIO40, RX GPIO41, RS to GND |
| Encoder Z inputs | 3× 4.7 kΩ to 3V3, 100 nF, series 1 kΩ | Omron NPN open-collector, 30 V max on the output |
| E-stop status | 1× 10 kΩ to 3V3, series 1 kΩ, to GPIO26 | Auxiliary NC contact of the e-stop, closed = run |
| 24 V-present sense | 24 V → divider/opto → `J_EXP1` P15 | Tells firmware motor power is up |
| Limit switches | 3× 10 kΩ to 3V3 → `J_EXP1` P05/P06/P07 | Axes 4-6, NC switches, closed = not at limit |
| 5 V buck | 24 V → 5 V, 2 A module, feeds carrier `J2` | ≤ 500 mA continuous budget (see §5.4) |
| Connectors | `J_GPIO1` mate; JST-XH for each encoder; e-stop; 24 V in; CAN out | Distinct pitches so nothing mis-mates |

No-connect on the daughterboard: `J_GPIO1` pin 3 (VDD_5V, the Heltec USB rail, dead
without USB and never to be driven) and pin 5 (GPIO45).

### 5.4 Power

- **Motor rail:** 24 V, 10 A supply. Seven MKS boards at 24 V; the boards draw only
  what the motors use, and holding current defaults to 50 % of working current.
- **E-stop:** a mushroom switch with two NC contacts. Contact 1 drives a 24 V DC
  contactor coil; the contactor breaks the 24 V motor rail ahead of all seven drivers.
  Contact 2 is the status signal to GPIO26. Pressing the button drops the motors to
  loose shafts; the arm sags under gravity, which is acceptable for this arm's mass
  and preferable to a locked joint with unknown state. After an e-stop the MKS
  multi-turn counts are lost and firmware forces a re-home before any move.
- **Heltec on the bench:** USB-C from the dev machine. It is also the console and
  flash port.
- **Heltec standalone:** the daughterboard buck into carrier `J2`. The carrier's solar
  fuse F1 has an unverified hold rating, so the budget is **500 mA continuous** until
  measured. A small LiPo on `J_BATT1` buffers WiFi transmit bursts through the
  Heltec's charger. Firmware must **never drive GPIO4 high** (carrier solar disconnect)
  and, if it ever deep-sleeps, must not do so with GPIO4 held.
- **Encoders:** Omron E6B2-CWZ6C accepts 5-24 V; power them from the daughterboard 5 V
  rail. Outputs are open-collector and pulled up to 3.3 V, so no level shifting.

### 5.5 Heltec pin map (Cybot)

| GPIO | Via | Function |
|---|---|---|
| 40 | `J_GPIO1`.8 | CAN TX |
| 41 | `J_GPIO1`.7 | CAN RX |
| 38 | `J_GPIO1`.10 | Encoder Z, axis 1 |
| 39 | `J_GPIO1`.9 | Encoder Z, axis 2 |
| 42 | `J_GPIO1`.6 | Encoder Z, axis 3 |
| 26 | `J_GPIO1`.4 | E-stop status (input, closed = run) |
| 45 | `J_GPIO1`.5 | unused (strap; carrier pulldown) |
| 47 / 48 | carrier I²C | TCA9535 at 0x20 (`J_EXP1`), MAX17048 at 0x36 |
| 4 | carrier | Solar disconnect — leave low, never assert |
| 17 / 18 / 21 | Heltec | OLED (status display) |
| 19 / 20 | Heltec | USB-Serial-JTAG console |
| 8-14, 2 | Heltec | SX1262 LoRa — unused, FEM_EN still driven high at boot |

The Omron A/B quadrature outputs are **not wired in v1**. The MKS boards report joint
position at 16384 counts per motor revolution; the Omron Z pulse provides the absolute
home reference once per joint revolution through the 1:1 encoder belt. If output-side
feedback proves necessary (belt slip, cycloid compliance), the upgrade path is a small
CAN node reading all three A/B pairs, not more Heltec pins.

### 5.6 Homing and limits

- **Axes 1-3:** MKS speed mode (`0xF6`) toward a soft-limit direction at 30 RPM motor
  speed, PCNT/GPIO interrupt on the Z pulse, then `0xF7` stop, back off, re-approach
  slowly, latch the MKS multi-turn count at the Z edge and `0x92` it as zero. Because
  Z fires once per joint revolution and the joint range is under one revolution, the
  first Z edge reached in the homing direction is unambiguous. Joint soft limits come
  from the URDF (axis 1 ±180°, axis 2 −90°/+150°, axis 3 −238°/+79°).
- **Axes 4-6:** NC microswitches on `J_EXP1`. Firmware polls the expander at 100 Hz
  during homing and stops the axis on open; the MKS boards also get their own homing
  parameters (`0x90`) as a second, on-board limit so a lost I²C poll cannot overrun.
- **Gripper:** MKS "noLimit" stall homing (`0x94`) against the open stop at low
  current, then a fixed close range.
- **Left/right limits on the MKS boards** are enabled after homing so an over-travel
  command is refused at the driver even if the planner is wrong.

---

## 6. Firmware design (ESP-IDF v5.4, C, PakaFW conventions)

```
cybot/
├── main/              app_main: boot, safety state machine, task wiring
├── components/
│   ├── mks_can/       TWAI driver + MKS frame codec (pure codec host-tested)
│   ├── axis/          per-axis config, unit conversion, soft limits (pure, tested)
│   ├── motion/        point-to-point planner with sync-execute (pure core, tested)
│   ├── homing/        Z-index and switch homing sequences
│   ├── cybot_io/      TCA9535 expander, e-stop input, 24 V sense
│   ├── cmd/           newline-JSON protocol parser and responder (pure, tested)
│   ├── transport/     USB-Serial-JTAG console + WiFi TCP server, same byte stream
│   └── display/       OLED status page (reuse PakaFW shared/display)
└── test/host/         host-built unit tests, same pattern as PakaFW/test/host
```

**Safety state machine:** `FAULT → IDLE → HOMED → MOVING`, with `ESTOP` reachable
from anywhere. Transitions: 24 V present and e-stop closed → `IDLE`; homing complete
→ `HOMED`; any move needs `HOMED`; e-stop open, 24 V lost, CAN timeout, or a driver
reporting stall/protection → `FAULT`, and `FAULT` clears only by explicit command with
the e-stop closed. The MKS heartbeat (`0x98`, 500 ms) is refreshed by a periodic
status read from the motion task, so a Heltec crash stops the motors within half a
second without any firmware help.

### 6.1 Motion control: two approaches

**A. Point-to-point with driver-side profiles (v1, recommended).** The planner takes
target joint angles, converts to motor counts, computes per-axis speed so that every
axis finishes at the same time (scale each axis's RPM by its share of the longest
move, like the original Arduino coordination function), loads all seven `0xF5`
commands with the sync flag armed (`0x4A` = 1), then fires one broadcast `0x4B`.
Arrival is detected by the `0xF5` status = 2 reply or by comparing `0x31` encoder
reads against the target. Simple, robust, and enough for teach-and-repeat and for
the camera phase's pick-and-place.

**B. Streamed setpoints (v2).** The Heltec runs a 50 Hz joint-space interpolator and
re-issues `0xF5` with updated position and speed each tick (supported since MKS
firmware V1.0.5). This enables Cartesian straight lines and blended motion. Same CAN
driver and same axis layer; only the planner grows.

Approach A is built first. The `motion` component's interface is a queue of joint
targets with a completion callback, so B slots in behind it.

### 6.2 Units and calibration

`counts = angle_deg / 360 × 16384 × R_total`, where `R_total = R_cycloid × R_belt`.
The cycloid ratios are known (23, 20, 20, 11, 11, 11). **The belt ratios are not**: the
main-body pulleys are a mix of 20T and 30T metal pulleys and large printed pulleys
(`axis2-GT2-stepper.stl` is about 118 mm in diameter). Calibration procedure per axis:

1. Home the axis.
2. Command a nominal 90° move using the cycloid ratio only.
3. Measure the real joint rotation with a phone inclinometer on the link.
4. Store the corrected `R_total` in NVS; the Z-index spacing (exactly one joint
   revolution) gives a second, exact check on axes 1-3 by counting motor counts
   between two Z edges.

### 6.3 Command protocol

Newline-delimited JSON, identical over USB serial and WiFi TCP port 5000. One request
per line, one reply per line, plus unsolicited telemetry lines when enabled.

| Request | Effect |
|---|---|
| `{"cmd":"status"}` | state, per-axis angle, homed flags, 24 V, e-stop, CAN health |
| `{"cmd":"home","axes":[1,2,3]}` | run homing on listed axes (omit for all) |
| `{"cmd":"move","j":[a1..a6],"v":0.5}` | joint-space move, `v` = fraction of max speed |
| `{"cmd":"jog","axis":2,"deg":5}` | relative move on one axis |
| `{"cmd":"grip","pos":0.8}` | gripper 0 = open, 1 = closed |
| `{"cmd":"stop"}` | decelerate all axes (`0xF5` with speed 0, acc ≠ 0) |
| `{"cmd":"estop"}` | `0xF7` broadcast; enters `FAULT` |
| `{"cmd":"clear"}` | leave `FAULT` if safe |
| `{"cmd":"set","axis":1,"key":"ratio","val":92.3}` | calibration and limits into NVS |
| `{"cmd":"telemetry","hz":10}` | periodic status lines |

Replies: `{"ok":true,...}` or `{"ok":false,"err":"not_homed"}`. This is the surface
the camera board will use later; it adds no new commands, it just sends `move` and
`grip` from detections.

### 6.4 What is host-tested

The MKS codec (frame build, CRC, reply decode), the axis unit conversion and soft
limits, the coordinated-speed planner, the JSON parser, and the safety state
machine. Everything that touches TWAI, I²C, or GPIO is exercised on hardware only,
first against a single MKS board on the bench, then on the assembled 20:1 joint.

---

## 7. Bill of materials (electronics, excluding printed parts)

| Item | Qty | Note |
|---|---|---|
| MKS SERVO57D CAN, board only | 2 | axes 2-3 |
| MKS SERVO42D CAN, board only | 5 | axes 1, 4-6 + gripper |
| NEMA23 dual-shaft, 6.35 mm front shaft, ≤ 3.2 A | 2 | 41 mm class, per §5.1 |
| NEMA17 dual-shaft, 5 mm front shaft, ≤ 1.7 A | 5 | 47 mm class; gripper 34-40 mm |
| 24 V 10 A PSU | 1 | |
| 24 V DC contactor + mushroom e-stop with 2× NC | 1 | |
| SN65HVD230 module, 120 Ω resistors | 1 + 2 | |
| 24 V → 5 V 2 A buck module | 1 | |
| Omron E6B2-CWZ6C 1000 P/R | 3 | already in the Cybot BOM |
| NC microswitches | 3 | axes 4-6 |
| Small LiPo, JST PH 2.0 | 1 | standalone Heltec buffer |
| Daughterboard PCB, connectors, passives | 1 | §5.3 |

Rough cost: drivers about 195 USD, motors about 130 USD, PSU and e-stop about 60 USD,
the rest under 40 USD.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Motor + MKS board too long for the body | 61 mm measured from the STLs; 41 mm motors or a plate recess (§5.1) |
| CAN bus errors from 7 nodes on hobby wiring | Twisted pair, both terminations, 500 kbit/s not 1 Mbit/s, error counters in `status` |
| Belt ratio unknown → wrong joint angles | Calibration procedure §6.2 before any coordinated move |
| Z pulse missed at homing speed | Homing approach at 30 RPM motor speed; Z is 0.36° of encoder shaft, PCNT edge capture, not polling |
| Heltec crash mid-move | MKS heartbeat 500 ms stops motors independently of firmware |
| E-stop loses position | Forced re-home after any `FAULT`; documented as expected |
| Carrier F1 rating unknown | 500 mA cap + cell buffer standalone; USB-C on the bench |
| I²C expander poll too slow for a limit switch | MKS on-board limits (`0x90`) as the hard stop; expander is the soft stop |

## 9. Rejected alternatives

- **TMC2209 + I²S shift registers.** Fits the pins, but adds a custom real-time step
  generator and a larger daughterboard for no gain once the founder chose smart
  steppers.
- **RS485 / Modbus-RTU MKS variants.** Half-duplex polling of seven axes and
  collision handling on the Heltec; CAN is native to the ESP32-S3 and multi-drop.
- **Wiring Omron A/B to the Heltec.** Six inputs exceed the boot-safe pin budget once
  CAN takes two; Z-only homing plus MKS position covers v1.
- **Camera over a UART.** No boot-safe pins left; the XIAO ESP32-S3 Sense has WiFi and
  speaks the same JSON protocol.
- **Serial bus servos (Feetech / Dynamixel).** Replace the whole motor-plus-cycloid
  design the STLs are built around.

## 10. Acceptance (bring-up)

1. One SERVO42D on the bench answers `0x31` over CAN from the Heltec at 500 kbit/s
   and executes an `0xF5` move; CRC and reply decode host-tested first.
2. Seven boards addressed 1-7, all reply to a broadcast-free status sweep in under
   20 ms total.
3. E-stop drops the 24 V rail; firmware enters `FAULT` within 50 ms and refuses `move`.
4. Heartbeat: killing the Heltec mid-move stops all motors within 600 ms.
5. The assembled 20:1 joint homes to its Z index three times with repeatability under
   0.1° at the joint, measured on the link.
6. A coordinated six-axis `move` starts and stops all axes together (sync flag).
7. The same command stream works over USB serial and over WiFi TCP.

## 11. Phasing

1. **Measure** the MKS board depth on one SERVO57D and one SERVO42D (pocket depth is
   now known from the STLs: 61 mm); pick motor lengths; order the rest.
2. **Codec and planner on the host**, tests green, while parts ship.
3. **Single-board bench**: Heltec + transceiver + one SERVO42D on a loose NEMA17.
4. **Daughterboard v1** once `J_GPIO1` orientation is frozen.
5. **Joint bench**: the assembled 20:1 joint, Omron Z homing, calibration.
6. **Full arm** as printing and assembly complete, one axis at a time.
7. **Camera**: separate spec.

## 12. Open items

- MKS board added depth (measure a unit), and whether the boards carry a
  termination jumper.
- NEMA23 answer: 41 mm motors vs a `mainBody2` recess.
- `J_GPIO1` frozen coordinates and vertical vs right-angle (Chopaka session).
- Carrier F1 hold current (Chopaka first-article).
- VDD_5V reading on `J_GPIO1` pin 3 under both power sources (Chopaka first-article).
