"""V2 head concept on the current arm: real cycloid STLs, dummy motors, placeholder roll tube and fork.
A visual layout, not print geometry. World frame is cybot-master's: roll axis along +x at y=0, z=555.
Axis 4 sits inline in the V1 holder's Ø68 bore; axes 5 and 6 are belted on a 188. The gripper motor stays
behind axis 6 and drives the three-finger hand through the rod: by default a T8 lead screw in the palm pulling
the whiffletree; with --t8-through the screw itself runs through a 20-1-hollow-t8 from the motor's coupler; with
--compact-drive a 20:1 compact sits on axis 6's output.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/head_concept.py [-- --t8-through | -- --compact-drive]
Writes model/head-concept.blend and model/head-concept/*.png (head-concept-t8.blend and head-concept/t8-through/, or
head-concept-compact.blend and head-concept/compact-drive/)."""
import bpy, bmesh, json, math, os, sys, mathutils
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
import forearm_dims as F
import wrist_dims as W
import elbow_dims as E
import shoulder_dims as S

ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
MODEL = os.path.join(ROOT, "model")
COMPACT_DRIVE = "--compact-drive" in sys.argv
SHOULDER = "--shoulder" in sys.argv           # the V2 shoulder, body, turning base and legs (model/shoulder/) under the elbow
ELBOW = "--elbow" in sys.argv or SHOULDER     # the V2 elbow and upper arm (model/elbow/) under the offset wrist
OFFSET_WRIST = "--offset-wrist" in sys.argv or ELBOW   # UR-style wrist on the tube forearm's flange (model/wrist/), axis 6 the hollow T8
T8_THROUGH = "--t8-through" in sys.argv or OFFSET_WRIST
TUBE_FOREARM = "--tube-forearm" in sys.argv or OFFSET_WRIST   # axis 4 compact at the elbow end turns the 190 aluminium tube out to a wrist flange
OUT = os.path.join(MODEL, "head-concept", *(["shoulder"] if SHOULDER else ["elbow"] if ELBOW else ["offset-wrist"] if OFFSET_WRIST else ["tube-forearm"] if TUBE_FOREARM else ["compact-drive"] if COMPACT_DRIVE else ["t8-through"] if T8_THROUGH else []))
BLEND = os.path.join(MODEL, "head-concept-shoulder.blend" if SHOULDER else "head-concept-elbow.blend" if ELBOW else "head-concept-wrist.blend" if OFFSET_WRIST else "head-concept-tube.blend" if TUBE_FOREARM else "head-concept-compact.blend" if COMPACT_DRIVE else "head-concept-t8.blend" if T8_THROUGH else "head-concept.blend")
PLACE = json.load(open(os.path.join(MODEL, "placements.json")))

ROLL_Z, PITCH_X = 555.0, 250.0                 # both V1's, so the reach stays comparable
HOUSING_R, HOUSING_L, HUB_FRONT = 34.0, 38.6, 39.6
Z_DISK0, COLLAR = 12.8, 1.0
AX6_FOLDER, AX6_Z_DISK0, AX6_HOUSING_L = ("20-1-hollow-t8", 9.8, 32.6) if T8_THROUGH else ("20-1-hollow", Z_DISK0, HOUSING_L)
AX6_HUB_FRONT = AX6_HOUSING_L + 1.0
AX4_REAR_X = 36.4                              # housing front flush with the holder's bore step at x=75
AX5_REAR_Y = -80.6                             # housing front on the fork arm's outer face, y=-42
AX6_REAR_X = 270.0
SQUARE = 42.3
PANCAKE_L, MOTOR34_L, SHAFT_L = 23.0, 34.0, 20.0
BELT_C = round(C.belt_centre_distance(20, 40, 188), 2)
R20, R40 = 20 / math.pi, 40 / math.pi
BELT_PLANE = -11.75
MOUNT_T = 6.0
COUPLER_L, COUPLER_R = 25.0, 9.5
SHAFT_IN_COUPLER = 12.5
FORK_IN, FORK_OUT = 36.0, 42.0
TUBE_X0, TUBE_X1 = 85.0, 146.0
FORK_ROOT_X, FORK_ROOT_T = 146.0, 6.0        # far enough back that the wrist motor clears at full pitch
if TUBE_FOREARM:                               # the fork, pitch body and axis 6 keep their spacing from the fork root
    FORK_ROOT_X = AX4_REAR_X + F.FLANGE_FACE
    PITCH_X = FORK_ROOT_X + 104.0
    AX6_REAR_X = PITCH_X + 20.0
AX6_Y = 0.0
if OFFSET_WRIST:                               # wrist_dims is in the forearm frame, which starts at the axis 4 housing's rear face
    PITCH_X = AX4_REAR_X + W.PITCH_X
    AX6_REAR_X = AX4_REAR_X + W.AX6_REAR_X
    AX6_Y = W.AX6_Y
AX4_COL = "Axis 4 compact, 188 belt, drives the tube" if TUBE_FOREARM else "Axis 4 inline, 20:1"
SHELL_R, TUBE_R = 36.0, 25.0                   # 6810: 50 bore, 65 OD
ADAPTER_BOSS_R, ADAPTER_ROD_R = (12.5, 5.25) if T8_THROUGH else (9.0, 3.0)
ADAPTER_BOSS_T, ADAPTER_PLATE_T = 4.0, 6.0     # the boss lifts the turning plate over axis 6's bolt heads, as on the test arm
AX7_REAR_Z = AX6_HUB_FRONT + ADAPTER_BOSS_T + ADAPTER_PLATE_T   # adapter plate's front face (compact's rear face), in axis 6's frame
ROD_START_Z, ROD_TIP_IN_COMPACT = -35.0, 31.0  # butts the motor shaft in the coupler; flush with the compact's front 625
HAND_BACK = 70.0                               # compact's hub to the finger axes: a guess, the palm's rear shell isn't designed
PROX_LEN, PAIR_PITCH = 40.0, 45.0              # hand_finger.py, hand_palm.py
PALM_BACK, TENDON_LIFT = 20.0, 5.0             # palm plate's rear face behind the finger axes; tendons run 5 palmar, so lifting the palm puts them on the screw axis
# Lead screw stack in axis 6's frame. The tendons pull the nut forward, so the rear collar bears on the 608's inner ring and its outer ring on the bulkhead's lip.
ROD_L = 100.0
COUPLER_58_Z = (52.5, 77.5)                    # 5 to 8 mm, about Ø19 x 25; centred on the rod's tip
STACK_Z = AX7_REAR_Z + 1.0 if T8_THROUGH else COUPLER_58_Z[1] + 1.0
REAR_COLLAR_Z = (STACK_Z, STACK_Z + 8.0)
BEARING_Z = (STACK_Z + 8.0, STACK_Z + 15.0)    # 608, 8 x 22 x 7
BULKHEAD_Z1, LIP_R = STACK_Z + 18.0, 9.5
FRONT_COLLAR_Z = (STACK_Z + 15.0, STACK_Z + 23.0)
NUT_L, NUT_FLANGE_R, TRAVEL = 15.0, 11.0, 16.0   # travel: the tendon that two knuckles take up
NUT_Z_CLOSED = FRONT_COLLAR_Z[1] + 0.5
BAR_T = 4.0
TENDON_RUN = 10.0                              # open whiffletree to the palm's rear face: keeps the tendons close to straight
GRIP_MOTOR_L = PANCAKE_L if COMPACT_DRIVE else MOTOR34_L

COLORS = {"cycloid": (0.25, 0.55, 0.85, 1), "disk": (0.95, 0.75, 0.2, 1), "motor": (0.12, 0.12, 0.14, 1),
          "steel": (0.75, 0.75, 0.78, 1), "belt": (0.05, 0.05, 0.05, 1), "pulley": (0.9, 0.45, 0.15, 1),
          "fixed": (0.62, 0.64, 0.68, 1), "moving": (0.45, 0.72, 0.82, 1), "v1": (0.82, 0.80, 0.74, 1), "ghost": (0.85, 0.3, 0.3, 1)}
MATS, COLS = {}, {}
scene = None


def material(key):
    if key not in MATS:
        m = bpy.data.materials.new(key); m.diffuse_color = COLORS[key]; MATS[key] = m
    return MATS[key]


def collection(name):
    if name not in COLS:
        c = bpy.data.collections.new(name); scene.collection.children.link(c); COLS[name] = c
    return COLS[name]


def place(o, col, mat, matrix=None):
    for oc in list(o.users_collection):
        oc.objects.unlink(o)
    collection(col).objects.link(o)
    o.data.materials.clear(); o.data.materials.append(material(mat))
    if matrix is not None:
        o.data.transform(matrix)
    return o


def stl(path, name):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name; return o


def frame(origin, axis, xdir):
    z, x = Vector(axis).normalized(), Vector(xdir).normalized()
    y = z.cross(x)
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2], m[i][3] = x[i], y[i], z[i], origin[i]
    return m


def flip():
    return Matrix.Diagonal((1, -1, -1, 1))


def cycloid(folder, prefix, col, m, z_disk0=Z_DISK0):
    """The print-orientation STLs back in the assembly frame of cycloid_poc.py, then into the world."""
    base = os.path.join(MODEL, "cycloid-poc", folder)
    poses = {"housing-rear": ("cycloid", Matrix()), "housing-front": ("cycloid", flip()),
             "carrier-rear": ("moving", flip()), "carrier-front": ("moving", Matrix()),
             "disk-a": ("disk", Matrix.Translation((C.E, 0, z_disk0))),
             "disk-b": ("disk", Matrix.Translation((-C.E, 0, z_disk0 + 6.0 + COLLAR))),
             "eccentric": ("steel", Matrix())}
    for part, (mat, local) in poses.items():
        place(stl(os.path.join(base, part + ".stl"), f"{prefix} {part}"), col, mat, m @ local)


