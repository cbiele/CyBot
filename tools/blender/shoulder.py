"""Shoulder (axis 2), body and turning base (axis 1) parts.
Built and checked in the shoulder frame (shoulder_dims.py), exported in print orientation to model/shoulder/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/shoulder.py"""
import bpy, bmesh, math, os, sys, json, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import elbow_dims as E
import forearm_dims as F
from shoulder_dims import *
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
MODEL = os.path.join(ROOT, "model")
OUT = os.path.join(MODEL, "shoulder")
ELBOW = os.path.join(MODEL, "elbow")
COMPACT = os.path.join(MODEL, "cycloid-poc", "20-1-compact-m25")
PARTS, CHECKS, PRINT_POSE, REPORT = {}, [], {}, {}
with open(os.path.join(ELBOW, "poses.json")) as _f:
    ELBOW_POSES = json.load(_f)


def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))


def basis(u, v, w, origin):
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2], m[i][3] = u[i], v[i], w[i], origin[i]
    return m


def cyl_y(name, x, z, r, y0, y1, n=96):
    c = L.cyl_z(name, 0, 0, r, y0, y1, n=n)
    c.data.transform(basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, 0)))
    c.data.transform(Matrix.Translation((x, 0, z)))
    return c


def cone_y(name, r0, y0, r1, y1, n=192):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r0, radius2=r1, depth=abs(y1 - y0))
    o = L._obj(name, bm)
    o.data.transform(basis((1, 0, 0), (0, 0, -1 if y1 > y0 else 1), (0, 1 if y1 > y0 else -1, 0), (0, (y0 + y1) / 2, 0)))
    return o


def rod(name, a, b, r, n=48):
    o = L.cyl_between(name, a, b, r, n=n)
    o.data.transform(o.matrix_world); o.matrix_world = Matrix(); return o


def copy(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c); return c


def join(objs, name):
    o = copy(objs[0], name)
    for p in objs[1:]:
        L.union(o, copy(p, "j"))
    return o


def overlap(a, b):
    ca, cb = copy(a, "ov_a"), copy(b, "ov_b")
    L.boolean(ca, cb, 'INTERSECT')
    bm = bmesh.new(); bm.from_mesh(ca.data); v = abs(bm.calc_volume()); bm.free()
    bpy.data.objects.remove(ca); return v


