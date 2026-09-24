"""Shared geometry for the three-finger hand (spec 2026-09-22). Finger frame: x along the
finger from base to tip, +y dorsal, z across the width. Knuckle axes run along z."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

W, H = 23.0, 12.0            # finger width across the pins, height
CHEEK, TONGUE, GAP = 5.0, 12.0, 0.5
PIN_L = 8.0                  # ISO 8752 4 x 8 cheek pins, one pressed flush from each cheek face
PIN_GAP = W - 2 * PIN_L      # 7 mm between the cheek pins' ends: the tongue's core
CORE_PIN_L, CORE_BORE = 8.0, 2.0   # O2 x 8 stainless dowel pressed into each core face; the cheek pin slides over it
WIRE_GAP = 3.0               # open width between the two core pins where the wire crosses the axis
CORE_FLOOR = 2.0             # core bores stop here, 0.5 mm before the wire gap so the press has a solid floor
R = H / 2                    # rounded knuckle ends
FORK_LEN = 8.0               # web to axis
TONGUE_LEN = 7.0             # axis to the wide body
CHEEK_BORE, TONGUE_BORE = 3.85, 4.7    # cheek press fit; tongue clearance round the cheek pin (it turns on the core pin)
TAB_Y0, TAB_Y1, TAB_BACK = 6.3, 7.8, 3.0          # dorsal extension stop over the cheeks
HEEL_X0, HEEL_X1, HEEL_Y = -8.0, -3.5, -7.2       # palmar flexion stop under the cheeks (~87 deg)
WIRE_D = 1.8                 # two 30 AWG PTFE wires as a pair, on the knuckle axis line
TENDON_Y, TENDON_D = -4.0, 2.0                  # enclosed tendon channel, 4 mm palmar of the axis line
TENDON_MOUTH = 4.0           # a tongue's tendon channel starts this far past its axis: with the mouth at
                             # least 4 mm past the axis the free span stays palmar of the axis up to 90 deg
STRIP_W, STRIP_T, PAD_L = 8.0, 2.0, 8.0            # TPU return strip
SNAP_Y0, SNAP_Y1, SNAP_DEPTH = -4.0, -2.5, 1.0      # side grooves that a snap-on grip pad's lips engage
DOT_R, DOT_H, DOT_Z = 1.2, 1.0, 5.5                 # front snap dots on the pad, dimples in the palmar face

def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

def box(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return _obj(name, bm)

def cyl_z(name, x, y, r, z0, z1, n=64):
    """Cylinder along z (a knuckle axis or bore)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(x, y, (z0 + z1) / 2), verts=bm.verts)
    return _obj(name, bm)

def cyl_between(name, a, b, r, n=32, r_end=None):
    """Cylinder from point a to point b (wire channels); a cone when r_end differs."""
    a, b = Vector(a), Vector(b); d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r if r_end is None else r_end, depth=d.length + 0.02)
    o = _obj(name, bm)
    o.matrix_world = Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    return o

def boolean(target, tool, op):
    m = target.modifiers.new(op, "BOOLEAN"); m.operation = op; m.solver = 'EXACT'; m.object = tool
    bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(tool)

def union(target, tool): boolean(target, tool, 'UNION')
def cut(target, tool): boolean(target, tool, 'DIFFERENCE')

def fork(target, xa, with_heels=True):
    """Add a fork whose axis is at x=xa: two cheeks from the web at xa-FORK_LEN, rounded R
    about the axis, plus the palmar heel stops. Cheek bore left to bore_cheeks()."""
    for zs in (1, -1):
        z0, z1 = sorted((zs * (TONGUE / 2 + GAP), zs * W / 2))
        union(target, box("cheek", xa - FORK_LEN, xa, -R, R, z0, z1))
        union(target, cyl_z("cheek_end", xa, 0, R, z0, z1))
        if with_heels:
            union(target, box("heel", xa + HEEL_X0, xa + HEEL_X1, HEEL_Y, -R + 0.01, z0, z1))

def bore_cheeks(target, xa, d=CHEEK_BORE):
    cut(target, cyl_z("cheek_bore", xa, 0, d / 2, -W / 2 - 1, W / 2 + 1))

def tongue(target, xa, direction=1):
    """Add a tongue whose axis is at x=xa, body side toward +x*direction. Rounded end R about
    the axis, a taller dorsal section joining the full-width tab that stops hyperextension.
    Bore, chamber and tendon ring are cut afterwards by bore_tongue()."""
    s = direction
    x_body = xa + s * TONGUE_LEN
    x0, x1 = sorted((xa, x_body))
    union(target, box("tongue", x0, x1, -R, TAB_Y1, -TONGUE / 2, TONGUE / 2))
    union(target, cyl_z("tongue_end", xa, 0, R, -TONGUE / 2, TONGUE / 2))
    tx0, tx1 = sorted((xa - s * TAB_BACK, x_body + s * 0.01))
    union(target, box("tab", tx0, tx1, TAB_Y0, TAB_Y1, -W / 2, W / 2))

