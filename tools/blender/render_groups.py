"""Render the pass-1 blend: whole model plus each group alone over the URDF ghost."""
import bpy, os, math, sys
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
blend = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else os.path.join(OUT,"cybot-pass1.blend")
tag = sys.argv[sys.argv.index("--")+2] if "--" in sys.argv and len(sys.argv)>sys.argv.index("--")+2 else "pass1"
bpy.ops.wm.open_mainfile(filepath=blend)
scene=bpy.context.scene
COLORS={"mainbody":(0.95,0.80,0.10,1),"axis1":(0.20,0.60,0.95,1),"axis2":(0.90,0.30,0.20,1),
 "axis3":(0.30,0.80,0.30,1),"axis4":(0.80,0.30,0.90,1),"axis56":(0.10,0.85,0.85,1),
 "gripper":(0.95,0.55,0.10,1),"urdf":(0.55,0.55,0.55,1)}
for m in bpy.data.materials:
    if m.name in COLORS: m.diffuse_color=COLORS[m.name]
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'; sh.show_xray=False
sh.show_cavity=True; sh.show_object_outline=True
scene.render.resolution_x=1600; scene.render.resolution_y=1100
scene.render.film_transparent=False
w=scene.world or bpy.data.worlds.new("W"); scene.world=w; w.color=(0.12,0.12,0.12)
cams={}
def cam(name,loc,rot,ortho):
    c=bpy.data.cameras.new(name); c.type='ORTHO'; c.ortho_scale=ortho; c.clip_end=6000
    o=bpy.data.objects.new(name,c); scene.collection.objects.link(o); o.location=loc; o.rotation_euler=rot; cams[name]=o
cam("front",(0,-2500,300),(math.radians(90),0,0),1000)
cam("side",(2500,0,300),(math.radians(90),0,math.radians(90)),1000)
cam("iso",(1600,-1600,1300),(math.radians(55),0,math.radians(45)),1100)
groups=[c.name for c in scene.collection.children if c.name!="urdf"]
def vis(active):
    for c in scene.collection.children:
        hide = not (c.name=="urdf" or active is None or c.name==active)
        c.hide_render=hide
        for o in c.objects: o.hide_render=hide
def shoot(label,view):
    scene.camera=cams[view]; scene.render.filepath=os.path.join(OUT,f"{tag}-{label}-{view}.png"); bpy.ops.render.render(write_still=True)
vis(None)
for v in ("front","side","iso"): shoot("all",v)
for g in groups:
    vis(g); shoot(g,"front"); shoot(g,"side")
print("RENDER DONE")
