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
    """The print-pose footprint inside 220 x 250, turned on the bed if it must be."""
    c = copy(PARTS[n], "fp"); c.data.transform(PRINT_POSE[n])
    vs = [v.co for v in c.data.vertices]
    assert abs(min(v.z for v in vs)) < 0.01, (n, "print pose not on the bed", min(v.z for v in vs))
    cx, cy = (max(v.x for v in vs) + min(v.x for v in vs)) / 2, (max(v.y for v in vs) + min(v.y for v in vs)) / 2
    bpy.data.objects.remove(c)
    for k in [0] + list(range(-90, 91)):
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
    else:
        for a in KEY_ANGLES:
            s = L.box("key slot", HUB_BORE_R - 1.0, B6810[0] + 1.0, -end - 1.0, -end + KEY_DEPTH_Y, -KEY_W / 2, KEY_W / 2)
            s.data.transform(Matrix.Rotation(-math.radians(a), 4, 'Y'))
            L.cut(h, s)
        for x, z in [polar(COLLAR_SCREW_R, a) for a in COLLAR_SCREW_ANGLES]:
            L.cut(h, cyl_y("collar insert", x, z, M3_INSERT_R, -end - 1.0, -end + M3_INSERT_DEPTH, n=32))
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


def concat(objs, name):
    """One object holding all of objs' meshes, without a boolean (for overlap and gap tests only)."""
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
        bpy.data.objects.remove(o)
    return L._obj(name, bm)


def prism_y(name, pts, y0, y1):
    """A prism through y on a polygon of (x, z) points."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y0, z)) for x, z in pts]
    hi = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(lo); bm.faces.new(hi[::-1])
    for i in range(len(pts)):
        bm.faces.new((lo[i], hi[i], hi[(i + 1) % len(pts)], lo[(i + 1) % len(pts)]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)


def sector_y(name, r0, r1, a0, a1, y0, y1, n=48):
    """Annular sector about the y axis, angles in the x-z plane from +x towards +z."""
    angs = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    return prism_y(name, [polar(r1, t) for t in angs] + [polar(r0, t) for t in angs[::-1]], y0, y1)


def posed_stl(path, name, matrix):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name
    o.data.transform(matrix)
    return o


def compact_posed():
    """The compact's housing: its cycloid frame's z runs from the rear face at COMPACT_REAR_Y towards the hub (-y)."""
    m = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, COMPACT_REAR_Y, 0))
    halves = [posed_stl(os.path.join(COMPACT, "housing-rear.stl"), "chr", m),
              posed_stl(os.path.join(COMPACT, "housing-front.stl"), "chf", m @ Matrix.Diagonal((1, -1, -1, 1)))]
    c = join(halves, "compact")   # a boolean union: two shells on a shared face upset the overlap tests
    for o in halves:
        bpy.data.objects.remove(o)
    return c


def wall_top(side):
    """The trapezoid's top corners, inside the boss disc so the union leaves no seam on the faces."""
    r = WALL_BOSS_R[side]
    return math.sqrt(r * r - (r / 2) ** 2) - 0.5, r / 2


def x_edge(side, z):
    xt, zt = wall_top(side)
    return xt + (WALL_BOTTOM_HALF_W - xt) * (zt - z) / (zt + SHOULDER_AXIS_Z)


def wall(side):
    """A plate on the turntable: the 6810 boss at the shoulder axis, a foot along its outer face, two windows by a rib."""
    sgn, r, h = (1 if side == "A" else -1), WALL_BOSS_R[side], SHOULDER_AXIS_Z
    y_in, y_out = WALL_Y[side]
    Y = sorted((y_in, y_out))
    xt, zt = wall_top(side)
    w = prism_y(f"body-wall-{side}", [(-xt, zt), (xt, zt), (WALL_BOTTOM_HALF_W, -h), (-WALL_BOTTOM_HALF_W, -h)], *Y)
    L.union(w, cyl_y("boss", 0, 0, r, *Y, n=192))
    L.union(w, L.box("foot", -WALL_BOTTOM_HALF_W, WALL_BOTTOM_HALF_W, *sorted((y_out - sgn * 0.01, y_out + sgn * FOOT_W)), -h, -h + FOOT_T))
    L.finish(w)
    L.cut(w, cyl_y("seat", 0, 0, SEAT_R, *sorted((y_in - sgn * 1.0, WALL_6810_Y[side][1])), n=192))
    L.cut(w, cyl_y("lip", 0, 0, WALL_LIP_R, *sorted((y_in - sgn * 1.0, y_out + sgn * 1.0)), n=192))
    zt, zb = -(r + WINDOW_BORDER), -h + FOOT_T + WINDOW_BORDER
    for s in (1, -1):
        pts = [(s * WINDOW_RIB, zt), (s * (x_edge(side, zt) - WINDOW_BORDER), zt), (s * (x_edge(side, zb) - WINDOW_BORDER), zb), (s * WINDOW_RIB, zb)]
        L.cut(w, prism_y("window", pts, Y[0] - 1.0, Y[1] + 1.0))
    for x, y in WALL_FOOT[side]:
        L.cut(w, L.cyl_z("foot bolt", x, y, M3_CLEAR_R, -h - 1.0, -h + FOOT_T + 1.0, n=32))
    PRINT_POSE[w.name] = basis((1, 0, 0), (0, 0, sgn), (0, -sgn, 0), (0, 0, -sgn * y_in))
    return w


def wall_a():
    w = wall("A")
    for a in CAGE_SCREW_ANGLES:
        x, z = polar(CAGE_SCREW_R, a)
        L.cut(w, cyl_y("cage insert", x, z, M3_INSERT_R, WALL_Y["A"][1] - M3_INSERT_DEPTH - 1.5, WALL_Y["A"][1] + 1.0, n=32))
    return w


def wall_b():
    w = wall("B")
    x0, z0 = WALL_B_FRONT
    L.cut(w, L.box("palm's path", x0, x0 + 100.0, WALL_Y["B"][1] - FOOT_W - 1.0, WALL_Y["B"][0] + 1.0, z0, WALL_BOSS_R["B"] + 1.0))
    for b in stop_blocks():
        L.union(w, b)
    L.finish(w)
    mx, mz = polar(MAGNET_AT_R, TAB_PHI)
    y = WALL_Y["B"][1]
    L.cut(w, L.box("sensor pocket", mx - SENSOR[0] / 2 - 0.1, mx + SENSOR[0] / 2 + 0.1, y - 1.0, y + SENSOR[2] + 0.1,
                   mz - SENSOR[1] / 2 - 0.1, mz + SENSOR[1] / 2 + 0.1))
    L.cut(w, L.box("leads", -1.5, 1.5, y - 1.0, y + 1.0, -WALL_BOSS_R["B"] - 1.0, mz))
    return w


def compact_cage():
    """Under the compact's front face on wall A: inserts for its four R30 bolts, four M3s into inserts in wall A."""
    y0, y1 = CAGE_Y
    c = cyl_y("compact-cage", 0, 0, CAGE_R, y0, y1, n=192)
    L.cut(c, cyl_y("round the hub's end", 0, 0, CAGE_BORE_R[0], y0 - 1.0, HUB_Y[1] + 0.5, n=192))
    L.cut(c, cyl_y("bore", 0, 0, CAGE_BORE_R[1], y0 - 1.0, y1 + 1.0, n=128))
    for x, z in [polar(F.BOLT_R, a) for a in F.BOLT_ANGLES]:
        L.cut(c, cyl_y("insert", x, z, M3_INSERT_R, y1 - M3_INSERT_DEPTH, y1 + 1.0, n=32))
        L.cut(c, cyl_y("bolt", x, z, M3_CLEAR_R, y0 - 1.0, y1, n=32))
    for x, z in [polar(CAGE_SCREW_R, a) for a in CAGE_SCREW_ANGLES]:
        L.cut(c, cyl_y("screw", x, z, M3_CLEAR_R, y0 - 1.0, y1 + 1.0, n=32))
    PRINT_POSE["compact-cage"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y1))
    return c


def stop_tab():
    return sector_y("stop tab", TAB_R[0], TAB_R[1], TAB_PHI - TAB_HALF, TAB_PHI + TAB_HALF, TAB_Y[1], TAB_Y[0])


def stop_blocks():
    """On wall B's outer face, where the tab's edges arrive at psi = +-92 (the tab turns by -psi)."""
    at_max = TAB_PHI - PSI_STOPS[1] - TAB_HALF
    at_min = TAB_PHI - PSI_STOPS[0] + TAB_HALF
    y0, y1 = TAB_Y[1], WALL_Y["B"][1] + 0.01
    return [sector_y("stop", STOP_R[0], STOP_R[1], at_max - STOP_BLOCK_DEG, at_max, y0, y1),
            sector_y("stop", STOP_R[0], STOP_R[1], at_min, at_min + STOP_BLOCK_DEG, y0, y1)]


