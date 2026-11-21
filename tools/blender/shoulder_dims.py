"""Shoulder (axis 2), body and turning base (axis 1) (docs/superpowers/specs/2026-11-19-shoulder-base-design.md).
Shoulder frame: origin on the shoulder axis at the upper arm's mid-plane, y along the shoulder axis towards plate A,
z up, x forward (the forearm's reach). The base axis is the z axis. The elbow frame maps in as (x, y, z + E.UPPER_L).
Shoulder pitch psi: 0 = upper arm straight up, +90 = level towards +x. Base angle phi about +z."""
import math
import elbow_dims as E
import forearm_dims as F
import cycloid_math as _C

PSI_STOPS = (-93.0, 93.0)                    # shoulder.py checks this is the widest the turntable's rim allows, less 2
PSI_RANGE = (PSI_STOPS[0] + 2.0, PSI_STOPS[1] - 2.0)
PHI_RANGE, PHI_STOPS = (-170.0, 170.0), (-172.0, 172.0)

B6810 = E.B6810
M3_CLEAR_R, M3_INSERT_R, M3_INSERT_DEPTH, M5_CLEAR_R = 1.7, 2.0, 5.0, 2.75
NUT_AF, NUT_T = 5.8, 2.6
M3_STOCK = (40, 45, 50)
SHOULDER_DESIGN_NMM = 13.5e3                 # 1.5x the spec's 9 N·m estimate; the hub lock, the output link and the stops
SHOULDER_CURRENT_CAP_A = 2.0 * 13.5 / (0.59 * 80)   # the driver's cap so a stall can't pass 13.5 N·m (17HS19: 0.59 N·m at 2.0 A, 80:1)
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
WALL_6810_Y = {"B": (-60.0, -60.0 - B6810[2])}   # wall A has no bearing: it holds the stub
WALL_LIP_R = 31.0                            # bears on the outer ring only
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

# Drill jig, plate B only: a spigot in the Ø65 seat, fences on the plate's straight sides, and a key just past the
# round end that lands on the plate if the jig is turned half round, so it can't seat the wrong way.
JIG_T, JIG_SPIGOT_DEPTH, JIG_R, JIG_FENCE = 10.0, 6.0, 44.0, (E.PLATE_R + 0.1, 44.0)
JIG_KEY = (8.0, (E.PLATE_R + 0.6, E.PLATE_R + 4.6))   # half width, z range below the axis

# Body walls, low (2026-11-20 spec): each stands on the turntable on its bottom face, held by M3s from under the
# turntable into inserts in that face. Each prints inner face down. The axis height is the lowest that keeps
# everything under it 3 above the turntable at psi 0 and still lets the stops sit past 92 (shoulder.py checks both).
SHOULDER_AXIS_Z = 46.5
WALL_BOSS_R = {"A": 46.0, "B": 48.0}
WALL_BOTTOM_HALF_W = {"A": 35.0, "B": 40.0}
WALL_B_FRONT = (44.0, -52.0)                 # wall B stops at x 44 above z -52: the palm passes at elbow 150, wrist pitch 90 (head_concept)
# An inward foot on each wall's bottom (inside the elbow belt's sweep, outside hub B's cone) gives the joint a second
# row of inserts, for the arm's weight off the wall's plane.
# Wall B's bearing sits over its own inserts, so one row does there.
WALL_FOOT_IN = {"A": (WALL_Y["A"][0] - 11.0, WALL_Y["A"][0])}
WALL_FOOT_T, WALL_FOOT_HALF = 6.0, 30.0
WALL_INSERTS = {"A": [(x, sum(WALL_Y["A"]) / 2) for x in (-25.0, 0.0, 25.0)] + [(x, sum(WALL_FOOT_IN["A"]) / 2) for x in (-24.0, 24.0)],
                "B": [(x, sum(WALL_Y["B"]) / 2) for x in (-25.0, 10.0, 25.0)]}   # B's middle one beside the Hall's leads
