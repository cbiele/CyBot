"""Axis 4 forearm parts: the 20:1 compact at the elbow end turns the 190 mm aluminium tube inside a fixed printed tube.
Built and checked in the forearm frame (forearm_dims.py, x on z), exported in print orientation to model/forearm-tube/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/forearm_tube.py"""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
from forearm_dims import *
import cycloid_math as C
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT = os.path.join(ROOT, "model", "forearm-tube")
PARTS, CHECKS, PRINT_POSE = {}, [], {}

def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

def outer_tube():
    """Fixed: bolts to the compact's front face through the housing bolts, carries both 6701s."""
    x0, x1 = OUTER_X
    cone_x = REAR_BRG_X[1] + (OUTER_REAR_R - OUTER_R)
    o = L.cyl_z("forearm-outer-tube", 0, 0, HOUSING_R, x0, x0 + OUTER_FLANGE_T, n=160)
    L.union(o, L.cyl_z("rear", 0, 0, OUTER_REAR_R, x0 + OUTER_FLANGE_T - 0.01, REAR_BRG_X[1] + 0.01, n=128))
    L.union(o, L.cyl_between("cone", (0, 0, REAR_BRG_X[1]), (0, 0, cone_x + 0.01), OUTER_REAR_R, n=128, r_end=OUTER_R))
    L.union(o, L.cyl_z("body", 0, 0, OUTER_R, cone_x, x1, n=128))
    L.cut(o, L.cyl_z("hub_bore", 0, 0, OUTER_HUB_BORE_R, x0 - 1, SEAT_CONE_X0 + 0.01, n=128))
    L.cut(o, L.cyl_between("seat_cone", (0, 0, SEAT_CONE_X0), (0, 0, REAR_BRG_X[0]), OUTER_HUB_BORE_R, n=128, r_end=BRG_SEAT_R))
    L.cut(o, L.cyl_z("rear_seat", 0, 0, BRG_SEAT_R, REAR_BRG_X[0] - 0.01, REAR_BRG_X[1], n=96))
    L.cut(o, L.cyl_z("lip", 0, 0, LIP_R, x0 - 1, x1 + 1, n=96))
    L.cut(o, L.cyl_z("front_seat", 0, 0, BRG_SEAT_R, FRONT_BRG_X[0], x1 + 1, n=96))
    for a in BOLT_ANGLES:
        L.cut(o, L.cyl_z("bolt", *polar(BOLT_R, a), 1.7, x0 - 1, x0 + OUTER_FLANGE_T + 1, n=32))
    L.finish(o)
    PRINT_POSE["forearm-outer-tube"] = Matrix.Translation((0, 0, -x0))
    return o

def check_outer_tube():
    o = PARTS["forearm-outer-tube"]
    assert L.stats(o)["non_manifold"] == 0
    assert abs(L.hole_diameter(o, 0, 0, sum(REAR_BRG_X) / 2) - 2 * BRG_SEAT_R) < 0.05, "rear 6701 seat"
    assert abs(L.hole_diameter(o, 0, 0, sum(FRONT_BRG_X) / 2) - 2 * BRG_SEAT_R) < 0.05, "front 6701 seat"
    assert abs(L.hole_diameter(o, 0, 0, 150.0) - 2 * LIP_R) < 0.05, "middle bore = lips"
    assert LIP_R - TUBE_R >= 1.5, "tube rubs the middle bore"
    assert abs(L.hole_diameter(o, 0, 0, HUB_X[0] + 5) - 2 * OUTER_HUB_BORE_R) < 0.05, "bore round the turning hubs"
    assert OUTER_HUB_BORE_R - HUB_R >= 1.0 and OUTER_HUB_BORE_R - PLATE_R >= 1.0
    assert abs(L.hole_diameter(o, 0, 0, REAR_BRG_X[0] - 3.0) - 2 * (BRG_SEAT_R + 3.0)) < 0.1, "hub bore to rear seat must be a 45° cone, not a flat overhang"
    assert OUTER_R - BRG_SEAT_R >= 3.0, "front seat wall under 3"
    assert abs(L.stats(o)["dims"][2] - (OUTER_X[1] - OUTER_X[0])) < 0.01

