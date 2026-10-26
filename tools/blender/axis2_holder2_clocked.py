"""axis2-holder2 with its six M4 rod holes clocked 30 deg so one sits at 12 o'clock, and the nut
recesses on the back widened so a socket reaches the nut. As exported by the Cults author the holes
are O4 on R28.5 about the bore at 0/60/.. deg (3 and 9 o'clock) with an O8 x 4 recess from the back
face, which an M4 nut (8.1 across corners) only just enters. The old holes are filled and recut;
nothing else changes. Frame as exported: bore axis along y at x=0, z=203; boss face y=33, back face y=49.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/axis2_holder2_clocked.py"""
import bpy, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
SRC = os.path.join(ROOT, "Cults3d_v5", "3-axis2", "axis2-holder2.stl")
OUT = os.path.join(ROOT, "model", "axis2"); os.makedirs(OUT, exist_ok=True)
AX_X, AX_Z = 0.0, 203.0
Y_BOSS, Y_RECESS, Y_BACK = 33.0, 45.0, 49.0
PCD_R, HOLE_D = 28.5, 4.0
OLD_ANGLES = [60 * k for k in range(6)]
NEW_ANGLES = [90 + 60 * k for k in range(6)]
OLD_RECESS_D = 8.0
RECESS_D = 12.5              # 7 mm socket for the M4 nut is about 10-11 OD, plus print shrink
FLUSH_GAP = 0.06

def at(deg):
    a = math.radians(deg); return AX_X + PCD_R * math.cos(a), AX_Z + PCD_R * math.sin(a)

def along_y(name, x, z, r, y0, y1, n=64):
    return L.cyl_between(name, (x, y0, z), (x, y1, z), r, n=n)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=SRC); o = bpy.context.selected_objects[0]; o.name = "axis2-holder2-clocked"
for deg in OLD_ANGLES:
    x, z = at(deg)
    # plugs stop FLUSH_GAP short of the faces: flush caps leave coplanar slivers that break the exact boolean
    L.union(o, along_y("fill", x, z, HOLE_D / 2 + 0.5, Y_BOSS + FLUSH_GAP, Y_RECESS + 0.5))
    L.union(o, along_y("fill_recess", x, z, OLD_RECESS_D / 2 + 0.5, Y_RECESS - 0.5, Y_BACK - FLUSH_GAP))
for deg in NEW_ANGLES:
    x, z = at(deg)
    L.cut(o, along_y("hole", x, z, HOLE_D / 2, Y_BOSS - 1, Y_BACK + 1))
    L.cut(o, along_y("recess", x, z, RECESS_D / 2, Y_RECESS, Y_BACK + 1, n=96))
L.finish(o)

def open_at(x, y, z):
    """True if the point is outside the material: the nearest face's normal points toward it."""
    import bmesh, mathutils
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    loc, nor, i, d = tree.find_nearest(mathutils.Vector((x, y, z))); bm.free()
    return (mathutils.Vector((x, y, z)) - loc).dot(nor) > 0

st = L.stats(o)
checks = {}
for deg in NEW_ANGLES:
    x, z = at(deg)
    checks[f"new{deg}"] = [open_at(x, y, z) for y in (Y_BOSS + 1, 41.0, Y_RECESS + 2)] + \
        [open_at(x + (RECESS_D / 2 - 0.3), Y_RECESS + 2, z), not open_at(x + (RECESS_D / 2 + 0.3), Y_RECESS + 2, z),
         not open_at(x + (RECESS_D / 2 - 0.3), Y_RECESS - 0.5, z)]
for deg in OLD_ANGLES:
    x, z = at(deg)
    checks[f"old{deg}"] = [not open_at(x, y, z) for y in (Y_BOSS + 1, 41.0, Y_BACK - 1)]
print("HOLDER2", json.dumps({**st, "checks_ok": all(all(v) for v in checks.values())}))
assert st["non_manifold"] == 0, st
assert all(all(v) for v in checks.values()), checks
L.export(o, os.path.join(OUT, "axis2-holder2-clocked.stl"))
print("HOLDER2 DONE")
