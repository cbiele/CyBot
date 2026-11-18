"""Elbow (axis 3) and upper arm parts: forearm collar, aluminium tube truss, elbow hub.
Built and checked in the elbow frame (elbow_dims.py), exported in print orientation to model/elbow/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/elbow.py"""
import bpy, bmesh, math, os, sys, json, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
import forearm_dims as F
from elbow_dims import *
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
MODEL = os.path.join(ROOT, "model")
OUT = os.path.join(MODEL, "elbow")
COMPACT = os.path.join(MODEL, "cycloid-poc", "20-1-compact")
FOREARM = os.path.join(MODEL, "forearm-tube")
PARTS, CHECKS, PRINT_POSE, REPORT = {}, [], {}, {}
AX4_BELT_C = round(C.belt_centre_distance(20, F.AX4_TEETH, F.AX4_BELT), 2)
SQUARE, PANCAKE_L = 42.3, 23.0
LUG_Y = (TUBE_PLANE_Y - SOCKET_R - SOCKET_WALL, TUBE_PLANE_Y + SOCKET_R + SOCKET_WALL)


def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))


def basis(u, v, w, origin):
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2], m[i][3] = u[i], v[i], w[i], origin[i]
    return m


def forearm_matrix():
    """A forearm-frame point into the elbow frame."""
    return Matrix.Translation((-ELBOW_FX, 0, OFFSET))


def ax4_matrix():
    """Axis 4's cycloid frame (z along the roll axis from the housing's rear face, x up to its motor) into the elbow frame."""
    return forearm_matrix() @ basis((0, 0, 1), (0, -1, 0), (1, 0, 0), (0, 0, 0))


def compact_matrix():
    """The elbow compact's cycloid frame: rear face on plate A's inner face, output towards plate B (-y)."""
    return basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, Y_REAR, 0))


def rot_elbow(theta):
    return Matrix.Rotation(math.radians(90.0 - theta), 4, 'Y')


def cyl_y(name, x, z, r, y0, y1, n=96):
    c = L.cyl_z(name, 0, 0, r, y0, y1, n=n)
    c.data.transform(basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, 0)))
    c.data.transform(Matrix.Translation((x, 0, z)))
    return c


def cyl_x(name, y, z, r, x0, x1, n=96):
    c = L.cyl_z(name, 0, 0, r, x0, x1, n=n)
    c.data.transform(basis((0, 0, -1), (0, 1, 0), (1, 0, 0), (0, 0, 0)))
    c.data.transform(Matrix.Translation((0, y, z)))
    return c


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


def hull(objs, name):
    """Convex hull of the objects' vertices; the objects are removed."""
    bm = bmesh.new()
    for o in objs:
        for v in o.data.vertices:
            bm.verts.new(v.co)
        bpy.data.objects.remove(o)
    res = bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)}), context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)


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
    """Bounding box of each connected piece: one entry means one island."""
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


def posed_stl(path, name, matrix):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name
    o.data.transform(matrix)
    return o


def flip():
    return Matrix.Diagonal((1, -1, -1, 1))


