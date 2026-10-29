"""Compact cycloid POC (docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md): 1:20 on 6804s.
Assembly frame: axis on z, z=0 the housing's rear face, input angle measured from +x; disk A (rear) on the
journal towards +x. Parts are built in the assembly frame, checked, posed at four input angles for
collisions, then exported in print orientation to model/cycloid-poc/20-1-compact/ (20-1-hollow/ with --hollow),
the bench and test arm to test-parts/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py"""
import bpy, bmesh, math, os, sys, json
import mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
BASE = os.path.join(ROOT, "model", "cycloid-poc")
P = json.load(open(os.path.join(BASE, "params.json")))

LIP_T, BRG_W, SHOULDER_T, PLATE_T, GAP, DISK_T, COLLAR_T = 0.8, 7.0, 0.5, 4.0, 0.5, 6.0, 1.0
B625_W = 5.0
END_R, COLLAR_R = 3.8, 5.2                   # ends pass the 6800 bore at the offset with 0.2 to spare; the collar stays inside its inner ring
ECC_FLOAT = 0.3                              # axial play between the 625 inner rings
ROD_R, ROD_FLAT = 2.5, 2.0                   # the steel rod; its flat is 0.5 deep. Walls count from the steel, not the bore's clearance
DOT_R, DOT_DEPTH, DOT_PCD_R = 1.0, 0.4, 12.0 # locator dots: one on disk A, two on disk B
HOLLOW = "--hollow" in sys.argv              # axis 6: eccentric as a hollow sleeve on 688s, the gripper rod through it
SLEEVE_R, SLEEVE_BORE_R = 3.975, 2.65        # 688 bore less 0.05; the Ø5 gripper rod plus 0.15 each side
SLEEVE_FLAT = 3.675                          # double-D for the 40T, 0.3 deep each side
MOUNT_T, PULLEY_GAP, PULLEY_H = 6.0, 1.0, 16.5   # motor mount plate; 40T free flange to the plate; 40T height (gt2_pulley.py)
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

def eccentric(name="eccentric", rod_flat=True):
    jr = P["journal_6800"] / 2
    za0, za1 = Z_DISK0, Z_DISK0 + DISK_T
    zb0, zb1 = za1 + COLLAR_T, za1 + COLLAR_T + DISK_T
    if HOLLOW:
        z_tail, z_nose = sleeve_ends()
        b = L.cyl_z("eccentric", 0, 0, SLEEVE_R, z_tail, z_nose, n=96)
    else:
        b = L.cyl_z(name, 0, 0, END_R, Z_DISK0 - GAP + ECC_FLOAT / 2, zb1 + GAP - ECC_FLOAT / 2, n=96)
    L.union(b, L.cyl_z("journal_a", C.E, 0, jr, za0, za1, n=128))
    L.union(b, L.cyl_z("collar", 0, 0, COLLAR_R, za1 - 0.01, zb0 + 0.01, n=96))
    L.union(b, L.cyl_z("journal_b", -C.E, 0, jr, zb0, zb1, n=128))
    if HOLLOW:
        L.cut(b, L.cyl_z("bore", 0, 0, SLEEVE_BORE_R, z_tail - 1, z_nose + 1, n=64))
        for x0, x1 in ((SLEEVE_FLAT, 5), (-5, -SLEEVE_FLAT)):
            L.cut(b, L.box("flat", x0, x1, -5, 5, z_tail - 1, -MOUNT_T - PULLEY_GAP + 0.5))
    else:
        rod = L.cyl_z("rod", 0, 0, P["rod_bore"] / 2, -1, L_HOUSING + 1, n=64)
        if rod_flat:
            L.cut(rod, L.box("flat", ROD_FLAT, 5, -5, 5, -2, L_HOUSING + 2))
        L.cut(b, rod)
    L.finish(b); return b

