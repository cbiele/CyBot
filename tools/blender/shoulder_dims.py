"""Shoulder (axis 2), body and turning base (axis 1) (docs/superpowers/specs/2026-11-21-arm-mounted-shoulder-v1-base-design.md).
Shoulder frame: origin on the shoulder axis at the upper arm's mid-plane, y along the shoulder axis towards plate A,
z up, x forward (the forearm's reach). The base axis is the z axis. The elbow frame maps in as (x, y, z + E.UPPER_L).
Shoulder pitch psi: 0 = upper arm straight up, +90 = level towards +x. Base angle phi about +z."""
import math
import elbow_dims as E
import forearm_dims as F
import cycloid_math as _C

PHI_RANGE, PHI_STOPS = (-170.0, 170.0), (-172.0, 172.0)

B6810 = E.B6810
M3_CLEAR_R, M3_INSERT_R, M3_INSERT_DEPTH, M5_CLEAR_R = 1.7, 2.0, 5.0, 2.75
NUT_AF, NUT_T = 5.8, 2.6
M3_STOCK = (40, 45, 50)
SHOULDER_DESIGN_NMM = 13.5e3                 # 1.5x the spec's 9 N·m estimate; the hub lock, the output link and the stops
SHOULDER_CURRENT_CAP_A = 2.0 * 13.5 / (0.59 * 80)   # the driver's cap so a stall can't pass 13.5 N·m (17HS19: 0.59 N·m at 2.0 A, 80:1)
PRINTED_MPA = 10.0

SHOULDER_RATIO, BASE_RATIO = 80, 6.5
SHOULDER_BELT_C = E.SH_BELT_C
BASE_BELT_C = round(_C.belt_centre_distance(20, 130, 477, pitch=3.0), 2)

# The printed upper arm (elbow.py): 6810 seats entered from each plate's outer face, lips on the inner faces.
PLATE_FACES = {"A": (E.Y_REAR, E.Y_REAR + E.PLATE_T), "B": (-E.Y_REAR - E.PLATE_T, -E.Y_REAR)}
LIP_FACE_Y = {"A": E.Y_REAR + E.PLATE_T - B6810[2], "B": -(E.Y_REAR + E.PLATE_T - B6810[2])}
SEAT_R = B6810[1] + 0.05                     # as elbow.py cuts it

# Still read by the base (Task 3 of the 2026-11-21 plan replaces them).
HUB_SHOULDER_R, WALL_LIP_R, WALL_MIN, BODY_MIN, INSERT_WALL_MIN = 27.5, 31.0, 1.2, 6.0, 2.0

# The compact's output plate: bigger, longer dogs than the forearm's, for the shoulder's torque.
OUT_PLATE_R, OUT_PLATE_T = 16.0, 5.0
DOG_PCD_R, DOG_R, DOG_H, DOG_ANGLES = 11.0, 3.5, 6.0, F.DOG_ANGLES
HUB_SCREW_L, HUB_BORE_R, HUB_FLOOR = 12.0, 18.0, 8.0
END_CHAMFER = 1.0

