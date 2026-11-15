"""Printed Tr8x2 test collars: can this printer make a thread that runs on the T8 screw?
Three clearances, marked with 1, 2 or 3 dimples on the top face. Print axis vertical, bed face z=0.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/t8_collar.py"""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import mathutils
from mathutils import Vector
OUT = "/Users/claytonbiele/dev/Claude/Projects/cybot/model/cycloid-poc/test-parts"

PITCH, R_PITCH = 2.0, 3.5                  # Tr8x2: 7 mm pitch diameter, 1 start, right hand
TAN_FLANK = math.tan(math.radians(15))
HEX_AF, HEIGHT = 16.0, 12.0
LEAD_IN = 0.8
CLEARANCES = [0.2, 0.3, 0.4]               # holes print about 0.15 small per side, leaving about 0.05, 0.15, 0.25
SEGMENTS, DZ = 96, 0.05                    # 96 puts the six hex corners on vertices
RIDGE_RAISE = 0.2                          # above the standard nut's R3.0: a thicker ridge tip matters more than full engagement
MIN_RIDGE_TIP = 0.2

def groove_half_width(r, c):
    return 0.5 + c / math.cos(math.radians(15)) - (r - R_PITCH) * TAN_FLANK

def r_minor(c): return R_PITCH - 0.5 + RIDGE_RAISE + c
def r_major(c): return 4.25 + c

def bore_r(a, z, c):
    """Bore radius at angle a, height z: the Tr profile running up a right-hand helix, opened by a lead-in cone at each face."""
    u = (z / PITCH - a / (2 * math.pi)) % 1
    off_centre = min(u, 1 - u) * PITCH
    thread = R_PITCH + (groove_half_width(R_PITCH, c) - off_centre) / TAN_FLANK
    thread = max(r_minor(c), min(r_major(c), thread))
    r_mouth = r_major(c) + 0.1
    slope = (r_mouth - r_minor(c)) / LEAD_IN
    return max(thread, r_mouth - slope * min(z, HEIGHT - z))

def hex_r(a):
    sector = math.radians(60)
    return HEX_AF / 2 / math.cos((a + sector / 2) % sector - sector / 2)

def threaded_hex(name, c):
    """Built vertex by vertex: Blender's exact boolean left stray sheets when cutting a helix tool."""
    rows = round(HEIGHT / DZ)
    angles = [2 * math.pi * i / SEGMENTS for i in range(SEGMENTS)]
    bm = bmesh.new()
    point = lambda a, r, z: bm.verts.new((r * math.cos(a), r * math.sin(a), z))
    bore = [[point(a, bore_r(a, DZ * j, c), DZ * j) for a in angles] for j in range(rows + 1)]
    outer = [[point(a, hex_r(a), z) for a in angles] for z in (0.0, HEIGHT)]
    def band(lo, hi):
        for i in range(SEGMENTS):
            k = (i + 1) % SEGMENTS
            bm.faces.new((lo[i], lo[k], hi[k])); bm.faces.new((lo[i], hi[k], hi[i]))
    for lo, hi in zip(bore, bore[1:]): band(lo, hi)
    band(outer[0], outer[1]); band(bore[0], outer[0]); band(bore[-1], outer[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)

def collar(name, c, dimples):
    body = threaded_hex(name, c)
    for k in range(dimples):
        a = math.radians(30 + 60 * k)
        L.cut(body, L.cyl_z("dimple", 6.4 * math.cos(a), 6.4 * math.sin(a), 0.7, HEIGHT - 0.6, HEIGHT + 1, n=24))
    L.finish(body); return body

def bore_radius_along_z(o, angle):
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    d = Vector((math.cos(angle), math.sin(angle), 0)); out = []
    for k in range(int((HEIGHT - 4) / 0.005)):
        z = 2 + k * 0.005
        out.append((z, tree.ray_cast(Vector((0, 0, z)), d)[0].to_2d().length))
    bm.free(); return out

def groove_spans(profile, r):
    """Each (start z, end z) where the bore is wider than r."""
    spans = []; start = None
    for z, d in profile:
        if d > r and start is None: start = z
        if d <= r and start is not None: spans.append((start, z)); start = None
    return spans[1:]                       # the scan may begin mid-groove

def check(o, c):
    st = L.stats(o)
    p0 = bore_radius_along_z(o, 0.01); p90 = bore_radius_along_z(o, 0.01 + math.pi / 2)
    r_probe = 3.8
    s0, s90 = groove_spans(p0, r_probe), groove_spans(p90, r_probe)
    centre = lambda s: (s[0] + s[1]) / 2
    pitch = (centre(s0[-1]) - centre(s0[0])) / (len(s0) - 1)
    width = s0[0][1] - s0[0][0]
    shift = (centre(s90[0]) - centre(s0[0])) % PITCH     # +PITCH/4 only on a right-hand thread
    tip = PITCH - 2 * groove_half_width(r_minor(c), c)
    report = {**st, "clearance": c, "minor_d": round(2 * min(d for _, d in p0), 3), "major_d": round(2 * max(d for _, d in p0), 3),
              "pitch": round(pitch, 3), "groove_width_at_r3.8": round(width, 3), "quarter_turn_shift": round(shift, 3),
              "ridge_tip": round(tip, 3), "radial_overlap_on_8mm_crest": round(4 - r_minor(c), 3)}
    assert st["non_manifold"] == 0, report
    assert abs(report["minor_d"] - 2 * r_minor(c)) < 0.03, report
    assert abs(report["major_d"] - 2 * r_major(c)) < 0.03, report
    assert abs(pitch - PITCH) < 0.01, report
    assert abs(width - 2 * groove_half_width(r_probe, c)) < 0.03, report
    assert abs(shift - PITCH / 4) < 0.02, report
    assert tip >= MIN_RIDGE_TIP, report
    return report

for i, c in enumerate(CLEARANCES):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    name = "t8-collar-c%02d" % round(c * 100)
    o = collar(name, c, i + 1)
    print("COLLAR", name, json.dumps(check(o, c)))
    L.export(o, os.path.join(OUT, name + ".stl"))
print("COLLAR DONE")
