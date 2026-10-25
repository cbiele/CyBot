"""Compact cycloid POC (docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md): 1:20 on 6804s.
Assembly frame: axis on z, z=0 the housing's rear face, input angle measured from +x; disk A (rear) on the
journal towards +x. Parts are built in the assembly frame, checked, posed at four input angles for
collisions, then exported in print orientation to model/cycloid-poc/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py"""
import bpy, bmesh, math, os, sys, json
import mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT = os.path.join(ROOT, "model", "cycloid-poc")
P = json.load(open(os.path.join(OUT, "params.json")))

LIP_T, BRG_W, SHOULDER_T, PLATE_T, GAP, DISK_T, COLLAR_T = 0.8, 7.0, 0.5, 4.0, 0.5, 6.0, 1.0
B625_W = 5.0
END_R, COLLAR_R = 3.8, 6.0                   # eccentric ends pass the 6800 bore at 1 mm offset, 0.2 to spare
ROD_R, ROD_FLAT = 2.5, 2.0                   # the steel rod; its flat is 0.5 deep. Walls count from the steel, not the bore's clearance
DOT_R, DOT_DEPTH, DOT_PCD_R = 1.0, 0.4, 12.0 # locator dots: one on disk A, two on disk B
Z_DISK0 = LIP_T + BRG_W + SHOULDER_T + PLATE_T + GAP
Z_MID = Z_DISK0 + DISK_T + COLLAR_T / 2
L_HOUSING = 2 * Z_MID
PARTS, CHECKS = {}, []

def prism(name, pts, z0, z1):
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z0)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)

def bore_diameter(o, x, y, z):
    """Median of 72 rays out from (x, y, z), half a step off the polygon's vertices (hand_lib.hole_diameter's
    rays land on vertices and some slip through)."""
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); ds = []
    for k in range(72):
        a = 2 * math.pi * (k + 0.5) / 72
        h = tree.ray_cast(Vector((x, y, z)), Vector((math.cos(a), math.sin(a), 0)))
        if h[0] is not None: ds.append((h[0] - Vector((x, y, z))).length)
    bm.free(); return round(2 * sorted(ds)[len(ds) // 2], 3)

def copy(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c); return c

def disk(name, phase, dots):
    d = prism(name, C.profile(720, phase), 0, DISK_T)
    L.cut(d, L.cyl_z("6800", 0, 0, P["seat_6800"] / 2, -1, DISK_T + 1, n=96))
    for k in range(C.N_OUT):
        a = 2 * math.pi * k / C.N_OUT
        L.cut(d, L.cyl_z("bushing", C.OUT_PCD_R * math.cos(a), C.OUT_PCD_R * math.sin(a), P["seat_bushing"] / 2, -1, DISK_T + 1, n=64))
    for j in range(dots):
        a = math.radians(30 + 10 * j)        # between two bushing seats
        L.cut(d, L.cyl_z("dot", DOT_PCD_R * math.cos(a), DOT_PCD_R * math.sin(a), DOT_R, DISK_T - DOT_DEPTH, DISK_T + 1, n=24))
    L.finish(d); return d

def eccentric():
    jr = P["journal_6800"] / 2
    za0, za1 = Z_DISK0, Z_DISK0 + DISK_T
    zb0, zb1 = za1 + COLLAR_T, za1 + COLLAR_T + DISK_T
    b = L.cyl_z("eccentric", 0, 0, END_R, Z_DISK0 - GAP, zb1 + GAP, n=96)
    L.union(b, L.cyl_z("journal_a", C.E, 0, jr, za0, za1, n=128))
    L.union(b, L.cyl_z("collar", 0, 0, COLLAR_R, za1 - 0.01, zb0 + 0.01, n=96))
    L.union(b, L.cyl_z("journal_b", -C.E, 0, jr, zb0, zb1, n=128))
    rod = L.cyl_z("rod", 0, 0, P["rod_bore"] / 2, -1, L_HOUSING + 1, n=64)
    L.cut(rod, L.box("flat", ROD_FLAT, 5, -5, 5, -2, L_HOUSING + 2))
    L.cut(b, rod); L.finish(b); return b

def check_disks():
    root = C.R - C.RP - C.CLEAR - C.E
    assert C.OUT_PCD_R - P["seat_bushing"] / 2 - P["seat_6800"] / 2 >= 1.5, "bushing seat too close to the 6800"
    assert root - C.OUT_PCD_R - P["seat_bushing"] / 2 >= 1.5, "bushing seat too close to the lobe root"
    assert 2 * C.OUT_PCD_R * math.sin(math.pi / C.N_OUT) - P["seat_bushing"] >= 1.5, "bushing seats too close"
    for name in ("disk-a", "disk-b"):
        o = PARTS[name]
        assert L.stats(o)["non_manifold"] == 0, name
        assert abs(bore_diameter(o, 0, 0, DISK_T / 2) - P["seat_6800"]) < 0.03, name

def check_eccentric():
    jr = P["journal_6800"] / 2
    assert END_R + C.E <= jr - 0.2, "a 6800 won't slide over the eccentric end"
    assert END_R - ROD_R >= 1.2, "eccentric end too thin round the rod"
    assert jr - C.E - ROD_R >= 1.5, "journal too thin round the rod"
    o = PARTS["eccentric"]
    assert L.stats(o)["non_manifold"] == 0
    za, zb = Z_DISK0 + DISK_T / 2, Z_MID + COLLAR_T / 2 + DISK_T / 2
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=za) - (C.E - jr)) < 0.05, "journal A not towards +x"
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=zb) - (-C.E - jr)) < 0.05, "journal B not towards -x"

bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["disk-a"] = disk("disk-a", 0.0, 1)
PARTS["disk-b"] = disk("disk-b", C.DISK_B_PHASE, 2)
PARTS["eccentric"] = eccentric()
CHECKS += [check_disks, check_eccentric]

LIP_R = 15.0                                 # holds each 6804's outer ring at the housing face
CARRIER_R, CARRIER_BORE_R = 22.0, 22.5
HOUSING_R, BOLT_R, BOLT_HOLE_R = 34.0, 30.0, 1.7
BOLT_ANGLES = [45 + 90 * k for k in range(4)]
SHOULDER_R = 11.5                            # bears on the 6804 inner ring only
HUB_PROUD = 1.0
ROD_CLEAR_R = 2.75
INSERT_R, INSERT_DEPTH, INSERT_PCD_R = 2.0, 3.5, 6.5   # M3 x 3 x 4.5 heat-set inserts for the test arm
INSERT_ANGLES = [90 + 120 * k for k in range(3)]
PIN_DEPTH = 3.0                              # output pin holes, blind from each plate's inner face
RING_PIN_L, OUT_PIN_L = 18.0, 20.0

def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

def mirror_to_front(o):
    """Reflect a part built on the rear side through the mid-plane."""
    o.matrix_world = Matrix.Translation((0, 0, 2 * Z_MID)) @ Matrix.Scale(-1, 4, (0, 0, 1))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()

def housing():
    rear_bores = [(-1, LIP_T, LIP_R), (LIP_T, LIP_T + BRG_W, P["seat_6804"] / 2),
                  (LIP_T + BRG_W, Z_DISK0, CARRIER_BORE_R), (Z_DISK0, Z_MID, C.DISK_ZONE_BORE_R)]
    h = L.cyl_z("housing", 0, 0, HOUSING_R, 0, L_HOUSING, n=160)
    for z0, z1, r in rear_bores + [(L_HOUSING - b, L_HOUSING - a, r) for a, b, r in rear_bores]:
        L.cut(h, L.cyl_z("bore", 0, 0, r, z0 - 0.01, z1 + 0.01, n=160))
    for a in BOLT_ANGLES:
        L.cut(h, L.cyl_z("bolt", *polar(BOLT_R, a), BOLT_HOLE_R, -1, L_HOUSING + 1, n=32))
    rear, front = copy(h, "housing-rear"), copy(h, "housing-front")
    bpy.data.objects.remove(h)
    L.cut(rear, L.box("split", -50, 50, -50, 50, Z_MID, L_HOUSING + 5))
    L.cut(front, L.box("split", -50, 50, -50, 50, -5, Z_MID))
    for k in range(C.N + 1):
        x, y = polar(C.R, 360 * k / (C.N + 1))
        L.cut(rear, L.cyl_z("pin", x, y, P["ring_pin_press"] / 2, Z_MID - RING_PIN_L / 2, Z_MID + 1, n=24))
        L.cut(front, L.cyl_z("pin", x, y, P["ring_pin_slip"] / 2, Z_MID - 1, Z_MID + RING_PIN_L / 2, n=24))
    L.finish(rear); L.finish(front); return rear, front