def posed_context():
    """The built parts the bracket meets, in the elbow frame."""
    a4, el = ax4_matrix(), compact_matrix()
    ctx = {
        "ax4 housing": join([posed_stl(os.path.join(COMPACT, "housing-rear.stl"), "a4hr", a4),
                             posed_stl(os.path.join(COMPACT, "housing-front.stl"), "a4hf", a4 @ flip())], "ax4 housing"),
        "outer tube": posed_stl(os.path.join(FOREARM, "forearm-outer-tube.stl"), "outer tube", a4 @ Matrix.Translation((0, 0, F.OUTER_X[0]))),
        "ax4 60T mount": posed_stl(os.path.join(FOREARM, "ax4-motor-mount-60T.stl"), "ax4 60T mount", a4),   # stored in its assembly frame
        "ax4 pancake": L.box("ax4 pancake", AX4_BELT_C - SQUARE / 2, AX4_BELT_C + SQUARE / 2, -SQUARE / 2, SQUARE / 2, 0, PANCAKE_L),
        "elbow compact": join([posed_stl(os.path.join(COMPACT, "housing-rear.stl"), "elhr", el),
                               posed_stl(os.path.join(COMPACT, "housing-front.stl"), "elhf", el @ flip())], "elbow compact"),
        "elbow output plate": posed_stl(os.path.join(FOREARM, "ax4-output-plate.stl"), "elbow output plate", el @ Matrix.Translation((0, 0, F.PLATE_X[0]))),
        "6810 B": cyl_y("6810 B", 0, 0, B6810[1], *sorted(HUB_6810_Y)),
    }
    ctx["ax4 pancake"].data.transform(a4)
    L.cut(ctx["6810 B"], cyl_y("bore", 0, 0, B6810[0], HUB_6810_Y[1] - 1, HUB_6810_Y[0] + 1))
    heads = [cyl_x("head", y, OFFSET + z, BOLT_HEAD_R, COLLAR_X[0] - ELBOW_FX, COLLAR_X[0] - ELBOW_FX + BOLT_HEAD_H, n=24)
             for a in F.BOLT_ANGLES for y, z in [polar(F.BOLT_R, a)]]
    ctx["bolt heads"] = join(heads, "bolt heads")
    nuts = [cyl_y("nut", x, z, NUT_AF / 2 / math.cos(math.radians(30)) + 0.05, Y_REAR - HOUSING_L - 2.4, Y_REAR - HOUSING_L, n=6)
            for a in F.BOLT_ANGLES for x, z in [polar(F.BOLT_R, a)]]
    ctx["elbow nuts"] = join(nuts, "elbow nuts")
    for o in heads + nuts:
        bpy.data.objects.remove(o)
    return ctx


def tube_axis(name):
    (ax, az), (bx, bz) = TUBE_ENDS[name]
    return Vector((ax, TUBE_PLANE_Y, az)), Vector((bx, TUBE_PLANE_Y, bz))


def tube_lengths():
    return {n: round((b - a).length + 2 * SOCKET_DEPTH, 1) for n in TUBE_ENDS for a, b in [tube_axis(n)]}


def tubes():
    out = []
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        d = (b - a).normalized()
        out.append(rod(f"tube {name}", a - d * SOCKET_DEPTH, b + d * SOCKET_DEPTH, TUBE_OR, n=32))
    return out


def socket_boss(mouth, d, name):
    """Boss round a socket running SOCKET_DEPTH from mouth along d, with SOCKET_WALL beyond its floor."""
    return rod(name, mouth, mouth + d * (SOCKET_DEPTH + SOCKET_WALL), SOCKET_R + SOCKET_WALL)


def socket_cut(mouth, d, name):
    return rod(name, mouth - d * 3.0, mouth + d * SOCKET_DEPTH, SOCKET_R)


def span_keepouts(part):
    """Clear each tube's open span, mouth to mouth, so the lugs neither block a tube nor close a socket."""
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        L.cut(part, rod("span", a, b, TUBE_OR + TUBE_CLEAR))


