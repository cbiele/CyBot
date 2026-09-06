"""Pass 2: rigid-register each local-frame part group onto the URDF reference
with ICP from a grid of initial poses; write transforms to model/transforms.json."""
import bpy, os, json, math, random
import numpy as np
from mathutils import Vector, Matrix, kdtree
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"cybot-pass1.blend"))
scene=bpy.context.scene
random.seed(1)

def verts_world(o, n=None):
    M=o.matrix_world; v=o.data.vertices
    idx=range(len(v)) if n is None or len(v)<=n else random.sample(range(len(v)),n)
    return np.array([(M@v[i].co)[:] for i in idx])

# target: all URDF links
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

def icp(P, R0, t0, iters=40, trim=0.7):
    R,t=R0.copy(),t0.copy()
    for _ in range(iters):
        Q=(R@P.T).T+t; C,d=nn(Q)
        keep=d<=np.quantile(d,trim)
        Rd,td=rigid_fit(Q[keep],C[keep]); R=Rd@R; t=Rd@t+td
    Q=(R@P.T).T+t; _,d=nn(Q)
    return R,t,float(np.median(d)),float(np.quantile(d,0.9))

def rotz(deg): a=math.radians(deg); return np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
def rotx(deg): a=math.radians(deg); return np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
def roty(deg): a=math.radians(deg); return np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])

GLOBAL={"axis2-holder1","axis2-holder2","axis4_axis5_holder","mainBody1","mainBody2","plateBall",
        "axis-1-rotatingBase1","axis-1-rotatingBase2","axis-1-rotatingBase3","axis1-baseHolder","axis1-encoderHolder","axis1-stepperHolder"}
SKIP={"axis5-holderNoSplit","beltTentioner1","beltTentioner2","beltTentioner3"}
def group_objs(g): return [o for o in bpy.data.collections[g].objects if o.name.split("/")[1] not in GLOBAL|SKIP]

# candidate initial poses per group: (rotation list, translation grid)
Z=lambda a,b,s: [np.array([0,0,z],float) for z in range(a,b+1,s)]
cands={
 "axis2":  ([np.eye(3),rotz(180)], Z(120,540,20)),
 "axis3":  ([np.eye(3),rotz(180)], Z(120,540,20)),
 "axis4":  ([rotz(90),rotz(-90),rotz(90)@rotx(180),rotz(-90)@rotx(180)], [np.array([x,0,z],float) for x in range(-40,200,20) for z in range(480,600,20)]),
 "axis56": ([np.eye(3)], Z(420,480,5)),
 "gripper":([np.eye(3),rotx(90),rotx(180),rotx(270)], [np.array([x,0,z],float) for x in range(260,340,20) for z in range(520,600,20)]),
}
results={}
for g,(rots,trans) in cands.items():
    objs=group_objs(g)
    P=np.vstack([verts_world(o,1500) for o in objs])
    best=None
    for R0 in rots:
        for t0 in trans:
            R,t,med,p90=icp(P,R0,t0,iters=12)
            if best is None or med<best[2]: best=(R,t,med,p90,R0,t0)
    R,t,med,p90,R0,t0=best
    R,t,med,p90=icp(P,R,t,iters=40)
    results[g]={"R":R.tolist(),"t":t.tolist(),"median_mm":round(med,2),"p90_mm":round(p90,2),"init_t":t0.tolist()}
    print(f"REG {g:8s} median {med:6.2f} mm  p90 {p90:6.2f} mm  t={np.round(t,1).tolist()}  from init {t0.tolist()}")
    M=Matrix(((R[0][0],R[0][1],R[0][2],t[0]),(R[1][0],R[1][1],R[1][2],t[1]),(R[2][0],R[2][1],R[2][2],t[2]),(0,0,0,1)))
    for o in objs: o.matrix_world=M@o.matrix_world
json.dump(results,open(os.path.join(OUT,"transforms.json"),"w"),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"cybot-pass2.blend"))
print("PASS2 DONE")
