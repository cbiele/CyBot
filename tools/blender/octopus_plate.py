"""Printed tray for the BTT Octopus Pro (V1.0/V1.1): 3 mm floor, four M3 standoffs
on the board's 150 x 90 hole grid, and a 2 mm lip following the board's R5 outline
that rises 3 mm above the board seating plane. Lip cutouts clear the right-edge
connectors (USB-C, reset switch, micro SD, USB-A, RJ11). Board data comes from
BTT's SIZE.pdf and STEP model (github.com/bigtreetech/BIGTREETECH-OCTOPUS-Pro).
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/octopus_plate.py
Exports model/electronics/octopus-pro-plate.stl and renders a preview."""
import bpy, bmesh, os, math
from mathutils import Vector
ROOT="/Users/claytonbiele/dev/Claude/Projects/cybot"; OUT=os.path.join(ROOT,"model","electronics")
os.makedirs(OUT,exist_ok=True)

BOARD_W,BOARD_H,BOARD_R=160.0,100.0,5.0
HOLE_GRID=(150.0,90.0)
CLEAR=0.5                      # lip to board edge, per side
WALL=2.0
FLOOR=3.0
STANDOFF_H,STANDOFF_D,PILOT_D=6.0,7.0,2.8   # M3 thread-forming into the post
LIP_ABOVE_BOARD=3.0            # lip top above the board seating plane
PLATE_W,PLATE_H,PLATE_R=184.0,110.0,8.0
PLATE_HOLE_GRID,PLATE_HOLE_D=(174.0,50.0),4.3
# right-edge connector spans in board coords (mm from the bottom edge), 1 mm clearance
# each side and neighbours merged: RJ11 12.5-28.3, USB-A 29-44.8, micro SD 49.9-64.5,
# USB-C 72.7-81.7, reset switch 84.6-89.2
RIGHT_CUTOUTS=[(11.0,66.0),(71.5,90.5)]

SEAT_Z=FLOOR+STANDOFF_H
LIP_TOP=SEAT_Z+LIP_ABOVE_BOARD

def rrect_points(w,h,r,n=12):
    pts=[]
    for cx,cy,a0 in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for i in range(n+1):
            a=math.radians(a0+90*i/n); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts
def prism(name,pts,z0,z1):
    bm=bmesh.new()
    lo=[bm.verts.new((x,y,z0)) for x,y in pts]; hi=[bm.verts.new((x,y,z1)) for x,y in pts]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for i in range(len(pts)):
        j=(i+1)%len(pts); bm.faces.new((lo[i],lo[j],hi[j],hi[i]))
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-4)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); return o
def box(name,x0,x1,y0,y1,z0,z1):
    return prism(name,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z0,z1)
def cyl(name,x,y,d,z0,z1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=d/2,depth=z1-z0,location=(x,y,(z0+z1)/2))
    o=bpy.context.object; o.name=name; return o
def boolean(target,tool,op):
    m=target.modifiers.new(op,"BOOLEAN"); m.operation=op; m.solver='EXACT'; m.object=tool
    bpy.context.view_layer.objects.active=target; bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(tool)
def stats(o):
    bm=bmesh.new(); bm.from_mesh(o.data); nm=sum(1 for e in bm.edges if not e.is_manifold); bm.free()
    d=o.dimensions; return f"{d.x:.1f} x {d.y:.1f} x {d.z:.1f} mm, {len(o.data.polygons)} faces, non-manifold edges {nm}"

bpy.ops.wm.read_factory_settings(use_empty=True)
plate=prism("octopus-pro-plate",rrect_points(PLATE_W,PLATE_H,PLATE_R),0,FLOOR)
inner_w,inner_h,inner_r=BOARD_W+2*CLEAR,BOARD_H+2*CLEAR,BOARD_R+CLEAR
lip=prism("lip",rrect_points(inner_w+2*WALL,inner_h+2*WALL,inner_r+WALL),FLOOR-0.5,LIP_TOP)
boolean(lip,prism("lip_inner",rrect_points(inner_w,inner_h,inner_r),FLOOR-1,LIP_TOP+1),'DIFFERENCE')
boolean(plate,lip,'UNION')
gx,gy=HOLE_GRID
for sx in (-1,1):
    for sy in (-1,1):
        boolean(plate,cyl("post",sx*gx/2,sy*gy/2,STANDOFF_D,FLOOR-0.5,SEAT_Z),'UNION')
        boolean(plate,cyl("pilot",sx*gx/2,sy*gy/2,PILOT_D,FLOOR-0.5,SEAT_Z+1),'DIFFERENCE')
px,py=PLATE_HOLE_GRID
for sx in (-1,1):
    for sy in (-1,1):
        boolean(plate,cyl("mount",sx*px/2,sy*py/2,PLATE_HOLE_D,-1,FLOOR+1),'DIFFERENCE')
for y0,y1 in RIGHT_CUTOUTS:
    boolean(plate,box("cut",BOARD_W/2-1,PLATE_W/2+1,y0-BOARD_H/2,y1-BOARD_H/2,SEAT_Z,LIP_TOP+1),'DIFFERENCE')

bm=bmesh.new(); bm.from_mesh(plate.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.02); bm.to_mesh(plate.data); bm.free()
bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True); bpy.context.view_layer.objects.active=plate
bpy.ops.wm.stl_export(filepath=os.path.join(OUT,"octopus-pro-plate.stl"),export_selected_objects=True)
print("PLATE",stats(plate))

scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'; sh=scene.display.shading
sh.light='STUDIO'; sh.show_cavity=True; sh.show_object_outline=True; sh.color_type='OBJECT'
plate.color=(0.20,0.60,0.95,1); scene.render.resolution_x=1600; scene.render.resolution_y=1000
cam=bpy.data.cameras.new("c"); cam.type='ORTHO'; cam.ortho_scale=230; cam.clip_end=10000
co=bpy.data.objects.new("c",cam); scene.collection.objects.link(co); scene.camera=co
co.rotation_euler=(math.radians(55),0,math.radians(35)); bpy.context.view_layer.update()
d=co.matrix_world.to_quaternion()@Vector((0,0,-1)); co.location=Vector((0,0,6))-d*800
scene.render.filepath=os.path.join(OUT,"octopus-pro-plate-iso.png"); bpy.ops.render.render(write_still=True)
co.rotation_euler=(0,0,0); co.location=(0,0,800); cam.ortho_scale=200
scene.render.filepath=os.path.join(OUT,"octopus-pro-plate-top.png"); bpy.ops.render.render(write_still=True)
print("PLATE DONE")