def collar():
    """Split clamp on the outer tube's Ø36 section, keyed over the R30 bolt heads; the lower half's lug carries the tubes' collar ends."""
    x0, x1 = COLLAR_X[0] - ELBOW_FX, COLLAR_X[1] - ELBOW_FX
    body = cyl_x("collar", 0, OFFSET, COLLAR_R, x0, x1)
    L.union(body, cyl_x("key disc", 0, OFFSET, HOUSING_R, x0, x0 + KEY_DISC_T))
    bosses = []
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        bosses.append(socket_boss(a, -(b - a).normalized(), "boss"))
    bosses.append(L.box("lug root", x0, x1, *LUG_Y, OFFSET - 20.0, OFFSET - 6.0))
    L.union(body, hull(bosses, "lug"))
    L.finish(body)
    L.cut(body, cyl_x("behind the flange", 0, OFFSET, HOUSING_R + 0.5, -80.0, x0, n=192))
    span_keepouts(body)
    L.cut(body, cyl_x("clamp bore", 0, OFFSET, F.OUTER_REAR_R + 0.05, x0 - 1, x1 + 0.01, n=192))
    L.cut(body, cyl_x("free bore", 0, OFFSET, COLLAR_FREE_R, x1, 120.0, n=192))
    for a in F.BOLT_ANGLES:
        y, z = polar(F.BOLT_R, a)
        L.cut(body, cyl_x("key", y, OFFSET + z, KEY_R, x0 - 1, x0 + KEY_DEPTH, n=32))
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        L.cut(body, socket_cut(a, -(b - a).normalized(), "socket"))
    cx, cy = CLAMP_SCREW
    for s in (1, -1):
        L.cut(body, L.cyl_z("clamp hole", cx, s * cy, 1.7, OFFSET - 14.5, OFFSET + 30, n=32))
        L.cut(body, L.cyl_z("clamp cb", cx, s * cy, 3.0, CLAMP_CB_Z, OFFSET + 30, n=32))
        y_in = s * (cy - NUT_AF / 2 / math.cos(math.radians(30)))
        L.cut(body, L.box("nut slot", cx - NUT_AF / 2, cx + NUT_AF / 2, min(y_in, s * 40), max(y_in, s * 40),
                          CLAMP_NUT_Z - NUT_T / 2, CLAMP_NUT_Z + NUT_T / 2))
    upper, lower = copy(body, "elbow-collar-upper"), body
    lower.name = "elbow-collar-lower"
    L.cut(upper, L.box("below split", -80, 140, -60, 60, -100, OFFSET + SPLIT_GAP / 2))
    L.cut(lower, L.box("above split", -80, 140, -60, 60, OFFSET - SPLIT_GAP / 2, 200))
    PRINT_POSE["elbow-collar-upper"] = Matrix.Translation((0, 0, -(OFFSET + SPLIT_GAP / 2)))
    PRINT_POSE["elbow-collar-lower"] = Matrix.Translation((0, 0, OFFSET - SPLIT_GAP / 2)) @ Matrix.Diagonal((1, -1, -1, 1))
    return lower, upper


def hub():
    """On the elbow compact's output plate, turning in plate B's 6810; its lug carries the tubes' hub ends."""
    h = cyl_y("elbow-hub", 0, 0, HUB_R, HUB_DISC_Y[1], HUB_DISC_Y[0], n=192)
    L.union(h, cyl_y("journal", 0, 0, B6810[0], HUB_END_Y, HUB_DISC_Y[1] + 0.01, n=96))
    bosses = [cyl_y("lug root", 0, 0, HUB_R, *LUG_Y, n=96)]
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        bosses.append(socket_boss(b, (b - a).normalized(), "boss"))
    L.union(h, hull(bosses, "lug"))
    L.finish(h)
    span_keepouts(h)
    L.cut(h, cyl_y("wire bore", 0, 0, HUB_BORE_R, HUB_END_Y - 1, Y_OUT - HUB_FLOOR, n=96))
    L.cut(h, L.box("wire window", -8.0, 8.0, HUB_END_Y + 0.8, HUB_6810_Y[1] - LIP_T - 0.5, 10.0, 30.0))
    for x, z in [polar(F.DOG_PCD_R, a) for a in F.DOG_ANGLES]:
        L.cut(h, cyl_y("dog", x, z, F.DOG_R + 0.15, Y_OUT - F.DOG_H - 0.5, Y_OUT + 1, n=32))
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        L.cut(h, cyl_y("screw", x, z, 1.7, Y_OUT - HUB_FLOOR - 1, Y_OUT + 1, n=32))
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        L.cut(h, socket_cut(b, (b - a).normalized(), "socket"))
    PRINT_POSE["elbow-hub"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -HUB_END_Y))
    return h


