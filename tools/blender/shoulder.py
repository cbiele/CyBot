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
COMPACT = os.path.join(MODEL, "cycloid-poc", "20-1-compact-stub")
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
    """Hub B: spigot in plate B's Ø65 seat against its lip, flange on the plate's outer face, 45-degree cone, shoulder,
    journal in wall B's 6810. Its nose reaches in through the lip to the compact's output plate; the bore is open from
    wall B's side, so the floor screws drive from there."""
    assert side == "B", "hub A went with the first build: plate A turns on the stub"
    name, lip, face = "shoulder-hub-b", abs(LIP_FACE_Y["B"]), E.Y_REAR + E.PLATE_T
    f1, wall_in, end = face + FLANGE_T, abs(WALL_6810_Y["B"][0]), abs(HUB_Y[0])
    Y = lambda a, b: sorted((-a, -b))
    nose_r, nose_face = HUB_B_NOSE[0], HUB_Y[1]
    h = cyl_y(name, 0, 0, SPIGOT_R, *Y(lip, face + 0.01), n=192)
    L.union(h, cyl_y("nose", 0, 0, nose_r, LIP_FACE_Y["B"] - 0.01, nose_face, n=192))
    L.union(h, cyl_y("flange", 0, 0, FLANGE_R, *Y(face, f1), n=192))
    L.union(h, cone_y("cone", FLANGE_R, -(f1 - 0.01), HUB_SHOULDER_R, -(f1 + CONE)))
    L.union(h, cyl_y("shoulder", 0, 0, HUB_SHOULDER_R, *Y(f1 + CONE - 0.01, wall_in), n=192))
    L.union(h, cyl_y("journal", 0, 0, B6810[0], *Y(wall_in - 0.01, end - END_CHAMFER), n=192))
    L.union(h, cone_y("end", B6810[0], -(end - END_CHAMFER - 0.01), B6810[0] - END_CHAMFER, -end))
    L.finish(h)
    floor = nose_face - HUB_FLOOR
    cone_r = F.INSERT_PCD_R + 3.5                # the floor's ceiling: a 45-degree cone down to a small bridge
    L.cut(h, cyl_y("bore", 0, 0, HUB_BORE_R, -end - 1.0, floor - (HUB_BORE_R - cone_r) + 0.01, n=128))
    L.cut(h, cone_y("bore cone", HUB_BORE_R, floor - (HUB_BORE_R - cone_r), cone_r, floor))
    for a in LOCK_ANGLES:
        x, z = polar(LOCK_R, a)
        L.cut(h, cyl_y("lock insert", x, z, M3_INSERT_R, *Y(face - 1.0, face + M3_INSERT_DEPTH), n=32))
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        L.cut(h, cyl_y("dog", x, z, DOG_R + 0.15, nose_face - DOG_H - 0.5, nose_face + 1.0, n=48))
    head_y = nose_face + OUT_PLATE_T + 3.3 - HUB_SCREW_L
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        L.cut(h, cyl_y("screw", x, z, M3_CLEAR_R, floor - 1.0, nose_face + 1.0, n=32))
        L.cut(h, cyl_y("screw cb", x, z, STUB["cb_r"], floor - 1.0, head_y, n=32))
    for a in KEY_ANGLES:
        s = L.box("key slot", HUB_BORE_R - 1.0, B6810[0] + 1.0, -end - 1.0, -end + KEY_DEPTH_Y, -KEY_W / 2, KEY_W / 2)
        s.data.transform(Matrix.Rotation(-math.radians(a), 4, 'Y'))
        L.cut(h, s)
    for x, z in [polar(COLLAR_SCREW_R, a) for a in COLLAR_SCREW_ANGLES]:
        L.cut(h, cyl_y("collar insert", x, z, M3_INSERT_R, -end - 1.0, -end + M3_INSERT_DEPTH, n=32))
    PRINT_POSE[name] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, end))
    return h


def stub():
    """Wall A's fixed axle: flange on wall A's outer face, body through the wall, shoulder and land in plate A's 6810,
    a pilot into the housing's rear lip; the 625 for the rod at its outer end, the compact's screws from that end."""
    S = STUB; (y_in, y_out), (ys0, ys1) = S["y"], S["shoulder_y"]
    s = cyl_y("shoulder-stub", 0, 0, S["flange_r"], y_out - S["flange_t"], y_out, n=192)
    L.union(s, cyl_y("body", 0, 0, S["body_r"], ys1, y_out - S["flange_t"] + 0.01, n=192))
    L.union(s, cyl_y("shoulder", 0, 0, S["shoulder_r"], ys0, ys1 + 0.01, n=192))
    L.union(s, cyl_y("land", 0, 0, S["bearing_r"], y_in, ys0 + 0.01, n=192))
    L.union(s, cyl_y("pilot", 0, 0, S["pilot_r"], S["pilot_y"], y_in + 0.01, n=192))
    L.finish(s)
    L.cut(s, cyl_y("bore", 0, 0, S["bore_r"], S["pilot_y"] - 1.0, y_out - B625[2] - 1.0, n=128))
    L.cut(s, cyl_y("lip", 0, 0, S["lip_r"], y_out - B625[2] - 2.0, y_out + 1.0, n=64))
    L.cut(s, cyl_y("625", 0, 0, B625[1] + 0.05, y_out - B625[2], y_out + 1.0, n=96))
    for a in STUB_FIX_ANGLES:
        x, z = polar(STUB_FIX_R, a)
        L.cut(s, cyl_y("fixing", x, z, M3_CLEAR_R, y_out - S["flange_t"] - 1.0, y_out + 1.0, n=30))
    for a in STUB_SCREW_ANGLES:
        x, z = polar(STUB_SCREW_R, a)
        L.cut(s, cyl_y("screw", x, z, M3_CLEAR_R, y_in - 1.0, S["head_y"] + 0.01, n=30))   # 30, not 32: on the axes, 32 left open edges
        L.cut(s, cyl_y("screw cb", x, z, S["cb_r"], S["head_y"], y_out + 1.0, n=30))
    PRINT_POSE["shoulder-stub"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y_out))
    return s


def stub_spacer():
    r0, r1, y0, y1 = STUB_SPACER
    p = cyl_y("shoulder-stub-spacer", 0, 0, r1, y0, y1, n=192)
    L.cut(p, cyl_y("bore", 0, 0, r0, y0 - 1.0, y1 + 1.0, n=192))
    PRINT_POSE["shoulder-stub-spacer"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -y0))
    return p


def output_plate():
    """Replaces the compact's forearm output plate: three bigger, longer dogs into hub B's nose, for the shoulder's torque."""
    y0 = HUB_Y[1]
    p = cyl_y("shoulder-output-plate", 0, 0, OUT_PLATE_R, y0, y0 + OUT_PLATE_T, n=128)
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        L.union(p, cyl_y("dog", x, z, DOG_R, y0 - DOG_H, y0 + 0.01, n=48))
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        L.cut(p, cyl_y("screw", x, z, M3_CLEAR_R, y0 - 1.0, y0 + OUT_PLATE_T + 1.0, n=32))
        L.cut(p, cyl_y("head", x, z, 3.0, y0 - 1.0, y0 + 3.2, n=48))   # the floor screws' heads stay in hub B's floor; this clears their shanks' fillets
    L.finish(p)
    PRINT_POSE["shoulder-output-plate"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y0 + OUT_PLATE_T))
    return p


def drill_jig():
    """For plate B: built on plate A's outer face, then turned half round about z. A spigot in the seat, fences on the
    straight sides, Ø3.4 guides, and a key just below the round end, which lands on the plate if the jig is turned over."""
    face = E.Y_REAR + E.PLATE_T
    top, w = face + JIG_T, JIG_FENCE[1]
    j = cyl_y("plate-drill-jig", 0, 0, JIG_R, face, top, n=192)
    L.union(j, L.box("towards the elbow", -w, w, face, top, 0.0, 46.0))
    L.union(j, cyl_y("spigot", 0, 0, SEAT_R - 0.1, face - JIG_SPIGOT_DEPTH, face + 0.01, n=192))
    for s in (1, -1):
        L.union(j, L.box("fence", *sorted((s * JIG_FENCE[0], s * w)), face - JIG_SPIGOT_DEPTH, face + 0.01, 3.0, 46.0))
    kw, (k0, k1) = JIG_KEY
    L.union(j, L.box("key", -kw, kw, face - JIG_SPIGOT_DEPTH, face + 0.01, -k1, -k0))
    L.finish(j)
    L.cut(j, cyl_y("window", 0, 0, 20.0, face - JIG_SPIGOT_DEPTH - 1.0, top + 1.0, n=96))
    for a in LOCK_ANGLES:
        x, z = polar(LOCK_R, a)
        L.cut(j, cyl_y("guide", x, z, LOCK_HOLE_R, face - JIG_SPIGOT_DEPTH - 1.0, top + 1.0, n=32))
    j.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
    PRINT_POSE["plate-drill-jig"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, top))
    return j


