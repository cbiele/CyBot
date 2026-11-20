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

# The stub-mount compact (cycloid_poc.py -- --stub-mount): M3 inserts in the rear housing's face, between its R30
# bolts. The stub's inner face must clear the rear carrier's hub, which turns and stands 1.0 proud of that face.
STUB_SCREW_R, STUB_SCREW_ANGLES = 21.5, (0.0, 90.0, 180.0, 270.0)
REAR_HUB_PROUD_R = 20.0 / 2 + 1.0            # the carrier hub's Ø20 (params.json hub_6804), plus 1.0

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
WALL_B_FRONT = (44.0, -52.0)                 # wall B stops at x 44 above z -52: the palm passes at elbow 150, wrist pitch 90 (head_concept)
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

# The shoulder motor: 48 degrees off straight down towards the rear, so a NEMA23 clears wall A's edge, body inboard
# (towards wall A) behind a swap plate on an upright bracket on the turntable, slotted along the belt line.
SHOULDER_MOTOR_DEG, MOTOR_SLOT = 48.0, 3.0
BELT_U = (-math.sin(math.radians(SHOULDER_MOTOR_DEG)), -math.cos(math.radians(SHOULDER_MOTOR_DEG)))   # (x, z) from the 80T to the motor


def motor_at(slot=0.0):
    return tuple((SHOULDER_BELT_C + slot) * c for c in BELT_U)


SHOULDER_MOTOR_AT = (motor_at()[0], SHOULDER_BELT_PLANE_Y, motor_at()[1])
MOTORS = {"17": {"sq": 42.3, "hole": 31.0 / 2, "hole_r": M3_CLEAR_R, "pilot_r": 22.4 / 2 + 0.1, "length": 60.0, "shaft": 24.0},
          "23": {"sq": 57.0, "hole": 47.14 / 2, "hole_r": M5_CLEAR_R, "pilot_r": 38.5 / 2 + 0.1, "length": 76.0, "shaft": 21.0}}
BRACKET_Y = (PULLEY80_Y - 1.0 - 8.0, PULLEY80_Y - 1.0)          # the 20T's hub 1.0 off its face, as the elbow's
SWAP_Y = (BRACKET_Y[0] - 5.0, BRACKET_Y[0])                      # the motor's face on the swap plate's far side
SWAP_HALF = 43.0
PLATE_MOUNT = [(36.0, 0.0), (0.0, 36.0), (-36.0, 0.0), (0.0, -36.0)]   # inserts in each swap plate, about the motor's axis
SWAP_SCREW_L = 12
CHAMFER_D = 52.0                                                 # the swap plate's corner towards the 80T, square to the belt line
LUG_D, LUG_HALF_W = (CHAMFER_D + MOTOR_SLOT + 1.0, CHAMFER_D + MOTOR_SLOT + 11.0), 7.0
PUSH_SCREW_L = 20
BRACKET_BOX = (-50.0, 56.0, -52.0, 52.0)                          # x0, x1 about the motor; z1 about it (z0 is the turntable)
BRACKET_WINDOW_R = 12.0
BRACKET_FOOT_Y = (103.0, BRACKET_Y[0])
BRACKET_FOOT = [(-37.0, 0.0), (0.0, 0.0), (37.0, 0.0)]           # x about the motor; y at the foot's middle

# The base (axis 1): the base axis is the shoulder frame's z axis. The turntable turns on two 6810s on a printed Ø50
# spigot rising from the fixed base; a cap and a spacer clamp the inner rings onto the spigot's shoulder, the
# turntable's top lip and the 130T ring (screwed under its hub) hold the outer rings. One piece each fits the bed.
TURNTABLE_Z = -SHOULDER_AXIS_Z
TURNTABLE_T = 8.0
TURNTABLE_XY = (-149.0, 99.0, -93.0, 122.0)                     # the walls' and bracket's feet, the electronics area
BASE_6810_Z = (TURNTABLE_Z - 7.0 - B6810[2], TURNTABLE_Z - 7.0 - B6810[2] - 45.0)   # each bearing's lower face; centres 45 apart
TT_LIP_R, RING_LIP_R = 31.0, 31.0
TT_HUB_R, TT_HUB_Z0 = 44.0, BASE_6810_Z[1]                       # the hub's lower face, on the lower 6810's
SPIGOT = {"r": 25.0, "bore_r": 16.0, "shoulder_r": 27.0, "top": BASE_6810_Z[0] + B6810[2] - 0.3}
SPACER_R, SPACER_Y = 27.0, (BASE_6810_Z[1] + B6810[2], BASE_6810_Z[0])
CAP_R, CAP_T, CAP_SCREW_R, CAP_SCREW_ANGLES, CAP_SCREW_L = 27.0, 3.0, 20.5, (90.0, 210.0, 330.0), 8
RING_TEETH, RING_SCREW_R, RING_SCREW_ANGLES, RING_SCREW_L = 130, 38.5, (45.0, 135.0, 225.0, 315.0), 20
# The ring's teeth as tools/blender/htd3m_pulley.py cuts them (copied: importing it runs that script).
PITCH, GROOVE_R, GROOVE_DEPTH, FLANGE_LIP, FLANGE_T_P, TEETH_W = 3.0, 1.05, 1.30, 1.5, 1.5, 11.5


def od_r(teeth):
    return teeth * PITCH / math.pi / 2 - 0.381