def motor(name, col, m, z_face, direction, length):
    """A NEMA17 dummy: face at z_face, body running along direction (+1 or -1) in the unit's frame, shaft the other way."""
    h = SQUARE / 2
    z0, z1 = sorted((z_face, z_face + direction * length))
    body = L.box(name, -h, h, -h, h, z0, z1)
    place(body, col, "motor", m)
    sz0, sz1 = sorted((z_face, z_face - direction * SHAFT_L))
    place(L.cyl_z(name + " shaft", 0, 0, 2.5, sz0, sz1, n=24), col, "steel", m)


def ring_prism(name, col, mat, m, r1, r2, c, z0, z1, t):
    """The belt: closed loop round two circles (r2 at the origin, r1 at x=c), thickness t outwards."""
    def outline(a, b):
        phi = math.asin((b - a) / c); pts = []
        for k in range(49):
            ang = (math.pi / 2 + phi) + (math.pi - 2 * phi) * k / 48
            pts.append((b * math.cos(ang), b * math.sin(ang)))
        for k in range(25):
            ang = -(math.pi / 2 - phi) + (math.pi - 2 * phi) * k / 24
            pts.append((c + a * math.cos(ang), a * math.sin(ang)))
        return pts
    inner, outer = outline(r1, r2), outline(r1 + t, r2 + t)
    bm = bmesh.new(); n = len(inner)
    vs = [[bm.verts.new((p[0], p[1], z)) for p in pts] for pts, z in ((inner, z0), (outer, z0), (outer, z1), (inner, z1))]
    for a in range(4):
        for i in range(n):
            bm.faces.new((vs[a][i], vs[a][(i + 1) % n], vs[(a + 1) % 4][(i + 1) % n], vs[(a + 1) % 4][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
    return place(o, col, mat, m)


def belted_drive(prefix, col, m, folder="20-1-hollow", plate=True, big=40, belt=188, outboard=False):
    """Mount plate, big pulley (40T, or the 60T of axes 4 and 5 on the offset wrist), 20T, belt and pancake, with the motor
    beside the housing as on the POC mount."""
    c = round(C.belt_centre_distance(20, big, belt), 2)
    r_big = big / math.pi
    if plate:
        x1 = c + 3.5 + SQUARE / 2 + 3
        p = L.cyl_z(prefix + " mount (placeholder for the 188)", 0, 0, HOUSING_R, -MOUNT_T, 0, n=96)
        L.union(p, L.box("arm", 10, x1, -SQUARE / 2 - 3, SQUARE / 2 + 3, -MOUNT_T, 0))
        place(p, col, "fixed", m)
    path = os.path.join(MODEL, "wrist", "pulley-60T.stl") if big == 60 else os.path.join(MODEL, "cycloid-poc", folder, "pulley-40T.stl")
    pulley = stl(path, f"{prefix} {big}T")
    place(pulley, col, "pulley", m @ Matrix.Translation((0, 0, -MOUNT_T - 1)) @ flip())
    place(L.cyl_z(prefix + " 20T (dummy)", c, 0, R20 + 0.5, BELT_PLANE - 4.5, BELT_PLANE + 4.5, n=40), col, "pulley", m)
    ring_prism(f"{prefix} belt {belt}", col, "belt", m, R20, r_big, c, BELT_PLANE - 3, BELT_PLANE + 3, 1.4)
    if outboard:   # on a plate past the belt, mirrored about the belt plane
        motor(prefix + " pancake", col, m @ Matrix.Translation((c, 0, 0)), 2 * BELT_PLANE, -1, PANCAKE_L)
    else:
        motor(prefix + " pancake", col, m @ Matrix.Translation((c, 0, 0)), 0.0, 1, PANCAKE_L)


def axis4():
    col = "Axis 4 inline, 20:1"
    m = frame((AX4_REAR_X, 0, ROLL_Z), (1, 0, 0), (0, 0, 1))
    cycloid("20-1-compact", "ax4", col, m)
    z_motor = -1.0 - 1.0 - COUPLER_L - (SHAFT_L - SHAFT_IN_COUPLER)
    motor("ax4 34 mm motor", col, m @ Matrix.Translation((0, 0, z_motor)), 0.0, -1, MOTOR34_L)
    place(L.cyl_z("ax4 coupler", 0, 0, COUPLER_R, -2.0 - COUPLER_L, -2.0, n=48), col, "steel", m)
    place(L.cyl_z("ax4 Ø5 rod", 0, 0, 2.5, -2.0 - COUPLER_L / 2, 31.0, n=32), col, "steel", m)
    cup = L.cyl_z("ax4 motor cup (placeholder)", 0, 0, HOUSING_R - 0.05, z_motor, 0, n=96)
    L.cut(cup, L.cyl_z("bore", 0, 0, HOUSING_R - 3, z_motor + 5, 1, n=96))
    L.cut(cup, L.cyl_z("pilot", 0, 0, 12, z_motor - 1, z_motor + 6, n=48))
    place(cup, "Structure placeholders", "fixed", m)
    return z_motor


def axis4_tube():
    """The compact at the elbow end, motor on top on the 188; its output turns the aluminium tube out to the wrist flange."""
    col = AX4_COL
    m = frame((AX4_REAR_X, 0, ROLL_Z), (1, 0, 0), (0, 0, 1))
    cycloid("20-1-compact", "ax4", col, m)
    if OFFSET_WRIST:   # geared 60:1 like axis 5 for the head's roll load pitched sideways
        belted_drive("ax4", col, m, "20-1-compact", big=F.AX4_TEETH, belt=F.AX4_BELT)
    else:
        belted_drive("ax4", col, m, "20-1-compact")
    place(L.cyl_z("ax4 Ø5 rod", 0, 0, 2.5, -23.5, 31.0, n=32), col, "steel", m)
    flip_back = Matrix.Diagonal((1, -1, -1, 1))
    parts = {"forearm-outer-tube": ("fixed", Matrix.Translation((0, 0, F.OUTER_X[0]))),
             "ax4-output-plate": ("moving", Matrix.Translation((0, 0, F.PLATE_X[0]))),
             "ax4-tube-hub": ("moving", Matrix.Translation((0, 0, F.HUB_X[0])))}
    if not OFFSET_WRIST:   # on the offset wrist the head bracket is glued on the tube in the hub's place
        parts["wrist-flange-hub"] = ("moving", flip_back @ Matrix.Translation((0, 0, -F.FLANGE_FACE)))
    for name, (mat, pose) in parts.items():
        place(stl(os.path.join(MODEL, "forearm-tube", name + ".stl"), "ax4 " + name), col, mat, m @ pose)
    place(ring("ax4 aluminium tube 9 x 11", F.TUBE_R, 4.5, *F.TUBE_X), col, "steel", m)
    for x in (F.REAR_BRG_X, F.FRONT_BRG_X):
        place(ring("ax4 6701", F.BRG_SEAT_R, 6.0, *x), col, "cycloid", m)


def ax5_frame():
    if OFFSET_WRIST:   # across the forearm end, output to the hand side (-y), pancake back and down
        a = math.radians(W.AX5_MOTOR_ANGLE)
        return frame((PITCH_X, W.AX5_REAR_Y, ROLL_Z), (0, -1, 0), (math.cos(a), 0, math.sin(a)))
    return frame((PITCH_X, AX5_REAR_Y, ROLL_Z), (0, 1, 0), (-1, 0, 0))


def axis5():
    col = "Axis 5 belted, 40:1"
    m = ax5_frame()
    cycloid("20-1-compact", "ax5", col, m)
    if OFFSET_WRIST:   # its mounts are inside its brackets; axis 5 is geared 60:1
        belted_drive("ax5", col, m, plate=False, big=W.AX5_TEETH, belt=W.AX5_BELT, outboard=W.PANCAKE_OUTBOARD)
    else:
        belted_drive("ax5", col, m)
    place(L.cyl_z("ax5 Ø5 rod", 0, 0, 2.5, -23.5, 31.0, n=32), col, "steel", m)


def axis6():
    col = "Axis 6 hollow, gripper motor behind"
    m = ax6_frame()
    cycloid(AX6_FOLDER, "ax6", col, m, AX6_Z_DISK0)
    belted_drive("ax6", col, m, AX6_FOLDER, plate=not OFFSET_WRIST)
    if not OFFSET_WRIST:   # the offset wrist's L-bracket carries the gripper motor's disc
        bracket = stl(os.path.join(MODEL, "cycloid-poc", AX6_FOLDER, "motor7-bracket.stl"), "ax6 gripper motor bracket")
        z_ext = sorted(v.co.z for v in bracket.data.vertices)
        place(bracket, col, "fixed", m @ Matrix.Translation((0, 0, -56.0 - z_ext[0])))
    motor("ax7 gripper motor", col, m @ Matrix.Translation((0, 0, -56.0)), 0.0, -1, GRIP_MOTOR_L)
    place(L.cyl_z("ax7 coupler", 0, 0, COUPLER_R, -50.0, -25.0, n=48), col, "steel", m)


def ax6_frame():
    return frame((AX6_REAR_X, AX6_Y, ROLL_Z), (1, 0, 0), (0, 0, 1))


def adapter(m6):
    a = L.cyl_z("adapter, axis 6 output to the hand (placeholder)", 0, 0, HOUSING_R, AX7_REAR_Z - ADAPTER_PLATE_T, AX7_REAR_Z, n=128)
    L.union(a, L.cyl_z("boss", 0, 0, ADAPTER_BOSS_R, AX6_HUB_FRONT, AX7_REAR_Z - ADAPTER_PLATE_T + 0.01, n=64))
    if COMPACT_DRIVE:
        L.cut(a, L.cyl_z("rear hub clearance", 0, 0, 12.0, AX7_REAR_Z - 1.5, AX7_REAR_Z + 1, n=64))
    L.cut(a, L.cyl_z("rod", 0, 0, ADAPTER_ROD_R, AX6_HUB_FRONT - 1, AX7_REAR_Z + 1, n=32))
    place(a, "Structure placeholders", "moving", m6)


def compact_drive():
    """Returns the finger axes' and shell's start z in axis 6's frame."""
    col = "Gripper drive, past axis 6"
    m6 = ax6_frame()
    cycloid("20-1-compact", "ax7", col, m6 @ Matrix.Translation((0, 0, AX7_REAR_Z)))
    place(L.cyl_z("ax7 Ø5 rod", 0, 0, 2.5, ROD_START_Z, AX7_REAR_Z + ROD_TIP_IN_COMPACT, n=32), col, "steel", m6)
    hub_z = AX7_REAR_Z + HUB_FRONT
    place(L.cyl_z("spool Ø16 (placeholder)", 0, 0, 8.0, hub_z + 1.0, hub_z + 13.0, n=48), col, "pulley", m6)
    return hub_z + HAND_BACK, hub_z, 0.0


def ring(name, r_out, r_in, z0, z1):
    o = L.cyl_z(name, 0, 0, r_out, z0, z1, n=64)
    L.cut(o, L.cyl_z("bore", 0, 0, r_in, z0 - 1, z1 + 1, n=32))
    return o


def screw_drive():
    """Shown with the fingers open, nut and whiffletree at the forward end of their travel. Returns as compact_drive does."""
    col = "Gripper drive, past axis 6"
    m6 = ax6_frame()
    if T8_THROUGH:
        screw_z0 = ROD_START_Z
    else:
        rod_tip = ROD_START_Z + ROD_L
        assert COUPLER_58_Z[0] < rod_tip < COUPLER_58_Z[1], "rod must end inside the 5 to 8 coupler"
        place(L.cyl_z("ax7 Ø5 rod", 0, 0, 2.5, ROD_START_Z, rod_tip, n=32), col, "steel", m6)
        place(L.cyl_z("5 to 8 coupler", 0, 0, COUPLER_R, *COUPLER_58_Z, n=48), col, "steel", m6)
        screw_z0 = rod_tip + 1.0
    place(ring("rear collar", 9.0, 4.0, *REAR_COLLAR_Z), col, "pulley", m6)
    place(ring("608", NUT_FLANGE_R, 4.0, *BEARING_Z), col, "cycloid", m6)
    place(ring("front collar", 9.0, 4.0, *FRONT_COLLAR_Z), col, "pulley", m6)
    z_open = NUT_Z_CLOSED + TRAVEL
    z_bar0 = z_open + NUT_L + 1.0
    z_bar1 = z_bar0 + BAR_T
    print("T8 SCREW mm", round(z_bar0 + 2.0 - screw_z0, 1), "unsupported span mm", round(BEARING_Z[0] - -25.0, 1))
    place(L.cyl_z("T8 lead screw", 0, 0, 4.0, screw_z0, z_bar0 + 2.0, n=32), col, "steel", m6)   # tip stays inside the whiffletree's hole
    place(L.cyl_z("T8 nut", 0, 0, NUT_FLANGE_R, z_open, z_open + NUT_L, n=48), col, "pulley", m6)
    place(L.box("nut carrier, its ends slide in the shell", -8, 8, -31, 31, z_open, z_open + NUT_L), col, "moving", m6)
    bar = L.box("whiffletree with a hole for the screw (placeholder)", -8, 8, -25, 25, z_bar0, z_bar1)
    L.cut(bar, L.cyl_z("screw hole", 0, 0, 5.0, z_bar0 - 1, z_bar1 + 1, n=32))
    place(bar, col, "disk", m6)
    palm_rear = z_bar1 + TENDON_RUN
    for sy in (-1, 1):
        place(L.cyl_z("tendon", 0, sy * PAIR_PITCH / 2, 0.5, z_bar1, palm_rear, n=12), col, "belt", m6)
    head = L.box("screw bulkhead (placeholder)", -20 + TENDON_LIFT, 22 + TENDON_LIFT, -31, 31, BEARING_Z[0], BULKHEAD_Z1)
    L.cut(head, L.cyl_z("608 seat", 0, 0, NUT_FLANGE_R, BEARING_Z[0] - 1, BEARING_Z[1], n=64))
    L.cut(head, L.cyl_z("lip", 0, 0, LIP_R, BEARING_Z[0], BULKHEAD_Z1 + 1, n=64))
    place(head, "Structure placeholders", "moving", m6)
    return palm_rear + PALM_BACK, AX7_REAR_Z, TENDON_LIFT


def hand(z_fingers, z_shell, lift):
    """Palm front and straight pair fingers, palm's +y up; the rear shell joins them to the drive. No thumb yet."""
    col = "Three-finger hand"
    m = frame((AX6_REAR_X + z_fingers, AX6_Y, ROLL_Z + lift), (0, -1, 0), (1, 0, 0))
    hand_dir = os.path.join(MODEL, "hand")
    place(stl(os.path.join(hand_dir, "palm-front.stl"), "palm-front"), col, "v1", m)
    for sz in (-1, 1):
        at = m @ Matrix.Translation((0, 0, sz * PAIR_PITCH / 2))
        place(stl(os.path.join(hand_dir, "finger-proximal.stl"), "finger-proximal"), col, "v1", at)
        place(stl(os.path.join(hand_dir, "finger-distal.stl"), "finger-distal"), col, "v1", at @ Matrix.Translation((PROX_LEN, 0, 0)))
    x0, x1 = AX6_REAR_X + z_shell, AX6_REAR_X + z_fingers - PALM_BACK
    zc = ROLL_Z + lift
    shell = L.box("palm rear shell (placeholder, not designed)", x0, x1, AX6_Y - 34, AX6_Y + 34, zc - 25, zc + 25)
    L.cut(shell, L.box("hollow", x0 - 1, x1 - 3, AX6_Y - 31, AX6_Y + 31, zc - 22, zc + 22))
    place(shell, "Structure placeholders", "moving")


def to_world(o, m):
    return place(o, "Structure placeholders", "moving", m)


def unprint(y_bed):
    """Inverse of wrist.py's print poses (x kept, y onto -z with the given face on the bed)."""
    return Matrix(((1, 0, 0, 0), (0, 0, -1, y_bed), (0, 1, 0, 0), (0, 0, 0, 1)))


def wrist_parts():
    to_world = Matrix.Translation((AX4_REAR_X, 0, ROLL_Z))
    wrist = os.path.join(MODEL, "wrist")
    place(stl(os.path.join(wrist, "head-bracket.stl"), "head-bracket"), "Wrist fixed", "fixed", to_world @ unprint(W.AX5_REAR_Y + 6.0))
    place(stl(os.path.join(wrist, "ax5-motor-plate.stl"), "ax5-motor-plate"), "Wrist fixed", "fixed",
          ax5_frame() @ Matrix.Translation((0, 0, W.MP_LOCAL_Z["plate"][0])))
    place(ring("6705, outer tube to the head bracket", W.BRG5_R_OUT, W.BRG5_R_IN, *W.BRG5_X), "Wrist fixed", "cycloid",
          frame((AX4_REAR_X, 0, ROLL_Z), (1, 0, 0), (0, 0, 1)))
    place(stl(os.path.join(wrist, "ax6-l-bracket.stl"), "ax6-l-bracket"), "Wrist pitch body", "moving", to_world @ unprint(W.LB_Y[0]))
    place(stl(os.path.join(MODEL, "forearm-tube", "ax4-output-plate.stl"), "ax5 output plate"), "Wrist pitch body", "moving",
          ax5_frame() @ Matrix.Translation((0, 0, F.PLATE_X[0])))


def structure():
    roll = frame((0, 0, ROLL_Z), (1, 0, 0), (0, 0, 1))
    if OFFSET_WRIST:
        wrist_parts(); return
    if TUBE_FOREARM:
        fork_and_cheeks(); return
    shell = L.cyl_z("fixed shell, holds the 6810s", 0, 0, SHELL_R, TUBE_X0, TUBE_X1 - 3, n=128)
    L.cut(shell, L.cyl_z("bore", 0, 0, SHELL_R - 3, TUBE_X0 - 1, TUBE_X1, n=128))
    place(shell, "Structure placeholders", "fixed", roll)
    tube = L.cyl_z("roll tube on 2 x 6810", 0, 0, TUBE_R, TUBE_X0, TUBE_X1, n=128)
    L.cut(tube, L.cyl_z("bore", 0, 0, TUBE_R - 3, TUBE_X0 - 1, TUBE_X1 + 1, n=128))
    to_world(tube, roll)
    to_world(L.cyl_z("coupling, cycloid output to tube", 0, 0, TUBE_R, 76.0, TUBE_X0, n=96), roll)
    fork_and_cheeks()


def fork_and_cheeks():
    root = L.box("fork root", FORK_ROOT_X, FORK_ROOT_X + FORK_ROOT_T, -FORK_OUT, FORK_OUT, ROLL_Z - HOUSING_R, ROLL_Z + HOUSING_R)
    place(root, "Structure placeholders", "moving")
    for sy in (-1, 1):
        y0, y1 = sorted((sy * FORK_IN, sy * FORK_OUT))
        arm = L.box("fork arm", FORK_ROOT_X, PITCH_X, y0, y1, ROLL_Z - HOUSING_R, ROLL_Z + HOUSING_R)
        L.union(arm, L.cyl_between("arm end", (PITCH_X, y0, ROLL_Z), (PITCH_X, y1, ROLL_Z), HOUSING_R, n=96))
        place(arm, "Structure placeholders", "moving")
    y0, y1 = FORK_IN, FORK_OUT
    place(L.cyl_between("6705 plain bearing, fork arm", (PITCH_X, y0, ROLL_Z), (PITCH_X, y1, ROLL_Z), 16.0, n=48), "Structure placeholders", "steel")
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 34.2, sy * 35.6))
        cheek = L.box("pitch body cheek", PITCH_X, AX6_REAR_X, y0, y1, ROLL_Z - 20, ROLL_Z + 20)
        L.union(cheek, L.cyl_between("pivot", (PITCH_X, y0, ROLL_Z), (PITCH_X, y1, ROLL_Z), 20.0, n=48))
        place(cheek, "Structure placeholders", "moving")


def v1_parts():
    for name, e in PLACE.items():
        g = name.split("/")[0]
        path = os.path.join(ROOT, e["file"])
        if g in (("mainbody", "axis1") if ELBOW else ("mainbody", "axis1", "axis2", "axis3")) or (name == "axis4/axis4_axis5_holder" and not TUBE_FOREARM):
            if "alternates" in e["collection"]:
                continue
            place(stl(path, name), "V1 arm kept", "v1", Matrix(e["matrix_world"]))
        elif g in ("axis4", "axis56") and e["collection"] != "alternates":
            place(stl(path, name), "V1 head (for comparison)", "ghost", Matrix(e["matrix_world"]))
        elif g == "gripper":
            place(stl(path, "v1 " + name), "V1 head (for comparison)", "ghost", Matrix(e["matrix_world"]))


def world_verts(names=None, col=None):
    pts = []
    for o in (COLS[col].objects if col else [bpy.data.objects[n] for n in names]):
        pts += [v.co.copy() for v in o.data.vertices]
    return pts


def clashes(a, names):
    def tree(o):
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
        t = mathutils.bvhtree.BVHTree.FromBMesh(bm); bm.free(); return t
    ta = tree(a)
    return {n: len(ta.overlap(tree(bpy.data.objects[n]))) for n in names}


def pitch_limit(pts):
    root_face = FORK_ROOT_X + FORK_ROOT_T
    for deg in range(1, 181):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        for p in pts:
            dx, dz = p.x - PITCH_X, p.z - ROLL_Z
            if PITCH_X + dx * c - dz * s <= root_face and abs(dx * s + dz * c) <= HOUSING_R:
                return deg
    return None


def inline_axis4_report():
    holder = bpy.data.objects["axis4/axis4_axis5_holder"]
    bm = bmesh.new(); bm.from_mesh(holder.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    fixed = [o for o in COLS[AX4_COL].objects if "disk" not in o.name]
    worst = 0.0
    for o in fixed:
        for v in o.data.vertices:
            loc, n, _, d = tree.find_nearest(v.co)
            if (v.co - loc).dot(n) < 0:
                worst = max(worst, d)
    bm.free()
    m4 = world_verts(col=AX4_COL)
    motor_pts = world_verts(names=["ax4 34 mm motor"])
    return {
        "axis4_deepest_into_holder_mm": round(worst, 2),
        "axis4_x_range": [round(min(p.x for p in m4), 1), round(max(p.x for p in m4), 1)],
        "axis4_motor_rear_x": round(min(p.x for p in motor_pts), 1),
        "axis4_motor_to_elbow_axis_mm": round(min(math.hypot(p.x, p.z - 453.0) for p in motor_pts), 1),
        "axis4_clash_tris_with_holder": clashes(holder, ["ax4 34 mm motor", "ax4 motor cup (placeholder)"]),
    }


def tube_axis4_report():
    ax4 = world_verts(col=AX4_COL)
    elbow = min(math.hypot(p.x, p.z - 453.0) for p in ax4)
    assert elbow >= 69.8 + 2.0, "axis 4 hits the elbow disk"
    v1_arm = [o.name for o in COLS["V1 arm kept"].objects]
    hits = {o.name: n for o in COLS[AX4_COL].objects for n in [sum(clashes(o, v1_arm).values())] if n}
    assert not hits, ("axis 4 hits the V1 arm", hits)
    if not OFFSET_WRIST:
        assert abs(FORK_ROOT_X - (AX4_REAR_X + F.FLANGE_FACE)) < 1e-6 and abs(PITCH_X - FORK_ROOT_X - 104.0) < 1e-6
    return {
        "axis4_x_range": [round(min(p.x for p in ax4), 1), round(max(p.x for p in ax4), 1)],
        "axis4_min_to_elbow_axis_mm": round(elbow, 1),
        "axis4_clash_tris_with_v1_arm": 0,
        "pitch_x": PITCH_X,
        "reach_vs_v1_mm": round(PITCH_X - 250.0, 1),
    }


ELBOW_AT = Vector((AX4_REAR_X + E.ELBOW_FX, 0, ROLL_Z - E.OFFSET))   # V1's roll height kept, so nothing past the elbow moves
ELBOW_COL, ELBOW_COMPACT_COL = "Elbow and upper arm", "Elbow compact"
ELBOW_MOVING_STL = ("elbow-collar-lower", "elbow-collar-upper", "elbow-hub", "elbow-stop-collar", "elbow-key-wedge")
BRACKET_G = 60                                 # collar, tubes and hub, my estimate
FOREARM_MEASURED_G = 1300                      # the user's scale, elbow forward, no hand, T8 cut to length (2026-11-17)
HOLD_17HS8401B, HOLD_PANCAKE = 0.52, 0.13      # N·m, build-plan §7: scales the measured pancake figure to the elbow motor


def elbow_frame():
    return Matrix.Translation(ELBOW_AT)


def elbow_arm():
    """The elbow and upper arm from model/elbow/, posed back from print orientation, at the head concept's elbow (forearm level)."""
    folder = os.path.join(MODEL, "elbow")
    poses = json.load(open(os.path.join(folder, "poses.json")))
    m = elbow_frame()
    for name, rows in poses.items():
        mat = "moving" if name in ELBOW_MOVING_STL else "fixed"
        place(stl(os.path.join(folder, name + ".stl"), "elbow " + name), ELBOW_COL, mat, m @ Matrix(rows))
    for name, ((ax, az), (bx, bz)) in E.TUBE_ENDS.items():
        a, b = Vector((ax, E.TUBE_PLANE_Y, az)), Vector((bx, E.TUBE_PLANE_Y, bz))
        d = (b - a).normalized()
        t = L.cyl_between("elbow tube " + name, a - d * E.SOCKET_DEPTH, b + d * E.SOCKET_DEPTH, E.TUBE_OR, n=24)
        t.data.transform(t.matrix_world); t.matrix_world = Matrix()
        place(t, ELBOW_COL, "steel", m)
    for x, z in E.CROSS_MEMBERS:
        place(L.cyl_between("elbow cross member", (x, -E.Y_REAR - E.PLATE_T, z), (x, E.Y_REAR + E.PLATE_T, z), E.TUBE_OR, n=24), ELBOW_COL, "steel")
    for o in [o for o in COLS[ELBOW_COL].objects if o.name.startswith("elbow cross member")]:
        o.data.transform(m @ o.matrix_world); o.matrix_world = Matrix()
    h = E.MOTOR_SQ / 2
    place(L.box("elbow motor 17HS8401B", -h, h, E.Y_REAR - E.MOTOR_L, E.Y_REAR, E.MOTOR_Z - h, E.MOTOR_Z + h), ELBOW_COL, "motor", m)
    up = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # a pulley's z (free flange to hub) onto -y, hub towards plate A
    top = E.PULLEY_Y0 + E.PULLEY_H
    for name, z in (("axis3-pulley-60T", 0.0), ("axis3-pulley-20T", E.MOTOR_Z)):
        place(stl(os.path.join(folder, name + ".stl"), "elbow " + name), ELBOW_COL, "pulley", m @ Matrix.Translation((0, top, z)) @ up)
    belt = basis_frame((0, 0, -1), (-1, 0, 0), (0, 1, 0))
    ring_prism("elbow belt 420-3M", ELBOW_COL, "belt", m @ belt, 20 * 3 / math.pi / 2, 60 * 3 / math.pi / 2, E.BELT_C, E.TEETH_Y[0] + 1, E.TEETH_Y[1] - 1, 1.6)
    cm = m @ basis_frame((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, E.Y_REAR, 0))
    cycloid("20-1-compact", "ax3", ELBOW_COMPACT_COL, cm)
    place(stl(os.path.join(MODEL, "forearm-tube", "ax4-output-plate.stl"), "ax3 output plate"), ELBOW_COMPACT_COL, "moving", cm @ Matrix.Translation((0, 0, F.PLATE_X[0])))


def basis_frame(u, v, w, origin=(0, 0, 0)):
    mm = Matrix.Identity(4)
    for i in range(3):
        mm[i][0], mm[i][1], mm[i][2], mm[i][3] = u[i], v[i], w[i], origin[i]
    return mm


def elbow_rot(theta):
    """Elbow angle theta (0 = forearm straight up, 90 = level, as modelled) about the elbow axis."""
    return Matrix.Translation(ELBOW_AT) @ Matrix.Rotation(math.radians(theta - 90.0), 4, 'Y') @ Matrix.Translation(-ELBOW_AT)


def past_elbow():
    """Everything the elbow carries, split into what pitches with axis 5 and what doesn't."""
    body = set(pitch_body())
    rest = [o for n in COLS if n not in (ELBOW_COL, ELBOW_COMPACT_COL, SH_COL, BASE_COL, "V1 arm kept", "V1 head (for comparison)") for o in COLS[n].objects if o not in body]
    rest += [o for o in COLS[ELBOW_COL].objects if any(o.name == "elbow " + k for k in ELBOW_MOVING_STL) or o.name.startswith("elbow tube")]
    return list(body), rest


def elbow_fixed():
    """The upper arm's own parts."""
    return [o for o in COLS[ELBOW_COL].objects if not (any(o.name == "elbow " + k for k in ELBOW_MOVING_STL) or o.name.startswith("elbow tube")
            or "60T" in o.name or "belt" in o.name)] + [o for o in COLS[ELBOW_COMPACT_COL].objects if "housing" in o.name]


def elbow_masses():
    """(centre, grams) groups past the elbow, scaled so the forearm without the hand weighs the user's measured 1300 g."""
    pitch = [(centre(mass_group(k)), g, True) for k, g in PITCH_MASSES.items()]
    fixed = [(centre(mass_group(k)), g, False) for k, g in FIXED_HEAD_MASSES.items()]
    known = sum(PITCH_MASSES.values()) + sum(FIXED_HEAD_MASSES.values()) - PITCH_MASSES["Three-finger hand"]
    rest = [(centre(list(COLS[AX4_COL].objects)), FOREARM_MEASURED_G - known, False),
            (centre([o for o in COLS[ELBOW_COL].objects if any(o.name == "elbow " + k for k in ELBOW_MOVING_STL)]), BRACKET_G, False)]
    return pitch + fixed + rest


def elbow_torque(theta, pitch_deg, groups, tip):
    em, pm = elbow_rot(theta), pitch_matrix(pitch_deg)
    s = 0.0
    for c, g, pitches in groups + [(tip, TOOL_KG * 1000, True)]:
        p = em @ (pm @ c if pitches else c)
        s += g * (p.x - ELBOW_AT.x)
    return 9.81 * abs(s) * 1e-6


def elbow_clash_pairs(pose, body, rest):
    th, pitch = pose
    out = []
    for f in elbow_fixed():
        tf = merged_tree([f])
        for o in body + rest:
            mm = elbow_rot(th) @ (pitch_matrix(pitch) if o in body else Matrix())
            if tf.overlap(merged_tree([o], mm)):
                out.append((o.name, f.name))
    return out


def elbow_report(report):
    body, rest = past_elbow()
    fixed = merged_tree(elbow_fixed())
    hits = []
    for pitch in (-90, 0, 90):
        for th in range(int(E.RANGE[0]), int(E.RANGE[1]) + 1, 2):
            em = elbow_rot(th)
            if fixed.overlap(merged_tree(rest, em)) or fixed.overlap(merged_tree(body, em @ pitch_matrix(pitch))):
                hits.append((th, pitch))
    grip = world_verts(col="Three-finger hand")
    tip = Vector((max(p.x for p in grip), AX6_Y, ROLL_Z))
    groups = elbow_masses()
    worst = max(((th, p) for p in (-90, 0, 90) for th in range(int(E.RANGE[0]), int(E.RANGE[1]) + 1, 2)), key=lambda tp: elbow_torque(*tp, groups, tip))
    t = elbow_torque(*worst, groups, tip)
    capacity = MEASURED_NM_AT_40 * (HOLD_17HS8401B / HOLD_PANCAKE) * 60 / 40
    report.update({"elbow_at": [round(c, 1) for c in ELBOW_AT], "elbow_sweep_clash": hits,
                   "elbow_torque_worst_nm": round(t, 2), "elbow_worst_pose_theta_pitch": list(worst),
                   "elbow_capacity_nm": round(capacity, 2), "elbow_margin": round(capacity / t, 2),
                   "elbow_mass_past_g": round(sum(g for _, g, _ in groups) + TOOL_KG * 1000)})
    assert not hits, ("the forearm or head hits the upper arm", hits, elbow_clash_pairs(hits[0], body, rest))
    assert t <= capacity, f"the elbow needs {t:.2f} N·m, over the {capacity:.2f} estimated: bring it to the user (spec)"


PITCH_MASSES = {"ax6 cycloid": 150, "ax6 pancake": 120, "ax7 gripper motor": 230, "Gripper drive, past axis 6": 80,
                "Three-finger hand": 400, "Wrist pitch body": 70}   # grams, estimates
FIXED_HEAD_MASSES = {"ax5 cycloid": 150, "ax5 pancake": 120, "head-bracket": 70, "ax5-motor-plate": 25}   # the bracket now includes the wrist hub
TOOL_KG = 0.2
MEASURED_NM_AT_40 = 1.17                       # red compact + pancake at 1000 mA, torque test 2026-11-15; the spec wants 1.5x over the load
CYCLOID_PARTS = ("housing", "carrier", "disk", "eccentric")
PITCH_PLACEHOLDERS = ("adapter", "screw bulkhead", "palm rear shell")


def mass_group(key):
    if key in COLS:
        objs = list(COLS[key].objects)
        if key == "Three-finger hand":
            objs += [o for o in COLS["Structure placeholders"].objects if o.name.startswith("palm rear shell")]
        return objs
    if key.endswith(" cycloid"):
        prefix = key.split(" ")[0]
        return [o for o in bpy.data.objects if o.name.startswith(prefix + " ") and any(p in o.name for p in CYCLOID_PARTS)]
    return [o for o in bpy.data.objects if o.name == key or o.name.startswith(key + " (")]


def centre(objs):
    pts = [v.co for o in objs for v in o.data.vertices]
    assert pts, "empty mass group"
    return Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])