def tree(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    t = mathutils.bvhtree.BVHTree.FromBMesh(bm); bm.free(); return t


def min_gap(a, b):
    t = tree(b)
    return min(t.find_nearest(v.co)[3] for v in a.data.vertices)


def touching(a, b):
    return min_gap(a, b) <= 0.05


def island_bounds(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, pts = [v], []
        while stack:
            w = stack.pop()
            if w.index in seen:
                continue
            seen.add(w.index); pts.append(w.co.copy())
            stack += [e.other_vert(w) for e in w.link_edges]
        out.append([[round(min(p[i] for p in pts), 1) for i in range(3)], [round(max(p[i] for p in pts), 1) for i in range(3)]])
    bm.free(); return out


def islands(o):
    return len(island_bounds(o))


def ray_len(o, origin, direction):
    h = tree(o).ray_cast(Vector(origin), Vector(direction).normalized())[0]
    return None if h is None else (h - Vector(origin)).length


def non_manifold_at(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    pts = [tuple(round(c, 1) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges if not e.is_manifold]
    bm.free(); return pts[:8]


def bolt_for_nut(grip):
    """Shortest stock M3 through a plain nut (2.4) on the far face, at most 2 past it."""
    fits = [n for n in M3_STOCK if grip + 2.4 <= n <= grip + 2.4 + 2.0]
    assert fits, ("no stock M3 for this grip", grip)
    return fits[0]


def radial_r(o, y, inward=True, r0=60.0):
    """Mean radius of o's surface at y, by 24 rays off the polygon's vertices: inward from r0 (a journal) or out from the axis (a bore)."""
    rs = []
    for k in range(24):
        a = 2 * math.pi * (k + 0.37) / 24
        u = Vector((math.cos(a), 0, math.sin(a)))
        rs.append(r0 - ray_len(o, u * r0 + Vector((0, y, 0)), -u) if inward else ray_len(o, (0, y, 0), u))
    return sum(rs) / len(rs)


def part_ok(n):
    assert islands(PARTS[n]) == 1, (n, "islands", island_bounds(PARTS[n]))
    assert L.stats(PARTS[n])["non_manifold"] == 0, (n, "non-manifold", non_manifold_at(PARTS[n]))


def on_bed(n):
    """The print-pose footprint inside 220 x 250, turned up to 20 degrees off the diagonal if it must be."""
    c = copy(PARTS[n], "fp"); c.data.transform(PRINT_POSE[n])
    vs = [v.co for v in c.data.vertices]
    assert abs(min(v.z for v in vs)) < 0.01, (n, "print pose not on the bed", min(v.z for v in vs))
    cx, cy = (max(v.x for v in vs) + min(v.x for v in vs)) / 2, (max(v.y for v in vs) + min(v.y for v in vs)) / 2
    bpy.data.objects.remove(c)
    for k in [0] + list(range(-65, 66)):
        a = math.radians(k)
        rx = [(v.x - cx) * math.cos(a) - (v.y - cy) * math.sin(a) for v in vs]
        ry = [(v.x - cx) * math.sin(a) + (v.y - cy) * math.cos(a) for v in vs]
        w, h = max(rx) - min(rx), max(ry) - min(ry)
        if w <= 220.0 and h <= 250.0 and max(v.z for v in vs) <= 250.0:
            REPORT.setdefault("on_bed_mm", {})[n] = (round(w, 1), round(h, 1))
            return
    assert False, (n, "doesn't fit the bed's 220 x 250")


def lock_wall(plate, side, angles=LOCK_ANGLES, r=LOCK_R, hole_r=LOCK_HOLE_R):
    """Least plastic round each drilled hole, by rays from its edge in 8 directions; each must leave the plate through its own surface."""
    y0, y1 = PLATE_FACES[side]
    t = tree(plate)
    walls = []
    for a in angles:
        cx, cz = polar(r, a)
        face = ray_len(plate, (cx, y1 + 1.0 if side == "A" else y0 - 1.0, cz), (0, -1 if side == "A" else 1, 0))
        assert face is not None and abs(face - 1.0) < 0.05, ("drilled hole not in plate material", side, a, face)
        for ym in (y0 + 0.3, (y0 + y1) / 2, y1 - 0.3):
            for k in range(8):
                u = Vector(polar(1.0, a + 45.0 * k)); u = Vector((u.x, 0, u.y))
                p = Vector((cx, ym, cz)) + u * hole_r
                loc, nrm, _, d = t.ray_cast(p, u)
                assert loc is not None and nrm.dot(u) > 0, ("hole breaks into a void", side, a, k)
                walls.append(d)
    return min(walls)


def elbow_part(name):
    """A model/elbow STL in the shoulder frame, the upper arm straight up."""
    bpy.ops.wm.stl_import(filepath=os.path.join(ELBOW, name + ".stl"))
    o = bpy.context.selected_objects[0]; o.name = name
    o.data.transform(Matrix.Translation((0, 0, E.UPPER_L)) @ Matrix(ELBOW_POSES[name]))
    return o


def rot_shoulder(psi):
    """The upper arm pitched by psi about the shoulder axis: +psi tips the elbow towards +x."""
    return Matrix.Rotation(math.radians(psi), 4, 'Y')


def upper_arm_moving():
    """What swings with the upper arm and could meet the body: both plates, the elbow motor (60 long) at both slot ends, its belt."""
    h, up = E.MOTOR_SQ / 2, E.UPPER_L
    out = {"plate A": elbow_part("upper-plate-A"), "plate B": elbow_part("upper-plate-B")}
    for s in (-1, 1):
        zm = E.MOTOR_Z + s * E.MOTOR_SLOT + up
        out[f"elbow motor {s:+d}"] = L.box("elbow motor", -h, h, E.Y_REAR - E.MOTOR_L_MAX, E.Y_REAR, zm - h, zm + h)
    w = E.R60_OD + E.BELT_T + 1.5
    out["elbow belt"] = L.box("elbow belt", -w, w, E.Y_REAR + E.PLATE_T, E.BELT_ENVELOPE_Y,
                              E.MOTOR_Z - E.MOTOR_SLOT - E.R20_OD - E.BELT_T - 1.5 + up, w + up)
    return out


def hub_half(side):
    """Spigot in the plate's Ø65 seat against its lip, flange on the plate's outer face, 45-degree cone, shoulder, journal in the wall's 6810."""
    sgn, name = (1, "shoulder-hub-a") if side == "A" else (-1, "shoulder-hub-b")
    Y = lambda a, b: sorted((sgn * a, sgn * b))
    lip, face = abs(LIP_FACE_Y[side]), E.Y_REAR + E.PLATE_T
    f1, wall_in, end = face + FLANGE_T, abs(WALL_6810_Y[side][0]), abs(HUB_Y[1] if side == "A" else HUB_Y[0])
    h = cyl_y(name, 0, 0, SPIGOT_R, *Y(lip, face + 0.01), n=192)
    L.union(h, cyl_y("flange", 0, 0, FLANGE_R, *Y(face, f1), n=192))
    L.union(h, cone_y("cone", FLANGE_R, sgn * (f1 - 0.01), HUB_SHOULDER_R, sgn * (f1 + CONE)))
    L.union(h, cyl_y("shoulder", 0, 0, HUB_SHOULDER_R, *Y(f1 + CONE - 0.01, wall_in), n=192))
    L.union(h, cyl_y("journal", 0, 0, B6810[0], *Y(wall_in - 0.01, end - END_CHAMFER), n=192))
    L.union(h, cone_y("end", B6810[0], sgn * (end - END_CHAMFER - 0.01), B6810[0] - END_CHAMFER, sgn * end))
    L.finish(h)
    L.cut(h, cyl_y("wire bore", 0, 0, HUB_BORE_R, *Y(lip - 1.0, end - HUB_FLOOR if side == "A" else end + 1.0), n=128))
    for a in LOCK_ANGLES:
        x, z = polar(LOCK_R, a)
        L.cut(h, cyl_y("lock insert", x, z, M3_INSERT_R, *Y(face - 1.0, face + M3_INSERT_DEPTH), n=32))
    if side == "A":
        for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
            L.cut(h, cyl_y("dog", x, z, DOG_R + 0.15, end - DOG_H - 0.5, end + 1.0, n=48))
        head_y = end + OUT_PLATE_T + 3.3 - HUB_SCREW_L
        for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
            L.cut(h, cyl_y("screw", x, z, M3_CLEAR_R, end - HUB_FLOOR - 1.0, end + 1.0, n=32))
            L.cut(h, cyl_y("screw cb", x, z, 3.0, end - HUB_FLOOR - 1.0, head_y, n=32))
    PRINT_POSE[name] = basis((1, 0, 0), (0, 0, -sgn), (0, sgn, 0), (0, 0, end))
    return h


def hub():
    return hub_half("A"), hub_half("B")


def output_plate():
    """Replaces the compact's forearm output plate: three bigger, longer dogs for the shoulder's torque."""
    y0 = HUB_Y[1]
    p = cyl_y("shoulder-output-plate", 0, 0, OUT_PLATE_R, y0, y0 + OUT_PLATE_T, n=128)
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        L.union(p, cyl_y("dog", x, z, DOG_R, y0 - DOG_H, y0 + 0.01, n=48))
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        L.cut(p, cyl_y("screw", x, z, M3_CLEAR_R, y0 - 1.0, y0 + OUT_PLATE_T + 1.0, n=32))
        L.cut(p, cyl_y("head", x, z, 3.0, y0 - 1.0, y0 + 3.2, n=48))
    L.finish(p)
    PRINT_POSE["shoulder-output-plate"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y0 + OUT_PLATE_T))
    return p


def drill_jig():
    """On plate A's outer face (turned half round about z for plate B): spigot in the seat, fences on the straight sides, Ø3.4 guides."""
    face = E.Y_REAR + E.PLATE_T
    top, w = face + JIG_T, JIG_FENCE[1]
    j = cyl_y("plate-drill-jig", 0, 0, JIG_R, face, top, n=192)
    L.union(j, L.box("towards the elbow", -w, w, face, top, 0.0, 46.0))
    L.union(j, cyl_y("spigot", 0, 0, SEAT_R - 0.1, face - JIG_SPIGOT_DEPTH, face + 0.01, n=192))
    for s in (1, -1):
        L.union(j, L.box("fence", *sorted((s * JIG_FENCE[0], s * w)), face - JIG_SPIGOT_DEPTH, face + 0.01, 3.0, 46.0))
    L.finish(j)
    L.cut(j, cyl_y("window", 0, 0, 20.0, face - JIG_SPIGOT_DEPTH - 1.0, top + 1.0, n=96))
    for a in LOCK_ANGLES:
        x, z = polar(LOCK_R, a)
        L.cut(j, cyl_y("guide", x, z, LOCK_HOLE_R, face - JIG_SPIGOT_DEPTH - 1.0, top + 1.0, n=32))
    PRINT_POSE["plate-drill-jig"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, top))
    return j


def check_hub():
    ha, hb, jig, op = PARTS["shoulder-hub-a"], PARTS["shoulder-hub-b"], PARTS["plate-drill-jig"], PARTS["shoulder-output-plate"]
    pa, pb = elbow_part("upper-plate-A"), elbow_part("upper-plate-B")
    for n in ("shoulder-hub-a", "shoulder-hub-b", "plate-drill-jig", "shoulder-output-plate"):
        part_ok(n); on_bed(n)
    for h, side in ((ha, "A"), (hb, "B")):
        j = radial_r(h, sum(WALL_6810_Y[side]) / 2)
        assert B6810[0] - 0.01 <= j <= B6810[0] + 0.1, ("journal", side, j)
        s = radial_r(h, sum((LIP_FACE_Y[side], PLATE_FACES[side][1] if side == "A" else PLATE_FACES[side][0])) / 2)
        assert SPIGOT_R - 0.01 <= s <= SPIGOT_R + 0.1, ("spigot", side, s)
        sgn = 1 if side == "A" else -1
        bore = radial_r(h, sgn * (abs(LIP_FACE_Y[side]) + 3.0), inward=False)
        assert bore >= HUB_BORE_R - 0.05, ("wire bore", side, bore)
        past = [v.co for v in h.data.vertices if sgn * v.co.y > abs(WALL_6810_Y[side][0]) + 0.01]
        assert max(math.hypot(p.x, p.z) for p in past) <= B6810[0] + 0.01, ("the 6810 can't slide onto the journal", side)
        land = [v.co for v in h.data.vertices if abs(FLANGE_Y[side][1 if side == "A" else 0]) + CONE - 0.005 <= sgn * v.co.y <= abs(WALL_6810_Y[side][0]) + 0.005]
        assert land and max(math.hypot(p.x, p.z) for p in land) <= HUB_SHOULDER_R + 0.01, ("shoulder past the 6810's inner ring", side)
        assert max(sgn * v.co.y for v in h.data.vertices if math.hypot(v.co.x, v.co.z) > B6810[0] + 0.5) >= abs(WALL_6810_Y[side][0]) - 0.01, ("shoulder doesn't reach the 6810", side)
    both = join([ha, hb], "hubs")
    run = ray_len(both, (0, HUB_Y[0] - 1.0, 0), (0, 1, 0))
    assert run is not None and run - 1.0 >= HUB_Y[1] - HUB_Y[0] - 10.0, ("wire bore blocked", run)
    for h, p, side in ((ha, pa, "A"), (hb, pb, "B")):
        assert overlap(h, p) < 0.05, ("hub hits its plate", side)
        sgn = 1 if side == "A" else -1
        spig = min(sgn * v.co.y for v in h.data.vertices if math.hypot(v.co.x, v.co.z) > E.LIP_IN_R + 0.5)
        lip = sgn * 35.0 - sgn * ray_len(p, (30.0, sgn * 35.0, 0), (0, -sgn, 0))
        assert abs(spig - sgn * lip) <= 0.05, ("spigot not on the lip", side, spig, lip)
        assert touching(h, p), ("flange not on the plate", side)
    walls = {s: round(lock_wall(p, s), 2) for p, s in ((pa, "A"), (pb, "B"))}
    assert min(walls.values()) >= WALL_MIN, ("lock hole wall", walls)
    n = len(LOCK_ANGLES)
    f = SHOULDER_DESIGN_NMM / LOCK_R / n
    shear, bearing = f / (math.pi * 1.5 ** 2), f / (3.0 * E.PLATE_T)
    assert shear <= PRINTED_MPA and bearing <= PRINTED_MPA, ("plate lock", shear, bearing)
    for h, side in ((ha, "A"), (hb, "B")):
        sgn = 1 if side == "A" else -1
        for a in LOCK_ANGLES:
            x, z = polar(LOCK_R, a)
            d = ray_len(h, (x, sgn * (PLATE_FACES[side][1] if side == "A" else -PLATE_FACES[side][0]) - sgn * 1.0, z), (0, sgn, 0))
            assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("lock insert", side, a, d)
            assert LOCK_BOLT_L - E.PLATE_T >= 3.0 and LOCK_BOLT_L - E.PLATE_T <= M3_INSERT_DEPTH - 0.5, "lock bolt engagement"
    dog = SHOULDER_DESIGN_NMM / DOG_PCD_R / len(DOG_ANGLES) / (2 * DOG_R * DOG_H)
    assert dog <= PRINTED_MPA, ("dog bearing", dog)
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        assert ray_len(ha, (x, HUB_Y[1] + 0.01, z), (0, -1, 0)) >= DOG_H + 0.2, "dog hole too shallow"
    carrier_face = HUB_Y[1] + OUT_PLATE_T
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        assert ray_len(ha, (x, HUB_Y[1] + 0.01, z), (0, -1, 0)) is None or ray_len(ha, (x, HUB_Y[1] + 0.01, z), (0, -1, 0)) > HUB_FLOOR, "screw hole blocked"
        floor = HUB_Y[1] - HUB_FLOOR - 1.0 + ray_len(ha, (x + 2.4, HUB_Y[1] - HUB_FLOOR - 1.0, z), (0, 1, 0))
        reach = HUB_SCREW_L - (carrier_face - floor)
        assert 3.0 <= reach <= 4.0, ("M3 x 12 into the carrier's inserts", reach)
    assert overlap(op, ha) < 0.05 and touching(op, ha), "output plate's dogs don't sit in the hub"
    check_jig(jig, pa, pb)
    REPORT.update({"lock_r": LOCK_R, "lock_angles": LOCK_ANGLES, "lock_wall_mm": walls, "lock_shear_mpa": round(shear, 1),
                   "lock_bearing_mpa": round(bearing, 1), "dog_bearing_mpa": round(dog, 1), "hub_y": HUB_Y,
                   "bolts": {"plate lock (from inside the plate gap, into flange inserts)": LOCK_BOLT_L, "hub floor to compact carrier": HUB_SCREW_L}})
    for o in (pa, pb, both):
        bpy.data.objects.remove(o)


def check_jig(jig, pa, pb):
    jb = copy(jig, "jig on B"); jb.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
    for j, p, side in ((jig, pa, "A"), (jb, pb, "B")):
        assert overlap(j, p) < 0.05, ("jig hits the plate", side)
        assert touching(j, p), ("jig doesn't sit on the plate", side)
        sgn = 1 if side == "A" else -1
        y_out = PLATE_FACES[side][1] if side == "A" else PLATE_FACES[side][0]
        for a in LOCK_ANGLES:
            x, z = polar(LOCK_R, a)
            x = x if side == "A" else -x
            assert ray_len(j, (x, y_out + sgn * (JIG_T + 1.0), z), (0, -sgn, 0)) is None, ("guide hole blocked", side, a)
        fence = [v.co for v in j.data.vertices if sgn * v.co.y < sgn * y_out - 1.0 and abs(v.co.x) > E.PLATE_R]
        assert any(p.x > 0 for p in fence) and any(p.x < 0 for p in fence), ("no fences on the plate's sides", side)
    s = radial_r(jig, PLATE_FACES["A"][1] - JIG_SPIGOT_DEPTH / 2, r0=35.0)   # inside the fences
    assert SEAT_R - 0.2 <= s <= SEAT_R - 0.02, ("jig spigot", s)
    bpy.data.objects.remove(jb)


bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["shoulder-hub-a"], PARTS["shoulder-hub-b"] = hub()
PARTS["shoulder-output-plate"] = output_plate()
PARTS["plate-drill-jig"] = drill_jig()
CHECKS.append(check_hub)
for check in CHECKS:
    check()
print("SHOULDER", json.dumps({**{n: L.stats(o) for n, o in PARTS.items()}, **REPORT}))
os.makedirs(OUT, exist_ok=True)
for n, o in PARTS.items():
    o.matrix_world = Matrix()
    o.data.transform(PRINT_POSE[n])
    L.export(o, os.path.join(OUT, n + ".stl"))
with open(os.path.join(OUT, "poses.json"), "w") as f:   # each STL back into the shoulder frame, for head_concept.py --shoulder
    json.dump({n: [[round(c, 6) for c in row] for row in PRINT_POSE[n].inverted()] for n in PARTS}, f, indent=1)
print("SHOULDER DONE")
