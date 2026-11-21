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


def volume(o):
    bm = bmesh.new(); bm.from_mesh(o.data); v = abs(bm.calc_volume()); bm.free(); return v


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


_TREES = {}


def ctree(o):
    """A BVH tree of o, kept while o lives (the screw checks cast many rays at the same parts)."""
    vs = o.data.vertices   # Blender reuses a removed object's pointer: key on the mesh too, or a new part gets an old tree
    k = (o.as_pointer(), o.name, len(vs), tuple(vs[0].co) if len(vs) else None, tuple(vs[len(vs) // 2].co) if len(vs) else None)
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


def hull(objs, name):
    bm = bmesh.new()
    for o in objs:
        for v in o.data.vertices:
            bm.verts.new(v.co)
        bpy.data.objects.remove(o)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    return L._obj(name, bm)


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


def bore_r_at(o, cx, cz, y):
    rs = []
    for k in range(24):
        a = 2 * math.pi * (k + 0.37) / 24
        rs.append(ray_len(o, (cx, y, cz), (math.cos(a), 0, math.sin(a))))
    return sum(rs) / len(rs)


def output_plate():
    """Replaces the compact's forearm output plate: three bigger, longer dogs into the fixed hub's face."""
    y0, y1 = OUT_PLATE_Y
    p = cyl_y("shoulder-output-plate", 0, 0, OUT_PLATE_R, y0, y1, n=128)
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        L.union(p, cyl_y("dog", x, z, DOG_R, y1 - 0.01, y1 + DOG_H, n=48))
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        L.cut(p, cyl_y("screw", x, z, M3_CLEAR_R, y0 - 1.0, y1 + 1.0, n=32))
        L.cut(p, cyl_y("head", x, z, 3.0, y1 - 3.2, y1 + 1.0, n=48))   # the floor screws' heads stay in the hub's floor; this clears their shanks' fillets
    L.finish(p)
    PRINT_POSE["shoulder-output-plate"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -y0))
    return p


def shoulder_hub():
    """Fixed: its face on the output plate's dogs, a shoulder on plate A's 6810's inner ring, the journal through it
    out to the lug. The floor's M3s drive from the open bore; the journal's end has the lug's key slots and inserts."""
    H = HUB
    f, ysh, end = H["face_y"], H["bearing_y"][0], H["end_y"]
    h = cyl_y("shoulder-hub", 0, 0, H["shoulder_r"], f, ysh, n=192)
    L.union(h, hull([cyl_y("journal", 0, 0, H["land_r"], ysh - 0.01, end - END_CHAMFER, n=192),
                     cyl_y("end", 0, 0, H["land_r"] - END_CHAMFER, end - END_CHAMFER, end, n=192)], "journal"))   # one solid: a seam at the chamfer broke the key slots' cuts
    L.finish(h)
    floor = f + HUB_FLOOR
    cone_r = F.INSERT_PCD_R + 3.5                # the floor's ceiling: a 45-degree cone up from a small bridge
    L.cut(h, hull([cyl_y("bore cone", 0, 0, cone_r, floor, floor + 0.01, n=190),   # 192 put an edge on the 90-degree counterbore's line
                   cyl_y("bore", 0, 0, HUB_BORE_R, floor + (HUB_BORE_R - cone_r), end + 1.0, n=190)], "bore"))
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        L.cut(h, cyl_y("dog", x, z, DOG_R + 0.15, f - 1.0, f + DOG_H + 0.5, n=48))
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        L.cut(h, cyl_y("screw", x, z, M3_CLEAR_R, f - 1.0, floor + 1.0, n=32))
        L.cut(h, cyl_y("screw cb", x, z, 3.3, HUB_HEAD_Y, floor + 1.0, n=32))
    for a in KEY_ANGLES:
        s = L.box("key slot", HUB_BORE_R - 1.0, H["land_r"] + 1.0, end - KEY_DEPTH_Y, end + 1.0, -KEY_W / 2, KEY_W / 2)
        s.data.transform(Matrix.Rotation(-math.radians(a), 4, 'Y'))
        L.cut(h, s)
    for x, z in [polar(COLLAR_SCREW_R, a) for a in COLLAR_SCREW_ANGLES]:
        L.cut(h, cyl_y("lug insert", x, z, M3_INSERT_R, end - M3_INSERT_DEPTH, end + 1.0, n=32))
    PRINT_POSE["shoulder-hub"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -f))
    return h


def tube_axis(name):
    (lx, lz), (bx, bz) = TUBE_ENDS[name]
    return Vector((lx, TUBE_PLANE_Y, lz)), Vector((bx, TUBE_PLANE_Y, bz))


def tube_lengths():
    return {n: round((tube_axis(n)[1] - tube_axis(n)[0]).length + 2 * E.SOCKET_DEPTH, 1) for n in TUBE_ENDS}


def tubes():
    out = []
    for n in TUBE_ENDS:
        a, b = tube_axis(n)
        d = (b - a).normalized()
        out.append(rod(f"tube {n}", a - d * E.SOCKET_DEPTH, b + d * E.SOCKET_DEPTH, E.TUBE_OR, n=32))
    return out


def sockets(part, at_lug):
    """Each tube's socket in part and its open span cleared by TUBE_CLEAR: SOCKET_DEPTH deep in the lug, through the
    bracket's towers (the tubes go in from outside them: blind both ends, no tube could get between)."""
    for n in TUBE_ENDS:
        a, b = tube_axis(n)
        d = (b - a).normalized()
        mouth, into = (a, -d) if at_lug else (b, d)
        L.cut(part, rod("span", a + d * 0.5, b - d * 0.5, E.TUBE_OR + E.TUBE_CLEAR, n=48))   # short of the mouths: its end on a face left open edges
        L.cut(part, rod("socket", mouth - into * 0.5, mouth + into * (E.SOCKET_DEPTH if at_lug else 3 * BRACKET["x"]), E.SOCKET_R, n=48))


def socket_boss(mouth, into, name):
    w = E.SOCKET_R + E.SOCKET_WALL
    return rod(name, mouth, mouth + into * (E.SOCKET_DEPTH + 3.0), w, n=48)


def lug():
    """Keyed onto the hub's journal end outside plate A: clamps the 6810's inner ring, carries the tab and the magnet,
    and holds the three tubes in its spider, past the elbow belt's sweep."""
    y0, (s0, s1), end = LUG["y0"], LUG["spider_y"], HUB["end_y"]
    yg = y0 + LUG_GAP
    g = cyl_y("shoulder-lug", 0, 0, HUB["shoulder_r"], y0, yg + 0.01, n=192)
    L.union(g, cyl_y("sleeve", 0, 0, LUG["sleeve_r"], yg, s0 + 0.01, n=192))
    bosses = [cyl_y("hub end", 0, 0, LUG["sleeve_r"], s0, s1, n=96)]
    for n in TUBE_ENDS:
        a, b = tube_axis(n)
        bosses.append(socket_boss(a, -(b - a).normalized(), "boss"))
    L.union(g, hull(bosses, "spider"))
    tab = sector_y("tab", TAB_R[0], TAB_R[1], TAB_PHI - TAB_HALF, TAB_PHI + TAB_HALF, TAB_Y[0], TAB_Y[1])
    wedge = sector_y("tab's 45", TAB_R[0], TAB_R[0] + 0.2, TAB_PHI - TAB_HALF, TAB_PHI + TAB_HALF, TAB_Y[1], TAB_Y[1] + TAB_R[1] - TAB_R[0])
    L.union(g, hull([tab, wedge], "tab"))           # its far side at 45 degrees, so it prints spider-down without supports
    L.finish(g)
    L.cut(g, cyl_y("bore", 0, 0, HUB["land_r"] + 0.05, y0 - 1.0, end + 0.3, n=192))
    for a in KEY_ANGLES:
        t = L.box("tongue", HUB_BORE_R - 0.5, HUB["land_r"] + 0.5, end - KEY_DEPTH_Y + 0.3, end + 0.3 + 0.5, -KEY_W / 2 + 0.2, KEY_W / 2 - 0.2)
        t.data.transform(Matrix.Rotation(-math.radians(a), 4, 'Y'))
        L.union(g, t)
    for x, z in [polar(COLLAR_SCREW_R, a) for a in COLLAR_SCREW_ANGLES]:
        L.cut(g, cyl_y("screw", x, z, M3_CLEAR_R, end - 1.0, LUG_CB_Y + 0.01, n=32))
        L.cut(g, cyl_y("screw cb", x, z, 3.3, LUG_CB_Y, s1 + 1.0, n=32))
    sockets(g, True)
    mx, mz = polar(MAGNET_AT_R, TAB_PHI)
    L.cut(g, cyl_y("magnet", mx, mz, MAGNET_R + 0.1, TAB_Y[0] - 1.0, TAB_Y[0] + MAGNET_RECESS + MAGNET_D, n=32))
    PRINT_POSE["shoulder-lug"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, s1))
    return g


