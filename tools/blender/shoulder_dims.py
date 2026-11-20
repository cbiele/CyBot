"""Shoulder (axis 2), body and turning base (axis 1) (docs/superpowers/specs/2026-11-19-shoulder-base-design.md).
Shoulder frame: origin on the shoulder axis at the upper arm's mid-plane, y along the shoulder axis towards plate A,
z up, x forward (the forearm's reach). The base axis is the z axis. The elbow frame maps in as (x, y, z + E.UPPER_L).
Shoulder pitch psi: 0 = upper arm straight up, +90 = level towards +x. Base angle phi about +z."""
import math
import elbow_dims as E
import forearm_dims as F
import cycloid_math as _C

PSI_RANGE, PSI_STOPS = (-90.0, 90.0), (-92.0, 92.0)
PHI_RANGE, PHI_STOPS = (-170.0, 170.0), (-172.0, 172.0)

B6810 = E.B6810
M3_CLEAR_R, M3_INSERT_R, M3_INSERT_DEPTH, M5_CLEAR_R = 1.7, 2.0, 5.0, 2.75
NUT_AF, NUT_T = 5.8, 2.6
M3_STOCK = (40, 45, 50)
SHOULDER_DESIGN_NMM = 13.5e3                 # 1.5x the spec's 9 N·m estimate; Task 6 replaces the estimate with the model's
PRINTED_MPA = 10.0

SHOULDER_RATIO, BASE_RATIO = 80, 6.5
SHOULDER_BELT_C = round(_C.belt_centre_distance(20, 80, 420, pitch=3.0), 2)
BASE_BELT_C = round(_C.belt_centre_distance(20, 130, 477, pitch=3.0), 2)

# The printed upper arm (elbow.py): 6810 seats entered from each plate's outer face, lips on the inner faces.
PLATE_FACES = {"A": (E.Y_REAR, E.Y_REAR + E.PLATE_T), "B": (-E.Y_REAR - E.PLATE_T, -E.Y_REAR)}
LIP_FACE_Y = {"A": E.Y_REAR + E.PLATE_T - B6810[2], "B": -(E.Y_REAR + E.PLATE_T - B6810[2])}
SEAT_R = B6810[1] + 0.05                     # as elbow.py cuts it

# Hub: one half per plate, each locked to its own plate; the plates' cross members tie the halves together.
SPIGOT_R, FLANGE_T, FLANGE_R = 32.5, 6.0, 41.0
HUB_BORE_R, HUB_SHOULDER_R, HUB_FLOOR = 18.0, 27.5, 8.0
CONE = FLANGE_R - HUB_SHOULDER_R             # 45 degrees under each flange, so both halves print end-down without supports
FLANGE_Y = {"A": (PLATE_FACES["A"][1], PLATE_FACES["A"][1] + FLANGE_T), "B": (PLATE_FACES["B"][0] - FLANGE_T, PLATE_FACES["B"][0])}

# Walls: wall A outside the elbow's belt envelope; wall B far enough out for hub B's cone (and the stops between).
WALL_T = B6810[2] + E.LIP_T
WALL_Y = {"A": (71.0, 71.0 + WALL_T), "B": (-60.0, -60.0 - WALL_T)}          # (inner face, outer face)
WALL_6810_Y = {"A": (71.0, 71.0 + B6810[2]), "B": (-60.0, -60.0 - B6810[2])}
WALL_LIP_R = 31.0                            # bears on the outer ring only
HUB_Y = (WALL_Y["B"][1] - 8.0, WALL_Y["A"][1] + 1.0)   # B's journal runs on past wall B for the stop collar; A's end face takes the output plate
END_CHAMFER = 1.0

# Plate lock: M3 x 12 from inside the plate gap, through the plate's shoulder boss, into inserts in the flange.
# Only the boss's upper half (towards the elbow) is wide enough; the angles straddle plate B's index holes.
LOCK_R, LOCK_ANGLES = 36.5, (20.0, 36.0, 62.0, 118.0, 144.0, 160.0)
LOCK_HOLE_R, LOCK_BOLT_L = 1.7, 12
WALL_MIN = 1.2

# The compact's output plate: bigger, longer dogs than the forearm's, for the shoulder's torque.
OUT_PLATE_R, OUT_PLATE_T = 16.0, 5.0
DOG_PCD_R, DOG_R, DOG_H, DOG_ANGLES = 11.0, 3.5, 6.0, F.DOG_ANGLES
HUB_SCREW_L = 12.0

