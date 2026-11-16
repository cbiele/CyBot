"""Offset wrist parts: the head bracket (wrist flange, 6705 skirt, axis 5 mount) and the axis 6 L-bracket.
Built and checked in the wrist frame (wrist_dims.py), exported in print orientation to model/wrist/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/wrist.py"""
import bpy, bmesh, math, os, sys, json, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
import forearm_dims as F
from wrist_dims import *
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT = os.path.join(ROOT, "model", "wrist")
T8 = os.path.join(ROOT, "model", "cycloid-poc", "20-1-hollow-t8")
COMPACT = os.path.join(ROOT, "model", "cycloid-poc", "20-1-compact")
FOREARM = os.path.join(ROOT, "model", "forearm-tube")
PARTS, CHECKS, PRINT_POSE = {}, [], {}
BELT_C = round(C.belt_centre_distance(20, 40, 188), 2)
MOTOR5_X = round(C.belt_centre_distance(20, AX5_TEETH, AX5_BELT), 2)
SLOT, NEMA_HOLE_OFF, NEMA_HOLE_R, NEMA_PILOT_R = C.MOTOR_SLOT, 15.5, 1.7, 11.75   # cycloid_poc's motor mount
RAIL_GAP, RAIL_W, RAIL_H, RAIL_X0, MOUNT_T = 42.7, 3.0, 5.0, 36.0, 6.0
MOUNT_HALF_W = RAIL_GAP / 2 + RAIL_W
ARM_CUT_X = 40.0                                 # the 188 arm is cut off here, past the disc's bolts and nut pockets
BOLT_HEAD_R, BOLT_HEAD_H = 2.75, 3.0
MOTOR7_DISC_Z, MOTOR7_DISC_R = (-56.0, -51.0), 30.5   # cycloid_poc's motor7-bracket disc, in axis 6's frame
FAR_POST_HALF_X, FAR_POST_Y = 4.5, (22.0, 30.0)   # axis 6 frame: the far side's tie between the mount and the gripper motor's disc; flat underside bridges in print
DRIVER_R, DRIVER_MAX_TILT = 1.3, 10.0          # 2.5 hex key shaft; a ball-end works to about 25 deg
RIB_Z0, RIB_Z1 = 10.0, 17.0                    # outside the driver path to the base disc's screws (|z| 9.5), inside axis 6's nut pockets (from z 17.85)
NUT_AF, NUT_T = 5.8, 2.6                         # cycloid_poc's nut pockets in the T8 mount
LB_SCREW_CB = 2.8                                # M3 x 12 then reaches 3.3 into the carrier's inserts
BELT_PLANE = -11.75                              # axis 5's frame, as head_concept's
MOTOR_PLATE_U = (MOTOR5_X - SLOT - 23.15, MOTOR5_X + SLOT + 23.15)
INSERT_DEPTH, MP_CB_DEPTH, MP_SCREW_L = 5.0, 2.0, 20.0
SHIM_X, SHIM_HALF_W = F.WRIST_X[0] - F.LAND_T - 0.15, 8.0   # the 0.3 shim's mid-plane, against the 6701's inner ring   # M3 heat-set inserts in the arm's belt face; M3 x 20 from the plate

def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

def basis(u, v, w, origin):
    """Exact matrix taking a part's x, y, z to u, v, w: built from 0/±1 and cos/sin, not rotations, so flat faces stay flat."""
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2], m[i][3] = u[i], v[i], w[i], origin[i]
    return m

def ax5_matrix():
    """Axis 5's assembly frame (cycloid_poc z) into the wrist frame: z to -y from the rear face, x towards the pancake."""
    dx, dz = round(math.cos(math.radians(AX5_MOTOR_ANGLE)), 12), round(math.sin(math.radians(AX5_MOTOR_ANGLE)), 12)
    return basis((dx, 0, dz), (-dz, 0, dx), (0, -1, 0), (PITCH_X, AX5_REAR_Y, 0))

def forearm_matrix():
    """A forearm part's frame (x on z) into the wrist frame, as head_concept.axis4_tube() poses it."""
    return basis((0, 0, 1), (0, -1, 0), (1, 0, 0), (0, 0, 0))

def x_axis():
    return basis((0, 0, -1), (0, 1, 0), (1, 0, 0), (0, 0, 0))

def cyl_x(name, y, z, r, x0, x1, n=96):
    c = L.cyl_z(name, 0, 0, r, x0, x1, n=n)
    c.data.transform(x_axis()); c.data.transform(Matrix.Translation((0, y, z)))
    return c

def copy(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c); return c