def bore_tongue(target, xa, direction=1, d=TONGUE_BORE, d_core=CORE_BORE):
    """From each tongue face: a clearance bore round the cheek pin as far as it reaches, then a
    press bore for the core pin down to just short of the wire gap. The cheek pin slides over the
    core pin, so the joint turns steel on steel and the tongue never rubs the cheek pin. Between
    the cores, the open pocket where the wire and the tendon cross the joint."""
    s = direction; hz = WIRE_GAP / 2; hp = PIN_GAP / 2
    for zs in (1, -1):
        cut(target, cyl_z("clear_bore", xa, 0, d / 2, *sorted((zs * hp, zs * (W / 2 + 1)))))
        cut(target, cyl_z("core_bore", xa, 0, d_core / 2, *sorted((zs * CORE_FLOOR, zs * (hp + 1)))))
    # the rear palmar quarter of the tongue, axis to rounded end: it faces the fork web at every
    # angle from extension to 90 deg, so the wire on the axis line bends freely in it
    x0, x1 = sorted((xa - s * (R + 0.5), xa))
    cut(target, box("wire_pocket", x0, x1, -R - 0.5, 1.0, -hz, hz))
    # the tendon's part of the pocket runs on to its channel mouth past the axis
    x0, x1 = sorted((xa - s * (R + 0.5), xa + s * TENDON_MOUTH))
    cut(target, box("tendon_pocket", x0, x1, -R - 0.5, TENDON_Y + TENDON_D / 2, -hz, hz))

def channel(target, y, x0, x1, d):
    """Straight enclosed channel along the finger at height y, on the z=0 plane."""
    cut(target, cyl_between("channel", (x0, y, 0), (x1, y, 0), d / 2))

def flare(target, x, y, direction, d, d_out):
    """Widen a channel mouth on the face at x into a 1.5 mm cone; direction is the way the
    channel runs away from the face. A line bending at the mouth rides the cone, not an edge."""
    cut(target, cyl_between("flare", (x - direction * 0.05, y, 0), (x + direction * 1.5, y, 0), d_out / 2, r_end=d / 2))

def strip_pocket(target, x0, x1):
    """Dorsal pocket for the glued end of the TPU skin (its return-spring run)."""
    cut(target, box("pocket", x0, x1, R - STRIP_T - 0.2, R + 0.1, -(STRIP_W + 2.2) / 2, (STRIP_W + 2.2) / 2))

def sphere(name, x, y, z, r, n=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=n // 2, radius=r)
    bmesh.ops.translate(bm, vec=(x, y, z), verts=bm.verts)
    return _obj(name, bm)

def dot_positions(x0, x1):
    """Two front snap dots on a diagonal so the pad is located lengthwise as well."""
    return ((x0 + (x1 - x0) * 0.25, DOT_Z), (x0 + (x1 - x0) * 0.75, -DOT_Z))

def snap_dimples(target, x0, x1):
    """Dimples in the palmar face that the pad's front dots snap into."""
    for x, z in dot_positions(x0, x1):
        cut(target, sphere("dimple", x, -R - (DOT_R - DOT_H) , z, DOT_R + 0.15))

def snap_grooves(target, x0, x1):
    """Grooves along both side faces near the palmar edge for a snap-on TPU grip pad."""
    for zs in (1, -1):
        z0, z1 = sorted((zs * (W / 2 - SNAP_DEPTH), zs * (W / 2 + 1)))
        cut(target, box("snap", x0, x1, SNAP_Y0, SNAP_Y1, z0, z1))

def snap_pad(name, length, thickness=1.8, wing=2.0):
    """Snap-on TPU grip pad: a palmar plate, two wings up the side faces and inward lips that
    drop into snap_grooves(). Modelled in place on a phalanx whose palmar face is y=-R, from
    x=0 to x=length."""
    y_face = -R
    pad = box(name, 0, length, y_face - thickness, y_face, -W / 2 - wing, W / 2 + wing)
    for zs in (1, -1):
        z0, z1 = sorted((zs * (W / 2 + 0.1), zs * (W / 2 + wing)))
        union(pad, box("wing", 0, length, y_face - thickness, SNAP_Y1, z0, z1))
        l0, l1 = sorted((zs * (W / 2 - SNAP_DEPTH + 0.1), zs * (W / 2 + 0.1 + 0.01)))
        union(pad, box("lip", 0, length, SNAP_Y0 + 0.1, SNAP_Y1 - 0.1, l0, l1))
    for x, z in dot_positions(0, length):
        union(pad, sphere("dot", x, y_face - (DOT_R - DOT_H), z, DOT_R))   # hemisphere standing DOT_H proud of the plate
    return pad

def finish(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bm.to_mesh(o.data); bm.free()

def stats(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold); bm.free()
    d = o.dimensions
    return {"dims": [round(d.x, 2), round(d.y, 2), round(d.z, 2)], "faces": len(o.data.polygons), "non_manifold": nm}

def hole_diameter(o, x, y, z_probe):
    """Measure a z-axis bore at (x, y) by casting rays outward in the plane z=z_probe."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    import mathutils
    tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); ds = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        hit = tree.ray_cast(Vector((x, y, z_probe)), Vector((math.cos(a), math.sin(a), 0)))
        if hit[0] is not None: ds.append((hit[0] - Vector((x, y, z_probe))).length)
    bm.free()
    return round(2 * sum(ds) / len(ds), 3) if ds else None

def _tree(o):
    import mathutils
    bm = bmesh.new(); bm.from_mesh(o.data)
    return mathutils.bvhtree.BVHTree.FromBMesh(bm), bm

def bore_floor_z(o, x, y, z_start):
    """z of the first face met going down from (x, y, z_start): the floor of a blind z bore."""
    tree, bm = _tree(o)
    h = tree.ray_cast(Vector((x, y, z_start)), Vector((0, 0, -1)))[0]; bm.free()
    return round(h.z, 3) if h is not None else None

def first_hit_x(o, y, x_start, r=0.4):
    """Push a line along x at (y, z=0) from x_start: the x of the first thing it meets, or None.
    Four rays r off the axis so the line's own thickness counts and no ray rides an edge."""
    tree, bm = _tree(o); xs = []
    for dy, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
        h = tree.ray_cast(Vector((x_start, y + dy, dz)), Vector((1, 0, 0)))
        if h[0] is not None: xs.append(h[0].x)
    bm.free()
    return round(min(xs), 3) if xs else None

def export(o, path):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