# Drill jig: a spigot in the Ø65 seat, fences on the plate's straight sides so it only goes on one way round.
JIG_T, JIG_SPIGOT_DEPTH, JIG_R, JIG_FENCE = 10.0, 6.0, 44.0, (E.PLATE_R + 0.1, 44.0)

# Body walls: each prints inner face down, so its feet turn outwards. The axis height leaves a NEMA23 (half 28.5) at
# slot -3 clear of wall A's foot with the shoulder belt up to 30 degrees off vertical (Task 3's call).
SHOULDER_AXIS_Z = 158.0
WALL_BOSS_R = {"A": 50.0, "B": 48.0}
WALL_BOTTOM_HALF_W, FOOT_T, FOOT_W, WINDOW_BORDER, WINDOW_RIB = 66.0, 8.0, 22.0, 9.0, 6.0
WALL_FOOT = {s: [(x, WALL_Y[s][1] + (FOOT_W / 2 if s == "A" else -FOOT_W / 2)) for x in (-52.0, -22.0, 22.0, 52.0)] for s in "AB"}
FOOT_BOLT_L = 12
BODY_MIN = 6.0

# The compact: its housing's front face on a printed cage on wall A (the R30 holes sit over wall A's 6810, and a
# boss on the wall itself would overhang its lip bore), the output plate between the carrier and the hub's A end.
COMPACT_Y = HUB_Y[1] + OUT_PLATE_T                       # the carrier's (output) face
HOUSING_FRONT_Y = COMPACT_Y + F.HUB_FACE - F.HOUSING_L
COMPACT_REAR_Y = COMPACT_Y + F.HUB_FACE
CAGE_Y, CAGE_R, CAGE_BORE_R = (WALL_Y["A"][1], HOUSING_FRONT_Y), 49.0, (26.0, 18.0)   # r26 round the hub's end, r18 round the output plate
CAGE_SCREW_R, CAGE_SCREW_ANGLES, CAGE_SCREW_L = 41.0, (0.0, 90.0, 180.0, 270.0), 12
COMPACT_BOLT_L, BOLT_HEAD_H = 45, E.BOLT_HEAD_H
R80_OD = (80 * 3.0 / math.pi - 0.762) / 2
PULLEY80_Y = COMPACT_REAR_Y + BOLT_HEAD_H + 1.0           # its hub's face, towards the compact
PULLEY80_TEETH_Y = (PULLEY80_Y + E.PULLEY_HUB + 1.5, PULLEY80_Y + E.PULLEY_HUB + 1.5 + 11.5)
SHOULDER_BELT_PLANE_Y = sum(PULLEY80_TEETH_Y) / 2
ROD_OUT = PULLEY80_Y + E.PULLEY_H - COMPACT_REAR_Y        # the input rod past the housing's rear face, through the 80T

# Stops and Hall, as on the elbow: a collar keyed onto hub B's journal end outside wall B (a tab under hub B's
# flange can't print end-down) carries the tab and the magnet; the blocks and the sensor are on wall B's outer face.
HUB_INNER_LAND_R, STOP_COLLAR_R, STOP_COLLAR_FLANGE = E.HUB_INNER_LAND_R, 29.5, 3.0
STOP_COLLAR_Y = (WALL_6810_Y["B"][1], HUB_Y[0] - 0.3 - STOP_COLLAR_FLANGE)
COLLAR_SCREW_R, COLLAR_SCREW_ANGLES, COLLAR_SCREW_L = 21.5, (90.0, 270.0), 8
KEY_ANGLES, KEY_W, KEY_DEPTH_Y = (0.0, 180.0), 6.0, 6.0
TAB_PHI, TAB_HALF, TAB_R, TAB_Y = 270.0, 12.0, (STOP_COLLAR_R - 0.1, 42.0), (WALL_Y["B"][1] - 0.5, STOP_COLLAR_Y[1])
STOP_BLOCK_DEG, STOP_R = 30.0, (31.0, 42.0)
MAGNET_R, MAGNET_D, MAGNET_AT_R, MAGNET_RECESS = 3.0, 3.0, 36.0, 0.7
SENSOR = E.SENSOR
SHOULDER_HALL = {"magnet": (MAGNET_AT_R, TAB_PHI, TAB_Y[0] - MAGNET_RECESS), "sensor_face_y": WALL_Y["B"][1]}