def overlap(a, b):
    """Volume (mm³) a and b share, worked out on copies."""
    ca, cb = copy(a, "ov_a"), copy(b, "ov_b")
    L.boolean(ca, cb, 'INTERSECT')
    bm = bmesh.new(); bm.from_mesh(ca.data); bm.transform(ca.matrix_world); v = abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(ca); return v

def tree(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    t = mathutils.bvhtree.BVHTree.FromBMesh(bm); bm.free(); return t

def min_gap(a, b):
    """Smallest distance from a's vertices to b's surface."""
    t = tree(b)
    return min(t.find_nearest(v.co)[3] for v in a.data.vertices)

def touching(a, b):
    return min_gap(a, b) <= 0.05

def radial_bore(o, x):
    """Diameter of a bore about the roll axis at x, from rays cast outwards in the y-z plane."""
    t = tree(o); ds = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        hit = t.ray_cast(Vector((x, 0, 0)), Vector((0, math.cos(a), math.sin(a))))
        if hit[0] is not None:
            ds.append((hit[0] - Vector((x, 0, 0))).length)
    return round(2 * sum(ds) / len(ds), 3) if ds else None

def x_floor(o, y, z, x_start):
    h = tree(o).ray_cast(Vector((x_start, y, z)), Vector((-1, 0, 0)))[0]
    return round(h.x, 3) if h is not None else None

def posed_stl(path, name, matrix, z_range):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name
    zs = [v.co.z for v in o.data.vertices]
    assert abs(min(zs) - z_range[0]) < 0.01 and abs(max(zs) - z_range[1]) < 0.01, (name, min(zs), max(zs))
    o.data.transform(matrix)
    return o

def ax5_housing():
    """The 20-1-compact housings in the wrist frame, with the axis 5 bolt heads on the hand-side face."""
    h = posed_stl(os.path.join(COMPACT, "housing-rear.stl"), "ax5 housing", Matrix(), (0.0, 19.3))
    front = posed_stl(os.path.join(COMPACT, "housing-front.stl"), "ax5 housing-front", Matrix.Diagonal((1, -1, -1, 1)), (-38.6, -19.3))
    L.union(h, front)
    for a in BOLT_ANGLES:
        L.union(h, L.cyl_z("bolt head", *polar(BOLT_R, a), BOLT_HEAD_R, 38.6 - 0.01, 38.6 + BOLT_HEAD_H, n=32))
    h.data.transform(ax5_matrix())
    return h

def ax5_pancake(x=MOTOR5_X):
    """The pancake on the motor plate: face on the plate's outer face, body outboard, away from the housing."""
    s, z_face = 42.3 / 2, MP_LOCAL_Z["plate"][0]
    m = L.box("ax5 pancake", x - s, x + s, -s, s, z_face - 23.0, z_face)
    m.data.transform(ax5_matrix())
    return m

def through_mount(b, u, v):
    """First hit of a ray from the housing side straight through axis 5's mount at its local (u, v), or None."""
    return tree(b).ray_cast(ax5_matrix() @ Vector((u, v, 1.0)), Vector((0, 1, 0)))[0]

def forearm_parts():
    m = forearm_matrix()
    tube = posed_stl(os.path.join(FOREARM, "forearm-outer-tube.stl"), "outer tube",
                     m @ Matrix.Translation((0, 0, F.OUTER_X[0])), (0.0, F.OUTER_X[1] - F.OUTER_X[0]))
    brg = cyl_x("6705", 0, 0, BRG5_R_OUT, *BRG5_X)
    L.cut(brg, cyl_x("bore", 0, 0, BRG5_R_IN, BRG5_X[0] - 1, BRG5_X[1] + 1))
    return tube, brg

def slot(name, x, y, r, half, z0, z1):
    s = L.cyl_z(name, x - half, y, r, z0, z1, n=32)
    L.union(s, L.cyl_z(name + "_b", x + half, y, r, z0, z1, n=32))
    L.union(s, L.box(name + "_m", x - half, x + half, y - r, y + r, z0, z1))
    return s

def insert_points():
    return [(u, sv * MP_SCREW_V) for u in (MOTOR_PLATE_U[0] + 5.0, MOTOR_PLATE_U[1] - 5.0) for sv in (-1, 1)]

def lengthen_arm(b):
    """The T8 mount's arm is set for the 188 and a pancake on it; rebuild it wider and longer for the motor plate.
    Done in the mount's own frame, before it is posed: faces on the posed STL's are only nearly coplanar and leave slivers."""
    x1 = MOTOR_PLATE_U[1]
    L.cut(b, L.box("old arm", ARM_CUT_X, 120.0, -MOUNT_HALF_W - 5, MOUNT_HALF_W + 5, -MOUNT_T - 5, RAIL_H + 5))
    L.union(b, L.box("arm", ARM_CUT_X - 1, x1, -ARM_HALF_W, ARM_HALF_W, -MOUNT_T, 0))
    for sv in (-1, 1):
        v0, v1 = sorted((sv * RAIL_GAP / 2, sv * MOUNT_HALF_W))
        L.union(b, L.box("rail", ARM_CUT_X - 1, x1, v0, v1, -0.01, RAIL_H))
    tool = slot("pilot", MOTOR5_X, 0, NEMA_PILOT_R, SLOT, -MOUNT_T - 1, 1)   # the shaft's tip reaches into the arm
    for u, v in insert_points():
        L.union(tool, L.cyl_z("insert", u, v, 2.0, -MOUNT_T - 1, -MOUNT_T + INSERT_DEPTH, n=32))
    L.finish(b)
    L.cut(b, tool)   # one cut: cut one by one, the second screw slot left non-manifold edges

def head_bracket():
    """Glued on the drive tube in the old wrist hub's place, rides the 6705 on the outer tube, and is axis 5's mount."""
    y1 = AX5_REAR_Y + MOUNT_T
    b = posed_stl(os.path.join(T8, "motor-mount.stl"), "head-bracket", Matrix(), (-6.0, 5.0))
    lengthen_arm(b)
    b.data.transform(ax5_matrix())
    boss = cyl_x("boss", 0, 0, SKIRT_R, *BOSS_X)
    L.union(boss, L.box("fill", BOSS_X[0], BOSS_X[1],
                        0.0, AX5_REAR_Y + 3.0, -FILL_HALF_Z, FILL_HALF_Z))
    L.union(b, boss)
    L.cut(b, cyl_x("6705 seat", 0, 0, BRG5_R_OUT, BRG5_X[0] - 1, BRG5_X[1]))
    L.cut(b, cyl_x("shoulder", 0, 0, SHOULDER_R, BRG5_X[1] - 0.01, F.WRIST_X[0]))
    land = cyl_x("land", 0, 0, F.LAND_R1, F.WRIST_X[0] - F.LAND_T, F.WRIST_X[0] + 0.01)
    L.cut(land, cyl_x("land bore", 0, 0, F.LAND_R0, F.WRIST_X[0] - 1, F.WRIST_X[0] + 1))
    L.union(b, land)
    L.cut(b, L.box("shim window", BRG5_X[1] + 0.5, F.WRIST_X[0] + 0.5, -SHIM_HALF_W, SHIM_HALF_W,
                   -SKIRT_R - 1.0, -(F.LAND_R1 + 0.5)))   # the glue-up shim comes out here; past the 6705's shoulder, below the land
    L.cut(b, cyl_x("socket", 0, 0, F.TUBE_R, F.WRIST_X[0] - 1, F.WRIST_X[0] + F.SOCKET_DEPTH + F.TUBE_SPARE))
    L.cut(b, L.cyl_between("hub", (PITCH_X, AX5_REAR_Y - 1, 0), (PITCH_X, y1 + 1, 0), 14.0, n=96))   # no final weld: at 0.01 it merges two vertices of the posed mesh into a non-manifold edge
    PRINT_POSE["head-bracket"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y1))   # belt face on the bed
    return b

