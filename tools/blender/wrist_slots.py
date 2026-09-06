"""List slot loops (3-4 mm wide, 8-20 mm long) on the wrist holders and their pairwise spacings."""
import bpy, bmesh, os, itertools
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
for name in ("axis5-holder","axis5-holder2","axis5-axis6holder1","axis5-axis6holder2","axis4_housingNema","mainHolder"):
    o=[x for x in bpy.data.objects if x.name.endswith("/"+name)][0]
    bm=bmesh.new(); bm.from_mesh(o.data)
    for s in (bm.verts,bm.edges,bm.faces): s.ensure_lookup_table()
    M=o.matrix_world; R=M.to_3x3(); planes={}
    for f in bm.faces:
        n=(R@f.normal).normalized(); c=M@f.calc_center_median()
        key=(round(n.x,1),round(n.y,1),round(n.z,1),round(n.dot(c)/2)*2); planes.setdefault(key,[]).append(f)
    print(f"## {name}")
    for key,faces in planes.items():
        fs=set(faces)
        if sum(f.calc_area() for f in faces)<300: continue
        bedges=[e for f in faces for e in f.edges if sum(1 for ff in e.link_faces if ff in fs)==1]
        adj={}
        for e in bedges:
            a,b=e.verts; adj.setdefault(a.index,set()).add(b.index); adj.setdefault(b.index,set()).add(a.index)
        seen=set(); slots=[]; holes=[]
        for s in adj:
            if s in seen: continue
            comp=[]; st=[s]
            while st:
                v=st.pop()
                if v in seen: continue
                seen.add(v); comp.append(v); st.extend(adj[v]-seen)
            pts=[M@bm.verts[i].co for i in comp]
            mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
            d=sorted([(mx-mn).x,(mx-mn).y,(mx-mn).z],reverse=True); c=(mn+mx)/2
            if 8<=d[0]<=22 and 2.5<=d[1]<=5.5: slots.append((c,d))
            elif 2.5<=d[0]<=7 and d[1]>=0.6*d[0]: holes.append((c,d))
        if len(slots)>=2 or len(holes)>=3:
            print(f"  plane n=({key[0]},{key[1]},{key[2]}) d={key[3]}: {len(slots)} slots, {len(holes)} holes")
            for c,d in slots: print(f"     slot {d[0]:4.1f}x{d[1]:3.1f} at ({c.x:6.1f},{c.y:6.1f},{c.z:6.1f})")
            for (c1,_),(c2,_) in itertools.combinations(slots,2):
                L=(c1-c2).length
                if 28<=L<=34 or 44<=L<=50: print(f"       slot pair spacing {L:5.1f} mm  -> {'NEMA17' if L<40 else 'NEMA23'}")
    bm.free()
print("SLOTS DONE")