COMPACT = os.path.join(ROOT, "model", "cycloid-poc", "20-1-compact")
BOLT_HEAD_R, BOLT_HEAD_H = 2.75, 3.0

def copy(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c); return c

def overlap(a, b):
    """Volume (mm³) a and b share, worked out on copies."""
    ca, cb = copy(a, "ov_a"), copy(b, "ov_b")
    L.boolean(ca, cb, 'INTERSECT')
    bm = bmesh.new(); bm.from_mesh(ca.data); bm.transform(ca.matrix_world); v = abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(ca); return v

def compact_front_housing():
    """housing-front.stl back in the assembly frame: it was exported flipped about x (PRINT_FLIP in cycloid_poc.py)."""
    bpy.ops.wm.stl_import(filepath=os.path.join(COMPACT, "housing-front.stl"))
    h = bpy.context.selected_objects[0]; h.name = "compact housing-front"
    h.data.transform(Matrix.Diagonal((1, -1, -1, 1)))
    zs = [v.co.z for v in h.data.vertices]
    assert abs(min(zs) - HOUSING_L / 2) < 0.01 and abs(max(zs) - HOUSING_L) < 0.01, (min(zs), max(zs))
    for a in BOLT_ANGLES:
        L.union(h, L.cyl_z("bolt head", *polar(BOLT_R, a), BOLT_HEAD_R, HOUSING_L - 0.01, HOUSING_L + BOLT_HEAD_H, n=32))
    return h

def inner_ring_land(name, x_face, direction):
    """Ring standing LAND_T off a hub face towards its 6701, so the hub bears on the inner ring only."""
    x0, x1 = sorted((x_face - 0.01 * direction, x_face + LAND_T * direction))
    land = L.cyl_z(name, 0, 0, LAND_R1, x0, x1, n=96)
    L.cut(land, L.cyl_z("land_bore", 0, 0, LAND_R0, x0 - 1, x1 + 1, n=96))
    return land

def output_plate():
    """On the compact's output hub. Screws go in first; the tube hub then slides over the dogs."""
    p = L.cyl_z("ax4-output-plate", 0, 0, PLATE_R, *PLATE_X, n=128)
    for a in DOG_ANGLES:
        L.union(p, L.cyl_z("dog", *polar(DOG_PCD_R, a), DOG_R, PLATE_X[1] - 0.01, PLATE_X[1] + DOG_H, n=48))
    for a in INSERT_ANGLES:
        L.cut(p, L.cyl_z("screw", *polar(INSERT_PCD_R, a), 1.7, PLATE_X[0] - 1, PLATE_X[1] + 1, n=32))
        L.cut(p, L.cyl_z("head", *polar(INSERT_PCD_R, a), 3.0, PLATE_X[1] - 3.2, PLATE_X[1] + 1, n=48))
    L.finish(p)
    PRINT_POSE["ax4-output-plate"] = Matrix.Translation((0, 0, -PLATE_X[0]))
    return p

def tube_hub():
    """Glued on the tube's rear end; the dogs drive it and its front land pushes the rear 6701's inner ring."""
    h = L.cyl_z("ax4-tube-hub", 0, 0, HUB_R, HUB_X[0], HUB_CHAMFER_X0 + 0.01, n=128)
    L.union(h, L.cyl_between("chamfer", (0, 0, HUB_CHAMFER_X0), (0, 0, HUB_X[1] - 0.01), HUB_R, n=128,
                             r_end=HUB_R - (HUB_X[1] - HUB_CHAMFER_X0)))
    L.union(h, inner_ring_land("land", HUB_X[1], 1))
    for a in DOG_ANGLES:
        L.cut(h, L.cyl_z("dog_hole", *polar(DOG_PCD_R, a), DOG_R + 0.25, HUB_X[0] - 1, HUB_X[0] + DOG_H + 0.5, n=48))
    L.cut(h, L.cyl_z("socket", 0, 0, TUBE_R, HUB_X[1] - SOCKET_DEPTH, HUB_X[1] + 1, n=96))
    L.finish(h)
    PRINT_POSE["ax4-tube-hub"] = Matrix.Translation((0, 0, -HUB_X[0]))
    return h