def socket_bracket():
    """On the turntable's ear: a base with M3s down into the turntable, and two towers holding the tubes' outer sockets."""
    X, tx, (f0, _), ft, rx = BRACKET["x"], BRACKET["tower_x"], BRACKET["flange_y"], BRACKET["flange_t"], BRACKET["root_x"]
    s0, s1 = LUG["spider_y"]
    zb = -SHOULDER_AXIS_Z
    b = L.box("shoulder-socket-bracket", -rx["rear"], rx["front"], f0, s1, zb, zb + ft)
    for name, sgn in (("front", 1), ("rear", -1)):
        top, root = L.box("top", *sorted((sgn * tx, sgn * X)), s0, s1, zb + ft - 0.01, BRACKET["tops"][name]), \
            L.box("root", *sorted((sgn * tx, sgn * rx[name])), s0, s1, zb + ft - 0.01, zb + ft)
        L.union(b, hull([top, root], name + " tower"))
    L.finish(b)
    sockets(b, False)
    for x, y in BRACKET_BOLTS:
        L.cut(b, L.cyl_z("bolt", x, y, M3_CLEAR_R, zb - 1.0, zb + ft + 1.0, n=30))
    PRINT_POSE["shoulder-socket-bracket"] = Matrix.Translation((0, 0, -zb))
    return b


def rod_post():
    """Outside the shoulder belt on plate B's side: a 625 on the input rod's end, two M3s down into the turntable."""
    (y_in, y_out), hw, top, ft = POST["y"], POST["half"], POST["top"], POST["foot_t"]
    zb = -SHOULDER_AXIS_Z
    p = L.box("shoulder-rod-post", -hw, hw, y_out, y_in, zb, 0.0)
    L.union(p, cyl_y("top", 0, 0, top, y_out, y_in, n=96))
    L.union(p, L.box("foot", -POST["foot_x"], POST["foot_x"], y_out, y_in, zb, zb + ft))
    L.finish(p)
    L.cut(p, cyl_y("625", 0, 0, B625[1] + 0.05, y_out - 1.0, y_in - POST["lip_t"], n=96))
    L.cut(p, cyl_y("lip", 0, 0, POST["lip_r"], y_out - 1.0, y_in + 1.0, n=64))
    for x, y in POST_BOLTS:
        L.cut(p, L.cyl_z("bolt", x, y, M3_CLEAR_R, zb - 1.0, zb + ft + 1.0, n=30))
    PRINT_POSE["shoulder-rod-post"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -y_out))
    return p


def compact_posed():
    """The shoulder compact's housing: its cycloid frame's z runs from the rear face on plate B (COMPACT_REAR_Y) towards plate A (+y)."""
    m = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, COMPACT_REAR_Y, 0))
    halves = [posed_stl(os.path.join(COMPACT, "housing-rear.stl"), "chr", m),
              posed_stl(os.path.join(COMPACT, "housing-front.stl"), "chf", m @ Matrix.Diagonal((1, -1, -1, 1)))]
    c = join(halves, "compact")   # a boolean union: two shells on a shared face upset the overlap tests
    for o in halves:
        bpy.data.objects.remove(o)
    return c


def compact_bolts():
    """The R30 M3 x 50s through plate B and the housing: heads on plate B's outer face, nuts on the housing's front face."""
    yb, yn = PLATE_FACES["B"][0], COMPACT_REAR_Y + F.HOUSING_L
    out = []
    for a in F.BOLT_ANGLES:
        x, z = polar(F.BOLT_R, a)
        out += [cyl_y("bolt head", x, z, 2.75, yb - BOLT_HEAD_H, yb + 0.01, n=24), cyl_y("nut", x, z, NUT_AF / math.sqrt(3), yn - 0.01, yn + 2.4, n=6)]
    return out


def sh_motor_box(slot):
    h, zm = E.MOTOR_SQ / 2, E.SH_MOTOR_Z + slot * E.SH_MOTOR_SLOT + E.UPPER_L
    b = L.box("shoulder motor", -h, h, -E.Y_REAR, -E.Y_REAR + E.SH_MOTOR_L, -h, h)
    b.data.transform(Matrix.Translation((0, 0, zm)) @ Matrix.Rotation(math.radians(E.SH_MOTOR_TURN), 4, 'Y'))
    return b


def pulley_env(z, r_od, r_hub=9.0):
    y0 = E.SH_PULLEY_Y0
    e = cyl_y("hub", 0, z, r_hub + 0.5, y0 - E.PULLEY_HUB - 0.01, y0 + 0.01)
    L.union(e, cyl_y("teeth", 0, z, r_od + 1.5, y0 - E.PULLEY_H, y0 - E.PULLEY_HUB))
    return e


def sh_belt_envelope(slot):
    """The 80T, the 20T and the belt outside plate B, the motor at slot (-1 to +1 of its travel), in the shoulder frame."""
    zm = E.SH_MOTOR_Z + slot * E.SH_MOTOR_SLOT + E.UPPER_L
    band = hull([cyl_y("a", 0, 0, R80_OD + E.BELT_T, E.SH_TEETH_Y[0] - 1.5, E.SH_TEETH_Y[1] + 1.5),
                 cyl_y("b", 0, zm, E.R20_OD + E.BELT_T, E.SH_TEETH_Y[0] - 1.5, E.SH_TEETH_Y[1] + 1.5)], "shoulder belt")
    L.union(band, pulley_env(0.0, R80_OD))
    L.union(band, pulley_env(zm, E.R20_OD))
    return band


def sh_belt_loop(slot):
    """The shoulder belt's loop only (not inside its spans) and both pulleys, the motor at slot: what a driver can't pass."""
    zm = E.SH_MOTOR_Z + slot * E.SH_MOTOR_SLOT + E.UPPER_L
    y0, y1 = E.SH_TEETH_Y[0] - 1.5, E.SH_TEETH_Y[1] + 1.5
    band = hull([cyl_y("a", 0, 0, R80_OD + E.BELT_T, y0, y1, n=192), cyl_y("b", 0, zm, E.R20_OD + E.BELT_T, y0, y1)], "shoulder belt loop")
    L.cut(band, hull([cyl_y("a", 0, 0, R80_OD - GROOVE_DEPTH - 0.5, y0 - 1.0, y1 + 1.0, n=192),
                      cyl_y("b", 0, zm, E.R20_OD - GROOVE_DEPTH - 0.5, y0 - 1.0, y1 + 1.0)], "inside the belt"))
    L.union(band, pulley_env(0.0, R80_OD))
    L.union(band, pulley_env(zm, E.R20_OD))
    return band


def ring_zone():
    r = cyl_y("6810 outer ring", 0, 0, RING_ZONE[1], LIP_FACE_Y["A"], PLATE_FACES["A"][1], n=192)
    L.cut(r, cyl_y("bore", 0, 0, RING_ZONE[0], LIP_FACE_Y["A"] - 1.0, PLATE_FACES["A"][1] + 1.0, n=192))
    return r


def fixed_shoulder():
    """What the hub holds still: the hub, the output plate, the lug, the tubes, the socket bracket and the post."""
    return [copy(PARTS[n], n) for n in ("shoulder-hub", "shoulder-output-plate", "shoulder-lug", "shoulder-socket-bracket", "shoulder-rod-post")] + tubes()


def turning_shoulder(psi):
    """What turns with the arm at psi: the plates, both motors at both slot ends, both belts, the cross members, the
    shoulder compact's housing and bolts, and plate A's 6810's outer ring."""
    objs = list(upper_arm_moving().values()) + [cross_members(), compact_posed(), ring_zone()] + compact_bolts()
    objs += [sh_motor_box(s) for s in (-1, 1)] + [sh_belt_envelope(s) for s in (-1, 1)]
    o = concat(objs, f"turning {psi}")
    o.data.transform(rot_shoulder(psi))
    return o