def check_bracket():
    ctx = CTX
    col_lo, col_hi, hub = PARTS["elbow-collar-lower"], PARTS["elbow-collar-upper"], PARTS["elbow-hub"]
    for n in ("elbow-collar-lower", "elbow-collar-upper", "elbow-hub"):
        assert islands(PARTS[n]) == 1, (n, "islands", island_bounds(PARTS[n]))
        assert L.stats(PARTS[n])["non_manifold"] == 0, (n, "non-manifold")
    fx = lambda x: x - ELBOW_FX
    mid = fx(sum(COLLAR_X) / 2)
    ds = [ray_len(o, (mid, 0, OFFSET), (0, math.cos(a), math.sin(a)))
          for k in range(24) for a in [2 * math.pi * k / 24] for o in [col_hi if math.sin(a) > 0.05 else col_lo if math.sin(a) < -0.05 else None] if o]
    clamp_d = 2 * sum(ds) / len(ds)
    assert 2 * F.OUTER_REAR_R <= clamp_d <= 2 * F.OUTER_REAR_R + 0.2, ("clamp bore", clamp_d)
    for o in (col_lo, col_hi):
        assert overlap(o, ctx["outer tube"]) < 0.01, "collar cuts into the outer tube"
        assert overlap(o, ctx["bolt heads"]) < 0.01, "collar hits the R30 bolt heads"
        stack = [v.co for v in o.data.vertices if v.co.x < fx(COLLAR_X[0]) - 0.01 and math.hypot(v.co.y, v.co.z - OFFSET) < HOUSING_R + 0.45]
        assert not stack, "collar reaches into axis 4's bolt stack"
        near = [v.co for v in o.data.vertices if v.co.x > fx(F.REAR_BRG_X[0] - 1.0) + 0.01 and math.hypot(v.co.y, v.co.z - OFFSET) < COLLAR_FREE_R - 0.05]
        assert not near, "collar bears over the rear 6701's seat"
    assert touching(col_lo, ctx["outer tube"]) and touching(col_hi, ctx["outer tube"]), "collar halves don't seat on the flange"
    for a in F.BOLT_ANGLES:
        y, z = polar(F.BOLT_R, a)
        o = col_hi if z > 0 else col_lo
        floor = ray_len(o, (fx(COLLAR_X[0]) - 1.0, y, OFFSET + z), (1, 0, 0))
        assert floor is not None and floor - 1.0 >= BOLT_HEAD_H + 0.2, ("key pocket depth", a, floor)
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        d = (b - a).normalized()
        for part, mouth, into in ((col_lo, a, -d), (hub, b, d)):
            inside = ray_len(part, mouth + into * 1.0, into)
            assert inside is not None and abs(inside + 1.0 - SOCKET_DEPTH) < 0.06, (name, part.name, "socket depth", inside)
            assert ray_len(part, mouth - into * 2.0, into) is None or ray_len(part, mouth - into * 2.0, into) > 2.0 + SOCKET_DEPTH - 0.06, (name, part.name, "socket mouth closed")
    t_all = join(TUBES, "tubes")
    for o in (col_lo, hub):
        assert overlap(o, t_all) < 1.0, ("a tube runs into a part outside its socket", o.name, overlap(o, t_all))
    for name in TUBE_ENDS:
        a, b = tube_axis(name)
        d = (b - a).normalized()
        side = d.cross(Vector((0, 1, 0))).normalized()
        for part, mouth, into in ((col_lo, a, -d), (hub, b, d)):
            p = mouth + into * (SOCKET_DEPTH - 1.0)
            for w in (side, -side, Vector((0, 1, 0)), Vector((0, -1, 0))):
                wall = ray_len(part, p, w)
                assert wall is not None and abs(wall - SOCKET_R) < 0.1, (name, part.name, "tube end not walled in its socket", wall)
    hd = [ray_len(hub, (0, sum(HUB_6810_Y) / 2, 0), (math.cos(a), 0, math.sin(a))) for k in range(24) for a in [2 * math.pi * k / 24]]
    bore = 2 * sum(hd) / len(hd)
    assert abs(bore - 2 * HUB_BORE_R) < 0.15, ("hub wire bore", bore)
    jr = [ray_len(hub, (60 * math.cos(a), sum(HUB_6810_Y) / 2, 60 * math.sin(a)), (-math.cos(a), 0, -math.sin(a))) for k in range(24) for a in [2 * math.pi * k / 24]]
    journal = 60 - sum(jr) / len(jr)
    assert B6810[0] - 0.01 <= journal <= B6810[0] + 0.1, ("6810 journal", journal)
    for o in ("6810 B", "elbow compact", "elbow output plate", "elbow nuts", "ax4 housing", "outer tube", "ax4 60T mount", "ax4 pancake"):
        if o != "elbow output plate":
            assert overlap(hub, ctx[o]) < 0.05, ("hub hits", o)
        assert overlap(t_all, ctx[o]) < 0.05, ("tubes hit", o)
        if o != "outer tube":
            assert overlap(col_lo, ctx[o]) < 0.05, ("collar hits", o)
    assert overlap(hub, ctx["elbow output plate"]) < 1.0, "hub hits the output plate outside its dog holes"
    shoulder = [v.co for v in hub.data.vertices if HUB_6810_Y[0] - 0.01 < v.co.y < HUB_DISC_Y[1] - 0.01 and math.hypot(v.co.x, v.co.z) > B6810[0] + 0.05]
    assert not shoulder, "hub bears past the 6810's inner ring"
    assert abs(min(v.co.y for v in hub.data.vertices if math.hypot(v.co.x, v.co.z) > B6810[0] + 0.5) - HUB_DISC_Y[1]) < 0.01
    assert HUB_R <= (B6810[0] + B6810[1]) / 2, "hub shoulder reaches the 6810's outer ring"
    for x, z in [polar(F.DOG_PCD_R, a) for a in F.DOG_ANGLES]:
        assert ray_len(hub, (x, Y_OUT + 0.01, z), (0, -1, 0)) >= F.DOG_H, "dog hole too shallow"
    for x, z in [polar(F.INSERT_PCD_R, a) for a in F.INSERT_ANGLES]:
        r = ray_len(hub, (x, Y_OUT + 0.01, z), (0, -1, 0))
        assert r is None or r > HUB_FLOOR, "screw hole blocked"
    tv = [v.co for v in t_all.data.vertices]
    assert max(abs(p.y) for p in tv) <= PLATE_GAP / 2 - 1.0, "a tube is within 1 of a plate"
    for o in (hub, col_lo):
        lug = [v.co.y for v in o.data.vertices if math.hypot(v.co.x, v.co.z) > B6810[1] + 1.0]
        assert min(lug) >= -PLATE_GAP / 2 + 1.0 or o is col_lo, ("lug within 1 of plate B", o.name, min(lug))
    lengths = tube_lengths()
    assert max(lengths.values()) <= TUBE_STOCK, ("tube too long for a 125 cut", lengths)
    dog_mpa = ELBOW_TORQUE_NMM / F.DOG_PCD_R / 3 / (2 * F.DOG_R * F.DOG_H)
    assert dog_mpa <= 15.0, ("dog bearing stress", dog_mpa)
    loads = truss_loads()
    assert max(abs(f) for f in loads.values()) <= 600.0, ("tube axial load", loads)
    REPORT.update({"tube_lengths_mm": lengths, "tube_axial_n": loads, "dog_bearing_mpa": round(dog_mpa, 1),
                   "clamp_bore_mm": round(clamp_d, 2), "hub_journal_r": round(journal, 2)})