def check_coupling():
    p, h = PARTS["ax4-output-plate"], PARTS["ax4-tube-hub"]
    for o in (p, h):
        assert L.stats(o)["non_manifold"] == 0
    assert abs(L.hole_diameter(h, 0, 0, HUB_X[1] - SOCKET_DEPTH / 2) - 2 * TUBE_R) < 0.03, "Ø11.0 socket"
    assert L.bore_floor_z(h, 0, 0, HUB_X[1] + 1) is not None, "socket has a floor"
    for a in INSERT_ANGLES:
        x, y = polar(INSERT_PCD_R + 2.3, a)  # inside the counterbore, outside the clearance hole
        assert abs(L.bore_floor_z(p, x, y, PLATE_X[1] + 10) - (PLATE_X[1] - 3.2)) < 0.05, "counterbore not open to the front"
        assert min(math.dist(polar(INSERT_PCD_R, a), polar(DOG_PCD_R, d)) for d in DOG_ANGLES) - 3.0 - DOG_R >= 1.0, "dog over a screw head"
    assert DOG_PCD_R + DOG_R <= PLATE_R - 1.0 and DOG_PCD_R - DOG_R - 0.25 - TUBE_R >= 1.5, "dog hole breaks into the socket or the rim"
    assert PLATE_X[1] - PLATE_X[0] - 3.2 >= 1.8 - 1e-9, "too little plate under the screw heads"
    assert overlap(p, p) > 100, "overlap() can't see a clash"
    housing, outer = compact_front_housing(), PARTS["forearm-outer-tube"]
    bad = {k: round(v, 3) for k, v in {"plate/housing": overlap(p, housing), "hub/outer": overlap(h, outer),
                                       "plate/outer": overlap(p, outer), "plate/hub": overlap(p, h)}.items() if v > 0.05}
    assert not bad, bad
    bpy.data.objects.remove(housing)

def wrist_hub():
    """Glued on the tube's front end; its rear land pushes the front 6701's inner ring. The flange is the axis 5 fork's interface."""
    w = L.cyl_z("wrist-flange-hub", 0, 0, WRIST_R, *WRIST_X, n=128)
    L.union(w, inner_ring_land("land", WRIST_X[0], -1))
    L.cut(w, L.cyl_z("socket", 0, 0, TUBE_R, WRIST_X[0] - 1, WRIST_X[0] + SOCKET_DEPTH + TUBE_SPARE, n=96))
    for a in FLANGE_ANGLES:
        L.cut(w, L.cyl_z("insert", *polar(FLANGE_INSERT_R, a), 2.0, FLANGE_FACE - 5.0, FLANGE_FACE + 1, n=32))
    L.finish(w)
    PRINT_POSE["wrist-flange-hub"] = Matrix.Translation((0, 0, FLANGE_FACE)) @ Matrix.Diagonal((1, -1, -1, 1))   # flange face on the bed
    return w

