"""Ring pin coupon for M2.5 x 20 roll pins in the compact cycloid's housings: a press block (the rear half's holes)
and a slip block (the front half's), each with three sizes, small to large from the notched end. The holes copy the
housing's: blind, opening up from the mating face as the halves print, 10 and 12 deep, 24-gons. The pitch matches
across the blocks, so pins pressed into the press block can take the slip block over them as in the housing.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/ring_pin_coupon.py"""
import bpy, math, os, sys, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "cycloid-poc", "test-parts")

PRESS, SLIP = (2.30, 2.40, 2.50), (2.60, 2.70, 2.80)
PRESS_DEPTH, SLIP_DEPTH, FLOOR = 10.0, 12.0, 2.0     # the housing's: half the 20 mm pin, and half plus 2 so the halves close
PITCH, END, WIDTH = 8.0, 5.0, 10.0
POLY = 24                                            # the housing's ring pin holes are 24-gons


def block(name, sizes, depth):
    top = depth + FLOOR
    b = L.box(name, 0, 2 * END + PITCH * (len(sizes) - 1), 0, WIDTH, 0, top)
    for j, d in enumerate(sizes):
        L.cut(b, L.cyl_z("pin", END + j * PITCH, WIDTH / 2, d / 2, FLOOR, top + 1, n=POLY))
    L.cut(b, L.box("notch", -1, 1.0, WIDTH / 2 - 1.5, WIDTH / 2 + 1.5, -1, top + 1))
    L.finish(b)
    return b


def bore_diameter(o, x, y, z):
    """Median of 72 rays, half a step off the 24-gon's vertices (cycloid_coupon's; importing it would run that script)."""
    tree, bm = L._tree(o); ds = []
    for k in range(72):
        a = 2 * math.pi * (k + 0.5) / 72
        h = tree.ray_cast(Vector((x, y, z)), Vector((math.cos(a), math.sin(a), 0)))
        if h[0] is not None:
            ds.append((h[0] - Vector((x, y, z))).length)
    bm.free()
    return round(2 * sorted(ds)[len(ds) // 2], 3)


def check(b, sizes, depth):
    st = L.stats(b)
    assert st["non_manifold"] == 0, st
    for j, d in enumerate(sizes):
        x = END + j * PITCH
        got = bore_diameter(b, x, WIDTH / 2, FLOOR + depth / 2)
        assert d * math.cos(math.pi / POLY) - 0.01 <= got <= d + 0.01, (b.name, d, got)
        assert abs(L.bore_floor_z(b, x, WIDTH / 2, FLOOR + depth - 0.5) - FLOOR) < 0.01, (b.name, d, "floor")
    return st


press = block("ring-pin-coupon-press", PRESS, PRESS_DEPTH)
slip = block("ring-pin-coupon-slip", SLIP, SLIP_DEPTH)
print("RING PIN COUPON", json.dumps({"press": check(press, PRESS, PRESS_DEPTH), "slip": check(slip, SLIP, SLIP_DEPTH)}))
for o in (press, slip):
    L.export(o, os.path.join(OUT, o.name + ".stl"))
print("RING PIN COUPON DONE")
