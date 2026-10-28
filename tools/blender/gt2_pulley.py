"""Printed GT2 40Ts for the compact cycloid's input, driven 2:1 from a bought 20T on a 232-2GT-6 belt.
POC: the Ø5 core rod with its flat 2.0 off the axis (cycloid_poc.ROD_FLAT); the bore takes the same D.
Hollow (axis 6): the printed sleeve's Ø7.95 tail with flats 3.675 off the axis both sides
(cycloid_poc.SLEEVE_R, SLEEVE_FLAT); the bore takes the same double-D.
The set screw runs in an M3 x 3 x 4.5 heat-set insert, as proven on the axis 2 30T (htd3m_pulley.py).
Frame: shaft axis on z, z=0 the free flange's outer face, which is the print bed face and faces the motor
mount. Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/gt2_pulley.py"""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
import mathutils
from mathutils import Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"

TEETH = 40
GROOVE_R, GROOVE_DEPTH = 0.65, 0.80                 # round groove; GT2 teeth are 0.75 high and a printed groove fills in
FLANGE_LIP = 1.0
CONE_T = 1.0                                        # hub-side flange is a 45 deg cone so it prints without support
HUB_R, HUB_L = 9.0, 7.0
SCREW_R = 1.65
INSERT_R, INSERT_DEPTH, INSERT_WALL = 2.0, 3.5, 1.0 # pilot for an M3 x 3 x 4.5 insert, pressed in radially
PULLEYS = [                                         # name, bore radius, flat offset, flat both sides
    ("cycloid-poc-pulley-40T", 2.6, 2.1, False),    # rod 5.0, 4.5 across its flat; about 0.1 clearance each
    ("cycloid-hollow-pulley-40T", 4.05, 3.725, True),   # sleeve 7.95, 7.35 across its flats; 0.05-0.075 each
]

z_teeth0 = C.GT2_FLANGE_T; z_teeth1 = z_teeth0 + C.GT2_TEETH_W
z_hub0 = z_teeth1 + CONE_T
z_top = z_hub0 + HUB_L
z_screw = (z_hub0 + z_top) / 2

def od_r():
    return TEETH * 2.0 / math.pi / 2 - 0.254        # GT2 pitch line differential

def pulley(name, bore_r, flat_x, double):
    r = od_r()
    p = L.cyl_z(name, 0, 0, r, z_teeth0 - 0.01, z_teeth1 + 0.01, n=240)
    for k in range(TEETH):
        a = 2 * math.pi * k / TEETH; c = r - GROOVE_DEPTH + GROOVE_R
        L.cut(p, L.cyl_z("groove", c * math.cos(a), c * math.sin(a), GROOVE_R, z_teeth0 - 1, z_teeth1 + 1, n=24))
    L.union(p, L.cyl_z("flange", 0, 0, r + FLANGE_LIP, 0, z_teeth0, n=240))
    L.union(p, L.cyl_between("cone", (0, 0, z_teeth1), (0, 0, z_hub0), r - GROOVE_DEPTH, n=240, r_end=r + FLANGE_LIP))
    L.union(p, L.cyl_z("hub", 0, 0, HUB_R, z_hub0 - 0.01, z_top, n=120))
    bore = L.cyl_z("bore", 0, 0, bore_r, -1, z_top + 1, n=64)
    L.cut(bore, L.box("flat", flat_x, bore_r + 1, -bore_r - 1, bore_r + 1, -2, z_top + 2))
    if double:
        L.cut(bore, L.box("flat_b", -bore_r - 1, -flat_x, -bore_r - 1, bore_r + 1, -2, z_top + 2))
    L.cut(p, bore)
    L.cut(p, L.cyl_between("insert", (HUB_R - INSERT_DEPTH, 0, z_screw), (HUB_R + 1, 0, z_screw), INSERT_R, n=48))
    L.cut(p, L.cyl_between("screw", (0, 0, z_screw), (HUB_R + 1, 0, z_screw), SCREW_R, n=32))
    L.finish(p); return p

def radial(o, z, n=1440):
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); out = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.37) / n; d = Vector((math.cos(a), math.sin(a), 0)); c = Vector((0, 0, z))
        h = tree.ray_cast(c + d * 30, -d); out.append((h[0] - c).length if h[0] is not None else None)
    bm.free(); return out

def bore_rays(o):
    """Rays out from the axis, offset from the bore's vertices: (angle in degrees, distance)."""
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); out = []
    c = Vector((0, 0, z_teeth0 + 3))
    for k in range(72):
        a = 2 * math.pi * (k + 0.5) / 72; h = tree.ray_cast(c, Vector((math.cos(a), math.sin(a), 0)))
        if h[0] is not None: out.append((round(math.degrees(a)), (h[0] - c).length))
    bm.free(); return out

def check(p, bore_r, flat_x, double):
    st = L.stats(p); r = od_r()
    prof = radial(p, (z_teeth0 + z_teeth1) / 2)
    deep = [d < r - GROOVE_DEPTH / 2 for d in prof]
    grooves = sum(1 for i in range(len(deep)) if deep[i] and not deep[i - 1])
    rays = bore_rays(p)
    far = min if double else max
    across = far(d for a, d in rays if 170 < a < 190) + min(d for a, d in rays if a < 3 or a > 357)
    report = {**st, "grooves": grooves, "od": round(2 * max(prof), 2), "root_d": round(2 * min(prof), 2),
              "bore_d": round(2 * max(d for a, d in rays), 2), "across_flat": round(across, 2), "height": z_top,
              "teeth_mid_from_flange_face": z_teeth0 + C.GT2_TEETH_W / 2}
    assert st["non_manifold"] == 0, st
    assert grooves == TEETH, grooves
    assert abs(report["od"] - 2 * r) < 0.05, report["od"]
    assert abs(report["bore_d"] - 2 * bore_r) < 0.05, report
    assert abs(across - (2 * flat_x if double else bore_r + flat_x)) < 0.05, report
    assert z_screw - INSERT_R - z_hub0 >= INSERT_WALL and z_top - z_screw - INSERT_R >= INSERT_WALL, "insert breaks out of the hub"
    assert HUB_R - INSERT_DEPTH > flat_x + 1.0, "insert pilot reaches the flat"
    return report

for name, bore_r, flat_x, double in PULLEYS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = pulley(name, bore_r, flat_x, double)
    print("PULLEY", name, json.dumps(check(p, bore_r, flat_x, double)))
    L.export(p, os.path.join(ROOT, "model", "cycloid-poc", name + ".stl"))
print("PULLEY DONE")