RING_Z = (TT_HUB_Z0 - FLANGE_T_P - TEETH_W, TT_HUB_Z0 - FLANGE_T_P)          # the teeth band
RING_Z0 = RING_Z[0] - FLANGE_T_P                                              # its lower face
BASE_TOP_Z = RING_Z[0] - 9.5 - 5.0                                            # the 20T's teeth on the band, over a 5 plate
BASE_T, BASE_DISC_R, BASE_ARM_HALF, BASE_ARM_END = 8.0, 96.0, 42.0, -152.0
BASE_MOTOR_DEG = 270.0
BASE_U = (math.cos(math.radians(BASE_MOTOR_DEG)), math.sin(math.radians(BASE_MOTOR_DEG)))


def base_motor_at(slot=0.0):
    return tuple((BASE_BELT_C + slot) * c for c in BASE_U)


BASE_MOTOR_AT = (base_motor_at()[0], base_motor_at()[1], BASE_TOP_Z)
BASE_PLATE_HALF, BASE_PLATE_T = 37.0, 5.0
BASE_PLATE_INSERTS = [(-31.0, -31.0), (31.0, -31.0), (-31.0, 31.0), (31.0, 31.0)]   # in the fixed base, about the motor at slot 0
BASE_PLATE_SCREW_L = 10
BASE_LUG = (BASE_BELT_C - BASE_PLATE_HALF - MOTOR_SLOT - 1.0, 8.0, 7.0, 8.5)        # its face's radius, thickness, half width, height
BASE_PUSH_L = 16
BASE_MOTOR_L = 60.0
BASE_DESIGN_NMM = 4.0e3                     # a 17HS19 stalled through 6.5:1
# Stops: one tab under the turntable, one block on the fixed base opposite it at home; they meet at +-172.
PHI_TAB_DEG, PHI_HALF, PHI_R = 180.0, 4.0, (66.0, 90.0)
PHI_TAB_Z, PHI_BLOCK_TOP = (TURNTABLE_Z - TURNTABLE_T, -214.0), -207.0
BASE_HALL = {"magnet": (78.0, PHI_TAB_DEG, PHI_TAB_Z[1] + MAGNET_RECESS), "sensor_top": PHI_TAB_Z[1] - 0.5}
HALL_POST_HALF = 5.0
ELECTRONICS_AREA = (-51.0, 99.0, -50.0, 50.0, 25.0)              # x0, x1, y0, y1 on the turntable, and the parts' height
ELECTRONICS_PILOTS = [(-46.0, -45.0), (94.0, -45.0), (-46.0, 45.0), (94.0, 45.0), (40.0, 0.0), (67.0, 0.0), (94.0, 0.0)]
SHOULDER_HALL = {"magnet": (MAGNET_AT_R, TAB_PHI, TAB_Y[0] - MAGNET_RECESS), "sensor_face_y": WALL_Y["B"][1]}

# Legs: four Ø9 aluminium tubes, 250 long, in sockets on the fixed base's rim. The sockets rise inwards from a mouth
# at the bed's level, so the fixed base still prints flat on its underside.
LEG_DEG = 45.0                               # the shallowest the spec allows: the widest footprint, the pads well under the motor
LEG_PHI = (45.0, 135.0, 225.0, 315.0)
TUBE_L, TUBE_LEG_R = 250.0, 4.5
SOCKET = {"r": 4.6, "depth": 25.0, "boss_r": 10.0, "floor": 3.0, "mouth_r": BASE_DISC_R + 4.0}
SOCKET_MOUTH_Z = BASE_TOP_Z - BASE_T + SOCKET["boss_r"] * math.cos(math.radians(LEG_DEG))   # the boss's lowest point on the bed
PINCH_AT = 12.5                              # the M3 pinch insert, from the mouth along the socket
FOOT = {"sleeve": 20.0, "boss_r": 8.0, "floor": 3.0, "pad_r": 18.0, "pad_t": 6.0}
PAD_R, PAD_T, PAD_RECESS = 15.0, 4.0, 2.0    # Ø30 x 4 TPU, 2 proud of the foot
CLAMP_TAB = (34.0, 34.0, 6.0)                # outwards from the pad, flat for a bench clamp


def leg_dir(phi):
    c = math.cos(math.radians(LEG_DEG))
    return (c * math.cos(math.radians(phi)), c * math.sin(math.radians(phi)), -math.sin(math.radians(LEG_DEG)))


def leg(phi):
    """(socket mouth, socket bottom, foot point: the tube's lower end) for the leg at phi."""
    d = leg_dir(phi)
    m = (SOCKET["mouth_r"] * math.cos(math.radians(phi)), SOCKET["mouth_r"] * math.sin(math.radians(phi)), SOCKET_MOUTH_Z)
    s = tuple(m[i] - SOCKET["depth"] * d[i] for i in range(3))
    return m, s, tuple(s[i] + TUBE_L * d[i] for i in range(3))


LEGS = [(leg(p)[0], leg(p)[2]) for p in LEG_PHI]
FOOT_BOTTOM_Z = (leg(LEG_PHI[0])[2][2] - FOOT["floor"] * math.sin(math.radians(LEG_DEG))
                 - FOOT["boss_r"] * math.cos(math.radians(LEG_DEG)) - 2.0)    # 2 of solid under the sleeve's lowest point
FOOT_PAD_Z = FOOT_BOTTOM_Z - (PAD_T - PAD_RECESS)                           # the bench
FOOT_PADS = [(f[0], f[1], FOOT_PAD_Z) for _, f in LEGS]
