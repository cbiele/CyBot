"""Ray-cast free length behind each motor mounting face in the assembled model (pass 3).
Motor footprint sampled at 9 points (centre + 8 around the body radius)."""
import bpy, math, os
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
scene=bpy.context.scene
for cname in ("urdf","alternates","unplaced"):
    for o in bpy.data.collections[cname].objects: o.hide_set(True); o.hide_viewport=True
dg=bpy.context.evaluated_depsgraph_get()
# (label, mounting-face centre, unit direction the motor BODY extends, body half-width)
M=[("axis1 NEMA17 (stepperHolder top, body up)",      Vector((-139.0,0,72.0)),  Vector((0,0,1)),  21.2),
   ("axis1 NEMA17 alt (body down into holder)",         Vector((-139.0,0,66.0)),  Vector((0,0,-1)), 21.2),
   ("axis2 NEMA23 (mainBody1 pocket floor, body +y)",   Vector((26.6,-33.0,309.7)), Vector((0,1,0)), 28.2),
   ("axis3 NEMA23 (mainBody1 pocket floor, body +y)",   Vector((-24.2,-33.0,356.0)), Vector((0,1,0)), 28.2),
   ("axis2 encoder E6B2 (mainBody2, body -y)",          Vector((40.7,34.5,361.6)), Vector((0,-1,0)), 20.0),
   ("axis3 encoder E6B2 (mainBody2, body -y)",          Vector((-41.2,34.5,305.0)), Vector((0,-1,0)), 20.0),
   ("axis4 NEMA17 (housingNema plate, body +x)",        Vector((120.7,1.0,647.0)), Vector((1,0,0)), 21.2),
   ("axis4 NEMA17 alt (body -x)",                       Vector((116.7,1.0,647.0)), Vector((-1,0,0)), 21.2),
   ("axis5 NEMA17 (wrist holder -y face, body -y)",     Vector((157.5,-90.0,540.8)), Vector((0,-1,0)), 21.2),
   ("axis6 NEMA17 (wrist holder +y face, body +y)",     Vector((158.0,90.0,571.0)), Vector((0,1,0)), 21.2),
   ("axis5/6 alt: holder -y face upper slots, body -y", Vector((158.3,-90.0,571.8)), Vector((0,-1,0)), 21.2),
   ("axis5/6 alt: holder +y face lower slots, body +y", Vector((158.0,90.0,539.8)), Vector((0,1,0)), 21.2),
   ("gripper NEMA17 (mainHolder -x face, body -x)",     Vector((355.5,13.8,554.0)), Vector((-1,0,0)), 21.2),
   ("gripper NEMA17 alt (+x face, body +x)",            Vector((401.5,13.7,554.0)), Vector((1,0,0)), 21.2)]
def cast(p,d,maxd=300):
    hit,loc,n,i,obj,mat=scene.ray_cast(dg,p+d*3.0,d,distance=maxd)
    return ((loc-p).length,obj.name.split("/")[-1]) if hit else (None,None)
print("FREE LENGTH BEHIND MOUNTING FACE (mm)  [ICP placement error ~5 mm; local-frame parts exact]")
for label,c,d,hw in M:
    t1=d.cross(Vector((0,0,1))) if abs(d.z)<0.9 else d.cross(Vector((1,0,0))); t1.normalize(); t2=d.cross(t1)
    res=[cast(c,d)]
    for k in range(8):
        a=k*math.pi/4; res.append(cast(c+(t1*math.cos(a)+t2*math.sin(a))*hw*0.85,d))
    hits=[r for r in res if r[0] is not None]
    if hits:
        mn=min(hits,key=lambda r:r[0]); print(f"  {label:52s} min free {mn[0]:6.1f} mm (hits {mn[1]}), {len(hits)}/9 rays blocked")
    else: print(f"  {label:52s} open (> 300 mm on all 9 rays)")
print("FREE DONE")