def torque_about(point, axes, masses, tool_at):
    """Worst-case static torque (N·m) about a line through point, with the lever horizontal; axes picks the two
    coordinates square to the line. Masses in grams, distances in mm."""
    s = [0.0, 0.0]
    for key, g in masses.items():
        c = centre(mass_group(key))
        for k, i in enumerate(axes):
            s[k] += g * (c[i] - point[i])
    for k, i in enumerate(axes):
        s[k] += TOOL_KG * 1000 * (tool_at[i] - point[i])
    return 9.81 * math.hypot(*s) * 1e-6


def roll_torque_pitched(deg, tip):
    """Worst over axis 4's roll angle of the static torque on axis 4 with the wrist pitched by deg: the pitch groups'
    centres and the tool turn with the pitch, the fixed head stays put."""
    m, s = pitch_matrix(deg), [0.0, 0.0]
    groups = [(centre(mass_group(k)), g) for k, g in FIXED_HEAD_MASSES.items()]
    groups += [(m @ centre(mass_group(k)), g) for k, g in PITCH_MASSES.items()] + [(m @ tip, TOOL_KG * 1000)]
    for c, g in groups:
        s[0] += g * c.y
        s[1] += g * (c.z - ROLL_Z)
    return 9.81 * math.hypot(*s) * 1e-6