def stop_collar():
    """Keyed onto hub B's journal end outside wall B: clamps the 6810's inner ring, carries the stop tab and the Hall magnet."""
    y_face, y_end = STOP_COLLAR_Y
    flange_in = HUB_Y[0] - 0.3
    c = cyl_y("shoulder-stop-collar", 0, 0, HUB_INNER_LAND_R, y_face - 2.0, y_face, n=192)
    L.union(c, cyl_y("body", 0, 0, STOP_COLLAR_R, y_end, y_face - 2.0 + 0.01, n=192))
    L.union(c, stop_tab())
    L.finish(c)
    L.cut(c, cyl_y("bore", 0, 0, B6810[0] + 0.05, flange_in, y_face + 1.0, n=192))
    L.cut(c, cyl_y("wires", 0, 0, HUB_BORE_R + 0.5, y_end - 1.0, y_face + 1.0, n=96))
    for a in KEY_ANGLES:
        t = L.box("tongue", HUB_BORE_R - 0.5, B6810[0] + 0.5, flange_in - 0.5, HUB_Y[0] + KEY_DEPTH_Y - 0.3, -KEY_W / 2 + 0.2, KEY_W / 2 - 0.2)
        t.data.transform(Matrix.Rotation(-math.radians(a), 4, 'Y'))
        L.union(c, t)
    for x, z in [polar(COLLAR_SCREW_R, a) for a in COLLAR_SCREW_ANGLES]:
        L.cut(c, cyl_y("screw", x, z, M3_CLEAR_R, y_end - 1.0, flange_in + 1.0, n=32))
    mx, mz = polar(MAGNET_AT_R, TAB_PHI)
    L.cut(c, cyl_y("magnet", mx, mz, MAGNET_R + 0.1, TAB_Y[0] - MAGNET_RECESS - MAGNET_D, TAB_Y[0] + 1.0, n=32))
    PRINT_POSE["shoulder-stop-collar"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -y_end))
    return c


def pulley80_envelope():
    e = cyl_y("80T hub", 0, 0, 9.5, PULLEY80_Y, PULLEY80_Y + E.PULLEY_HUB + 0.01)
    L.union(e, cyl_y("80T teeth", 0, 0, R80_OD + 1.5, PULLEY80_Y + E.PULLEY_HUB, PULLEY80_Y + E.PULLEY_H))
    return e


def hull(objs, name):
    bm = bmesh.new()
    for o in objs:
        for v in o.data.vertices:
            bm.verts.new(v.co)
        bpy.data.objects.remove(o)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    return L._obj(name, bm)


def shoulder_belt_envelope(slot):
    """Both pulleys and the belt between them, with the motor at slot (-3 to +3 along the belt line)."""
    x, z = motor_at(slot)
    y0, y1 = PULLEY80_TEETH_Y[0] - 1.5, PULLEY80_TEETH_Y[1] + 1.5
    band = hull([cyl_y("a", 0, 0, R80_OD + E.BELT_T, y0, y1), cyl_y("b", x, z, E.R20_OD + E.BELT_T, y0, y1)], "shoulder belt")
    L.union(band, pulley80_envelope())
    L.union(band, cyl_y("20T hub", x, z, 9.5, PULLEY80_Y, PULLEY80_Y + E.PULLEY_HUB + 0.01))
    L.union(band, cyl_y("20T teeth", x, z, E.R20_OD + 1.5, PULLEY80_Y + E.PULLEY_HUB, PULLEY80_Y + E.PULLEY_H))
    return band


def shoulder_motor_box(kind, slot):
    m, (x, z) = MOTORS[kind], motor_at(slot)
    h = m["sq"] / 2
    return L.box(f"motor {kind}", x - h, x + h, SWAP_Y[0] - m["length"], SWAP_Y[0], z - h, z + h)


def along(name, d0, d1, half_w, y0, y1):
    """A box in the belt plane's sense: from d0 to d1 towards the 80T (from the motor's axis at slot 0), half_w across."""
    mx, mz = motor_at()
    n = (-BELT_U[0], -BELT_U[1]); t = (-n[1], n[0])
    pts = [(mx + n[0] * d + t[0] * s, mz + n[1] * d + t[1] * s) for d, s in ((d0, -half_w), (d1, -half_w), (d1, half_w), (d0, half_w))]
    return prism_y(name, pts, y0, y1)


def push_lug():
    return along("push lug", LUG_D[0], LUG_D[1], LUG_HALF_W, SWAP_Y[0], SWAP_Y[1] + 0.01)


