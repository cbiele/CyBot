"""Assemble the phase 1 finger at a sweep of knuckle angles and measure interference volume,
then render. Positive flexion curls toward the palm (-y)."""
import bpy, bmesh, os, sys, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
bpy.ops.wm.read_factory_settings(use_empty=True)
def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, name + ".stl")); o = bpy.context.selected_objects[0]; o.name = name; return o
def volume(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); v = bm.calc_volume(); bm.free(); return v
def interference(a, b):
    """Volume of a AND b, using a copy of a."""
    c = a.copy(); c.data = a.data.copy(); bpy.context.scene.collection.objects.link(c)
    m = c.modifiers.new("i", "BOOLEAN"); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = b
    bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier=m.name)
    v = volume(c) if len(c.data.polygons) else 0.0
    bpy.data.objects.remove(c); return v
prox, dist, fix = load("finger-proximal"), load("finger-distal"), load("finger-fixture")
PROX_LEN = 40.0
def place(o, xa, deg):
    o.matrix_world = Matrix.Translation((xa, 0, 0)) @ Matrix.Rotation(math.radians(-deg), 4, 'Z')
    bpy.context.view_layer.update()
res = {}
for deg in (-6, -3, 0, 20, 45, 70, 80, 85, 87, 90, 95):
    place(dist, PROX_LEN, deg); place(prox, 0, 0)
    res[f"distal@{deg}"] = round(interference(dist, prox), 2)
for deg in (-3, 0, 45, 85, 90, 95):
    place(prox, 0, deg); place(dist, PROX_LEN, 0)   # distal rides along; only fixture/prox checked
    res[f"proximal@{deg}"] = round(interference(prox, fix), 2)
    if 0 < res[f"proximal@{deg}"] < 5:
        c = prox.copy(); c.data = prox.data.copy(); bpy.context.scene.collection.objects.link(c)
        m = c.modifiers.new("i", "BOOLEAN"); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = fix
        bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier=m.name)
        pts = [c.matrix_world @ v.co for v in c.data.vertices]
        if pts: res[f"proximal@{deg}_bbox"] = [[round(min(p[i] for p in pts),2), round(max(p[i] for p in pts),2)] for i in range(3)]
        bpy.data.objects.remove(c)
free = [k for k in res if k.endswith(("@-3", "@0", "@20", "@45", "@70", "@80", "@85", "@87"))]
assert all(res[k] == 0.0 for k in free), {k: res[k] for k in free if res[k]}
assert res["distal@90"] > 0 and res["distal@-6"] > 0 and res["proximal@90"] > 0
print("CHECK", json.dumps(res))
# render: straight and curled
scene = bpy.context.scene; scene.render.engine = 'BLENDER_WORKBENCH'; sh = scene.display.shading
sh.light = 'STUDIO'; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = 'OBJECT'
prox.color = (0.2, 0.6, 0.95, 1); dist.color = (0.95, 0.5, 0.1, 1); fix.color = (0.6, 0.6, 0.6, 1)
scene.render.resolution_x = 1600; scene.render.resolution_y = 900
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = 130; cam.clip_end = 1000
co = bpy.data.objects.new("c", cam); scene.collection.objects.link(co); scene.camera = co
for tag, pd, dd in (("straight", 0, 0), ("curled", 85, 85)):
    place(prox, 0, pd)
    # distal axis is at the proximal tip after the proximal rotates
    tip = Vector((PROX_LEN, 0, 0)); tipw = prox.matrix_world @ tip
    dist.matrix_world = Matrix.Translation(tipw) @ Matrix.Rotation(math.radians(-(pd + dd)), 4, 'Z')
    bpy.context.view_layer.update()
    co.rotation_euler = (math.radians(60), 0, math.radians(30)); bpy.context.view_layer.update()
    d = co.matrix_world.to_quaternion() @ Vector((0, 0, -1)); co.location = Vector((25, -10, 0)) - d * 400
    scene.render.filepath = os.path.join(OUT, f"finger-{tag}-iso.png"); bpy.ops.render.render(write_still=True)
    co.rotation_euler = (math.radians(90), 0, 0); co.location = (25, -10, 400) if False else (25, -400, 0)
    co.rotation_euler = (math.radians(90), 0, 0); bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUT, f"finger-{tag}-side.png"); bpy.ops.render.render(write_still=True)
print("CHECK DONE")
