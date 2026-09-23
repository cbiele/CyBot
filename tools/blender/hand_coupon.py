"""Pin-fit coupons for the three-finger hand: three forks with 3.80/3.85/3.90 mm cheek bores
and three tongues with 4.1/4.2/4.3 mm bores, for ISO 8752 4 x 20 spring pins.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_coupon.py"""
import bpy, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
PITCH = 30.0
FORK_BORES = (3.80, 3.85, 3.90)
TONGUE_BORES = (4.1, 4.2, 4.3)

forks = L.box("coupon-forks", -14, PITCH * 2 + 1, -L.R, L.R, -L.W / 2, L.W / 2)   # common bar, the "web"
for i, d in enumerate(FORK_BORES):
    xa = i * PITCH
    L.fork(forks, xa)
    L.bore_cheeks(forks, xa, d)
    L.cut(forks, L.box("label", xa - 12 + 0.0, xa - 12 + 2 * (i + 1), L.R - 0.6, L.R + 0.1, 6, 8))  # i+1 notches on the dorsal face
L.finish(forks)

tongues = L.box("coupon-tongues", 1, PITCH * 2 + 13, -L.R, L.R, -L.W / 2, L.W / 2)
for i, d in enumerate(TONGUE_BORES):
    xa = i * PITCH + 7
    # a tongue pointing -x out of the bar, body side +x
    L.tongue(tongues, xa, direction=1)
    L.cut(tongues, L.cyl_z("tb", xa, 0, d / 2, -L.W, L.W))
    L.cut(tongues, L.box("label", xa + 10, xa + 10 + 2 * (i + 1), L.R - 0.6, L.R + 0.1, 6, 8))
L.finish(tongues)

report = {}
for o, bores, ys in ((forks, FORK_BORES, 7.5), (tongues, TONGUE_BORES, 0.0)):
    st = L.stats(o); measured = []
    for i, d in enumerate(bores):
        xa = i * PITCH + (0 if o is forks else 7)
        measured.append(L.hole_diameter(o, xa, 0, ys))
    report[o.name] = {**st, "bores_nominal": list(bores), "bores_measured": measured}
    L.export(o, os.path.join(OUT, o.name + ".stl"))
for name, r in report.items():
    assert r["non_manifold"] == 0, name
    for nom, meas in zip(r["bores_nominal"], r["bores_measured"]):
        assert abs(nom - meas) < 0.02, (name, nom, meas)
print("COUPON", json.dumps(report))
