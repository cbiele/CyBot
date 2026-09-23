"""Phase 1 finger for the three-finger hand: proximal and distal phalanges, a bench fixture
that stands in for the palm fork, and the one-piece TPU skin. Frame per hand_lib.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_finger.py"""
import bpy, os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
PARAMS = os.path.join(OUT, "params.json")          # written after the coupon test: {"cheek_bore": 3.85}
CHEEK_BORE = json.load(open(PARAMS))["cheek_bore"] if os.path.exists(PARAMS) else L.CHEEK_BORE
PROX_LEN, DIST_LEN = 40.0, 30.0
W2, R = L.W / 2, L.R

# ---- proximal phalanx: base tongue at x=0, tip fork axis at x=PROX_LEN
prox = L.box("finger-proximal", L.TONGUE_LEN, PROX_LEN - L.FORK_LEN, -R, R, -W2, W2)
L.tongue(prox, 0.0, direction=1)
L.fork(prox, PROX_LEN)
L.bore_tongue(prox, 0.0, direction=1)
L.bore_cheeks(prox, PROX_LEN, CHEEK_BORE)
L.tendon_groove(prox, 0.0, PROX_LEN - L.FORK_LEN + 0.1)
L.strip_pocket(prox, PROX_LEN - L.FORK_LEN - 2 - L.PAD_L, PROX_LEN - L.FORK_LEN - 2)
PAD_X0, PAD_X1 = 12.0, 26.0                        # snap-on grip pad on the inside of the proximal
L.snap_grooves(prox, PAD_X0, PAD_X1)
L.snap_dimples(prox, PAD_X0, PAD_X1)
# wire: external groove on the +z face from the tip pin end back 12 mm, then a channel
# diving to the base chamber
L.cut(prox, L.box("wire_groove", PROX_LEN - 12, PROX_LEN + 0.1, -L.WIRE_D / 2, L.WIRE_D / 2, W2 - L.WIRE_D, W2 + 0.1))
L.cut(prox, L.cyl_between("wire_dive", (PROX_LEN - 12, 0, W2 - L.WIRE_D / 2), (L.TONGUE_LEN - 2, 0, 0), L.WIRE_D / 2))
L.finish(prox)

# ---- distal phalanx: base tongue at x=0, rounded tip at x=DIST_LEN. The TPU skin wraps the
# tip and covers the palmar face, so the sensor pocket, its tail cavity and the skin's two
# M2 anchor holes are on the palmar side; the tendon anchors just past the knuckle.
dist = L.box("finger-distal", L.TONGUE_LEN, DIST_LEN - R, -R, R, -W2, W2)
L.union(dist, L.cyl_z("tip", DIST_LEN - R, 0, R, -W2, W2))
L.tongue(dist, 0.0, direction=1)
L.bore_tongue(dist, 0.0, direction=1)
TENDON_ANCHOR_X = 14.0
L.tendon_groove(dist, 0.0, TENDON_ANCHOR_X + 1.0)
L.cut(dist, L.cyl_between("anchor_hole", (TENDON_ANCHOR_X, -R - 1, 0), (TENDON_ANCHOR_X, R + 1, 0), 0.75))
L.cut(dist, L.box("ferrule", TENDON_ANCHOR_X - 1.5, TENDON_ANCHOR_X + 1.5, R - 2.0, R + 0.5, -1.5, 1.5))
# skin anchor: two M2 pilot holes on the palmar face, either side of the tendon groove
SKIN_EAR_X, SKIN_EAR_Z = 10.0, 6.0
for z in (-SKIN_EAR_Z, SKIN_EAR_Z):
    L.cut(dist, L.cyl_between("ear_pilot", (SKIN_EAR_X, -R - 1, z), (SKIN_EAR_X, -R + 4, z), 0.8))
# FSR 400 pocket on the palmar face (7.6 mm body), tail slot up into a solder cavity, and the
# wire channel from that cavity to the tongue chamber, offset in z to miss the tendon hole
SENSOR_X = 21.0
L.cut(dist, L.cyl_between("fsr_pocket", (SENSOR_X, -R - 1, 0), (SENSOR_X, -R + 0.6, 0), 4.0))
L.cut(dist, L.box("tail_slot", SENSOR_X - 4.5, SENSOR_X - 3.0, -R + 0.5, -R + 1.6, -2.0, 2.0))
L.cut(dist, L.box("solder_cavity", SENSOR_X - 4.5, SENSOR_X + 3.5, -R + 1.5, -R + 4.5, -2.5, 2.5))
L.cut(dist, L.cyl_between("wire_run", (SENSOR_X - 4.0, -R + 3.0, 2.5), (L.TONGUE_LEN - 2.0, 0.0, 1.5), L.WIRE_D / 2))
L.finish(dist)

