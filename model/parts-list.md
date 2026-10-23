# Cybot print list (from the Cults3D v5 + gripper STLs)

Rule: one STL file = one placed instance, so quantity = number of files (byte-identical files confirmed for axis3 disks). `holderNoSplit` is an ALTERNATIVE to holder+holder2, not an extra part. **Rule exceptions:** `plateBall` prints 4 (one per base corner) the gripper's `grip`, `Axe` and `T8_to_Axes` print 4 each (four fingers), and `axis2-diskCap` prints 3 (one per cycloid disk; confirmed on the printed part 2026-09-06, and `axis4_diskCap` prints 2 per 1:11 gearbox, confirmed on the bench 2026-09-12), although each is a single file.

Bed: Bambu P2S 256 x 256 x 256 mm. Fit = all three bbox dims <= 256. Diagonal = longest dim <= 362 and the part is thin enough to lie flat rotated 45 deg (needs a manual check). Split = longest dim > 362.

| Group | Part | X x Y x Z (mm) | Volume cm3 | Bed |
|---|---|---|---|---|
| 1-mainbody | beltTentioner1 | 93 x 30 x 18 | 12 | fits |
| 1-mainbody | beltTentioner2 | 87 x 30 x 18 | 17 | fits |
| 1-mainbody | beltTentioner3 | 106 x 30 x 21 | 15 | fits |
| 1-mainbody | mainBody1 | 380 x 142 x 16 | 351 | SPLIT |
| 1-mainbody | mainBody2 | 380 x 142 x 16 | 389 | SPLIT |
| 1-mainbody | plateBall | 60 x 60 x 50 | 77 | fits |
| 2-axis1 | axis-1-rotatingBase1 | 170 x 170 x 28 | 314 | fits |
| 2-axis1 | axis-1-rotatingBase2 | 170 x 170 x 17 | 189 | fits |
| 2-axis1 | axis-1-rotatingBase3 | 170 x 170 x 69 | 744 | fits |
| 2-axis1 | axis1-baseHolder | 170 x 170 x 68 | 402 | fits |
| 2-axis1 | axis1-encoderHolder | 80 x 78 x 30 | 50 | fits |
| 2-axis1 | axis1-stepperHolder | 80 x 79 x 50 | 76 | fits |
| 3-axis2 | axis2-GT2-encoder | 118 x 118 x 38 | 122 | fits |
| 3-axis2 | axis2-GT2-stepper | 118 x 118 x 15 | 112 | fits |
| 3-axis2 | axis2-OPH1 | 69 x 69 x 14 | 36 | fits |
| 3-axis2 | axis2-OPH2 | 69 x 69 x 14 | 36 | fits |
| 3-axis2 | axis2-disk1 | 118 x 118 x 9 | 65 | fits |
| 3-axis2 | axis2-disk2 | 118 x 118 x 9 | 65 | fits |
| 3-axis2 | axis2-disk3 | 118 x 118 x 9 | 65 | fits |
| 3-axis2 | axis2-diskCap (x3) | 80 x 80 x 3 | 11 | fits |
| 3-axis2 | axis2-holder1 | 132 x 130 x 20 | 157 | fits |
| 3-axis2 | axis2-holder2 | 132 x 130 x 20 | 157 | fits |
| 3-axis2 | axis2-housing1 | 142 x 142 x 32 | 118 | fits |
| 3-axis2 | axis2-housing2 | 142 x 142 x 32 | 118 | fits |
| 3-axis2 | axis2-shaft1 | 26 x 24 x 16 | 6 | fits |
| 3-axis2 | axis2-shaft2 | 27 x 26 x 11 | 4 | fits |
| 3-axis2 | axis2-shaft3 | 27 x 24 x 11 | 4 | fits |
| 3-axis2 | axis2-shaft4 | 26 x 25 x 16 | 6 | fits |
| 4-axis3 | axis3-GT2-encoder | 106 x 106 x 15 | 90 | fits |
| 4-axis3 | axis3-GT2-stepper | 106 x 106 x 38 | 100 | fits |
| 4-axis3 | axis3-OPH1 | 69 x 69 x 20 | 53 | fits |
| 4-axis3 | axis3-OPH2 | 69 x 69 x 20 | 53 | fits |
| 4-axis3 | axis3-disk1 | 102 x 102 x 9 | 42 | fits |
| 4-axis3 | axis3-disk2 | 102 x 102 x 9 | 42 | fits |
| 4-axis3 | axis3-disk3 | 102 x 102 x 9 | 42 | fits |
| 4-axis3 | axis3-holder1 | 118 x 118 x 32 | 60 | fits |
| 4-axis3 | axis3-holder2 | 118 x 118 x 34 | 62 | fits |
| 5-axis4 | axis4_80TGT2-7mm | 53 x 53 x 19 | 21 | fits |
| 5-axis4 | axis4_OPH | 64 x 64 x 12 | 22 | fits |
| 5-axis4 | ~~axis4_OPH2~~ print `model/axis4/axis4_OPH2-spigot.stl` instead (tools/blender/oph2_spigot.py): boss turned from 58 to 55.4 so it slides into the tube's 56 socket; six M5 through the tube's radial holes into it | 64 x 64 x 32 | 55 | fits |
| 5-axis4 | axis4_Tube | 174 x 62 x 62 | 143 | fits |
| 5-axis4 | axis4_axis5_holder | 206 x 160 x 103 | 688 | fits |
| 5-axis4 | axis4_disk1 | 68 x 68 x 7 | 13 | fits |
| 5-axis4 | axis4_disk2 | 68 x 68 x 7 | 13 | fits |
| 5-axis4 | axis4_diskCap | 56 x 56 x 2 | 2 | fits |
| 5-axis4 | axis4_housing | 100 x 80 x 25 | 22 | fits |
| 5-axis4 | axis4_housingNema | 129 x 100 x 25 | 33 | fits |
| 5-axis4 | axis4_shaft | 30 x 28 x 13 | 6 | fits |
| 5-axis4 | axis4_shaft2 | 30 x 28 x 13 | 6 | fits |
| 5-axis4 | axis4_shaft3 | 32 x 28 x 9 | 4 | fits |
| 6-axis5-6 | axis5-80T-7mm | 53 x 53 x 19 | 21 | fits |
| 6-axis5-6 | axis5-80T-rotor | 54 x 54 x 14 | 20 | fits |
| 6-axis5-6 | axis5-axis6holder1 | 89 x 77 x 45 | 43 | fits |
| 6-axis5-6 | axis5-axis6holder2 | 93 x 64 x 40 | 59 | fits |
| 6-axis5-6 | axis5-holder | 209 x 187 x 45 | 246 | fits |
| 6-axis5-6 | axis5-holder2 | 209 x 187 x 45 | 251 | fits |
| 6-axis5-6 | axis5-holderNoSplit | 205 x 187 x 89 | 502 | fits |
| 6-axis5-6 | axis5-pulley | 54 x 54 x 14 | 15 | fits |
| 6-axis5-6 | axis5-pulleySpacer | 54 x 54 x 29 | 48 | fits |
| 6-axis5-6 | axis5-quarterTurnBeltDrive | 76 x 20 x 14 | 4 | fits |
| 6-axis5-6 | axis5_Housing2Attach1 | 100 x 80 x 25 | 20 | fits |
| 6-axis5-6 | axis5_Housing2Attach2 | 100 x 80 x 25 | 20 | fits |
| gripper | Axe | 39 x 34 x 6 | 3 | fits |
| gripper | OPH_To_Gripper | 77 x 68 x 66 | 79 | fits |
| gripper | T8_Srcew_Holder | 36 x 36 x 14 | 7 | fits |
| gripper | T8_to_Axes | 26 x 10 x 10 | 1 | fits |
| gripper | grip | 83 x 41 x 10 | 16 | fits |
| gripper | mainHolder | 95 x 95 x 73 | 126 | fits |
| electronics | octopus-pro-plate (tools/blender/octopus_plate.py) | 184 x 110 x 12 | 70 | fits |
| base | spider-ring (tools/blender/spider_base.py) | 191 x 191 x 35 | ~300 | fits, top plate down |
| base | spider-arm ×3 | 274 x 90 x 35 | ~185 each | A1 on the bed diagonal (239 mm) |
| base | spider-arm-motor | 274 x 90 x 88 | ~230 | A1 on the bed diagonal (239 mm) |
| base | spider-pad ×4 (TPU) | 24 x 24 x 13 | ~3 each | A1 |
| hand | palm-front (tools/blender/hand_palm.py) | 26 x 50 x 68 | ~29 | standing on an end face, bores vertical |
| hand | palm-bench-foot (tools/blender/hand_palm.py) | 22 x 58 x 68 | ~31 | on its rear face |
| hand | palm-whiffletree-bar (tools/blender/hand_palm.py) | 4 x 8 x 50 | ~1 | flat |

