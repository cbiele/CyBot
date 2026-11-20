"""Shoulder (axis 2), body and turning base (axis 1) (docs/superpowers/specs/2026-11-19-shoulder-base-design.md).
Shoulder frame: origin on the shoulder axis at the upper arm's mid-plane, y along the shoulder axis towards plate A,
z up, x forward (the forearm's reach). The base axis is the z axis. The elbow frame maps in as (x, y, z + E.UPPER_L).
Shoulder pitch psi: 0 = upper arm straight up, +90 = level towards +x. Base angle phi about +z."""
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
HUB_Y = (WALL_Y["B"][1] - 1.0, WALL_Y["A"][1] + 1.0)   # B's open end, A's end face (the compact's output plate)
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