def motor_plate():
    """A U channel over the belt: walls on the arm's inserts, the pancake on its outer face; it slides on its screws for tension."""
    (pz0, pz1), (wz0, wz1) = MP_LOCAL_Z["plate"], MP_LOCAL_Z["walls"]
    u0, u1 = MOTOR_PLATE_U
    p = L.box("ax5-motor-plate", u0, u1, -MP_WALL_V[1], MP_WALL_V[1], pz0, pz1)
    for sv in (-1, 1):
        v0, v1 = sorted((sv * MP_WALL_V[0], sv * MP_WALL_V[1]))
        L.union(p, L.box("wall", u0, u1, v0, v1, pz1 - 0.01, wz1))
    L.finish(p)
    tool = L.cyl_z("pilot", MOTOR5_X, 0, NEMA_PILOT_R, pz0 - 1, pz1 + 1, n=64)
    for su in (-1, 1):
        for sv in (-1, 1):
            L.union(tool, L.cyl_z("nema", MOTOR5_X + su * NEMA_HOLE_OFF, sv * NEMA_HOLE_OFF, NEMA_HOLE_R, pz0 - 1, pz1 + 1, n=32))
    for u, v in insert_points():   # slotted: the whole plate slides to tension the belt, its screw heads outside
        L.union(tool, slot("screw", u, v, 1.7, SLOT, pz0 - 1, wz1 + 1))
        L.union(tool, slot("counterbore", u, v, 3.0, SLOT, pz0 - 1, pz0 + MP_CB_DEPTH))
    L.cut(p, tool)
    p.data.transform(ax5_matrix())
    PRINT_POSE["ax5-motor-plate"] = Matrix.Translation((0, 0, -pz0)) @ ax5_matrix().inverted()   # outer face on the bed
    return p

