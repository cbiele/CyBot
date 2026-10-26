"""Printed HTD 3M motor pulleys, in place of bought ones.
axis1: 27T for the spider base (spec §5.3). The motor hangs upside down from the bracket plate, whose
underside is 48 above the ring top; the shaft is 20 long with a D flat 4.0 across, so its tip is at
about 33 and the pulley's lower teeth and flange hang past it. 27 not 30: the round pilot hole fixed
the motor and the 621 belt was tight at 30. Ring-top height = z + Z_MOUNT.
axis2: 30T on the shoulder NEMA23's 6.35 shaft, replacing a GT2 30T that had been driving the 3M
belt and skipped under load. A round bore spun on the shaft, so the bore has the shaft's D flat and
the set screw runs in an M3 x 3 x 4.5 heat-set insert, on a hub long enough to wall the insert in.
Frame: shaft axis on z, z=0 the free flange's outer face, which is the print bed face.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/htd3m_pulley.py"""
import bpy, bmesh, math, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import mathutils
from mathutils import Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"

PITCH = 3.0
GROOVE_R, GROOVE_DEPTH = 1.05, 1.30                 # round groove; a printed groove fills in, so it errs wide
FLANGE_T, FLANGE_LIP = 1.5, 1.5
TEETH_W = 11.5                                      # 10 mm belt
CONE_T = 1.5                                        # hub-side flange is a 45 deg cone so it prints without support
HUB_R = 9.0
NUT_W, NUT_X0, NUT_X1 = 5.8, 4.0, 6.6               # M3 nut slot, open at the hub's top, the screw bears on the flat
SCREW_R = 1.65
INSERT_R, INSERT_DEPTH, INSERT_WALL = 2.0, 3.5, 1.0 # pilot for an M3 x 3 x 4.5 insert, pressed in radially
Z_MOUNT = 28.25                                     # axis1: teeth at 29.75-41.25 on the 30-41 band, hub top 0.5 under the plate
PULLEYS = [                                         # name, teeth, bore radius, flat offset, hub length, insert, folder
    ("axis1-pulley-27T", 27, 2.6, 1.6, 4.75, False, "base"),    # O5 D shaft, 4.0 across the flat, about 0.1 clearance each
    ("axis2-pulley-30T", 30, 3.275, 2.675, 7.0, True, "axis2"), # O6.35 D shaft, 5.85 across the flat
]

z_teeth0 = FLANGE_T; z_teeth1 = z_teeth0 + TEETH_W
z_hub0 = z_teeth1 + CONE_T

def hub_z(hub_l, insert):
    """Hub top and set screw height."""
    z_top = z_hub0 + hub_l
    return z_top, (z_hub0 + z_top) / 2 if insert else z_top - 2.25

def od_r(teeth):
    return teeth * PITCH / math.pi / 2 - 0.381       # HTD 3M pitch line differential

def pulley(name, teeth, bore_r, flat_x, hub_l, insert):
    r = od_r(teeth); z_top, z_screw = hub_z(hub_l, insert)
    p = L.cyl_z(name, 0, 0, r, z_teeth0 - 0.01, z_teeth1 + 0.01, n=180)
    for k in range(teeth):
        a = 2 * math.pi * k / teeth; c = r - GROOVE_DEPTH + GROOVE_R
        L.cut(p, L.cyl_z("groove", c * math.cos(a), c * math.sin(a), GROOVE_R, z_teeth0 - 1, z_teeth1 + 1, n=32))
    L.union(p, L.cyl_z("flange", 0, 0, r + FLANGE_LIP, 0, z_teeth0, n=180))
    L.union(p, L.cyl_between("cone", (0, 0, z_teeth1), (0, 0, z_hub0), r - GROOVE_DEPTH, n=180, r_end=r + FLANGE_LIP))
    L.union(p, L.cyl_z("hub", 0, 0, HUB_R, z_hub0 - 0.01, z_top, n=120))
    bore = L.cyl_z("bore", 0, 0, bore_r, -1, z_top + 1, n=64)
    if flat_x is not None:
        L.cut(bore, L.box("flat", flat_x, bore_r + 1, -bore_r - 1, bore_r + 1, -2, z_top + 2))
    L.cut(p, bore)
    if insert:
        L.cut(p, L.cyl_between("insert", (HUB_R - INSERT_DEPTH, 0, z_screw), (HUB_R + 1, 0, z_screw), INSERT_R, n=48))
    else:
        L.cut(p, L.box("nut", NUT_X0, NUT_X1, -NUT_W / 2, NUT_W / 2, z_screw - NUT_W / 2 - 0.2, z_top + 1))
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

def check(p, teeth, bore_r, flat_x):
    st = L.stats(p); r = od_r(teeth)
    prof = radial(p, (z_teeth0 + z_teeth1) / 2)
    deep = [d < r - GROOVE_DEPTH / 2 for d in prof]
    grooves = sum(1 for i in range(len(deep)) if deep[i] and not deep[i - 1])
    rays = bore_rays(p)
    report = {**st, "grooves": grooves, "od": round(2 * max(prof), 2), "root_d": round(2 * min(prof), 2),
              "bore_d": round(2 * max(d for a, d in rays), 2)}
    assert st["non_manifold"] == 0, st
    assert grooves == teeth, grooves
    assert abs(report["od"] - 2 * r) < 0.05, report["od"]
    assert abs(report["bore_d"] - 2 * bore_r) < 0.05, report
    if flat_x is not None:
        across = max(d for a, d in rays if 170 < a < 190) + min(d for a, d in rays if a < 3 or a > 357)
        report["across_flat"] = round(across, 2)
        assert abs(across - (bore_r + flat_x)) < 0.05, report
    else:
        assert max(d for a, d in rays) - min(d for a, d in rays) < 0.05, "round bore is not round"
    return report

for name, teeth, bore_r, flat_x, hub_l, insert, folder in PULLEYS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = pulley(name, teeth, bore_r, flat_x, hub_l, insert)
    report = check(p, teeth, bore_r, flat_x)
    z_top, z_screw = hub_z(hub_l, insert); report["height"] = z_top
    if insert:
        assert z_screw - INSERT_R - z_hub0 >= INSERT_WALL and z_top - z_screw - INSERT_R >= INSERT_WALL, "insert breaks out of the hub"
        assert HUB_R - INSERT_DEPTH > flat_x + 1.0, "insert pilot reaches the flat"
    if name.startswith("axis1"):
        report.update({"teeth_on_band": [round(z_teeth0 + Z_MOUNT, 2), round(z_teeth1 + Z_MOUNT, 2)],
                       "hub_top_on_band": round(z_top + Z_MOUNT, 2)})
        assert z_top + Z_MOUNT <= 48.0 - 0.5, "hub hits the bracket plate"
        assert z_screw - 1.6 > 33.0 - Z_MOUNT, "set screw below the shaft tip"
    print("PULLEY", name, json.dumps(report))
    out = os.path.join(ROOT, "model", folder); os.makedirs(out, exist_ok=True)
    L.export(p, os.path.join(out, name + ".stl"))
print("PULLEY DONE")