def motor_plate(kind):
    """The swap plate: the motor's face on its far side, inserts in the common outer pattern, its corner towards the 80T square to the belt."""
    m, (mx, mz) = MOTORS[kind], motor_at()
    name = f"shoulder-motor-plate-{kind}"
    p = L.box(name, mx - SWAP_HALF, mx + SWAP_HALF, *SWAP_Y, mz - SWAP_HALF, mz + SWAP_HALF)
    L.cut(p, along("chamfer", CHAMFER_D, CHAMFER_D + 100.0, 100.0, SWAP_Y[0] - 1.0, SWAP_Y[1] + 1.0))
    L.cut(p, cyl_y("pilot", mx, mz, m["pilot_r"], SWAP_Y[0] - 1.0, SWAP_Y[1] + 1.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            L.cut(p, cyl_y("motor screw", mx + sx * m["hole"], mz + sz * m["hole"], m["hole_r"], SWAP_Y[0] - 1.0, SWAP_Y[1] + 1.0, n=32))
    for dx, dz in PLATE_MOUNT:
        L.cut(p, cyl_y("insert", mx + dx, mz + dz, M3_INSERT_R, SWAP_Y[0] - 1.0, SWAP_Y[1] + 1.0, n=32))
    PRINT_POSE[name] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (-mx, mz, -SWAP_Y[0]))
    return p


def slot_y(name, x, z, r, y0, y1, n=16):
    """A round-ended slot along the belt line, MOTOR_SLOT each way."""
    pts = []
    for e in (1, -1):
        cx, cz = x + e * MOTOR_SLOT * BELT_U[0], z + e * MOTOR_SLOT * BELT_U[1]
        base = math.degrees(math.atan2(BELT_U[1], BELT_U[0])) + (0 if e > 0 else 180)
        pts += [(cx + r * math.cos(math.radians(base - 90 + 180 * k / n)), cz + r * math.sin(math.radians(base - 90 + 180 * k / n))) for k in range(n + 1)]
    return prism_y(name, pts, y0, y1)


def motor_bracket():
    """Upright on the turntable behind the 80T's belt plane: the swap plate slides on its far face, the push screw's lug beside it."""
    (mx, mz), h = motor_at(), SHOULDER_AXIS_Z
    x0, x1 = mx + BRACKET_BOX[0], mx + BRACKET_BOX[1]
    b = L.box("shoulder-motor-bracket", x0, x1, *BRACKET_Y, -h, mz + BRACKET_BOX[3])
    L.union(b, L.box("foot", x0, x1, BRACKET_FOOT_Y[0], BRACKET_Y[0] + 0.01, -h, -h + FOOT_T))
    L.union(b, push_lug())
    L.finish(b)
    L.cut(b, cyl_y("window", mx, mz, BRACKET_WINDOW_R, BRACKET_Y[0] - 1.0, BRACKET_Y[1] + 1.0))
    for dx, dz in PLATE_MOUNT:
        L.cut(b, slot_y("slot", mx + dx, mz + dz, M3_CLEAR_R, BRACKET_Y[0] - 1.0, BRACKET_Y[1] + 1.0))
    n, yl = (-BELT_U[0], -BELT_U[1]), sum(SWAP_Y) / 2
    at = lambda d: (mx + n[0] * d, yl, mz + n[1] * d)
    L.cut(b, rod("push insert", at(LUG_D[1] - M3_INSERT_DEPTH), at(LUG_D[1] + 1.0), M3_INSERT_R, n=32))
    L.cut(b, rod("push screw", at(LUG_D[0] - 1.0), at(LUG_D[1]), M3_CLEAR_R, n=32))
    for dx, _ in BRACKET_FOOT:
        L.cut(b, L.cyl_z("foot bolt", mx + dx, sum(BRACKET_FOOT_Y) / 2, M3_CLEAR_R, -h - 1.0, -h + FOOT_T + 1.0, n=32))
    PRINT_POSE["shoulder-motor-bracket"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (-mx, 0, BRACKET_Y[1]))
    return b


_ARM = {}


def swept_upper_arm(psis):
    if "arm" not in _ARM:
        _ARM["arm"] = concat(list(upper_arm_moving().values()), "upper arm")
    out = []
    for p in psis:
        c = copy(_ARM["arm"], f"upper arm {p}"); c.data.transform(rot_shoulder(p)); out.append(c)
    return out


def material_round(o, centre, axis, r, n=8):
    """Least material round a hole of radius r at centre, by rays outwards from its edge square to its axis."""
    axis = Vector(axis).normalized()
    a = axis.orthogonal().normalized(); b = axis.cross(a)
    t, c, out = tree(o), Vector(centre), []
    for k in range(n):
        th = 2 * math.pi * (k + 0.37) / n
        u = a * math.cos(th) + b * math.sin(th)
        loc, nrm, _, d = t.ray_cast(c + u * (r + 0.02), u)   # just off the hole's own facets
        assert loc is not None and nrm.dot(u) > 0, ("hole breaks into a void", centre, k)
        out.append(d + 0.02)
    return min(out)


def bounds(vs, pad):
    return [min(p[i] for p in vs) - pad for i in range(3)], [max(p[i] for p in vs) + pad for i in range(3)]


def inside(p, box):
    return all(box[0][i] <= p[i] <= box[1][i] for i in range(3))


def sweep_gap(arm, tf, fixed_verts, fixed_box):
    """Least gap between the swept arm and the fixed body, both ways round, near each other only."""
    av = [v.co for v in arm.data.vertices]
    ta = tree(arm)
    if ta.overlap(tf):
        return 0.0
    arm_box = bounds(av, 10.0)
    gaps = [ta.find_nearest(p)[3] for p in fixed_verts if inside(p, arm_box)] + [tf.find_nearest(p)[3] for p in av if inside(p, fixed_box)]
    return min(gaps) if gaps else 99.0


def check_body():
    names = ("body-wall-A", "body-wall-B", "compact-cage", "shoulder-stop-collar")
    wa, wb, cage, col = (PARTS[n] for n in names)
    ha, hb, op = PARTS["shoulder-hub-a"], PARTS["shoulder-hub-b"], PARTS["shoulder-output-plate"]
    for n in names:
        part_ok(n); on_bed(n)
    rounds = {}
    for w, side in ((wa, "A"), (wb, "B")):
        sgn = 1 if side == "A" else -1
        y_in, y_brg = WALL_6810_Y[side]
        seat = radial_r(w, (y_in + y_brg) / 2, inward=False)
        assert B6810[1] <= seat <= B6810[1] + 0.1, ("wall seat", side, seat)
        depth = ray_len(w, (31.8, y_in - sgn * 1.0, 0), (0, sgn, 0)) - 1.0
        assert abs(depth - B6810[2]) < 0.05, ("wall seat depth", side, depth)
        lip = radial_r(w, y_brg + sgn * E.LIP_T / 2, inward=False)
        assert HUB_SHOULDER_R + 0.5 <= lip <= WALL_LIP_R + 0.01, ("wall lip", side, lip)
        assert abs(min(v.co.z for v in w.data.vertices) + SHOULDER_AXIS_Z) < 0.01, ("wall not on the turntable", side)
        rs = [material_round(w, (0, (y_in + y_brg) / 2, 0), (0, 1, 0), SEAT_R)]
        assert len(WALL_FOOT[side]) >= 4, ("wall feet", side)
        for x, y in WALL_FOOT[side]:
            assert ray_len(w, (x, y, -SHOULDER_AXIS_Z + FOOT_T + 1.0), (0, 0, -1)) is None, ("foot hole blocked", side, x)
            rs.append(material_round(w, (x, y, -SHOULDER_AXIS_Z + FOOT_T / 2), (0, 0, 1), M3_CLEAR_R))
        if side == "A":
            for a in CAGE_SCREW_ANGLES:
                x, z = polar(CAGE_SCREW_R, a)
                rs.append(material_round(w, (x, WALL_Y["A"][1] - M3_INSERT_DEPTH / 2, z), (0, 1, 0), M3_INSERT_R))
        rounds[side] = round(min(rs), 2)
        assert rounds[side] >= BODY_MIN, ("material round a wall's seat or holes", side, rs)
    for h, w, side in ((ha, wa, "A"), (hb, wb, "B")):
        assert overlap(h, w) < 0.05, ("hub hits its wall", side)
    # The compact on its cage, the cage on wall A.
    cp = compact_posed()
    for o, n in ((wa, "wall A"), (ha, "hub A"), (op, "output plate"), (cage, "cage")):
        assert overlap(cp, o) < 0.05, ("compact hits", n)
    for o, n in ((wa, "wall A"), (ha, "hub A"), (op, "output plate")):
        assert overlap(cage, o) < 0.05, ("cage hits", n)
    assert touching(cage, wa), "cage not on wall A"
    assert touching(cp, cage), "compact not on its cage"
    assert abs(max(v.co.y for v in op.data.vertices) - COMPACT_Y) < 0.01, "output plate not on the compact's carrier"
    assert abs(min(v.co.y for v in cp.data.vertices) - HOUSING_FRONT_Y) < 0.01, "compact's front face"
    bore = radial_r(cp, HOUSING_FRONT_Y + 0.5, inward=False)
    assert CAGE_BORE_R[1] >= bore + 0.3, ("cage bore under the carrier", bore)
    tip = HOUSING_FRONT_Y - (COMPACT_BOLT_L - F.HOUSING_L)
    assert COMPACT_BOLT_L - F.HOUSING_L >= M3_INSERT_DEPTH + 0.5 and tip >= CAGE_Y[0] + 0.3, ("compact bolts into the cage", tip)
    cage_rs = []
    for a in F.BOLT_ANGLES:
        x, z = polar(F.BOLT_R, a)
        assert ray_len(cage, (x, CAGE_Y[1] + 1.0, z), (0, -1, 0)) is None, ("compact bolt hole blocked", a)
        d = ray_len(cage, (x + 1.85, CAGE_Y[1] + 1.0, z), (0, -1, 0))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("compact bolt insert", a, d)
        cage_rs.append(material_round(cage, (x, CAGE_Y[1] - M3_INSERT_DEPTH / 2, z), (0, 1, 0), M3_INSERT_R))
    assert min(cage_rs) >= BODY_MIN, ("material round the cage's inserts", cage_rs)
    cage_t = CAGE_Y[1] - CAGE_Y[0]
    assert 3.0 <= CAGE_SCREW_L - cage_t <= M3_INSERT_DEPTH, ("cage screws into wall A", CAGE_SCREW_L - cage_t)
    for a in CAGE_SCREW_ANGLES:
        x, z = polar(CAGE_SCREW_R, a)
        assert ray_len(cage, (x, CAGE_Y[1] + 1.0, z), (0, -1, 0)) is None, ("cage screw hole blocked", a)
        d = ray_len(wa, (x, CAGE_Y[0] + 1.0, z), (0, -1, 0)) - 1.0
        assert d >= CAGE_SCREW_L - cage_t + 0.5, ("cage screw bottoms in wall A", a, d)
    gap80 = PULLEY80_Y - (COMPACT_REAR_Y + BOLT_HEAD_H)
    assert gap80 >= 1.0 - 1e-6, ("80T on the compact's bolt heads", gap80)
    assert max(v.co.y for v in cp.data.vertices) <= PULLEY80_Y - 1.0 + 0.01, "80T on the compact"
    worst, low = sweep([copy(o, "f") for o in (wa, wb, cage, cp)] + [pulley80_envelope()] +
                       [shoulder_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)], "body")
    assert worst >= 2.0, ("upper arm within 2 of the body", worst)
    assert low >= 2.0, ("upper arm within 2 of the turntable", low)
    check_stops(col, wb, hb)
    assert SHOULDER_AXIS_Z >= B6810[1] + 3.0, "shoulder axis too low for the walls' seats"
    REPORT.update({"shoulder_min_gap_mm": round(worst, 2), "arm_above_turntable_mm": round(low, 1), "SHOULDER_AXIS_Z": SHOULDER_AXIS_Z,
                   "rod_out_mm": round(ROD_OUT, 1), "pulley80_y": PULLEY80_Y, "shoulder_belt_plane_y": SHOULDER_BELT_PLANE_Y,
                   "compact_y": COMPACT_Y, "wall_material_mm": rounds, "cage_material_mm": round(min(cage_rs), 2),
                   "housing_bore_r": round(bore, 2)})
    REPORT["bolts"].update({"compact to cage (R30, into inserts)": COMPACT_BOLT_L, "cage to wall A": CAGE_SCREW_L,
                            "wall feet into the turntable": FOOT_BOLT_L, "stop collar to hub B": COLLAR_SCREW_L})
    bpy.data.objects.remove(cp)


def sweep(objs, what):
    """The upper arm at every degree between the stops against objs (consumed): least gap, and least height above the turntable."""
    fixed = concat(objs, what)
    fixed_verts = [v.co.copy() for v in fixed.data.vertices]
    fixed_box, tf = bounds(fixed_verts, 10.0), tree(fixed)
    worst, low = math.inf, math.inf
    for psi in range(int(PSI_STOPS[0]), int(PSI_STOPS[1]) + 1):
        arm = swept_upper_arm([psi])[0]
        g = sweep_gap(arm, tf, fixed_verts, fixed_box)
        assert g > 0.0, ("upper arm hits the " + what, psi)
        worst = min(worst, g)
        low = min(low, min(v.co.z for v in arm.data.vertices) + SHOULDER_AXIS_Z)
        bpy.data.objects.remove(arm)
    bpy.data.objects.remove(fixed)
    return worst, low


def moved(o, slot, name):
    """A copy of o (built at slot 0) slid along the belt line."""
    c = copy(o, name)
    c.data.transform(Matrix.Translation((slot * BELT_U[0], 0, slot * BELT_U[1])))
    return c


def bore_r_at(o, cx, cz, y):
    rs = []
    for k in range(24):
        a = 2 * math.pi * (k + 0.37) / 24
        rs.append(ray_len(o, (cx, y, cz), (math.cos(a), 0, math.sin(a))))
    return sum(rs) / len(rs)