def check_shoulder_core():
    names = ("shoulder-hub", "shoulder-output-plate", "shoulder-lug", "shoulder-socket-bracket", "shoulder-rod-post")
    hub, op, lg, br, post = (PARTS[n] for n in names)
    for n in names:
        part_ok(n); on_bed(n)
    pa, pb = elbow_part("upper-plate-A"), elbow_part("upper-plate-B")
    cp = compact_posed()
    # Plate A's 6810 on the hub: the land across its width, the inner ring clamped by the hub's shoulder and the lug.
    y0, y1 = HUB["bearing_y"]
    land = radial_r(hub, (y0 + y1) / 2)
    assert B6810[0] - 0.01 <= land <= B6810[0] + 0.1, ("hub's land in plate A's 6810", land)
    for r in (B6810[0] + 0.15, HUB["shoulder_r"] - 0.15):
        up, down = ray_len(hub, (r, (y0 + y1) / 2, 0), (0, -1, 0)), ray_len(lg, (r, (y0 + y1) / 2, 0), (0, 1, 0))
        assert up is not None and abs(up - (y1 - y0) / 2) < 0.02, ("hub's shoulder not on the inner ring", r, up)
        assert down is not None and abs(down - (y1 - y0) / 2) < 0.02, ("lug not on the inner ring", r, down)
    assert HUB["shoulder_r"] - B6810[0] >= 0.3, "inner ring contact under 0.3"
    band = [v.co for o in (hub, lg) for v in o.data.vertices if y0 - 0.5 <= v.co.y <= y1 + 0.5 and math.hypot(v.co.x, v.co.z) > RING_ZONE[0] - 0.5]
    assert not band, ("fixed part within 0.5 of the 6810's outer ring", band[:3])
    # Running gaps: everything fixed against everything that turns with the arm, through the range.
    fixed = concat(fixed_shoulder(), "fixed shoulder")
    fv = [v.co.copy() for v in fixed.data.vertices]; fbox, tf = bounds(fv, 10.0), tree(fixed)
    arm0 = turning_shoulder(0.0)
    worst, at = math.inf, None
    for psi in range(int(PSI_RANGE[0]), int(PSI_RANGE[1]) + 1):
        arm = copy(arm0, "arm"); arm.data.transform(rot_shoulder(psi))
        g = sweep_gap(arm, tf, fv, fbox)
        if g < worst:
            worst, at = g, psi
        bpy.data.objects.remove(arm)
    assert worst >= 0.5, ("a fixed part of the shoulder within 0.5 of a turning one", round(worst, 2), at)
    # The link: the output plate on the carrier, its dogs in the hub's face, its screws into the carrier's inserts.
    f = HUB["face_y"]
    assert overlap(op, hub) < 0.05 and touching(op, hub), "output plate's dogs don't sit in the hub's face"
    assert abs(min(v.co.y for v in op.data.vertices) - COMPACT_Y) < 0.01, "output plate not on the compact's carrier"
    assert overlap(op, cp) < 0.05, "output plate hits the housing"
    dog = SHOULDER_DESIGN_NMM / DOG_PCD_R / len(DOG_ANGLES) / (2 * DOG_R * DOG_H)
    J = math.pi / 2 * (B6810[0] ** 4 - HUB_BORE_R ** 4)
    shear = SHOULDER_DESIGN_NMM * B6810[0] / J
    assert dog <= PRINTED_MPA and shear <= PRINTED_MPA, ("link", dog, shear)
    for x, z in [polar(DOG_PCD_R, a) for a in DOG_ANGLES]:
        assert ray_len(hub, (x, f - 0.01, z), (0, 1, 0)) >= DOG_H + 0.2, "dog hole too shallow"
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        y_floor = f + HUB_FLOOR + 1.0
        seat = y_floor - ray_len(hub, (x + 2.5, y_floor, z), (0, -1, 0))
        reach = HUB_SCREW_L - (seat - COMPACT_Y)
        assert 3.0 <= reach <= 4.0, ("M3 x 12 into the carrier's inserts", reach)
        assert ray_len(hub, (x, f - 0.01, z), (0, 1, 0)) is None, ("hub floor screw hole blocked", x, z)
    # The lug: keyed one way only, its inserts' walls, its sockets, the stops on plate A and the Hall.
    over = copy(lg, "lug turned"); over.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))
    turned = overlap(over, hub)
    assert turned >= 1.0, ("the lug goes on the hub turned half round", turned)
    bpy.data.objects.remove(over)
    assert overlap(lg, hub) < 0.05 and touching(lg, hub), "lug doesn't seat on the hub"
    end = HUB["end_y"]
    for a in KEY_ANGLES:
        kx, kz = polar((HUB_BORE_R + B6810[0]) / 2, a)
        slot = ray_len(hub, (kx, end + 1.0, kz), (0, -1, 0))
        assert slot is not None and abs(slot - 1.0 - KEY_DEPTH_Y) < 0.05, ("key slot in the hub", a, slot)
    key_mpa = SHOULDER_DESIGN_NMM / ((HUB_BORE_R + B6810[0]) / 2) / len(KEY_ANGLES) / (KEY_DEPTH_Y * (B6810[0] - HUB_BORE_R))
    assert key_mpa <= PRINTED_MPA, ("lug's tongues", round(key_mpa, 1))
    walls = []
    for a in COLLAR_SCREW_ANGLES:
        x, z = polar(COLLAR_SCREW_R, a)
        d = ray_len(hub, (x + 1.85, end + 1.0, z), (0, -1, 0))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("lug insert in the hub", a, d)
        walls.append(material_round(hub, (x, end - M3_INSERT_DEPTH / 2, z), (0, 1, 0), M3_INSERT_R))
    assert min(walls) >= WALL_MIN, ("material round the lug's inserts", walls)
    engage = COLLAR_SCREW_L - (LUG_CB_Y - end)
    assert 3.0 <= engage <= M3_INSERT_DEPTH - 0.5, ("lug screws", engage)
    check_tubes(lg, br)
    stops = check_stops(lg, pa)
    # The post: the 625 on the axis, outside the shoulder belt, the rod's length and side load.
    (py_in, py_out) = POST["y"]
    seat = radial_r(post, (py_out + py_in - POST["lip_t"]) / 2, inward=False)
    assert B625[1] - 0.01 <= seat <= B625[1] + 0.1, ("625 seat", seat)
    off = max(abs(ray_len(post, (0, (py_out + py_in - POST["lip_t"]) / 2, 0), (math.cos(a), 0, math.sin(a))) - seat) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2))
    assert off <= 0.05 + 0.1, ("625 seat off the shoulder axis", off)
    for s in (-1, 1):
        belt = sh_belt_envelope(s)
        assert min_gap(belt, post) >= 1.0 and min_gap(post, belt) >= 1.0, ("post within 1 of the shoulder belt", s)
        bpy.data.objects.remove(belt)
    span = COMPACT_REAR_Y - sum(POST["y"]) / 2       # the rod as a beam from the housing's rear (its input bearing) to the 625
    belt_at = COMPACT_REAR_Y - E.SH_BELT_PLANE_Y
    side = {"625": round(BELT_PULL_N * belt_at / span, 1), "compact input": round(BELT_PULL_N * (span - belt_at) / span, 1),
            "span_mm": round(span, 1)}
    # Screws: room round each head and a straight path to it, with every part in place at that step.
    zb = -SHOULDER_AXIS_Z
    tt = turntable_disc(SHOULDER_AXIS_Z)
    for a in F.INSERT_ANGLES:
        x, z = polar(F.INSERT_PCD_R, a)
        screw_access(("hub floor", a), (x, HUB_HEAD_Y, z), (0, 1, 0), 2.75, BOLT_HEAD_H, [pa, pb, hub, op, cp])
    for a in COLLAR_SCREW_ANGLES:
        x, z = polar(COLLAR_SCREW_R, a)
        screw_access(("lug", a), (x, LUG_CB_Y, z), (0, 1, 0), 2.75, BOLT_HEAD_H, [pa, hub, lg, br])
    for s in (-1, 1):   # tightened after the belt is tensioned: a driver from outside plate B, between or outside its spans
        loop, zm = sh_belt_loop(s), E.SH_MOTOR_Z + s * E.SH_MOTOR_SLOT + E.UPPER_L
        for dx, dz in E.SH_MOTOR_SCREWS:
            screw_access(("shoulder motor screw", s, round(dx, 1), round(dz, 1)), (dx, PLATE_FACES["B"][0], zm + dz), (0, -1, 0), 2.75, BOLT_HEAD_H, [pb, loop])
        bpy.data.objects.remove(loop)
    for (x, y), part in [(xy, br) for xy in BRACKET_BOLTS] + [(xy, post) for xy in POST_BOLTS]:
        screw_access(("turntable bolt", part.name, x), (x, y, zb + BRACKET["flange_t"]), (0, 0, 1), 2.75, BOLT_HEAD_H,
                     [pa, pb, hub, lg, br, post, cp] + tubes())
    assert 3.0 <= TURNTABLE_SCREW_L - BRACKET["flange_t"] <= M3_INSERT_DEPTH - 0.5, "turntable bolts"
    REPORT.update({"shoulder_core_min_gap_mm": round(worst, 2), "shoulder_core_min_gap_psi": at, "lug_180_overlap_mm3": round(turned, 1),
                   "link_mpa": {"dog bearing": round(dog, 1), "hub shear": round(shear, 2), "lug tongues": round(key_mpa, 1)},
                   "compact_y": COMPACT_Y, "hub": HUB, "rod_out_mm": round(ROD_OUT, 1), "rod_side_load_n": side,
                   "lug_insert_wall_mm": round(min(walls), 2), **stops,
                   "bolts": {"hub floor to compact carrier": HUB_SCREW_L, "lug to the hub's journal end": COLLAR_SCREW_L,
                             "bracket and post into the turntable": TURNTABLE_SCREW_L,
                             "compact to plate B (nut on the housing's front face)": bolt_for_nut(E.PLATE_T + F.HOUSING_L)}})
    for o in (pa, pb, cp, fixed, arm0, tt):
        bpy.data.objects.remove(o)


