"""Split mainBody1/2 (380 mm) for a 256 mm bed with a 40 mm half-lap joint.
Lap zone z 258-298: LOWER piece keeps the OUTER half of the 16 mm thickness,
UPPER piece keeps the INNER half. Two M4 clearance holes through the lap at
x = +/-55, z 268. Exports to model/split/ and renders an exploded view."""
import bpy, os, math
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model","split")
Z0,Z1=258.0,298.0; HOLES=[(-55.0,268.0),(55.0,268.0)]; HOLE_D=4.3
bpy.ops.wm.read_factory_settings(use_empty=True)
def box(name,x0,x1,y0,y1,z0,z1):
    bpy.ops.mesh.primitive_cube_add(); o=bpy.context.object; o.name=name
    o.location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2); o.scale=((x1-x0)/2,(y1-y0)/2,(z1-z0)/2)
    bpy.ops.object.transform_apply(scale=True); return o
def cyl(name,x,z,d):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=d/2,depth=200); o=bpy.context.object; o.name=name
    o.location=(x,0,z); o.rotation_euler=(math.radians(90),0,0); bpy.ops.object.transform_apply(rotation=True); return o
def cut(target,tool):
    m=target.modifiers.new("cut","BOOLEAN"); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=tool
    bpy.context.view_layer.objects.active=target; bpy.ops.object.modifier_apply(modifier=m.name)
def stats(o):
    import bmesh
    bm=bmesh.new(); bm.from_mesh(o.data); nm=sum(1 for e in bm.edges if not e.is_manifold); bm.free()
    d=o.dimensions; return f"{d.x:.1f} x {d.y:.1f} x {d.z:.1f} mm, {len(o.data.polygons)} faces, non-manifold edges {nm}"
report=[]
for name,(yin,yout) in {"mainBody1":(-28.0,-44.0),"mainBody2":(28.0,44.0)}.items():
    ymid=(yin+yout)/2; lo=min(yin,yout); hi=max(yin,yout)
    inner=(min(yin,ymid),max(yin,ymid)); outer=(min(yout,ymid),max(yout,ymid))
    for piece in ("lower","upper"):
        bpy.ops.wm.stl_import(filepath=os.path.join(ROOT,"Cults3d_v5/1-mainbody",name+".stl")); o=bpy.context.selected_objects[0]; o.name=f"{name}_{piece}"
        # tool faces must never coincide with plate faces: overshoot every outside face by 0.5 mm
        yi=(inner[0]-0.5,inner[1]) if inner[0]<inner[1] and abs(inner[0]-yin)<1e-6 else (inner[0],inner[1]+0.5)
        yo=(outer[0]-0.5,outer[1]) if abs(outer[0]-yout)<1e-6 else (outer[0],outer[1]+0.5)
        if piece=="lower":
            cut(o,box("b",-200,200,lo-5,hi+5,Z1,700)); cut(o,box("b2",-200,200,yi[0],yi[1],Z0,Z1+0.5))
        else:
            cut(o,box("b",-200,200,lo-5,hi+5,0,Z0)); cut(o,box("b2",-200,200,yo[0],yo[1],Z0-0.5,Z1))
        for x,z in HOLES: cut(o,cyl("h",x,z,HOLE_D))
        # boolean tessellation leaves zero-length slivers; merge them away
        import bmesh
        bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.02)
        bmesh.ops.dissolve_degenerate(bm,edges=bm.edges,dist=0.05)
        bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=8)   # micro gaps (incl. the original file's)
        bm.to_mesh(o.data); bm.free()
        for t in [t for t in bpy.data.objects if t.type=='MESH' and t is not o and not t.name.startswith("mainBody")]: bpy.data.objects.remove(t)
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.ops.wm.stl_export(filepath=os.path.join(OUT,f"{o.name}.stl"),export_selected_objects=True)
        report.append(f"{o.name}: {stats(o)}")
        o.color=(0.95,0.80,0.10,1) if piece=="lower" else (0.20,0.60,0.95,1)
        o.location.y += (-60 if piece=="lower" else 60)*(1 if name=="mainBody2" else -1)   # explode for the render
for r in report: print("SPLIT",r)
# render exploded view
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'; sh=scene.display.shading; sh.light='STUDIO'; sh.show_cavity=True; sh.show_object_outline=True; sh.color_type='OBJECT'
scene.render.resolution_x=1600; scene.render.resolution_y=1000
cam=bpy.data.cameras.new("c"); cam.type='ORTHO'; cam.ortho_scale=520; cam.clip_end=10000; co=bpy.data.objects.new("c",cam); scene.collection.objects.link(co)
co.rotation_euler=(math.radians(60),0,math.radians(45)); scene.camera=co
bpy.context.view_layer.update(); d=co.matrix_world.to_quaternion()@Vector((0,0,-1)); co.location=Vector((0,0,320))-d*1500
scene.render.filepath=os.path.join(OUT,"exploded.png"); bpy.ops.render.render(write_still=True)
co.location=(0,-1500,322); co.rotation_euler=(math.radians(90),0,0); cam.ortho_scale=440
scene.render.filepath=os.path.join(OUT,"front.png"); bpy.ops.render.render(write_still=True)
print("SPLIT DONE")
