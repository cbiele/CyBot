"""Seat the three axis-2 cycloid disks on their eccentrics and add a diskCap to each.
The Fusion export left the disks up to 4 mm off the shaft eccentrics and their O16 pocket
patterns ~30 deg from the O8 rod holes in the holders. Each disk is rotated about the joint
axis (y) until its pocket pattern sits on the 0/60/120 deg rod positions, then translated so
its bore centre matches the eccentric section of the shaft it rides. Caps are concentric with
their disk, flush with its -y face. Updates model/placements.json and model/bearings.json.
Run: Blender -b -P tools/blender/seat_axis2_disks.py"""
import bpy, bmesh, os, json, math
from mathutils import Vector, Matrix
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"
PJ=os.path.join(ROOT,"model/placements.json"); BJ=os.path.join(ROOT,"model/bearings.json")
P=json.load(open(PJ)); B=json.load(open(BJ))
ECC={"axis2-disk3":(-0.7,201.33),"axis2-disk2":(-1.1,204.7),"axis2-disk1":(1.8,203.0)}   # shaft eccentric centres (x,z) by y-range
bpy.ops.wm.read_factory_settings(use_empty=True)

def loops(o,minsz,maxsz):
    bm=bmesh.new(); bm.from_mesh(o.data)
    for s in (bm.verts,bm.edges,bm.faces): s.ensure_lookup_table()
    M=o.matrix_world; R=M.to_3x3(); planes={}
    for f in bm.faces:
        n=(R@f.normal).normalized(); c=M@f.calc_center_median()
        planes.setdefault((round(n.x,1),round(n.y,1),round(n.z,1),round(n.dot(c)*2)/2),[]).append(f)
    out=[]
    for key,faces in planes.items():
        fs=set(faces); adj={}
        for f in faces:
            for e in f.edges:
                if sum(1 for ff in e.link_faces if ff in fs)==1:
                    a,b=e.verts; adj.setdefault(a.index,set()).add(b.index); adj.setdefault(b.index,set()).add(a.index)
        seen=set()
        for s in adj:
            if s in seen: continue
            comp=[]; st=[s]
            while st:
                v=st.pop()
                if v in seen: continue
                seen.add(v); comp.append(v); st.extend(adj[v]-seen)
            pts=[M@bm.verts[i].co for i in comp]; ctr=sum(pts,Vector())/len(pts)
            r=[(p-ctr).length for p in pts]; rm=sum(r)/len(r)
            if len(pts)>=12 and max(abs(x-rm) for x in r)<0.15*rm and minsz<=2*rm<=maxsz: out.append((ctr,2*rm))
    bm.free(); return out
def pattern(o):
    """centre of the O32 bore and phase (deg) of the six O16 pockets, from the -y-most planes"""
    L=loops(o,15,33)
    bore=[c for c,d in L if abs(d-32)<0.5]; pk=[c for c,d in L if abs(d-16)<0.5]
    cx=sum(c.x for c in bore)/len(bore); cz=sum(c.z for c in bore)/len(bore)
    # circular mean over the 60 deg period so pockets straddling 0 deg do not average to 30
    sx=sum(math.cos(6*math.atan2(c.z-cz,c.x-cx)) for c in pk); sz=sum(math.sin(6*math.atan2(c.z-cz,c.x-cx)) for c in pk)
    return cx,cz,(math.degrees(math.atan2(sz,sx))/6)%60,pk
def load(nm):
    e=P[nm]; bpy.ops.wm.stl_import(filepath=os.path.join(ROOT,e["file"])); o=bpy.context.selected_objects[0]
    o.matrix_world=Matrix(e["matrix_world"]); return o
def rot_y_about(o,deg,cx,cz):
    piv=Vector((cx,0,cz)); o.matrix_world=Matrix.Translation(piv)@Matrix.Rotation(math.radians(deg),4,'Y')@Matrix.Translation(-piv)@o.matrix_world