def check_wrist_and_play():
    w = PARTS["wrist-flange-hub"]
    assert L.stats(w)["non_manifold"] == 0
    assert abs(L.hole_diameter(w, 0, 0, WRIST_X[0] + SOCKET_DEPTH / 2) - 2 * TUBE_R) < 0.03
    assert abs(L.hole_diameter(w, 0, 0, TUBE_X[1] + 0.75) - 2 * TUBE_R) < 0.03, "tube bottoms in the wrist hub: a hand-cut length would set the bearing play"
    for a in FLANGE_ANGLES:
        x, y = polar(FLANGE_INSERT_R, a)
        assert abs(L.bore_floor_z(w, x, y, FLANGE_FACE + 1) - (FLANGE_FACE - 5.0)) < 0.05, "flange insert depth"
    assert FLANGE_INSERT_R - 2.0 - TUBE_R >= 2.0 and WRIST_R - FLANGE_INSERT_R - 2.0 >= 1.5
    assert overlap(w, PARTS["forearm-outer-tube"]) < 0.05
    play_rear = REAR_BRG_X[0] - (HUB_X[1] + LAND_T)
    play_front = (WRIST_X[0] - LAND_T) - FRONT_BRG_X[1]
    assert 0.2 <= play_rear + play_front <= 0.5, "roll binds or rattles"
    assert LAND_R1 < LIP_R and LAND_R0 >= 6.0, "a land reaches the outer ring or misses the inner ring"
    assert TUBE_X[1] - TUBE_X[0] == TUBE_L

HOLLOW_MOUNT = os.path.join(ROOT, "model", "cycloid-poc", "20-1-hollow", "motor-mount.stl")
MOTOR4_X = round(C.belt_centre_distance(20, AX4_TEETH, AX4_BELT), 2)
SLOT, NEMA_HOLE_OFF, NEMA_HOLE_R, NEMA_PILOT_R = C.MOTOR_SLOT, 15.5, 1.7, 11.75   # cycloid_poc's motor mount
RAIL_GAP, RAIL_W, RAIL_H, MOUNT_T = 42.7, 3.0, 5.0, 6.0
MOUNT_HALF_W = RAIL_GAP / 2 + RAIL_W
ARM_CUT_X = 40.0                                 # past the disc's bolts and post holes

def slot(name, x, y, r, half, z0, z1):
    s = L.cyl_z(name, x - half, y, r, z0, z1, n=32)
    L.union(s, L.cyl_z(name + "_b", x + half, y, r, z0, z1, n=32))
    L.union(s, L.box(name + "_m", x - half, x + half, y - r, y + r, z0, z1))
    return s

def ax4_motor_mount():
    """The 188 mount (20-1-hollow) with its arm rebuilt and re-slotted for axis 4's 20T/60T on a 234."""
    bpy.ops.wm.stl_import(filepath=HOLLOW_MOUNT)
    m = bpy.context.selected_objects[0]; m.name = "ax4-motor-mount-60T"
    x1 = MOTOR4_X + SLOT + MOUNT_HALF_W
    L.cut(m, L.box("old arm", ARM_CUT_X, 120.0, -MOUNT_HALF_W - 5, MOUNT_HALF_W + 5, -MOUNT_T - 5, RAIL_H + 5))
    L.union(m, L.box("arm", ARM_CUT_X - 1, x1, -MOUNT_HALF_W, MOUNT_HALF_W, -MOUNT_T, 0))
    for sv in (-1, 1):
        v0, v1 = sorted((sv * RAIL_GAP / 2, sv * MOUNT_HALF_W))
        L.union(m, L.box("rail", ARM_CUT_X - 1, x1, v0, v1, -0.01, RAIL_H))
    slots = slot("pilot", MOTOR4_X, 0, NEMA_PILOT_R, SLOT, -MOUNT_T - 1, 1)
    for su in (-1, 1):
        for sv in (-1, 1):
            L.union(slots, slot("nema", MOTOR4_X + su * NEMA_HOLE_OFF, sv * NEMA_HOLE_OFF, NEMA_HOLE_R, SLOT, -MOUNT_T - 1, 1))
    L.finish(m)
    L.cut(m, slots)   # one cut, as in wrist.py: cut one by one, the screw slots leave non-manifold edges
    PRINT_POSE["ax4-motor-mount-60T"] = Matrix()   # stored in the assembly frame, like the 188 mount it replaces
    return m