def check_shoulder_drive():
    brk = PARTS["shoulder-motor-bracket"]
    plates = {k: PARTS[f"shoulder-motor-plate-{k}"] for k in MOTORS}
    walls, hubs = [PARTS["body-wall-A"], PARTS["body-wall-B"]], [PARTS["shoulder-hub-a"], PARTS["shoulder-hub-b"]]
    for n in ["shoulder-motor-bracket"] + [f"shoulder-motor-plate-{k}" for k in MOTORS]:
        part_ok(n); on_bed(n)
    mx, mz = motor_at()
    ym = sum(SWAP_Y) / 2
    for k, p in plates.items():
        m = MOTORS[k]
        for dx, dz in PLATE_MOUNT:
            assert ray_len(p, (mx + dx, SWAP_Y[0] - 1.0, mz + dz), (0, 1, 0)) is None, ("outer pattern hole", k, dx, dz)
            assert material_round(p, (mx + dx, ym, mz + dz), (0, 1, 0), M3_INSERT_R) >= 1.2, ("outer pattern insert wall", k)
        for sx in (-1, 1):
            for sz in (-1, 1):
                x, z = mx + sx * m["hole"], mz + sz * m["hole"]
                assert ray_len(p, (x, SWAP_Y[0] - 1.0, z), (0, 1, 0)) is None, ("motor hole", k)
                assert bore_r_at(p, x, z, ym) >= m["hole_r"] - 0.05, ("motor hole size", k)
        pilot = bore_r_at(p, mx, mz, ym)
        assert pilot >= m["pilot_r"] - 0.05, ("pilot", k, pilot)
        assert SWAP_Y[0] + m["shaft"] >= PULLEY80_Y + E.PULLEY_HUB / 2 + 1.5, ("shaft short of the 20T's set screw", k)
    belts = {}
    for s in (-MOTOR_SLOT, 0.0, MOTOR_SLOT):
        x, z = motor_at(s)
        belts[s] = round(math.hypot(x, z), 2)
        assert abs(belts[s] - SHOULDER_BELT_C - s) <= 0.1, ("belt centres", s, belts[s])
    cp = compact_posed()
    p80 = posed_stl(os.path.join(OUT, "shoulder-pulley-80T.stl"), "80T",
                    Matrix.Translation((0, PULLEY80_Y + E.PULLEY_H, 0)) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    gap80 = min(v.co.y for v in p80.data.vertices) - (COMPACT_REAR_Y + BOLT_HEAD_H)
    assert 1.0 - 1e-6 <= gap80 <= 1.2, ("80T's inside face to the compact's bolt heads", gap80)
    assert overlap(p80, cp) < 0.05, "80T hits the compact"
    lug_gaps, reach = {}, {}
    for s in (-MOTOR_SLOT, MOTOR_SLOT):
        for k in MOTORS:
            box, pl = shoulder_motor_box(k, s), moved(plates[k], s, "plate")
            for o, n in zip(walls + hubs + [brk, cp], ("wall A", "wall B", "hub A", "hub B", "bracket", "compact")):
                assert overlap(box, o) < 0.05, ("motor box hits", n, k, s)
            assert min(v.co.z for v in box.data.vertices) >= -SHOULDER_AXIS_Z + 2.0, ("motor on the turntable", k, s)
            assert overlap(pl, brk) < 0.05 and touching(pl, brk), ("swap plate on the bracket", k, s)
            assert overlap(pl, box) < 0.05 and touching(pl, box), ("motor on its swap plate", k, s)
            lug = push_lug()
            lug_gaps[f"{k} {s:+.0f}"] = round(min_gap(pl, lug), 2)
            for o in (box, pl, lug):
                bpy.data.objects.remove(o)
        belt = shoulder_belt_envelope(s)
        for o, n in ((walls[0], "wall A"), (cp, "compact"), (brk, "bracket")):
            assert overlap(belt, o) < 0.05, ("shoulder belt hits", n, s)
        bpy.data.objects.remove(belt)
        tip = LUG_D[0] - (PUSH_SCREW_L - (LUG_D[1] - LUG_D[0]))
        reach[s] = round(CHAMFER_D - s - tip, 2)
    assert min(lug_gaps.values()) >= 0.5, ("swap plate on the push-screw lug", lug_gaps)
    assert min(reach.values()) >= 0.0, ("push screw can't reach the plate at full travel", reach)
    engage = SWAP_SCREW_L - (BRACKET_Y[1] - BRACKET_Y[0])
    assert 3.0 <= engage <= SWAP_Y[1] - SWAP_Y[0], ("swap plate screws", engage)
    worst, low = sweep([shoulder_motor_box(k, s) for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)] +
                       [shoulder_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)] + [copy(brk, "b")] +
                       [moved(plates[k], s, "p") for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)], "shoulder drive")
    assert worst >= 2.0, ("upper arm within 2 of the shoulder drive", worst)
    REPORT.update({"shoulder_motor_at": [round(c_, 2) for c_ in SHOULDER_MOTOR_AT], "shoulder_motor_deg": SHOULDER_MOTOR_DEG,
                   "shoulder_belt_centres": belts, "pulley80_gap_mm": round(gap80, 2), "push_lug_gap_mm": lug_gaps,
                   "push_reach_mm": reach, "drive_min_gap_mm": round(worst, 2)})
    REPORT["bolts"].update({"swap plate to bracket (into the plate's inserts)": SWAP_SCREW_L, "push screw": PUSH_SCREW_L,
                            "bracket foot into the turntable": FOOT_BOLT_L})
    for o in (cp, p80):
        bpy.data.objects.remove(o)


def check_stops(col, wb, hb):
    tab = stop_tab(); blocks = join(stop_blocks(), "blocks")
    gaps = {}
    for psi in (PSI_RANGE[0], PSI_RANGE[1], PSI_STOPS[0], PSI_STOPS[1], PSI_STOPS[0] + 0.3, PSI_STOPS[1] - 0.3):
        t = copy(tab, "t"); t.data.transform(rot_shoulder(psi))
        gaps[psi] = round(min_gap(t, blocks), 2)
        bpy.data.objects.remove(t)
    assert gaps[PSI_STOPS[0]] <= 0.05 and gaps[PSI_STOPS[1]] <= 0.05, ("tab doesn't meet the stops", gaps)
    assert gaps[PSI_STOPS[0] + 0.3] > 0.0 and gaps[PSI_STOPS[1] - 0.3] > 0.0, ("tab meets a stop more than 0.3 early", gaps)
    assert gaps[PSI_RANGE[0]] >= 1.0 and gaps[PSI_RANGE[1]] >= 1.0, ("stops within 1 mm inside the range", gaps)
    assert STOP_BLOCK_DEG >= 30.0, "stop blocks under 30 degrees"
    for psi in range(int(PSI_RANGE[0]), int(PSI_RANGE[1]) + 1):
        t = copy(tab, "t"); t.data.transform(rot_shoulder(psi))
        assert not tree(t).overlap(tree(blocks)), ("tab hits a stop inside the range", psi)
        bpy.data.objects.remove(t)
    stall_n = SHOULDER_DESIGN_NMM / ((STOP_R[0] + STOP_R[1]) / 2)
    tang = math.radians(STOP_BLOCK_DEG) * STOP_R[0]
    lever = abs(TAB_Y[1] - TAB_Y[0]) / 2 + 0.5
    stop_mpa = stall_n * lever / ((STOP_R[1] - STOP_R[0]) * tang ** 2 / 6)
    assert stop_mpa <= PRINTED_MPA, ("stop block bending, across layers", round(stop_mpa, 1))
    key_mpa = SHOULDER_DESIGN_NMM / ((HUB_BORE_R + B6810[0]) / 2) / len(KEY_ANGLES) / (KEY_DEPTH_Y * (B6810[0] - HUB_BORE_R))
    assert key_mpa <= PRINTED_MPA, ("stop collar's tongues", round(key_mpa, 1))
    for o, n in ((wb, "wall B"), (hb, "hub B")):
        assert overlap(col, o) < 0.05, ("stop collar hits", n)
    assert touching(col, hb), "stop collar doesn't seat on hub B"
    assert max(v.co.y for v in col.data.vertices) <= WALL_6810_Y["B"][1] + 0.01, "stop collar reaches into the 6810"
    for a in KEY_ANGLES:
        kx, kz = polar((HUB_BORE_R + B6810[0]) / 2, a)
        tip = ray_len(col, (kx, HUB_Y[0] + KEY_DEPTH_Y + 1.0, kz), (0, -1, 0))
        assert tip is not None and abs(tip - 1.3) < 0.05, ("tongue doesn't fill the key slot", a, tip)
        slot = ray_len(hb, (kx, HUB_Y[0] - 1.0, kz), (0, 1, 0))
        assert slot is not None and abs(slot - 1.0 - KEY_DEPTH_Y) < 0.05, ("key slot in hub B", a, slot)
    walls = []
    for a in COLLAR_SCREW_ANGLES:
        x, z = polar(COLLAR_SCREW_R, a)
        d = ray_len(hb, (x + 1.85, HUB_Y[0] - 1.0, z), (0, 1, 0))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("collar insert in hub B", a, d)
        walls.append(material_round(hb, (x, HUB_Y[0] + M3_INSERT_DEPTH / 2, z), (0, 1, 0), M3_INSERT_R))
    assert min(walls) >= WALL_MIN, ("material round the collar's inserts", walls)
    engage = COLLAR_SCREW_L - STOP_COLLAR_FLANGE - 0.3
    assert 3.0 <= engage <= M3_INSERT_DEPTH, ("collar screws", engage)
    mx, mz = polar(MAGNET_AT_R, TAB_PHI)
    floor = ray_len(col, (mx, TAB_Y[0] + 1.0, mz), (0, -1, 0)) - 1.0
    magnet = rot_shoulder(0.0) @ Vector((mx, TAB_Y[0] - floor + MAGNET_D, mz))
    sensor_face = Vector((mx, WALL_Y["B"][1], mz))
    assert math.hypot(magnet.x - sensor_face.x, magnet.z - sensor_face.z) < 0.5, ("magnet not over the sensor at home", magnet)
    gap = abs(magnet.y - sensor_face.y)
    assert 1.0 <= gap <= 2.0, ("Hall gap at home", gap)
    assert ray_len(wb, (mx, WALL_Y["B"][1] - 1.0, mz), (0, 1, 0)) >= 1.0 + SENSOR[2], "sensor pocket missing"
    REPORT.update({"stop_gaps_mm": gaps, "stop_block_mpa": round(stop_mpa, 1), "collar_key_mpa": round(key_mpa, 1),
                   "collar_insert_wall_mm": round(min(walls), 2), "hall_gap_mm": round(gap, 2)})
    for o in (tab, blocks):
        bpy.data.objects.remove(o)


