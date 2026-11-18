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
    L.union(h, stop_tab())
    L.cut(h, rod("magnet", Vector((0, sum(TAB_Y) / 2, -TAB_R[1] - 1)), Vector((0, sum(TAB_Y) / 2, -TAB_R[1] + MAGNET_D)), MAGNET_R + 0.1, n=32))
    PRINT_POSE["elbow-hub"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -HUB_END_Y))
    return h


def sector_y(name, r0, r1, a0, a1, y0, y1, n=48):
    """Annular sector about the y axis, angles in the x-z plane from +x towards +z."""
    bm = bmesh.new()
    angs = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    ring = [(r1 * math.cos(math.radians(t)), r1 * math.sin(math.radians(t))) for t in angs]
    ring += [(r0 * math.cos(math.radians(t)), r0 * math.sin(math.radians(t))) for t in angs[::-1]]
    lo = [bm.verts.new((x, y0, z)) for x, z in ring]
    hi = [bm.verts.new((x, y1, z)) for x, z in ring]
    m = len(ring)
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(m):
        bm.faces.new((lo[i], lo[(i + 1) % m], hi[(i + 1) % m], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)


def stop_tab():
    """On the hub's journal end outside plate B; its edges meet the plate's stop blocks at the ends of the range."""
    return sector_y("stop tab", B6810[0] - 0.5, TAB_R[1], TAB_PHI - TAB_HALF, TAB_PHI + TAB_HALF, TAB_Y[1], TAB_Y[0])


def tab_angle(theta):
    return TAB_PHI + theta - 90.0


def stop_blocks():
    hi = tab_angle(STOPS[1]) + TAB_HALF
    lo = tab_angle(STOPS[0]) - TAB_HALF
    y0, y1 = TAB_Y[1], -Y_REAR - PLATE_T + 0.01
    return [sector_y("stop", STOP_R[0], STOP_R[1], hi, hi + STOP_BLOCK_DEG, y0, y1),
            sector_y("stop", STOP_R[0], STOP_R[1], lo - STOP_BLOCK_DEG, lo, y0, y1)]


def sensor_block():
    """Holds the TO-92 Hall facing the magnet at home (elbow 0), where the tab points to -x."""
    r_face = TAB_R[1] + SENSOR_GAP
    b = L.box("sensor block", -(r_face + SENSOR[2] + 2.5), -r_face, TAB_Y[1], -Y_REAR - PLATE_T + 0.01, -SENSOR[0] / 2 - 2.5, SENSOR[0] / 2 + 2.5)
    return b


def sensor_pocket():
    r_face = TAB_R[1] + SENSOR_GAP
    return L.box("sensor pocket", -(r_face + SENSOR[2] + 0.1), -r_face + 0.01, TAB_Y[1] - 1, -Y_REAR - PLATE_T - 0.4, -SENSOR[0] / 2 - 0.1, SENSOR[0] / 2 + 0.1)


def prism_y(name, outline, y0, y1):
    """Prism along y from a closed (x, z) outline, counter-clockwise seen from +y."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y0, z)) for x, z in outline]
    hi = [bm.verts.new((x, y1, z)) for x, z in outline]
    m = len(outline)
    bm.faces.new(lo); bm.faces.new(hi[::-1])
    for i in range(m):
        bm.faces.new((lo[i], hi[i], hi[(i + 1) % m], lo[(i + 1) % m]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)


def stadium(name, y0, y1, n=64):
    top = [polar(PLATE_R, 180.0 * k / n) for k in range(n + 1)]
    bottom = [(x, SHOULDER_Z + z) for x, z in [polar(PLATE_R, 180.0 + 180.0 * k / n) for k in range(n + 1)]]
    return prism_y(name, top + bottom, y0, y1)


def slot_y(name, x, z, r, half, y0, y1, along="z"):
    dx, dz = (0, half) if along == "z" else (half, 0)
    return hull([cyl_y("a", x - dx, z - dz, r, y0, y1, n=32), cyl_y("b", x + dx, z + dz, r, y0, y1, n=32)], name)


def plate_common_cuts(p, y0, y1):
    for x, z in CROSS_MEMBERS:
        L.cut(p, cyl_y("cross member", x, z, CM_HOLE_R, y0 - 1, y1 + 1, n=48))
    wx, wz0, wz1 = WINDOW
    L.cut(p, L.box("window", -wx, wx, y0 - 1, y1 + 1, wz1, wz0))


def seat(p, z, y_in, y_out):
    """6810 seat from the inner face, lip on the outer face bearing on the outer ring."""
    s = 1 if y_out > y_in else -1
    L.cut(p, cyl_y("seat", 0, z, B6810[1] + 0.05, *sorted((y_in - s, y_in + s * B6810[2])), n=192))
    L.cut(p, cyl_y("lip", 0, z, LIP_IN_R, *sorted((y_in - s, y_out + s)), n=128))


def plate_a():
    y0, y1 = Y_REAR, Y_REAR + PLATE_T
    p = stadium("upper-plate-A", y0, y1)
    ix, iz = IDLER_AT
    L.union(p, slot_y("idler boss", ix, iz, IDLER_BOSS_R, IDLER_SLOT, y1 - 0.01, ROLLER_Y[0] - 0.5, along="x"))
    L.finish(p)
    L.cut(p, cyl_y("compact hub", 0, 0, 14.0, y0 - 1, y1 + 1))
    for x, z in [polar(F.BOLT_R, a) for a in F.BOLT_ANGLES]:
        L.cut(p, cyl_y("compact bolt", x, z, 1.7, y0 - 1, y1 + 1, n=32))
    L.cut(p, slot_y("pilot", 0, MOTOR_Z, MOTOR_PILOT_R + 0.5, MOTOR_SLOT, y0 - 1, y1 + 1))
    for sx in (1, -1):
        for sz in (1, -1):
            L.cut(p, slot_y("motor screw", sx * MOTOR_HOLE, MOTOR_Z + sz * MOTOR_HOLE, 1.7, MOTOR_SLOT, y0 - 1, y1 + 1))
    L.cut(p, slot_y("idler slot", ix, iz, 1.7, IDLER_SLOT, y0 - 1, ROLLER_Y[0] + 1, along="x"))
    seat(p, SHOULDER_Z, y1, y0)
    plate_common_cuts(p, y0, y1)
    PRINT_POSE["upper-plate-A"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -Y_REAR))
    return p


def plate_b():
    y0, y1 = -Y_REAR, -Y_REAR - PLATE_T
    p = stadium("upper-plate-B", y1, y0)
    for b in stop_blocks() + [sensor_block()]:
        L.union(p, b)
    L.finish(p)
    seat(p, 0.0, y0, y1)
    seat(p, SHOULDER_Z, y1, y0)
    h = MOTOR_SQ / 2 + 1.0
    L.cut(p, L.box("motor window", -h, h, y1 - 1, y0 + 1, MOTOR_Z - h - MOTOR_SLOT, MOTOR_Z + h + MOTOR_SLOT))
    L.cut(p, sensor_pocket())
    index_holes(p)
    plate_common_cuts(p, y1, y0)
    L.finish(p)
    PRINT_POSE["upper-plate-B"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, -Y_REAR))
    return p


def idler():
    r = cyl_y("belt-idler", 0, 0, ROLLER_R, ROLLER_Y[0] + 1.0, ROLLER_Y[1] - 1.0, n=96)
    for ya, yb in ((ROLLER_Y[0], ROLLER_Y[0] + 1.0 + 0.01), (ROLLER_Y[1] - 1.0 - 0.01, ROLLER_Y[1])):
        L.union(r, cyl_y("flange", 0, 0, ROLLER_FLANGE_R, ya, yb, n=96))
    L.finish(r)
    L.cut(r, cyl_y("axle", 0, 0, 1.75, ROLLER_Y[0] - 1, ROLLER_Y[1] + 1, n=32))
    r.data.transform(Matrix.Translation((IDLER_AT[0], 0, IDLER_AT[1])))
    PRINT_POSE["belt-idler"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (-IDLER_AT[0], -IDLER_AT[1], -ROLLER_Y[0])) if False else \
        Matrix.Translation((0, 0, 0)) @ basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -ROLLER_Y[0])) @ Matrix.Translation((-IDLER_AT[0], 0, -IDLER_AT[1]))
    return r


def pulley_envelope(z, r_od, r_hub=9.0):
    e = cyl_y("hub", 0, z, r_hub + 0.5, PULLEY_Y0 - 0.01, PULLEY_Y0 + PULLEY_HUB + 0.01)
    L.union(e, cyl_y("teeth", 0, z, r_od + 1.5, PULLEY_Y0 + PULLEY_HUB, PULLEY_Y0 + PULLEY_H))
    return e


def belt_envelope(slot):
    """Both pulleys and the belt between them, with the motor at slot (-1 to +1 of its travel)."""
    zm = MOTOR_Z + slot * MOTOR_SLOT
    band = hull([cyl_y("a", 0, 0, R60_OD + BELT_T, TEETH_Y[0] - 1.5, TEETH_Y[1] + 1.5), cyl_y("b", 0, zm, R20_OD + BELT_T, TEETH_Y[0] - 1.5, TEETH_Y[1] + 1.5)], "belt")
    L.union(band, pulley_envelope(0.0, R60_OD))
    L.union(band, pulley_envelope(zm, R20_OD))
    return band


def motor_posed(slot, length=MOTOR_L):
    zm = MOTOR_Z + slot * MOTOR_SLOT
    h = MOTOR_SQ / 2
    return L.box("motor", -h, h, Y_REAR - length, Y_REAR, zm - h, zm + h)


def screw_heads(slot):
    zm = MOTOR_Z + slot * MOTOR_SLOT
    hs = [cyl_y("head", sx * MOTOR_HOLE, zm + sz * MOTOR_HOLE, 2.75, Y_REAR + PLATE_T, Y_REAR + PLATE_T + 3.0, n=24) for sx in (1, -1) for sz in (1, -1)]
    hs += [cyl_y("head", x, z, 2.75, Y_REAR + PLATE_T, Y_REAR + PLATE_T + 3.0, n=24) for x, z in [polar(F.BOLT_R, a) for a in F.BOLT_ANGLES]]
    return hull_free_join(hs, "heads")


def hull_free_join(objs, name):
    o = join(objs, name)
    for x in objs:
        bpy.data.objects.remove(x)
    return o


def cross_members():
    return hull_free_join([cyl_y("cm", x, z, TUBE_OR, -Y_REAR - PLATE_T, Y_REAR + PLATE_T, n=32) for x, z in CROSS_MEMBERS], "cross members")


def bvh_hit(a, b):
    return bool(tree(a).overlap(tree(b)))


def swept(objs, theta):
    m = rot_elbow(theta)
    o = join(objs, f"swept {theta}")
    o.data.transform(m)
    return o


def bolt_for_nut(grip):
    """Shortest stock M3 through a plain nut (2.4) on the far face, at most 2 past it."""
    fits = [n for n in M3_STOCK if grip + 2.4 <= n <= grip + 2.4 + 2.0]
    assert fits, ("no stock M3 for this grip", grip)
    return fits[0]


def span_line_x(z):
    """x of the belt's back on the +x span at z (outer tangent of the two pitch circles)."""
    r1, r2 = 20 * 3.0 / math.pi / 2, 60 * 3.0 / math.pi / 2
    s = (r2 - r1) / BELT_C
    c = math.sqrt(1 - s * s)
    p2, p1 = Vector((r2 * c, -r2 * s * 0 + r2 * s)), Vector((r1 * c, MOTOR_Z + r1 * s))
    t = (z - p1.y) / (p2.y - p1.y)
    return p1.x + (p2.x - p1.x) * t + (BELT_T - 0.4) / c


def check_plates():
    pa, pb, idl = PARTS["upper-plate-A"], PARTS["upper-plate-B"], PARTS["belt-idler"]
    for n in ("upper-plate-A", "upper-plate-B", "belt-idler"):
        assert islands(PARTS[n]) == 1, (n, "islands", island_bounds(PARTS[n]))
        assert L.stats(PARTS[n])["non_manifold"] == 0, (n, "non-manifold", non_manifold_at(PARTS[n]))
    ang = math.atan2(250.0, 220.0)
    for n in ("upper-plate-A", "upper-plate-B"):
        c = copy(PARTS[n], "fp"); c.data.transform(PRINT_POSE[n])
        vs = [v.co for v in c.data.vertices]
        cx, cy = (max(v.x for v in vs) + min(v.x for v in vs)) / 2, (max(v.y for v in vs) + min(v.y for v in vs)) / 2
        best = None
        for k in range(-20, 21):
            a = ang - math.pi / 2 + math.radians(k)
            rx = [(v.x - cx) * math.cos(a) - (v.y - cy) * math.sin(a) for v in vs]
            ry = [(v.x - cx) * math.sin(a) + (v.y - cy) * math.cos(a) for v in vs]
            w, hgt = max(rx) - min(rx), max(ry) - min(ry)
            if w <= 220.0 and hgt <= 250.0:
                best = (round(w, 1), round(hgt, 1)); break
        assert best, (n, "doesn't fit the bed's 220 x 250 even on the diagonal")
        REPORT.setdefault("plate_on_bed_mm", {})[n] = best
        bpy.data.objects.remove(c)
        bm = bmesh.new(); bm.from_mesh(PARTS[n].data); vol = bm.calc_volume() / 1000; bm.free()
        REPORT.setdefault("plate_mass_g", {})[n] = round(vol * 1.24 * 0.55, 0)
    y_mid_a = Y_REAR + PLATE_T / 2
    assert ray_len(pa, (0, Y_REAR - 1, 0), (0, 1, 0)) is None, "compact's input rod can't leave through plate A"
    assert L.hole_diameter(copy_xz(pa), 0, 0, y_mid_a) >= 28.0, "compact hub clearance under r14"
    for s in (1, -1):
        zm = MOTOR_Z + s * MOTOR_SLOT
        assert ray_len(pa, (0, Y_REAR - 1, zm), (0, 1, 0)) is None, "pilot slot closed"
        for sx in (1, -1):
            for sz in (1, -1):
                assert ray_len(pa, (sx * MOTOR_HOLE, Y_REAR - 1, zm + sz * MOTOR_HOLE), (0, 1, 0)) is None, "motor screw slot closed"
        assert ray_len(pa, (IDLER_AT[0] + s * IDLER_SLOT, Y_REAR - 1, IDLER_AT[1]), (0, 1, 0)) is None, "idler slot closed"
    for p, z, y_in, y_out in ((pb, 0.0, -Y_REAR, -Y_REAR - PLATE_T), (pb, SHOULDER_Z, -Y_REAR - PLATE_T, -Y_REAR), (pa, SHOULDER_Z, Y_REAR + PLATE_T, Y_REAR)):
        ym = y_in + (y_out - y_in) * B6810[2] / PLATE_T / 2
        d = seat_diameter(p, z, ym)
        assert 2 * B6810[1] <= d <= 2 * B6810[1] + 0.2, ("6810 seat", p.name, z, d)
        lip = seat_diameter(p, z, y_out + (y_in - y_out) * 0.05 / PLATE_T * 10)
        assert LIP_IN_R * 2 - 0.2 <= lip <= 2 * (B6810[1] - 1.5), ("lip", p.name, z, lip)
        assert LIP_IN_R >= 27.5 + 0.5
    assert PLATE_T - B6810[2] >= LIP_T
    c_mid = math.hypot(0, MOTOR_Z)
    assert abs(c_mid - C.belt_centre_distance(20, 60, 420, pitch=3.0)) < 0.1, "belt centres"
    dx = span_line_x(IDLER_AT[1]) - (IDLER_AT[0] - ROLLER_R)
    assert dx >= 2.0, ("idler deflects the belt by less than 2", dx)
    heads = {s: screw_heads(s) for s in (-1, 1)}
    cm = cross_members()
    for s in (-1, 1):
        env = belt_envelope(s)
        for o, n in ((pa, "plate A"), (heads[s], "screw heads"), (cm, "cross members")):
            assert overlap(env, o) < 0.05, ("belt envelope hits", n, s)
        assert max(v.co.y for v in env.data.vertices) <= BELT_ENVELOPE_Y - 2.0 + 0.01
        long = motor_posed(s, MOTOR_L_MAX)
        for o, n in ((pb, "plate B"), (cm, "cross members"), (PARTS["elbow-hub"], "hub"), (pa, "plate A")):
            assert overlap(long, o) < 0.05, ("60 mm motor hits", n, s)
    assert PULLEY_Y0 - (Y_REAR + PLATE_T) >= 1.0 - 0.01, "60T's inside face within 1 of plate A"
    assert TEETH_Y[0] > PULLEY_Y0 + PULLEY_HUB and PULLEY_Y0 + PULLEY_HUB / 2 < Y_REAR + MOTOR_SHAFT_L, "20T's set screw past the shaft"
    for o, n in ((pa, "plate A"), (pb, "plate B")):
        for x, z in CROSS_MEMBERS:
            ym = (Y_REAR + PLATE_T / 2) * (1 if o is pa else -1)
            d = seat_diameter(o, z, ym, x=x)
            assert 2 * TUBE_OR <= d <= 2 * TUBE_OR + 0.3, ("cross member hole", n, x, z, d)
    moving = [PARTS["elbow-hub"]] + TUBES
    hits = []
    for th in range(int(RANGE[0]), int(RANGE[1]) + 1, 2):
        s = swept(moving, th)
        if bvh_hit(s, cm):
            hits.append(th)
        bpy.data.objects.remove(s)
    assert not hits, ("hub or tubes hit a cross member", hits)
    tab = stop_tab(); blocks = hull_free_join(stop_blocks(), "blocks")
    gaps = {}
    for th in (STOPS[0] + 0.5, RANGE[0], RANGE[1], STOPS[1] - 0.5, STOPS[0], STOPS[1]):
        t = copy(tab, "t"); t.data.transform(rot_elbow(th))
        gaps[th] = round(min_gap(t, blocks), 2)
        bpy.data.objects.remove(t)
    assert gaps[STOPS[0]] <= 0.05 and gaps[STOPS[1]] <= 0.05, ("tab doesn't meet the stops", gaps)
    assert gaps[STOPS[0] + 0.5] <= 0.3 and gaps[STOPS[1] - 0.5] <= 0.3, ("plan's -22/+152 not within 0.3", gaps)
    assert gaps[RANGE[0]] >= 1.0 and gaps[RANGE[1]] >= 1.0, ("stops within 1 mm inside the range", gaps)
    for th in range(int(RANGE[0]), int(RANGE[1]) + 1, 2):
        t = copy(tab, "t"); t.data.transform(rot_elbow(th))
        assert not bvh_hit(t, blocks), ("tab hits a stop inside the range", th)
        bpy.data.objects.remove(t)
    magnet = rot_elbow(0.0) @ Vector((0, sum(TAB_Y) / 2, -TAB_R[1]))
    sensor_face = Vector((-(TAB_R[1] + SENSOR_GAP), sum(TAB_Y) / 2, 0))
    gap = (sensor_face - magnet).length
    assert 1.0 <= gap <= 2.0, ("Hall gap at home", gap)
    assert ray_len(pb, (-(TAB_R[1] + SENSOR_GAP) - 0.2, -Y_REAR - PLATE_T - 2.0, 0), (-1, 0, 0)) >= SENSOR[2] - 0.2, "sensor pocket missing"
    REPORT.update({"belt_centre_mm": BELT_C, "idler_deflection_mm": round(dx, 2), "stop_gaps_mm": gaps, "hall_gap_mm": round(gap, 2),
                   "bolts": {"elbow compact to plate A (nut on its front face)": bolt_for_nut(PLATE_T + HOUSING_L),
                             "motor to plate A": 12, "idler axle": 30, "collar clamp": 20, "hub to compact carrier": 12}})


def non_manifold_at(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    pts = [tuple(round(c, 1) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges if not e.is_manifold]
    bm.free(); return pts[:8]


def shoulder_hub():
    """Fixed to the body; the plates turn on it. Shoulder on plate A's 6810, end flanges carry the body's interface."""
    z, y0, y1 = SHOULDER_Z, SHOULDER_HUB_Y[0], SHOULDER_HUB_Y[1]
    h = cyl_y("shoulder-hub", 0, z, SHOULDER_HUB_R, y0, y1, n=192)
    L.union(h, cyl_y("shoulder", 0, z, SHOULDER_SHOULDER_R, Y_REAR + PLATE_T + 0.3, y1 - HUB_END_T + 0.01, n=192))
    L.union(h, cyl_y("end", 0, z, HUB_END_R, y1 - HUB_END_T, y1, n=192))
    L.finish(h)
    L.cut(h, cyl_y("bore", 0, z, SHOULDER_BORE_R, y0 - 1, y1 + 1, n=128))
    for a in HUB_END_ANGLES:
        x, dz = polar(HUB_END_INSERT_R, a)
        L.cut(h, cyl_y("insert", x, z + dz, 2.0, y1 - HUB_END_INSERT_DEPTH, y1 + 1, n=32))
    PRINT_POSE["shoulder-hub"] = basis((1, 0, 0), (0, 0, -1), (0, 1, 0), (0, 0, y1)) @ Matrix.Translation((0, 0, -z))
    return h


def shoulder_clamp():
    """Pinch collar on the hub's plate B end: pushes plate B's 6810 inner ring inwards, carries the other end flange."""
    z, y0, y1 = SHOULDER_Z, CLAMP_Y[0], CLAMP_Y[1]
    c = cyl_y("shoulder-hub-clamp", 0, z, HUB_END_R, y0, y1 - 0.5, n=192)
    L.union(c, cyl_y("face", 0, z, SHOULDER_SHOULDER_R, y1 - 0.51, y1, n=192))
    L.finish(c)
    L.cut(c, cyl_y("bore", 0, z, SHOULDER_HUB_R, y0 - 1, y1 + 1, n=192))
    L.cut(c, L.box("split", -CLAMP_SPLIT / 2, CLAMP_SPLIT / 2, y0 - 1, y1 + 1, z + SHOULDER_HUB_R - 1, z + HUB_END_R + 1))
    ym = (y0 + y1) / 2 - 1.0
    L.cut(c, rod("pinch", Vector((-12, ym, z + CLAMP_PINCH)), Vector((12, ym, z + CLAMP_PINCH)), 1.7, n=24))
    L.cut(c, L.box("pinch nut", 4.0, 4.0 + NUT_T, ym - NUT_AF / 2, ym + NUT_AF / 2, z + CLAMP_PINCH - NUT_AF / 2, z + HUB_END_R + 1))
    for a in HUB_END_ANGLES:
        x, dz = polar(HUB_END_INSERT_R, a)
        L.cut(c, cyl_y("insert", x, z + dz, 2.0, y0 - 1, y0 + HUB_END_INSERT_DEPTH, n=32))
    PRINT_POSE["shoulder-hub-clamp"] = basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, -y0)) @ Matrix.Translation((0, 0, -z))
    return c


def bench_stand():
    """Two cheeks bolted to the hub's end faces, a base with clamp pads, and a Ø4 index pin hole into plate B."""
    z = SHOULDER_Z
    ya, yb = SHOULDER_HUB_Y[1], SHOULDER_HUB_Y[0]
    w = HUB_END_R + 6.0
    parts = [L.box("cheek A", -w, w, ya, ya + STAND_T, STAND_BASE_Z - 0.01, z),
             cyl_y("cheek A top", 0, z, w, ya, ya + STAND_T, n=96),
             L.box("cheek B", -w, w, yb - STAND_T, yb, STAND_BASE_Z - 0.01, z),
             cyl_y("cheek B top", 0, z, w, yb - STAND_T, yb, n=96),
             L.box("base", -w, w, yb - STAND_T, ya + STAND_T, STAND_BASE_Z - STAND_BASE_T, STAND_BASE_Z)]
    px, pz = polar(INDEX_R, INDEX_PIN_DEG)
    parts.append(L.box("pin arm", -w, px + 6.0, yb - STAND_T, yb, z, z + pz + 6.0))
    for sx in (1, -1):
        x0, x1 = sorted((sx * w, sx * (STAND_PAD[0] + 40.0)))
        parts.append(L.box("pad", x0 - 0.01, x1 + 0.01, (yb + ya) / 2 - STAND_PAD[1] / 2, (yb + ya) / 2 + STAND_PAD[1] / 2, STAND_BASE_Z - STAND_BASE_T, STAND_BASE_Z))
    s = join(parts, "bench-stand")
    for o in parts:
        bpy.data.objects.remove(o)
    L.finish(s)
    L.cut(s, cyl_y("pin", px, z + pz, INDEX_HOLE_R, yb - STAND_T - 1, yb + 1, n=32))
    for yf, yo in ((ya, ya + STAND_T), (yb - STAND_T, yb)):
        L.cut(s, cyl_y("wires", 0, z, SHOULDER_BORE_R, yf - 1, yo + 1, n=96))
        for a in HUB_END_ANGLES:
            x, dz = polar(HUB_END_INSERT_R, a)
            L.cut(s, cyl_y("bolt", x, z + dz, 1.7, yf - 1, yo + 1, n=32))
    PRINT_POSE["bench-stand"] = Matrix.Translation((0, 0, -(STAND_BASE_Z - STAND_BASE_T)))
    return s


def index_holes(p):
    for psi in INDEX_ANGLES:
        x, z = polar(INDEX_R, INDEX_PIN_DEG + psi)
        L.cut(p, cyl_y("index", x, SHOULDER_Z + z, INDEX_HOLE_R, -Y_REAR - PLATE_T - 1, -Y_REAR + 1, n=32))


def rot_shoulder(psi):
    """The upper arm pitched forward by psi about the shoulder axis (elbow towards +x)."""
    c = Vector((0, 0, SHOULDER_Z))
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(psi), 4, 'Y') @ Matrix.Translation(-c)


