"""Save a viewer-friendly copy: URDF ghost + parked parts hidden, per-group colours
in the viewport, camera objects removed, clip range and viewport framed on the arm."""
import bpy, os
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
scene=bpy.context.scene
COLORS={"mainbody":(0.95,0.80,0.10,1),"axis1":(0.20,0.60,0.95,1),"axis2":(0.90,0.30,0.20,1),
 "axis3":(0.30,0.80,0.30,1),"axis4":(0.80,0.30,0.90,1),"axis56":(0.10,0.85,0.85,1),
 "gripper":(0.95,0.55,0.10,1),"urdf":(0.55,0.55,0.55,1)}
for m in bpy.data.materials:
    if m.name in COLORS: m.diffuse_color=COLORS[m.name]
for o in [o for o in bpy.data.objects if o.type=='CAMERA']: bpy.data.objects.remove(o)
for cname in ("urdf","alternates","unplaced"):
    c=bpy.data.collections.get(cname)
    if c: c.hide_viewport=True; c.hide_render=True
for o in bpy.data.objects:
    if o.type=='MESH': o.hide_set(False); o.hide_viewport=False; o.hide_render=False
# viewport: solid shading with material colours, big clip range, framed on everything visible
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        sp=area.spaces.active; sp.clip_start=1.0; sp.clip_end=100000.0
        sp.shading.type='SOLID'; sp.shading.color_type='MATERIAL'; sp.shading.show_cavity=True
        r3d=sp.region_3d; r3d.view_distance=1400; r3d.view_location=(150,0,320)
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=0.001; scene.unit_settings.length_unit='MILLIMETERS'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"cybot-assembly.blend"))
print("VIEWABLE DONE", os.path.join(OUT,"cybot-assembly.blend"))