def prism_z(name, pts, z0, z1):
    """A prism through z on a polygon of (x, y) points."""
    o = prism_y(name, [(x, y) for x, y in pts], -z1, -z0)
    o.data.transform(basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, 0)))
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def sector_z(name, r0, r1, a0, a1, z0, z1, n=24):
    angs = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    return prism_z(name, [polar(r1, t) for t in angs] + [polar(r0, t) for t in angs[::-1]], z0, z1)


def bracket_feet():
    mx = motor_at()[0]
    return [(mx + dx, sum(BRACKET_FOOT_Y) / 2) for dx, _ in BRACKET_FOOT]


def phi_tab():
    return sector_z("phi tab", PHI_R[0], PHI_R[1], PHI_TAB_DEG - PHI_HALF, PHI_TAB_DEG + PHI_HALF, PHI_TAB_Z[1], PHI_TAB_Z[0] + 0.01)


def phi_block():
    return sector_z("phi block", PHI_R[0], PHI_R[1], -PHI_HALF, PHI_HALF, BASE_TOP_Z - 0.01, PHI_BLOCK_TOP)


def hall_xy():
    r, a, _ = BASE_HALL["magnet"]
    return polar(r, a)


def turntable():
    """Plate under the walls, the bracket and the electronics; hub on the two 6810s; the base stop's tab and the Hall magnet under it."""
    x0, x1, y0, y1 = TURNTABLE_XY
    zt, zb = TURNTABLE_Z, TURNTABLE_Z - TURNTABLE_T
    t = L.box("turntable", x0, x1, y0, y1, zb, zt)
    L.union(t, L.cyl_z("hub", 0, 0, TT_HUB_R, TT_HUB_Z0, zb + 0.01, n=192))
    L.union(t, phi_tab())
    L.finish(t)
    L.cut(t, L.cyl_z("seats", 0, 0, SEAT_R, TT_HUB_Z0 - 1.0, BASE_6810_Z[0] + B6810[2], n=192))
    L.cut(t, L.cyl_z("lip", 0, 0, TT_LIP_R, TT_HUB_Z0 - 1.0, zt + 1.0, n=192))
    for a in RING_SCREW_ANGLES:
        x, y = polar(RING_SCREW_R, a)
        L.cut(t, L.cyl_z("ring insert", x, y, M3_INSERT_R, TT_HUB_Z0 - 1.0, TT_HUB_Z0 + M3_INSERT_DEPTH + 2.0, n=32))
    for x, y in WALL_FOOT["A"] + WALL_FOOT["B"] + bracket_feet() + ELECTRONICS_PILOTS:
        L.cut(t, L.cyl_z("insert", x, y, M3_INSERT_R, zt - M3_INSERT_DEPTH, zt + 1.0, n=32))
    mx, my = hall_xy()
    L.cut(t, L.cyl_z("magnet", mx, my, MAGNET_R + 0.1, PHI_TAB_Z[1] - 1.0, PHI_TAB_Z[1] + MAGNET_RECESS + MAGNET_D, n=32))
    PRINT_POSE["turntable"] = basis((1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, zt))
    return t


def base_ring():
    """The 130T under the turntable's hub, teeth as htd3m_pulley's; its lip holds the lower 6810's outer ring."""
    r = od_r(RING_TEETH)
    g = L.cyl_z("base-ring-130T", 0, 0, r, RING_Z[0] - 0.01, RING_Z[1] + 0.01, n=720)
    for k in range(RING_TEETH):
        a = 2 * math.pi * k / RING_TEETH; c = r - GROOVE_DEPTH + GROOVE_R
        L.cut(g, L.cyl_z("groove", c * math.cos(a), c * math.sin(a), GROOVE_R, RING_Z[0] - 1.0, RING_Z[1] + 1.0, n=24))
    L.union(g, L.cyl_z("flange", 0, 0, r + FLANGE_LIP, RING_Z[1], TT_HUB_Z0, n=720))
    L.union(g, L.cyl_between("cone", (0, 0, RING_Z[0] + 0.01), (0, 0, RING_Z0), r - GROOVE_DEPTH, n=720, r_end=r + FLANGE_LIP))
    L.finish(g)
    L.cut(g, L.cyl_z("bore", 0, 0, RING_LIP_R, RING_Z0 - 1.0, TT_HUB_Z0 + 1.0, n=192))
    for a in RING_SCREW_ANGLES:
        x, y = polar(RING_SCREW_R, a)
        L.cut(g, L.cyl_z("screw", x, y, M3_CLEAR_R, RING_Z0 - 1.0, TT_HUB_Z0 + 1.0, n=32))
    PRINT_POSE["base-ring-130T"] = basis((1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, TT_HUB_Z0))
    return g


def spigot_spacer():
    s = L.cyl_z("spigot-spacer", 0, 0, SPACER_R, *SPACER_Y, n=192)
    L.cut(s, L.cyl_z("bore", 0, 0, SPIGOT["r"] + 0.1, SPACER_Y[0] - 1.0, SPACER_Y[1] + 1.0, n=192))
    PRINT_POSE["spigot-spacer"] = Matrix.Translation((0, 0, -SPACER_Y[0]))
    return s


def spigot_cap():
    z0 = BASE_6810_Z[0] + B6810[2]
    c = L.cyl_z("spigot-cap", 0, 0, CAP_R, z0, z0 + CAP_T, n=192)
    L.cut(c, L.cyl_z("bore", 0, 0, 12.0, z0 - 1.0, z0 + CAP_T + 1.0, n=96))
    for a in CAP_SCREW_ANGLES:
        x, y = polar(CAP_SCREW_R, a)
        L.cut(c, L.cyl_z("screw", x, y, M3_CLEAR_R, z0 - 1.0, z0 + CAP_T + 1.0, n=32))
    PRINT_POSE["spigot-cap"] = Matrix.Translation((0, 0, -z0))
    return c


def base_lug():
    r0, t, hw, h = BASE_LUG
    ux, uy = BASE_U
    return prism_z("base lug", [((r0 - t) * ux + s * hw * -uy, (r0 - t) * uy + s * hw * ux) for s in (-1, 1)] +
                   [(r0 * ux + s * hw * -uy, r0 * uy + s * hw * ux) for s in (1, -1)], BASE_TOP_Z - 0.01, BASE_TOP_Z + h)


def base_motor_box(slot):
    x, y = base_motor_at(slot)
    h = MOTORS["17"]["sq"] / 2
    return L.box("base motor", x - h, x + h, y - h, y + h, BASE_TOP_Z - BASE_MOTOR_L, BASE_TOP_Z)


def base_belt_envelope(slot):
    """The belt between the 130T and the 20T (not the ring's inside), and the 20T, with the motor at slot."""
    x, y = base_motor_at(slot)
    z0, z1 = RING_Z[0] - 1.5, RING_Z[1] + 1.5
    band = hull([L.cyl_z("a", 0, 0, od_r(RING_TEETH) + E.BELT_T, z0, z1, n=192), L.cyl_z("b", x, y, E.R20_OD + E.BELT_T, z0, z1)], "base belt")
    L.cut(band, L.cyl_z("ring", 0, 0, od_r(RING_TEETH) - GROOVE_DEPTH - 0.5, z0 - 1.0, z1 + 1.0, n=192))
    zp = BASE_TOP_Z + BASE_PLATE_T
    L.union(band, L.cyl_z("20T hub", x, y, 9.5, zp + 1.0, zp + 1.0 + E.PULLEY_HUB + 0.01))
    L.union(band, L.cyl_z("20T teeth", x, y, E.R20_OD + 1.5, zp + 1.0 + E.PULLEY_HUB, zp + 1.0 + E.PULLEY_H))
    return band