def carrier(front):
    """Built as the rear carrier; the output (front) carrier is mirrored and gets insert holes instead of a rod hole."""
    z_in = Z_DISK0 - GAP
    z_plate, z_hub_end = z_in - PLATE_T, -HUB_PROUD
    z_sh = z_plate - SHOULDER_T
    c = L.cyl_z("carrier-front" if front else "carrier-rear", 0, 0, CARRIER_R, z_plate, z_in, n=160)
    L.union(c, L.cyl_z("shoulder", 0, 0, SHOULDER_R, z_sh, z_plate + 0.01, n=120))
    L.union(c, L.cyl_z("hub", 0, 0, P["hub_6804"] / 2, z_hub_end, z_sh + 0.01, n=120))
    L.cut(c, L.cyl_z("625", 0, 0, P["seat_625"] / 2, z_in - B625_W, z_in + 1, n=96))
    for k in range(C.N_OUT):
        L.cut(c, L.cyl_z("pin", *polar(C.OUT_PCD_R, 360 * k / C.N_OUT), P["out_pin_press"] / 2, z_in - PIN_DEPTH, z_in + 1, n=32))
    if front:
        for a in INSERT_ANGLES:
            L.cut(c, L.cyl_z("insert", *polar(INSERT_PCD_R, a), INSERT_R, z_hub_end - 1, z_hub_end + INSERT_DEPTH, n=32))
    else:
        L.cut(c, L.cyl_z("rod", 0, 0, ROD_CLEAR_R, z_hub_end - 1, z_in - B625_W + 0.01, n=48))
    L.finish(c)
    if front:
        mirror_to_front(c)
    return c

def check_housing_and_carriers():
    z_in = Z_DISK0 - GAP
    assert CARRIER_BORE_R - CARRIER_R >= 0.5, "carrier rubs the housing"
    assert C.R - P["ring_pin_press"] / 2 - CARRIER_BORE_R >= 0.8, "ring pin hole breaks into the carrier bore"
    assert BOLT_R - BOLT_HOLE_R - (C.R + C.RP) >= 1.5, "bolt hole too close to the ring pins"
    assert HOUSING_R - BOLT_R - BOLT_HOLE_R >= 1.5, "bolt hole too close to the outside"
    assert Z_DISK0 - (Z_MID - RING_PIN_L / 2) >= 2.0, "ring pins engage less than 2 mm"
    assert abs(2 * (Z_MID - z_in) + 2 * PIN_DEPTH - OUT_PIN_L) < 1e-6, "output pins don't fill both plates' holes"
    assert P["ring_pin_slip"] - 2 * C.RP >= 0.1, "front half won't slide over the ring pins"
    assert P["hub_6804"] / 2 - P["seat_625"] / 2 >= 1.5, "carrier hub too thin round the 625"
    assert INSERT_PCD_R + INSERT_R <= P["hub_6804"] / 2 - 1.0, "insert breaks out of the hub"
    assert PIN_DEPTH <= PLATE_T - 1.0, "output pin holes break through the plate"
    for name in ("housing-rear", "housing-front", "carrier-rear", "carrier-front"):
        assert L.stats(PARTS[name])["non_manifold"] == 0, name
    rear = PARTS["housing-rear"]
    assert abs(bore_diameter(rear, 0, 0, LIP_T + BRG_W / 2) - P["seat_6804"]) < 0.03
    assert abs(bore_diameter(rear, 0, 0, LIP_T + BRG_W + 2) - 2 * CARRIER_BORE_R) < 0.05
    assert abs(bore_diameter(PARTS["carrier-rear"], 0, 0, z_in - B625_W / 2) - P["seat_625"]) < 0.03

PARTS["housing-rear"], PARTS["housing-front"] = housing()
PARTS["carrier-rear"] = carrier(False)
PARTS["carrier-front"] = carrier(True)
CHECKS.append(check_housing_and_carriers)

UPRIGHT_T, UPRIGHT_HALF_H, FOOT_T, FOOT_L = 5.0, 40.0, 6.0, 70.0
MOTOR_X = round(C.belt_centre_distance(20, 40, 232), 2)
SLOT = C.MOTOR_SLOT                          # motor travel each way along x, for belt tension
NEMA_HOLE_OFF, NEMA_HOLE_R, NEMA_PILOT_R = 15.5, 1.7, 11.75
HUB_CLEAR_R = 12.0
CLAMP_R = 3.25
ARM_L, ARM_W, ARM_T = 150.0, 20.0, 6.0
WEIGHT_X = (50.0, 100.0, 140.0)              # 1.7 N·m is about 1.25 kg on the 140 hole
THETAS = (0.0, 0.9, 2.3, 4.0)
PRINT_FLIP = {"housing-front", "carrier-rear"}

def slot(name, x, y, r, half, z0, z1):
    s = L.cyl_z(name, x - half, y, r, z0, z1, n=32)
    L.union(s, L.cyl_z(name + "_b", x + half, y, r, z0, z1, n=32))
    L.union(s, L.box(name + "_m", x - half, x + half, y - r, y + r, z0, z1))
    return s