def check_shoulder():
    hub, clamp, stand = PARTS["shoulder-hub"], PARTS["shoulder-hub-clamp"], PARTS["bench-stand"]
    for n in ("shoulder-hub", "shoulder-hub-clamp", "bench-stand"):
        assert islands(PARTS[n]) == 1, (n, "islands", island_bounds(PARTS[n]))
        assert L.stats(PARTS[n])["non_manifold"] == 0, (n, "non-manifold", non_manifold_at(PARTS[n]))
    for y0, y1 in SHOULDER_6810_Y:
        ym = (y0 + y1) / 2
        r = 60 - sum(ray_len(hub, (60 * math.cos(a), ym, SHOULDER_Z + 60 * math.sin(a)), (-math.cos(a), 0, -math.sin(a)))
                     for a in [2 * math.pi * (k + 0.37) / 24 for k in range(24)]) / 24
        assert B6810[0] - 0.01 <= r <= B6810[0] + 0.1, ("shoulder journal", ym, r)
    assert seat_diameter(hub, SHOULDER_Z, 0.0) >= 2 * SHOULDER_BORE_R - 0.05, "shoulder wire bore under Ø44"
    sh = [v.co for v in hub.data.vertices if math.hypot(v.co.x, v.co.z - SHOULDER_Z) > B6810[0] + 0.05 and abs(v.co.y) < Y_REAR + PLATE_T + 0.4]
    assert not sh or max(math.hypot(p.x, p.z - SHOULDER_Z) for p in sh) <= SHOULDER_SHOULDER_R + 0.01, "hub shoulder past the inner ring"
    assert SHOULDER_SHOULDER_R <= 27.5
    assert SHOULDER_HUB_Y[1] >= BELT_ENVELOPE_Y + 8.0 - 0.01 and max(v.co.y for v in hub.data.vertices) >= SHOULDER_HUB_Y[1] - 0.01
    for y_face, o, into in ((SHOULDER_HUB_Y[1], hub, -1), (SHOULDER_HUB_Y[0], clamp, 1)):
        for a in HUB_END_ANGLES:
            x, z = polar(HUB_END_INSERT_R, a)
            d = ray_len(o, (x, y_face - into * 1.0, SHOULDER_Z + z), (0, into, 0))
            assert d is not None and abs(d - 1.0 - HUB_END_INSERT_DEPTH) < 0.06, ("hub end insert", o.name, a, d)
    for n, o in (("plate A", PARTS["upper-plate-A"]), ("plate B", PARTS["upper-plate-B"])):
        assert overlap(hub, o) < 0.05 and overlap(clamp, o) < 0.05, ("shoulder hub hits", n)
    assert overlap(clamp, hub) < 0.05 and touching(clamp, hub), "clamp doesn't grip the hub's journal"
    for psi in INDEX_ANGLES:
        m = rot_shoulder(psi)
        moving = [copy(PARTS[k], "mv") for k in ("upper-plate-A", "upper-plate-B")] + [motor_posed(s, MOTOR_L_MAX) for s in (-1, 1)] + [belt_envelope(s) for s in (-1, 1)]
        for o in moving:
            o.data.transform(m)
            assert not bvh_hit(o, stand), ("stand hits the arm at shoulder", psi, o.name)
        pb = moving[1]
        px, pz = polar(INDEX_R, INDEX_PIN_DEG)
        hit = tree(pb).ray_cast(Vector((px, -Y_REAR - PLATE_T - 3.0, SHOULDER_Z + pz)), Vector((0, 1, 0)))[0]
        assert hit is None or hit.y > -Y_REAR + 0.1, ("index hole doesn't line up with the stand's pin", psi)
        for o in moving:
            bpy.data.objects.remove(o)
    px, pz = polar(INDEX_R, INDEX_PIN_DEG)
    pin = ray_len(stand, (px, SHOULDER_HUB_Y[0] - STAND_T - 5.0, SHOULDER_Z + pz), (0, 1, 0))
    assert pin is None or pin > STAND_T + 6.0, "stand has no pin hole"
    pads = [v.co for v in stand.data.vertices if abs(v.co.z - (STAND_BASE_Z - STAND_BASE_T)) < 0.01]
    assert pads and max(abs(p.x) for p in pads) >= STAND_PAD[0] + 40.0 - 0.01, "stand has no clamp pads"
    for n in ("shoulder-hub", "shoulder-hub-clamp", "bench-stand"):
        c = copy(PARTS[n], "fp"); c.data.transform(PRINT_POSE[n]); d = c.dimensions
        assert d.x <= 220 and d.y <= 250 and d.z <= 250, (n, "doesn't fit the bed", tuple(d))
        bpy.data.objects.remove(c)
    REPORT.update({"shoulder_hub_y": SHOULDER_HUB_Y, "hub_end_interface": {"insert_r": HUB_END_INSERT_R, "angles": HUB_END_ANGLES, "bore_d": 2 * SHOULDER_BORE_R}})


