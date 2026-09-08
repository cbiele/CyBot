"""Rebuild model/cybot-master.blend from the raw STLs and model/placements.json.
placements.json: {object name: {collection, file, matrix_world, hide}}; instances repeat a file.
Run: Blender -b -P tools/blender/apply_placements.py
placements.json is the authority for every hand-seated part (joint stacks, pulleys,
axis-4 and axis-5 gearboxes, roll stack, gripper); regenerate it from a live session
by dumping matrix_world per object."""
import bpy, glob, os, json
from mathutils import Matrix
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
GROUPS={"mainbody":"Cults3d_v5/1-mainbody","axis1":"Cults3d_v5/2-axis1","axis2":"Cults3d_v5/3-axis2","axis3":"Cults3d_v5/4-axis3",
        "axis4":"Cults3d_v5/5-axis4","axis56":"Cults3d_v5/6-axis5-6","gripper":"4FingersGripper"}
COLORS={"mainbody":(0.95,0.80,0.10,1),"axis1":(0.20,0.60,0.95,1),"axis2":(0.90,0.30,0.20,1),"axis3":(0.30,0.80,0.30,1),
        "axis4":(0.80,0.30,0.90,1),"axis56":(0.10,0.85,0.85,1),"gripper":(0.95,0.55,0.10,1),"urdf":(0.55,0.55,0.55,1)}
P=json.load(open(os.path.join(OUT,"placements.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=0.001; scene.unit_settings.length_unit='MILLIMETERS'
def mat(name):
    m=bpy.data.materials.new(name); m.diffuse_color=COLORS[name]; return m
cols={}
def coll(name):
    if name not in cols:
        c=bpy.data.collections.new(name); scene.collection.children.link(c); cols[name]=c
    return cols[name]
def imp(path,cname,m,scale=1.0,name=None):
    bpy.ops.wm.stl_import(filepath=path,global_scale=scale); o=bpy.context.selected_objects[0]
    for oc in list(o.users_collection): oc.objects.unlink(o)
    coll(cname).objects.link(o); o.data.materials.append(m); o.name=name or o.name; return o
mu=mat("urdf")
for p in sorted(glob.glob(os.path.join(ROOT,"URDF/*.stl"))): imp(p,"urdf",mu,1000.0,"urdf_"+os.path.basename(p)[:-4])
mats={g:mat(g) for g in GROUPS}
# one entry per placed object; instances of the same STL share a "file" and get suffixed names
for nm,entry in P.items():
    g=nm.split("/")[0]
    o=imp(os.path.join(ROOT,entry["file"]),entry["collection"],mats[g],1.0,nm)
    o.matrix_world=Matrix(entry["matrix_world"])
for cname,entry in {v["collection"]:v for v in P.values()}.items():
    if entry["hide"]: coll(cname).hide_viewport=True; coll(cname).hide_render=True
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        sp=area.spaces.active; sp.clip_start=1.0; sp.clip_end=100000.0; sp.shading.type='SOLID'; sp.shading.color_type='MATERIAL'; sp.shading.show_cavity=True
        sp.region_3d.view_distance=1400; sp.region_3d.view_location=(150,0,320)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"cybot-master.blend")); print("REBUILT", len(P), "placements")