# The shoulder drive rides in the arm (2026-11-21 spec), the elbow's joint mirrored: the compact's rear face on plate
# B's inner face, its housing turning with the arm, its output plate dogged into a fixed hub. The hub turns in plate
# A's 6810 (the arm turns on it); a lug keyed on its journal end clamps that 6810's inner ring, carries the stop tab
# and the magnet, and holds three tubes splayed down to a socket bracket bolted on the turntable. Fixed parts on
# plate A's side stay inside the elbow belt's sweep in its y band, and past it beyond; on plate B's side a post
# outside the shoulder belt's envelope carries a 625 on the input rod's end.
SHOULDER_AXIS_Z = 46.5
PSI_STOPS = E.SH_PSI_STOPS                   # shoulder.py checks this is the widest the turntable's rim allows, less 2
PSI_RANGE = (PSI_STOPS[0] + 2.0, PSI_STOPS[1] - 2.0)
TURNTABLE_R = 89.0
BOLT_HEAD_H = E.BOLT_HEAD_H
COMPACT_REAR_Y = E.SH_COMPACT_REAR_Y
COMPACT_Y = COMPACT_REAR_Y + F.HUB_FACE      # the carrier's (output) face
OUT_PLATE_Y = (COMPACT_Y, COMPACT_Y + OUT_PLATE_T)
RING_ZONE = (B6810[1] - 5.0, B6810[1])       # plate A's 6810's turning outer ring, radially
HUB_HEAD_Y = OUT_PLATE_Y[1] - OUT_PLATE_T - 3.3 + HUB_SCREW_L   # the floor screws' heads: 3.3 into the carrier's inserts
HUB = {"face_y": OUT_PLATE_Y[1], "shoulder_r": 26.8, "land_r": B6810[0], "bearing_y": (LIP_FACE_Y["A"], PLATE_FACES["A"][1]),
       "end_y": 68.0, "bore_r": HUB_BORE_R}
assert HUB["shoulder_r"] <= E.LIP_IN_R - 0.5
LUG_GAP = E.SH_TAB_GAP                       # off plate A's outer face, past the inner ring
TUBE_PLANE_Y = 74.6                          # >= the elbow belt's envelope + 1 + a socket's radius and wall
LUG = {"y0": PLATE_FACES["A"][1], "sleeve_r": 31.0, "spider_y": (TUBE_PLANE_Y - E.SOCKET_R - E.SOCKET_WALL, TUBE_PLANE_Y + E.SOCKET_R + E.SOCKET_WALL)}
assert TUBE_PLANE_Y - E.SOCKET_R - E.SOCKET_WALL >= E.BELT_ENVELOPE_Y + 1.0
KEY_ANGLES, KEY_W, KEY_DEPTH_Y = (90.0, 250.0), 6.0, 6.0   # not 180 apart: the lug only goes on one way
COLLAR_SCREW_R, COLLAR_SCREW_ANGLES, COLLAR_SCREW_L, LUG_CB_Y = 21.5, (0.0, 180.0), 10, LUG["spider_y"][0] + 7.0
TAB_PHI, TAB_HALF, TAB_R = E.SH_TAB_PHI, E.SH_TAB_HALF, (LUG["sleeve_r"] - 0.1, E.SH_TAB_R1)
TAB_Y = (PLATE_FACES["A"][1] + LUG_GAP, PLATE_FACES["A"][1] + E.SH_STOP_H)
MAGNET_R, MAGNET_D, MAGNET_AT_R, MAGNET_RECESS = 3.0, 3.0, E.SH_MAGNET_AT_R, 0.7
SENSOR = E.SENSOR
# The tubes in the plane y = TUBE_PLANE_Y: (lug mouth, bracket mouth) in (x, z). The axis is only SHOULDER_AXIS_Z over
# the turntable and the lug's spider is r31, so there's no room for a V under it: the tubes run out sideways to two
# towers on the bracket, one horizontal each side of the axis (they take the torque) and a diagonal (the weight).
_LR = 31.0
_LZ = 19.3
TUBE_ENDS = {"front": ((math.sqrt(_LR ** 2 - _LZ ** 2), -_LZ), (45.0, -_LZ)),
             "rear": ((-math.sqrt(_LR ** 2 - _LZ ** 2), _LZ), (-45.0, _LZ)),
             "diagonal": ((math.sqrt(_LR ** 2 - _LZ ** 2), _LZ), (45.0, 6.0))}
# Each tower's outer face runs from x at its top out to root_x on the base, so it takes its tubes' bending within
# PRINTED_MPA (it can't be deeper in y: below the tubes' band is the elbow belt's sweep).
BRACKET = {"x": 64.0, "root_x": {"front": 72.0, "rear": 84.0}, "tower_x": 45.0, "tops": {"front": 15.0, "rear": 27.0},
           "flange_y": (55.0, LUG["spider_y"][0]), "flange_t": 5.0}
