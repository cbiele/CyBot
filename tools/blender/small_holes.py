"""Small-hole patterns (2.5-7 mm) near given centres on mainBody2 outer face and stepperHolder faces."""
import bpy, bmesh, os
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
def loops(o, minsz, maxsz):
    bm=bmesh.new(); bm.from_mesh(o.data)
    for s in (bm.verts,bm.edges,bm.faces): s.ensure_lookup_table()
    M=o.matrix_world; R=M.to_3x3(); planes={}
    for f in bm.faces:
        n=(R@f.normal).normalized(); c=M@f.calc_center_median()
        key=(round(n.x,1),round(n.y,1),round(n.z,1),round(n.dot(c)/2)*2); planes.setdefault(key,[]).append(f)
    out=[]
    for key,faces in planes.items():
        fs=set(faces)
        if sum(f.calc_area() for f in faces)<500: continue
        bedges=[e for f in faces for e in f.edges if sum(1 for ff in e.link_faces if ff in fs)==1]
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
            mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
            d=sorted([(mx-mn).x,(mx-mn).y,(mx-mn).z],reverse=True)
            if minsz<=d[0]<=maxsz: out.append((key,(mn+mx)/2,d[0]))
    bm.free(); return out
def near(o,centres,rad,minsz=2.5,maxsz=7):
    for key,c,d in loops(o,minsz,maxsz):
        for cc in centres:
            if (c-cc).length<rad: print(f"   plane n=({key[0]},{key[1]},{key[2]}) d={key[3]}  hole {d:4.1f} mm at ({c.x:6.1f},{c.y:6.1f},{c.z:6.1f})  offset from {tuple(round(v,1) for v in cc)}: ({c.x-cc.x:+6.1f},{c.z-cc.z:+6.1f})")
objs={o.name.split("/")[-1]:o for o in bpy.data.objects if o.type=='MESH'}
print("## mainBody2 42mm pockets: small holes around centres")
near(objs["mainBody2"],[Vector((40.6,44,361.6)),Vector((-41.2,44,305.0))],28)
print("## mainBody1 69mm pockets: small holes around centres")
near(objs["mainBody1"],[Vector((26.6,-44,309.7)),Vector((-24.2,-44,356.0))],40)
print("## axis1-stepperHolder: all loops 2.5-45 mm on any plane")
for key,c,d in loops(objs["axis1-stepperHolder"],2.5,45): print(f"   plane n=({key[0]},{key[1]},{key[2]}) d={key[3]}  loop {d:4.1f} mm at ({c.x:6.1f},{c.y:6.1f},{c.z:6.1f})")
print("## axis1-encoderHolder: all loops 2.5-45 mm")
for key,c,d in loops(objs["axis1-encoderHolder"],2.5,45): print(f"   plane n=({key[0]},{key[1]},{key[2]}) d={key[3]}  loop {d:4.1f} mm at ({c.x:6.1f},{c.y:6.1f},{c.z:6.1f})")
print("## axis5-holder: loops 2.5-70 mm")
for key,c,d in loops(objs["axis5-holder"],2.5,70): print(f"   plane n=({key[0]},{key[1]},{key[2]}) d={key[3]}  loop {d:4.1f} mm at ({c.x:6.1f},{c.y:6.1f},{c.z:6.1f})")
print("## axis4_housingNema: loops 2.5-70 mm")
for key,c,d in loops(objs["axis4_housingNema"],2.5,70): print(f"   plane n=({key[0]},{key[1]},{key[2]}) d={key[3]}  loop {d:4.1f} mm at ({c.x:6.1f},{c.y:6.1f},{c.z:6.1f})")
print("HOLES DONE")
