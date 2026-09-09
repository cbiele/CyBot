# reference/video — every CyBoT video from the channel (pulled 2026-09-09)

Channel: https://www.youtube.com/@CyBoT_robot (30 videos, 53 min). All 23
Cybot videos are here; the 7 drone/CNC/watch videos were skipped. No video
has captions worth reading (the one auto-caption is "[Music]"); descriptions
are quoted below where they say anything. The 1080p .mp4 files are
gitignored (650 MB); `frames/` holds one JPEG every 5 s plus a contact sheet
per video and is tracked. Re-download with:
`uvx yt-dlp -f "bv*[height<=1080]+ba" --merge-output-format mp4 <url>`
(ffmpeg from `uvx --from imageio-ffmpeg`).

| Date | Video | Id | Frames | What it shows |
|---|---|---|---|---|
| 2021-12-14 | Progress on Axis 5 and 6 | 1bqRt2XQlIc | 24 | wrist yoke with both gearboxes in, belts on |
| 2022-01-03 | Quarter turn belt for axis 6 | wjkaDF5IcJk | 8 | the 90° GT2 belt path over the printed idler (HK0608 rollers) |
| 2022-01-07 | A Close Look To Axis 5&6 holder | V26ltPOez2g | 31 | wrist holder halves, 6810/6812 seats, motor placement |
| 2022-01-08 | Cycloidal drive Assembly | vwFGVBSI5IE | 66 | **the 1:11 wrist gearbox** being assembled, not the 1:20 body joint |

## The other 19, in date order, and what they add

| Date | Video | Frames | Worth knowing |
|---|---|---|---|
| 2021-10-29 | Working on a 3 disks cycloidal drive | 10 | first 1:24 prototype; description credits Damian Lickindorf's OpenCyRe/Atlas as the inspiration and links a Thingiverse WIP (thing:5142762, JS-only page, not scraped) |
| 2021-11-08 | 1:24 fusion 360 Cycloidal Gearbox | 23 | Fusion build-up of the body joint: 4-piece eccentric shaft, three disks 120° apart, ring pins, OPH plates, housing. Same architecture as our axis-2 exploded file |
| 2021-11-14 | 3d printed 1:24 Cycloidal Gearbox | 12 | first print; "housing too tight" |
| 2021-11-21 | Progress on Axis 1-2-3 | 14 | Fusion: early body with both joints, the belt run and the first tensioner idea |
| 2021-11-26 | Progress on Base Join Axis 1 | 20 | **Fusion explode of the base**: base plate with pin rollers, the two 6816 stacked in a ring, the rotating base pieces and the Ø80 column. Frame 005 is the clearest |
| 2021-11-29 | 6 axis robot arm cycloidal drive | 16 | axis-4 design start; "same gearbox for axes 4, 5, 6, min 1:11, NEMA17" |
| 2021-11-29 | Cycloidal disk 1:11 reducer in Fusion 360 | 55 | how the disk profile was drawn (loft for smoother rotation); links the profile tutorial he followed |
| 2021-12-07 | 3d Printed 1:24 Actuator with NEMA17 | 7 | the body joint running on a bench with the big yellow pulley; the vertical pin slots in the housing are visible |
| 2021-12-23 | 3d Printed 1:11 Actuator with NEMA17 | 21 | "2 disks version with **6811** and 6705 bearings", output pins home-made while waiting for 6 mm pins |
| 2021-12-24 | High Precision 1:11 reducer | 13 | same unit, close-ups |
| 2022-01-04 | Tomorrow I'll put the two steppers together | 7 | wrist with both NEMA17s fitted |
| 2022-01-09 | Axis 5 and 6 Holder | 4 | the 32 h holder print, one half failed |
| 2022-02-03 | BigTreeTech GTR V1 with TMC2209 | 11 | the electronics he settled on: STM32 GTR + TMC2209, SpeedyStepper ported to STM32 |
| 2022-02-09 | Fourth Axis Moving | 11 | first axis-4 motion; Raspberry Pi 4 over UART added |
| 2022-04-02 | ROS Moveit RViz First POC | 11 | first ROS connection; "will design the urdf file" (it stayed the ABB placeholder) |
| 2022-05-25 | Final Design Fusion360 | 22 | **turntable of the finished CAD** from every side: body belts and tensioners, wrist, flange. Best overall reference for how the whole arm looks assembled |
| 2022-06-02 | Bodybuilding exercise for axis 2 | 9 | axis 2 lifting the full arm; shows the arm's real reach and speed |
| 2022-10-14 | Finally working with Moveit Rviz | 13 | RViz driving the real arm side by side; the Cults files went live here |
| 2023-11-05 | Adding joystick and gripper | 21 | final state: gripper fitted, gamepad control |

Takeaways beyond the parts: the 1:11 gearbox was designed with 6811 (55×72×9)
bearings before the Cults PDF's 6812; the STL bores are Ø78, so the PDF wins.
The body joint was called 1:24 throughout development, the PDF calls it 1:23
and 1:20; count the ring pins on a printed housing to be sure. The author
never wrote a Cybot URDF or homing.

## Cycloidal drive Assembly, what the frames show (frame = 5 s)

- 001-006: blue 12-lobe disk, orange `axis4_diskCap` dropped on it after the
  brass bushings go in the disk's six Ø10 holes; the cap's small holes take
  the M3 rods.
- 007-024: second disk phased 180°, the two disks stacked on the eccentric,
  Ø6 ring pins pushed through the black housing halves around the disks.
- 025-030: output side: the OPH with the big bearing (6812) on its boss, then
  the housing dropped over the disks; a NEMA17 plate (yellow) bolted on.
- 031-050: M4 rods through the bushings, nuts on both ends, pulley end, the
  input eccentric shaft with its 6705 bearings pressed on (frame 057: the
  80T pulley with the shaft and hex socket).
- 051-066: finished gearbox turned by drill, then the second unit started.

So this video is the reference for the **axis-4 and axis-5 gearboxes**; for
the 1:20 body joint the order is the same idea with 688 bearings in the
disks instead of bushings, see model/subassemblies/axis2-assembly.md.
