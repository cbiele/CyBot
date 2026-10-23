# Marlin for the Octopus Pro bench

Marlin (bugfix-2.1.x, pinned in `UPSTREAM_SHA`) configured as a six-axis
arm controller for the BTT Octopus Pro V1.1 (STM32H723). Marlin itself is
never committed: `build.sh` clones it into `upstream/` (gitignored), resets
the two configuration files, applies `configure.py`, and builds with
PlatformIO (installed via `uv tool install platformio`). Output:
`out/firmware.bin`.

`configure.py` is the whole configuration: one exact line-for-line edit per
change, and it aborts if any edit no longer matches, so a Marlin update
cannot silently build the wrong thing.

## Axis and slot map

| Joint | Marlin axis | G-code letter | Octopus slot | Motor | Driver | Steps/deg |
|---|---|---|---|---|---|---|
| 1 base yaw | X | X | MOTOR0 | 42SHDC3025-24B | TMC2209 UART | 58.93 (179/27 belt) |
| 2 shoulder | Y | Y | MOTOR1 | 23HS22-2804S | TMC5160 SPI | 306.67 (1.5 x 23) |
| 3 elbow | Z | Z | MOTOR2 | 23HS22-2804S | TMC5160 SPI | 266.67 (1.5 x 20) |
| unused | Z2 | | MOTOR3 | | | |
| 4 forearm roll | I | A | MOTOR4 | 17HS8401B | TMC2209 UART | 97.78 (11) |
| 5 wrist pitch | J | B | MOTOR5 | 17HS8401B | TMC2209 UART | 97.78 (11) |
| 6 wrist roll | K | C | MOTOR6 | 17HS8401B | TMC2209 UART | 88.89 (TBD) |
| gripper (later) | U | D | MOTOR7 | 42C kit motor | TMC2209 UART | |

Marlin assigns I, J, K to the E0, E1, E2 sockets in order because EXTRUDERS
is 0. All axes are in degrees; feedrates in G-code are deg/min. Currents in
`configure.py` are RMS: 1200 mA on the NEMA17s, 2000 mA on the NEMA23s.
spreadCycle everywhere (stealthChop off) for torque. Motors never time out,
so the arm holds position; `M18` releases it.

## Board setup

- Driver mode jumpers under each socket per the BTT Octopus Pro manual:
  UART positions for the TMC2209 slots, the SPI set for the two TMC5160
  slots. Do not mix within a slot. Leave the DIAG jumpers off.
- Driver-power input jumper on VIN (both inputs from the same 19.5-24 V).
  Only the driver input goes through the e-stop.
- Fan across the driver row before the NEMA23s run at 2 A.
- Serial: USB (`/dev/tty.usbmodem*`, 250000 baud) is port 1; the TFT header
  UART is port 2 for the Heltec later.

## Flashing

1. `./build.sh` (first run downloads the STM32 toolchain, several minutes).
2. Copy `out/firmware.bin` to a FAT32 SD card root as `firmware.bin`.
3. Power the board with the card in; the bootloader flashes and renames it
   `FIRMWARE.CUR`. `M115` over USB should answer `Cybot`.
4. `M122` prints one connection line per driver (`OK`, or `All LOW` for an
   empty socket). The full TMC_DEBUG table is off: with empty TMC2209
   sockets it overruns the 4 s watchdog and resets the board.

## First motion: the 28BYJ-48

Its 5-pin plug is unipolar and fits no stepper socket. Open the motor's
little PCB and cut the trace to the red centre-tap wire; it is then a
4-wire bipolar motor: orange+pink one coil, yellow+blue the other. Plug it
into MOTOR0 with a TMC2209 and send over USB:

```
M115            ; identify
M122            ; TMC driver report, X must show a live driver
M906 X200       ; 200 mA RMS for the little motor
M92 X91         ; 32768 microsteps per output rev / 360
G91             ; relative moves
G1 X90 F600     ; quarter turn at 10 deg/s
G1 X-90 F600
M500            ; keep the settings
```

Then the real motors, one socket at a time: `M122` for the driver, a
10-degree move, check direction (flip `INVERT_*_DIR` in `configure.py`),
check steps/deg with a mark on the output.