_TREES = {}


def ctree(o):
    """A BVH tree of o, kept while o lives (the screw checks cast many rays at the same parts)."""
    k = o.as_pointer()
    if k not in _TREES:
        _TREES[k] = tree(o)
    return _TREES[k]


def screw_access(what, seat, out, head_r, head_h, objs, path_objs=None):
    """The head on its seat (seat: the centre of its seat face, out: from the seat towards the driver): 0.5 of room
    round it against objs, and a straight path of 30 past its top, for a driver about r 1.2, against path_objs
    (objs unless the screw goes in at the bench)."""
    out, seat = Vector(out).normalized(), Vector(seat)
    head = rod("head room", seat + out * 0.02, seat + out * head_h, head_r + 0.5, n=32)
    th = tree(head)
    for o in objs:
        assert not th.overlap(ctree(o)), (what, "no room round the head", o.name)
    bpy.data.objects.remove(head)
    a = out.orthogonal().normalized(); b = out.cross(a)
    top = seat + out * (head_h + 0.02)
    for p in [Vector()] + [(a * math.cos(k * math.pi / 2) + b * math.sin(k * math.pi / 2)) * 1.2 for k in range(4)]:
        for o in (objs if path_objs is None else path_objs):
            h = ctree(o).ray_cast(top + p, out)
            assert h[0] is None or h[3] >= 30.0, (what, "no straight path to the head", o.name, round(h[3], 1))


def cross_members():
    """The upper arm's aluminium tubes, in the shoulder frame."""
    return concat([cyl_y("cm", x, z + E.UPPER_L, E.TUBE_OR, -E.Y_REAR - E.PLATE_T, E.Y_REAR + E.PLATE_T, n=32)
                   for x, z in E.CROSS_MEMBERS], "cross members")


def fixed_shoulder():
    """What stays with the body inside and beside the arm: the stub, its spacer and the compact's housing."""
    return [copy(PARTS["shoulder-stub"], "stub"), copy(PARTS["shoulder-stub-spacer"], "spacer"), compact_posed()]


def ring_zone():
    return cyl_y("6810 outer ring", 0, 0, RING_ZONE[1], LIP_FACE_Y["A"], PLATE_FACES["A"][1], n=192)


def turning_shoulder(psi):
    """What turns with the arm round the fixed stub and compact, at psi: the plates, the elbow motor at both slot
    ends, its belt, the cross members, hub B, the output plate and plate A's 6810's outer ring."""
    ring = ring_zone(); L.cut(ring, cyl_y("bore", 0, 0, RING_ZONE[0], LIP_FACE_Y["A"] - 1.0, PLATE_FACES["A"][1] + 1.0, n=192))
    objs = list(upper_arm_moving().values()) + [cross_members(), copy(PARTS["shoulder-hub-b"], "hb"),
                                                 copy(PARTS["shoulder-output-plate"], "op"), ring]
    o = concat(objs, f"turning {psi}")
    o.data.transform(rot_shoulder(psi))
    return o


def check_shoulder_core():
    names = ("shoulder-stub", "shoulder-stub-spacer", "shoulder-hub-b", "shoulder-output-plate", "plate-drill-jig")
    st, sp, hb, op, jig = (PARTS[n] for n in names)
    pa, pb = elbow_part("upper-plate-A"), elbow_part("upper-plate-B")
    for n in names:
        part_ok(n); on_bed(n)
    # Plate A's 6810 on the stub: the land across its width, the inner ring clamped by the shoulder and the spacer.
    y0, y1 = LIP_FACE_Y["A"], PLATE_FACES["A"][1]
    land = radial_r(st, (y0 + y1) / 2)
    assert STUB["bearing_r"] - 0.01 <= land <= STUB["bearing_r"] + 0.1, ("stub's bearing land", land)
    assert min(v.co.y for v in st.data.vertices if math.hypot(v.co.x, v.co.z) > STUB["bearing_r"] + 0.05) >= y1 - 0.01, "stub wider than its land in the 6810"
    for r in (STUB["bearing_r"] + 0.15, STUB["shoulder_r"] - 0.15):
        up, down = ray_len(st, (r, (y0 + y1) / 2, 0), (0, 1, 0)), ray_len(sp, (r, (y0 + y1) / 2, 0), (0, -1, 0))
        assert up is not None and abs(up - (y1 - y0) / 2) < 0.02, ("stub's shoulder not on the inner ring", r, up)
        assert down is not None and abs(down - (y1 - y0) / 2) < 0.02, ("spacer not on the inner ring", r, down)
    assert STUB["shoulder_r"] - STUB["bearing_r"] >= 0.3 and STUB_SPACER[1] - STUB_SPACER[0] >= 0.3, "inner ring contact under 0.3"
    cp = compact_posed()
    band = [v.co for o in (st, sp, cp) for v in o.data.vertices if E.Y_REAR - 0.5 <= v.co.y <= y1 + 0.5 and math.hypot(v.co.x, v.co.z) > RING_ZONE[0] - 0.5]
    assert not [p for p in band if p.y > COMPACT_REAR_Y + 0.01], ("fixed part within 0.5 of the outer ring or the lip", band[:3])
    sp_y = [v.co.y for v in sp.data.vertices]
    assert abs(min(sp_y) - COMPACT_REAR_Y) < 0.01 and abs(max(sp_y) - y0) < 0.01, "spacer not between the housing and the inner ring"
    assert abs(min(v.co.y for v in st.data.vertices if math.hypot(v.co.x, v.co.z) > STUB["pilot_r"] + 0.05) - STUB["y"][0]) < 0.01, "stub's end face"
    assert overlap(st, cp) < 0.05 and overlap(sp, cp) < 0.05 and overlap(st, sp) < 0.05, "stub, spacer and housing overlap"
    assert touching(sp, cp), "spacer not on the housing"
    bore = radial_r(st, STUB["y"][0] + 0.5, inward=False)
    assert bore >= REAR_HUB_PROUD_R - 0.05, ("stub's bore on the rear carrier's hub", bore)
    assert radial_r(st, sum(STUB["y"]) / 2, inward=False) >= B625[0] + 0.5, "rod rubs the stub"
    seat = radial_r(st, STUB["y"][1] - B625[2] / 2, inward=False)
    assert B625[1] - 0.01 <= seat <= B625[1] + 0.1, ("625 seat", seat)
    for a in STUB_SCREW_ANGLES:
        x, z = polar(STUB_SCREW_R, a)
        assert ray_len(st, (x, STUB["y"][1] + 1.0, z), (0, -1, 0)) is None, ("stub screw hole blocked", a)
        seat_y = STUB["y"][1] + 1.0 - ray_len(st, (x + 2.5, STUB["y"][1] + 1.0, z), (0, -1, 0))
        assert abs(seat_y - STUB["head_y"]) < 0.02, ("stub screw head seat", a, seat_y)
        assert material_round(st, (x, (y0 + y1) / 2, z), (0, 1, 0), M3_CLEAR_R) >= WALL_MIN, ("stub screw wall", a)
    grip = STUB["head_y"] - COMPACT_REAR_Y
    assert 3.0 <= STUB["screw_l"] - grip <= M3_INSERT_DEPTH - 0.5, ("stub screws into the housing", STUB["screw_l"] - grip)
    # Running gaps: the stub and the compact clear everything that turns with the arm, a full turn round.
    fixed = concat(fixed_shoulder(), "fixed shoulder")
    fv = [v.co.copy() for v in fixed.data.vertices]; fbox, tf = bounds(fv, 10.0), tree(fixed)
    arm0 = turning_shoulder(0.0)
    worst, at = math.inf, None
    for psi in range(-180, 181):
        arm = copy(arm0, "arm"); arm.data.transform(rot_shoulder(psi))
        g = sweep_gap(arm, tf, fv, fbox)
        if g < worst:
            worst, at = g, psi
        bpy.data.objects.remove(arm)
    assert worst >= 0.5, ("a fixed part of the shoulder within 0.5 of a turning one", round(worst, 2), at)
    # The link: the output plate's dogs in hub B's nose, its screws into the carrier, the nose inside plate B's lip.
    end = HUB_Y[1]
    assert max(math.hypot(v.co.x, v.co.z) for v in hb.data.vertices if LIP_FACE_Y["B"] + 0.01 <= v.co.y <= end + 0.01) <= HUB_B_NOSE[0] + 0.01, "nose wider than plate B's lip"
    assert overlap(op, hb) < 0.05 and touching(op, hb), "output plate's dogs don't sit in hub B's nose"
    assert abs(max(v.co.y for v in op.data.vertices) - COMPACT_Y) < 0.01, "output plate not on the compact's carrier"
    assert overlap(op, cp) < 0.05, "output plate hits the housing"
    dog = SHOULDER_DESIGN_NMM / DOG_PCD_R / len(DOG_ANGLES) / (2 * DOG_R * DOG_H)
    J = math.pi / 2 * (HUB_B_NOSE[0] ** 4 - HUB_BORE_R ** 4)
    nose = SHOULDER_DESIGN_NMM * HUB_B_NOSE[0] / J
    assert dog <= PRINTED_MPA and nose <= PRINTED_MPA, ("link", dog, nose)
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        assert ray_len(hb, (x, end + 0.01, z), (0, -1, 0)) >= DOG_H + 0.2, "dog hole too shallow"
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        y_floor = end - HUB_FLOOR - 1.0
        seat = y_floor + ray_len(hb, (x + 2.5, y_floor, z), (0, 1, 0))
        reach = HUB_SCREW_L - (COMPACT_Y - seat)
        assert 3.0 <= reach <= 4.0, ("M3 x 12 into the carrier's inserts", reach)
        assert ray_len(hb, (x, end + 0.01, z), (0, -1, 0)) is None, ("hub floor screw hole blocked", x, z)
    # Hub B's lock to plate B, carried over.
    assert overlap(hb, pb) < 0.05 and touching(hb, pb), "hub B on plate B"
    wall = round(lock_wall(pb, "B"), 2)
    assert wall >= WALL_MIN, ("lock hole wall", wall)
    f = SHOULDER_DESIGN_NMM / LOCK_R / len(LOCK_ANGLES)
    shear, bearing = f / (math.pi * 1.5 ** 2), f / (3.0 * E.PLATE_T)
    assert shear <= PRINTED_MPA and bearing <= PRINTED_MPA, ("plate lock", shear, bearing)
    # Screws: room round each head and a straight path to it, with every part in place at that step.
    arm_parts = [pa, pb, hb, op, cp]
    for a in LOCK_ANGLES:
        x, z = polar(LOCK_R, a)
        screw_access(("plate lock", a), (x, PLATE_FACES["B"][1], z), (0, 1, 0), 2.75, BOLT_HEAD_H, arm_parts)
    for a in F.INSERT_ANGLES:
        x, z = polar(F.INSERT_PCD_R, a)
        head_seat = end + OUT_PLATE_T + 3.3 - HUB_SCREW_L
        screw_access(("hub floor", a), (x, head_seat, z), (0, -1, 0), 2.75, BOLT_HEAD_H, arm_parts)
    for a in STUB_SCREW_ANGLES:
        x, z = polar(STUB_SCREW_R, a)
        screw_access(("stub", a), (x, STUB["head_y"], z), (0, 1, 0), 2.75, BOLT_HEAD_H, arm_parts + [st, sp, PARTS["body-wall-A"]])
    j180 = check_jig(jig, pb)
    REPORT.update({"stub": {k: v for k, v in STUB.items()}, "rod_out_mm": round(ROD_OUT, 1), "shoulder_core_min_gap_mm": round(worst, 2),
                   "shoulder_core_min_gap_psi": at, "jig_180_overlap_mm3": round(j180, 1),
                   "link_mpa": {"dog bearing": round(dog, 1), "nose shear": round(nose, 2)}, "compact_y": COMPACT_Y, "hub_y": HUB_Y,
                   "lock_r": LOCK_R, "lock_angles": LOCK_ANGLES, "lock_wall_mm": wall, "lock_shear_mpa": round(shear, 1),
                   "lock_bearing_mpa": round(bearing, 1),
                   "bolts": {"plate lock (from inside the plate gap, into flange inserts)": LOCK_BOLT_L, "hub floor to compact carrier": HUB_SCREW_L,
                             "stub to the compact's housing (from the stub's outer end)": STUB["screw_l"]}})
    for o in (pa, pb, cp, fixed, arm0):
        bpy.data.objects.remove(o)