def screw_heads():
    """M3 socket heads, Ø5.5 x 3, seated in the motor plate's counterbores."""
    z = MP_LOCAL_Z["plate"][0] + MP_CB_DEPTH
    heads = None
    for u, v in insert_points():
        h = L.cyl_z("head", u, v, BOLT_HEAD_R, z - BOLT_HEAD_H, z, n=32)
        if heads is None:
            heads = h
        else:
            L.union(heads, h)
    heads.data.transform(ax5_matrix())
    return heads

def check_head_bracket():
    b = PARTS["head-bracket"]
    assert L.stats(b)["non_manifold"] == 0
    seat_x = sum(BRG5_X) / 2
    assert abs(radial_bore(b, seat_x) - 2 * BRG5_R_OUT) < 0.05, ("6705 seat", radial_bore(b, seat_x))
    assert abs(radial_bore(b, BRG5_X[1] + 0.25) - 2 * SHOULDER_R) < 0.05, ("6705 shoulder", radial_bore(b, BRG5_X[1] + 0.25))
    assert SHOULDER_R >= BRG5_R_IN + 1.0 and SHOULDER_R < BRG5_R_OUT - 1.0, "shoulder rubs the inner ring or misses the outer"
    assert abs(radial_bore(b, F.WRIST_X[0] + F.SOCKET_DEPTH / 2) - 2 * F.TUBE_R) < 0.03, ("Ø11 socket", radial_bore(b, F.WRIST_X[0] + F.SOCKET_DEPTH / 2))
    assert abs(radial_bore(b, F.TUBE_X[1] + 0.75) - 2 * F.TUBE_R) < 0.03, "tube bottoms in the socket: the shim must set the play"
    land_r = (F.LAND_R0 + F.LAND_R1) / 2
    h = tree(b).ray_cast(Vector((F.WRIST_X[0] - 1.0, land_r, 0)), Vector((1, 0, 0)))[0]
    assert h is not None and abs(h.x - (F.WRIST_X[0] - F.LAND_T)) < 0.05, ("land on the 6701's inner ring", h)
    for y in (-SHIM_HALF_W + 0.5, 0.0, SHIM_HALF_W - 0.5):   # a horseshoe shim between the land and the 6701 slides out along -z
        hit = tree(b).ray_cast(Vector((SHIM_X, y, -(F.LAND_R1 + 0.5))), Vector((0, 0, -1)))[0]
        assert hit is None, ("0.3 shim trapped in the shoulder pocket", y, hit)
    rmin = min(math.hypot(v.co.y, v.co.z) for v in b.data.vertices if v.co.x < F.OUTER_X[1])
    REPORT["roll_clearance_r"] = round(rmin, 2)
    assert rmin >= F.OUTER_R + 1.0, ("head rubs the fixed outer tube as it rolls", rmin)
    assert PITCH_X - HOUSING_R - BOSS_X[1] >= 1.0 - 1e-6, "boss within 1 of the axis 5 housing"
    ax5 = ax5_housing()
    tube, brg = forearm_parts()
    near, far = ax5_pancake(MOTOR5_X - SLOT), ax5_pancake(MOTOR5_X + SLOT)
    bad = {k: round(v, 3) for k, v in {"ax5": overlap(b, ax5), "tube": overlap(b, tube),
                                       "pancake near": overlap(b, near), "pancake far": overlap(b, far),
                                       "pancake/tube": overlap(near, tube), "pancake far/tube": overlap(far, tube),
                                       "pancake/6705": overlap(near, brg), "pancake/ax5": overlap(near, ax5),
                                       "pancake far/ax5": overlap(far, ax5)}.items() if v > 0.05}
    assert not bad, bad
    for u in (MOTOR5_X - SLOT, MOTOR5_X + SLOT):
        assert through_mount(b, u, 0) is None, ("no pilot slot for the pancake's shaft", u)
    t = tree(b)
    for u, v in insert_points():
        top = ax5_matrix() @ Vector((u, v, -MOUNT_T - 1.0))
        hit = t.ray_cast(top, Vector((0, -1, 0)))[0]
        assert hit is not None and abs(hit.y - (AX5_REAR_Y + MOUNT_T - INSERT_DEPTH)) < 0.05, ("motor plate insert hole", u, v, hit)
    for o in (near, far):
        bpy.data.objects.remove(o)
    assert BRG5_R_IN == F.OUTER_R and F.OUTER_X[0] < BRG5_X[0] and BRG5_X[1] <= F.OUTER_X[1], "6705 not on the outer tube's end"
    for a in BOLT_ANGLES:
        p = ax5_matrix() @ Vector((*polar(BOLT_R, a), 1.0))
        hit = t.ray_cast(p, Vector((0, 1, 0)))[0]
        assert hit is None, ("axis 5 housing bolt hole blocked", a, hit)
    assert overlap(b, brg) > 0.0 or touching(brg, b), "6705 seat not on the 6705"
    ys = [v.co.y for v in b.data.vertices]
    assert max(ys) <= AX5_REAR_Y + MOUNT_T + 1e-3 and min(ys) >= -SKIRT_R - 1e-3, ("bracket leaves its y slab", min(ys), max(ys))
    for o in (ax5, tube, brg):
        bpy.data.objects.remove(o)