def check_tubes(lg, br):
    t_all = concat(tubes(), "tubes")
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        d = (b - a).normalized()
        assert (b - a).length >= 20.0, (name, "open span under 20")
        for part, mouth, into in ((lg, a, -d), (br, b, d)):
            inside_ = ray_len(part, mouth + into * 1.0, into)
            if part is br:
                assert inside_ is None, (name, "the tower's socket doesn't run through for the tube to go in from outside", inside_)
            else:
                assert inside_ is not None and abs(inside_ + 1.0 - E.SOCKET_DEPTH) < 0.06, (name, part.name, "socket depth", inside_)
            p = mouth + into * (E.SOCKET_DEPTH - 1.0)
            side = d.cross(Vector((0, 1, 0))).normalized()
            for w in (side, -side, Vector((0, 1, 0)), Vector((0, -1, 0))):
                wall = ray_len(part, p, w)
                assert wall is not None and abs(wall - E.SOCKET_R) < 0.1, (name, part.name, "tube end not walled in its socket", wall)
                assert material_round(part, p, d, E.SOCKET_R) >= E.SOCKET_WALL - 0.05, (name, part.name, "socket wall")
    for o in (lg, br):
        assert overlap(o, t_all) < 1.0, ("a tube runs into a part outside its socket", o.name, overlap(o, t_all))
    loads = truss_loads()
    assert max(abs(f) for f in loads.values()) <= 600.0, ("tube axial load", loads)
    towers = tower_mpa(br)
    assert max(s for s, _ in towers.values()) <= PRINTED_MPA, ("a bracket tower bending across its layers (MPa, at z)", towers)
    socket_m = ARM_LOAD_N * TUBE_PLANE_Y / len(TUBE_ENDS)      # the arm's weight off the tubes' plane, shared at the sockets
    REPORT.update({"tube_lengths_mm": tube_lengths(), "tube_axial_n": loads, "tube_socket_bending_nmm": round(socket_m), "bracket_tower_mpa": towers})
    bpy.data.objects.remove(t_all)


def check_bracket_assembly():
    """The arm on the turntable with the lug and post on: the bracket slides in along the shoulder axis from outside onto
    the ear, then each tube, glued, slides in along its own axis from outside its tower into the lug's socket, the
    others already in."""
    lg, br, post = PARTS["shoulder-lug"], PARTS["shoulder-socket-bracket"], PARTS["shoulder-rod-post"]
    arm, tt = turning_shoulder(0.0), turntable_disc(SHOULDER_AXIS_Z)
    fixed = [lg, post, arm, tt]
    b = copy(br, "bracket"); b.data.transform(Matrix.Translation((0, 0, 0.05)))   # off the turntable's face it slides on
    pl = concat([copy(p, "p") for p in fixed], "placed")
    hit = slides_home(b, (0, -1, 0), LUG["spider_y"][1] + 1.0 - BRACKET["flange_y"][0], pl)
    bpy.data.objects.remove(pl); bpy.data.objects.remove(b)
    assert hit is None, ("the bracket can't slide in along the axis onto the ear", hit)
    ts = dict(zip(TUBE_ENDS, tubes()))
    for name, t in ts.items():
        a, bm = tube_axis(name)
        d = (bm - a).normalized()
        inner = a - d * E.SOCKET_DEPTH
        out_x = math.copysign(max(BRACKET["root_x"].values()), d.x)
        pl = concat([copy(p, "p") for p in fixed + [br] + [o for n, o in ts.items() if n != name]], "placed")
        hit = slides_home(t, -d, (out_x - inner.x) / d.x + 1.0, pl)
        bpy.data.objects.remove(pl)
        assert hit is None, (name, "tube can't slide in from outside its tower to the lug's socket", hit)
    for o in list(ts.values()) + [arm, tt]:
        bpy.data.objects.remove(o)


def tower_mpa(br):
    """The worst bending plus direct stress across each of br's towers, at every 1 mm from its root on the base up to
    its top tube, from its tubes' forces, the design torque either way round. The section's width is measured off the
    part beside the sockets; where a socket crosses the section its diameter comes off the section's depth."""
    root_z = -SHOULDER_AXIS_Z + BRACKET["flange_t"]
    y = LUG["spider_y"][0] + 0.5
    depth = LUG["spider_y"][1] - LUG["spider_y"][0]
    out = {}
    for tower, names, sgn in (("front", ("front", "diagonal"), 1), ("rear", ("rear",), -1)):
        axes = [tube_axis(n) for n in names]
        top = max(m.z for _, m in axes) - E.SOCKET_R
        z = root_z + 0.5
        while z < top:
            x_out = sgn * (3 * BRACKET["x"] - ray_len(br, (sgn * 3 * BRACKET["x"], y, z), (-sgn, 0, 0)))
            x_in = sgn * (BRACKET["tower_x"] - 5.0 + ray_len(br, (sgn * (BRACKET["tower_x"] - 5.0), y, z), (sgn, 0, 0)))
            h, x0 = abs(x_out - x_in), (x_out + x_in) / 2
            crossed = any(min(m.z, m.z + (x_out - m.x) * (m - a).z / (m - a).x) - E.SOCKET_R <= z <= m.z + E.SOCKET_R for a, m in axes)
            b = depth - (2 * E.SOCKET_R if crossed else 0.0)
            for torque in (SHOULDER_DESIGN_NMM, -SHOULDER_DESIGN_NMM):
                f = truss_loads(torque)
                mo = n = 0.0
                for name, (a, mouth) in zip(names, axes):
                    if mouth.z - E.SOCKET_R <= z:
                        continue
                    force = -f[name] * (mouth - a).normalized()   # on the tower: a tube in tension pulls it towards the lug
                    mo += (mouth.x - x0) * force.z - (mouth.z - z) * force.x
                    n += force.z
                s = abs(mo) / (b * h * h / 6) + abs(n) / (b * h)
                if s > out.get(tower, (0.0,))[0]:
                    out[tower] = (round(s, 1), round(z, 1))
            z += 1.0
    return out


def truss_loads(torque=SHOULDER_DESIGN_NMM):
    """Axial force in each tube (tension +) with the arm's weight and the torque on the lug."""
    names = list(TUBE_ENDS)
    us, ps = [], []
    for n in names:
        a, b = tube_axis(n)
        u = (b - a).normalized()
        us.append((u.x, u.z)); ps.append((a.x, a.z))
    m = [[us[i][0] for i in range(3)], [us[i][1] for i in range(3)], [ps[i][0] * us[i][1] - ps[i][1] * us[i][0] for i in range(3)]]
    f = mathutils.Matrix(m).inverted() @ Vector((0.0, ARM_LOAD_N, torque))
    return {n: round(f[i], 1) for i, n in enumerate(names)}


def check_stops(lg, pa):
    """The lug's tab against plate A's blocks (elbow.py builds them from E.SH_PSI_STOPS); the magnet over the sensor."""
    assert PSI_STOPS == E.SH_PSI_STOPS
    blocks = copy(pa, "plate A's blocks")
    L.cut(blocks, L.box("the plate", -300.0, 300.0, -100.0, PLATE_FACES["A"][1] + 0.05, -300.0, 300.0))
    gaps = {}
    for psi in (PSI_STOPS[0], PSI_STOPS[0] + 2.0, 0.0, PSI_STOPS[1] - 2.0, PSI_STOPS[1]):
        a = copy(blocks, "a"); a.data.transform(rot_shoulder(psi))
        gaps[psi] = round(min(min_gap(lg, a), min_gap(a, lg)), 2)
        bpy.data.objects.remove(a)
    bpy.data.objects.remove(blocks)
    assert gaps[PSI_STOPS[0]] <= 0.3 and gaps[PSI_STOPS[1]] <= 0.3, ("tab doesn't meet the stops", gaps)
    assert gaps[PSI_STOPS[0] + 2.0] >= 1.0 and gaps[PSI_STOPS[1] - 2.0] >= 1.0, ("stops within 1 mm inside the range", gaps)
    stall_n = SHOULDER_DESIGN_NMM / ((STOP_R[0] + STOP_R[1]) / 2)
    tang = math.radians(STOP_BLOCK_DEG) * STOP_R[0]
    lever = (TAB_Y[1] - TAB_Y[0]) / 2 + 0.5
    stop_mpa = stall_n * lever / ((STOP_R[1] - STOP_R[0]) * tang ** 2 / 6)
    assert stop_mpa <= PRINTED_MPA, ("stop block bending, across layers", round(stop_mpa, 1))
    mx, mz = polar(MAGNET_AT_R, TAB_PHI)
    floor = ray_len(lg, (mx, TAB_Y[0] - 1.0, mz), (0, 1, 0)) - 1.0
    magnet_face = TAB_Y[0] + floor - MAGNET_D
    gap = magnet_face - PLATE_FACES["A"][1]
    assert 1.0 <= gap <= 2.0, ("Hall gap at home", gap)
    assert ray_len(pa, (mx, PLATE_FACES["A"][1] + 1.0, mz), (0, -1, 0)) >= 1.0 + SENSOR[2], "sensor pocket missing under the magnet"
    return {"stop_gaps_mm": gaps, "stop_block_mpa": round(stop_mpa, 1), "hall_gap_mm": round(gap, 2)}


