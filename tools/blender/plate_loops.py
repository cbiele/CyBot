"""List every boundary loop (holes/slots) on the large planar faces of selected parts."""
import bpy, bmesh, os
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
PARTS=["mainBody1","mainBody2","axis1-stepperHolder","axis4_housingNema","axis5-holder","axis5-holder2","axis2-holder1","axis4_axis5_holder"]
for o in bpy.data.objects:
    base=o.name.split("/")[-1]
    if base not in PARTS or o.type!='MESH': continue
    bm=bmesh.new(); bm.from_mesh(o.data)
    for s in (bm.verts,bm.edges,bm.faces): s.ensure_lookup_table()
    M=o.matrix_world; R=M.to_3x3(); planes={}
    for f in bm.faces:
        n=(R@f.normal).normalized(); c=M@f.calc_center_median()
        key=(round(n.x,1),round(n.y,1),round(n.z,1),round(n.dot(c)/2)*2)
        planes.setdefault(key,[]).append(f)
    print(f"## {base}")
    for key,faces in sorted(planes.items(),key=lambda kv:-len(kv[1]))[:6]:
        fs=set(faces); area=sum(f.calc_area() for f in faces)
        if area<2000: continue
        bedges=[e for f in faces for e in f.edges if sum(1 for ff in e.link_faces if ff in fs)==1]
        adj={}
        for e in bedges:
            a,b=e.verts; adj.setdefault(a.index,set()).add(b.index); adj.setdefault(b.index,set()).add(a.index)
        seen=set(); loops=[]
        for s in adj:
            if s in seen: continue
            comp=[]; st=[s]
            while st:
                v=st.pop()
                if v in seen: continue
                seen.add(v); comp.append(v); st.extend(adj[v]-seen)
            pts=[M@bm.verts[i].co for i in comp]
            mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
            d=mx-mn; dims=sorted([d.x,d.y,d.z],reverse=True)
            if 12<=dims[0]<=80: loops.append(((mn+mx)/2,dims,len(pts)))
        print(f"  plane n=({key[0]},{key[1]},{key[2]}) d={key[3]} area={area/100:.0f} cm2  loops 12-80 mm: {len(loops)}")
        for c,dims,npts in sorted(loops,key=lambda l:-l[1][0]):
            print(f"     centre=({c.x:7.1f},{c.y:7.1f},{c.z:7.1f})  size {dims[0]:5.1f} x {dims[1]:5.1f}  pts={npts}")
    bm.free()
print("LOOPS DONE")
