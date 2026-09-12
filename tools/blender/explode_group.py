"""Build model/subassemblies/<group>.blend: one print folder as an exploded assembly.
Parts come from model/placements.json, bearings from model/bearings.json. Two collections:
<group>-assembled (true positions, hidden) and <group>-exploded (parts pushed apart along the
joint axis in stack order, bearings floated above their host part, labels below). The text block
ASSEMBLY.md lists the stack order and hardware.
Run: Blender -b -P tools/blender/explode_group.py -- axis2 [GAP_mm]"""
import bpy, bmesh, os, sys, json, math
from mathutils import Vector, Matrix
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model/subassemblies")
argv=sys.argv[sys.argv.index("--")+1:]; GROUP=argv[0]; GAP=float(argv[1]) if len(argv)>1 else 25.0
COLORS={"mainbody":(0.95,0.80,0.10,1),"axis1":(0.20,0.60,0.95,1),"axis2":(0.90,0.30,0.20,1),"axis3":(0.30,0.80,0.30,1),
        "axis4":(0.80,0.30,0.90,1),"axis56":(0.10,0.85,0.85,1),"gripper":(0.95,0.55,0.10,1)}
P={k:v for k,v in json.load(open(os.path.join(ROOT,"model/placements.json"))).items() if v["collection"]==GROUP}
BG=json.load(open(os.path.join(ROOT,"model/bearings.json")))[GROUP]
A=Vector(BG["axis"]).normalized(); U=Vector(BG["up"]).normalized(); O=Vector(BG["origin"]); V=A.cross(U)
R=Matrix((A,U,V)).transposed()   # columns: along-axis, up, toward-camera

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=0.001; scene.unit_settings.length_unit='MILLIMETERS'
def mat(name,rgba):
    m=bpy.data.materials.new(name); m.diffuse_color=rgba; return m
m_part=mat(GROUP,COLORS[GROUP]); m_brg=mat("bearing",(0.35,0.35,0.38,1)); m_txt=mat("label",(0.05,0.05,0.05,1))
cols={}
def coll(name):
    if name not in cols:
        c=bpy.data.collections.new(name); scene.collection.children.link(c); cols[name]=c
    return cols[name]
ASM=coll(GROUP+"-assembled"); EXP=coll(GROUP+"-exploded")

