"""axis4_OPH2 with its spigot turned down to fit the tube. As exported by the Cults author the
boss on OPH2's tube end is O58 and sits inside the tube's O56 socket, 1 mm too big all round.
This trims the boss to SPIGOT_D over its full length and changes nothing else: the six radial
O4 holes (M5 thread-forming, through the tube's socket wall into the boss), the axial holes, the
keyed O30 bore and the O62 shoulder that lands on the tube's end face all stay.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/oph2_spigot.py"""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import mathutils
from mathutils import Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
SRC = os.path.join(ROOT, "Cults3d_v5", "5-axis4", "axis4_OPH2.stl")
OUT = os.path.join(ROOT, "model", "axis4"); os.makedirs(OUT, exist_ok=True)
SPIGOT_D = 55.4              # 0.6 under the tube's O56 socket; about 0.3 once the socket prints small
SOCKET_D, BOSS_D = 56.0, 58.0
HOLE_Y = -38.5               # the six radial holes, 6 mm in from the tube's end face at y=-32.5

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=SRC); o = bpy.context.selected_objects[0]; o.name = "axis4_OPH2-spigot"
verts = [v.co for v in o.data.vertices]
y_end = min(v.y for v in verts)                                              # spigot end face
y_shoulder = min(v.y for v in verts if math.hypot(v.x, v.z) > BOSS_D / 2 + 0.5)   # where the O62 shoulder starts
ring = L.cyl_between("ring_out", (0, y_end - 1, 0), (0, y_shoulder + 0.05, 0), 40.0, n=128)
L.boolean(ring, L.cyl_between("ring_in", (0, y_end - 2, 0), (0, y_shoulder + 1, 0), SPIGOT_D / 2, n=256), 'DIFFERENCE')
L.cut(o, ring)
L.finish(o)

def radial(y, n=720):
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); out = []
    for k in range(n):
        a = 2 * math.pi * k / n; d = Vector((math.cos(a), 0, math.sin(a))); c = Vector((0, y, 0))
        h = tree.ray_cast(c + d * 60, -d); out.append((a, (h[0] - c).length if h[0] is not None else None))
    bm.free(); return out
st = L.stats(o)
prof = radial(-42.0); ods = [2 * r for a, r in prof if r is not None]          # a height with no holes
holes = sorted(round(math.degrees(a)) for a, r in radial(HOLE_Y) if r is not None and r < SPIGOT_D / 2 - 1)   # blind holes: the ray hits their floor
groups = []
for ang in holes:
    if groups and ang - groups[-1][-1] <= 1: groups[-1].append(ang)
    else: groups.append([ang])
report = {**st, "spigot_od": [round(min(ods), 2), round(max(ods), 2)], "spigot_len": round(y_shoulder - y_end, 2),
          "radial_holes": [(g[0], g[-1]) for g in groups], "hole_width_deg": [g[-1] - g[0] + 1 for g in groups]}
print("OPH2", json.dumps(report))
assert st["non_manifold"] == 0, st
assert abs(report["spigot_od"][0] - SPIGOT_D) < 0.05 and abs(report["spigot_od"][1] - SPIGOT_D) < 0.05, report["spigot_od"]
assert len(report["radial_holes"]) == 6, report["radial_holes"]
L.export(o, os.path.join(OUT, "axis4_OPH2-spigot.stl"))
print("OPH2 DONE")
