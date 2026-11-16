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
MOTOR7_POST_R, MOTOR7_POST_RAD = 26.0, 4.5      # cycloid_poc's POST_R, POST_RAD
RIB_Z0, RIB_Z1 = 8.0, 17.0                     # between the motor7 post (z ±4.5) and axis 6's nut pockets (from z 17.85)
NUT_AF, NUT_T = 5.8, 2.6                         # cycloid_poc's nut pockets in the T8 mount
LB_SCREW_CB = 2.8                                # M3 x 12 then reaches 3.3 into the carrier's inserts

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
    dx, dz = math.cos(math.radians(AX5_MOTOR_ANGLE)), math.sin(math.radians(AX5_MOTOR_ANGLE))
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
    """The pancake as the mount's rails hold it: square to the arm, face on the mount, body on the housing side."""
    s = 42.3 / 2
    m = L.box("ax5 pancake", x - s, x + s, -s, s, 0.0, 23.0)
    m.data.transform(ax5_matrix())
    return m

def through_mount(b, u, v):
    """First hit of a ray from the housing side straight through axis 5's mount at its local (u, v), or None."""
    return tree(b).ray_cast(ax5_matrix() @ Vector((u, v, 1.0)), Vector((0, 1, 0)))[0]

def forearm_parts():
    m = forearm_matrix()
    hub = posed_stl(os.path.join(FOREARM, "wrist-flange-hub.stl"), "wrist hub",
                    m @ Matrix.Diagonal((1, -1, -1, 1)) @ Matrix.Translation((0, 0, -F.FLANGE_FACE)), (0.0, F.WRIST_X[1] - F.WRIST_X[0] + F.LAND_T))
    tube = posed_stl(os.path.join(FOREARM, "forearm-outer-tube.stl"), "outer tube",
                     m @ Matrix.Translation((0, 0, F.OUTER_X[0])), (0.0, F.OUTER_X[1] - F.OUTER_X[0]))
    brg = cyl_x("6705", 0, 0, BRG5_R_OUT, *BRG5_X)
    L.cut(brg, cyl_x("bore", 0, 0, BRG5_R_IN, BRG5_X[0] - 1, BRG5_X[1] + 1))
    return hub, tube, brg

def slot(name, x, y, r, half, z0, z1):
    s = L.cyl_z(name, x - half, y, r, z0, z1, n=32)
    L.union(s, L.cyl_z(name + "_b", x + half, y, r, z0, z1, n=32))
    L.union(s, L.box(name + "_m", x - half, x + half, y - r, y + r, z0, z1))
    return s

def lengthen_arm(b):
    """The T8 mount's arm is set for the 188; rebuild it past the disc and re-slot it for the 20T/60T on the 234.
    Done in the mount's own frame, before it is posed: faces on the posed STL's are only nearly coplanar and leave slivers."""
    x1 = MOTOR5_X + SLOT + MOUNT_HALF_W
    L.cut(b, L.box("old arm", ARM_CUT_X, 120.0, -MOUNT_HALF_W - 5, MOUNT_HALF_W + 5, -MOUNT_T - 5, RAIL_H + 5))
    L.union(b, L.box("arm", ARM_CUT_X - 1, x1, -MOUNT_HALF_W, MOUNT_HALF_W, -MOUNT_T, 0))
    for sv in (-1, 1):
        v0, v1 = sorted((sv * RAIL_GAP / 2, sv * MOUNT_HALF_W))
        L.union(b, L.box("rail", ARM_CUT_X - 1, x1, v0, v1, -0.01, RAIL_H))
    slots = slot("pilot", MOTOR5_X, 0, NEMA_PILOT_R, SLOT, -MOUNT_T - 1, 1)
    for su in (-1, 1):
        for sv in (-1, 1):
            L.union(slots, slot("nema", MOTOR5_X + su * NEMA_HOLE_OFF, sv * NEMA_HOLE_OFF, NEMA_HOLE_R, SLOT, -MOUNT_T - 1, 1))
    L.finish(b)
    L.cut(b, slots)   # one cut: cut one by one, the second screw slot left non-manifold edges