def sleeve_ends():
    """Tail flush with the 40T's hub top behind the mount; nose 0.2 short of the front 688's outer face."""
    return -(MOUNT_T + PULLEY_GAP + PULLEY_H), 2 * Z_MID - (Z_DISK0 - GAP) + B625_W - 0.2

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
    end_r, core_r = (SLEEVE_R, SLEEVE_BORE_R) if HOLLOW else (END_R, ROD_R)
    assert end_r + C.E <= jr - 0.2, "a 6800 won't slide over the eccentric end"
    assert end_r - core_r >= 1.2, "eccentric end too thin round the rod"
    assert jr - C.E - core_r >= 1.5, "journal too thin round the rod"
    if HOLLOW:
        assert SLEEVE_FLAT - SLEEVE_BORE_R >= 1.0, "sleeve too thin under the 40T flats"
    o = PARTS["eccentric"]
    assert L.stats(o)["non_manifold"] == 0
    za, zb = Z_DISK0 + DISK_T / 2, Z_MID + COLLAR_T / 2 + DISK_T / 2
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=za) - (C.E - jr)) < 0.05, "journal A not towards +x"
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=zb) - (-C.E - jr)) < 0.05, "journal B not towards -x"

bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["disk-a"] = disk("disk-a", 0.0, 1)
PARTS["disk-b"] = disk("disk-b", C.DISK_B_PHASE, 2)
PARTS["eccentric"] = eccentric()
if not HOLLOW:
    PARTS["eccentric-round"] = eccentric("eccentric-round", rod_flat=False)   # pressed onto a plain rod with no flat
CHECKS += [check_disks, check_eccentric]

LIP_R = 15.0                                 # holds each 6804's outer ring at the housing face
CARRIER_R, CARRIER_BORE_R = 22.0, 22.5
HOUSING_R, BOLT_R, BOLT_HOLE_R = 34.0, 30.0, 1.7
BOLT_ANGLES = [45 + 90 * k for k in range(4)]
SHOULDER_R = 11.5                            # bears on the 6804 inner ring only
HUB_PROUD = 1.0
ROD_CLEAR_R = 2.75
SLEEVE_CLEAR, GRIP_ROD_CLEAR_R = 0.5, 2.8    # rear hub round the turning sleeve; front hub round the gripper rod
INSERT_R, INSERT_DEPTH, INSERT_PCD_R = 2.0, 3.5, 6.5   # M3 x 3 x 4.5 heat-set inserts for the test arm
INSERT_ANGLES = [90 + 120 * k for k in range(3)]
RELIEF_R, RELIEF_T = 5.5, 0.4                # 625 seat floor relieved under the inner ring, so only the outer ring seats
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
    L.cut(c, L.cyl_z("625_relief", 0, 0, RELIEF_R, z_in - B625_W - RELIEF_T, z_in - B625_W + 0.01, n=64))
    for k in range(C.N_OUT):
        L.cut(c, L.cyl_z("pin", *polar(C.OUT_PCD_R, 360 * k / C.N_OUT), P["out_pin_press"] / 2, z_plate - 1, z_in + 1, n=32))
    if front:
        for a in INSERT_ANGLES:
            L.cut(c, L.cyl_z("insert", *polar(INSERT_PCD_R, a), INSERT_R, z_hub_end - 1, z_hub_end + INSERT_DEPTH, n=32))
        if HOLLOW:
            L.cut(c, L.cyl_z("grip_rod", 0, 0, GRIP_ROD_CLEAR_R, z_hub_end - 1, z_in - B625_W + 0.01, n=48))
    else:
        rod_r = SLEEVE_R + SLEEVE_CLEAR if HOLLOW else ROD_CLEAR_R
        L.cut(c, L.cyl_z("rod", 0, 0, rod_r, z_hub_end - 1, z_in - B625_W + 0.01, n=48))
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
    assert 2.5 <= (OUT_PIN_L - 2 * (Z_MID - z_in)) / 2 <= PLATE_T, "output pins engage each plate 2.5 mm to the full plate"
    assert P["ring_pin_slip"] - 2 * C.RP >= 0.1, "front half won't slide over the ring pins"
    assert P["hub_6804"] / 2 - P["seat_625"] / 2 >= 1.5, "carrier hub too thin round the 625"
    assert INSERT_PCD_R + INSERT_R <= P["hub_6804"] / 2 - 1.0, "insert breaks out of the hub"
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
ARM_BOSS_R, ARM_BOSS_T = 9.0, 4.0            # lifts the arm over the bolt heads on the front face
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