def belt_envelope(u_motor):
    """Hull of the 20T and the 60T, 1.5 over their pitch radii, across the belt's width plus 0.5 each side."""
    bm = bmesh.new()
    for u, r in ((u_motor, 20 / math.pi + 1.5), (0.0, 60 / math.pi + 1.5)):
        for k in range(48):
            a = 2 * math.pi * k / 48
            for z in (BELT_PLANE - 3.5, BELT_PLANE + 3.5):
                bm.verts.new((u + r * math.cos(a), r * math.sin(a), z))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new("belt"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("belt envelope", me); bpy.context.scene.collection.objects.link(o)
    o.data.transform(ax5_matrix())
    return o

def check_motor_plate():
    p, b = PARTS["ax5-motor-plate"], PARTS["head-bracket"]
    assert L.stats(p)["non_manifold"] == 0
    t = tree(p)
    for su, sv in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        q = ax5_matrix() @ Vector((MOTOR5_X + su * NEMA_HOLE_OFF, sv * NEMA_HOLE_OFF, MP_LOCAL_Z["plate"][1] + 0.5))
        assert t.ray_cast(q, Vector((0, 1, 0)))[0] is None, ("motor hole closed", su, sv)
    for u, v in insert_points():
        q = ax5_matrix() @ Vector((u, v - math.copysign(2.4, v), MP_LOCAL_Z["plate"][0] - 1.0))   # inside the counterbore, beside the slot
        hit = t.ray_cast(q, Vector((0, -1, 0)))[0]
        floor_y = AX5_REAR_Y - MP_LOCAL_Z["plate"][0] - MP_CB_DEPTH
        assert hit is not None and abs(hit.y - floor_y) < 0.05, ("counterbore", u, v, hit)
        q = ax5_matrix() @ Vector((u, v, MP_LOCAL_Z["plate"][0] - MP_CB_DEPTH - 0.5))
        assert t.ray_cast(q, Vector((0, -1, 0)))[0] is None, ("screw hole through the plate", u, v)
        for du in (-SLOT, SLOT):   # the plate slides on its four screws to tension the belt; the heads stay outside
            q = ax5_matrix() @ Vector((u + du, v, MP_LOCAL_Z["plate"][0] - MP_CB_DEPTH - 0.5))
            assert t.ray_cast(q, Vector((0, -1, 0)))[0] is None, ("plate screw hole not slotted for tensioning", u, du)
    tip = MP_LOCAL_Z["plate"][0] + MP_CB_DEPTH + MP_SCREW_L
    assert tip <= -MOUNT_T + INSERT_DEPTH + 1e-6 and tip - (-MOUNT_T) >= 4.0, ("M3 x 20 misses the insert", tip)
    near, far = ax5_pancake(MOTOR5_X - SLOT), ax5_pancake(MOTOR5_X + SLOT)
    heads = screw_heads()
    lb = PARTS["ax6-l-bracket"]
    checks = {"heads/near": overlap(heads, near), "heads/far": overlap(heads, far), "pancake/l-bracket": overlap(near, lb)}
    for name, du in (("near", -SLOT), ("far", SLOT)):   # plate and pancake slide together
        ps = copy(p, "plate " + name); ps.data.transform(Matrix.Translation(ax5_matrix().to_3x3() @ Vector((du, 0, 0))))
        pan = near if du < 0 else far
        env = belt_envelope(MOTOR5_X + du)
        checks["plate " + name + "/pancake"], checks["plate " + name + "/bracket"] = overlap(ps, pan), overlap(ps, b)
        checks["belt " + name + "/plate"], checks["belt " + name + "/bracket"] = overlap(env, ps), overlap(env, b)
        assert touching(pan, ps), ("pancake face not on the motor plate", name)
        bpy.data.objects.remove(env); bpy.data.objects.remove(ps)
    bad = {k: round(v, 3) for k, v in checks.items() if v > 0.05}
    assert not bad, bad
    py = [v.co.y for o in (near, far) for v in o.data.vertices]
    REPORT["pancake_y"] = [round(min(py), 2), round(max(py), 2)]
    REPORT["heads_to_pancake_mm"] = round(min(min_gap(heads, near), min_gap(heads, far)), 2)
    for o in (near, far, heads):
        bpy.data.objects.remove(o)

def ax6_mount_matrix():
    """Axis 6's assembly frame into the wrist frame: z along +x from the T8 housing's rear face, the mount's arm up."""
    return basis((0, 0, 1), (0, -1, 0), (1, 0, 0), (AX6_REAR_X, AX6_Y, 0))

def ax5_output_plate_posed():
    return posed_stl(os.path.join(FOREARM, "ax4-output-plate.stl"), "ax5 output plate",
                     ax5_matrix() @ Matrix.Translation((0, 0, F.PLATE_X[0])), (0.0, F.PLATE_X[1] - F.PLATE_X[0] + F.DOG_H))

def t8_housings_posed():
    h = posed_stl(os.path.join(T8, "housing-rear.stl"), "ax6 housing", Matrix(), (0.0, T8_HOUSING_L / 2))
    L.union(h, posed_stl(os.path.join(T8, "housing-front.stl"), "ax6 housing-front", Matrix.Diagonal((1, -1, -1, 1)), (-T8_HOUSING_L, -T8_HOUSING_L / 2)))
    h.data.transform(ax6_mount_matrix())
    return h

def ax5_front_bolt_heads():
    heads = L.cyl_z("ax5 bolt heads", *polar(BOLT_R, BOLT_ANGLES[0]), BOLT_HEAD_R, 38.6, 38.6 + BOLT_HEAD_H, n=32)
    for a in BOLT_ANGLES[1:]:
        L.union(heads, L.cyl_z("head", *polar(BOLT_R, a), BOLT_HEAD_R, 38.6, 38.6 + BOLT_HEAD_H, n=32))
    heads.data.transform(ax5_matrix())
    return heads

def dog_point(a, w):
    """A dog's centre at height w in axis 5's output frame, in the wrist frame."""
    return ax5_matrix() @ Vector((*polar(F.DOG_PCD_R, a), w))

def dog_hole_depth(lb, a):
    p = dog_point(a, AX5_REAR_Y - LB_Y[0] - 1.0)
    h = tree(lb).ray_cast(p, Vector((0, -1, 0)))[0]
    return round(LB_Y[0] - h.y, 3) if h is not None else None

def cyl_y(name, x, z, r, y0, y1, n=128):
    c = L.cyl_z(name, 0, 0, r, y0, y1, n=n)
    c.data.transform(basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (x, 0, z)))
    return c

