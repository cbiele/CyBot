"""Build model/cycloid-poc/20-1-compact/exploded.blend: the POC drive assembled and blown out along its axis,
from the printed STLs plus stand-ins for the bought hardware (bearings, pins, bushings, rod, pulleys, belt,
motor, bolts). Two collections: cycloid-poc-assembled (true positions, shown above) and
cycloid-poc-exploded (pushed apart in assembly order, rear to front). Also renders a PNG next to it.
Positions follow the assembly frame of cycloid_poc.py (axis on z, z=0 the housing's rear face, input at 0);
the stack constants below are copied from it and must follow it if it changes.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc_explode.py"""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
BASE = os.path.join(ROOT, "model", "cycloid-poc")
OUT = os.path.join(BASE, "20-1-compact")
GAP = 26.0
LIFT = 150.0                                 # the assembled copy sits this far above the exploded row

LIP_T, BRG_W, SHOULDER_T, PLATE_T, GAP_DISK, DISK_T, COLLAR_T = 0.8, 7.0, 0.5, 4.0, 0.5, 6.0, 1.0
Z_DISK0 = LIP_T + BRG_W + SHOULDER_T + PLATE_T + GAP_DISK
Z_MID = Z_DISK0 + DISK_T + COLLAR_T / 2
L_HOUSING = 2 * Z_MID
Z_IN = Z_DISK0 - GAP_DISK
Z_HUB_FRONT = L_HOUSING + 1.0
BOLT_R, INSERT_PCD_R = 30.0, 6.5
BOLT_ANGLES = [45 + 90 * k for k in range(4)]
INSERT_ANGLES = [90 + 120 * k for k in range(3)]
ARM_TOP = Z_HUB_FRONT + 4.0 + 6.0
MOTOR_X = round(C.belt_centre_distance(20, 40, 232), 2)
UPRIGHT_BACK = -5.0
ROD_FRONT = L_HOUSING - Z_IN                 # flush with the front 625's outer face
ROD_L = 57.0
PULLEY_Z0 = UPRIGHT_BACK - 0.5               # hub towards the upright, set screw reachable
PRINT_FLIP = {"housing-front", "carrier-rear"}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 0.001; scene.unit_settings.length_unit = 'MILLIMETERS'

def mat(name, rgba):
    m = bpy.data.materials.new(name); m.diffuse_color = rgba; return m
MATS = {k: mat(k, v) for k, v in {
    "housing": (0.25, 0.45, 0.80, 1), "carrier": (0.30, 0.75, 0.35, 1), "disk-a": (0.95, 0.55, 0.10, 1),
    "disk-b": (0.95, 0.80, 0.15, 1), "eccentric": (0.85, 0.20, 0.20, 1), "bench": (0.70, 0.70, 0.72, 1),
    "bearing": (0.30, 0.30, 0.34, 1), "steel": (0.78, 0.80, 0.84, 1), "bronze": (0.80, 0.50, 0.22, 1),
    "brass": (0.85, 0.70, 0.25, 1), "pulley": (0.85, 0.85, 0.90, 1), "belt": (0.06, 0.06, 0.06, 1),
    "motor": (0.15, 0.15, 0.17, 1)}.items()}

def ring_mesh(name, od, id_, w, n=48):
    bm = bmesh.new(); rings = []
    for r, z in ((od / 2, w / 2), (id_ / 2, w / 2), (id_ / 2, -w / 2), (od / 2, -w / 2)):
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)) for i in range(n)])
    for k in range(4):
        a, b = rings[k], rings[(k + 1) % 4]
        for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); return o

def gt2_pulley(name, teeth, length=16.0, hub_l=7.0):
    """Bought GT2 pulley, shown plain: hub at z 0..hub_l, then flange, 7 mm of teeth, flange."""
    r = teeth * 2.0 / math.pi / 2 - 0.254
    p = L.cyl_z(name, 0, 0, max(r * 0.65, 4.5), 0, hub_l + 0.01, n=64)
    L.union(p, L.cyl_z("flange", 0, 0, r + 1.5, hub_l, hub_l + 1, n=96))
    L.union(p, L.cyl_z("teeth", 0, 0, r, hub_l + 0.99, length - 0.99, n=teeth * 2))
    L.union(p, L.cyl_z("flange", 0, 0, r + 1.5, length - 1, length, n=96))
    L.cut(p, L.cyl_z("bore", 0, 0, 2.5, -1, length + 1, n=32))
    return p