def slot_z(name, x, y, r, z0, z1, n=16):
    pts = []
    for e in (1, -1):
        cx, cy = x + e * MOTOR_SLOT * BASE_U[0], y + e * MOTOR_SLOT * BASE_U[1]
        base = math.degrees(math.atan2(BASE_U[1], BASE_U[0])) + (0 if e > 0 else 180)
        pts += [(cx + r * math.cos(math.radians(base - 90 + 180 * k / n)), cy + r * math.sin(math.radians(base - 90 + 180 * k / n))) for k in range(n + 1)]
    return prism_z(name, pts, z0, z1)


def moved_base(o, slot):
    c = copy(o, "plate")
    c.data.transform(Matrix.Translation((slot * BASE_U[0], slot * BASE_U[1], 0)))
    return c


def fixed_base():
    """Disc and motor arm, the spigot with its shoulder, the stop block, the Hall post and the base motor's push lug."""
    zt, zb = BASE_TOP_Z, BASE_TOP_Z - BASE_T
    f = L.cyl_z("fixed-base", 0, 0, BASE_DISC_R, zb, zt, n=192)
    L.union(f, L.box("arm", -BASE_ARM_HALF, BASE_ARM_HALF, BASE_ARM_END, 0.0, zb, zt))
    L.union(f, L.cyl_z("shoulder", 0, 0, SPIGOT["shoulder_r"], zt - 0.01, TT_HUB_Z0, n=192))
    L.union(f, L.cyl_z("spigot", 0, 0, SPIGOT["r"], TT_HUB_Z0 - 0.01, SPIGOT["top"], n=192))
    L.union(f, phi_block())
    hx, hy = hall_xy()
    L.union(f, L.box("hall post", hx - HALL_POST_HALF, hx + HALL_POST_HALF, hy - HALL_POST_HALF, hy + HALL_POST_HALF, zt - 0.01, BASE_HALL["sensor_top"]))
    L.union(f, base_lug())
    L.finish(f)
    L.cut(f, L.cyl_z("bore", 0, 0, SPIGOT["bore_r"], zb - 1.0, SPIGOT["top"] + 1.0, n=128))
    for a in CAP_SCREW_ANGLES:
        x, y = polar(CAP_SCREW_R, a)
        L.cut(f, L.cyl_z("cap insert", x, y, M3_INSERT_R, SPIGOT["top"] - M3_INSERT_DEPTH - 1.0, SPIGOT["top"] + 1.0, n=32))
    mx, my = base_motor_at()
    h = MOTORS["17"]["sq"] / 2 + 1.0
    L.cut(f, L.box("motor window", mx - h - abs(BASE_U[0]) * (MOTOR_SLOT + 1), mx + h + abs(BASE_U[0]) * (MOTOR_SLOT + 1),
                   my - h - abs(BASE_U[1]) * (MOTOR_SLOT + 1), my + h + abs(BASE_U[1]) * (MOTOR_SLOT + 1), zb - 1.0, zt + 1.0))
    for dx, dy in BASE_PLATE_INSERTS:
        L.cut(f, L.cyl_z("plate insert", mx + dx, my + dy, M3_INSERT_R, zt - M3_INSERT_DEPTH - 1.0, zt + 1.0, n=32))
    r0, t, hw, lh = BASE_LUG
    zs = zt + BASE_PLATE_T / 2
    a, b = (BASE_U[0] * (r0 - t), BASE_U[1] * (r0 - t), zs), (BASE_U[0] * r0, BASE_U[1] * r0, zs)
    ins = (BASE_U[0] * (r0 - t + M3_INSERT_DEPTH), BASE_U[1] * (r0 - t + M3_INSERT_DEPTH), zs)
    L.cut(f, rod("push insert", (BASE_U[0] * (r0 - t - 1.0), BASE_U[1] * (r0 - t - 1.0), zs), ins, M3_INSERT_R, n=32))
    L.cut(f, rod("push screw", a, (BASE_U[0] * (r0 + 1.0), BASE_U[1] * (r0 + 1.0), zs), M3_CLEAR_R, n=32))
    st = BASE_HALL["sensor_top"]
    L.cut(f, L.box("sensor pocket", hx - SENSOR[1] / 2 - 0.1, hx + SENSOR[1] / 2 + 0.1, hy - SENSOR[0] / 2 - 0.1, hy + SENSOR[0] / 2 + 0.1,
                   st - SENSOR[2] - 0.1, st + 1.0))
    L.cut(f, L.box("leads", hx - HALL_POST_HALF - 1.0, hx, hy - 1.0, hy + 1.0, st - 1.0, st + 1.0))
    leg_sockets(f)
    PRINT_POSE["fixed-base"] = Matrix.Translation((0, 0, -zb))
    return f


def base_motor_plate():
    """The base motor hangs under it through the fixed base's window; slotted along the belt, pushed by the lug's screw."""
    mx, my = base_motor_at()
    zt = BASE_TOP_Z + BASE_PLATE_T
    m = MOTORS["17"]
    p = L.box("base-motor-plate", mx - BASE_PLATE_HALF, mx + BASE_PLATE_HALF, my - BASE_PLATE_HALF, my + BASE_PLATE_HALF, BASE_TOP_Z, zt)
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.cut(p, L.cyl_z("motor screw", mx + sx * m["hole"], my + sy * m["hole"], m["hole_r"], BASE_TOP_Z - 1.0, zt + 1.0, n=32))
    for dx, dy in BASE_PLATE_INSERTS:
        L.cut(p, slot_z("slot", mx + dx, my + dy, M3_CLEAR_R, BASE_TOP_Z - 1.0, zt + 1.0))
    L.cut(p, L.cyl_z("pilot", mx, my, m["pilot_r"], BASE_TOP_Z - 1.0, zt + 1.0, n=96))   # last: off the origin, the exact solver left the screw holes open after it
    PRINT_POSE["base-motor-plate"] = Matrix.Translation((-mx, -my, -BASE_TOP_Z))
    return p


def radial_z(o, z, inward=True, r0=120.0, n=24):
    """Mean radius of o's surface at height z about the base axis, inward from r0 or out from the axis."""
    rs = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.37) / n
        u = Vector((math.cos(a), math.sin(a), 0))
        rs.append(r0 - ray_len(o, u * r0 + Vector((0, 0, z)), -u) if inward else ray_len(o, (0, 0, z), u))
    return sum(rs) / len(rs)


def grooves_at(o, z, r_od, n=2880):
    t, deep = tree(o), []
    for k in range(n):
        a = 2 * math.pi * (k + 0.37) / n
        u = Vector((math.cos(a), math.sin(a), 0))
        h = t.ray_cast(u * (r_od + 20.0) + Vector((0, 0, z)), -u)[0]
        deep.append((h - Vector((0, 0, z))).length < r_od - GROOVE_DEPTH / 2)
    return sum(1 for i in range(n) if deep[i] and not deep[i - 1])


def rot_base(phi):
    return Matrix.Rotation(math.radians(phi), 4, 'Z')