BRACKET_BOLTS = [(-56.0, 61.0), (-33.0, 61.0), (33.0, 61.0), (56.0, 61.0)]   # outside the hub and lug (r31), so a driver comes straight down
# Under the lug, which otherwise hangs off its three tubes: a saddle 0.2 under it from past plate A's stops back over the
# bracket's flange, slid in from behind along the axis (narrow enough to pass under the spider), and a tail behind the
# flange screwed down into the turntable, where a driver reaches.
CRADLE = {"half_x": 10.0, "y": (TAB_Y[1] + 1.0, LUG["spider_y"][1] - 0.2), "tail_y": (LUG["spider_y"][1] + 0.3, LUG["spider_y"][1] + 6.3),
          "gap": 0.2, "seat_h": 8.0, "top_z": -26.0}
CRADLE_SCREWS = [(-5.0, LUG["spider_y"][1] + 3.3), (5.0, LUG["spider_y"][1] + 3.3)]
CRADLE_SCREW_L = 12                          # through the tail's 8 into the turntable's inserts
# Under the hub inside the arm, between the compact's output and plate A: two mirrored halves split on the axis, each
# slid in from its own side (the hub only rises away from a half as it comes in), each with a foot tab out past the hub
# screwed down into the turntable (y 18 keeps their inserts clear of the ring's, underneath).
HUB_CRADLE = {"y": (HUB["face_y"] + 0.4, PLATE_FACES["A"][0] - 1.0), "split": 0.1, "half_x": 20.0, "tab_x": 33.0,
              "tab_t": 6.0, "gap": 0.2, "top_z": -19.5}
HUB_CRADLE_SCREWS = [(30.0, 18.0), (-30.0, 18.0)]
HUB_CRADLE_SCREW_L = 10                      # through the tab's 6 into the turntable's inserts
EAR = {"x": (-BRACKET["root_x"]["rear"] - 2.0, BRACKET["root_x"]["front"] + 2.0), "y": (53.0, LUG["spider_y"][1] + 2.0)}   # the turntable's tab under the bracket, outside the arm's y band
B625 = (2.5, 8.0, 5.0)                       # bore r, seat r (params.json seat_625), width
POST = {"y": (E.SH_BELT_ENVELOPE_Y - 1.0, E.SH_BELT_ENVELOPE_Y - 1.0 - 1.0 - B625[2]), "half": 12.0, "top": B625[1] + 4.0,
        "lip_r": 6.5, "lip_t": 1.0, "foot_x": 24.0, "foot_t": 5.0}   # (inner face, outer face): the 625 from outside against a lip
POST_BOLTS = [(-18.0, sum(POST["y"]) / 2), (18.0, sum(POST["y"]) / 2)]
TURNTABLE_SCREW_L = 8                       # down through a 5 foot into the turntable's inserts
ROD_OUT = COMPACT_REAR_Y - POST["y"][1]     # the input rod past the housing's rear face, through plate B and the 80T into the 625
PULLEY80_Y = E.SH_PULLEY_Y0                  # its hub's face, 1 off plate B's outer face
R80_OD = E.R80_OD
ARM_LOAD_N = 60.0                            # the arm's weight (about 3 kg) doubled for knocks
BELT_PULL_N = 2 * 60.0                       # 2x a 9 mm 3M belt's working tension (about 60 N)
MOTORS = {"17": {"sq": 42.3, "hole": 31.0 / 2, "hole_r": M3_CLEAR_R, "pilot_r": 22.4 / 2 + 0.1, "length": 60.0, "shaft": 24.0, "head": (2.75, 3.0)}}
MOTOR_SLOT = E.SH_MOTOR_SLOT
STOP_BLOCK_DEG, STOP_R = E.SH_STOP_BLOCK_DEG, E.SH_STOP_R
SHOULDER_HALL = {"magnet": (MAGNET_AT_R, TAB_PHI, TAB_Y[0] + MAGNET_RECESS), "sensor_face_y": PLATE_FACES["A"][1]}