def pitch_body():
    objs = []
    for name in ("Wrist pitch body", "Axis 6 hollow, gripper motor behind", "Gripper drive, past axis 6", "Three-finger hand"):
        objs += COLS[name].objects
    return objs + [o for o in COLS["Structure placeholders"].objects if o.name.startswith(PITCH_PLACEHOLDERS)]


def wrist_fixed():
    objs = list(COLS["Wrist fixed"].objects) + list(COLS[AX4_COL].objects)
    return objs + [o for o in COLS["Axis 5 belted, 40:1"].objects if not any(p in o.name for p in ("carrier", "disk", "eccentric"))]


def merged_tree(objs, m=None, pre=None):
    """One BVH tree of objs, each moved by m; pre: {id(o): a matrix applied to that one first}."""
    verts, polys = [], []
    for o in objs:
        base = len(verts)
        mo = (m or Matrix()) @ pre[id(o)] if pre and id(o) in pre else m
        verts += [(mo @ v.co) if mo else v.co.copy() for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return mathutils.bvhtree.BVHTree.FromPolygons(verts, polys)


def pitch_matrix(deg):
    c = Vector((PITCH_X, 0, ROLL_Z))
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, 'Y') @ Matrix.Translation(-c)


def pitch_sweep(degs):
    fixed, body = merged_tree(wrist_fixed()), pitch_body()
    return [d for d in degs if fixed.overlap(merged_tree(body, pitch_matrix(d)))]