def check_base():
    names = ("turntable", "base-ring-130T", "spigot-spacer", "spigot-cap", "fixed-base", "base-motor-plate")
    tt, ring, spacer, cap, fb, bp = (PARTS[n] for n in names)
    for n in names:
        part_ok(n); on_bed(n)
    for z0 in BASE_6810_Z:
        zm = z0 + B6810[2] / 2
        s = radial_z(fb, zm)
        assert SPIGOT["r"] - 0.01 <= s <= SPIGOT["r"] + 0.1, ("spigot", zm, s)   # -0.01: the polygon's chords
        seat = radial_z(tt, zm, inward=False)
        assert B6810[1] <= seat <= B6810[1] + 0.1, ("turntable seat", zm, seat)
    for o, z, n in ((tt, BASE_6810_Z[0] + B6810[2] + 1.0, "turntable's top lip"), (ring, TT_HUB_Z0 - 0.5, "ring's lip")):
        lip = radial_z(o, z, inward=False)
        assert HUB_SHOULDER_R + 0.5 <= lip <= WALL_LIP_R + 0.01, (n, lip)
    for o, z, n in ((cap, BASE_6810_Z[0] + B6810[2] + 0.5, "cap"), (spacer, sum(SPACER_Y) / 2, "spacer"), (fb, TT_HUB_Z0 - 0.5, "spigot shoulder")):
        r = radial_z(o, z)
        assert r <= HUB_SHOULDER_R - 0.45, ("bears past the inner ring", n, r)
    assert abs(min(v.co.z for v in cap.data.vertices) - (BASE_6810_Z[0] + B6810[2])) < 0.01, "cap not on the upper inner ring"
    assert max(v.co.z for v in cap.data.vertices) <= TURNTABLE_Z - 0.5, "cap stands above the turntable"
    sp = [v.co.z for v in spacer.data.vertices]
    assert abs(min(sp) - SPACER_Y[0]) < 0.01 and abs(max(sp) - SPACER_Y[1]) < 0.01, "spacer between the inner rings"
    for o, other, n in ((tt, fb, "turntable on the fixed base"), (ring, fb, "ring on the fixed base"), (cap, tt, "cap on the turntable"),
                        (spacer, tt, "spacer on the turntable"), (ring, tt, "ring in the turntable"), (spacer, fb, "spacer on the spigot"),
                        (cap, fb, "cap in the spigot")):
        assert overlap(o, other) < 0.05, n
    hub_face = ray_len(tt, (41.0 * math.cos(0.3), 41.0 * math.sin(0.3), TT_HUB_Z0 - 1.0), (0, 0, 1))
    assert abs(max(v.co.z for v in ring.data.vertices) - TT_HUB_Z0) < 0.01 and abs(hub_face - 1.0) < 0.01, "ring not on the turntable's hub"
    g_cap = ray_len(fb, (23.5, 0, BASE_6810_Z[0] + B6810[2]), (0, 0, -1))
    assert abs(g_cap - 0.3) < 0.01, ("cap should stand 0.3 off the spigot top, on the inner ring", g_cap)
    g = grooves_at(ring, sum(RING_Z) / 2, od_r(RING_TEETH))
    od = 2 * radial_z(ring, sum(RING_Z) / 2, r0=od_r(RING_TEETH) + 20.0)
    assert g == RING_TEETH, ("ring grooves", g)
    peak = 2 * max(od_r(RING_TEETH) + 20.0 - ray_len(ring, (math.cos(a) * (od_r(RING_TEETH) + 20.0), math.sin(a) * (od_r(RING_TEETH) + 20.0), sum(RING_Z) / 2),
                                                       (-math.cos(a), -math.sin(a), 0)) for a in [2 * math.pi * k / 2880 for k in range(2880)])
    assert abs(peak - 2 * od_r(RING_TEETH)) <= 0.05, ("ring OD", peak)
    belts = {}
    for s in (-MOTOR_SLOT, 0.0, MOTOR_SLOT):
        belts[s] = round(math.hypot(*base_motor_at(s)), 2)
        assert abs(belts[s] - BASE_BELT_C - s) <= 0.1, ("base belt centres", s, belts[s])
    turning = join([tt, ring], "turning")
    for s in (-MOTOR_SLOT, MOTOR_SLOT):
        box, belt, plate = base_motor_box(s), base_belt_envelope(s), moved_base(bp, s)
        assert overlap(box, fb) < 0.05, ("base motor hits the fixed base", s)
        assert overlap(plate, fb) < 0.05 and touching(plate, fb) and touching(plate, box), ("base motor plate", s)
        assert overlap(belt, fb) < 0.05, ("base belt hits the fixed base", s)
        for phi in range(-170, 171, 10):
            t = copy(turning, "t"); t.data.transform(rot_base(phi))
            assert overlap(box, t) < 0.05, ("base motor hits the turntable", s, phi)
            tb = copy(tt, "tb"); tb.data.transform(rot_base(phi))
            assert overlap(belt, tb) < 0.05, ("base belt hits the turntable", s, phi)
            for o in (t, tb):
                bpy.data.objects.remove(o)
        lug = base_lug()
        assert min_gap(plate, lug) >= 0.5, ("base plate on its push lug", s)
        for o in (box, belt, plate, lug):
            bpy.data.objects.remove(o)
    reach = {s: round(BASE_LUG[0] - BASE_LUG[1] + BASE_PUSH_L - (BASE_BELT_C + s - BASE_PLATE_HALF), 2) for s in (-MOTOR_SLOT, MOTOR_SLOT)}
    assert min(reach.values()) >= 0.0, ("base push screw short", reach)
    tab, block = phi_tab(), phi_block()
    gaps = {}
    for phi in (PHI_RANGE[0], PHI_RANGE[1], PHI_STOPS[0], PHI_STOPS[1], PHI_STOPS[0] + 0.3, PHI_STOPS[1] - 0.3, 0.0, 90.0, -90.0):
        t = copy(tab, "t"); t.data.transform(rot_base(phi))
        gaps[phi] = round(min_gap(t, block), 2)
        bpy.data.objects.remove(t)
    assert gaps[PHI_STOPS[0]] <= 0.05 and gaps[PHI_STOPS[1]] <= 0.05, ("base stops don't meet", gaps)
    assert gaps[PHI_STOPS[0] + 0.3] > 0.0 and gaps[PHI_STOPS[1] - 0.3] > 0.0, ("base stop more than 0.3 early", gaps)
    assert min(gaps[PHI_RANGE[0]], gaps[PHI_RANGE[1]]) >= 1.0, ("base stops within 1 inside the range", gaps)
    for phi in range(int(PHI_RANGE[0]), int(PHI_RANGE[1]) + 1, 5):
        t = copy(tab, "t"); t.data.transform(rot_base(phi))
        assert not tree(t).overlap(tree(fb)), ("tab hits the fixed base", phi)
        bpy.data.objects.remove(t)
    f = BASE_DESIGN_NMM / (sum(PHI_R) / 2)
    w = 2 * math.radians(PHI_HALF) * PHI_R[0]
    mpa = {"tab": f * (PHI_TAB_Z[0] - PHI_TAB_Z[1]) / ((PHI_R[1] - PHI_R[0]) * w * w / 6),
           "block": f * (PHI_BLOCK_TOP - BASE_TOP_Z) / ((PHI_R[1] - PHI_R[0]) * w * w / 6)}
    assert max(mpa.values()) <= PRINTED_MPA, ("base stop bending", mpa)
    mr, ma, _ = BASE_HALL["magnet"]
    mx, my = mr * math.cos(math.radians(ma)), mr * math.sin(math.radians(ma))
    floor = ray_len(tt, (mx, my, PHI_TAB_Z[1] - 1.0), (0, 0, 1)) - 1.0
    magnet_face = PHI_TAB_Z[1] + floor - MAGNET_D
    sensor = PHI_TAB_Z[1] + 1.0 - ray_len(fb, (mx, my + SENSOR[0] / 2 + 1.5, PHI_TAB_Z[1] + 1.0), (0, 0, -1))   # the post's top, beside the pocket
    hall = magnet_face - sensor
    assert 1.0 <= hall <= 2.0, ("base Hall gap", hall)
    assert ray_len(fb, (mx, my, sensor + 1.0), (0, 0, -1)) >= 1.0 + SENSOR[2], "base sensor pocket missing"
    feet = []
    for x, y in WALL_FOOT["A"] + WALL_FOOT["B"] + bracket_feet():
        d = ray_len(tt, (x + 1.85, y, TURNTABLE_Z + 1.0), (0, 0, -1))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("foot insert", x, y, d)
        feet.append(material_round(tt, (x, y, TURNTABLE_Z - M3_INSERT_DEPTH / 2), (0, 0, 1), M3_INSERT_R))
    assert min(feet) >= 2.0, ("foot insert wall", feet)
    x0, x1, y0, y1, hgt = ELECTRONICS_AREA
    area = L.box("electronics", x0, x1, y0, y1, TURNTABLE_Z, TURNTABLE_Z + hgt)
    near = [PARTS["body-wall-A"], PARTS["body-wall-B"], PARTS["shoulder-motor-bracket"]]
    near += [shoulder_motor_box(k, s) for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)]
    near += [moved(PARTS[f"shoulder-motor-plate-{k}"], s, "p") for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)]
    near += [shoulder_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)]
    for o in near:
        assert overlap(area, o) < 0.05, ("electronics area hits", o.name)
    assert all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in ELECTRONICS_PILOTS), "electronics pilot outside the area"
    for x, y in ELECTRONICS_PILOTS:
        d = ray_len(tt, (x + 1.85, y, TURNTABLE_Z + 1.0), (0, 0, -1))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("electronics pilot", x, y, d)
        feet.append(material_round(tt, (x, y, TURNTABLE_Z - M3_INSERT_DEPTH / 2), (0, 0, 1), M3_INSERT_R))
    assert min(feet) >= 2.0, ("insert wall", feet)
    REPORT.update({"base_belt_centres": belts, "base_push_reach_mm": reach, "phi_stop_gaps_mm": gaps,
                   "phi_stop_mpa": {k: round(v, 1) for k, v in mpa.items()}, "base_hall_gap_mm": round(hall, 2),
                   "turntable_insert_wall_mm": round(min(feet), 2), "ring_grooves": g, "ring_od": round(peak, 2),
                   "base_motor_at": [round(c, 2) for c in BASE_MOTOR_AT], "turntable_z": TURNTABLE_Z, "base_top_z": BASE_TOP_Z,
                   "fixed_base_lowest_z": round(min(v.co.z for v in fb.data.vertices), 2)})
    REPORT["bolts"].update({"spigot cap": CAP_SCREW_L, "ring to turntable hub": RING_SCREW_L, "base motor plate": BASE_PLATE_SCREW_L,
                            "base push screw": BASE_PUSH_L})
    for o in [turning, tab, block, area] + near[3:]:
        bpy.data.objects.remove(o)


def V(t):
    return Vector(t)


def pinch_dir(d):
    """Square to the leg, pointing up: the pinch screw goes in from above."""
    up = Vector((0, 0, 1)); d = Vector(d)
    return (up - d * up.dot(d)).normalized()