# The base (axis 1), V1's way (2026-11-21 spec): the turntable, the 130T ring under it and a cylinder hanging from the
# ring turn together on two 6810s seated in the drum's hub tube. The cylinder's shoulder and a retainer on its end
# clamp the inner rings through a spacer; a lip between the seats takes the outer rings. Top down: the base stop's tab
# under the turntable, the ring's teeth below it (so the belt never meets the tab), the base motor's 20T at the same
# band, shaft up from the motor hanging under the drum's shelf, beside a flat in the drum's wall.
TURNTABLE_Z = -SHOULDER_AXIS_Z
TURNTABLE_T = 8.0
TT_HUB_Z0 = TURNTABLE_Z - TURNTABLE_T         # the turntable's underside: the ring's top face
PHI_TAB_H = 10.0
PHI_TAB_Z = (TT_HUB_Z0, TT_HUB_Z0 - PHI_TAB_H)  # (top, bottom)
PITCH, GROOVE_R, GROOVE_DEPTH, FLANGE_LIP, FLANGE_T_P, TEETH_W = 3.0, 1.05, 1.30, 1.5, 1.5, 11.5
RING_Z = (PHI_TAB_Z[1] - 1.0 - 1.5 - TEETH_W, PHI_TAB_Z[1] - 1.0 - 1.5)   # the teeth band, the 20T's and the ring's: the belt 1.0 under the tab
BASE20_HUB_Z = (RING_Z[0] - FLANGE_T_P - E.PULLEY_HUB, RING_Z[0] - FLANGE_T_P)   # the 20T's hub down towards the motor
BASE_PLATE_T = 5.0
BASE_PLATE_Z = (BASE20_HUB_Z[0] - 1.0 - BASE_PLATE_T, BASE20_HUB_Z[0] - 1.0)   # the clamp plate on the shelf
SHELF_T = 5.0
SHELF_Z = (BASE_PLATE_Z[0] - SHELF_T, BASE_PLATE_Z[0])
BASE_MOTOR_L = 50.0                          # a 17HS19's 48 body, plus 2, under the shelf
BASE_MOTOR_FACE_Z = SHELF_Z[0]
RING_TEETH, RING_SCREW_R, RING_SCREW_ANGLES, RING_SCREW_L = 130, 36.5, (45.0, 135.0, 225.0, 315.0), 20
# The ring's teeth as tools/blender/htd3m_pulley.py cuts them (copied: importing it runs that script).


def od_r(teeth):
    return teeth * PITCH / math.pi / 2 - 0.381