Total solid volume of all listed parts: 6769 cm3 (before infill; at 40 % infill roughly 4.2 kg of PLA counting walls).

## Parts that do not fit the P2S bed as exported

Resolved: print `model/split/mainBody1_lower`, `mainBody1_upper`, `mainBody2_lower`, `mainBody2_upper` instead of the two plates (half-lap joint, glue plus 2× M4 bolts per plate).

- **mainBody1.stl** 380 x 142 x 16 mm: SPLIT
- **mainBody2.stl** 380 x 142 x 16 mm: SPLIT

## Hardware per 1:11 gearbox (5-axis4, bench-verified 2026-09-12)

The arm has two 1:11 gearboxes (axes 4 and 5; axis 6 is the belt-driven
rotor), so double these. Only the internals print twice: the axis-5 unit
uses `axis5_Housing2Attach1/2` (same 12 pin holes as `axis4_housing`) as
its housing halves, `axis5-axis6holder2` as its output plate and
`axis5-80T-7mm` as its pulley, so the second set is disk1, disk2,
diskCap ×2, shaft, shaft2, shaft3 and OPH only (2026-09-15).

| Item | Qty per gearbox | Where |
|---|---|---|
| 6812zz 60x78x10 | 2 | one on each OPH's O60 boss, outer ring in the O78 pocket of housing / housingNema |
| 6705zz 25x32x4 | 4 | one inside each OPH on the shaft journal, one in each disk's centre bore |
| brass bushing 8x10x6 | 12 | six per disk, in the O10 holes; M4 output rods pass through |
| pins O6x25 | 6 | housing ring pins |
| M4 rod | 6 output rods + cam lock rods | cut from the 1 m stock |
| M3 rod, M5x20 | per PDF | clamp-up |