def belt(name, d=MOTOR_X, w=6.0, t=1.4):
    """232 GT2 loop round the 40T at the origin and the 20T at x = d, on the pitch line."""
    r1, r2 = 40 / math.pi, 20 / math.pi
    b = math.acos((r1 - r2) / d); n = 120
    pts = [((0, 0), r1, b + (2 * math.pi - 2 * b) * i / n) for i in range(n + 1)]
    pts += [((d, 0), r2, -b + 2 * b * i / (n // 3)) for i in range(n // 3 + 1)]
    bm = bmesh.new(); loops = []
    for dr, z in ((-0.6, -w / 2), (t - 0.6, -w / 2), (t - 0.6, w / 2), (-0.6, w / 2)):
        loops.append([bm.verts.new((c[0] + (r + dr) * math.cos(a), c[1] + (r + dr) * math.sin(a), z)) for c, r, a in pts])
    m = len(pts)
    for k in range(4):
        a, c = loops[k], loops[(k + 1) % 4]
        for i in range(m): bm.faces.new((a[i], a[(i + 1) % m], c[(i + 1) % m], c[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); return o

def motor(name):
    """17HS8401B: 42.3 square x 48 body on the upright's front face, pilot boss and 5 mm shaft through it."""
    m = L.box(name, -21.15, 21.15, -21.15, 21.15, 0, 48)
    L.union(m, L.cyl_z("boss", 0, 0, 11, -2, 0.01, n=64))
    L.union(m, L.cyl_z("shaft", 0, 0, 2.5, -24, -1.99, n=32))
    return m

def bolt(name, length, head_r=2.75, head_h=3.0):
    """Socket head pointing +z, head underside at z = 0."""
    b = L.cyl_z(name, 0, 0, 1.5, -length, 0.01, n=24)
    L.union(b, L.cyl_z("head", 0, 0, head_r, 0, head_h, n=32))
    return b

def stl(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(BASE, "test-parts" if name in ("bench-upright", "test-arm") else "20-1-compact", name + ".stl")); o = bpy.context.selected_objects[0]
    o.name = name
    if name in PRINT_FLIP:
        o.data.transform(Matrix.Rotation(math.pi, 4, 'X'))
    return o

ITEMS = []                                   # (object, matrix in the assembly frame, explode step, material)
def add(o, m, step, material):
    o.data.materials.clear(); o.data.materials.append(MATS[material]); ITEMS.append((o, m, step, material))

def T(x, y, z): return Matrix.Translation((x, y, z))
def polar(r, deg): return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

# rear: the bench, the motor and the belt stay together; the rod is pulled out the back
add(stl("bench-upright"), Matrix(), -2, "bench")
add(motor("motor-17HS8401B"), T(MOTOR_X, 0, 0), -2, "motor")
add(gt2_pulley("pulley-20T", 20), T(MOTOR_X, 0, PULLEY_Z0) @ Matrix.Scale(-1, 4, (0, 0, 1)), -2, "pulley")
add(gt2_pulley("pulley-40T", 40), T(0, 0, PULLEY_Z0) @ Matrix.Scale(-1, 4, (0, 0, 1)), -2, "pulley")
add(belt("belt-GT2-232"), T(0, 0, PULLEY_Z0 - 7 - 1 - 3.5), -2, "belt")
for i, a in enumerate(BOLT_ANGLES):
    add(L.cyl_z(f"nut-M3-{i + 1}", 0, 0, 3.18, 0, 2.4, n=6), T(*polar(BOLT_R, a), UPRIGHT_BACK - 2.4), -3, "steel")
rod = L.cyl_z("rod-5mm", 0, 0, 2.5, ROD_FRONT - ROD_L, ROD_FRONT, n=32)
L.cut(rod, L.box("flat", 2.0, 3, -3, 3, ROD_FRONT - ROD_L - 1, ROD_FRONT - ROD_L + 20))
L.cut(rod, L.box("flat", 2.0, 3, -3, 3, ROD_FRONT - 19, ROD_FRONT + 1))
add(rod, Matrix(), -6, "steel")

# the reducer, rear to front, in the order it goes together
add(stl("housing-rear"), Matrix(), 0, "housing")
add(ring_mesh("6804-rear", 32, 20, BRG_W), T(0, 0, LIP_T + BRG_W / 2), 1, "bearing")
add(stl("carrier-rear"), Matrix(), 2, "carrier")
add(ring_mesh("625-rear", 16, 5, 5), T(0, 0, Z_IN - 2.5), 3, "bearing")
for k in range(C.N_OUT):
    add(ring_mesh(f"output-pin-{k + 1}", 4.3, 2.6, 20, n=24), T(*polar(C.OUT_PCD_R, 60 * k), Z_MID), 4, "steel")
for k in range(C.N + 1):
    add(ring_mesh(f"ring-pin-{k + 1}", 2 * C.RP, 1.8, 18, n=16), T(*polar(C.R, 360 * k / (C.N + 1)), Z_MID), 4, "steel")
for name, sign, z0, step in (("disk-a", 1, Z_DISK0, 5), ("disk-b", -1, Z_DISK0 + DISK_T + COLLAR_T, 8)):
    cx = sign * C.E
    add(stl(name), T(cx, 0, z0), step, name)
    add(ring_mesh(f"6800-{name[-1]}", 19, 10, 5), T(cx, 0, z0 + DISK_T / 2), step + 0.6, "bearing")
    for k in range(C.N_OUT):
        add(ring_mesh(f"bushing-{name[-1]}{k + 1}", 8, 6, 5, n=32), T(cx + polar(C.OUT_PCD_R, 60 * k)[0], polar(C.OUT_PCD_R, 60 * k)[1], z0 + 3.5),
            step + 0.6, "bronze")
    if name == "disk-a":
        add(stl("eccentric"), Matrix(), 7, "eccentric")
add(ring_mesh("625-front", 16, 5, 5), T(0, 0, L_HOUSING - Z_IN + 2.5), 10, "bearing")
add(stl("carrier-front"), Matrix(), 11, "carrier")
for i, a in enumerate(INSERT_ANGLES):
    add(ring_mesh(f"insert-M3-{i + 1}", 4.5, 3, 3, n=24), T(*polar(INSERT_PCD_R, a), Z_HUB_FRONT - 1.5), 11.5, "brass")
add(ring_mesh("6804-front", 32, 20, BRG_W), T(0, 0, L_HOUSING - LIP_T - BRG_W / 2), 12, "bearing")
add(stl("housing-front"), Matrix(), 13, "housing")
add(stl("test-arm"), Matrix(), 14, "bench")
for i, a in enumerate(INSERT_ANGLES):
    add(bolt(f"screw-M3x12-{i + 1}", 12), T(*polar(INSERT_PCD_R, a), ARM_TOP), 15, "steel")
for i, a in enumerate(BOLT_ANGLES):
    add(bolt(f"bolt-M3x50-{i + 1}", 50), T(*polar(BOLT_R, a), L_HOUSING), 17, "steel")

# axis on z becomes horizontal, the upright's foot down; the assembled copy sits above
VIEW = Matrix.Rotation(math.pi / 2, 4, 'X')
cols = {}
for key in ("assembled", "exploded"):
    cols[key] = bpy.data.collections.new("cycloid-poc-" + key); scene.collection.children.link(cols[key])
for o, m, step, _ in ITEMS:
    for oc in list(o.users_collection): oc.objects.unlink(o)
    o.matrix_world = VIEW @ T(0, 0, step * GAP) @ m; cols["exploded"].objects.link(o)
    a = o.copy(); a.name = o.name + ".asm"; a.matrix_world = T(0, 0, LIFT) @ VIEW @ m; cols["assembled"].objects.link(a)

lines = ["# Cycloid POC: assembly order, rear to front (explode step x %.0f mm along the axis)\n" % GAP]
for o, m, step, material in sorted(ITEMS, key=lambda it: it[2]):
    lines.append(f"- step {step:+5.1f}  {o.name}  ({material})")
txt = bpy.data.texts.new("ASSEMBLY.md"); txt.write("\n".join(lines) + "\n")

lo = min(step for _, _, step, _ in ITEMS) * GAP - 30; hi = max(step for _, _, step, _ in ITEMS) * GAP + L_HOUSING + 15
centre = VIEW @ Vector((0, 0, (lo + hi) / 2)) + Vector((0, 0, LIFT / 2))
look = Vector((-1.0, 0.35, 0.4)).normalized()
rot = (-look).to_track_quat('-Z', 'Y')
cam = bpy.data.cameras.new("cam"); cam.type = 'ORTHO'; cam.ortho_scale = (hi - lo) * 1.1; cam.clip_end = 10000
co = bpy.data.objects.new("Camera", cam); scene.collection.objects.link(co); scene.camera = co
co.matrix_world = Matrix.Translation(centre + look * 1500) @ rot.to_matrix().to_4x4()
scene.render.engine = 'BLENDER_WORKBENCH'; scene.render.resolution_x = 2400; scene.render.resolution_y = 1500
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'; scene.display.shading.show_cavity = True
scene.world = bpy.data.worlds.new("w"); scene.world.color = (1, 1, 1)
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        sp = area.spaces.active; sp.clip_start = 1.0; sp.clip_end = 100000.0
        sp.shading.type = 'SOLID'; sp.shading.color_type = 'MATERIAL'; sp.shading.show_cavity = True
        sp.region_3d.view_distance = cam.ortho_scale; sp.region_3d.view_location = centre; sp.region_3d.view_rotation = rot
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "exploded.blend"))
scene.render.filepath = os.path.join(OUT, "exploded.png"); bpy.ops.render.render(write_still=True)
print("EXPLODED", len(ITEMS), "items, row", round(lo), round(hi))