def offset_wrist_report(report):
    pan = [v.co for v in bpy.data.objects["ax5 pancake"].data.vertices]
    assert min(p.y for p in pan) >= 40.0 and all(abs(p.z - ROLL_Z) <= 25.0 for p in pan), "axis 5's pancake isn't beside the forearm, in line with it"
    assert not [o for o in bpy.data.objects if "wrist-flange-hub" in o.name], "the old wrist hub is still drawn: the head bracket replaces it"
    hits = pitch_sweep(range(-170, 171, 10))
    assert not hits, ("pitch body clashes", hits)
    grip = world_verts(col="Three-finger hand")
    tip = Vector((max(p.x for p in grip), AX6_Y, ROLL_Z))
    pitch = Vector((PITCH_X, 0, ROLL_Z))
    t5 = torque_about(pitch, (0, 2), PITCH_MASSES, tip)
    roll = torque_about(Vector((0, 0, ROLL_Z)), (1, 2), {**PITCH_MASSES, **FIXED_HEAD_MASSES}, tip)
    lever = {k: round(centre(mass_group(k)).x - PITCH_X, 1) for k in PITCH_MASSES}
    lever["tool at the fingertips"] = round(tip.x - PITCH_X, 1)
    print("AXIS5 LEVERS mm", json.dumps(lever), "torque N·m", round(t5, 2))
    ratio = 20 * W.AX5_TEETH / 20
    capacity = MEASURED_NM_AT_40 * ratio / 40
    ax5_limit = capacity / 1.5
    worst = max(range(-170, 171, 5), key=lambda d: roll_torque_pitched(d, tip))
    report.update({"axis4_roll_torque_worst_nm": round(roll_torque_pitched(worst, tip), 2), "axis4_roll_worst_at_pitch_deg": worst,
                   "axis4_ratio": 20 * F.AX4_TEETH / 20, "axis4_roll_capacity_nm": round(MEASURED_NM_AT_40 * F.AX4_TEETH / 40, 2)})
    report["axis4_roll_margin"] = round(report["axis4_roll_capacity_nm"] / report["axis4_roll_torque_worst_nm"], 2)
    report.update({"axis5_ratio": ratio, "axis5_capacity_nm": round(capacity, 2), "axis5_margin": round(capacity / t5, 2)})
    report.update({"pitch_x": PITCH_X, "ax6_offset_y": AX6_Y, "pitch_sweep_clash_deg": hits,
                   "axis5_torque_nm": round(t5, 2), "axis4_roll_torque_nm": round(roll, 2),
                   "head_mass_g": sum(PITCH_MASSES.values()) + sum(FIXED_HEAD_MASSES.values())})
    assert report["axis4_roll_torque_worst_nm"] >= report["axis4_roll_torque_nm"], "worst-case roll misses pitch 0"
    assert t5 <= ax5_limit, f"axis 5 needs {t5:.2f} N·m with a 200 g tool, over {ax5_limit:.2f}: bring it to the user (spec)"
    assert report["axis4_roll_torque_worst_nm"] <= report["axis4_roll_capacity_nm"], "axis 4 can't hold the head pitched sideways"