def truss_loads():
    """Axial force in each tube (tension +) with the forearm's load and the elbow torque on the collar."""
    names = list(TUBE_ENDS)
    us, ps = [], []
    for n in names:
        a, b = tube_axis(n)
        u = (b - a).normalized()
        us.append((u.x, u.z)); ps.append((a.x, a.z))
    m = [[us[i][0] for i in range(3)], [us[i][1] for i in range(3)], [ps[i][0] * us[i][1] - ps[i][1] * us[i][0] for i in range(3)]]
    f = mathutils.Matrix(m).inverted() @ Vector((0.0, FOREARM_N, ELBOW_TORQUE_NMM))
    return {n: round(f[i], 1) for i, n in enumerate(names)}


bpy.ops.wm.read_factory_settings(use_empty=True)
CTX = posed_context()
TUBES = tubes()
PARTS["elbow-collar-lower"], PARTS["elbow-collar-upper"] = collar()
PARTS["elbow-hub"] = hub()
CHECKS.append(check_bracket)
for check in CHECKS:
    check()
print("ELBOW", json.dumps({**{n: L.stats(o) for n, o in PARTS.items()}, **REPORT}))
os.makedirs(OUT, exist_ok=True)
for n, o in PARTS.items():
    o.matrix_world = Matrix()
    o.data.transform(PRINT_POSE[n])
    L.export(o, os.path.join(OUT, n + ".stl"))
print("ELBOW DONE")