RING_Z0 = RING_Z[0] - FLANGE_T_P                                              # its lower face
RING_CB_Z = TT_HUB_Z0 - (RING_SCREW_L - (M3_INSERT_DEPTH - 0.5))              # the ring screws' heads, counterbored up into the ring
DRUM_TOP = RING_Z0 - 1.5
DRUM_R, DRUM_H = 96.0, 75.0
BENCH_Z = DRUM_TOP - DRUM_H                  # the drum's underside: the bench
DRUM = (DRUM_R, DRUM_TOP, BENCH_Z)
DRUM_WALL, DRUM_RIB = 1.8, 1.8              # a shell open top and bottom, like V1's ring: the turntable covers it
RIB_FILLET = 5.0                             # each rib's fillets onto the hub tube, either side, down its full height
BASE_6810_SPACING = 50.0
BASE_6810_Z = (DRUM_TOP - B6810[2], DRUM_TOP - B6810[2] - BASE_6810_SPACING)   # each bearing's lower face: upper, lower
CYL = {"r": B6810[0], "shoulder_r": 26.8, "bore_r": 18.0, "end_z": BASE_6810_Z[1] + 0.3}   # the end 0.3 inside the lower inner ring, so the retainer clamps
SPACER_R, SPACER_Z = 26.8, (BASE_6810_Z[1] + B6810[2], BASE_6810_Z[0])
RETAINER = {"r": 26.8, "t": 3.5, "bore_r": 12.0, "screw_r": 21.5, "angles": (90.0, 210.0, 330.0), "screw_l": 8}
HUB_TUBE_R = B6810[1] + 0.05 + 2.45          # the drum's hub tube round the two seats, down to the bench
TT_LIP_R = 31.0                              # the hub tube's lip between the seats, on the outer rings only
TEARDROP = math.sqrt(2.0)                    # the socket bosses' undersides come to a point at 45 degrees, on the leg's rib
SHELF_UNDER = 10.0                           # the shelf's walls at their outer end, under the shelf
FIXED_BASE_MAX_CM3 = 265.0                  # solid: the shell slices at about 1.13 g per cm3 (309 g at 273), so plate 5 stays under 300 g
BASE_TOP_Z, BASE_T, BASE_DISC_R = DRUM_TOP, DRUM_H, DRUM_R   # the legs' sockets still read these
BASE_MOTOR_DEG = 270.0
BASE_U = (math.cos(math.radians(BASE_MOTOR_DEG)), math.sin(math.radians(BASE_MOTOR_DEG)))
# The base motor is turned 45 degrees on its shaft: square to the belt, its inboard screws would sit under the belt's
# spans, where no driver reaches them; turned, they sit on the belt's centre line and out to its sides.
BASE_MOTOR_SCREWS = [(15.5 * math.sqrt(2) * math.cos(math.radians(90 * k)), 15.5 * math.sqrt(2) * math.sin(math.radians(90 * k))) for k in range(4)]   # (r, t)
BASE_MOTOR_REACH = 42.3 / 2 * math.sqrt(2)    # the turned square's corner, from the shaft
FLAT_R = BASE_BELT_C - MOTOR_SLOT - BASE_MOTOR_REACH - 1.0   # the drum's wall at 270 is a plane this far out: the motor hangs beside it


def base_motor_at(slot=0.0):
    return tuple((BASE_BELT_C + slot) * c for c in BASE_U)


BASE_MOTOR_AT = (base_motor_at()[0], base_motor_at()[1], BASE_MOTOR_FACE_Z)
# The clamp plate on the shelf: the motor's four M3s go down through it and slots in the shelf into the motor's face;
# set the belt's tension by hand along the slots and tighten (no push screw: under the turntable no driver reaches one).
BASE_PLATE_HALF_R, BASE_PLATE_HALF_T = 26.0, 26.0
BASE_MOTOR_SCREW_L = 14                      # plate 5 + shelf 5 + 4 into the motor
SHELF = {"r": (FLAT_R - DRUM_WALL, BASE_BELT_C + BASE_PLATE_HALF_R + MOTOR_SLOT + 2.0), "half": 36.0, "wall": 5.0}   # walls 5 off the turned motor's corners
BASE_DESIGN_NMM = 4.0e3                     # a 17HS19 stalled through 6.5:1
# Stops: one tab under the turntable, above the belt's band; one block on the drum opposite it at home, where the belt
# hugs the ring (its spans run 207..333 degrees, towards the motor). They meet at +-172.
PHI_TAB_DEG, PHI_HALF, PHI_R = 180.0, 4.0, (66.0, 88.0)   # r66 clear of the belt on the ring, r88 short of the base motor's 20T
PHI_BLOCK_TOP = PHI_TAB_Z[1] + 7.0
BASE_HALL = {"magnet": (78.0, PHI_TAB_DEG, PHI_TAB_Z[1] + MAGNET_RECESS), "sensor_top": PHI_TAB_Z[1] - 0.5}
HALL_POST_HALF = 5.0
# The base's assembly order, as the print sheet gives it: each part slides home along z past what's already in. A part
# that comes up from below the bench needs the drum tipped or lifted, so it must come before the legs go on.
BASE_ORDER = ("upper 6810", "turntable, ring and cylinder", "base-spacer", "lower 6810", "base-retainer", "base motor", "legs on", "clamp the feet")

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