SH_COL, BASE_COL = "Shoulder and body", "Base and legs"
SH_MOVING_STL = ("shoulder-hub-b", "shoulder-output-plate", "shoulder-stop-collar")
SH_SKIP_STL = ("plate-drill-jig", "shoulder-motor-plate-23")      # a drilling tool, and the NEMA23's spare plate
BASE_STL = ("turntable", "base-ring-130T", "spigot-spacer", "spigot-cap", "fixed-base", "base-motor-plate", "foot", "foot-pad")
PHI_TURNING_STL = ("turntable", "base-ring-130T")   # base parts that turn with phi; the rest of the base stays with the bench
SH_AT = ELBOW_AT - Vector((0, 0, E.UPPER_L))   # the shoulder axis; the shoulder frame maps in by translation
PRINTED_G_MM3 = 1.24e-3 * 0.4                  # PLA at 40% infill
MOTOR_G, COMPACT_G, PAYLOAD_G, LEG_TUBE_G = 350, 120, 500, 17   # each; the tube is Ø9 x 1 aluminium, 250 long
USER_HEAD_G = 1346                             # the user's scale with the pancakes and T8 on, no hand (2026-11-19)
WRIST_TEST_G = 500                             # at the wrist pitch axis: lifted cleanly at 800 mA (2026-11-19)


def shoulder_frame():
    return Matrix.Translation(SH_AT)


def shoulder_rot(psi):
    """Shoulder pitch psi about the shoulder axis: +psi tips the upper arm forwards (+x)."""
    return Matrix.Translation(SH_AT) @ Matrix.Rotation(math.radians(psi), 4, 'Y') @ Matrix.Translation(-SH_AT)


def base_rot(phi):
    c = Vector((SH_AT.x, SH_AT.y, 0))
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(phi), 4, 'Z') @ Matrix.Translation(-c)


def shoulder_body():
    """model/shoulder/ posed back from print orientation, the compact, the motors and pulleys, and the legs, at phi 0."""
    folder = os.path.join(MODEL, "shoulder")
    poses = json.load(open(os.path.join(folder, "poses.json")))
    m = shoulder_frame()
    for name, rows in poses.items():
        if name in SH_SKIP_STL:
            continue
        col, mat = (BASE_COL, "fixed") if name in BASE_STL else (SH_COL, "moving" if name in SH_MOVING_STL else "fixed")
        if name in ("foot", "foot-pad"):
            for phi in S.LEG_PHI:
                place(stl(os.path.join(folder, name + ".stl"), f"{name} {phi:.0f}"), col, mat,
                      m @ Matrix.Rotation(math.radians(phi - S.LEG_PHI[0]), 4, 'Z') @ Matrix(rows))
            continue
        place(stl(os.path.join(folder, name + ".stl"), "shoulder " + name), col, mat, m @ Matrix(rows))
    cycloid("20-1-compact", "ax2", SH_COL, m @ basis_frame((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, S.COMPACT_REAR_Y, 0)))
    up = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # a pulley's z onto -y, hub towards the stub
    out = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # a pulley's z onto +y, hub towards the motor
    top = S.PULLEY80_Y + E.PULLEY_H
    mx, mz = S.motor_at()
    place(stl(os.path.join(folder, "shoulder-pulley-80T.stl"), "shoulder 80T"), SH_COL, "pulley", m @ Matrix.Translation((0, top, 0)) @ up)
    place(stl(os.path.join(MODEL, "elbow", "axis3-pulley-20T.stl"), "shoulder 20T"), SH_COL, "pulley",
          m @ Matrix.Translation((mx, S.PULLEY20_HUB_Y[1] - E.PULLEY_H, mz)) @ out)
    h = S.MOTORS["17"]["sq"] / 2
    local = basis_frame((S.BELT_U[0], 0, S.BELT_U[1]), (S.BELT_W[0], 0, S.BELT_W[1]), (0, 1, 0), (mx, 0, mz))
    place(L.box("shoulder motor 17HS19", -h, h, -h, h, S.MOTOR_FACE_Y, S.MOTOR_FACE_Y + S.MOTORS["17"]["length"]), SH_COL, "motor", m @ local)
    bx, by = S.base_motor_at()
    place(L.box("base motor 17HS19", bx - h, bx + h, by - h, by + h, S.BASE_PLATE_Z[1], S.BASE_PLATE_Z[1] + S.BASE_MOTOR_L), BASE_COL, "motor", m)
    place(stl(os.path.join(MODEL, "elbow", "axis3-pulley-20T.stl"), "base 20T"), BASE_COL, "pulley",
          m @ Matrix.Translation((bx, by, S.BASE20_HUB_Z[1] - E.PULLEY_H)))
    for phi in S.LEG_PHI:
        _, s, f = S.leg(phi)
        t = L.cyl_between(f"leg tube {phi:.0f}", s, f, S.TUBE_LEG_R, n=24)
        t.data.transform(t.matrix_world); t.matrix_world = Matrix()
        place(t, BASE_COL, "steel", m)


def shoulder_moving():
    """Everything the shoulder carries: the upper arm, everything past the elbow, and the hub's parts."""
    out = [o for n in COLS if n not in (SH_COL, BASE_COL, "V1 arm kept", "V1 head (for comparison)") for o in COLS[n].objects]
    return out + [o for o in COLS[SH_COL].objects if any(o.name == "shoulder " + k for k in SH_MOVING_STL)]


def shoulder_fixed():
    """The body, the base and the legs (both shoulder plates' motor: the 17 is drawn; the 23's box is no bigger where it matters)."""
    body = [o for o in COLS[SH_COL].objects if not any(o.name == "shoulder " + k for k in SH_MOVING_STL)]
    body = [o for o in body if not (o.name.startswith("ax2 ") and "housing" not in o.name)]   # the compact's insides turn with its output
    return body + list(COLS[BASE_COL].objects)


def printed_g(objs):
    g = 0.0
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); g += abs(bm.calc_volume()) * PRINTED_G_MM3; bm.free()
    return g


def obj(name):
    return bpy.data.objects[name]


def named_elbow_masses():
    """elbow_masses(), with each group's name."""
    names = list(PITCH_MASSES) + list(FIXED_HEAD_MASSES) + ["forearm rest", "elbow bracket"]
    return list(zip(names, elbow_masses()))


def upper_arm_masses():
    plates = [obj("elbow upper-plate-A"), obj("elbow upper-plate-B")]
    compact = [o for o in COLS[ELBOW_COMPACT_COL].objects if "housing" in o.name]
    return [(centre(plates), printed_g(plates)), (centre([obj("elbow motor 17HS8401B")]), MOTOR_G), (centre(compact), COMPACT_G)]


def arm_points(psi, theta, pitch, groups, upper, tip, payload):
    """(world point, grams) for the moving masses at the pose: the upper arm turns by psi, the rest by theta and the pitch as well."""
    sm, em, pm = shoulder_rot(psi), elbow_rot(theta), pitch_matrix(pitch)
    out = [(sm @ c, g) for c, g in upper]
    out += [(sm @ em @ (pm @ c if pitches else c), g) for c, g, pitches in groups]
    return out + [(sm @ em @ pm @ tip, payload)]


def shoulder_torque(psi, theta, pitch, groups, upper, tip):
    return 9.81 * abs(sum(g * (p.x - SH_AT.x) for p, g in arm_points(psi, theta, pitch, groups, upper, tip, PAYLOAD_G))) * 1e-6


def upper_arm_objs():
    """What turns with the shoulder but not the elbow: the upper arm, the elbow compact, the shoulder hub's parts."""
    _, rest = past_elbow()
    out = [o for n in (ELBOW_COL, ELBOW_COMPACT_COL) for o in COLS[n].objects if o not in rest]
    return out + [o for o in COLS[SH_COL].objects if any(o.name == "shoulder " + k for k in SH_MOVING_STL)]


def np_verts(objs, m=None):
    import numpy as np
    parts = []
    for o in objs:
        a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", a); parts.append(a.reshape(-1, 3))
    pts = np.vstack(parts)
    if m is not None:
        r = np.array([[m[i][j] for j in range(3)] for i in range(3)]); t = np.array([m[i][3] for i in range(3)])
        pts = pts @ r.T + t
    return pts


def phi_split():
    """shoulder_fixed() split into what turns with the base (the body on the turntable) and what stays with the bench."""
    base = {o.name for o in COLS[BASE_COL].objects}
    turning = [o for o in shoulder_fixed() if o.name in ["shoulder " + k for k in PHI_TURNING_STL] or o.name not in base]
    return turning, [o for o in shoulder_fixed() if o not in turning]