def upright():
    u = L.box("bench-upright", -40, MOTOR_X + 30, -UPRIGHT_HALF_H, UPRIGHT_HALF_H, -UPRIGHT_T, 0)
    L.union(u, L.box("foot", -40, MOTOR_X + 30, -UPRIGHT_HALF_H - FOOT_T, -UPRIGHT_HALF_H + 0.01, -UPRIGHT_T, FOOT_L))
    L.cut(u, L.cyl_z("hub", 0, 0, HUB_CLEAR_R, -UPRIGHT_T - 1, 1, n=96))
    for a in BOLT_ANGLES:
        L.cut(u, L.cyl_z("bolt", *polar(BOLT_R, a), BOLT_HOLE_R, -UPRIGHT_T - 1, 1, n=32))
    L.cut(u, slot("pilot", MOTOR_X, 0, NEMA_PILOT_R, SLOT, -UPRIGHT_T - 1, 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.cut(u, slot("nema", MOTOR_X + sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, NEMA_HOLE_R, SLOT, -UPRIGHT_T - 1, 1))
    for x in (0.0, MOTOR_X):
        y0 = -UPRIGHT_HALF_H - FOOT_T - 1
        L.cut(u, L.cyl_between("clamp", (x, y0, FOOT_L - 20), (x, -UPRIGHT_HALF_H + 1, FOOT_L - 20), CLAMP_R, n=32))
    L.finish(u); return u

def test_arm():
    z0 = L_HOUSING + HUB_PROUD
    a = L.box("test-arm", -15, ARM_L, -ARM_W / 2, ARM_W / 2, z0, z0 + ARM_T)
    for ang in INSERT_ANGLES:
        L.cut(a, L.cyl_z("screw", *polar(INSERT_PCD_R, ang), 1.7, z0 - 1, z0 + ARM_T + 1, n=32))
    for x in WEIGHT_X:
        L.cut(a, L.cyl_z("weight", x, 0, 2.8, z0 - 1, z0 + ARM_T + 1, n=32))
    L.finish(a); return a

def pose(theta):
    """Place the moving parts at input angle theta (rad); disks are built at z 0..DISK_T."""
    out = Matrix.Rotation(-theta / C.N, 4, 'Z')
    PARTS["disk-a"].matrix_world = Matrix.Translation((C.E * math.cos(theta), C.E * math.sin(theta), Z_DISK0)) @ out
    PARTS["disk-b"].matrix_world = Matrix.Translation((-C.E * math.cos(theta), -C.E * math.sin(theta), Z_DISK0 + DISK_T + COLLAR_T)) @ out
    PARTS["eccentric"].matrix_world = Matrix.Rotation(theta, 4, 'Z')
    for n in ("carrier-rear", "carrier-front", "test-arm"):
        PARTS[n].matrix_world = out

def overlap(a, b):
    """Volume (mm³) a and b share, worked out on copies."""
    ca, cb = copy(a, "ov_a"), copy(b, "ov_b")
    ca.matrix_world, cb.matrix_world = a.matrix_world.copy(), b.matrix_world.copy()
    L.boolean(ca, cb, 'INTERSECT')
    bm = bmesh.new(); bm.from_mesh(ca.data); bm.transform(ca.matrix_world); v = abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(ca); return v

PAIRS = [("disk-a", "housing-rear"), ("disk-a", "housing-front"), ("disk-b", "housing-rear"), ("disk-b", "housing-front"),
         ("disk-a", "disk-b"), ("disk-a", "carrier-rear"), ("disk-b", "carrier-front"), ("disk-a", "eccentric"), ("disk-b", "eccentric"),
         ("eccentric", "carrier-rear"), ("eccentric", "carrier-front"), ("carrier-rear", "housing-rear"),
         ("carrier-front", "housing-front"), ("test-arm", "housing-front"), ("bench-upright", "housing-rear")]

def check_assembly():
    worst = {}
    for th in THETAS:
        pose(th)
        for a, b in PAIRS:
            worst[(a, b)] = max(worst.get((a, b), 0.0), overlap(PARTS[a], PARTS[b]))
    pose(0.0)
    bad = {f"{a}/{b}": round(v, 3) for (a, b), v in worst.items() if v > 0.05}
    assert not bad, bad
    assert MOTOR_X - SLOT - 21.2 > HOUSING_R + 2, "motor body (42.3 square) hits the housing"

PARTS["bench-upright"] = upright()
PARTS["test-arm"] = test_arm()
CHECKS.append(check_assembly)

for check in CHECKS:
    check()
print("POC", json.dumps({n: L.stats(o) for n, o in PARTS.items()}))
for n, o in PARTS.items():
    o.matrix_world = Matrix.Rotation(math.pi, 4, 'X') if n in PRINT_FLIP else Matrix()
    L.export(o, os.path.join(OUT, n + ".stl"))
print("POC DONE")