# ---- snap-on TPU grip pad for the proximal's inside face, modelled in place then exported
pad = L.snap_pad("finger-pad-proximal", PAD_X1 - PAD_X0)
pad.location.x = PAD_X0
L.finish(pad)

# ---- bench fixture: a block with the palm-side fork for the proximal base, a tendon exit
# hole, a strip pocket, and a foot to clamp to the bench
fix = L.box("finger-fixture", -30, -L.FORK_LEN, -R, R, -W2, W2)
L.fork(fix, 0.0)
L.bore_cheeks(fix, 0.0, CHEEK_BORE)
# the foot stays behind the fork (x <= -8.5) so the curling finger never sweeps into it
L.union(fix, L.box("foot", -30, -8.5, -R - 12, -R + 0.01, -W2 - 10, W2 + 10))
L.cut(fix, L.cyl_between("tendon_exit", (-8, -R + 1, 0), (-31, -R + 1, 0), 1.5))
L.strip_pocket(fix, -8 - 2 - L.PAD_L, -8 - 2)
L.cut(fix, L.box("wire_groove", -30.1, 0.1, -L.WIRE_D / 2, L.WIRE_D / 2, W2 - L.WIRE_D, W2 + 0.1))
for x in (-24, -14):
    for z in (-W2 - 5, W2 + 5):
        L.cut(fix, L.cyl_between("clamp", (x, -R - 12.1, z), (x, -R + 0.1, z), 2.2))
L.finish(fix)

# ---- TPU skin: one flat part. Dorsal run (return spring) from the fixture pocket over both
# knuckles to the start of the tip round, then the wrap around the R6 tip, then the palmar pad
# over the sensor with a moulded dome, ending in a T bar with two M2 holes. Printed flat.
TIP_START = PROX_LEN + DIST_LEN - R                    # world x where the tip round begins
DORSAL = TIP_START - (-8 - 2 - L.PAD_L)                # fixture pad start to tip start
WRAP = math.pi * (R + L.STRIP_T / 2)                    # half circumference at mid-thickness
PAD_W, PAD_END = 14.0, TIP_START - (PROX_LEN + SKIN_EAR_X)   # pad runs back to the ears
T_W, T_L = 20.0, 4.0
x_wrap0, x_pad0 = DORSAL, DORSAL + WRAP
skin = L.box("finger-skin", 0, x_wrap0, 0, L.STRIP_T - 0.2, -L.STRIP_W / 2, L.STRIP_W / 2)
L.union(skin, L.box("wrap", x_wrap0 - 0.01, x_pad0 + 0.01, 0, L.STRIP_T - 0.2, -PAD_W / 2, PAD_W / 2))
L.union(skin, L.box("pad", x_pad0 - 0.01, x_pad0 + PAD_END, 0, L.STRIP_T - 0.2, -PAD_W / 2, PAD_W / 2))
L.union(skin, L.box("tbar", x_pad0 + PAD_END - T_L, x_pad0 + PAD_END, 0, L.STRIP_T - 0.2, -T_W / 2, T_W / 2))
dome_x = x_pad0 + (TIP_START - (PROX_LEN + SENSOR_X))   # over the sensor centre
L.union(skin, L.cyl_between("dome", (dome_x, -0.01, 0), (dome_x, -1.5, 0), 2.5, n=48))   # bump on the inside face
for z in (-SKIN_EAR_Z, SKIN_EAR_Z):
    L.cut(skin, L.cyl_between("ear_hole", (x_pad0 + PAD_END - T_L / 2, -2, z), (x_pad0 + PAD_END - T_L / 2, 3, z), 1.1))
L.finish(skin)
span = round(x_pad0 + PAD_END, 1)

report = {}
for o in (prox, dist, fix, skin, pad):
    report[o.name] = L.stats(o); L.export(o, os.path.join(OUT, o.name + ".stl"))
report["cheek_bore_measured"] = L.hole_diameter(prox, PROX_LEN, 0, 7.5)
report["tongue_bore_measured"] = L.hole_diameter(dist, 0, 0, 3.5)
report["skin_flat_length"] = span
report["skin_dorsal_run"] = round(DORSAL, 1); report["skin_wrap"] = round(WRAP, 1)
for name in ("finger-proximal", "finger-distal", "finger-fixture", "finger-skin", "finger-pad-proximal"):
    assert report[name]["non_manifold"] == 0, name
assert abs(report["cheek_bore_measured"] - CHEEK_BORE) < 0.02
assert abs(report["tongue_bore_measured"] - L.TONGUE_BORE) < 0.02
print("FINGER", json.dumps(report))
