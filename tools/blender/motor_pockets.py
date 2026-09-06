"""Find NEMA pilot holes (38.1 mm = NEMA23, 22 mm = NEMA17) on planar faces of the
printed parts in the assembled pass-3 model and ray-cast the free depth behind
each mounting face (motor side) through ALL parts."""
import bpy, bmesh, math, os
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
scene=bpy.context.scene
# hide reference/alternates from ray casts
for cname in ("urdf","alternates","unplaced"):
    for o in bpy.data.collections[cname].objects: o.hide_viewport=True; o.hide_set(True)
dg=bpy.context.evaluated_depsgraph_get()
PILOTS={"NEMA23":(38.1,1.5),"NEMA17":(22.0,1.0)}
CANDS=["axis1-stepperHolder","mainBody1","mainBody2","axis4_housingNema","axis5-holder","axis5-holder2","axis5-axis6holder1","axis5-axis6holder2","axis4_axis5_holder","mainHolder","OPH_To_Gripper","T8_Srcew_Holder"]
def loops_on_planes(o):
    bm=bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    M=o.matrix_world; res=[]
    # group faces by (normal, offset) plane
    planes={}
    for f in bm.faces:
        n=(M.to_3x3()@f.normal).normalized(); c=M@f.calc_center_median()
        key=(round(n.x,2),round(n.y,2),round(n.z,2),round(n.dot(c),0))
        planes.setdefault(key,[]).append(f)
    for key,faces in planes.items():
        if len(faces)<20: continue
        fs=set(faces); bedges=[e for f in faces for e in f.edges if sum(1 for ff in e.link_faces if ff in fs)==1]
        # connected components over boundary edges
        adj={}
        for e in bedges:
            a,b=e.verts; adj.setdefault(a.index,set()).add(b.index); adj.setdefault(b.index,set()).add(a.index)
        seen=set()
        for s in adj:
            if s in seen: continue
            comp=[]; st=[s]
            while st:
                v=st.pop()
                if v in seen: continue
                seen.add(v); comp.append(v); st.extend(adj[v]-seen)
            pts=[M@bm.verts[i].co for i in comp]
            n=Vector(key[:3]); ctr=sum(pts,Vector())/len(pts)
            r=[ (p-ctr).length for p in pts]
            rmean=sum(r)/len(r); rdev=max(abs(x-rmean) for x in r)
            if len(pts)>=16 and rdev<0.6: res.append((n,ctr,2*rmean,len(pts)))
    bm.free(); return res
def free_depth(origin,direction,maxd=400):
    hit,loc,nrm,idx,obj,mat=scene.ray_cast(dg,origin+direction*0.5,direction,distance=maxd)
    return ((loc-origin).length,obj.name) if hit else (None,None)
print("MOTOR PILOT HOLES (assembled model, pass 3)")
for o in bpy.data.objects:
    if o.hide_get() or o.type!='MESH': continue
    base=o.name.split("/")[-1]
    if base not in CANDS: continue
    for n,ctr,dia,npts in loops_on_planes(o):
        for nema,(d,tol) in PILOTS.items():
            if abs(dia-d)<=tol:
                # free depth on both sides of the plane at the hole centre and at 4 points on the motor body corner radius
                R={"NEMA23":33.0,"NEMA17":25.0}[nema]  # half-diagonal-ish of body
                for sign,label in ((1,"+n"),(-1,"-n")):
                    dirv=n*sign; ds=[]
                    for k in range(8):
                        a=k*math.pi/4; off=Vector((math.cos(a),math.sin(a),0))
                        # build a basis perpendicular to n
                        t1=n.cross(Vector((0,0,1))) if abs(n.z)<0.9 else n.cross(Vector((1,0,0))); t1.normalize(); t2=n.cross(t1)
                        p=ctr+ (t1*math.cos(a)+t2*math.sin(a))*R*0.6
                        dd,who=free_depth(p,dirv); ds.append((dd if dd else 9999,who))
                    dc,whoc=free_depth(ctr,dirv)
                    mn=min(ds,key=lambda x:x[0])
                    print(f"  {base:22s} {nema} pilot {dia:5.1f} mm  centre=({ctr.x:7.1f},{ctr.y:7.1f},{ctr.z:7.1f}) normal=({n.x:5.2f},{n.y:5.2f},{n.z:5.2f}) side {label}: free depth min {mn[0]:.1f} mm (blocked by {mn[1]}), at centre {dc if dc else 'open'} {whoc or ''}")
print("POCKETS DONE")