def check_jig(jig, pb):
    """On plate B: seated, guides clear, fences on both sides; turned half round about the seat's axis it can't seat."""
    assert overlap(jig, pb) < 0.05, "jig hits plate B"
    assert touching(jig, pb), "jig doesn't sit on plate B"
    y_out = PLATE_FACES["B"][0]
    for a in LOCK_ANGLES:
        x, z = polar(LOCK_R, a)
        assert ray_len(jig, (-x, y_out - (JIG_T + 1.0), z), (0, 1, 0)) is None, ("guide hole blocked", a)
    fence = [v.co for v in jig.data.vertices if v.co.y > y_out + 1.0 and abs(v.co.x) > E.PLATE_R]
    assert any(p.x > 0 for p in fence) and any(p.x < 0 for p in fence), "no fences on plate B's sides"
    s = radial_r(jig, y_out + JIG_SPIGOT_DEPTH / 2, r0=35.0)
    assert SEAT_R - 0.2 <= s <= SEAT_R - 0.02, ("jig spigot", s)
    over = copy(jig, "jig turned over"); over.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))
    v = overlap(over, pb)
    assert v >= 1.0, ("the jig seats on plate B turned half round", v)
    bpy.data.objects.remove(over)
    return v


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


def local_frame():
    """The shoulder motor's local frame at slot 0, in the shoulder frame: x = u along the belt away from the 80T,
    y = w square to it in the belt's plane, z = the shoulder frame's y."""
    mx, mz = motor_at()
    return basis((BELT_U[0], 0, BELT_U[1]), (BELT_W[0], 0, BELT_W[1]), (0, 1, 0), (mx, 0, mz))


def at_local(u, w, y):
    return local_frame() @ Vector((u, w, y))


def wall(side):
    """A low plate on the turntable: the boss round the axis and a trapezoid down to its bottom face."""
    r, h, hw = WALL_BOSS_R[side], SHOULDER_AXIS_Z, WALL_BOTTOM_HALF_W[side]
    Y = sorted(WALL_Y[side])
    zt = r / 2
    xt = math.sqrt(r * r - zt * zt) - 0.5
    w = prism_y(f"body-wall-{side}", [(-xt, zt), (xt, zt), (hw, -h), (-hw, -h)], *Y)
    L.union(w, cyl_y("boss", 0, 0, r, *Y, n=192))
    return w


def clip_to_turntable(w, side):
    """Nothing below the turntable's top, and only the wall's own bottom face on it."""
    Y = sorted(WALL_Y[side])
    h, hw = SHOULDER_AXIS_Z, WALL_BOTTOM_HALF_W[side]
    L.cut(w, L.box("under the turntable", -400.0, 400.0, -200.0, 200.0, -h - 200.0, -h))
    for s in (1, -1):
        L.cut(w, L.box("off the turntable", *sorted((s * hw, s * 400.0)), -200.0, 200.0, -h - 1.0, -h + 3.0))
    L.finish(w)


def wall_bottom_inserts(w, side):
    for x, y in WALL_INSERTS[side]:
        L.cut(w, L.cyl_z("bottom insert", x, y, M3_INSERT_R, -SHOULDER_AXIS_Z - 1.0, -SHOULDER_AXIS_Z + M3_INSERT_DEPTH, n=32))


def bracket():
    """Wall A's box for the shoulder motor's drop-in plate, built in the motor's local frame: its back on wall A's
    plane, slabs either side of the belt, the end (the pull screw's), and the roof the plate seats under, slotted
    round the motor's body and open towards the 80T, so the plate with its motor slides in."""
    u0, u1 = BOX["u"]
    W, t, yi, yo = BOX["w"], BOX["slab"], WALL_Y["A"][0], WALL_Y["A"][1]
    b = L.box("bracket", BOX["back_u0"], u1, -W, W, yi, yo)
    for s in (1, -1):
        L.union(b, L.box("slab", u0, u1, *sorted((s * (W - t), s * W)), yo - 0.01, BRACKET_Y[0] + 0.01))
    L.union(b, L.box("end", BOX["end"], u1, -W, W, yo - 0.01, BRACKET_Y[1]))
    L.union(b, L.box("roof", u0, u1, -W, W, *BRACKET_Y))
    L.finish(b)
    L.cut(b, L.box("motor slot", u0 - 1.0, MOTOR_SLOT_U, -MOTOR_SLOT_W, MOTOR_SLOT_W, BRACKET_Y[0] - 1.0, BRACKET_Y[1] + 1.0))
    for du, dw in PLATE_MOUNT:
        L.cut(b, slot_u("mount slot", du, dw, M3_CLEAR_R, BRACKET_Y[0] - 1.0, BRACKET_Y[1] + 1.0))
    L.cut(b, rod("pull screw", (BOX["end"] - 1.0, 0, PULL_Y), (u1 + 1.0, 0, PULL_Y), M3_CLEAR_R, n=32))
    b.data.transform(local_frame())
    return b