WALL_A_SLOT = 1.5                            # wall A's holes in the turntable, slotted along y: it finds its place on the stub
ARM_LOAD_N, WALL_INSERT_N = 60.0, 400.0      # the arm's weight (about 3 kg) doubled for knocks; a third of an M3 insert's pull-out in PLA
WALL_SCREW_L = 12
WALL_A_BORE_R = 30.1                         # the stub's r30 body, a slip fit
BODY_MIN, INSERT_WALL_MIN = 6.0, 2.0
TURNTABLE_R = 89.0                           # provisional (Task 4): both walls' bottoms with 2 of edge

# The compact inside the arm on a fixed stub (2026-11-20 spec). The stub's flange sits on wall A's outer face, so it
# prints flange-down; its land carries plate A's 6810, whose inner ring is clamped between the stub's shoulder and a
# spacer on the housing's rear face. The stub stops STUB_GAP short of the housing, so its screws clamp through the
# spacer and the inner ring. A pilot in the housing's r15 rear lip centres the compact; a 625 at the stub's outer end
# carries the long input rod next to the 80T.
COMPACT_REAR_Y = E.Y_REAR - 0.5
COMPACT_Y = COMPACT_REAR_Y - F.HUB_FACE                  # the carrier's (output) face
STUB_GAP, BOLT_HEAD_H = 0.2, E.BOLT_HEAD_H
B625 = (2.5, 8.0, 5.0)                                   # bore r, seat r (params.json seat_625), width
STUB = {"bore_r": REAR_HUB_PROUD_R, "bearing_r": B6810[0], "shoulder_r": 26.8, "body_r": 30.0, "flange_r": 42.0,
        "flange_t": 7.0, "pilot_r": 14.9, "pilot_y": COMPACT_REAR_Y - 0.5, "lip_r": 6.5,
        "y": (COMPACT_REAR_Y + STUB_GAP, WALL_Y["A"][1] + 7.0), "shoulder_y": (PLATE_FACES["A"][1], PLATE_FACES["A"][1] + 1.0),
        "screw_l": 16, "screw_engage": 4.0, "cb_r": 3.3}
STUB["head_y"] = COMPACT_REAR_Y - STUB["screw_engage"] + STUB["screw_l"]
STUB_SPACER = (B6810[0] + 0.1, STUB["shoulder_r"], COMPACT_REAR_Y, LIP_FACE_Y["A"])   # r0, r1, y0, y1
STUB_FIX_R, STUB_FIX_ANGLES, STUB_FIX_L = 38.0, (45.0, 135.0, 225.0, 315.0), 10   # flange to wall A's inserts, plain holes
HUB_B_NOSE = (E.LIP_IN_R - 0.5, COMPACT_Y - OUT_PLATE_T, LIP_FACE_Y["B"])           # r, y0 (its face), y1
HUB_Y = (WALL_Y["B"][1] - 8.0, HUB_B_NOSE[1])           # B's journal end (past wall B for the stop collar), its nose face
RING_ZONE = (B6810[1] - 5.0, B6810[1])                   # the 6810's turning outer ring, radially
R80_OD = (80 * 3.0 / math.pi - 0.762) / 2
PULLEY80_Y = STUB["y"][1] + 1.0                          # its hub's face, 1.0 off the stub's outer end
PULLEY80_TEETH_Y = (PULLEY80_Y + E.PULLEY_HUB + 1.5, PULLEY80_Y + E.PULLEY_HUB + 1.5 + 11.5)
SHOULDER_BELT_PLANE_Y = sum(PULLEY80_TEETH_Y) / 2
ROD_OUT = PULLEY80_Y + E.PULLEY_H - COMPACT_REAR_Y        # the input rod past the housing's rear face, through the stub and the 80T