def l_bracket():
    """Axis 5's output to axis 6 and the gripper motor in one piece: a disc on the output plate's dogs, two legs back
    along axis 6 joining it to axis 6's T8 188 mount and to the gripper motor's disc, and a bar tying the two on the far side."""
    lb = posed_stl(os.path.join(T8, "motor-mount.stl"), "ax6-l-bracket", ax6_mount_matrix(), (-6.0, 5.0))
    L.union(lb, cyl_y("base disc", PITCH_X, 0, LB_R, LB_Y[1], LB_Y[0]))
    m7 = L.cyl_z("motor7 disc", 0, 0, MOTOR7_DISC_R, *MOTOR7_DISC_Z, n=160)
    m7.data.transform(ax6_mount_matrix())
    L.union(lb, m7)
    for z0, z1 in ((RIB_Z0, RIB_Z1), (-RIB_Z1, -RIB_Z0)):    # the open cage between them is the driver's way to the base disc's screws
        L.union(lb, L.box("leg", AX6_REAR_X + MOTOR7_DISC_Z[0], AX6_REAR_X, -45.0, LB_Y[0], z0, z1))
    far = L.box("far post", -FAR_POST_HALF_X, FAR_POST_HALF_X, *FAR_POST_Y, MOTOR7_DISC_Z[1] - 0.01, -MOUNT_T + 0.01)
    far.data.transform(ax6_mount_matrix())
    L.union(lb, far)
    m7_holes = L.cyl_z("pilot", 0, 0, NEMA_PILOT_R, MOTOR7_DISC_Z[0] - 1, MOTOR7_DISC_Z[1] + 1, n=96)
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.union(m7_holes, L.cyl_z("nema", sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, NEMA_HOLE_R, MOTOR7_DISC_Z[0] - 1, MOTOR7_DISC_Z[1] + 1, n=32))
    m7_holes.data.transform(ax6_mount_matrix())
    L.cut(lb, m7_holes)
    w0, w1 = AX5_REAR_Y - LB_Y[0] - 1.0, AX5_REAR_Y - LB_Y[0] + F.DOG_H + 0.5
    for a in F.DOG_ANGLES:
        L.cut(lb, L.cyl_between("dog hole", dog_point(a, w0), dog_point(a, w1), F.DOG_R + 0.25, n=48))
    L.cut(lb, cyl_y("sight hole", PITCH_X, 0, 2.5, LB_Y[1] - 1, LB_Y[0] + 1, n=48))
    w_face = AX5_REAR_Y - LB_Y[1]
    for a in F.INSERT_ANGLES:   # M3 x 12 through the disc and the output plate into the carrier's inserts; driven first, through the empty cage
        L.cut(lb, L.cyl_between("screw", ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face - 7.0)),
                                ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face + 1.0)), 1.7, n=32))
        L.cut(lb, L.cyl_between("head", ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face - LB_SCREW_CB)),
                                ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face + 1.0)), 3.0, n=48))
    L.finish(lb)
    PRINT_POSE["ax6-l-bracket"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, LB_Y[0]))   # base disc's +y face on the bed
    return lb