def slot_u(name, u, w, r, y0, y1, n=16):
    """A round-ended slot along u, MOTOR_SLOT each way, in the local frame."""
    pts = []
    for e in (1, -1):
        cu = u + e * MOTOR_SLOT
        pts += [(cu + e * r * math.sin(math.radians(180 * k / n)), w - e * r * math.cos(math.radians(180 * k / n))) for k in range(n + 1)]
    return prism_z(name, pts, y0, y1)


def wall_a():
    w = wall("A")
    L.union(w, bracket())
    clip_to_turntable(w, "A")
    L.cut(w, cyl_y("stub bore", 0, 0, WALL_A_BORE_R, WALL_Y["A"][0] - 1.0, WALL_Y["A"][1] + 1.0, n=192))
    for a in STUB_FIX_ANGLES:
        x, z = polar(STUB_FIX_R, a)
        L.cut(w, cyl_y("stub fix insert", x, z, M3_INSERT_R, WALL_Y["A"][1] - M3_INSERT_DEPTH, WALL_Y["A"][1] + 1.0, n=32))
    wall_bottom_inserts(w, "A")
    PRINT_POSE[w.name] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -WALL_Y["A"][0]))
    return w


def wall_b():
    w = wall("B")
    for b in stop_blocks():
        L.union(w, b)
    clip_to_turntable(w, "B")
    x0, z0 = WALL_B_FRONT
    L.cut(w, L.box("palm's path", x0, x0 + 100.0, WALL_Y["B"][1] - 1.0, WALL_Y["B"][0] + 1.0, z0, WALL_BOSS_R["B"] + 1.0))
    L.cut(w, cyl_y("seat", 0, 0, SEAT_R, WALL_6810_Y["B"][1], WALL_Y["B"][0] + 1.0, n=192))
    L.cut(w, cyl_y("lip", 0, 0, WALL_LIP_R, WALL_Y["B"][1] - 1.0, WALL_Y["B"][0] + 1.0, n=192))
    mx, mz = polar(MAGNET_AT_R, TAB_PHI)
    y = WALL_Y["B"][1]
    L.cut(w, L.box("sensor pocket", mx - SENSOR[0] / 2 - 0.1, mx + SENSOR[0] / 2 + 0.1, y - 1.0, y + SENSOR[2] + 0.1,
                   mz - SENSOR[1] / 2 - 0.1, mz + SENSOR[1] / 2 + 0.1))
    L.cut(w, L.box("leads", -1.5, 1.5, y - 1.0, y + 1.0, -SHOULDER_AXIS_Z - 1.0, mz))
    wall_bottom_inserts(w, "B")
    PRINT_POSE[w.name] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, WALL_Y["B"][0]))
    return w


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
    L.union(band, cyl_y("20T teeth", x, z, E.R20_OD + 1.5, y0, y1 + 0.01))
    L.union(band, cyl_y("20T hub", x, z, 9.5, y1, PULLEY20_HUB_Y[1]))
    return band


def shoulder_motor_box(kind, slot):
    h = MOTORS[kind]["sq"] / 2
    b = L.box(f"motor {kind}", slot - h, slot + h, -h, h, MOTOR_FACE_Y, MOTOR_FACE_Y + MOTORS[kind]["length"])
    b.data.transform(local_frame())
    return b


def motor_plate(kind):
    """The drop-in plate: the motor's face on its outer face, inserts for the roof's four screws, a tab on its far
    end for the pull screw, the 20T's hub through its pilot."""
    m, name = MOTORS[kind], f"shoulder-motor-plate-{kind}"
    y0, y1 = MOTOR_PLATE_Y
    p = L.box(name, -PLATE_HALF, PLATE_HALF, -PLATE_HALF, PLATE_HALF, y0, y1)
    L.union(p, L.box("tab", TAB["u"][0], TAB["u"][1], -TAB["w"], TAB["w"], TAB["y"][0], y0 + 0.01))
    L.finish(p)
    for su in (-1, 1):
        for sw in (-1, 1):
            L.cut(p, L.cyl_z("motor screw", su * m["hole"], sw * m["hole"], m["hole_r"], y0 - 1.0, y1 + 1.0, n=30))
    for du, dw in PLATE_MOUNT:
        L.cut(p, L.cyl_z("insert", du, dw, M3_INSERT_R, y1 - M3_INSERT_DEPTH, y1 + 1.0, n=30))
    L.cut(p, rod("pull insert", (PLATE_HALF - M3_INSERT_DEPTH, 0, PULL_Y), (PLATE_HALF + 1.0, 0, PULL_Y), M3_INSERT_R, n=32))
    L.cut(p, rod("pull bore", (PLATE_HALF - PULL_BORE, 0, PULL_Y), (PLATE_HALF, 0, PULL_Y), M3_CLEAR_R, n=32))
    L.cut(p, L.cyl_z("pilot", 0, 0, m["pilot_r"], y0 - 1.0, y1 + 1.0, n=96))
    p.data.transform(local_frame())
    PRINT_POSE[name] = Matrix(((1, 0, 0, 0), (0, -1, 0, 0), (0, 0, -1, y1), (0, 0, 0, 1))) @ local_frame().inverted()
    return p


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
    names = ("body-wall-A", "body-wall-B", "shoulder-stop-collar")
    wa, wb, col = (PARTS[n] for n in names)
    hb, st = PARTS["shoulder-hub-b"], PARTS["shoulder-stub"]
    for n in names:
        part_ok(n); on_bed(n)
    y_in, y_brg = WALL_6810_Y["B"]
    seat = radial_r(wb, (y_in + y_brg) / 2, inward=False)
    assert B6810[1] <= seat <= B6810[1] + 0.1, ("wall B's seat", seat)
    depth = ray_len(wb, (31.8, y_in + 1.0, 0), (0, -1, 0)) - 1.0
    assert abs(depth - B6810[2]) < 0.05, ("wall B's seat depth", depth)
    lip = radial_r(wb, y_brg - E.LIP_T / 2, inward=False)
    assert HUB_SHOULDER_R + 0.5 <= lip <= WALL_LIP_R + 0.01, ("wall B's lip", lip)
    bore = radial_r(wa, sum(WALL_Y["A"]) / 2, inward=False)
    assert WALL_A_BORE_R - 0.01 <= bore <= WALL_A_BORE_R + 0.1 and bore - STUB["body_r"] <= 0.2, ("wall A's bore for the stub", bore)
    rounds = {"B seat": material_round(wb, (0, (y_in + y_brg) / 2, 0), (0, 1, 0), SEAT_R)}
    assert rounds["B seat"] >= BODY_MIN, ("material round wall B's seat", rounds)
    for w, side in ((wa, "A"), (wb, "B")):
        assert abs(min(v.co.z for v in w.data.vertices) + SHOULDER_AXIS_Z) < 0.01, ("wall not on the turntable", side)
        for x, y in WALL_INSERTS[side]:
            d = ray_len(w, (x + 1.85, y, -SHOULDER_AXIS_Z - 1.0), (0, 0, 1))
            assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("wall bottom insert", side, x, d)
            rounds[f"{side} bottom {x:+.0f}"] = material_round(w, (x, y, -SHOULDER_AXIS_Z + M3_INSERT_DEPTH / 2), (0, 0, 1), M3_INSERT_R)
    assert min(v for k, v in rounds.items() if "bottom" in k) >= INSERT_WALL_MIN, ("wall bottom insert wall", rounds)
    assert 3.0 <= WALL_SCREW_L - TURNTABLE_T <= M3_INSERT_DEPTH - 0.5, "wall screws from under the turntable"
    # The stub's fixing: its flange on wall A's outer face, M3 x 10 through it into wall A's inserts.
    assert overlap(st, wa) < 0.05 and touching(st, wa), "stub not on wall A"
    for a in STUB_FIX_ANGLES:
        x, z = polar(STUB_FIX_R, a)
        assert ray_len(st, (x, STUB["y"][1] + 1.0, z), (0, -1, 0)) is None, ("stub's fixing hole blocked", a)
        d = ray_len(wa, (x + 1.85, WALL_Y["A"][1] + 1.0, z), (0, -1, 0))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("stub fixing insert", a, d)
        rounds[f"A fix {a:.0f}"] = material_round(wa, (x, WALL_Y["A"][1] - M3_INSERT_DEPTH / 2, z), (0, 1, 0), M3_INSERT_R)
        assert rounds[f"A fix {a:.0f}"] >= WALL_MIN, ("stub fixing insert wall", a)
        screw_access(("stub fixing", a), (x, STUB["y"][1], z), (0, 1, 0), 2.75, BOLT_HEAD_H, [st, wa])
    engage = STUB_FIX_L - STUB["flange_t"]
    assert 3.0 <= engage <= M3_INSERT_DEPTH - 0.5, ("stub fixing screws", engage)
    assert overlap(hb, wb) < 0.05, "hub B hits wall B"
    assert PULLEY80_Y - STUB["y"][1] >= 1.0 - 1e-6, "80T on the stub's end"
    worst, _ = sweep([copy(o, "f") for o in (wa, wb)] + [pulley80_envelope()] +
                     [shoulder_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)], "body")
    assert worst >= 2.0, ("upper arm within 2 of the body", worst)
    check_axis_and_stops()
    check_stops(col, wb, hb)
    REPORT.update({"shoulder_min_gap_mm": round(worst, 2), "SHOULDER_AXIS_Z": SHOULDER_AXIS_Z, "shoulder_axis_z": SHOULDER_AXIS_Z,
                   "pulley80_y": PULLEY80_Y, "shoulder_belt_plane_y": SHOULDER_BELT_PLANE_Y, "rod_out_mm": round(ROD_OUT, 1),
                   "wall_material_mm": {k: round(v, 2) for k, v in rounds.items()}})
    REPORT["bolts"].update({"walls from under the turntable (into the walls' bottom inserts)": WALL_SCREW_L,
                            "stub flange to wall A": STUB_FIX_L, "stop collar to hub B": COLLAR_SCREW_L})