def turntable_disc(h):
    t = L.cyl_z("turntable's top", 0, 0, TURNTABLE_R, -h - TURNTABLE_T, -h, n=192)
    L.union(t, L.box("ear", *EAR["x"], *EAR["y"], -h - TURNTABLE_T, -h))
    return t


_TURN = {}


def psi_limits(h):
    """The widest psi each way, in 1-degree steps from 89, at which what turns with the arm stays 1.0 from a turntable
    with its top at -h (and its ear)."""
    if "arm" not in _TURN:
        _TURN["arm"] = turning_shoulder(0.0)
    fixed = concat([turntable_disc(h)], "turntable")   # the fixed shoulder has its own 0.5 sweep: the lug sits 0.6 off the 6810's outer ring at every psi
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
    """SHOULDER_AXIS_Z: the lowest, in 0.5 steps, that keeps everything turning 3 above the turntable at psi 0 and lets
    the stops sit past 92. PSI_STOPS: the widest the turntable's rim allows, less 2, the same both ways."""
    h = SHOULDER_AXIS_Z
    arm = copy(_TURN.setdefault("arm", turning_shoulder(0.0)), "arm")
    low = min(v.co.z for v in arm.data.vertices)
    bpy.data.objects.remove(arm)
    lim = psi_limits(h)
    stops = min(lim) - 2
    assert low + h >= 3.0 - 1e-6, ("a turning part within 3 of the turntable", round(low + h, 2))
    assert stops > 92, ("stops not past 92", lim)
    assert PSI_STOPS == (-float(stops), float(stops)), ("PSI_STOPS should be", stops)
    lo = psi_limits(h - 0.5)
    assert low + h - 0.5 < 3.0 or min(lo) - 2 <= 92, ("the axis could go 0.5 lower", lo)
    REPORT.update({"psi_stops": PSI_STOPS, "psi_range": PSI_RANGE, "psi_limits_raw": lim, "under_axis_clear_mm": round(low + h, 2),
                   "shoulder_axis_z": SHOULDER_AXIS_Z})


def slot_u(name, u, w, r, y0, y1, n=16):
    """A round-ended slot along u, MOTOR_SLOT each way, in the local frame."""
    pts = []
    for e in (1, -1):
        cu = u + e * MOTOR_SLOT
        pts += [(cu + e * r * math.sin(math.radians(180 * k / n)), w - e * r * math.cos(math.radians(180 * k / n))) for k in range(n + 1)]
    return prism_z(name, pts, y0, y1)


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
    """A plate with an ear under the shoulder's socket bracket; the ring screws up into its underside; the base stop's tab and the Hall magnet under it."""
    zt, zb = TURNTABLE_Z, TT_HUB_Z0
    t = L.cyl_z("turntable", 0, 0, TURNTABLE_R, zb, zt, n=192)
    L.union(t, L.box("ear", *EAR["x"], *EAR["y"], zb, zt))
    L.union(t, phi_tab())
    L.finish(t)
    for a in RING_SCREW_ANGLES:
        x, y = polar(RING_SCREW_R, a)
        L.cut(t, L.cyl_z("ring insert", x, y, M3_INSERT_R, zb - 1.0, zb + M3_INSERT_DEPTH, n=32))
    for x, y in BRACKET_BOLTS + POST_BOLTS:
        L.cut(t, L.cyl_z("bracket insert", x, y, M3_INSERT_R, zt - M3_INSERT_DEPTH, zt + 1.0, n=31))
    mx, my = hall_xy()
    L.cut(t, L.cyl_z("magnet", mx, my, MAGNET_R + 0.1, PHI_TAB_Z[1] - 1.0, PHI_TAB_Z[1] + MAGNET_RECESS + MAGNET_D, n=32))
    PRINT_POSE["turntable"] = basis((1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, zt))
    return t


def base_ring():
    """The 130T under the turntable, teeth as htd3m_pulley's, a thick top flange so the teeth sit under the stop tab, and
    the cylinder down through the drum's two 6810s: its shoulder on the upper inner ring, inserts in its end for the retainer."""
    r = od_r(RING_TEETH)
    g = L.cyl_z("base-ring-130T", 0, 0, r, RING_Z[0] - 0.01, RING_Z[1] + 0.01, n=720)
    for k in range(RING_TEETH):
        a = 2 * math.pi * k / RING_TEETH; c = r - GROOVE_DEPTH + GROOVE_R
        L.cut(g, L.cyl_z("groove", c * math.cos(a), c * math.sin(a), GROOVE_R, RING_Z[0] - 1.0, RING_Z[1] + 1.0, n=24))
    L.union(g, L.cyl_z("flange", 0, 0, r + FLANGE_LIP, RING_Z[1], TT_HUB_Z0, n=720))
    L.union(g, L.cyl_between("cone", (0, 0, RING_Z[0] + 0.01), (0, 0, RING_Z0), r - GROOVE_DEPTH, n=720, r_end=r + FLANGE_LIP))
    L.union(g, L.cyl_z("shoulder", 0, 0, CYL["shoulder_r"], DRUM_TOP, RING_Z0 + 0.01, n=192))
    L.union(g, L.cyl_z("cylinder", 0, 0, CYL["r"], CYL["end_z"], DRUM_TOP + 0.01, n=192))
    L.finish(g)
    L.cut(g, L.cyl_z("bore", 0, 0, CYL["bore_r"], CYL["end_z"] - 1.0, TT_HUB_Z0 + 1.0, n=192))
    for a in RING_SCREW_ANGLES:
        x, y = polar(RING_SCREW_R, a)
        L.cut(g, L.cyl_z("screw", x, y, M3_CLEAR_R, RING_CB_Z - 0.01, TT_HUB_Z0 + 1.0, n=32))
        L.cut(g, L.cyl_z("screw cb", x, y, 3.3, RING_Z0 - 1.0, RING_CB_Z, n=32))
    for a in RETAINER["angles"]:
        x, y = polar(RETAINER["screw_r"], a)
        L.cut(g, L.cyl_z("retainer insert", x, y, M3_INSERT_R, CYL["end_z"] - 1.0, CYL["end_z"] + M3_INSERT_DEPTH, n=32))
    PRINT_POSE["base-ring-130T"] = basis((1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, TT_HUB_Z0))
    return g


def base_spacer():
    s = L.cyl_z("base-spacer", 0, 0, SPACER_R, *SPACER_Z, n=192)
    L.cut(s, L.cyl_z("bore", 0, 0, CYL["r"] + 0.1, SPACER_Z[0] - 1.0, SPACER_Z[1] + 1.0, n=192))
    PRINT_POSE["base-spacer"] = Matrix.Translation((0, 0, -SPACER_Z[0]))
    return s


def base_retainer():
    z1 = BASE_6810_Z[1]
    c = L.cyl_z("base-retainer", 0, 0, RETAINER["r"], z1 - RETAINER["t"], z1, n=192)
    L.cut(c, L.cyl_z("bore", 0, 0, RETAINER["bore_r"], z1 - RETAINER["t"] - 1.0, z1 + 1.0, n=96))
    for a in RETAINER["angles"]:
        x, y = polar(RETAINER["screw_r"], a)
        L.cut(c, L.cyl_z("screw", x, y, M3_CLEAR_R, z1 - RETAINER["t"] - 1.0, z1 + 1.0, n=32))
    PRINT_POSE["base-retainer"] = Matrix.Translation((0, 0, -(z1 - RETAINER["t"])))
    return c


def base_frame():
    """The base motor's local frame: x = r out along BASE_U, y = t across it, z up."""
    return basis((BASE_U[0], BASE_U[1], 0), (-BASE_U[1], BASE_U[0], 0), (0, 0, 1), (0, 0, 0))


def at_base(r, t, z):
    return base_frame() @ Vector((r, t, z))


def base_motor_box(slot):
    h, r = MOTORS["17"]["sq"] / 2, BASE_BELT_C + slot
    b = L.box("base motor", -h, h, -h, h, BASE_MOTOR_FACE_Z - BASE_MOTOR_L, BASE_MOTOR_FACE_Z)
    b.data.transform(base_frame() @ Matrix.Translation((r, 0, 0)) @ Matrix.Rotation(math.radians(45.0), 4, 'Z'))
    return b