NEMA_SQUARE = 42.3
RAIL_GAP, RAIL_W, RAIL_H = 42.7, 3.0, 5.0   # motor rails on the motor face, 0.2 a side; the motor slides between them for tension
RAIL_X0 = HOUSING_R + 2.0
MOUNT_HALF_W = RAIL_GAP / 2 + RAIL_W
CB_R, CB_DEPTH = 3.0, 3.2                    # M3 socket heads sunk in the housing face, under the housing
MOTOR_SHAFT_L = 20.0                         # shortest NEMA 17 shaft we fit (pancake), from the face
POST_R, POST_RAD, POST_ANGLES = 26.0, 4.5, (90, 180, 270)   # MOTOR7 bracket's posts, on the side away from the belt
POST_INSERT_DEPTH = 5.0
COUPLER_L, COUPLER_R = 25.0, 9.5             # 5 to 5 mm flexible coupler, about Ø19 x 25; check when it arrives
BRACKET_T, ROD_L = 5.0, 100.0

def bracket_z():
    """Coupler 1.5 behind the sleeve tail, bracket 1 behind the coupler; motor face on the bracket's rear."""
    z_coupler1 = sleeve_ends()[0] - 1.5
    z_front = z_coupler1 - COUPLER_L - 1.0
    return z_front - BRACKET_T, z_front, z_coupler1

def grip_rod_z():
    """Rod butts 1 past the MOTOR7 shaft tip inside the coupler."""
    z0 = bracket_z()[0] + MOTOR_SHAFT_L + 1.0
    return z0, z0 + ROD_L

def motor7_bracket():
    """Disc for MOTOR7 with three posts up to the mount's belt face; prints disc down. Screws come through the
    mount from its housing face into inserts in the post tips, so it goes on before the mount meets the housing."""
    z0, z1, _ = bracket_z()
    b = L.cyl_z("motor7-bracket", 0, 0, POST_R + POST_RAD, z0, z1, n=160)
    for a in POST_ANGLES:
        L.union(b, L.cyl_z("post", *polar(POST_R, a), POST_RAD, z1 - 0.01, -MOUNT_T, n=48))
        L.cut(b, L.cyl_z("insert", *polar(POST_R, a), INSERT_R, -MOUNT_T - POST_INSERT_DEPTH, -MOUNT_T + 1, n=32))
    L.cut(b, L.cyl_z("pilot", 0, 0, NEMA_PILOT_R, z0 - 1, z1 + 1, n=96))
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.cut(b, L.cyl_z("nema", sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, NEMA_HOLE_R, z0 - 1, z1 + 1, n=32))
    L.finish(b); return b