def soft_limits(turning, still, bench_z, phi):
    """(psi, theta) pairs, 5 degree steps, where the arm meets the body, the base, the legs or the bench; pitch 0. The
    base stands at phi: what stays with the bench is turned by -phi about the base axis, into the turntable's frame."""
    import numpy as np
    upper = upper_arm_objs()
    body, rest = past_elbow()
    fixed_trees = {psi: merged_tree(turning + still, shoulder_rot(-psi), {id(o): base_rot(-phi) for o in still})
                   for psi in range(int(S.PSI_RANGE[0]), int(S.PSI_RANGE[1]) + 1, 5)}
    hits = []
    up_tree = merged_tree(upper)
    up_v = np_verts(upper)
    for th in range(int(E.RANGE[0]), int(E.RANGE[1]) + 1, 5):
        em = elbow_rot(th)
        tree = merged_tree(body + rest, em)
        pts = np.vstack([np_verts(body + rest, em), up_v]) - np.array(tuple(SH_AT))
        for psi, ft in fixed_trees.items():
            a = math.radians(psi)
            z = -pts[:, 0] * math.sin(a) + pts[:, 2] * math.cos(a) + SH_AT.z
            if z.min() < bench_z or ft.overlap(tree) or ft.overlap(up_tree):
                hits.append([psi, th])
    return hits


def bench_reach(fixed, bench_z, tip):
    """Poses (psi, theta, wrist pitch) that bring the tool's point to the bench (within 2) with nothing of the arm under
    it or in the body, the base or the legs, at phi 0: the one nearest the base axis."""
    import numpy as np
    body, rest = past_elbow()
    upper = upper_arm_objs()
    ft = merged_tree(fixed)
    cands = []
    for psi in range(int(S.PSI_RANGE[0]), int(S.PSI_RANGE[1]) + 1):
        for th in range(int(E.RANGE[0]), int(E.RANGE[1]) + 1, 2):
            for pitch in range(-90, 91, 10):
                p = shoulder_rot(psi) @ elbow_rot(th) @ pitch_matrix(pitch) @ tip
                if p.z <= bench_z + 2.0:
                    cands.append((math.hypot(p.x - SH_AT.x, p.y - SH_AT.y), psi, th, pitch, p.z))
    for r, psi, th, pitch, z in sorted(cands):
        sm, em, pm = shoulder_rot(psi), elbow_rot(th), pitch_matrix(pitch)
        arm = np.vstack([np_verts(body, sm @ em @ pm), np_verts(rest, sm @ em), np_verts(upper, sm)])
        if arm[:, 2].min() < bench_z - 1.0:
            continue
        if ft.overlap(merged_tree(body, sm @ em @ pm)) or ft.overlap(merged_tree(rest, sm @ em)) or ft.overlap(merged_tree(upper, sm)):
            continue
        return {"reaches": True, "closest_r_mm": round(r, 1), "pose": [psi, th, pitch], "tip_above_bench_mm": round(z - bench_z, 2), "candidates": len(cands)}
    return {"reaches": False, "closest_r_mm": None, "pose": None, "candidates": len(cands)}


def tip_margin(groups, upper, tip, sweep):
    """Least distance from the whole arm's centre of mass, projected, to the pad square's edges, at the longest reaches."""
    turning, still = phi_split()
    turn_g = [(centre([o]), printed_g([o])) for o in turning if o.name.startswith("shoulder ") and "motor 17HS19" not in o.name and "80T" not in o.name]
    turn_g += [(centre([obj("shoulder motor 17HS19")]), MOTOR_G), (centre([o for o in COLS[SH_COL].objects if o.name.startswith("ax2 housing")]), COMPACT_G)]
    turn_g += [(centre([obj("shoulder 80T")]), printed_g([obj("shoulder 80T")]))]
    still_g = [(centre([o]), printed_g([o])) for o in still if not o.name.startswith(("base motor", "leg tube"))]
    still_g += [(centre([obj("base motor 17HS19")]), MOTOR_G)] + [(centre([o]), LEG_TUBE_G) for o in still if o.name.startswith("leg tube")]
    pads = [Vector((p[0], p[1], 0)) + Vector((SH_AT.x, SH_AT.y, 0)) for p in S.FOOT_PADS]
    worst, at = math.inf, None
    for psi in (S.PSI_RANGE[0], S.PSI_RANGE[1]):
        th, pitch = max(sweep, key=lambda tp: abs((shoulder_rot(psi) @ elbow_rot(tp[0]) @ pitch_matrix(tp[1]) @ tip).x - SH_AT.x))
        arm = arm_points(psi, th, pitch, groups, upper, tip, PAYLOAD_G)
        arm += [(shoulder_rot(psi) @ centre([o]), printed_g([o])) for o in COLS[SH_COL].objects if any(o.name == "shoulder " + k for k in SH_MOVING_STL)]
        for phi in range(0, 360, 45):
            bm = base_rot(phi)
            pts = [(bm @ p, g) for p, g in arm + turn_g] + still_g
            total = sum(g for _, g in pts)
            com = sum((p * g for p, g in pts), Vector()) / total
            d = min(((b - a).cross(Vector((com.x, com.y, 0)) - a)).z / (b - a).length for a, b in zip(pads, pads[1:] + pads[:1]))
            if d < worst:
                worst, at = d, {"psi": psi, "theta": th, "pitch": pitch, "phi": phi, "com": [round(c, 1) for c in com], "mass_g": round(total)}
    return worst, at


def shoulder_report(report):
    fixed = shoulder_fixed()
    turning, still = phi_split()
    body, rest = past_elbow()
    ft = merged_tree(fixed)
    home = []
    for th in range(int(E.RANGE[0]), int(E.RANGE[1]) + 1, 2):
        em = elbow_rot(th)
        rest_hit = bool(ft.overlap(merged_tree(rest, em)))
        for pitch in (-90, 0, 90):
            if rest_hit or ft.overlap(merged_tree(body, em @ pitch_matrix(pitch))):
                home.append((th, pitch))
    upper_hit = ft.overlap(merged_tree(upper_arm_objs()))
    grip = world_verts(col="Three-finger hand")
    tip = Vector((max(p.x for p in grip), AX6_Y, ROLL_Z))
    named = named_elbow_masses()
    groups = [grp for _, grp in named]
    upper = upper_arm_masses()
    sweep = [(th, p) for p in (-90, 0, 90) for th in range(int(E.RANGE[0]), int(E.RANGE[1]) + 1, 5)]
    poses = [(psi, th, p) for psi in range(int(S.PSI_RANGE[0]), int(S.PSI_RANGE[1]) + 1, 5) for th, p in sweep]
    worst = max(poses, key=lambda q: shoulder_torque(*q, groups, upper, tip))
    t = shoulder_torque(*worst, groups, upper, tip)
    head = [(c, g, pitches) for n, (c, g, pitches) in named if n != "Three-finger hand"]
    scale = USER_HEAD_G / sum(g for _, g, _ in head)
    demo = 9.81 * (sum(g * scale * (c.x - ELBOW_AT.x) for c, g, _ in head) + WRIST_TEST_G * (PITCH_X - ELBOW_AT.x)) * 1e-6
    capacity = min(demo * S.SHOULDER_RATIO / 60, S.SHOULDER_DESIGN_NMM / 1000)   # the driver's current cap holds it to 13.5
    margin = capacity / t
    over = [q for q in poses if shoulder_torque(*q, groups, upper, tip) > capacity]
    over_worst = max(over, key=lambda q: shoulder_torque(*q, groups, upper, tip)) if over else None
    bench = SH_AT.z + S.FOOT_PAD_Z
    phis = sorted(set(list(range(0, 360, 45)) + [int(S.BASE_MOTOR_DEG) % 360]))
    per_phi = {phi: soft_limits(turning, still, bench, phi) for phi in phis}
    union = sorted({tuple(h) for hs in per_phi.values() for h in hs})
    limits0 = per_phi[0]
    assert {tuple(h) for h in limits0} <= set(union), "the soft limits over phi miss phi 0's"
    reach = bench_reach(fixed, bench, tip)
    assert reach["reaches"], ("the tool can't reach the bench", reach)
    tip_mm, tip_at = tip_margin(groups, upper, tip, sweep)
    report.update({"shoulder_at": [round(c, 1) for c in SH_AT], "shoulder_home_clashes": home, "upper_arm_hits_body": bool(upper_hit),
                   "plate_mass_g": round(upper[0][1]), "shoulder_torque_worst_nm": round(t, 2), "shoulder_worst_pose_psi_theta_pitch": list(worst),
                   "elbow_demo_nm": round(demo, 2), "shoulder_capacity_nm": round(capacity, 2), "shoulder_margin": round(margin, 2),
                   "shoulder_over_capacity": {"count": len(over), "of": len(poses), "worst": list(over_worst) if over_worst else None},
                   "shoulder_current_cap_a": round(S.SHOULDER_CURRENT_CAP_A, 3), "psi_range": list(S.PSI_RANGE),
                   "shoulder_soft_limits": [list(h) for h in union], "shoulder_soft_limits_phi0": limits0,
                   "shoulder_soft_limits_by_phi": {str(k): len(v) for k, v in per_phi.items()}, "bench_reach": reach,
                   "bench_z": round(bench, 1), "tip_margin_mm": round(tip_mm, 1), "tip_worst": tip_at})
    assert report["shoulder_current_cap_a"] == round(S.SHOULDER_CURRENT_CAP_A, 3)
    if margin < 1.2:
        report["shoulder_note"] = "shoulder: bench test at higher current, NEMA23 plate ready"
    if tip_mm < 15:
        # The user accepted clamped feet as the stability answer (2026-11-20), so tipping unclamped is reported, not asserted.
        report["tip_note"] = "clamp the feet"
    if upper_hit:
        pairs = [(o.name, f.name) for o in upper_arm_objs() for f in fixed if merged_tree([o]).overlap(merged_tree([f]))]
        assert False, ("the upper arm hits the body at home", pairs[:12])