def copy_xz(o):
    """o with y turned onto z, for L.hole_diameter's z bores."""
    c = copy(o, "xz"); c.data.transform(basis((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, 0))); return c


def seat_diameter(o, z, y, x=0.0):
    ds = []
    for k in range(24):
        a = 2 * math.pi * (k + 0.37) / 24   # off the polygon's vertices, where a ray can slip between faces
        r = ray_len(o, (x, y, z), (math.cos(a), 0, math.sin(a)))
        if r is not None:
            ds.append(r)
    return 2 * sum(ds) / len(ds)


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
    assert abs(min(v.co.y for v in hub.data.vertices if math.hypot(v.co.x, v.co.z) > B6810[0] + 0.5 and v.co.y > -Y_REAR - PLATE_T) - HUB_DISC_Y[1]) < 0.01, "hub reaches into the 6810 between the plates"
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
PARTS["upper-plate-A"] = plate_a()
PARTS["upper-plate-B"] = plate_b()
PARTS["belt-idler"] = idler()
PARTS["shoulder-hub"] = shoulder_hub()
PARTS["shoulder-hub-clamp"] = shoulder_clamp()
PARTS["bench-stand"] = bench_stand()
CHECKS.append(check_bracket)
CHECKS.append(check_plates)
CHECKS.append(check_shoulder)
for check in CHECKS:
    check()
print("ELBOW", json.dumps({**{n: L.stats(o) for n, o in PARTS.items()}, **REPORT}))
os.makedirs(OUT, exist_ok=True)
for n, o in PARTS.items():
    o.matrix_world = Matrix()
    o.data.transform(PRINT_POSE[n])
    L.export(o, os.path.join(OUT, n + ".stl"))
print("ELBOW DONE")