def base_belt_envelope(slot):
    """The belt between the 130T and the 20T (not the ring's inside), and the 20T standing on the clamp plate, at slot."""
    x, y = base_motor_at(slot)
    z0, z1 = RING_Z[0] - 1.5, RING_Z[1] + 1.5
    band = hull([L.cyl_z("a", 0, 0, od_r(RING_TEETH) + E.BELT_T, z0, z1, n=192), L.cyl_z("b", x, y, E.R20_OD + E.BELT_T, z0, z1)], "base belt")
    L.cut(band, hull([L.cyl_z("ring", 0, 0, od_r(RING_TEETH) - GROOVE_DEPTH - 0.5, z0 - 1.0, z1 + 1.0, n=192),
                      L.cyl_z("20T", x, y, E.R20_OD - GROOVE_DEPTH - 0.5, z0 - 1.0, z1 + 1.0)], "inside the belt"))   # the loop only: screws sit between its spans
    L.union(band, L.cyl_z("20T teeth", x, y, E.R20_OD + 1.5, z0, z1))
    L.union(band, L.cyl_z("20T hub", x, y, 9.5, BASE20_HUB_Z[0], z0 + 0.01))
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


def drum_rib(phi):
    """In the leg's vertical plane: a full-height web from the hub tube out under the socket's boss to the wall, filleted onto
    the hub, so the hub is held to the drum down its whole height and not only at its top."""
    zt, zb = DRUM_TOP, BENCH_Z - 2.0                                # past the drum's own faces: no coplanar union
    t, n = math.tan(math.radians(LEG_DEG)), (math.sin(math.radians(LEG_DEG)), math.cos(math.radians(LEG_DEG)))
    mr, mz, h = SOCKET["mouth_r"], SOCKET_MOUTH_Z, SOCKET["boss_r"] * TEARDROP
    rw = DRUM_R - DRUM_WALL / 2
    tip = (mr - h * n[0], mz - h * n[1] + 0.5)          # the teardrop's point on the boss's end face
    pts = [(HUB_TUBE_R - 0.5, zt), (mr + (zt - mz) * t, zt), tip, (rw, tip[1] - (tip[0] - rw)), (rw, zb), (HUB_TUBE_R - 0.5, zb)]
    r = prism_y("rib", pts, -DRUM_RIB / 2, DRUM_RIB / 2)
    hw, w = DRUM_RIB / 2, DRUM_RIB / 2 + RIB_FILLET
    x0 = math.sqrt(HUB_TUBE_R ** 2 - w ** 2) - 0.5
    plan = [(x0, -w), (HUB_TUBE_R + RIB_FILLET, -hw), (HUB_TUBE_R + RIB_FILLET, hw), (x0, w)]   # (radial, tangential)
    fillet = prism_y("rib fillet", plan, zb, zt - 0.2)
    fillet.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
    L.union(r, fillet)
    r.data.transform(Matrix.Rotation(math.radians(phi), 4, 'Z'))
    return r


def drum_bracket(name, r0, r_post, half, deg):
    """Under a post on the open drum's top: a web out to the wall with a 45-degree underside, up into the post and 0.3 inside it."""
    r1, a, top = DRUM_R - DRUM_WALL / 2, r0 + 0.3, DRUM_TOP + 0.5
    pts = [(a, top), (r_post - 0.3, top), (r_post - 0.3, DRUM_TOP - 0.3), (r1, DRUM_TOP - 0.3), (r1, top - (r1 - a))]
    b = prism_y(name, pts, -half + 0.3, half - 0.3)
    b.data.transform(Matrix.Rotation(math.radians(deg), 4, 'Z'))
    return b


def fixed_base():
    """The drum on the bench: a thin shell open top and bottom, flat at 270 for the base motor; the hub tube with the two
    6810 seats down to the bench; ribs out to the legs' sockets; brackets under the stop block and the Hall post; the
    shelf the motor hangs under, on side walls with 45-degree undersides."""
    zt, zb = DRUM_TOP, BENCH_Z - 1.0                               # zb: trimmed back to the bench at the end, one flat underside
    f = L.cyl_z("fixed-base", 0, 0, DRUM_R, zb, zt, n=192)
    L.cut(f, L.cyl_z("hollow", 0, 0, DRUM_R - DRUM_WALL, zb - 1.0, zt + 1.0, n=192))
    beyond = L.box("beyond the flat", FLAT_R, 200.0, -200.0, 200.0, zb - 1.0, zt + 1.0); beyond.data.transform(base_frame())
    L.cut(f, beyond)
    half = math.sqrt(DRUM_R ** 2 - (FLAT_R - DRUM_WALL) ** 2)
    flat = L.box("flat", FLAT_R - DRUM_WALL, FLAT_R, -half, half, zb, zt); flat.data.transform(base_frame())
    L.union(f, flat)
    past = L.cyl_z("past the drum", 0, 0, 200.0, zb - 1.0, zt + 1.0, n=64)
    L.cut(past, L.cyl_z("drum", 0, 0, DRUM_R, zb - 2.0, zt + 2.0, n=192))
    L.cut(f, past)                                                 # the flat's ends stop at the drum's outside
    L.union(f, L.cyl_z("hub", 0, 0, HUB_TUBE_R, zb, zt, n=192))
    for phi in LEG_PHI:
        L.union(f, drum_rib(phi))
    L.union(f, drum_bracket("block bracket", PHI_R[0], PHI_R[1], PHI_R[0] * math.sin(math.radians(PHI_HALF)), 0.0))
    hr = BASE_HALL["magnet"][0]
    L.union(f, drum_bracket("hall bracket", hr - HALL_POST_HALF, hr + HALL_POST_HALF, HALL_POST_HALF, BASE_HALL["magnet"][1]))
    L.union(f, phi_block())
    hx, hy = hall_xy()
    L.union(f, L.box("hall post", hx - HALL_POST_HALF, hx + HALL_POST_HALF, hy - HALL_POST_HALF, hy + HALL_POST_HALF, zt - 0.01, BASE_HALL["sensor_top"]))
    r0, r1 = SHELF["r"]
    t_in = SHELF["half"] - SHELF["wall"]
    z_end = SHELF_Z[0] - SHELF_UNDER
    foot = max(r0 + 6.0, r1 - (z_end - zb))                        # the 45-degree underside meets the bench this far out
    side = [(r0, SHELF_Z[1]), (r0, zb), (foot, zb), (r1, z_end), (r1, SHELF_Z[1])]
    arm = L.box("shelf", r0, r1, -SHELF["half"], SHELF["half"], *SHELF_Z)
    for sg in (1, -1):
        L.union(arm, prism_y("wall", side, *sorted((sg * t_in, sg * SHELF["half"]))))
    L.finish(arm)
    m, c = MOTORS["17"], BASE_BELT_C
    L.cut(arm, slot_u("pilot window", c, 0.0, m["pilot_r"] + 0.5, SHELF_Z[0] - 1.0, SHELF_Z[1] + 1.0, n=24))
    for dr, dt in BASE_MOTOR_SCREWS:
        L.cut(arm, slot_u("motor screw slot", c + dr, dt, M3_CLEAR_R, SHELF_Z[0] - 1.0, SHELF_Z[1] + 1.0))
    arm.data.transform(base_frame())
    L.union(f, arm)
    L.finish(f)
    L.cut(f, L.cyl_z("lip", 0, 0, TT_LIP_R, zb - 1.0, zt + 1.0, n=192))
    L.cut(f, L.cyl_z("upper seat", 0, 0, B6810[1] + 0.05, BASE_6810_Z[0], zt + 1.0, n=192))
    L.cut(f, L.cyl_z("lower seat", 0, 0, B6810[1] + 0.05, zb - 1.0, BASE_6810_Z[1] + B6810[2], n=192))
    st = BASE_HALL["sensor_top"]
    L.cut(f, L.box("sensor pocket", hx - SENSOR[1] / 2 - 0.1, hx + SENSOR[1] / 2 + 0.1, hy - SENSOR[0] / 2 - 0.1, hy + SENSOR[0] / 2 + 0.1,
                   st - SENSOR[2] - 0.1, st + 1.0))
    L.cut(f, L.box("leads", hx - HALL_POST_HALF - 1.0, hx, hy - 1.0, hy + 1.0, st - 1.0, st + 1.0))
    leg_sockets(f)
    L.cut(f, L.box("under the bench", -200.0, 200.0, -200.0, 200.0, BENCH_Z - 5.0, BENCH_Z))
    PRINT_POSE["fixed-base"] = Matrix.Translation((0, 0, -BENCH_Z))
    return f


