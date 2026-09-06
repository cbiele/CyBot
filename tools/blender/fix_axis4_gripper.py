"""Pass 3: re-fit axis4 with the tube constrained to +X, place the gripper on the
axis-6 flange (no URDF geometry exists for it), park alternates, save pass3."""
import bpy, os, json, math, random
import numpy as np
from mathutils import Vector, Matrix, kdtree
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass1.blend"))
scene=bpy.context.scene; random.seed(1)
T=json.load(open(os.path.join(OUT,"transforms.json")))
def M_of(R,t): return Matrix(((R[0][0],R[0][1],R[0][2],t[0]),(R[1][0],R[1][1],R[1][2],t[1]),(R[2][0],R[2][1],R[2][2],t[2]),(0,0,0,1)))
GLOBAL={"axis2-holder1","axis2-holder2","axis4_axis5_holder","mainBody1","mainBody2","plateBall",
        "axis-1-rotatingBase1","axis-1-rotatingBase2","axis-1-rotatingBase3","axis1-baseHolder","axis1-encoderHolder","axis1-stepperHolder"}
ALT={"axis5-holderNoSplit"}; UNPLACED={"beltTentioner1","beltTentioner2","beltTentioner3"}
def gobjs(g): return [o for o in bpy.data.collections[g].objects if o.name.split("/")[1] not in GLOBAL|ALT|UNPLACED]
# apply the good pass-2 results
for g in ("axis2","axis3","axis56"):
    M=M_of(T[g]["R"],T[g]["t"])
    for o in gobjs(g): o.matrix_world=M@o.matrix_world

def verts_world(o,n=None):
    M=o.matrix_world; v=o.data.vertices
    idx=range(len(v)) if n is None or len(v)<=n else random.sample(range(len(v)),n)
    return np.array([(M@v[i].co)[:] for i in idx])
tgt=np.vstack([verts_world(o) for o in bpy.data.collections["urdf"].objects])
kd=kdtree.KDTree(len(tgt))
for i,p in enumerate(tgt): kd.insert(Vector(p),i)
kd.balance()
def nn(P):
    out=np.empty_like(P); d=np.empty(len(P))
    for i,p in enumerate(P):
        co,idx,dist=kd.find(Vector(p)); out[i]=co[:]; d[i]=dist
    return out,d
def rigid_fit(A,B):
    ca,cb=A.mean(0),B.mean(0); H=(A-ca).T@(B-cb); U,S,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    return R, cb-R@ca
def icp(P,R0,t0,iters=40,trim=0.7):
    R,t=R0.copy(),t0.copy()
    for _ in range(iters):
        Q=(R@P.T).T+t; C,d=nn(Q); keep=d<=np.quantile(d,trim)
        Rd,td=rigid_fit(Q[keep],C[keep]); R=Rd@R; t=Rd@t+td
    Q=(R@P.T).T+t; _,d=nn(Q); return R,t,float(np.median(d)),float(np.quantile(d,0.9))
def rotz(deg): a=math.radians(deg); return np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
def rotx(deg): a=math.radians(deg); return np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])

# axis4: local -Y (tube) must map to +X  => rotz(90); allow roll about X
objs=gobjs("axis4"); P=np.vstack([verts_world(o,1500) for o in objs])
best=None
for phi in (0,90,180,270):
    R0=rotx(phi)@rotz(90)
    for x in range(40,160,20):
        for z in range(535,580,10):
            R,t,med,p90=icp(P,R0,np.array([x,0,z],float),iters=12)
            if best is None or med<best[2]: best=(R,t,med,p90,phi,x,z)
R,t,med,p90,phi,x,z=best; R,t,med,p90=icp(P,R,t,iters=40)
ang=math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2))))
print(f"REG axis4 median {med:.2f} p90 {p90:.2f} t={np.round(t,1).tolist()} rot={ang:.1f} from phi={phi} x={x} z={z}")
T["axis4"]={"R":R.tolist(),"t":t.tolist(),"median_mm":round(med,2),"p90_mm":round(p90,2)}
M=M_of(R.tolist(),t.tolist())
for o in objs: o.matrix_world=M@o.matrix_world

# gripper: identity rotation, adapter (OPH_To_Gripper) x-min placed at the axis-6 flange.
# flange = +X extreme of the URDF wrist (link_5) ; forearm axis height/lateral = link_5 center
l5=[o for o in bpy.data.collections["urdf"].objects if o.name.endswith("link_5")][0]
V=verts_world(l5); fx=float(V[:,0].max()); cy=float((V[:,1].max()+V[:,1].min())/2); cz=float((V[:,2].max()+V[:,2].min())/2)
ad=[o for o in bpy.data.collections["gripper"].objects if o.name.endswith("OPH_To_Gripper")][0]
A=verts_world(ad); ax=float(A[:,0].min()); ay=float((A[:,1].max()+A[:,1].min())/2); az=float((A[:,2].max()+A[:,2].min())/2)
tg=[fx-ax, cy-ay, cz-az]
print(f"GRIPPER flange x={fx:.1f} y={cy:.1f} z={cz:.1f}  -> t={np.round(tg,1).tolist()}  (analytic, not fitted)")
T["gripper"]={"R":np.eye(3).tolist(),"t":tg,"median_mm":None,"p90_mm":None,"note":"analytic: adapter x-min on link_5 x-max"}
M=M_of(np.eye(3).tolist(),tg)
for o in bpy.data.collections["gripper"].objects: o.matrix_world=M@o.matrix_world

# park alternates / unplaced
for cname,names,off in (("alternates",ALT,(0,600,0)),("unplaced",UNPLACED,(0,-600,0))):
    c=bpy.data.collections.new(cname); scene.collection.children.link(c)
    for col in list(scene.collection.children):
        for o in list(col.objects):
            if o.name.split("/")[-1] in names:
                col.objects.unlink(o); c.objects.link(o); o.location=Vector(off)+o.location
json.dump(T,open(os.path.join(OUT,"transforms.json"),"w"),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"cybot-pass3.blend")); print("PASS3 DONE")
