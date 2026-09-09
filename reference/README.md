# reference/ — quartit's public Cybot repositories, pulled 2026-09-09

Verbatim snapshots of everything on github.com/quartit (three repositories,
all of it). Nested .git directories were stripped so this project's git does
not treat them as submodules; each folder carries GIT_HISTORY.txt with the
upstream log, and the HEAD commits are below. Only cybot_arduino declares a
license (GPL-3.0); the other two have none, so treat them as read-only
reference, not code to reuse.

| Folder | HEAD | Last push | What it is |
|---|---|---|---|
| cybot | b1c49fc | 2022-06-08 | Four Raspberry Pi python scripts. Two publish MOVE strings to a ROS topic `/cybot_btt_cmd` that the (unpublished) STM32 BigTreeTech GTR firmware consumed; one sends grbl-style x/y strings over /dev/ttyAMA0; one is a UART echo test. 82 commits, all edits to these five files. |
| cybot_arduino | a8b8ca1 | 2023-11-13 | The Arduino MEGA + sensor shield + TMC2209 starter: one SpeedyStepper sketch driving two axes from serial commands (move X..../X, accel, maxspeed), plus wiring photos. |
| cybot_support | ad06c34 | 2022-10-13 | The ROS package: the ABB-placeholder cybot.urdf, a UR5 RViz test, and the seven link meshes (same files as ../URDF/simplify). See ../URDF/cybot_support/README.md for what carries over. |

## What is NOT here, because the author never published it

- The STM32 / BigTreeTech GTR firmware (CubeIDE, FlexyStepper, rosserial)
  that actually ran the six axes. The PDF says "I will add later"; it never
  appeared. Its command format is visible from cybot/cybot_demo.py:
  `MOVE<X>20000</X><Y>-20000</Y><Z>..</Z><E0>..</E0><E1>..</E1><E2>..</E2>`,
  six axes named X Y Z E0 E1 E2 with relative step counts.
- Any steps-per-degree, belt ratio, microstep, or homing values. The Arduino
  sketch is a bare two-axis step test with no per-axis calibration, and the
  python scripts only carry raw step counts (20 000-40 000 per demo move),
  so the ratios in the electronics spec still have to be measured on the arm.
- cybot_core, the catkin package cybot_support depends on.

## Numbers that are usable

- Arduino pin convention for the starter: EN/STEP/DIR on MEGA 14/15/16 (axis X)
  and 18/19/20 (axis Y); X accel 500, speed 6000 steps/s; Y accel 2000,
  speed 3000 steps/s.
- Serial to the Pi at 115200 on /dev/ttyAMA0 or /dev/ttyS0.