def turntable_disc(h):
    return L.cyl_z("turntable's top", 0, 0, TURNTABLE_R, -h - TURNTABLE_T, -h, n=192)


_TURN = {}


def psi_limits(h):
    """The widest psi each way, in 1-degree steps from 90, at which what turns with the arm stays 1.0 from the body,
    the shoulder drive and a turntable with its top at -h."""
    if "arm" not in _TURN:
        _TURN["arm"] = turning_shoulder(0.0)
    fixed = concat([copy(PARTS[n], "f") for n in ("body-wall-A", "body-wall-B")] +
                   [shoulder_motor_box(k, s) for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)] +
                   [shoulder_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)] +
                   [moved(PARTS[f"shoulder-motor-plate-{k}"], s, "p") for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)] +
                   [turntable_disc(h)], "fixed body")
    fv = [v.co.copy() for v in fixed.data.vertices]
    fbox, tf = bounds(fv, 10.0), tree(fixed)
    out = []
    for sgn in (1, -1):
        psi = 89
        while psi < 180:
            arm = copy(_TURN["arm"], "arm"); arm.data.transform(rot_shoulder(sgn * (psi + 1)))
            g = sweep_gap(arm, tf, fv, fbox)
            bpy.data.objects.remove(arm)
            if g < 1.0:
                break
            psi += 1
        out.append(psi)
    bpy.data.objects.remove(fixed)
    return out


def check_axis_and_stops():
    """SHOULDER_AXIS_Z: the lowest, in 0.5 steps, that keeps everything under the axis 3 above the turntable at psi 0
    and lets the stops sit past 92. PSI_STOPS: the widest the turntable's rim allows, less 2, the same both ways."""
    h = SHOULDER_AXIS_Z
    low_parts = [copy(_TURN.setdefault("arm", turning_shoulder(0.0)), "arm")] + fixed_shoulder() + \
                [copy(PARTS["shoulder-stop-collar"], "c"), pulley80_envelope()]
    low = min(min(v.co.z for v in o.data.vertices) for o in low_parts)
    for o in low_parts:
        bpy.data.objects.remove(o)
    lim = psi_limits(h)
    stops = min(lim) - 2
    assert low + h >= 3.0 - 1e-6, ("a part under the axis within 3 of the turntable", round(low + h, 2))
    assert lim[0] >= 90 and lim[1] >= 90, ("the upper arm can't reach level", lim)
    assert stops > 92, ("stops not past 92", lim)
    assert PSI_STOPS == (-float(stops), float(stops)), ("PSI_STOPS should be", stops)
    lo = psi_limits(h - 0.5)
    assert low + h - 0.5 < 3.0 or min(lo) - 2 <= 92, ("the axis could go 0.5 lower", lo)
    trade = {f"{h + dh:.0f}": min(psi_limits(h + dh)) - 2 for dh in (5.0, 10.0, 20.0)}
    REPORT.update({"psi_stops": PSI_STOPS, "psi_range": PSI_RANGE, "psi_limits_raw": lim, "under_axis_clear_mm": round(low + h, 2),
                   "psi_stops_if_axis_z": trade})


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
    wa, wb, st, hb = (PARTS[n] for n in ("body-wall-A", "body-wall-B", "shoulder-stub", "shoulder-hub-b"))
    plates = {k: PARTS[f"shoulder-motor-plate-{k}"] for k in MOTORS}
    for n in plates.values():
        part_ok(n.name); on_bed(n.name)
    y0, y1 = MOTOR_PLATE_Y
    for k, p in plates.items():
        m = MOTORS[k]
        for du, dw in PLATE_MOUNT:
            c = at_local(du, dw, y1 + 1.0)
            d = ray_len(p, at_local(du + 1.85, dw, y1 + 1.0), (0, -1, 0))
            assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("plate insert", k, du, dw, d)
            assert material_round(p, at_local(du, dw, y1 - M3_INSERT_DEPTH / 2), (0, 1, 0), M3_INSERT_R) >= WALL_MIN, ("plate insert wall", k)
        for su in (-1, 1):
            for sw in (-1, 1):
                c = at_local(su * m["hole"], sw * m["hole"], 0)
                assert ray_len(p, (c.x, y0 - 1.0, c.z), (0, 1, 0)) is None, ("motor hole", k)
                assert bore_r_at(p, c.x, c.z, sum(MOTOR_PLATE_Y) / 2) >= m["hole_r"] - 0.05, ("motor hole size", k)
        c = at_local(0, 0, 0)
        assert bore_r_at(p, c.x, c.z, y0 + 0.5) >= m["pilot_r"] - 0.05, ("pilot", k)
        assert MOTOR_FACE_Y - m["shaft"] <= sum(PULLEY20_HUB_Y) / 2 - 1.5, ("shaft short of the 20T's set screw", k)
        tab = material_round(p, at_local(PLATE_HALF - M3_INSERT_DEPTH / 2, 0, PULL_Y), BELT_U[0:1] + (0,) + BELT_U[1:], M3_INSERT_R)
        assert tab >= WALL_MIN, ("pull insert wall", k, tab)
    belts = {}
    for s in (-MOTOR_SLOT, 0.0, MOTOR_SLOT):
        x, z = motor_at(s)
        belts[s] = round(math.hypot(x, z), 2)
        assert abs(belts[s] - SHOULDER_BELT_C - s) <= 0.1, ("belt centres", s, belts[s])
    cp = compact_posed()
    p80 = posed_stl(os.path.join(OUT, "shoulder-pulley-80T.stl"), "80T",
                    Matrix.Translation((0, PULLEY80_Y + E.PULLEY_H, 0)) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    gap80 = min(v.co.y for v in p80.data.vertices) - STUB["y"][1]
    assert 1.0 - 1e-6 <= gap80 <= 1.2, ("80T's inside face to the stub's end", gap80)
    assert overlap(p80, st) < 0.05 and overlap(p80, wa) < 0.05, "80T hits the stub or wall A"
    pulls = {}
    for s in (-MOTOR_SLOT, MOTOR_SLOT):
        belt = shoulder_belt_envelope(s)
        for o, n in ((wa, "wall A"), (st, "stub"), (cp, "compact")):
            assert overlap(belt, o) < 0.05, ("shoulder belt hits", n, s)
        for k in MOTORS:
            box, pl = shoulder_motor_box(k, s), moved(plates[k], s, "plate")
            for o, n in ((wa, "wall A"), (wb, "wall B"), (st, "stub"), (hb, "hub B"), (cp, "compact")):
                assert overlap(box, o) < 0.05, ("motor box hits", n, k, s)
            assert overlap(pl, wa) < 0.05 and touching(pl, wa), ("plate under the roof", k, s)
            assert overlap(pl, box) < 0.05 and touching(pl, box), ("motor on its plate", k, s)
            assert overlap(pl, belt) < 0.05, ("plate on the belt", k, s)
            hr, hh = MOTORS[k]["head"]
            for su in (-1, 1):
                for sw in (-1, 1):
                    seat = at_local(s + su * MOTORS[k]["hole"], sw * MOTORS[k]["hole"], MOTOR_PLATE_Y[0])
                    screw_access(("motor screw", k, s, su, sw), seat, (0, -1, 0), hr, hh, [wa, belt, st], path_objs=[pl])
            for du, dw in PLATE_MOUNT:
                screw_access(("plate screw", k, s, du, dw), at_local(s + du, dw, BRACKET_Y[1]), (0, 1, 0), 2.75, BOLT_HEAD_H, [wa, box])
            screw_access(("pull screw", k, s), at_local(BOX["u"][1], 0, PULL_Y), (BELT_U[0], 0, BELT_U[1]), 2.75, BOLT_HEAD_H, [wa, pl, box])
            for o in (box, pl):
                bpy.data.objects.remove(o)
        bpy.data.objects.remove(belt)
        gap = BOX["end"] - (PLATE_HALF + s)
        depth = PULL_SCREW_L - (BOX["u"][1] - BOX["end"]) - gap
        assert gap >= 0.5 and M3_INSERT_DEPTH <= depth <= PULL_BORE - 0.5, ("pull screw", s, gap, depth)
        pulls[f"{s:+.0f}"] = {"gap": round(gap, 2), "depth": round(depth, 2)}
    assert BOX["w"] - BOX["slab"] - PLATE_HALF >= 0.5, "plate on the box's slabs"
    engage = PLATE_SCREW_L - (BRACKET_Y[1] - BRACKET_Y[0])
    assert 3.0 <= engage <= M3_INSERT_DEPTH - 0.5, ("plate screws", engage)
    worst, _ = sweep([shoulder_motor_box(k, s) for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)] +
                     [shoulder_belt_envelope(s) for s in (-MOTOR_SLOT, MOTOR_SLOT)] +
                     [moved(plates[k], s, "p") for k in MOTORS for s in (-MOTOR_SLOT, MOTOR_SLOT)], "shoulder drive")
    assert worst >= 2.0, ("upper arm within 2 of the shoulder drive", worst)
    REPORT.update({"motor_wall": MOTOR_WALL, "shoulder_motor_at": [round(c_, 2) for c_ in SHOULDER_MOTOR_AT],
                   "shoulder_motor_deg": SHOULDER_MOTOR_DEG, "shoulder_motor_direction": "rear (-x), 10 degrees above level, body outwards (+y)",
                   "shoulder_belt_centres": belts, "pulley80_gap_mm": round(gap80, 2), "pull_screw": pulls, "drive_min_gap_mm": round(worst, 2)})
    REPORT["bolts"].update({"motor plate into the roof (into the plate's inserts)": PLATE_SCREW_L, "pull screw": PULL_SCREW_L})
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
    over = copy(col, "collar turned over"); over.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))
    turned = overlap(over, hb)
    assert turned >= 1.0, ("the stop collar goes on hub B turned half round", turned)
    bpy.data.objects.remove(over)
    REPORT["collar_180_overlap_mm3"] = round(turned, 1)
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