def shoulder_renders():
    shown = set(COLS) - {"V1 arm kept", "V1 head (for comparison)"}
    movers, at = shoulder_moving(), 0.0
    target = tuple(SH_AT + Vector((80, 0, -40)))
    for psi, name in ((0, "shoulder-side"), (90, "shoulder-forward"), (-90, "shoulder-back")):
        for o in movers:
            o.data.transform(shoulder_rot(psi) @ shoulder_rot(at).inverted())
        at = psi
        render(name, (0, -1, 0), shown, target=target, scale=1300)
    for o in movers:
        o.data.transform(shoulder_rot(at).inverted())
    render("shoulder-iso", (1, -1.1, 0.6), shown, target=target, scale=1300)
    render("shoulder-top", (0, 0, 1), shown, target=target, scale=1300)


def check(z_motor):
    pitch_pts = world_verts(col="Axis 6 hollow, gripper motor behind")
    swing = max(math.hypot(p.x - PITCH_X, p.z - ROLL_Z) for p in pitch_pts)
    half_y = max(abs(p.y) for p in pitch_pts)
    ax5 = world_verts(col="Axis 5 belted, 40:1")
    report = {"belt_188_centre_mm": BELT_C, **(tube_axis4_report() if TUBE_FOREARM else inline_axis4_report())}
    report.update({
        "elbow_disk_radius_mm": 69.8,
        "pitch_body_swing_radius_mm": round(swing, 1),
        "swing_clear_of_fork_root_mm": round(PITCH_X - swing - FORK_ROOT_X - FORK_ROOT_T, 1),
        "pitch_body_half_width_y_mm": round(half_y, 1),
        "fork_inner_half_width_mm": FORK_IN,
        "axis5_y_range": [round(min(p.y for p in ax5), 1), round(max(p.y for p in ax5), 1)],
        "axis5_x_range": [round(min(p.x for p in ax5), 1), round(max(p.x for p in ax5), 1)],
    })
    ax7 = world_verts(col="Gripper drive, past axis 6")
    grip = world_verts(col="Three-finger hand")
    report.update({
        "gripper_motor_rear_x": round(min(p.x for p in pitch_pts), 1),
        "drive_x_range": [round(min(p.x for p in ax7), 1), round(max(p.x for p in ax7), 1)],
        "drive_half_width_y_mm": round(max(abs(p.y) for p in ax7), 1),
        "drive_max_z_from_axis_mm": round(max(abs(p.z - ROLL_Z) for p in ax7), 1),
        "rod_length_mm": AX7_REAR_Z + ROD_TIP_IN_COMPACT - ROD_START_Z if COMPACT_DRIVE else ROD_L,
        "plate_clear_of_ax6_bolt_heads_mm": round(AX7_REAR_Z - ADAPTER_PLATE_T - (AX6_HOUSING_L + 3.0), 1),
        "hand_half_width_y_mm": round(max(abs(p.y) for p in grip), 1),
        "fingertip_x": round(max(p.x for p in grip), 1),
        "pitch_deg_before_front_meets_fork_root": pitch_limit(ax7 + grip),
    })
    new_head =[p for n in (AX4_COL, "Axis 5 belted, 40:1", "Axis 6 hollow, gripper motor behind", "Structure placeholders") for p in world_verts(col=n) if p.x > 90]
    old_head = [p for o in COLS["V1 head (for comparison)"].objects if not o.name.startswith("v1 gripper") for p in (v.co for v in o.data.vertices) if p.x > 90]
    for label, pts in (("new_head", new_head), ("v1_head", old_head)):
        report[label + "_past_holder_y_mm"] = round(max(p.y for p in pts) - min(p.y for p in pts), 1)
        report[label + "_past_holder_z_mm"] = round(max(p.z for p in pts) - min(p.z for p in pts), 1)
        report[label + "_x_max"] = round(max(p.x for p in pts), 1)
    if OFFSET_WRIST:
        for k in ("pitch_deg_before_front_meets_fork_root", "swing_clear_of_fork_root_mm", "fork_inner_half_width_mm"):
            report.pop(k)
        offset_wrist_report(report)
    if ELBOW:
        elbow_report(report)
    if SHOULDER:
        shoulder_report(report)
    print("HEAD", json.dumps(report))


def show(names):
    for name, c in COLS.items():
        c.hide_render = name not in names


def render(name, view, shown, target=(150, 0, 520), scale=620):
    show(shown)
    cam = bpy.data.objects["Concept camera"]; cam.data.ortho_scale = scale
    d = Vector(view).normalized()
    cam.location = Vector(target) + d * 1500
    cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


def main():
    global scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 0.001; scene.unit_settings.length_unit = 'MILLIMETERS'
    v1_parts()
    z_motor = axis4_tube() if TUBE_FOREARM else axis4()
    axis5()
    axis6()
    adapter(ax6_frame())
    hand(*(compact_drive() if COMPACT_DRIVE else screw_drive()))
    structure()
    if ELBOW:
        elbow_arm()
    if SHOULDER:
        shoulder_body()
    check(z_motor)
    COLS["V1 head (for comparison)"].hide_viewport = True
    cam = bpy.data.cameras.new("Concept camera"); cam.type = 'ORTHO'; cam.clip_end = 5000
    co = bpy.data.objects.new("Concept camera", cam); scene.collection.objects.link(co); scene.camera = co
    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = False
    scene.render.resolution_x, scene.render.resolution_y = 1400, 1100
    scene.world = bpy.data.worlds.new("w"); scene.world.color = (0.93, 0.93, 0.95)
    os.makedirs(OUT, exist_ok=True)
    kept = {"V1 arm kept"}
    new = kept | {AX4_COL, "Axis 5 belted, 40:1", "Axis 6 hollow, gripper motor behind", "Gripper drive, past axis 6", "Three-finger hand",
                  "Structure placeholders", "Wrist fixed", "Wrist pitch body"}
    inner = new - {"Structure placeholders"}
    head = (max(PITCH_X, 250.0), 0, 555)
    if SHOULDER:
        shoulder_renders()
    else:
        render("concept-iso", (1, -1.1, 0.7), new, target=(120, 0, 450), scale=900)
        render("head-side", (0, -1, 0), new, target=head, scale=560)
        render("head-top", (0, 0, 1), new, target=head, scale=560)
        render("head-iso", (1, -1.1, 0.7), new, target=head, scale=560)
        render("head-parts-only-side", (0, -1, 0), inner, target=head, scale=560)
        render("head-parts-only-iso", (1, -1.1, 0.7), inner, target=head, scale=560)
        render("compare-v1-side", (0, -1, 0), {"V1 arm kept", "V1 head (for comparison)"}, target=head, scale=560)
        render("compare-v1-top", (0, 0, 1), {"V1 arm kept", "V1 head (for comparison)"}, target=head, scale=560)
        if not TUBE_FOREARM:
            holder = bpy.data.objects["axis4/axis4_axis5_holder"]
            holder.hide_render = True
            render("axis4-without-holder", (0, -1, 0.35), new - {"Structure placeholders"}, target=(40, 0, 530), scale=320)
            holder.hide_render = False
        if OFFSET_WRIST:
            body = pitch_body()
            for deg, name in ((90, "head-side-pitch-down"), (-180, "head-side-pitch-up")):   # +90 about +y turns +x to -z
                for o in body:
                    o.data.transform(pitch_matrix(deg))
                render(name, (0, -1, 0), new, target=head, scale=560)
            for o in body:
                o.data.transform(pitch_matrix(90))
        if ELBOW:
            arm = new - {"V1 arm kept"} | {ELBOW_COL, ELBOW_COMPACT_COL}
            body, rest = past_elbow()
            movers = body + rest
            at = 90.0
            for theta, name in ((90, "elbow-side"), (0, "elbow-side-up"), (-20, "elbow-side-back"), (150, "elbow-side-down")):
                for o in movers:
                    o.data.transform(elbow_rot(theta) @ elbow_rot(at).inverted())
                at = theta
                render(name, (0, -1, 0), arm, target=tuple(ELBOW_AT + Vector((80, 0, 0))), scale=820)
            for o in movers:
                o.data.transform(elbow_rot(90) @ elbow_rot(at).inverted())
            render("elbow-iso", (1, -1.1, 0.6), arm, target=tuple(ELBOW_AT + Vector((80, 0, -40))), scale=820)
    show(new)
    frame_viewports()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if ELBOW:
        save_v2_only()
    print("HEAD DONE")


def save_v2_only():
    """The V2 arm alone, elbow to hand: V1 stays in the head-concept file only, for the clash checks and comparisons."""
    for name in ("V1 arm kept", "V1 head (for comparison)"):
        for o in list(COLS[name].objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(COLS.pop(name))
    bpy.data.orphans_purge(do_recursive=True)
    show(set(COLS))
    frame_viewports()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MODEL, "cybot-v2.blend"))


def frame_viewports():
    """The parts are in mm, hundreds of units from the origin: Blender's default views (15 units out, clipped at 1000) open on nothing."""
    pts = [o.matrix_world @ v.co for o in scene.objects if o.type == 'MESH' for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.clip_start, space.clip_end = 1.0, 20000.0
                r = space.region_3d
                r.view_location = (lo + hi) / 2
                r.view_distance = (hi - lo).length * 1.2
                r.view_rotation = Vector((1, -1.1, 0.7)).normalized().to_track_quat('Z', 'Y')
                r.view_perspective = 'PERSP'


main()
