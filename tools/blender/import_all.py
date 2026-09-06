"""Pass 1: import every STL as-is (identity transforms) plus the URDF links
scaled to mm, one collection per source folder, render orthographic views."""
import bpy, glob, os, sys, math
from mathutils import Vector

ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT  = os.path.join(ROOT, "model")
GROUPS = {
    "mainbody": "Cults3d_v5/1-mainbody",
    "axis1":    "Cults3d_v5/2-axis1",
    "axis2":    "Cults3d_v5/3-axis2",
    "axis3":    "Cults3d_v5/4-axis3",
    "axis4":    "Cults3d_v5/5-axis4",
    "axis56":   "Cults3d_v5/6-axis5-6",
    "gripper":  "4FingersGripper",
}
COLORS = {
    "mainbody": (0.95,0.80,0.10,1), "axis1": (0.20,0.60,0.95,1), "axis2": (0.90,0.30,0.20,1),
    "axis3": (0.30,0.80,0.30,1), "axis4": (0.80,0.30,0.90,1), "axis56": (0.10,0.85,0.85,1),
    "gripper": (0.95,0.55,0.10,1), "urdf": (0.6,0.6,0.6,0.25),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'; scene.unit_settings.length_unit = 'MILLIMETERS'; scene.unit_settings.scale_length = 0.001

def mat(name, rgba):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    if rgba[3] < 1:
        bsdf.inputs["Alpha"].default_value = rgba[3]; m.blend_method = 'BLEND'
    return m

def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c

def import_stl(path, c, m, scale=1.0):
    bpy.ops.wm.stl_import(filepath=path, global_scale=scale)
    o = bpy.context.selected_objects[0]
    for oc in list(o.users_collection): oc.objects.unlink(o)
    c.objects.link(o); o.data.materials.append(m)
    return o

# URDF links (meters -> mm)
cu = coll("urdf"); mu = mat("urdf", COLORS["urdf"])
for p in sorted(glob.glob(os.path.join(ROOT, "URDF/*.stl"))):
    o = import_stl(p, cu, mu, scale=1000.0); o.name = "urdf_" + os.path.basename(p)[:-4]

for g, rel in GROUPS.items():
    c = coll(g); m = mat(g, COLORS[g])
    for p in sorted(glob.glob(os.path.join(ROOT, rel, "*.stl"))):
        o = import_stl(p, c, m); o.name = g + "/" + os.path.basename(p)[:-4]

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "cybot-pass1.blend"))

# Orthographic renders: front(-Y), side(+X), top(+Z)
def render(name, loc, rot, ortho):
    cam = bpy.data.cameras.new(name); cam.type = 'ORTHO'; cam.ortho_scale = ortho; cam.clip_end = 5000
    co = bpy.data.objects.new(name, cam); scene.collection.objects.link(co)
    co.location = loc; co.rotation_euler = rot; scene.camera = co
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_xray = True; scene.display.shading.xray_alpha = 0.5
    scene.render.resolution_x = 1400; scene.render.resolution_y = 1000
    scene.render.filepath = os.path.join(OUT, f"pass1-{name}.png"); bpy.ops.render.render(write_still=True)

render("front", (0,-1500,250), (math.radians(90),0,0), 900)
render("side",  (1500,0,250), (math.radians(90),0,math.radians(90)), 900)
render("top",   (0,0,1500), (0,0,0), 900)
print("PASS1 DONE")