# Stops and Hall, as on the elbow: a collar keyed onto hub B's journal end outside wall B (a tab under hub B's
# flange can't print end-down) carries the tab and the magnet; the blocks and the sensor are on wall B's outer face.
HUB_INNER_LAND_R, STOP_COLLAR_R, STOP_COLLAR_FLANGE = E.HUB_INNER_LAND_R, 29.5, 3.0
STOP_COLLAR_Y = (WALL_6810_Y["B"][1], HUB_Y[0] - 0.3 - STOP_COLLAR_FLANGE)
COLLAR_SCREW_R, COLLAR_SCREW_ANGLES, COLLAR_SCREW_L = 21.5, (90.0, 270.0), 8
KEY_ANGLES, KEY_W, KEY_DEPTH_Y = (0.0, 160.0), 6.0, 6.0   # not 180 apart: the collar only goes on tab down
TAB_PHI, TAB_HALF, TAB_R, TAB_Y = 270.0, 12.0, (STOP_COLLAR_R - 0.1, 42.0), (WALL_Y["B"][1] - 0.5, STOP_COLLAR_Y[1])
STOP_BLOCK_DEG, STOP_R = 30.0, (31.0, 42.0)
MAGNET_R, MAGNET_D, MAGNET_AT_R, MAGNET_RECESS = 3.0, 3.0, 36.0, 0.7
SENSOR = E.SENSOR

# The shoulder motor (2026-11-20 spec): behind the arm, its body outwards (+y) so it never enters the arm's swing,
# the belt 10 degrees above level towards the rear, so the motor's plate clears the turntable's rim. The motor and its
# 20T go on the drop-in plate at the bench; the plate drops into a box that's part of wall A, from outside, onto the
# box's seat, the 20T through the seat's window. Four M3s from outside through slots in the plate into the seat, and a
# pull screw through the box's end into a tab on the plate set the belt's tension. Local frame about the motor at
# slot 0: u along the belt away from the 80T, w square to it in the belt's plane (upwards), y as the shoulder frame's.
SHOULDER_MOTOR_DEG, MOTOR_SLOT, MOTOR_WALL = 10.0, 3.0, "A"
BELT_U = (-math.cos(math.radians(SHOULDER_MOTOR_DEG)), math.sin(math.radians(SHOULDER_MOTOR_DEG)))   # (x, z) from the 80T to the motor
BELT_W = (BELT_U[1], -BELT_U[0])


def motor_at(slot=0.0):
    return tuple((SHOULDER_BELT_C + slot) * c for c in BELT_U)


SHOULDER_MOTOR_AT = (motor_at()[0], SHOULDER_BELT_PLANE_Y, motor_at()[1])
MOTORS = {"17": {"sq": 42.3, "hole": 31.0 / 2, "hole_r": M3_CLEAR_R, "pilot_r": 22.4 / 2 + 0.1, "length": 60.0, "shaft": 24.0, "head": (2.75, 3.0)},
          "23": {"sq": 57.0, "hole": 47.14 / 2, "hole_r": M5_CLEAR_R, "pilot_r": 38.5 / 2 + 0.1, "length": 76.0, "shaft": 21.0, "head": (4.25, 5.0)}}
PULLEY20_HUB_Y = (PULLEY80_TEETH_Y[1] + 1.5, PULLEY80_TEETH_Y[1] + 1.5 + E.PULLEY_HUB)   # its hub towards the motor
SEAT_Y = (PULLEY20_HUB_Y[1] + 1.0, PULLEY20_HUB_Y[1] + 9.0)       # the seat in wall A's box, under the plate
MOTOR_PLATE_Y = (SEAT_Y[1], SEAT_Y[1] + 6.0)
MOTOR_FACE_Y = MOTOR_PLATE_Y[1]                                   # the motor's face on the plate's outer face
PLATE_HALF = 48.0
PLATE_MOUNT = [(40.0, 40.0), (40.0, -40.0), (-40.0, 40.0), (-40.0, -40.0)]   # inserts in the seat, about the motor at slot 0
PLATE_SCREW_L = 10
SEAT_WINDOW = (29.0 + MOTOR_SLOT, 29.5)      # u, w half: the 23's M5 heads (23.6 + 4.25 + 0.5) at either end of the slot
TAB = {"u": (PLATE_HALF - 14.0, PLATE_HALF), "w": 7.0, "y": (MOTOR_PLATE_Y[0], MOTOR_PLATE_Y[1] + 6.0)}
PULL_Y = sum(TAB["y"]) / 2
BOX = {"u": (-SHOULDER_BELT_C + 45.0, PLATE_HALF + 4.0 + 8.0), "w": 60.0, "slab": 8.0, "end": PLATE_HALF + 4.0,
       "back_u0": -SHOULDER_BELT_C, "slab_top": MOTOR_PLATE_Y[1], "end_top": TAB["y"][1] + 1.0}