def base_motor_plate():
    """On the shelf: the motor's four M3s go down through it and the shelf's slots into the motor hanging underneath."""
    m, c = MOTORS["17"], BASE_BELT_C
    z0, z1 = BASE_PLATE_Z
    p = L.box("base-motor-plate", c - BASE_PLATE_HALF_R, c + BASE_PLATE_HALF_R, -BASE_PLATE_HALF_T, BASE_PLATE_HALF_T, z0, z1)
    for dr, dt in BASE_MOTOR_SCREWS:
        L.cut(p, L.cyl_z("motor screw", c + dr, dt, m["hole_r"], z0 - 1.0, z1 + 1.0, n=30))
    L.cut(p, L.cyl_z("shaft", c, 0, 4.0, z0 - 1.0, z1 + 1.0, n=48))
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
    names = ("turntable", "base-ring-130T", "base-spacer", "base-retainer", "fixed-base", "base-motor-plate")
    tt, ring, spacer, ret, fb, bp = (PARTS[n] for n in names)
    for n in names:
        part_ok(n); on_bed(n)
    # The two 6810s: the cylinder's land through both inner rings, the drum's seats, the lip between them on the outer rings.
    for z0 in BASE_6810_Z:
        zm = z0 + B6810[2] / 2
        land = radial_z(ring, zm, r0=30.0)
        assert CYL["r"] - 0.01 <= land <= CYL["r"] + 0.1, ("cylinder's land", zm, land)   # -0.01: the polygon's chords
        seat = radial_z(fb, zm, inward=False)
        assert B6810[1] <= seat <= B6810[1] + 0.1, ("drum seat", zm, seat)
    lip = radial_z(fb, sum(SPACER_Z) / 2, inward=False)
    assert 27.5 + 0.5 <= lip <= B6810[1] - 1.5 + 0.01, ("the drum's lip should bear on the outer rings only", lip)
    for o, z, n in ((ring, DRUM_TOP + 0.5, "the cylinder's shoulder"), (spacer, sum(SPACER_Z) / 2, "spacer"), (ret, BASE_6810_Z[1] - 0.5, "retainer")):
        r = radial_z(o, z, r0=30.0)
        assert r <= 27.5 - 0.45, ("bears past the inner ring", n, r)
    shoulder = min(v.co.z for v in ring.data.vertices if math.hypot(v.co.x, v.co.y) > CYL["r"] + 0.05 and v.co.z < RING_Z0 + 0.5)
    assert abs(shoulder - DRUM_TOP) < 0.01, ("the cylinder's shoulder isn't on the upper inner ring", shoulder)
    sp = [v.co.z for v in spacer.data.vertices]
    assert abs(min(sp) - SPACER_Z[0]) < 0.01 and abs(max(sp) - SPACER_Z[1]) < 0.01, "spacer between the inner rings"
    assert abs(max(v.co.z for v in ret.data.vertices) - BASE_6810_Z[1]) < 0.01, "retainer not on the lower inner ring"
    end = ray_len(ring, (23.5, 0, BASE_6810_Z[1]), (0, 0, 1))
    assert end is not None and abs(end - 0.3) < 0.01, ("the cylinder's end should stand 0.3 inside the lower inner ring", end)
    for a, b, n in ((tt, fb, "turntable"), (ring, fb, "ring"), (spacer, fb, "spacer"), (ret, fb, "retainer"), (spacer, ring, "spacer on the cylinder"),
                    (ret, ring, "retainer on the cylinder"), (ring, tt, "ring in the turntable")):
        assert overlap(a, b) < 0.05, (n, "overlaps")
    assert touching(ring, tt), "ring not on the turntable's underside"
    turning = join([tt, ring, spacer, ret], "turning")
    tf = tree(fb)
    fv = [v.co.copy() for v in fb.data.vertices]
    running = sweep_gap(turning, tf, fv, bounds(fv, 10.0))
    assert running >= 0.5, ("the turntable, ring or cylinder within 0.5 of the drum", running)
    g = grooves_at(ring, sum(RING_Z) / 2, od_r(RING_TEETH))
    assert g == RING_TEETH, ("ring grooves", g)
    peak = 2 * max(od_r(RING_TEETH) + 20.0 - ray_len(ring, (math.cos(a) * (od_r(RING_TEETH) + 20.0), math.sin(a) * (od_r(RING_TEETH) + 20.0), sum(RING_Z) / 2),
                                                       (-math.cos(a), -math.sin(a), 0)) for a in [2 * math.pi * k / 2880 for k in range(2880)])
    assert abs(peak - 2 * od_r(RING_TEETH)) <= 0.05, ("ring OD", peak)
    belts = {}
    for s in (-MOTOR_SLOT, 0.0, MOTOR_SLOT):
        belts[s] = round(math.hypot(*base_motor_at(s)), 2)
        assert abs(belts[s] - BASE_BELT_C - s) <= 0.1, ("base belt centres", s, belts[s])
    above = concat(fixed_shoulder(), "on the turntable")
    m = MOTORS["17"]
    flat_gap, belt_gap = {}, math.inf
    for s in (-MOTOR_SLOT, MOTOR_SLOT):
        box, belt, plate = base_motor_box(s), base_belt_envelope(s), moved_base(bp, s)
        assert overlap(box, fb) < 0.05 and touching(box, fb), ("base motor not hanging under the shelf", s)
        flat_gap[f"{s:+.0f}"] = round(BASE_BELT_C + s - BASE_MOTOR_REACH - FLAT_R, 2)
        assert flat_gap[f"{s:+.0f}"] >= 1.0 - 1e-6, ("base motor within 1 of the drum's flat", s)
        assert overlap(plate, fb) < 0.05 and touching(plate, fb), ("clamp plate not on the shelf", s)
        assert overlap(belt, fb) < 0.05 and overlap(belt, plate) < 0.05, ("base belt hits the drum or the plate", s)
        for phi in range(int(PHI_RANGE[0]), int(PHI_RANGE[1]) + 1, 5):
            t = copy(turning, "t"); t.data.transform(rot_base(phi))
            top = copy(tt, "tt"); top.data.transform(rot_base(phi))   # the belt runs on the ring: only the turntable and its tab
            a = copy(above, "a"); a.data.transform(rot_base(phi))
            for o, n, other in ((box, "base motor", t), (belt, "base belt", top), (plate, "clamp plate", t)):
                assert not tree(o).overlap(tree(other)), (n + " hits the turntable or ring", s, phi)
                assert not tree(o).overlap(tree(a)), (n + " hits the shoulder on the turntable", s, phi)
            if phi % 10 == 0:
                belt_gap = min(belt_gap, min_gap(top, belt), min_gap(belt, top), min_gap(a, belt), min_gap(a, box))
            for o in (t, top, a):
                bpy.data.objects.remove(o)
        for dr, dt in BASE_MOTOR_SCREWS:
            seat = at_base(BASE_BELT_C + s + dr, dt, BASE_PLATE_Z[1])
            screw_access(("base motor screw", s, round(dr), round(dt)), seat, (0, 0, 1), 2.75, BOLT_HEAD_H, [fb, plate, belt, turning, above])
        for o in (box, belt, plate):
            bpy.data.objects.remove(o)
    assert belt_gap >= 1.0, ("something turning within 1 of the base motor or its belt", round(belt_gap, 2))
    assert 3.0 <= BASE_MOTOR_SCREW_L - BASE_PLATE_T - SHELF_T <= 4.5, "base motor screws into the motor"
    for a in RING_SCREW_ANGLES:
        x, y = polar(RING_SCREW_R, a)
        screw_access(("ring screw", a), (x, y, RING_CB_Z), (0, 0, -1), 2.75, BOLT_HEAD_H, [ring, tt])
    assert 3.0 <= RING_SCREW_L - (TT_HUB_Z0 - RING_CB_Z) <= M3_INSERT_DEPTH - 0.5, "ring screws into the turntable"
    walls = []
    for a in RETAINER["angles"]:
        x, y = polar(RETAINER["screw_r"], a)
        screw_access(("retainer screw", a), (x, y, BASE_6810_Z[1] - RETAINER["t"]), (0, 0, -1), 2.75, BOLT_HEAD_H, [ring, ret, spacer, fb])
        d = ray_len(ring, (x + 1.85, y, CYL["end_z"] - 1.0), (0, 0, 1))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("retainer insert in the cylinder", a, d)
        walls.append(material_round(ring, (x, y, CYL["end_z"] + M3_INSERT_DEPTH / 2), (0, 0, 1), M3_INSERT_R))
    assert min(walls) >= WALL_MIN, ("material round the retainer's inserts", walls)
    assert 3.0 <= RETAINER["screw_l"] - RETAINER["t"] - 0.3 <= M3_INSERT_DEPTH - 0.5, "retainer screws"
    under = [v.co.z for v in fb.data.vertices if v.co.z <= BENCH_Z + 0.01]
    assert under and max(under) - min(under) <= 0.02 and abs(min(under) - BENCH_Z) <= 0.02, ("drum's underside not flat on the bench", min(under), max(under))
    bpy.data.objects.remove(above)
    cm3 = volume(fb) / 1000.0
    assert cm3 <= FIXED_BASE_MAX_CM3, ("fixed base too heavy", round(cm3, 1))
    for phi in LEG_PHI:
        u = Vector((math.cos(math.radians(phi)), math.sin(math.radians(phi)), 0)); t = Vector((-u.y, u.x, 0))
        heights = [BENCH_Z + k + 0.5 for k in range(int(DRUM_H))]
        joined = sum(1 for z in heights if (lambda h: h[0] is not None and h[1].dot(t) > 0)(
            tree(fb).ray_cast(u * (HUB_TUBE_R + 1.0) + Vector((0, 0, z)), t)))
        assert joined >= 0.9 * len(heights), ("rib not joined to the hub tube down its height", phi, joined, len(heights))
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
    for x, y in BRACKET_BOLTS + POST_BOLTS:
        d = ray_len(tt, (x + 1.85, y, TURNTABLE_Z + 1.0), (0, 0, -1))
        assert d is not None and abs(d - 1.0 - M3_INSERT_DEPTH) < 0.06, ("bracket or post insert in the turntable", x, y, d)
        assert material_round(tt, (x, y, TURNTABLE_Z - M3_INSERT_DEPTH / 2), (0, 0, 1), M3_INSERT_R) >= INSERT_WALL_MIN, ("turntable insert wall", x, y)
    for n, (x0, x1, y0, y1) in (("bracket", (-BRACKET["root_x"]["rear"], BRACKET["root_x"]["front"], BRACKET["flange_y"][0], LUG["spider_y"][1])),
                                ("post", (-POST["foot_x"], POST["foot_x"], POST["y"][1], POST["y"][0]))):
        for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
            inside_tt = math.hypot(x, y) <= TURNTABLE_R - 2.0 or (EAR["x"][0] + 2.0 <= x <= EAR["x"][1] - 2.0 and EAR["y"][0] <= y <= EAR["y"][1] - 2.0)
            assert inside_tt, (n + "'s foot within 2 of the turntable's edge", x, y)
    REPORT.update({"base_belt_centres": belts, "base_motor_flat_gap_mm": flat_gap, "base_motor_belt_min_gap_mm": round(belt_gap, 2),
                   "base_running_gap_mm": round(running, 2), "drum": DRUM, "bench_z": BENCH_Z, "bench_to_shoulder_axis_mm": round(-BENCH_Z, 1),
                   "base_6810_spacing": BASE_6810_SPACING, "phi_stop_gaps_mm": gaps, "phi_stop_mpa": {k: round(v, 1) for k, v in mpa.items()},
                   "base_hall_gap_mm": round(hall, 2), "turntable_r": TURNTABLE_R, "ring_grooves": g, "ring_od": round(peak, 2),
                   "base_motor_at": [round(c, 2) for c in BASE_MOTOR_AT], "turntable_z": TURNTABLE_Z, "base_screws_reached_at_phi": 0,
                   "fixed_base_lowest_z": round(min(v.co.z for v in fb.data.vertices), 2), "fixed_base_cm3": round(cm3, 1)})
    REPORT["bolts"].update({"ring to turntable (from under the ring)": RING_SCREW_L, "base motor through the plate and shelf": BASE_MOTOR_SCREW_L,
                            "retainer into the cylinder": RETAINER["screw_l"]})
    for o in (turning, tab, block):
        bpy.data.objects.remove(o)