def ax4_housing():
    """The compact's housings in its assembly frame (z from the rear face, the mount on z < 0)."""
    bpy.ops.wm.stl_import(filepath=os.path.join(COMPACT, "housing-rear.stl"))
    h = bpy.context.selected_objects[0]
    bpy.ops.wm.stl_import(filepath=os.path.join(COMPACT, "housing-front.stl"))
    f = bpy.context.selected_objects[0]
    f.data.transform(Matrix.Diagonal((1, -1, -1, 1)))
    L.union(h, f)
    return h

def mount_ray_open(m, u, v):
    """True if a ray straight through the mount's arm at (u, v) meets nothing."""
    return L._tree(m)[0].ray_cast(Vector((u, v, -MOUNT_T - 1.0)), Vector((0, 0, 1)))[0] is None

def check_ax4_mount():
    m = PARTS["ax4-motor-mount-60T"]
    assert L.stats(m)["non_manifold"] == 0
    zs = [v.co.z for v in m.data.vertices]
    assert abs(min(zs) + MOUNT_T) < 0.01 and abs(max(zs) - RAIL_H) < 0.01, ("mount's z range moved", min(zs), max(zs))
    for u in (MOTOR4_X - SLOT, MOTOR4_X + SLOT):
        assert mount_ray_open(m, u, 0), ("pilot slot", u)
        for su in (-1, 1):
            for sv in (-1, 1):
                assert mount_ray_open(m, u + su * NEMA_HOLE_OFF, sv * NEMA_HOLE_OFF), ("motor screw slot", u, su, sv)
    old = C.belt_centre_distance(20, 40, 188)
    assert not mount_ray_open(m, old - NEMA_HOLE_OFF, NEMA_HOLE_OFF), "the 188's screw slot is still open"
    assert MOTOR4_X + SLOT + 42.3 / 2 <= max(v.co.x for v in m.data.vertices) + 1e-3, "motor runs off the rails' far end"
    housing = ax4_housing()
    bad = {}
    for u in (MOTOR4_X - SLOT, MOTOR4_X + SLOT):
        pan = L.box("pancake", u - 21.15, u + 21.15, -21.15, 21.15, 0.0, 23.0)
        for name, o in (("housing", housing), ("mount", m)):
            v = overlap(pan, o)
            if v > 0.05:
                bad[(name, u)] = round(v, 3)
        bpy.data.objects.remove(pan)
    assert not bad, bad
    bpy.data.objects.remove(housing)

bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["forearm-outer-tube"] = outer_tube()
PARTS["ax4-output-plate"] = output_plate()
PARTS["ax4-tube-hub"] = tube_hub()
PARTS["wrist-flange-hub"] = wrist_hub()
CHECKS.append(check_outer_tube)
CHECKS.append(check_coupling)
CHECKS.append(check_wrist_and_play)
PARTS["ax4-motor-mount-60T"] = ax4_motor_mount()
CHECKS.append(check_ax4_mount)

for check in CHECKS:
    check()
report = {n: L.stats(o) for n, o in PARTS.items()}
report["reach"] = {"flange_face_from_housing_rear": round(FLANGE_FACE, 2), "tube_x": [round(v, 2) for v in TUBE_X],
                   "bearing_play_total": round(REAR_BRG_X[0] - HUB_X[1] - LAND_T + WRIST_X[0] - LAND_T - FRONT_BRG_X[1], 2)}
print("FOREARM", json.dumps(report))
os.makedirs(OUT, exist_ok=True)
for n, o in PARTS.items():
    o.matrix_world = Matrix()
    o.data.transform(PRINT_POSE[n])
    L.export(o, os.path.join(OUT, n + ".stl"))
print("FOREARM DONE")