PULL_SCREW_L, PULL_BORE = 20, 12.0          # the pull screw's insert, then a clearance bore on into the tab

# The base (axis 1): the base axis is the shoulder frame's z axis. The turntable turns on two 6810s on a printed Ø50
# spigot rising from the drum; a cap and a spacer clamp the inner rings onto the spigot's shoulder, the turntable's
# top lip and the 130T ring (screwed under its hub) hold the outer rings. The base motor stands shaft-down on a shelf
# of the drum beside the turntable, as on V1, its top 3 under the turntable so everything on the turntable passes over
# it; that sets the 20T's band, so the ring's, so the bearings' spacing, from the top down.
TURNTABLE_Z = -SHOULDER_AXIS_Z
TURNTABLE_T = 8.0
BASE_MOTOR_L = 50.0                          # a 17HS19's 48 body, plus 2
BASE_MOTOR_TOP = TURNTABLE_Z - TURNTABLE_T - 3.0
BASE_PLATE_T = 5.0
BASE_PLATE_Z = (BASE_MOTOR_TOP - BASE_MOTOR_L - BASE_PLATE_T, BASE_MOTOR_TOP - BASE_MOTOR_L)   # the motor's face on its top
SHELF_T = 5.0
SHELF_Z = (BASE_PLATE_Z[0] - SHELF_T, BASE_PLATE_Z[0])
BASE20_HUB_Z = (SHELF_Z[0] - 1.0 - E.PULLEY_HUB, SHELF_Z[0] - 1.0)   # the 20T hangs under the shelf, hub up
PITCH, GROOVE_R, GROOVE_DEPTH, FLANGE_LIP, FLANGE_T_P, TEETH_W = 3.0, 1.05, 1.30, 1.5, 1.5, 11.5
RING_Z = (BASE20_HUB_Z[0] - FLANGE_T_P - TEETH_W, BASE20_HUB_Z[0] - FLANGE_T_P)   # the teeth band, the 20T's and the ring's
TT_HUB_Z0 = RING_Z[1] + FLANGE_T_P           # the hub's lower face, on the lower 6810's
BASE_6810_Z = (TURNTABLE_Z - 7.0 - B6810[2], TT_HUB_Z0)   # each bearing's lower face
BASE_6810_SPACING = BASE_6810_Z[0] - BASE_6810_Z[1]
TT_LIP_R, RING_LIP_R = 31.0, 31.0
TT_HUB_R = 40.0                              # slim, so the base push screw's driver has its 30
SPIGOT = {"r": 25.0, "bore_r": 16.0, "shoulder_r": 27.0, "top": BASE_6810_Z[0] + B6810[2] - 0.3}
SPACER_R, SPACER_Y = 27.0, (BASE_6810_Z[1] + B6810[2], BASE_6810_Z[0])
CAP_R, CAP_T, CAP_SCREW_R, CAP_SCREW_ANGLES, CAP_SCREW_L = 27.0, 3.0, 20.5, (90.0, 210.0, 330.0), 8
RING_TEETH, RING_SCREW_R, RING_SCREW_ANGLES, RING_SCREW_L = 130, 36.5, (45.0, 135.0, 225.0, 315.0), 20
# The ring's teeth as tools/blender/htd3m_pulley.py cuts them (copied: importing it runs that script).


def od_r(teeth):
    return teeth * PITCH / math.pi / 2 - 0.381


RING_Z0 = RING_Z[0] - FLANGE_T_P                                              # its lower face
BENCH_Z = None                               # set below, from the drum
DRUM_TOP = RING_Z0 - BOLT_HEAD_H - 1.5       # under the ring's screw heads, which turn with it
DRUM_R, DRUM_H = 96.0, 75.0
BENCH_Z = DRUM_TOP - DRUM_H                  # the drum's underside: the bench
DRUM = (DRUM_R, DRUM_TOP, BENCH_Z)
BASE_TOP_Z, BASE_T, BASE_DISC_R = DRUM_TOP, DRUM_H, DRUM_R   # the legs' sockets (Task 5) still read these
BASE_MOTOR_DEG = 270.0
BASE_U = (math.cos(math.radians(BASE_MOTOR_DEG)), math.sin(math.radians(BASE_MOTOR_DEG)))