def phi_tab():
    return sector_z("phi tab", PHI_R[0], PHI_R[1], PHI_TAB_DEG - PHI_HALF, PHI_TAB_DEG + PHI_HALF, PHI_TAB_Z[1], PHI_TAB_Z[0] + 0.01)


def phi_block():
    return sector_z("phi block", PHI_R[0], PHI_R[1], -PHI_HALF, PHI_HALF, DRUM_TOP - 0.01, PHI_BLOCK_TOP)


def hall_xy():
    r, a, _ = BASE_HALL["magnet"]
    return polar(r, a)


def turntable():
    """A round plate under the walls; hub on the two 6810s; the base stop's tab and the Hall magnet under it."""
    zt, zb = TURNTABLE_Z, TURNTABLE_Z - TURNTABLE_T
    t = L.cyl_z("turntable", 0, 0, TURNTABLE_R, zb, zt, n=192)
    L.union(t, L.cyl_z("hub", 0, 0, TT_HUB_R, TT_HUB_Z0, zb + 0.01, n=192))
    L.union(t, phi_tab())
    L.finish(t)
    L.cut(t, L.cyl_z("seats", 0, 0, SEAT_R, TT_HUB_Z0 - 1.0, BASE_6810_Z[0] + B6810[2], n=192))
    L.cut(t, L.cyl_z("lip", 0, 0, TT_LIP_R, TT_HUB_Z0 - 1.0, zt + 1.0, n=192))
    for a in RING_SCREW_ANGLES:
        x, y = polar(RING_SCREW_R, a)
        L.cut(t, L.cyl_z("ring insert", x, y, M3_INSERT_R, TT_HUB_Z0 - 1.0, TT_HUB_Z0 + M3_INSERT_DEPTH + 2.0, n=32))
    for x, y in WALL_INSERTS["A"] + WALL_INSERTS["B"]:
        L.cut(t, L.cyl_z("wall screw", x, y, M3_CLEAR_R, zb - 1.0, zt + 1.0, n=30))
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


def base_frame():
    """The base motor's local frame: x = r out along BASE_U, y = t across it, z up."""
    return basis((BASE_U[0], BASE_U[1], 0), (-BASE_U[1], BASE_U[0], 0), (0, 0, 1), (0, 0, 0))


def at_base(r, t, z):
    return base_frame() @ Vector((r, t, z))


PUSH_Z = sum(BASE_PLATE_Z) / 2
LUG_TOP = BASE_PLATE_Z[1] + 2.0


def base_lug():
    lug = L.box("base lug", BASE_LUG["r"][0], BASE_LUG["r"][1], -BASE_LUG["half"], BASE_LUG["half"], SHELF_Z[1] - 0.01, LUG_TOP)
    lug.data.transform(base_frame())
    return lug


def base_motor_box(slot):
    h, r = MOTORS["17"]["sq"] / 2, BASE_BELT_C + slot
    b = L.box("base motor", r - h, r + h, -h, h, BASE_PLATE_Z[1], BASE_PLATE_Z[1] + BASE_MOTOR_L)
    b.data.transform(base_frame())
    return b