def leg_sockets(f):
    """Bosses on the fixed base's rim with a buttress down to the bed, then the sockets and the pinch inserts."""
    for phi in LEG_PHI:
        m, s, _ = (V(p) for p in leg(phi)); d = V(leg_dir(phi))
        boss = rod("socket boss", s - d * SOCKET["floor"], m, SOCKET["boss_r"])
        foot = copy(boss, "buttress foot")
        bm = bmesh.new(); bm.from_mesh(foot.data)
        for v in bm.verts:
            v.co.z = BASE_TOP_Z - BASE_T
        bm.to_mesh(foot.data); bm.free()
        L.union(f, hull([boss, foot], "socket"))
    L.finish(f)
    for phi in LEG_PHI:
        m, s, _ = (V(p) for p in leg(phi)); d = V(leg_dir(phi)); n = pinch_dir(d)
        L.cut(f, rod("socket", s, m + d * 30.0, SOCKET["r"], n=64))   # on through the buttress's foot, which reaches past the mouth
        c = m - d * PINCH_AT
        L.cut(f, rod("pinch insert", c + n * (SOCKET["boss_r"] - M3_INSERT_DEPTH), c + n * (SOCKET["boss_r"] + 1.0), M3_INSERT_R, n=32))
        L.cut(f, rod("pinch screw", c, c + n * (SOCKET["boss_r"] - M3_INSERT_DEPTH + 0.5), M3_CLEAR_R, n=32))


def foot_part():
    """Over the tube's lower end (built for the leg at LEG_PHI[0]): a sleeve, a level pad face with the TPU pad's recess, a clamp tab."""
    _, _, f = (V(p) for p in leg(LEG_PHI[0])); d = V(leg_dir(LEG_PHI[0]))
    boss = rod("sleeve boss", f - d * FOOT["sleeve"], f + d * FOOT["floor"], FOOT["boss_r"])
    disc = L.cyl_z("pad disc", f.x, f.y, FOOT["pad_r"], FOOT_BOTTOM_Z, FOOT_BOTTOM_Z + FOOT["pad_t"], n=96)
    o = hull([boss, disc], "foot")
    h = Vector((d.x, d.y, 0)).normalized(); t = Vector((-h.y, h.x, 0))
    a, b, tz = FOOT["pad_r"] - 4.0, FOOT["pad_r"] - 4.0 + CLAMP_TAB[0], CLAMP_TAB[2]
    pts = [(f.x + h.x * u + t.x * w, f.y + h.y * u + t.y * w) for u, w in ((a, -CLAMP_TAB[1] / 2), (b, -CLAMP_TAB[1] / 2), (b, CLAMP_TAB[1] / 2), (a, CLAMP_TAB[1] / 2))]
    L.union(o, prism_z("clamp tab", pts, FOOT_BOTTOM_Z, FOOT_BOTTOM_Z + tz))
    L.finish(o)
    L.cut(o, rod("sleeve", f, f - d * (FOOT["sleeve"] + 1.0), SOCKET["r"], n=64))
    L.cut(o, L.cyl_z("pad recess", f.x, f.y, PAD_R + 0.2, FOOT_BOTTOM_Z - 1.0, FOOT_BOTTOM_Z + PAD_RECESS, n=96))
    PRINT_POSE["foot"] = Matrix.Translation((0, 0, -FOOT_BOTTOM_Z)) @ Matrix.Rotation(-math.radians(LEG_PHI[0]), 4, 'Z') @ Matrix.Translation((-f.x, -f.y, 0))
    return o


def foot_pad():
    _, _, f = leg(LEG_PHI[0])
    p = L.cyl_z("foot-pad", f[0], f[1], PAD_R, FOOT_PAD_Z, FOOT_PAD_Z + PAD_T, n=96)
    PRINT_POSE["foot-pad"] = Matrix.Translation((-f[0], -f[1], -FOOT_PAD_Z))
    return p


def check_legs():
    fb, ft, pd = PARTS["fixed-base"], PARTS["foot"], PARTS["foot-pad"]
    for n in ("foot", "foot-pad"):
        part_ok(n); on_bed(n)
    walls, pinch, pads, level = [], [], [], []
    tt = join([PARTS["turntable"], PARTS["base-ring-130T"]], "turning")
    others = [base_motor_box(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)] + [base_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)]
    for phi in LEG_PHI:
        m, s, f = (V(p) for p in leg(phi)); d = V(leg_dir(phi)); n = pinch_dir(d)
        depth = ray_len(fb, m + d * 1.0, -d) - 1.0
        assert abs(depth - SOCKET["depth"]) <= 0.1, ("socket depth", phi, depth)
        a = d.orthogonal().normalized(); b = d.cross(a); c = m - d * 6.0
        r = sum(ray_len(fb, c, a * math.cos(2 * math.pi * (k + 0.37) / 24) + b * math.sin(2 * math.pi * (k + 0.37) / 24)) for k in range(24)) / 24
        assert SOCKET["r"] - 0.01 <= r <= SOCKET["r"] + 0.1, ("socket radius", phi, r)
        walls.append(min(material_round(fb, m - d * z, d, SOCKET["r"]) for z in (4.0, 20.0)))
        ci = m - d * PINCH_AT
        pinch.append(material_round(fb, ci + n * (SOCKET["boss_r"] - M3_INSERT_DEPTH / 2), n, M3_INSERT_R))
        through = ray_len(fb, ci + n * (SOCKET["boss_r"] + 1.0), -n)
        assert through is not None and through >= 1.0 + SOCKET["boss_r"] + 2.0, ("pinch screw doesn't reach the socket", phi, through)
        rot = Matrix.Rotation(math.radians(phi - LEG_PHI[0]), 4, 'Z')
        fo = copy(ft, "foot"); fo.data.transform(rot)
        tube = rod("tube", s, f, TUBE_LEG_R, n=32)
        for o, nm in ((fo, "foot"), (tube, "tube")):
            for x in others:
                assert overlap(o, x) < 0.05, ("leg hits the base drive", phi, nm, x.name)
            for ph in range(-170, 171, 10):
                t = copy(tt, "t"); t.data.transform(rot_base(ph))
                assert not tree(o).overlap(tree(t)), ("leg hits the turntable", phi, nm, ph)
                bpy.data.objects.remove(t)
        assert overlap(tube, fb) < 0.05 and overlap(tube, fo) < 0.05, ("tube in its socket and foot", phi)
        zs = []
        for k in range(4):
            u = (f.x + 10.0 * math.cos(k * math.pi / 2), f.y + 10.0 * math.sin(k * math.pi / 2)) if k else (f.x, f.y)
            zs.append(FOOT_BOTTOM_Z - 1.0 + ray_len(fo, (u[0], u[1], FOOT_BOTTOM_Z - 1.0), (0, 0, 1)))
        level.append(math.degrees(math.atan((max(zs) - min(zs)) / 10.0)))
        pads.append(zs[0])
        for o in (fo, tube):
            bpy.data.objects.remove(o)
    assert min(walls) >= 2.0, ("socket wall", walls)
    assert min(pinch) >= 2.0, ("pinch insert wall", pinch)
    assert max(level) <= 0.5, ("pad face not level", level)
    assert max(pads) - min(pads) <= 0.1, ("pads not on one plane", pads)
    assert abs(pads[0] - PAD_RECESS - FOOT_BOTTOM_Z) < 0.05, "pad recess depth"
    lowest = min(min(v.co.z for v in fb.data.vertices), BASE_TOP_Z - BASE_MOTOR_L)
    assert FOOT_PAD_Z + PAD_T / 2 <= lowest - 20.0, ("pads not 20 under the base and its motor", FOOT_PAD_Z, lowest)
    assert CLAMP_TAB[0] >= 30 and CLAMP_TAB[1] >= 30 and CLAMP_TAB[2] >= 6, "clamp tab"
    pts = [(p[0], p[1]) for p in FOOT_PADS]
    edges = []
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        edges.append(abs(x0 * y1 - x1 * y0) / math.hypot(x1 - x0, y1 - y0))
    REPORT.update({"footprint_r_mm": round(min(edges), 1), "leg_deg": LEG_DEG, "foot_pads": [[round(c, 1) for c in p] for p in FOOT_PADS],
                   "socket_wall_mm": round(min(walls), 2), "pinch_insert_wall_mm": round(min(pinch), 2),
                   "pad_level_deg": round(max(level), 3), "bench_below_lowest_mm": round(lowest - FOOT_PAD_Z, 1)})
    REPORT["bolts"].update({"leg pinch screws": 6})
    for o in [tt] + others:
        bpy.data.objects.remove(o)


bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["shoulder-hub-a"], PARTS["shoulder-hub-b"] = hub()
PARTS["shoulder-output-plate"] = output_plate()
PARTS["plate-drill-jig"] = drill_jig()
PARTS["body-wall-A"], PARTS["body-wall-B"] = wall_a(), wall_b()
PARTS["compact-cage"] = compact_cage()
PARTS["shoulder-stop-collar"] = stop_collar()
for k in MOTORS:
    PARTS[f"shoulder-motor-plate-{k}"] = motor_plate(k)
PARTS["shoulder-motor-bracket"] = motor_bracket()
PARTS["turntable"], PARTS["base-ring-130T"] = turntable(), base_ring()
PARTS["spigot-spacer"], PARTS["spigot-cap"] = spigot_spacer(), spigot_cap()
PARTS["fixed-base"], PARTS["base-motor-plate"] = fixed_base(), base_motor_plate()
PARTS["foot"], PARTS["foot-pad"] = foot_part(), foot_pad()
CHECKS += [check_hub, check_body, check_shoulder_drive, check_base, check_legs]
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
