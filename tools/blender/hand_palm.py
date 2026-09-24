"""Phase 2 palm front: the plate both pair fingers hinge on, a bench foot that bolts to its rear
face on the rear shell's bolt pattern, and a whiffletree bar for a hand-pulled test. Palm frame =
the finger frame of a finger on the centre line: x along the fingers, +y dorsal, z across the hand;
finger axes at x=0, y=0, z=+-PITCH/2.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_palm.py"""
import bpy, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
from mathutils import Vector
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
_params = json.load(open(os.path.join(OUT, "params.json"))) if os.path.exists(os.path.join(OUT, "params.json")) else {}
CHEEK_BORE = _params.get("cheek_bore", L.CHEEK_BORE)

PITCH = 45.0                                    # finger axis to finger axis
FINGERS = (-PITCH / 2, PITCH / 2)
PLATE_T, PLATE_H = 12.0, 50.0
PLATE_W = PITCH + L.W                           # 68: outer cheeks flush with the ends
X_WEB, X_BACK = -L.FORK_LEN, -L.FORK_LEN - PLATE_T
Y0, Y1, Z0, Z1 = -PLATE_H / 2, PLATE_H / 2, -PLATE_W / 2, PLATE_W / 2
TENDON_Y = L.TENDON_Y - 1.0                     # as the fixture: 1 mm below the finger's channel line
TENDON_D = 2.5
PAD_D, PAD_DEPTH, PAD_Y = 19.0, 0.6, -2.0       # FSR 402 body 18.3
TAIL_W, TAIL_H, TAIL_Y1 = 7.0, 1.2, -11.6       # its tail, through to the rear face
SHELL_BOLTS = [(y, z) for y in (-20.0, 20.0) for z in (-28.0, 28.0)]
BOLT_D, BOLT_CB_D, BOLT_CB_DEPTH = 3.2, 6.0, 3.0
CRADLE_PILOTS = [(y, z) for y in (-12.0, -22.0) for z in (-20.0, 20.0)]
PILOT_D, PILOT_DEPTH = 2.8, 8.0
FOOT_T, SOLE_X0, SOLE_Y0, CLAMP_D = 10.0, -30.0, -33.0, 4.4
BAR_L, BAR_H, BAR_T = 50.0, 8.0, 4.0

def pilot(target, x_face, y, z, direction, d=PILOT_D, depth=PILOT_DEPTH):
    """Thread-forming M3 pilot into the face at x_face; direction is the way it goes into the part."""
    L.cut(target, L.cyl_between("pilot", (x_face - direction * 0.5, y, z), (x_face + direction * depth, y, z), d / 2))

# ---- front plate
plate = L.box("palm-front", X_BACK, X_WEB, Y0, Y1, Z0, Z1)
for zc in FINGERS:
    L.fork(plate, 0.0, zc=zc)
    L.bore_cheeks(plate, 0.0, CHEEK_BORE, zc=zc)
    L.cut(plate, L.cyl_between("tendon", (X_WEB + 1, TENDON_Y, zc), (X_BACK - 1, TENDON_Y, zc), TENDON_D / 2))
    L.cut(plate, L.cyl_between("wire", (X_WEB + 1, 0, zc), (X_BACK - 1, 0, zc), L.WIRE_D / 2))
    L.cut(plate, L.cyl_between("tendon_flare", (X_WEB + 0.05, TENDON_Y, zc), (X_WEB - 1.5, TENDON_Y, zc), 2.25, r_end=TENDON_D / 2))
    L.cut(plate, L.cyl_between("wire_flare", (X_WEB + 0.05, 0, zc), (X_WEB - 1.5, 0, zc), 1.4, r_end=L.WIRE_D / 2))
L.cut(plate, L.cyl_between("pad_pocket", (X_WEB + 1, PAD_Y, 0), (X_WEB - PAD_DEPTH, PAD_Y, 0), PAD_D / 2, n=64))
L.cut(plate, L.box("pad_tail", X_BACK - 1, X_WEB + 1, TAIL_Y1 - TAIL_H, TAIL_Y1, -TAIL_W / 2, TAIL_W / 2))
for y, z in SHELL_BOLTS:
    L.cut(plate, L.cyl_between("shell_bolt", (X_WEB + 1, y, z), (X_BACK - 1, y, z), BOLT_D / 2))
    L.cut(plate, L.cyl_between("shell_cb", (X_WEB + 1, y, z), (X_WEB - BOLT_CB_DEPTH, y, z), BOLT_CB_D / 2))
for y, z in CRADLE_PILOTS:
    pilot(plate, X_WEB, y, z, -1)
L.finish(plate)

