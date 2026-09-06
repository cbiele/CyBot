"""Scan every printed part for motor/encoder mounting patterns:
NEMA17 = 4 holes on a 31.0 mm square, NEMA23 = 4 holes on a 47.14 mm square,
E6B2 encoder = 3 holes on a 30 mm PCD (120 deg)."""
import bpy, bmesh, os, math, itertools
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend"))
def plane_loops(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    for s in (bm.verts,bm.edges,bm.faces): s.ensure_lookup_table()
    M=o.matrix_world; R=M.to_3x3(); planes={}
    for f in bm.faces:
        n=(R@f.normal).normalized(); c=M@f.calc_center_median()
        key=(round(n.x,1),round(n.y,1),round(n.z,1),round(n.dot(c)/2)*2); planes.setdefault(key,[]).append(f)
    res={}
    for key,faces in planes.items():
        fs=set(faces)
        if sum(f.calc_area() for f in faces)<300: continue
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
            d=sorted([(mx-mn).x,(mx-mn).y,(mx-mn).z],reverse=True)
            loops.append(((mn+mx)/2,d[0],d[1]))
        res[key]=loops
    bm.free(); return res
def find_patterns(loops):
    holes=[(c,d) for c,d,d2 in loops if 2.4<=d<=7.5 and d2>=d*0.6]
    out=[]
    # squares
    for side,name,tol in ((31.0,"NEMA17",1.2),(47.14,"NEMA23",1.5)):
        for combo in itertools.combinations(holes,4):
            pts=[c for c,_ in combo]; ctr=sum(pts,Vector())/4
            r=[(p-ctr).length for p in pts]; want=side/math.sqrt(2)
            if all(abs(x-want)<tol for x in r):
                ds=sorted((a-b).length for a,b in itertools.combinations(pts,2))
                if abs(ds[0]-side)<tol and abs(ds[3]-side)<tol: out.append((name,ctr,combo[0][1]))
    # E6B2 triangle: 3 holes at r=15
    for combo in itertools.combinations(holes,3):
        pts=[c for c,_ in combo]; ctr=sum(pts,Vector())/3
        r=[(p-ctr).length for p in pts]
        ds=sorted((a-b).length for a,b in itertools.combinations(pts,2))
        if all(abs(x-15.0)<1.0 for x in r) and all(abs(x-25.98)<1.5 for x in ds): out.append(("E6B2",ctr,combo[0][1]))
    # dedupe
    ded=[]
    for o in out:
        if not any(o[0]==p[0] and (o[1]-p[1]).length<2 for p in ded): ded.append(o)
    return ded
print("MOUNT PATTERNS")
for o in bpy.data.objects:
    if o.type!='MESH' or o.hide_render or o.name.startswith("urdf"): continue
    if o.users_collection and o.users_collection[0].name in ("urdf","alternates","unplaced"): continue
    for key,loops in plane_loops(o).items():
        for name,ctr,hd in find_patterns(loops):
            big=[ (d) for c,d,d2 in loops if 15<=d<=45 and (c-ctr).length<4]
            print(f"  {o.name.split('/')[-1]:24s} {name:6s} centre=({ctr.x:7.1f},{ctr.y:7.1f},{ctr.z:7.1f}) plane n=({key[0]},{key[1]},{key[2]}) hole={hd:.1f}mm pilot/bore={['%.1f'%b for b in big]}")
print("PATTERNS DONE")