def base_belt_envelope(slot):
    """The belt between the 130T and the 20T (not the ring's inside), and the 20T hanging under the shelf, at slot."""
    x, y = base_motor_at(slot)
    z0, z1 = RING_Z[0] - 1.5, RING_Z[1] + 1.5
    band = hull([L.cyl_z("a", 0, 0, od_r(RING_TEETH) + E.BELT_T, z0, z1, n=192), L.cyl_z("b", x, y, E.R20_OD + E.BELT_T, z0, z1)], "base belt")
    L.cut(band, L.cyl_z("ring", 0, 0, od_r(RING_TEETH) - GROOVE_DEPTH - 0.5, z0 - 1.0, z1 + 1.0, n=192))
    L.union(band, L.cyl_z("20T teeth", x, y, E.R20_OD + 1.5, z0, z1 + 0.01))
    L.union(band, L.cyl_z("20T hub", x, y, 9.5, z1, BASE20_HUB_Z[1]))
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
    """The drum on the bench, the spigot with its shoulder, the stop block, the Hall post, and the base motor's shelf:
    side walls under it with 45-degree undersides past the drum, so the drum prints on its underside."""
    zt, zb = DRUM_TOP, BENCH_Z
    f = L.cyl_z("fixed-base", 0, 0, DRUM_R, zb, zt, n=192)
    L.union(f, L.cyl_z("shoulder", 0, 0, SPIGOT["shoulder_r"], zt - 0.01, TT_HUB_Z0, n=192))
    L.union(f, L.cyl_z("spigot", 0, 0, SPIGOT["r"], TT_HUB_Z0 - 0.01, SPIGOT["top"], n=192))
    L.union(f, phi_block())
    hx, hy = hall_xy()
    L.union(f, L.box("hall post", hx - HALL_POST_HALF, hx + HALL_POST_HALF, hy - HALL_POST_HALF, hy + HALL_POST_HALF, zt - 0.01, BASE_HALL["sensor_top"]))
    r0, r1 = SHELF["r"]
    rin = math.sqrt(DRUM_R ** 2 - SHELF["half"] ** 2) - 1.0       # where the walls' outer corners leave the drum
    rw = SHELF["wall_r0"]                                          # the walls start clear of the belt's sweep in to the ring
    side = [(rw, zt - 1.0), (rin, zt - 1.0), (rin, zb), (r1, zb + (r1 - rin)), (r1, SHELF_Z[1]), (rw, SHELF_Z[1])]
    arm = L.box("shelf", r0, r1, -SHELF["half"], SHELF["half"], *SHELF_Z)
    for sg in (1, -1):
        L.union(arm, prism_y("wall", side, *sorted((sg * (SHELF["half"] - SHELF["wall"]), sg * SHELF["half"]))))
    L.union(arm, L.box("lug", BASE_LUG["r"][0], BASE_LUG["r"][1], -BASE_LUG["half"], BASE_LUG["half"], SHELF_Z[1] - 0.01, LUG_TOP))
    L.finish(arm)
    w, m = SHELF["window"], BASE_BELT_C
    L.cut(arm, L.box("window", m - w - MOTOR_SLOT, m + w + MOTOR_SLOT, -w, w, SHELF_Z[0] - 1.0, SHELF_Z[1] + 1.0))
    for dr, dt in BASE_PLATE_INSERTS:
        L.cut(arm, L.cyl_z("plate insert", m + dr, dt, M3_INSERT_R, SHELF_Z[0] - 1.0, SHELF_Z[1] + 1.0, n=30))
    L.cut(arm, rod("push insert", (BASE_LUG["r"][0] - 1.0, 0, PUSH_Z), (BASE_LUG["r"][1] + 1.0, 0, PUSH_Z), M3_INSERT_R, n=32))
    arm.data.transform(base_frame())
    L.union(f, arm)
    L.finish(f)
    L.cut(f, L.cyl_z("bore", 0, 0, SPIGOT["bore_r"], zb - 1.0, SPIGOT["top"] + 1.0, n=128))
    for a in CAP_SCREW_ANGLES:
        x, y = polar(CAP_SCREW_R, a)
        L.cut(f, L.cyl_z("cap insert", x, y, M3_INSERT_R, SPIGOT["top"] - M3_INSERT_DEPTH - 1.0, SPIGOT["top"] + 1.0, n=32))
    st = BASE_HALL["sensor_top"]
    L.cut(f, L.box("sensor pocket", hx - SENSOR[1] / 2 - 0.1, hx + SENSOR[1] / 2 + 0.1, hy - SENSOR[0] / 2 - 0.1, hy + SENSOR[0] / 2 + 0.1,
                   st - SENSOR[2] - 0.1, st + 1.0))
    L.cut(f, L.box("leads", hx - HALL_POST_HALF - 1.0, hx, hy - 1.0, hy + 1.0, st - 1.0, st + 1.0))
    leg_sockets(f)
    PRINT_POSE["fixed-base"] = Matrix.Translation((0, 0, -zb))
    return f