def ring_mesh(od,id_,w,n=48):
    bm=bmesh.new(); rings=[]
    for r,z in ((od/2,w/2),(id_/2,w/2),(id_/2,-w/2),(od/2,-w/2)):
        rings.append([bm.verts.new((r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z)) for i in range(n)])
    for k in range(4):
        a,b=rings[k],rings[(k+1)%4]
        for i in range(n): bm.faces.new((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
    me=bpy.data.meshes.new("ring"); bm.to_mesh(me); bm.free(); return me

def bbox(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return pts
def along(o):
    t=[(p-O).dot(A) for p in bbox(o)]; return (min(t)+max(t))/2, max(t)-min(t)
def radial(o):
    return max(((p-O)-(p-O).dot(A)*A).length for p in bbox(o))

parts=[]
for nm,e in P.items():
    bpy.ops.wm.stl_import(filepath=os.path.join(ROOT,e["file"])); o=bpy.context.selected_objects[0]
    for oc in list(o.users_collection): oc.objects.unlink(o)
    ASM.objects.link(o); o.name=nm.split("/")[-1]; o.data.materials.append(m_part); o.matrix_world=Matrix(e["matrix_world"])
    parts.append(o)
bearings=[]
for i,b in enumerate(BG["bearings"]):
    o=bpy.data.objects.new(f"{b['type']}_{i+1:02d}", ring_mesh(b["od"],b["id"],b["w"])); o.data.materials.append(m_brg)
    ax=Vector(b["axis"]).normalized(); rot=Vector((0,0,1)).rotation_difference(ax).to_matrix().to_4x4()
    o.matrix_world=Matrix.Translation(Vector(b["center"]))@rot; ASM.objects.link(o)
    o["host"]=b["between"][0]; o["between"]=" / ".join(b["between"]); o["note"]=b.get("note",""); bearings.append(o)

# stack order and exploded positions for printed parts
order=sorted(parts,key=lambda o:(along(o)[0],o.name)); rmax_all=max(radial(o) for o in parts)
for name,anchor in BG.get("order_after",{}).items():
    o=next(x for x in order if x.name==name); order.remove(o); order.insert(order.index(next(x for x in order if x.name==anchor))+1,o)
# "order": an explicit left-to-right list from the bench; unlisted parts trail it in their natural order
if BG.get("order"):
    byname={o.name:o for o in order}; listed=[byname[n] for n in BG["order"]]
    order=listed+[o for o in order if o not in listed]
FLIP=set(BG.get("flip",[]))   # parts shown turned 180 deg about the up axis in the exploded row only
newt={}; prev_end=None
for o in order:
    t,ext=along(o)
    t2=t if prev_end is None else max(t,prev_end+GAP+ext/2)
    newt[o.name]=t2; prev_end=t2+ext/2
def dup(o,shift):
    d=o.copy(); d.data=o.data; d.name=o.name+".x"; d.matrix_world=Matrix.Translation(shift)@o.matrix_world; EXP.objects.link(d); return d
labels=[]
for i,o in enumerate(order):
    t,ext=along(o); d=dup(o,A*(newt[o.name]-t))
    if o.name in FLIP:
        c=O+A*newt[o.name]; d.matrix_world=Matrix.Translation(c)@Matrix.Rotation(math.pi,4,U)@Matrix.Translation(-c)@d.matrix_world
    labels.append((o.name,newt[o.name],-(rmax_all+12+22*(i%3))))   # three staggered rows so short parts' labels do not collide
hosts={o.name:o for o in parts}; cluster={}
for b in bearings:
    h=hosts.get(b["host"])
    if h is None: continue
    t,ext=along(h); lift=radial(h)+b.data.vertices[0].co.length+15
    dup(b,A*(newt[h.name]-t)+U*lift)
    top=(b.matrix_world.translation-O).dot(U)+lift+b.data.vertices[0].co.length
    c=cluster.setdefault(h.name,{"t":newt[h.name],"top":0,"types":{}}); c["top"]=max(c["top"],top)
    c["types"][b.name.split("_")[0]]=c["types"].get(b.name.split("_")[0],0)+1
for h,c in cluster.items():
    labels.append((" + ".join(f"{k} x{n}" if n>1 else k for k,n in c["types"].items()),c["t"],c["top"]+10))
bpy.ops.object.select_all(action='DESELECT')
for name,t,drop in labels:
    bpy.ops.object.text_add(); tx=bpy.context.object; tx.data.body=name; tx.data.size=9; tx.data.align_x='CENTER'
    tx.data.materials.append(m_txt); tx.name="label_"+name
    for oc in list(tx.users_collection): oc.objects.unlink(tx)
    EXP.objects.link(tx); tx.matrix_world=Matrix.Translation(O+A*t+U*drop)@R.to_4x4()

# camera: orthographic, looking along -V at the exploded row
ts=[newt[o.name] for o in order]; tmin=min(ts)-90; tmax=max(ts)+90
rmax=max(radial(o) for o in parts)
centre=O+A*((tmin+tmax)/2)
cam=bpy.data.cameras.new("cam"); cam.type='ORTHO'; cam.ortho_scale=max(tmax-tmin,4*rmax+120); cam.clip_end=10000
co=bpy.data.objects.new("Camera",cam); scene.collection.objects.link(co); scene.camera=co
Rc=R.to_4x4()@Matrix.Rotation(math.radians(35),4,'Y')@Matrix.Rotation(math.radians(-22),4,'X')
co.matrix_world=Matrix.Translation(centre+(Rc.to_3x3()@Vector((0,0,1)))*1500)@Rc
scene.render.engine='BLENDER_WORKBENCH'; scene.render.resolution_x=2400; scene.render.resolution_y=int(2400*max(0.35,min(1.0,(4*rmax+120)/max(tmax-tmin,1))))
scene.display.shading.light='STUDIO'; scene.display.shading.color_type='MATERIAL'; scene.display.shading.show_cavity=True
scene.render.film_transparent=False; scene.world=bpy.data.worlds.new("w"); scene.world.color=(1,1,1)
ASM.hide_viewport=True; ASM.hide_render=True

# assembly notes
lines=[f"# {GROUP}: stack order along the joint axis {tuple(BG['axis'])} (assembled coordinates, mm)\n",
       "Parts in the order they sit along the axis; bearings listed under the part they seat in.\n"]
if BG.get("order"): lines.append(f"Order set by hand on the bench ({BG.get('order_note','')}); parts after the listed ones are unplaced.\n")
for o in order:
    t,ext=along(o); flag=" [flipped]" if o.name in FLIP else ""; flag+=" [not in the bench order]" if BG.get("order") and o.name not in BG["order"] else ""
    lines.append(f"- {o.name}  (centre {t:+.1f}, {ext:.0f} mm long){flag}")
    seen={}
    for b in bearings:
        if b["host"]!=o.name: continue
        k=(b.name.split('_')[0],b['between']); seen.setdefault(k,[0,b['note']]); seen[k][0]+=1
    for (typ,btw),(n,note) in seen.items(): lines.append(f"    - {typ}{' x'+str(n) if n>1 else ''}  {btw}" + (f": {note}" if note else ""))
lines.append("\n## Hardware (PDF list + STL count)")
lines+=["- "+h for h in BG["hardware"]]
txt=bpy.data.texts.new("ASSEMBLY.md"); txt.write("\n".join(lines)+"\n")
open(os.path.join(OUT,GROUP+"-assembly.md"),"w").write("\n".join(lines)+"\n")

for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        sp=area.spaces.active; sp.clip_start=1.0; sp.clip_end=100000.0; sp.shading.type='SOLID'; sp.shading.color_type='MATERIAL'; sp.shading.show_cavity=True
        sp.region_3d.view_distance=cam.ortho_scale*0.9; sp.region_3d.view_location=centre; sp.region_3d.view_rotation=Rc.to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,GROUP+".blend"))
scene.render.filepath=os.path.join(OUT,GROUP+"-exploded.png"); bpy.ops.render.render(write_still=True)
print("EXPLODED",GROUP,len(parts),"parts",len(bearings),"bearings", "row", round(tmin), round(tmax))
