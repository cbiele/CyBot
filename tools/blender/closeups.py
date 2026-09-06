import bpy, os, math, sys
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'; sh=scene.display.shading; sh.light='STUDIO'; sh.color_type='MATERIAL'; sh.show_cavity=True; sh.show_object_outline=True
scene.render.resolution_x=1400; scene.render.resolution_y=1400
w=scene.world or bpy.data.worlds.new("W"); scene.world=w; w.color=(0.12,0.12,0.12)
def only(names):
    for o in bpy.data.objects:
        if o.type!='MESH': continue
        o.hide_render = o.name.split("/")[-1] not in names
def shot(label, names, cam_loc, cam_rot, ortho):
    only(names)
    c=bpy.data.cameras.new(label); c.type='ORTHO'; c.ortho_scale=ortho; c.clip_end=5000
    co=bpy.data.objects.new(label,c); scene.collection.objects.link(co); co.location=cam_loc; co.rotation_euler=cam_rot; scene.camera=co
    scene.render.filepath=os.path.join(OUT,f"closeup-{label}.png"); bpy.ops.render.render(write_still=True)
# plate 2 seen from outside (+Y looking -Y) and plate 1 from outside (-Y looking +Y), with the joint groups for context
shot("plate2-outside", {"mainBody2","axis2-GT2-stepper","axis2-GT2-encoder","axis3-GT2-stepper","axis3-GT2-encoder","axis2-holder2"}, (0,1500,322), (math.radians(90),0,math.radians(180)), 420)
shot("plate1-outside", {"mainBody1","axis2-GT2-stepper","axis2-GT2-encoder","axis3-GT2-stepper","axis3-GT2-encoder","axis2-holder1"}, (0,-1500,322), (math.radians(90),0,0), 420)
shot("body-side", {"mainBody1","mainBody2","axis2-holder1","axis2-holder2","axis2-housing1","axis2-housing2","axis3-holder1","axis3-holder2","axis2-GT2-stepper","axis2-GT2-encoder","axis3-GT2-stepper","axis3-GT2-encoder"}, (1500,0,322), (math.radians(90),0,math.radians(90)), 420)
shot("base-iso", {"axis1-stepperHolder","axis1-encoderHolder","axis1-baseHolder","axis-1-rotatingBase1","axis-1-rotatingBase2","axis-1-rotatingBase3"}, (600,-600,500), (math.radians(55),0,math.radians(45)), 380)
shot("stepperHolder", {"axis1-stepperHolder"}, (-135,-400,57), (math.radians(90),0,0), 120)
shot("wrist-iso", {"axis5-holder","axis5-holder2","axis5-axis6holder1","axis5-axis6holder2","axis4_housingNema","axis4_housing","axis4_Tube","axis4_axis5_holder","axis5_Housing2Attach1","axis5_Housing2Attach2"}, (700,-700,1100), (math.radians(55),0,math.radians(45)), 420)
print("CLOSEUPS DONE")