def bearing_6810(z0):
    """A 6810 with its lower face at z0, 0.05 inside its seat and land and 0.02 inside its faces, so it slides on them."""
    b = L.cyl_z("6810", 0, 0, B6810[1] - 0.05, z0 + 0.02, z0 + B6810[2] - 0.02, n=192)
    L.cut(b, L.cyl_z("bore", 0, 0, B6810[0] + 0.05, z0 - 1.0, z0 + B6810[2] + 1.0, n=192))
    return b


def slides_home(o, d, travel, placed, step=1.0):
    """Where o, sliding along d to its seat from travel back, first meets placed (its distance short of home), or None."""
    tp, s = tree(placed), travel
    while True:
        s = max(s, 0.05)
        c = copy(o, "sliding"); c.data.transform(Matrix.Translation(-Vector(d) * s))
        hit = tree(c).overlap(tp)
        bpy.data.objects.remove(c)
        if hit:
            return round(s, 2)
        if s == 0.05:
            return None
        s -= step


def check_base_order():
    """The sheet's order (BASE_ORDER): each part slides home along z past what's already in; any that comes up from under
    the bench comes before the legs go on, and the feet are clamped after the legs."""
    up, down = Vector((0, 0, 1)), Vector((0, 0, -1))
    turning = concat([copy(PARTS[n], n) for n in ("turntable", "base-ring-130T")], "turntable, ring and cylinder")
    parts = {"upper 6810": (bearing_6810(BASE_6810_Z[0]), down), "turntable, ring and cylinder": (turning, down),
             "base-spacer": (copy(PARTS["base-spacer"], "spacer"), up), "lower 6810": (bearing_6810(BASE_6810_Z[1]), up),
             "base-retainer": (copy(PARTS["base-retainer"], "retainer"), up), "base motor": (base_motor_box(0.0), up)}
    placed, under_bench = [PARTS["fixed-base"]], []
    for i, step in enumerate(BASE_ORDER):
        if step not in parts:
            continue
        o, d = parts[step]
        zs = [v.co.z for v in o.data.vertices]
        travel = MOTORS["17"]["shaft"] + 2.0 if step == "base motor" else (DRUM_TOP + 1.0 - min(zs) if d == down else max(zs) - (BENCH_Z - 1.0))
        if d == up and min(zs) - travel < BENCH_Z:
            under_bench.append(i)
        pl = concat([copy(p, "p") for p in placed], "placed")
        hit = slides_home(o, d, travel, pl)
        bpy.data.objects.remove(pl)
        assert hit is None, (step, "meets a part already in, this far short of home", hit, [p.name for p in placed])
        placed.append(o)
    legs, clamp = BASE_ORDER.index("legs on"), BASE_ORDER.index("clamp the feet")
    assert all(i < legs for i in under_bench), ("comes up from under the bench after the legs are on", [BASE_ORDER[i] for i in under_bench if i > legs])
    assert legs < clamp, "the feet are clamped before the legs are on"
    REPORT["base_order"] = BASE_ORDER
    for o in placed[1:]:
        bpy.data.objects.remove(o)


def V(t):
    return Vector(t)


def pinch_dir(d):
    """Square to the leg, pointing up: the pinch screw goes in from above."""
    up = Vector((0, 0, 1)); d = Vector(d)
    return (up - d * up.dot(d)).normalized()


def leg_sockets(f):
    """Bosses on the drum's rim, their undersides a 45-degree teardrop down onto the leg's rib, then the sockets and the pinch inserts."""
    h = SOCKET["boss_r"] * TEARDROP
    for phi in LEG_PHI:
        m, s, _ = (V(p) for p in leg(phi)); d = V(leg_dir(phi)); n = pinch_dir(d)
        a = s - d * SOCKET["floor"]
        boss = rod("socket boss", a, m, SOCKET["boss_r"], n=47)   # odd: no vertex row on the pinch insert's axis
        L.union(f, hull([boss, rod("teardrop", a - n * h, m - n * h, 0.5, n=8)], "socket"))
    L.finish(f)
    for phi in LEG_PHI:
        m, s, _ = (V(p) for p in leg(phi)); d = V(leg_dir(phi)); n = pinch_dir(d)
        L.cut(f, rod("socket", s, m + d * 30.0, SOCKET["r"], n=64))   # on out past the mouth
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
        away = (phi + 270.0) % 360.0 - 180.0     # the turntable turned so its ear (+y at phi 0) is opposite this leg: it spans more than 90 degrees
        t = copy(tt, "t"); t.data.transform(rot_base(away))
        screw_access(("leg pinch screw", phi, "turntable at", away), seat, n, 2.75, BOLT_HEAD_H, [fb, t])
        bpy.data.objects.remove(t)
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
PARTS["shoulder-hub"], PARTS["shoulder-output-plate"] = shoulder_hub(), output_plate()
PARTS["shoulder-lug"], PARTS["shoulder-socket-bracket"], PARTS["shoulder-rod-post"] = lug(), socket_bracket(), rod_post()
PARTS["turntable"], PARTS["base-ring-130T"] = turntable(), base_ring()
PARTS["base-spacer"], PARTS["base-retainer"] = base_spacer(), base_retainer()
PARTS["fixed-base"], PARTS["base-motor-plate"] = fixed_base(), base_motor_plate()
PARTS["foot"], PARTS["foot-pad"] = foot_part(), foot_pad()
CHECKS += [check_shoulder_core, check_bracket_assembly, check_axis_and_stops, check_base, check_base_order, check_legs]
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
