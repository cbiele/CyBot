"""Phase 1 finger for the three-finger hand: proximal and distal phalanges, a bench fixture
that stands in for the palm fork, and the one-piece TPU skin. Frame per hand_lib.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hand_finger.py"""
import bpy, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
OUT = os.environ.get("HAND_OUT", os.path.join("/Users/claytonbiele/dev/Claude/Projects/cybot", "model", "hand"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
PARAMS = os.path.join(OUT, "params.json")          # measured fits from the bench, e.g. {"cheek_bore": 3.9, "core_bore": 2.0}
_params = json.load(open(PARAMS)) if os.path.exists(PARAMS) else {}
CHEEK_BORE = _params.get("cheek_bore", L.CHEEK_BORE)
TONGUE_BORE = _params.get("tongue_bore", L.TONGUE_BORE)
CORE_BORE = _params.get("core_bore", L.CORE_BORE)
PROX_LEN, DIST_LEN = 40.0, 30.0
W2, R = L.W / 2, L.R

# ---- proximal phalanx: base tongue at x=0, tip fork axis at x=PROX_LEN
prox = L.box("finger-proximal", L.TONGUE_LEN, PROX_LEN - L.FORK_LEN, -R, R, -W2, W2)
L.tongue(prox, 0.0, direction=1)
L.fork(prox, PROX_LEN)
L.bore_tongue(prox, 0.0, direction=1, d=TONGUE_BORE, d_core=CORE_BORE)
L.bore_cheeks(prox, PROX_LEN, CHEEK_BORE)
L.strip_pocket(prox, PROX_LEN - L.FORK_LEN - 2 - L.PAD_L, PROX_LEN - L.FORK_LEN - 2)
PAD_X0, PAD_X1 = 12.0, 26.0                        # snap-on grip pad on the inside of the proximal
L.snap_grooves(prox, PAD_X0, PAD_X1)
L.snap_dimples(prox, PAD_X0, PAD_X1)
# two straight enclosed channels the length of the body: the sensor pair on the axis line and the
# tendon 4 mm below it, both opening into the base tongue's pocket and out of the fork web. With
# the finger straight both run in one line from the fixture to the distal, so they can be pushed in.
WEB_X = PROX_LEN - L.FORK_LEN
L.channel(prox, 0.0, -1.0, WEB_X + 1.0, L.WIRE_D)
L.channel(prox, L.TENDON_Y, L.TENDON_MOUTH - 0.5, WEB_X + 1.0, L.TENDON_D)
L.flare(prox, 0.0, 0.0, 1, L.WIRE_D, 2.8)
L.flare(prox, L.TENDON_MOUTH, L.TENDON_Y, 1, L.TENDON_D, 4.0)
L.flare(prox, WEB_X, 0.0, -1, L.WIRE_D, 2.8)
L.flare(prox, WEB_X, L.TENDON_Y, -1, L.TENDON_D, 4.0)
L.finish(prox)

# ---- distal phalanx: base tongue at x=0, rounded tip at x=DIST_LEN. The TPU skin wraps the
# tip and covers the palmar face, so the sensor pocket, its tail cavity, the tendon anchor and
# the skin's two M2 anchor holes are all on the palmar side.
dist = L.box("finger-distal", L.TONGUE_LEN, DIST_LEN - R, -R, R, -W2, W2)
L.union(dist, L.cyl_z("tip", DIST_LEN - R, 0, R, -W2, W2))
L.tongue(dist, 0.0, direction=1)
L.bore_tongue(dist, 0.0, direction=1, d=TONGUE_BORE, d_core=CORE_BORE)
# tendon: enclosed channel from the tongue's mouth to an open pocket in the palmar face, where a
# knot or crimp too big for the channel stops against the pocket's rear wall
ANCHOR_X0, ANCHOR_X1 = 8.0, 15.5
L.channel(dist, L.TENDON_Y, L.TENDON_MOUTH - 0.5, ANCHOR_X0 + 0.5, L.TENDON_D)
L.flare(dist, L.TENDON_MOUTH, L.TENDON_Y, 1, L.TENDON_D, 4.0)
L.cut(dist, L.box("anchor_pocket", ANCHOR_X0, ANCHOR_X1, -R - 0.1, L.TENDON_Y + L.TENDON_D / 2 + 0.2, -1.5, 1.5))
# skin anchor: two M2 pilot holes on the palmar face, either side of the tendon groove
SKIN_EAR_X, SKIN_EAR_Z = 10.0, 6.0
for z in (-SKIN_EAR_Z, SKIN_EAR_Z):
    L.cut(dist, L.cyl_between("ear_pilot", (SKIN_EAR_X, -R - 1, z), (SKIN_EAR_X, -R + 4, z), 0.8))
# FSR 400 pocket on the palmar face (7.6 mm body). Its tail runs toward the tip in a 0.6 mm
# groove round the R6 end to a solder pocket at the very tip, where the wire pair comes out of
# the straight channel on the axis line; the pair is pushed in at the tip, knotted there, and
# soldered to the tail last. All of it sits under the skin's tip wrap.
SENSOR_X = 21.0
TIP_C = DIST_LEN - R                                  # centre of the rounded tip
L.cut(dist, L.cyl_between("fsr_pocket", (SENSOR_X, -R - 1, 0), (SENSOR_X, -R + 0.6, 0), 4.0))
band = L.cyl_z("tail_band", TIP_C, 0, R + 0.1, -2.5, 2.5)
L.boolean(band, L.cyl_z("band_in", TIP_C, 0, R - 0.6, -3, 3), 'DIFFERENCE')
L.boolean(band, L.box("band_clip", TIP_C, TIP_C + R + 1, -R - 1, 0.5, -3, 3), 'INTERSECT')
L.cut(dist, band)
L.cut(dist, L.cyl_between("tip_pocket", (TIP_C + 4.0, 0, 0), (TIP_C + R + 2.5, 0, 0), 2.25))
L.channel(dist, 0.0, -1.0, TIP_C + 4.5, L.WIRE_D)
L.flare(dist, 0.0, 0.0, 1, L.WIRE_D, 2.8)
L.finish(dist)

# ---- snap-on TPU grip pad for the proximal's inside face, modelled in place then exported
pad = L.snap_pad("finger-pad-proximal", PAD_X1 - PAD_X0)
pad.location.x = PAD_X0
L.finish(pad)

# ---- bench fixture: a block with the palm-side fork for the proximal base, the tendon and
# wire channels continued out of the back, a strip pocket, and a foot to clamp to the bench
fix = L.box("finger-fixture", -30, -L.FORK_LEN, -R, R, -W2, W2)
L.fork(fix, 0.0)
L.bore_cheeks(fix, 0.0, CHEEK_BORE)
# the foot stays behind the fork web so the curling finger never sweeps into it
L.union(fix, L.box("foot", -30, -L.FORK_LEN + 0.01, -R - 12, -R + 0.01, -W2 - 10, W2 + 10))
# the tendon leaves the fixture 1 mm below the finger's channel line: the span to the proximal's
# mouth then slopes less as the finger curls, so the line drags less on the exit (bench, 2026-09-24)
FIX_TENDON_Y = L.TENDON_Y - 1.0
L.channel(fix, FIX_TENDON_Y, -L.FORK_LEN + 1, -31, 2.5)
L.channel(fix, 0.0, -L.FORK_LEN + 1, -31, L.WIRE_D)
L.flare(fix, -L.FORK_LEN, 0.0, -1, L.WIRE_D, 2.8)
L.flare(fix, -L.FORK_LEN, FIX_TENDON_Y, -1, 2.5, 4.5)
L.strip_pocket(fix, -8 - 2 - L.PAD_L, -8 - 2)
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
report["tongue_bore_measured"] = L.hole_diameter(dist, 0, 0, L.PIN_GAP / 2 + 1.0)
report["core_bore_measured"] = L.hole_diameter(dist, 0, 0, (L.PIN_GAP / 2 + L.CORE_FLOOR) / 2)
report["tongue_bore_floor"] = L.bore_floor_z(dist, 1.5, 1.5, W2 + 1)   # inside the clearance bore, outside the core bore
report["core_bore_floor"] = L.bore_floor_z(dist, 0.3, 0.7, W2 + 1)     # inside the core bore, clear of the wire channel and pocket
# straight channels: a line pushed along each channel axis meets nothing until it should
report["wire_line_prox"] = L.first_hit_x(prox, 0.0, -10.0)
report["wire_line_dist"] = L.first_hit_x(dist, 0.0, -10.0)
report["tendon_line_prox"] = L.first_hit_x(prox, L.TENDON_Y, -10.0)
report["tendon_line_dist"] = L.first_hit_x(dist, L.TENDON_Y, -10.0)
report["wire_line_fix"] = L.first_hit_x(fix, 0.0, -40.0)
report["tendon_line_fix"] = L.first_hit_x(fix, FIX_TENDON_Y, -40.0)
report["skin_flat_length"] = span
report["skin_dorsal_run"] = round(DORSAL, 1); report["skin_wrap"] = round(WRAP, 1)
print("FINGER", json.dumps(report))
for name in ("finger-proximal", "finger-distal", "finger-fixture", "finger-skin", "finger-pad-proximal"):
    assert report[name]["non_manifold"] == 0, name
assert abs(report["cheek_bore_measured"] - CHEEK_BORE) < 0.02
assert abs(report["tongue_bore_measured"] - TONGUE_BORE) < 0.02
assert abs(report["core_bore_measured"] - CORE_BORE) < 0.02
assert abs(report["tongue_bore_floor"] - L.PIN_GAP / 2) < 0.05
assert abs(report["core_bore_floor"] - L.CORE_FLOOR) < 0.05
assert report["wire_line_prox"] is None and report["wire_line_fix"] is None and report["tendon_line_fix"] is None
assert report["tendon_line_prox"] is None
assert report["wire_line_dist"] is None                     # out of the tip pocket
assert abs(report["tendon_line_dist"] - ANCHOR_X1) < 0.1    # stops at the anchor pocket's end wall