Elbow pivot, not part of the gearbox but in the same folder: 2x 6804zz 20x32x7 in `axis4_axis5_holder`'s O32 x 10 side pockets on the elbow axis (z 453). The holder's two O78 pockets are not bearing seats in this arrangement.

## Repaired meshes (2026-09-14)

Four exports failed slicing (naked and non-manifold edges, inverted normals,
degenerate faces) and were run through an online repair tool. Print the
`_fixed` file in place of the original:

| Original | Repaired | Triangles | Max surface deviation |
|---|---|---|---|
| `Cults3d_v5/6-axis5-6/axis5-holder.stl` | `axis5-holder_fixed.stl` | 21626 -> 22004 | 0.03 mm |
| `Cults3d_v5/6-axis5-6/axis5-holder2.stl` | `axis5-holder2_fixed.stl` | 105908 -> 29754 | see note |
| `model/split/mainBody1_upper.stl` | `mainBody1_upper_fixed.stl` | 8504 -> 8644 | 0.02 mm |
| `model/split/mainBody2_lower.stl` | `mainBody2_lower_fixed.stl` | 5044 -> 5062 | 0.02 mm |

`axis5-holder2`: every vertex of the repaired mesh lies on the original
surface (0.004 mm) and the bounding box is unchanged, but the original had
a second, overlapping shell about 1 mm inside it (13 non-manifold edges,
inverted normals) that the repair merged away, which is where 72 % of the
triangles went. The outer envelope is intact; check the 6812 / 6810 seats
on the print with the bearings before assembly.