def head_bracket():
    """Bolts to the wrist flange, rides the 6705 on the outer tube, and is axis 5's mount (20T/60T on a 234)."""
    y1 = AX5_REAR_Y + 6.0
    b = posed_stl(os.path.join(T8, "motor-mount.stl"), "head-bracket", Matrix(), (-6.0, 5.0))
    lengthen_arm(b)
    b.data.transform(ax5_matrix())
    plate = cyl_x("plate", 0, 0, PLATE_R, *PLATE_X)
    L.union(plate, L.box("plate to mount", *PLATE_X, 0, y1, -PLATE_HALF_Z, PLATE_HALF_Z))
    L.union(b, plate)
    L.union(b, L.box("bridge", PLATE_X[0], BRIDGE_X1, AX5_REAR_Y, y1, -16.0, 16.0))   # ends before the R30 bolt and nut pocket at 205°
    skirt = cyl_x("skirt", 0, 0, SKIRT_R, BRG5_X[0], PLATE_X[0] + 0.01)
    L.cut(skirt, cyl_x("bore", 0, 0, SKIRT_BORE_R, BRG5_X[0] - 1, PLATE_X[0]))
    L.cut(skirt, cyl_x("6705 seat", 0, 0, BRG5_R_OUT, BRG5_X[0] - 1, BRG5_X[1]))
    L.union(b, skirt)
    for a in F.FLANGE_ANGLES:
        y, z = polar(F.FLANGE_INSERT_R, a)
        L.cut(b, cyl_x("flange screw", y, z, FLANGE_HOLE_R, PLATE_X[0] - 1, PLATE_X[1] + 1, n=32))
        L.cut(b, cyl_x("counterbore", y, z, FLANGE_CB_R, PLATE_X[1] - FLANGE_CB_DEPTH, PLATE_X[1] + 1, n=48))
    L.cut(b, L.cyl_between("hub", (PITCH_X, AX5_REAR_Y - 1, 0), (PITCH_X, y1 + 1, 0), 14.0, n=96))   # no final weld: at 0.01 it merges two vertices of the posed mesh into a non-manifold edge
    PRINT_POSE["head-bracket"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y1))   # belt face on the bed
    return b