def motor_mount():
    """Head version of the upright: on the housing's rear face, motor face on the housing side so its body runs
    forward beside the housing, shaft back through the plate to the belt plane behind it."""
    x1 = MOTOR_X + SLOT + MOUNT_HALF_W
    m = L.cyl_z("motor-mount", 0, 0, HOUSING_R, -MOUNT_T, 0, n=160)
    L.union(m, L.box("arm", 10.0, x1, -MOUNT_HALF_W, MOUNT_HALF_W, -MOUNT_T, 0))   # starts inside the disc, clear of the post screws
    for sy in (-1, 1):
        y0, y1 = sorted((sy * RAIL_GAP / 2, sy * MOUNT_HALF_W))
        L.union(m, L.box("rail", RAIL_X0, x1, y0, y1, -0.01, RAIL_H))
    L.cut(m, L.cyl_z("hub", 0, 0, HUB_CLEAR_R, -MOUNT_T - 1, 1, n=96))
    for a in BOLT_ANGLES:
        L.cut(m, L.cyl_z("bolt", *polar(BOLT_R, a), BOLT_HOLE_R, -MOUNT_T - 1, 1, n=32))
    L.cut(m, slot("pilot", MOTOR_X, 0, NEMA_PILOT_R, SLOT, -MOUNT_T - 1, 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.cut(m, slot("nema", MOTOR_X + sx * NEMA_HOLE_OFF, sy * NEMA_HOLE_OFF, NEMA_HOLE_R, SLOT, -MOUNT_T - 1, 1))
    if HOLLOW:
        for a in POST_ANGLES:
            L.cut(m, L.cyl_z("post_screw", *polar(POST_R, a), BOLT_HOLE_R, -MOUNT_T - 1, 1, n=32))
            L.cut(m, L.cyl_z("post_head", *polar(POST_R, a), CB_R, -CB_DEPTH, 1, n=32))
    L.finish(m); return m

def belt_plane_from_motor_face():
    return MOUNT_T + PULLEY_GAP + C.GT2_FLANGE_T + C.GT2_TEETH_W / 2

def check_motor_mount():
    m = PARTS["motor-mount"]
    assert L.stats(m)["non_manifold"] == 0
    assert HUB_CLEAR_R - P["hub_6804"] / 2 >= 1.5, "mount rubs the rear carrier's hub"
    assert RAIL_X0 - HOUSING_R >= 1.5, "rails hit the housing"
    assert 0.2 <= RAIL_GAP - NEMA_SQUARE <= 0.6, "rails don't hold the motor snugly"
    assert MOTOR_X - SLOT - NEMA_SQUARE / 2 >= RAIL_X0, "motor runs off the rails' housing end"
    assert MOTOR_X + SLOT + MOUNT_HALF_W >= MOTOR_X + SLOT + NEMA_SQUARE / 2, "motor runs off the rails' far end"
    assert belt_plane_from_motor_face() + C.GT2_TEETH_W / 2 <= MOTOR_SHAFT_L - 2.0, "20T can't reach the belt plane"
    if not HOLLOW:
        assert abs(L.stats(m)["dims"][2] - (MOUNT_T + RAIL_H)) < 0.01
        return
    assert MOUNT_T - CB_DEPTH >= 2.5, "too little plate under the post screw heads"
    z0, z_front, z_coupler1 = bracket_z()
    flange_r = 40 / math.pi - 0.254 + 1.0
    bolt_heads = [polar(BOLT_R, b) for b in BOLT_ANGLES]
    for a in POST_ANGLES:
        x, y = polar(POST_R, a)
        assert min(math.hypot(x - bx, y - by) for bx, by in bolt_heads) >= POST_RAD + 2.75 + 1.0, "post hits a housing bolt head"
        assert abs(y) - POST_RAD >= flange_r + 2.0 or x < -(flange_r + POST_RAD + 2.0), "post in the belt or the 40T"
    assert POST_R - POST_RAD - COUPLER_R >= 2.0, "coupler rubs a post"
    assert z_coupler1 < sleeve_ends()[0] - 1.0, "coupler rubs the sleeve tail"
    r0, r1 = grip_rod_z()
    assert r0 > z0 + MOTOR_SHAFT_L and z_coupler1 - r0 >= 8.0, "rod meets the motor shaft or grips less than 8 of the coupler"
    assert r1 - (L_HOUSING + HUB_PROUD) >= 20.0, "rod stands less than 20 past the output face"
    assert INSERT_PCD_R - INSERT_R - GRIP_ROD_CLEAR_R >= 1.0, "output insert breaks into the rod hole"
    b = PARTS["motor7-bracket"]
    assert L.stats(b)["non_manifold"] == 0
    assert abs(L.stats(b)["dims"][2] - (-MOUNT_T - z0)) < 0.01, "posts don't reach the mount's belt face"

def test_arm():
    z0 = L_HOUSING + HUB_PROUD; z1 = z0 + ARM_BOSS_T + ARM_T
    a = L.box("test-arm", -15, ARM_L, -ARM_W / 2, ARM_W / 2, z0 + ARM_BOSS_T, z1)
    L.union(a, L.cyl_z("boss", 0, 0, ARM_BOSS_R, z0, z0 + ARM_BOSS_T + 0.01, n=96))
    for ang in INSERT_ANGLES:
        L.cut(a, L.cyl_z("screw", *polar(INSERT_PCD_R, ang), 1.7, z0 - 1, z1 + 1, n=32))
    for x in WEIGHT_X:
        L.cut(a, L.cyl_z("weight", x, 0, 2.8, z0 - 1, z1 + 1, n=32))
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
         ("carrier-front", "housing-front"), ("test-arm", "housing-front"), ("bench-upright", "housing-rear"),
         ("motor-mount", "housing-rear"), ("motor-mount", "carrier-rear"), ("motor-mount", "eccentric")]
if HOLLOW:
    PAIRS += [("motor7-bracket", "motor-mount"), ("motor7-bracket", "eccentric")]

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
PARTS["motor-mount"] = motor_mount()
if HOLLOW:
    PARTS["motor7-bracket"] = motor7_bracket()
CHECKS.append(check_motor_mount)
PARTS["test-arm"] = test_arm()
CHECKS.append(check_assembly)

BOLT_HEAD_H = 3.0                            # M3 socket head on the front face
SEAL_R = 6.2                                 # 6800 inner ring land; past it a part rubs the seal

def floor_z(o, x, z_start, up=False):
    tree, bm = L._tree(o)
    h = tree.ray_cast(Vector((x, 0, z_start)), Vector((0, 0, 1 if up else -1)))[0]; bm.free()
    return h.z if h is not None else None

def check_running_clearances():
    z_in = Z_DISK0 - GAP
    rear, front = PARTS["carrier-rear"], PARTS["carrier-front"]
    x_inner = 5.0 if HOLLOW else 4                 # under the inner ring: 688 from 4 out, 625 from 2.5
    arm_low = min(v.co.z for v in PARTS["test-arm"].data.vertices if math.hypot(v.co.x, v.co.y) >= BOLT_R - 3)
    fails = {
        "test arm hits the bolt heads": arm_low - (L_HOUSING + BOLT_HEAD_H) < 1.5,
        "rear 625 floor touches the inner ring": floor_z(rear, 7, z_in - 0.1) - floor_z(rear, x_inner, z_in - 0.1) < 0.3,
        "front 625 floor touches the inner ring": floor_z(front, x_inner, 2 * Z_MID - z_in + 0.1, up=True) - floor_z(front, 7, 2 * Z_MID - z_in + 0.1, up=True) < 0.3,
        "eccentric clamps the 625 inner rings": not HOLLOW and L.stats(PARTS["eccentric"])["dims"][2] > 2 * (Z_MID - z_in) - 0.3,
        "output pins bottom in the carrier": floor_z(rear, C.OUT_PCD_R, z_in - 0.1) is not None,
        "collar rubs the 6800 seal": COLLAR_R + C.E > SEAL_R,
    }
    bad = [k for k, v in fails.items() if v]
    assert not bad, bad

CHECKS.append(check_running_clearances)

for check in CHECKS:
    check()
print("BELT PLANE from motor face", belt_plane_from_motor_face(), "mm; motor at", MOTOR_X)
print("POC", json.dumps({n: L.stats(o) for n, o in PARTS.items()}))
TEST_PARTS = {"bench-upright", "test-arm"}
if HOLLOW:
    print("GRIP ROD z", grip_rod_z(), "bracket z", bracket_z())
for n, o in PARTS.items():
    if HOLLOW and n in TEST_PARTS:
        continue
    folder = "test-parts" if n in TEST_PARTS else "20-1-hollow" if HOLLOW else "20-1-compact"
    o.matrix_world = Matrix.Rotation(math.pi, 4, 'X') if n in PRINT_FLIP else Matrix()
    L.export(o, os.path.join(BASE, folder, n + ".stl"))
print("POC DONE")