# ---- bench foot: a block on the plate's rear face, bolted through the shell holes, with a sole
# under the plate that clamps to the bench. The sole stops at the web line so the curled fingers
# never sweep into it.
foot = L.box("palm-bench-foot", X_BACK - FOOT_T, X_BACK - 0.01, Y0, Y1, Z0, Z1)
L.union(foot, L.box("sole", SOLE_X0, X_WEB, SOLE_Y0, Y0 + 0.01, Z0, Z1))
for y, z in SHELL_BOLTS:
    pilot(foot, X_BACK, y, z, -1)
for zc in FINGERS:
    L.cut(foot, L.cyl_between("tendon_pass", (X_BACK + 1, TENDON_Y, zc), (X_BACK - FOOT_T - 1, TENDON_Y, zc), 2.0))
    L.cut(foot, L.cyl_between("wire_pass", (X_BACK + 1, 0, zc), (X_BACK - FOOT_T - 1, 0, zc), 1.5))
for x in (SOLE_X0 + 5, X_WEB - 5):
    for z in (-25.0, 25.0):
        L.cut(foot, L.cyl_between("clamp", (x, SOLE_Y0 - 1, z), (x, Y0 + 1, z), CLAMP_D / 2))
L.finish(foot)

# ---- whiffletree bar, modelled behind the foot where it floats in use
bar = L.box("palm-whiffletree-bar", X_BACK - FOOT_T - 20 - BAR_T, X_BACK - FOOT_T - 20, TENDON_Y - BAR_H / 2, TENDON_Y + BAR_H / 2, -BAR_L / 2, BAR_L / 2)
for z, d in ((-PITCH / 2, 1.5), (PITCH / 2, 1.5), (0.0, 2.0)):
    L.cut(bar, L.cyl_between("hole", (X_BACK - FOOT_T - 20 + 1, TENDON_Y, z), (X_BACK - FOOT_T - 20 - BAR_T - 1, TENDON_Y, z), d / 2))
L.finish(bar)

# ---- checks and export
report = {}
for o in (plate, foot, bar):
    report[o.name] = L.stats(o); L.export(o, os.path.join(OUT, o.name + ".stl"))
    assert report[o.name]["non_manifold"] == 0, o.name
report["cheek_bores"] = [L.hole_diameter(plate, 0, 0, zc + L.W / 2 - 2.5) for zc in FINGERS]
report["tendon_lines"] = [L.first_hit_x(plate, TENDON_Y, -40.0, z=zc) for zc in FINGERS]
report["wire_lines"] = [L.first_hit_x(plate, 0.0, -40.0, z=zc) for zc in FINGERS]
report["foot_tendon_lines"] = [L.first_hit_x(foot, TENDON_Y, -60.0, z=zc) for zc in FINGERS]
report["foot_wire_lines"] = [L.first_hit_x(foot, 0.0, -60.0, z=zc) for zc in FINGERS]
report["plate_dims"] = report["palm-front"]["dims"]
print("PALM", json.dumps(report))
for d in report["cheek_bores"]: assert abs(d - CHEEK_BORE) < 0.02, d
for key in ("tendon_lines", "wire_lines", "foot_tendon_lines", "foot_wire_lines"):
    assert report[key] == [None, None], (key, report[key])
assert report["plate_dims"] == [PLATE_T + L.FORK_LEN + L.R, PLATE_H, PLATE_W], report["plate_dims"]   # rounded cheek ends reach x=+R

# ---- assembly render: plate, foot, bar and both fingers straight
scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; sh = scene.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = 'OBJECT'
scene.render.resolution_x = 1600; scene.render.resolution_y = 1000
plate.color = (0.85, 0.85, 0.85, 1); foot.color = (0.75, 0.75, 0.7, 1); bar.color = (0.9, 0.6, 0.2, 1)
for zc in FINGERS:
    for name, x in (("finger-proximal", 0.0), ("finger-distal", 40.0)):
        path = os.path.join(OUT, name + ".stl")
        if not os.path.exists(path): continue
        bpy.ops.wm.stl_import(filepath=path); f = bpy.context.selected_objects[0]
        f.location = (x, 0, zc); f.color = (0.55, 0.7, 0.9, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = 150; cam.clip_end = 10000
co = bpy.data.objects.new("c", cam); scene.collection.objects.link(co); scene.camera = co
co.rotation_euler = (math.radians(60), 0, math.radians(35)); bpy.context.view_layer.update()
d = co.matrix_world.to_quaternion() @ Vector((0, 0, -1)); co.location = Vector((10, -5, 0)) - d * 600
scene.render.filepath = os.path.join(OUT, "palm-iso.png"); bpy.ops.render.render(write_still=True)
print("PALM DONE")
