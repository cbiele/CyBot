"""Standalone spider base for axis 1 (spec docs/superpowers/specs/2026-09-23-axis1-spider-base-design.md).
Frame: base axis on z, ground at z=0, ring top (the mounting plane) at z=RING_H. Arms are generated
along +x with the ring facet at x=FACET_X; the assembly render turns copies to 0/90/180/270 deg.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/spider_base.py
Writes model/base/spider-*.stl and renders; SPIDER_OUT overrides the output folder."""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
from mathutils import Vector, Matrix
import mathutils
OUT = os.environ.get("SPIDER_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "base"))
os.makedirs(OUT, exist_ok=True)
CULTS = "/Users/claytonbiele/dev/Claude/Projects/cybot/Cults3d_v5/2-axis1"

# ---- ring
RING_R, RING_H, RING_PLATE_T, WALL, CENTRE_R = 100.0, 35.0, 4.0, 3.0, 25.0
HOLE_R, HOLE_D = 70.6, 5.5                                   # Cults base holder pattern, measured from its STL
HOLE_ANGLES = [11.3, 33.7, 101.3, 123.7, 191.3, 213.7, 281.3, 303.7]
NUT_AF, NUT_H, NUT_BOSS_D = 8.4, 4.5, 14.0                   # M5 nut, pocket open downward under the top plate
RIB_ANGLES = [22.5 + 45 * k for k in range(8)]
ARM_ANGLES = [0, 90, 180, 270]; MOTOR_ARM_ANGLE = 180
FACET_W = 60.0; FACET_X = math.sqrt(RING_R ** 2 - (FACET_W / 2) ** 2)   # 95.39: a 60 mm flat on the Ø200 wall
BOSS_D, BACK_T = 18.0, 4.0                                   # boss depth; the mortise is blind, leaving a back wall the bolts pass through
MORTISE_W, MORTISE_Z0, MORTISE_Z1, FIT = 40.0, 4.0, RING_H - RING_PLATE_T, 0.3
MORTISE_DEPTH = BOSS_D - BACK_T
JOINT_BOLT_Y, JOINT_BOLT_Z, JOINT_BOLT_D = 14.0, 17.5, 5.5   # inboard of the mortise cheeks so the holes stay inside the back wall

# ---- arms
ARM_LEN, RAIL_T, RAIL_H0, RAIL_H1 = 260.0, 5.0, 35.0, 15.0
HALF_W0, HALF_W1 = 30.0, 45.0                                 # outer faces: 60 wide at the root, 90 at the foot
SKIN_T, WEB_T, BAYS = 2.0, 3.0, 4
FOOT_L, FOOT_T, FOOT_HOLE_D, FOOT_CB_D, FOOT_CB_DEPTH = 25.0, 8.0, 5.5, 10.0, 3.0
TENON_L = MORTISE_DEPTH - FIT                                 # 0.3 mm short of the back wall
NUT_SLOT_X0, NUT_SLOT_W, NUT_SLOT_Z0 = 6.5, 4.5, 12.5          # cross pocket in the tenon for the joint nut; nut corners span 12.65 to 22.35
BED_DIAG_MAX = 250.0

# ---- motor arm bracket: motor on top of a plate, shaft down, pulley on the rotating base's band
MOTOR_R = 139.0                                                # Cults centre distance
BR_X0, BR_X1, PLATE_X0, PLATE_X1 = 108.0, 177.0, 110.0, 170.0
BR_PLATE_T, PLATE_TOP = 5.0, RING_H + 53.0
WIN_X0, WIN_X1, WIN_Z0, WIN_Z1 = 108.0, 136.0, RING_H + 23.0, PLATE_TOP - BR_PLATE_T + 1.0
NEMA_PITCH, SLOT_W, SLOT_L, PILOT_D = 31.0, 3.4, 8.0, 23.0
PULLEY_R, PULLEY_TEETH_W, HUB_L, SHAFT_L, BIG_R = 14.3, 12.0, 6.0, 24.0, 83.0
BAND = (30.0, 42.0)                                            # pulley teeth above the ring top, matching the base's band

# ---- TPU foot pad plug
PAD_D, PAD_T, PEG_D, PEG_L, HEAD_D, HEAD_T = 24.0, 6.0, 5.8, 5.5, 6.5, 1.5    # head lands inside the foot counterbore

def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

def hull8(name, bottom, top):
    """Hexahedron from four bottom corners (counter-clockwise seen from above) and the four top
    corners above them, so rails and web bars can taper in plan and in height at once."""
    bm = bmesh.new()
    b = [bm.verts.new(p) for p in bottom]; t = [bm.verts.new(p) for p in top]
    bm.faces.new(b[::-1]); bm.faces.new(t)
    for i in range(4):
        j = (i + 1) % 4; bm.faces.new((b[i], b[j], t[j], t[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm)

def slab(name, x0, x1, ylo0, yhi0, ylo1, yhi1, z0, zt0, zt1):
    """Block between x0 and x1 whose y extent and top height vary linearly along x."""
    return hull8(name, [(x0, ylo0, z0), (x1, ylo1, z0), (x1, yhi1, z0), (x0, yhi0, z0)],
                       [(x0, ylo0, zt0), (x1, ylo1, zt1), (x1, yhi1, zt1), (x0, yhi0, zt0)])

def bar(name, a, b, w, z0, ztop_a, ztop_b):
    """Bar in plan from a to b, w wide, bottom at z0, top rising from ztop_a to ztop_b."""
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy); px, py = -dy / n * w / 2, dx / n * w / 2
    return hull8(name, [(ax - px, ay - py, z0), (bx - px, by - py, z0), (bx + px, by + py, z0), (ax + px, ay + py, z0)],
                       [(ax - px, ay - py, ztop_a), (bx - px, by - py, ztop_b), (bx + px, by + py, ztop_b), (ax + px, ay + py, ztop_a)])

def hex_z(name, x, y, af, z0, z1):
    return L.cyl_z(name, x, y, af / 2 / math.cos(math.radians(30)), z0, z1, n=6)

def turned(o, deg):
    o.matrix_world = Matrix.Rotation(math.radians(deg), 4, 'Z') @ o.matrix_world; bpy.context.view_layer.update(); return o

def probe(o, p, d):
    """Distance from point p to the surface of o along direction d, or None."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    hit = mathutils.bvhtree.BVHTree.FromBMesh(bm).ray_cast(Vector(p), Vector(d).normalized()); bm.free()
    return None if hit[0] is None else round((hit[0] - Vector(p)).length, 3)

def bore(o, x, y, z, n=24):
    """Median diameter of a z-axis bore at (x, y): rays outward in the plane z, offset half a step so
    none of them lands exactly on a polygon vertex, where a ray cast can pass straight through."""
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); ds = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        hit = tree.ray_cast(Vector((x, y, z)), Vector((math.cos(a), math.sin(a), 0)))
        if hit[0] is not None: ds.append((hit[0] - Vector((x, y, z))).length)
    bm.free(); ds.sort()
    return round(2 * ds[len(ds) // 2], 3) if ds else None

def diagonal_extent(o):
    """Bounding box of o measured along the bed diagonals (the part is printed turned 45 deg)."""
    c = math.cos(math.radians(45))
    u = [v.co.x * c + v.co.y * c for v in o.data.vertices]; w = [-v.co.x * c + v.co.y * c for v in o.data.vertices]
    return round(max(u) - min(u), 1), round(max(w) - min(w), 1)

def polar(r, deg):
    a = math.radians(deg); return r * math.cos(a), r * math.sin(a)

def facet(r, deg):
    """Flatten the outer wall at 60 mm width, thicken it into a boss, cut the mortise and the two
    radial bolt holes; everything generated along +x then turned to the arm angle."""
    L.cut(r, turned(L.box("flat", FACET_X, RING_R + 1, -FACET_W / 2 - 1, FACET_W / 2 + 1, -1, RING_H + 1), deg))
    L.union(r, turned(L.box("boss", FACET_X - BOSS_D, FACET_X, -FACET_W / 2, FACET_W / 2, 0, RING_H), deg))
    L.cut(r, turned(L.box("mortise", FACET_X - MORTISE_DEPTH, FACET_X + 0.1, -MORTISE_W / 2, MORTISE_W / 2, MORTISE_Z0, MORTISE_Z1), deg))
    for y in (-JOINT_BOLT_Y, JOINT_BOLT_Y):
        L.cut(r, turned(L.cyl_between("bolt", (FACET_X - BOSS_D - 1, y, JOINT_BOLT_Z), (FACET_X - MORTISE_DEPTH + 1, y, JOINT_BOLT_Z), JOINT_BOLT_D / 2), deg))

def ring():
    r = L.cyl_z("spider-ring", 0, 0, RING_R, 0, RING_H, n=180)
    L.cut(r, L.cyl_z("hollow", 0, 0, RING_R - WALL, -1, RING_H - RING_PLATE_T))
    L.union(r, L.cyl_z("hub", 0, 0, CENTRE_R + WALL, 0, RING_H))
    for deg in RIB_ANGLES:
        L.union(r, bar("rib", polar(CENTRE_R + 1, deg), polar(RING_R - 1, deg), WALL, 0, RING_H - 1, RING_H - 1))
    for deg in HOLE_ANGLES:
        x, y = polar(HOLE_R, deg); z_plate = RING_H - RING_PLATE_T
        L.union(r, L.cyl_z("nut_boss", x, y, NUT_BOSS_D / 2, z_plate - NUT_H, z_plate + 0.01))
        L.cut(r, hex_z("nut", x, y, NUT_AF, z_plate - NUT_H - 0.1, z_plate + 0.5))
        L.cut(r, L.cyl_z("hole", x, y, HOLE_D / 2, z_plate - NUT_H - 1, RING_H + 1))
    for deg in ARM_ANGLES:
        facet(r, deg)
    L.cut(r, L.cyl_z("centre", 0, 0, CENTRE_R, -1, RING_H + 1))
    L.finish(r); return r

def check_ring(r, report):
    st = L.stats(r); assert st["non_manifold"] == 0, st
    holes = [bore(r, *polar(HOLE_R, d), RING_H - 1) for d in HOLE_ANGLES]
    assert all(abs(h - HOLE_D) < 0.05 for h in holes), holes
    pockets = [bore(r, *polar(HOLE_R, d), RING_H - RING_PLATE_T - 2) for d in HOLE_ANGLES]
    assert all(NUT_AF <= p <= NUT_AF / math.cos(math.radians(30)) + 0.05 for p in pockets), pockets
    mid = (FACET_X - MORTISE_DEPTH / 2, 0, JOINT_BOLT_Z)
    mortise_w = probe(r, mid, (0, 1, 0)) + probe(r, mid, (0, -1, 0))
    mortise_h = probe(r, mid, (0, 0, 1)) + probe(r, mid, (0, 0, -1))
    mortise_d = probe(r, mid, (-1, 0, 0)) + MORTISE_DEPTH / 2
    assert abs(mortise_w - MORTISE_W) < 0.05 and abs(mortise_h - (MORTISE_Z1 - MORTISE_Z0)) < 0.05, (mortise_w, mortise_h)
    assert abs(mortise_d - MORTISE_DEPTH) < 0.05, mortise_d
    assert abs(bore(r, 0, 0, RING_H - 1) - 2 * CENTRE_R) < 0.1
    report["spider-ring"] = {**st, "holes": holes, "mortise": [round(mortise_w, 2), round(mortise_h, 2), round(mortise_d, 2)]}

def rail_outer(x):
    return HALF_W0 + (HALF_W1 - HALF_W0) * (x - FACET_X) / ARM_LEN

def rail_top(x):
    return RAIL_H0 + (RAIL_H1 - RAIL_H0) * (x - FACET_X) / ARM_LEN

def arm(name):
    """Two tapered rails on a 2 mm skin with a Warren web, a wide foot with one hole, and the
    tenon that plugs into a ring facet. Root face at x=FACET_X, foot end at FACET_X + ARM_LEN."""
    x0, x1 = FACET_X, FACET_X + ARM_LEN; xf = x1 - FOOT_L
    a = slab(name, x0, xf, -rail_outer(x0), rail_outer(x0), -rail_outer(xf), rail_outer(xf), 0, SKIN_T, SKIN_T)
    for s in (-1, 1):
        yo0, yo1 = s * rail_outer(x0), s * rail_outer(xf); yi0, yi1 = yo0 - s * RAIL_T, yo1 - s * RAIL_T
        L.union(a, slab("rail", x0, xf, min(yo0, yi0), max(yo0, yi0), min(yo1, yi1), max(yo1, yi1), 0, rail_top(x0), rail_top(xf)))
    nodes = []
    for k in range(BAYS + 1):
        x = x0 + (xf - x0) * k / BAYS; s = -1 if k % 2 == 0 else 1
        nodes.append((x, s * (rail_outer(x) - RAIL_T + 1.5)))         # 1.5 mm into the rail so the union is solid
    for (xa, ya), (xb, yb) in zip(nodes, nodes[1:]):
        L.union(a, bar("web", (xa, ya), (xb, yb), WEB_T, 0, rail_top(xa), rail_top(xb)))
    L.union(a, L.box("foot", xf - 0.01, x1, -HALF_W1, HALF_W1, 0, FOOT_T))
    L.cut(a, L.cyl_z("foot_hole", x1 - FOOT_L / 2, 0, FOOT_HOLE_D / 2, -1, FOOT_T + 1))
    L.cut(a, L.cyl_z("foot_cb", x1 - FOOT_L / 2, 0, FOOT_CB_D / 2, FOOT_T - FOOT_CB_DEPTH, FOOT_T + 1))
    L.union(a, L.box("tenon", x0 - TENON_L, x0 + 0.01, -(MORTISE_W - FIT) / 2, (MORTISE_W - FIT) / 2, MORTISE_Z0 + FIT / 2, MORTISE_Z1 - FIT / 2))
    for y in (-JOINT_BOLT_Y, JOINT_BOLT_Y):
        L.cut(a, L.cyl_between("bolt", (x0 - TENON_L - 1, y, JOINT_BOLT_Z), (x0 + 3, y, JOINT_BOLT_Z), JOINT_BOLT_D / 2))
        L.cut(a, L.box("nut_slot", x0 - TENON_L + NUT_SLOT_X0, x0 - TENON_L + NUT_SLOT_X0 + NUT_SLOT_W, y - NUT_AF / 2, y + NUT_AF / 2, NUT_SLOT_Z0, MORTISE_Z1 + 1))
    L.finish(a); return a

def check_arm(a, report):
    st = L.stats(a); assert st["non_manifold"] == 0, st
    diag = diagonal_extent(a); assert max(diag) <= BED_DIAG_MAX, diag
    x0, x1 = FACET_X, FACET_X + ARM_LEN
    ys = [v.co.y for v in a.data.vertices if v.co.x < x0 - 3]
    tenon_w = round(max(ys) - min(ys), 2); assert abs(MORTISE_W - tenon_w - FIT) < 0.02, tenon_w
    zs = [v.co.z for v in a.data.vertices if v.co.x < x0 - 3]
    tenon_h = round(max(zs) - min(zs), 2); assert abs((MORTISE_Z1 - MORTISE_Z0) - tenon_h - FIT) < 0.02, tenon_h
    xs = [v.co.x for v in a.data.vertices if v.co.x < x0 - 3]
    tenon_l = round(x0 - min(xs), 2); assert abs(MORTISE_DEPTH - tenon_l - FIT) < 0.02, tenon_l
    foot_hole = bore(a, x1 - FOOT_L / 2, 0, 2.0); assert abs(foot_hole - FOOT_HOLE_D) < 0.05, foot_hole
    cb = bore(a, x1 - FOOT_L / 2, 0, FOOT_T - 1.0); assert abs(cb - FOOT_CB_D) < 0.05, cb
    report[a.name] = {**st, "diagonal": diag, "tenon": [tenon_w, tenon_h, tenon_l], "foot_hole": foot_hole}

def motor_arm():
    m = arm("spider-arm-motor")
    # walls stand on the rails, inset 0.3 mm from the rail faces and starting 1 mm inside the rail top,
    # so no wall face coincides with a rail face (coincident faces break the exact boolean)
    for s in (-1, 1):
        yo0, yo1 = s * (rail_outer(BR_X0) - 0.3), s * (rail_outer(BR_X1) - 0.3); yi0, yi1 = yo0 - s * (RAIL_T - 0.6), yo1 - s * (RAIL_T - 0.6)
        L.union(m, slab("wall", BR_X0, BR_X1, min(yo0, yi0), max(yo0, yi0), min(yo1, yi1), max(yo1, yi1), rail_top(BR_X1) - 1, PLATE_TOP - BR_PLATE_T + 0.01, PLATE_TOP - BR_PLATE_T + 0.01))
    L.union(m, slab("plate", PLATE_X0, PLATE_X1, -rail_outer(PLATE_X0), rail_outer(PLATE_X0), -rail_outer(PLATE_X1), rail_outer(PLATE_X1), PLATE_TOP - BR_PLATE_T, PLATE_TOP, PLATE_TOP))
    L.cut(m, L.box("window", WIN_X0 - 1, WIN_X1, -60, 60, WIN_Z0, WIN_Z1))
    L.cut(m, L.cyl_z("pilot", MOTOR_R, 0, PILOT_D / 2, PLATE_TOP - BR_PLATE_T - 1, PLATE_TOP + 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = MOTOR_R + sx * NEMA_PITCH / 2, sy * NEMA_PITCH / 2; half = (SLOT_L - SLOT_W) / 2
            L.cut(m, L.box("slot", cx - half, cx + half, cy - SLOT_W / 2, cy + SLOT_W / 2, PLATE_TOP - BR_PLATE_T - 1, PLATE_TOP + 1))
            for ex in (cx - half, cx + half):
                L.cut(m, L.cyl_z("slot_end", ex, cy, SLOT_W / 2, PLATE_TOP - BR_PLATE_T - 1, PLATE_TOP + 1, n=32))
    L.finish(m); return m

def check_motor_arm(m, report):
    check_arm(m, report)
    zp = PLATE_TOP - BR_PLATE_T / 2
    pilot = bore(m, MOTOR_R, 0, zp); assert abs(pilot - PILOT_D) < 0.05, pilot
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (MOTOR_R + sx * NEMA_PITCH / 2, sy * NEMA_PITCH / 2, zp)
            w = probe(m, c, (0, 1, 0)) + probe(m, c, (0, -1, 0)); l = probe(m, c, (1, 0, 0)) + probe(m, c, (-1, 0, 0))
            assert abs(w - SLOT_W) < 0.05 and abs(l - SLOT_L) < 0.05, (c, w, l)
    teeth_top = PLATE_TOP - BR_PLATE_T - HUB_L; teeth_bot = teeth_top - PULLEY_TEETH_W
    assert (teeth_bot - RING_H, teeth_top - RING_H) == BAND, (teeth_bot, teeth_top)
    assert PLATE_TOP - SHAFT_L <= teeth_bot, "shaft too short for the pulley"
    for s in (-1, 1):
        for z in (teeth_bot, (teeth_bot + teeth_top) / 2, teeth_top):
            p0 = Vector((MOTOR_R, s * PULLEY_R, z)); p1 = Vector((0, s * BIG_R, z))
            d = probe(m, p0, p1 - p0)
            assert d is None or d > (p1 - p0).length, ("belt run hits the arm", s, z, d)
    report[m.name].update({"pilot": pilot, "teeth_above_ring": [teeth_bot - RING_H, teeth_top - RING_H]})

def pad():
    p = L.cyl_z("spider-pad", 0, 0, PAD_D / 2, 0, PAD_T)
    L.union(p, L.cyl_z("peg", 0, 0, PEG_D / 2, PAD_T - 0.01, PAD_T + PEG_L))
    L.union(p, L.cyl_z("head", 0, 0, HEAD_D / 2, PAD_T + PEG_L - 0.01, PAD_T + PEG_L + HEAD_T))
    L.finish(p); return p

def check_pad(p, report):
    st = L.stats(p); assert st["non_manifold"] == 0, st
    assert PAD_T + PEG_L + HEAD_T < PAD_T + FOOT_T and PAD_T + PEG_L > PAD_T + FOOT_T - FOOT_CB_DEPTH, "head must sit inside the counterbore"
    report["spider-pad"] = st

def render(r, a, m):
    """Assembly: ring, three plain arms, the motor arm at 180 deg, the Cults base holder and first
    rotating stage sitting on the ring top, a motor block and its pulley."""
    def instance(src, deg):
        o = src.copy(); o.data = src.data; bpy.context.scene.collection.objects.link(o)
        o.rotation_euler = (0, 0, math.radians(deg)); o.color = src.color; return o
    r.color = (0.85, 0.85, 0.85, 1); a.color = (0.6, 0.75, 0.9, 1); m.color = (0.9, 0.75, 0.5, 1)
    for deg in ARM_ANGLES:
        instance(m if deg == MOTOR_ARM_ANGLE else a, deg)
    a.hide_render = m.hide_render = True
    for name, color in (("axis1-baseHolder", (0.6, 0.6, 0.6, 1)), ("axis-1-rotatingBase1", (0.4, 0.6, 0.9, 1))):
        bpy.ops.wm.stl_import(filepath=os.path.join(CULTS, name + ".stl")); o = bpy.context.selected_objects[0]
        o.location.z = RING_H - 32.5; o.color = color
    mx = -MOTOR_R
    motor = L.box("motor", mx - 21.15, mx + 21.15, -21.15, 21.15, PLATE_TOP, PLATE_TOP + 48); motor.color = (0.2, 0.2, 0.2, 1)
    teeth_top = PLATE_TOP - BR_PLATE_T - HUB_L
    pulley = L.cyl_z("pulley", mx, 0, PULLEY_R, teeth_top - PULLEY_TEETH_W, teeth_top + HUB_L); pulley.color = (0.8, 0.7, 0.2, 1)
    scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; sh = scene.display.shading
    sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = 'OBJECT'
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1100
    cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.clip_end = 10000
    co = bpy.data.objects.new("c", cam); scene.collection.objects.link(co); scene.camera = co
    for name, rot, scale, target in (("spider-iso", (58, 0, 35), 900, (0, 0, 40)), ("spider-side", (88, 0, 90), 800, (0, 0, 60))):
        cam.ortho_scale = scale; co.rotation_euler = tuple(math.radians(v) for v in rot); bpy.context.view_layer.update()
        d = co.matrix_world.to_quaternion() @ Vector((0, 0, -1)); co.location = Vector(target) - d * 2000
        scene.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
report = {}
r = ring(); check_ring(r, report); L.export(r, os.path.join(OUT, "spider-ring.stl"))
a = arm("spider-arm"); check_arm(a, report); L.export(a, os.path.join(OUT, "spider-arm.stl"))
m = motor_arm(); check_motor_arm(m, report); L.export(m, os.path.join(OUT, "spider-arm-motor.stl"))
p = pad(); check_pad(p, report); L.export(p, os.path.join(OUT, "spider-pad.stl")); bpy.data.objects.remove(p)
print("SPIDER", json.dumps(report))
render(r, a, m)
print("SPIDER DONE")
