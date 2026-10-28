"""Fit coupon for the compact cycloid POC: a plate with one row of holes per press fit and a strip of
pegs for the bearing bores, each in three sizes (left to right: nominal - 0.1, nominal, nominal + 0.1;
one notch on the plate's left edge marks the -0.1 end). The print picks the diameters in
model/cycloid-poc/params.json.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_coupon.py"""
import bpy, bmesh, math, os, sys, json
import mathutils
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
BASE = os.path.join(ROOT, "model", "cycloid-poc")
OUT = os.path.join(BASE, "test-parts")
P = json.load(open(os.path.join(BASE, "params.json")))
STEPS = (-0.1, 0.0, 0.1)
HOLES = ["seat_6804", "seat_6800", "seat_625", "seat_bushing", "ring_pin_press", "ring_pin_slip", "out_pin_press", "rod_bore"]
PEGS = ["hub_6804", "journal_6800"]
PLATE_T, PEG_H, BASE_T, GAP = 7.0, 6.0, 3.0, 4.0
ROD_FLAT = 2.0                                       # the rod's flat sits 2.0 from its axis

def bore_diameter(o, x, y, z):
    """Median of 72 rays out from (x, y, z). The rays sit half a step off the cylinder's vertices:
    hand_lib.hole_diameter's 24 rays land on vertices of a 96-gon and some slip through the cracks."""
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); ds = []
    for k in range(72):
        a = 2 * math.pi * (k + 0.5) / 72
        h = tree.ray_cast(Vector((x, y, z)), Vector((math.cos(a), math.sin(a), 0)))
        if h[0] is not None: ds.append((h[0] - Vector((x, y, z))).length)
    bm.free(); return round(2 * sorted(ds)[len(ds) // 2], 3)

def rows(keys):
    """(key, diameter, x, y) for every size, rows stacked along y."""
    out, y = [], 0.0
    for k in keys:
        d_max = P[k] + max(STEPS); y += d_max / 2 + GAP
        for j, s in enumerate(STEPS):
            out.append((k, P[k] + s, GAP + d_max / 2 + j * (d_max + GAP), y))
        y += d_max / 2
    return out, y + GAP

def hole_plate():
    holes, y_top = rows(HOLES)
    x_max = max(x + d / 2 for k, d, x, y in holes) + GAP
    p = L.box("fit-coupon-holes", 0, x_max, 0, y_top, 0, PLATE_T)
    for k, d, x, y in holes:
        c = L.cyl_z("hole", x, y, d / 2, -1, PLATE_T + 1, n=96)
        if k == "rod_bore":
            L.cut(c, L.box("flat", x + ROD_FLAT, x + d, y - d, y + d, -2, PLATE_T + 2))
        L.cut(p, c)
    L.cut(p, L.box("notch", -1, 1.5, y_top / 2 - 1.5, y_top / 2 + 1.5, -1, PLATE_T + 1))
    L.finish(p); return p, holes

def peg_strip():
    pegs, y_top = rows(PEGS)
    x_max = max(x + d / 2 for k, d, x, y in pegs) + GAP
    s = L.box("fit-coupon-pegs", 0, x_max, 0, y_top, 0, BASE_T)
    for k, d, x, y in pegs:
        L.union(s, L.cyl_z("peg", x, y, d / 2, BASE_T - 0.01, BASE_T + PEG_H, n=96))
    L.cut(s, L.box("notch", -1, 1.5, y_top / 2 - 1.5, y_top / 2 + 1.5, -1, BASE_T + 1))
    L.finish(s); return s

bpy.ops.wm.read_factory_settings(use_empty=True)
plate, holes = hole_plate()
st = L.stats(plate); assert st["non_manifold"] == 0, st
for k, d, x, y in holes:
    if k == "rod_bore":
        continue
    got = bore_diameter(plate, x, y, PLATE_T / 2)
    assert abs(got - d) < 0.03, (k, d, got)
strip = peg_strip()
st2 = L.stats(strip); assert st2["non_manifold"] == 0, st2
print("COUPON", json.dumps({"holes": st, "pegs": st2}))
L.export(plate, os.path.join(OUT, "fit-coupon-holes.stl"))
L.export(strip, os.path.join(OUT, "fit-coupon-pegs.stl"))
print("COUPON DONE")