def check_head_bracket():
    b = PARTS["head-bracket"]
    assert L.stats(b)["non_manifold"] == 0
    seat_x = sum(BRG5_X) / 2
    assert abs(radial_bore(b, seat_x) - 2 * BRG5_R_OUT) < 0.05, ("6705 seat", radial_bore(b, seat_x))
    assert abs(radial_bore(b, F.WRIST_X[0] + 5) - 2 * SKIRT_BORE_R) < 0.05, "skirt bore over the wrist hub"
    assert SKIRT_BORE_R - F.WRIST_R >= 0.5 and SKIRT_BORE_R < BRG5_R_OUT, "hub rubs the skirt, or the shoulder misses the outer ring"
    for a in F.FLANGE_ANGLES:
        y, z = polar(F.FLANGE_INSERT_R + 2.4, a)   # inside the counterbore, outside the clearance hole
        assert abs(x_floor(b, y, z, PLATE_X[1] + 10) - (PLATE_X[1] - FLANGE_CB_DEPTH)) < 0.05, ("flange screw counterbore", a)
    assert PITCH_X - HOUSING_R - PLATE_X[1] >= 1.5, "plate hits the axis 5 housing"
    ax5 = ax5_housing()
    hub, tube, brg = forearm_parts()
    near, far = ax5_pancake(MOTOR5_X - SLOT), ax5_pancake(MOTOR5_X + SLOT)
    bad = {k: round(v, 3) for k, v in {"ax5": overlap(b, ax5), "hub": overlap(b, hub), "tube": overlap(b, tube),
                                       "pancake near": overlap(b, near), "pancake far": overlap(b, far),
                                       "pancake/tube": overlap(near, tube)}.items() if v > 0.05}
    assert not bad, bad
    assert MOTOR5_X - SLOT - 42.3 / 2 >= HOUSING_R + 2.0, "pancake hits the axis 5 housing"
    for u in (MOTOR5_X - SLOT, MOTOR5_X + SLOT):
        assert through_mount(b, u, 0) is None, ("no pilot slot for the 60T centre distance", u)
        for su in (-1, 1):
            for sv in (-1, 1):
                assert through_mount(b, u + su * NEMA_HOLE_OFF, sv * NEMA_HOLE_OFF) is None, ("no motor screw slot", u, su, sv)
    assert through_mount(b, BELT_C - NEMA_HOLE_OFF, NEMA_HOLE_OFF) is not None, "the 188's motor screw slot is still open"
    for o in (near, far):
        bpy.data.objects.remove(o)
    assert BRG5_R_IN == F.OUTER_R and F.OUTER_X[0] < BRG5_X[0] and BRG5_X[1] <= F.OUTER_X[1], "6705 not on the outer tube's end"
    t = tree(b)
    for a in BOLT_ANGLES:
        p = ax5_matrix() @ Vector((*polar(BOLT_R, a), 1.0))
        hit = t.ray_cast(p, Vector((0, 1, 0)))[0]
        assert hit is None, ("axis 5 housing bolt hole blocked", a, hit)
    assert overlap(b, brg) > 0.0 or touching(brg, b), "skirt not on the 6705"
    ys = [v.co.y for v in b.data.vertices]
    assert max(ys) <= AX5_REAR_Y + 6.0 + 1e-3 and min(ys) >= -PLATE_R - 1e-3, ("bracket leaves its y slab", min(ys), max(ys))
    for o in (ax5, hub, tube, brg):
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
    """Axis 5's output to axis 6: a disc on the output plate's dogs, ribbed into a T8 188 mount that is axis 6's own."""
    lb = posed_stl(os.path.join(T8, "motor-mount.stl"), "ax6-l-bracket", ax6_mount_matrix(), (-6.0, 5.0))
    L.union(lb, cyl_y("base disc", PITCH_X, 0, LB_R, LB_Y[1], LB_Y[0]))
    for z0, z1 in ((RIB_Z0, RIB_Z1), (-RIB_Z1, -RIB_Z0)):    # the gap between them clears the motor7 post at z 0
        L.union(lb, L.box("rib", PITCH_X + 5.0, AX6_REAR_X, -45.0, LB_Y[0], z0, z1))
    w0, w1 = AX5_REAR_Y - LB_Y[0] - 1.0, AX5_REAR_Y - LB_Y[0] + F.DOG_H + 0.5
    for a in F.DOG_ANGLES:
        L.cut(lb, L.cyl_between("dog hole", dog_point(a, w0), dog_point(a, w1), F.DOG_R + 0.25, n=48))
    L.cut(lb, cyl_y("sight hole", PITCH_X, 0, 2.5, LB_Y[1] - 1, LB_Y[0] + 1, n=48))
    w_face = AX5_REAR_Y - LB_Y[1]
    for a in F.INSERT_ANGLES:   # M3 x 12 through the disc and the output plate into the carrier's inserts; in before the motor7 bracket, whose post hides them
        L.cut(lb, L.cyl_between("screw", ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face - 7.0)),
                                ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face + 1.0)), 1.7, n=32))
        L.cut(lb, L.cyl_between("head", ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face - LB_SCREW_CB)),
                                ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), w_face + 1.0)), 3.0, n=48))
    L.finish(lb)
    PRINT_POSE["ax6-l-bracket"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, LB_Y[0]))   # base disc's +y face on the bed
    return lb