def zero_phase(o):
    cx,cz,ph,_=pattern(o)
    for sgn in (-1,1):
        m=o.matrix_world.copy(); rot_y_about(o,sgn*ph,cx,cz)
        if min(pattern(o)[2],60-pattern(o)[2])<0.3: return sgn*ph
        o.matrix_world=m
    raise RuntimeError(o.name)

def bb(o): return [o.matrix_world@Vector(c) for c in o.bound_box]
def face_y(o,sign,rlo,rhi):
    """area-weighted y of the planar faces with normal sign*y whose outer radius (about the joint axis) is in rlo..rhi"""
    bm=bmesh.new(); bm.from_mesh(o.data); M=o.matrix_world; R=M.to_3x3(); a=0; ay=0
    for f in bm.faces:
        n=(R@f.normal).normalized()
        if n.y*sign<0.99: continue
        rmax=max(((M@v.co).x**2+((M@v.co).z-203)**2)**0.5 for v in f.verts)
        if rlo<=rmax<=rhi: ar=f.calc_area(); a+=ar; ay+=ar*(M@f.calc_center_median()).y
    bm.free(); return ay/a
caps=[]; report={}
cap=load("axis2/axis2-diskCap"); cap_rot=zero_phase(cap); cap_base=cap.matrix_world.copy()
for nm,(ex,ez) in ECC.items():
    o=load("axis2/"+nm); rot=zero_phase(o); cx,cz,ph,_=pattern(o)
    o.matrix_world=Matrix.Translation(Vector((ex-cx,0,ez-cz)))@o.matrix_world
    cx,cz,ph,pk=pattern(o); ymin=min(p.y for p in bb(o))
    P["axis2/"+nm]["matrix_world"]=[list(r) for r in o.matrix_world]
    # cap: concentric, flush with the disk's -y face
    c=cap.copy(); c.data=cap.data; bpy.context.scene.collection.objects.link(c); c.matrix_world=cap_base.copy()
    ccx,ccz,_,_=pattern(c)
    floor=face_y(o,-1,40,43); capface=face_y(c,+1,40,43)   # disk recess floor (-y facing, r<=42) and the cap's +y face
    c.matrix_world=Matrix.Translation(Vector((cx-ccx,floor-capface,cz-ccz)))@c.matrix_world
    caps.append(c); report[nm]={"rot":round(rot,1),"centre":(round(cx,2),round(cz,2)),"phase":round(ph,1),"rim":round(face_y(o,-1,55,62),1),"floor":round(floor,1),"cap_y":(round(min(p.y for p in bb(c)),1),round(max(p.y for p in bb(c)),1))}
    # bearings: 6804 at the bore, 688 at the pockets (pocket loops give the -y mouth; centre the 5 mm bearing 2.5 mm in)
    for b in B["axis2"]["bearings"]:
        if b["between"][0]!=nm: continue
        if b["type"].startswith("6804"): b["center"]=[round(cx,2),b["center"][1],round(cz,2)]
    pks=sorted({(round(p.x,1),round(p.z,1)) for p in pk})
    # group pocket loop centres (two planes per pocket) into six positions
    pos=[]
    for x,z in pks:
        if not any(abs(x-a)<2 and abs(z-b_)<2 for a,b_ in pos): pos.append((x,z))
    i=0
    for b in B["axis2"]["bearings"]:
        if b["between"][0]==nm and b["type"].startswith("688"):
            b["center"]=[pos[i][0],b["center"][1],pos[i][1]]; i+=1
    report[nm]["pockets"]=len(pos)
for i,c in enumerate(caps):
    key="axis2/axis2-diskCap" if i==0 else f"axis2/axis2-diskCap.{i+1}"
    P[key]={"collection":"axis2","file":"Cults3d_v5/3-axis2/axis2-diskCap.stl","matrix_world":[list(r) for r in c.matrix_world],"hide":False}
json.dump(P,open(PJ,"w"),indent=1); json.dump(B,open(BJ,"w"),indent=1)
print("SEATED",json.dumps(report),"cap_rot",round(cap_rot,1))