def base_motor_at(slot=0.0):
    return tuple((BASE_BELT_C + slot) * c for c in BASE_U)


BASE_MOTOR_AT = (base_motor_at()[0], base_motor_at()[1], BASE_PLATE_Z[1])
# The plate: along the motor's radius (r) and across it (t), about the motor at slot 0. Two slotted M3s each side into
# inserts through the shelf; a push screw from the inboard side, its head towards the axis, through a lug on the shelf.
BASE_PLATE_HALF_R, BASE_PLATE_HALF_T = 25.0, 33.0
BASE_PLATE_INSERTS = [(-15.0, -27.0), (15.0, -27.0), (-15.0, 27.0), (15.0, 27.0)]   # (r, t) about the motor at slot 0
BASE_PLATE_SCREW_L = 8
SHELF = {"r": (BASE_BELT_C - BASE_PLATE_HALF_R - 4.0 - 5.0, BASE_BELT_C + BASE_PLATE_HALF_R + MOTOR_SLOT + 1.0),
         "half": 36.0, "wall": 6.0, "window": 23.0, "wall_r0": 90.0}
BASE_LUG = {"r": (SHELF["r"][0], SHELF["r"][0] + 5.0), "half": 7.0}   # its insert fills it: the screw's head stays out towards the axis
BASE_PUSH_L = 12
BASE_DESIGN_NMM = 4.0e3                     # a 17HS19 stalled through 6.5:1
# Stops: one tab under the turntable, one block on the drum opposite it at home; they meet at +-172. Both between the
# ring's flange and the base motor's plate.
PHI_TAB_DEG, PHI_HALF, PHI_R = 180.0, 4.0, (65.0, 88.0)   # 4 degrees half: they meet at 172; r65 is 1.4 off the ring's flange, r88 short of the base motor
PHI_TAB_Z, PHI_BLOCK_TOP = (TURNTABLE_Z - TURNTABLE_T, BASE_PLATE_Z[1] + 3.0), BASE_PLATE_Z[1] + 10.0
BASE_HALL = {"magnet": (78.0, PHI_TAB_DEG, PHI_TAB_Z[1] + MAGNET_RECESS), "sensor_top": PHI_TAB_Z[1] - 0.5}
HALL_POST_HALF = 5.0
SHOULDER_HALL = {"magnet": (MAGNET_AT_R, TAB_PHI, TAB_Y[0] - MAGNET_RECESS), "sensor_face_y": WALL_Y["B"][1]}

# Legs (2026-11-20 spec): four Ø9 aluminium tubes, 250 long, about 15 degrees below level, in sockets on the drum's
# side, so the drum's underside and the four pads all sit on the bench: five contacts. The sockets' mouths are set
# from the bench so the pads land on it.
LEG_DEG = 15.0
LEG_PHI = (45.0, 135.0, 225.0, 315.0)        # clear of the base motor's shelf at 270
TUBE_L, TUBE_LEG_R = 250.0, 4.5
SOCKET = {"r": 4.6, "depth": 25.0, "boss_r": 10.0, "floor": 3.0, "mouth_r": BASE_DISC_R + 4.0}
PINCH_AT = 12.5                              # the M3 pinch insert, from the mouth along the socket
FOOT = {"sleeve": 20.0, "boss_r": 8.0, "floor": 3.0, "pad_r": 18.0, "pad_t": 6.0}
PAD_R, PAD_T, PAD_RECESS = 15.0, 4.0, 2.0    # Ø30 x 4 TPU, 2 proud of the foot
_SIN, _COS = math.sin(math.radians(LEG_DEG)), math.cos(math.radians(LEG_DEG))
SOCKET_MOUTH_Z = (BENCH_Z + (PAD_T - PAD_RECESS) + 2.0 + FOOT["boss_r"] * _COS + FOOT["floor"] * _SIN
                  + (TUBE_L - SOCKET["depth"]) * _SIN)   # the pads then land on the bench
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