def check_l_bracket():
    lb = PARTS["ax6-l-bracket"]
    assert L.stats(lb)["non_manifold"] == 0
    plate = ax5_output_plate_posed()
    t8 = t8_housings_posed()
    posts = posed_stl(os.path.join(T8, "motor7-bracket.stl"), "motor7", ax6_mount_matrix(), (-56.0, -6.0))
    heads = ax5_front_bolt_heads()
    bad = {k: round(v, 3) for k, v in {"plate": overlap(lb, plate), "t8": overlap(lb, t8), "posts": overlap(lb, posts),
                                       "heads": overlap(lb, heads)}.items() if v > 0.05}
    assert not bad, bad
    post_y = AX6_Y + MOTOR7_POST_R              # the post on the base disc's side, on the axis 6 axis' z
    gap = min(LB_Y[1] - (post_y + MOTOR7_POST_RAD), RIB_Z0 - MOTOR7_POST_RAD)
    REPORT["post_gap_mm"] = round(gap, 2)
    assert gap >= 1.0, ("gripper bracket post within 1 mm of the L-bracket", gap)
    assert max(v.co.y for v in lb.data.vertices) <= LB_Y[0] + 1e-3, "L-bracket reaches into axis 5's slab"
    assert LB_Y[0] - (-22.3) <= -3.0, "base disc within 3 of axis 5's bolt heads"
    for a in F.DOG_ANGLES:
        d = dog_hole_depth(lb, a)
        assert d is not None and d >= F.DOG_H + 0.5 - 0.05, ("dog hole too shallow", a, d)
    assert AX6_Y + HOUSING_R <= -25.0, "axis 6 housing reaches axis 5's slab"
    t = tree(lb)
    for a in F.INSERT_ANGLES:   # L-bracket to axis 5: M3 through the disc and output plate into the carrier's inserts
        p = ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R, a), AX5_REAR_Y - LB_Y[0] - 1.0))
        assert t.ray_cast(p, Vector((0, -1, 0)))[0] is None, ("no screw hole through the base disc", a)
        q = ax5_matrix() @ Vector((*polar(F.INSERT_PCD_R + 2.4, a), AX5_REAR_Y + 200.0))
        h = t.ray_cast(q, Vector((0, 1, 0)))[0]
        assert h is not None and abs(h.y - (LB_Y[1] + LB_SCREW_CB)) < 0.05, ("screw head counterbore not reachable from -y", a, h)
    for a in BOLT_ANGLES:       # axis 6 housing bolts: hole open and a whole nut pocket on the mount's belt face
        c = ax6_mount_matrix() @ Vector((*polar(BOLT_R, a), 1.0))
        assert t.ray_cast(c, Vector((-1, 0, 0)))[0] is None, ("axis 6 bolt hole blocked", a)
        mid = ax6_mount_matrix() @ Vector((*polar(BOLT_R, a), -MOUNT_T + NUT_T / 2))
        wall = min((t.ray_cast(mid, Vector((0, math.cos(k * math.pi / 12), math.sin(k * math.pi / 12))))[0] - mid).length for k in range(24))
        assert wall >= NUT_AF / 2 - 0.05, ("axis 6 nut pocket narrowed", a, round(wall, 2))
    assert -45.0 >= AX6_Y + 40 / math.pi + 3.0, "gusset within 3 of axis 6's 40T / belt"
    for o in (plate, t8, posts, heads):
        bpy.data.objects.remove(o)

REPORT = {}
bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["head-bracket"] = head_bracket()
PARTS["ax6-l-bracket"] = l_bracket()
CHECKS.append(check_head_bracket)
CHECKS.append(check_l_bracket)

for check in CHECKS:
    check()
print("WRIST", json.dumps({**{n: L.stats(o) for n, o in PARTS.items()}, "ax6_offset_y": AX6_Y, **REPORT}))
os.makedirs(OUT, exist_ok=True)
for n, o in PARTS.items():
    o.matrix_world = Matrix()
    o.data.transform(PRINT_POSE[n])
    L.export(o, os.path.join(OUT, n + ".stl"))
print("WRIST DONE")