def base_motor_plate():
    """The base motor stands on it shaft-down through the shelf's window; slotted along its radius, pushed out by the lug's screw."""
    m, c = MOTORS["17"], BASE_BELT_C
    z0, z1 = BASE_PLATE_Z
    p = L.box("base-motor-plate", c - BASE_PLATE_HALF_R, c + BASE_PLATE_HALF_R, -BASE_PLATE_HALF_T, BASE_PLATE_HALF_T, z0, z1)
    for sr in (-1, 1):
        for st_ in (-1, 1):
            L.cut(p, L.cyl_z("motor screw", c + sr * m["hole"], st_ * m["hole"], m["hole_r"], z0 - 1.0, z1 + 1.0, n=30))
    for dr, dt in BASE_PLATE_INSERTS:
        L.cut(p, slot_u("slot", c + dr, dt, M3_CLEAR_R, z0 - 1.0, z1 + 1.0))
    L.cut(p, L.cyl_z("pilot", c, 0, m["pilot_r"], z0 - 1.0, z1 + 1.0, n=96))
    p.data.transform(base_frame())
    mx, my = base_motor_at()
    PRINT_POSE["base-motor-plate"] = Matrix.Translation((-mx, -my, -z0))
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
        s = radial_z(fb, zm, r0=30.0)   # from just outside: the stop block and the shelf's walls stand further out
        assert SPIGOT["r"] - 0.01 <= s <= SPIGOT["r"] + 0.1, ("spigot", zm, s)   # -0.01: the polygon's chords
        seat = radial_z(tt, zm, inward=False)
        assert B6810[1] <= seat <= B6810[1] + 0.1, ("turntable seat", zm, seat)
    for o, z, n in ((tt, BASE_6810_Z[0] + B6810[2] + 1.0, "turntable's top lip"), (ring, TT_HUB_Z0 - 0.5, "ring's lip")):
        lip = radial_z(o, z, inward=False)
        assert HUB_SHOULDER_R + 0.5 <= lip <= WALL_LIP_R + 0.01, (n, lip)
    for o, z, n in ((cap, BASE_6810_Z[0] + B6810[2] + 0.5, "cap"), (spacer, sum(SPACER_Y) / 2, "spacer"), (fb, TT_HUB_Z0 - 0.5, "spigot shoulder")):
        r = radial_z(o, z, r0=30.0)
        assert r <= HUB_SHOULDER_R - 0.45, ("bears past the inner ring", n, r)
    assert abs(min(v.co.z for v in cap.data.vertices) - (BASE_6810_Z[0] + B6810[2])) < 0.01, "cap not on the upper inner ring"
    assert max(v.co.z for v in cap.data.vertices) <= TURNTABLE_Z - 0.5, "cap stands above the turntable"
    sp = [v.co.z for v in spacer.data.vertices]
    assert abs(min(sp) - SPACER_Y[0]) < 0.01 and abs(max(sp) - SPACER_Y[1]) < 0.01, "spacer between the inner rings"
    for o, other, n in ((tt, fb, "turntable on the fixed base"), (ring, fb, "ring on the fixed base"), (cap, tt, "cap on the turntable"),
                        (spacer, tt, "spacer on the turntable"), (ring, tt, "ring in the turntable"), (spacer, fb, "spacer on the spigot"),
                        (cap, fb, "cap in the spigot")):
        assert overlap(o, other) < 0.05, n
    hub_face = ray_len(tt, ((TT_HUB_R - 1.0) * math.cos(0.3), (TT_HUB_R - 1.0) * math.sin(0.3), TT_HUB_Z0 - 1.0), (0, 0, 1))
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
    above = concat([copy(PARTS[n], "a") for n in ("body-wall-A", "body-wall-B")] +
                   [shoulder_motor_box(k, sl) for k in MOTORS for sl in (-MOTOR_SLOT, MOTOR_SLOT)] +
                   [moved(PARTS[f"shoulder-motor-plate-{k}"], sl, "p") for k in MOTORS for sl in (-MOTOR_SLOT, MOTOR_SLOT)] +
                   [shoulder_belt_envelope(sl) for sl in (-MOTOR_SLOT, MOTOR_SLOT)], "on the turntable")
    push, tt_gap = {}, math.inf
    for s in (-MOTOR_SLOT, MOTOR_SLOT):
        box, belt, plate, lug = base_motor_box(s), base_belt_envelope(s), moved_base(bp, s), base_lug()
        assert overlap(box, fb) < 0.05, ("base motor hits the fixed base", s)
        assert overlap(plate, fb) < 0.05 and touching(plate, fb) and touching(plate, box), ("base motor plate", s)
        assert overlap(belt, fb) < 0.05 and overlap(belt, plate) < 0.05, ("base belt hits the fixed base or the plate", s)
        for phi in range(-170, 171, 10):
            t = copy(turning, "t"); t.data.transform(rot_base(phi))
            for o, n in ((box, "base motor"), (plate, "base motor plate"), (lug, "push lug")):
                assert overlap(o, t) < 0.05, (n + " hits the turntable", s, phi)
            tt_gap = min(tt_gap, min_gap(box, t))
            a = copy(above, "a"); a.data.transform(rot_base(phi))
            for o, n in ((box, "base motor"), (belt, "base belt"), (plate, "base motor plate")):
                assert not tree(o).overlap(tree(a)), (n + " hits the body or the shoulder drive", s, phi)
            for o in (t, a):
                bpy.data.objects.remove(o)
        tb = copy(tt, "tb")
        for phi in range(-170, 171, 10):
            tb.data.transform(rot_base(10 if phi > -170 else -170))
            assert overlap(belt, tb) < 0.05, ("base belt hits the turntable", s, phi)
        bpy.data.objects.remove(tb)
        gap = min_gap(plate, lug)
        assert gap >= 0.5, ("base plate on its push lug", s, gap)
        g = (BASE_BELT_C + s - BASE_PLATE_HALF_R) - BASE_LUG["r"][1]
        seat_r = BASE_LUG["r"][1] + g - BASE_PUSH_L
        assert seat_r <= BASE_LUG["r"][0] + 0.01, ("base push screw short of the plate", s, seat_r)
        screw_access(("base push screw", s), at_base(seat_r, 0, PUSH_Z), (-BASE_U[0], -BASE_U[1], 0), 2.75, BOLT_HEAD_H, [fb, turning, plate, box, cap])
        push[f"{s:+.0f}"] = {"gap": round(g, 2), "head_r": round(seat_r - BOLT_HEAD_H, 2)}
        for dr, dt in BASE_PLATE_INSERTS:
            screw_access(("base plate screw", s, dr, dt), at_base(BASE_BELT_C + s + dr, dt, BASE_PLATE_Z[1]), (0, 0, 1), 2.75, BOLT_HEAD_H, [fb, box, turning])
        for sr in (-1, 1):
            for st_ in (-1, 1):
                seat = at_base(BASE_BELT_C + s + sr * MOTORS["17"]["hole"], st_ * MOTORS["17"]["hole"], BASE_PLATE_Z[0])
                screw_access(("base motor screw", s, sr, st_), seat, (0, 0, -1), 2.75, BOLT_HEAD_H, [fb, belt], path_objs=[plate])
        for o in (box, belt, plate, lug):
            bpy.data.objects.remove(o)
    assert tt_gap >= 3.0 - 1e-6, ("base motor within 3 of the turntable", tt_gap)
    assert 3.0 <= BASE_PLATE_SCREW_L - BASE_PLATE_T <= M3_INSERT_DEPTH - 0.5, "base plate screws"
    ins = material_round(fb, at_base(BASE_LUG["r"][0] + M3_INSERT_DEPTH / 2, 0, PUSH_Z), (BASE_U[0], BASE_U[1], 0), M3_INSERT_R)
    assert ins >= WALL_MIN, ("push insert wall", ins)
    for dr, dt in BASE_PLATE_INSERTS:
        assert material_round(fb, at_base(BASE_BELT_C + dr, dt, sum(SHELF_Z) / 2), (0, 0, 1), M3_INSERT_R) >= WALL_MIN, ("shelf insert wall", dr, dt)
    under = [v.co.z for v in fb.data.vertices if v.co.z <= BENCH_Z + 0.01]
    assert under and max(under) - min(under) <= 0.02 and abs(min(under) - BENCH_Z) <= 0.02, ("drum's underside not flat on the bench", min(under), max(under))
    bpy.data.objects.remove(above)
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
    under = [tt, ring, fb, cap, spacer]
    for x, y in WALL_INSERTS["A"] + WALL_INSERTS["B"]:
        assert ray_len(tt, (x, y, TURNTABLE_Z + 1.0), (0, 0, -1)) is None, ("wall screw hole blocked", x, y)
        assert math.hypot(x, y) + 2.75 + 2.0 <= TURNTABLE_R, ("wall screw head off the turntable's edge", x, y)
        screw_access(("wall screw", x, y), (x, y, TURNTABLE_Z - TURNTABLE_T), (0, 0, -1), 2.75, BOLT_HEAD_H, under)
    REPORT.update({"base_belt_centres": belts, "base_push_screw": push, "base_motor_turntable_gap_mm": round(tt_gap, 2),
                   "drum": DRUM, "bench_z": BENCH_Z, "base_6810_spacing": BASE_6810_SPACING, "phi_stop_gaps_mm": gaps,
                   "phi_stop_mpa": {k: round(v, 1) for k, v in mpa.items()}, "base_hall_gap_mm": round(hall, 2),
                   "turntable_r": TURNTABLE_R, "ring_grooves": g, "ring_od": round(peak, 2),
                   "base_motor_at": [round(c, 2) for c in BASE_MOTOR_AT], "turntable_z": TURNTABLE_Z,
                   "fixed_base_lowest_z": round(min(v.co.z for v in fb.data.vertices), 2)})
    REPORT["bolts"].update({"spigot cap": CAP_SCREW_L, "ring to turntable hub": RING_SCREW_L, "base motor plate": BASE_PLATE_SCREW_L,
                            "base push screw": BASE_PUSH_L})
    for o in (turning, tab, block):
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
        boss = rod("socket boss", s - d * SOCKET["floor"], m, SOCKET["boss_r"], n=47)   # odd: no vertex row on the pinch insert's axis
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
        L.cut(f, rod("pinch insert", c + n * (SOCKET["boss_r"] - M3_INSERT_DEPTH), c + n * (SOCKET["boss_r"] + 2.3), M3_INSERT_R, n=30))
        L.cut(f, rod("pinch screw", c, c + n * (SOCKET["boss_r"] - M3_INSERT_DEPTH + 0.5), M3_CLEAR_R, n=30))


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
    # Five contacts: each pad's underside and the drum's underside on the bench.
    contacts = {"drum": round(min(v.co.z for v in fb.data.vertices), 3)}
    for phi in LEG_PHI:
        pad = copy(pd, "pad"); pad.data.transform(Matrix.Rotation(math.radians(phi - LEG_PHI[0]), 4, 'Z'))
        contacts[f"pad {phi:.0f}"] = round(min(v.co.z for v in pad.data.vertices), 3)
        bpy.data.objects.remove(pad)
    assert all(abs(z - BENCH_Z) <= 0.2 for z in contacts.values()), ("not five contacts on the bench", contacts)
    for phi in LEG_PHI:
        m, _, _ = (V(p) for p in leg(phi)); d = V(leg_dir(phi)); n = pinch_dir(d)
        c = m - d * PINCH_AT
        side = c + d * 2.5 + n * (SOCKET["boss_r"] + 5.0)          # beside the insert, on the boss's top line
        seat = side - n * ray_len(fb, side, -n) - d * 2.5
        screw_access(("leg pinch screw", phi), seat, n, 2.75, BOLT_HEAD_H, [fb, tt])
    assert CLAMP_TAB[0] >= 30 and CLAMP_TAB[1] >= 30 and CLAMP_TAB[2] >= 6, "clamp tab"
    pts = [(p[0], p[1]) for p in FOOT_PADS]
    edges = []
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        edges.append(abs(x0 * y1 - x1 * y0) / math.hypot(x1 - x0, y1 - y0))
    REPORT.update({"footprint_r_mm": round(min(edges), 1), "leg_deg": LEG_DEG, "foot_pads": [[round(c, 1) for c in p] for p in FOOT_PADS],
                   "socket_wall_mm": round(min(walls), 2), "pinch_insert_wall_mm": round(min(pinch), 2),
                   "pad_level_deg": round(max(level), 3), "contacts_z": contacts, "drum_h_mm": DRUM_H,
                   "shoulder_axis_above_bench_mm": round(-BENCH_Z, 1)})
    REPORT["bolts"].update({"leg pinch screws": 6})
    for o in [tt] + others:
        bpy.data.objects.remove(o)


bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["shoulder-stub"], PARTS["shoulder-stub-spacer"] = stub(), stub_spacer()
PARTS["shoulder-hub-b"] = hub_half("B")
PARTS["shoulder-output-plate"] = output_plate()
PARTS["plate-drill-jig"] = drill_jig()
PARTS["body-wall-A"], PARTS["body-wall-B"] = wall_a(), wall_b()
PARTS["shoulder-stop-collar"] = stop_collar()
for k in MOTORS:
    PARTS[f"shoulder-motor-plate-{k}"] = motor_plate(k)
PARTS["turntable"], PARTS["base-ring-130T"] = turntable(), base_ring()
PARTS["spigot-spacer"], PARTS["spigot-cap"] = spigot_spacer(), spigot_cap()
PARTS["fixed-base"], PARTS["base-motor-plate"] = fixed_base(), base_motor_plate()
PARTS["foot"], PARTS["foot-pad"] = foot_part(), foot_pad()
CHECKS += [check_shoulder_core, check_body, check_shoulder_drive, check_base, check_legs]
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