def ax6_local(x, y, z):
    return ax6_mount_matrix() @ Vector((x, y, z))

def islands(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen, n = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        n += 1; stack = [v]
        while stack:
            w = stack.pop()
            if w.index in seen:
                continue
            seen.add(w.index)
            stack += [e.other_vert(w) for e in w.link_edges]
    bm.free(); return n

def driver_tilt(t, head):
    """Smallest tilt in z (deg) at which a 2.5 hex key's shaft, from the head out along -y, clears the part."""
    for step in range(0, 41):
        for sign in (1, -1):
            ang = math.radians(0.5 * step * sign)
            d = Vector((0, -math.cos(ang), math.sin(ang)))
            offs = [Vector()] + [Vector((DRIVER_R * math.cos(k * math.pi / 4), 0, DRIVER_R * math.sin(k * math.pi / 4))) for k in range(8)]
            if all(t.ray_cast(head + o, d)[0] is None for o in offs):
                return 0.5 * step
    return 99.0

def gripper_parts_posed():
    """The gripper motor's screw heads on the disc's front, its body behind, and the coupler, in the wrist frame."""
    heads = L.cyl_z("motor7 heads", NEMA_HOLE_OFF, NEMA_HOLE_OFF, BOLT_HEAD_R, MOTOR7_DISC_Z[1], MOTOR7_DISC_Z[1] + BOLT_HEAD_H, n=32)
    for sx, sy in ((-1, 1), (1, -1), (-1, -1)):
        L.union(heads, L.cyl_z("head", sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, BOLT_HEAD_R, MOTOR7_DISC_Z[1], MOTOR7_DISC_Z[1] + BOLT_HEAD_H, n=32))
    body = L.box("motor7 body", -21.15, 21.15, -21.15, 21.15, MOTOR7_DISC_Z[0] - 20.0, MOTOR7_DISC_Z[0])
    coupler = L.cyl_z("coupler", 0, 0, 9.5, -50.0, -25.0, n=48)
    for o in (heads, body, coupler):
        o.data.transform(ax6_mount_matrix())
    return heads, body, coupler

def check_l_bracket():
    lb = PARTS["ax6-l-bracket"]
    assert L.stats(lb)["non_manifold"] == 0
    assert islands(lb) == 1, ("bracket is not one piece", islands(lb))
    plate = ax5_output_plate_posed()
    t8 = t8_housings_posed()
    heads = ax5_front_bolt_heads()
    m7_heads, m7_body, coupler = gripper_parts_posed()
    bad = {k: round(v, 3) for k, v in {"plate": overlap(lb, plate), "t8": overlap(lb, t8), "heads": overlap(lb, heads),
                                       "motor7 heads": overlap(lb, m7_heads), "motor7 body": overlap(lb, m7_body),
                                       "coupler": overlap(lb, coupler)}.items() if v > 0.05}
    assert not bad, bad
    leg_gaps = []
    for sx in (-1, 1):          # the two heads on the legs' side; their tops face the legs across y
        top = ax6_local(sx * NEMA_HOLE_OFF, -(NEMA_HOLE_OFF + BOLT_HEAD_R), MOTOR7_DISC_Z[1] + BOLT_HEAD_H / 2)
        h = tree(lb).ray_cast(top, Vector((0, 1, 0)))[0]
        leg_gaps.append((h - top).length if h is not None else 99.0)
    REPORT["motor7_heads_to_legs_mm"] = round(min(leg_gaps), 2)
    assert REPORT["motor7_heads_to_legs_mm"] >= 0.5, ("gripper motor screw heads within 0.5 of the legs", REPORT["motor7_heads_to_legs_mm"])
    assert max(v.co.y for v in lb.data.vertices) <= LB_Y[0] + 1e-3, "L-bracket reaches into axis 5's slab"
    assert LB_Y[0] - (-22.3) <= -3.0, "base disc within 3 of axis 5's bolt heads"
    for a in F.DOG_ANGLES:
        d = dog_hole_depth(lb, a)
        assert d is not None and d >= F.DOG_H + 0.5 - 0.05, ("dog hole too shallow", a, d)
    assert AX6_Y + HOUSING_R <= -25.0, "axis 6 housing reaches axis 5's slab"
    t = tree(lb)
    tilts = []
    for a in F.INSERT_ANGLES:   # L-bracket to axis 5: M3 through the disc and output plate, driven from -y through the cage
        p = ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), AX5_REAR_Y - LB_Y[0] - 1.0))
        h = t.ray_cast(p, Vector((0, -1, 0)))[0]
        assert h is None or h.y < LB_Y[1] - 0.5, ("no screw hole through the base disc", a)
        for k in range(4):
            q = ax5_matrix() @ (Vector((*polar(F.INSERT_PCD_R, a), AX5_REAR_Y - LB_Y[1] + 1.0)) + Vector((*polar(2.4, 90 * k), 0)))
            h = t.ray_cast(q, Vector((0, 1, 0)))[0]
            assert h is not None and abs(h.y - (LB_Y[1] + LB_SCREW_CB)) < 0.05, ("screw head counterbore not reachable from -y", a, k, h)
        tilts.append(driver_tilt(t, ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), AX5_REAR_Y - LB_Y[1] - LB_SCREW_CB + 0.05))))
    REPORT["base_disc_driver_tilt_deg"] = max(tilts)
    assert max(tilts) <= DRIVER_MAX_TILT, ("base disc screws need too steep a ball-end driver", tilts)
    post = t.ray_cast(ax6_local(0, 45.0, -30.0), Vector((0, 1, 0)))[0]
    assert post is not None and abs(post.y - (AX6_Y - FAR_POST_Y[1])) < 0.05, ("no far post", post)
    disc = t.ray_cast(ax6_local(0, 22.0, -40.0), Vector((-1, 0, 0)))[0]
    assert disc is not None and abs(disc.x - (AX6_REAR_X + MOTOR7_DISC_Z[1])) < 0.05, ("no gripper motor disc", disc)
    for sx, sy in ((0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):   # pilot and the four NEMA holes open through the disc
        o = ax6_local(sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, -40.0)
        assert t.ray_cast(o, Vector((-1, 0, 0)))[0] is None, ("gripper motor hole blocked", sx, sy)
    for a in BOLT_ANGLES:       # axis 6 housing bolts: hole open and a whole nut pocket on the mount's belt face
        c = ax6_mount_matrix() @ Vector((*polar(BOLT_R, a), 1.0))
        b_out = t.ray_cast(c, Vector((-1, 0, 0)))[0]   # the M3 x 50 ends at its nut; the gripper motor's disc is past that
        assert b_out is None or b_out.x <= AX6_REAR_X + MOTOR7_DISC_Z[1] + 0.05, ("axis 6 bolt hole blocked", a)
        mid = ax6_mount_matrix() @ Vector((*polar(BOLT_R, a), -MOUNT_T + NUT_T / 2))
        wall = min((t.ray_cast(mid, Vector((0, math.cos(k * math.pi / 12), math.sin(k * math.pi / 12))))[0] - mid).length for k in range(24))
        assert wall >= NUT_AF / 2 - 0.05, ("axis 6 nut pocket narrowed", a, round(wall, 2))
        n_out = t.ray_cast(mid, Vector((-1, 0, 0)))[0]
        assert n_out is None or n_out.x <= AX6_REAR_X + MOTOR7_DISC_Z[1] + 0.05, ("nut can't go into its pocket", a)
    assert -45.0 >= AX6_Y + 40 / math.pi + 3.0, "gusset within 3 of axis 6's 40T / belt"
    for o in (plate, t8, heads, m7_heads, m7_body, coupler):
        bpy.data.objects.remove(o)

REPORT = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["head-bracket"] = head_bracket()
PARTS["ax6-l-bracket"] = l_bracket()
PARTS["ax5-motor-plate"] = motor_plate()
CHECKS.append(check_head_bracket)
CHECKS.append(check_motor_plate)
CHECKS.append(check_l_bracket)

for check in CHECKS:
    check()
print("WRIST", json.dumps({**{n: L.stats(o) for n, o in PARTS.items()}, "ax6_offset_y": AX6_Y, "pitch_x": PITCH_X, **REPORT}))
os.makedirs(OUT, exist_ok=True)
for n, o in PARTS.items():
    o.matrix_world = Matrix()
    o.data.transform(PRINT_POSE[n])
    L.export(o, os.path.join(OUT, n + ".stl"))
print("WRIST DONE")
