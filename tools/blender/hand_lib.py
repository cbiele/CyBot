"""Shared geometry for the three-finger hand (spec 2026-09-22). Finger frame: x along the
finger from base to tip, +y dorsal, z across the width. Knuckle axes run along z."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

W, H = 20.0, 12.0            # finger width across the pin, height
CHEEK, TONGUE, GAP = 5.0, 9.0, 0.5
R = H / 2                    # rounded knuckle ends
FORK_LEN = 8.0               # web to axis
TONGUE_LEN = 7.0             # axis to the wide body
CHEEK_BORE, TONGUE_BORE = 3.85, 4.2
TAB_Y0, TAB_Y1, TAB_BACK = 6.3, 7.8, 3.0          # dorsal extension stop over the cheeks
HEEL_X0, HEEL_X1, HEEL_Y = -8.0, -3.5, -7.2       # palmar flexion stop under the cheeks (~87 deg)
TENDON_W, TENDON_DEPTH = 2.0, 2.0
WIRE_D, CHAMBER, CAVITY_R = 1.8, 4.0, 4.0      # two 30 AWG PTFE wires; wire cavity width along the pin and its radius
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

def cyl_between(name, a, b, r, n=32):
    """Cylinder from point a to point b (wire channels)."""
    a, b = Vector(a), Vector(b); d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=d.length + 0.02)
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

def bore_tongue(target, xa, direction=1, d=TONGUE_BORE):
    s = direction
    cut(target, cyl_z("tongue_bore", xa, 0, d / 2, -W / 2 - 1, W / 2 + 1))
    # wire cavity: a quarter ring round the pin from the body side to the dorsal side, so the pin
    # slot opens into free space from 3 deg of hyperextension to 90 deg of flexion; the wire wraps
    # a quarter turn round the pin in here as the joint curls
    cav = cyl_z("cavity", xa, 0, CAVITY_R, -CHAMBER / 2, CHAMBER / 2)
    kx0, kx1 = sorted((xa - s * 1.0, xa + s * (CAVITY_R + 1)))
    boolean(cav, box("keep", kx0, kx1, -1.5, CAVITY_R + 1, -3, 3), 'INTERSECT')
    cut(target, cav)
    # tendon ring: 2 mm wide groove around the palmar half of the rounded end
    ring = cyl_z("ring", xa, 0, R + 0.5, -TENDON_W / 2, TENDON_W / 2)
    boolean(ring, cyl_z("ring_in", xa, 0, R - TENDON_DEPTH, -TENDON_W / 2 - 1, TENDON_W / 2 + 1), 'DIFFERENCE')
    boolean(ring, box("ring_clip", xa - R - 1, xa + R + 1, -R - 1, 0.0, -2, 2), 'INTERSECT')
    cut(target, ring)

def tendon_groove(target, x0, x1):
    cut(target, box("groove", x0, x1, -R - 0.1, -R + TENDON_DEPTH, -TENDON_W / 2, TENDON_W / 2))

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

def snap_pad(name, length, thickness=1.8, wing=2.0, slot=2.6):
    """Snap-on TPU grip pad: a palmar plate with a through-slot for the tendon, two wings up
    the side faces and inward lips that drop into snap_grooves(). Modelled in place on a
    phalanx whose palmar face is y=-R, from x=0 to x=length."""
    y_face = -R
    pad = box(name, 0, length, y_face - thickness, y_face, -W / 2 - wing, W / 2 + wing)
    for zs in (1, -1):
        z0, z1 = sorted((zs * (W / 2 + 0.1), zs * (W / 2 + wing)))
        union(pad, box("wing", 0, length, y_face - thickness, SNAP_Y1, z0, z1))
        l0, l1 = sorted((zs * (W / 2 - SNAP_DEPTH + 0.1), zs * (W / 2 + 0.1 + 0.01)))
        union(pad, box("lip", 0, length, SNAP_Y0 + 0.1, SNAP_Y1 - 0.1, l0, l1))
    cut(pad, box("tendon_slot", -1, length + 1, y_face - thickness - 1, y_face + 1, -slot / 2, slot / 2))
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

def export(o, path):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
