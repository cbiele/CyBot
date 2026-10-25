"""Compact cycloid POC (docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md): 1:20 on 6804s.
Assembly frame: axis on z, z=0 the housing's rear face, input angle measured from +x; disk A (rear) on the
journal towards +x. Parts are built in the assembly frame, checked, posed at four input angles for
collisions, then exported in print orientation to model/cycloid-poc/.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/cycloid_poc.py"""
import bpy, bmesh, math, os, sys, json
import mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_lib as L
import cycloid_math as C
from mathutils import Matrix, Vector
ROOT = "/Users/claytonbiele/dev/Claude/Projects/cybot"
OUT = os.path.join(ROOT, "model", "cycloid-poc")
P = json.load(open(os.path.join(OUT, "params.json")))

LIP_T, BRG_W, SHOULDER_T, PLATE_T, GAP, DISK_T, COLLAR_T = 0.8, 7.0, 0.5, 4.0, 0.5, 6.0, 1.0
B625_W = 5.0
END_R, COLLAR_R = 3.8, 6.0                   # eccentric ends pass the 6800 bore at 1 mm offset, 0.2 to spare
ROD_R, ROD_FLAT = 2.5, 2.0                   # the steel rod; its flat is 0.5 deep. Walls count from the steel, not the bore's clearance
DOT_R, DOT_DEPTH, DOT_PCD_R = 1.0, 0.4, 12.0 # locator dots: one on disk A, two on disk B
Z_DISK0 = LIP_T + BRG_W + SHOULDER_T + PLATE_T + GAP
Z_MID = Z_DISK0 + DISK_T + COLLAR_T / 2
L_HOUSING = 2 * Z_MID
PARTS, CHECKS = {}, []

def prism(name, pts, z0, z1):
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z0)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L._obj(name, bm)

def bore_diameter(o, x, y, z):
    """Median of 72 rays out from (x, y, z), half a step off the polygon's vertices (hand_lib.hole_diameter's
    rays land on vertices and some slip through)."""
    bm = bmesh.new(); bm.from_mesh(o.data); tree = mathutils.bvhtree.BVHTree.FromBMesh(bm); ds = []
    for k in range(72):
        a = 2 * math.pi * (k + 0.5) / 72
        h = tree.ray_cast(Vector((x, y, z)), Vector((math.cos(a), math.sin(a), 0)))
        if h[0] is not None: ds.append((h[0] - Vector((x, y, z))).length)
    bm.free(); return round(2 * sorted(ds)[len(ds) // 2], 3)

def copy(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c); return c

def disk(name, phase, dots):
    d = prism(name, C.profile(720, phase), 0, DISK_T)
    L.cut(d, L.cyl_z("6800", 0, 0, P["seat_6800"] / 2, -1, DISK_T + 1, n=96))
    for k in range(C.N_OUT):
        a = 2 * math.pi * k / C.N_OUT
        L.cut(d, L.cyl_z("bushing", C.OUT_PCD_R * math.cos(a), C.OUT_PCD_R * math.sin(a), P["seat_bushing"] / 2, -1, DISK_T + 1, n=64))
    for j in range(dots):
        a = math.radians(30 + 10 * j)        # between two bushing seats
        L.cut(d, L.cyl_z("dot", DOT_PCD_R * math.cos(a), DOT_PCD_R * math.sin(a), DOT_R, DISK_T - DOT_DEPTH, DISK_T + 1, n=24))
    L.finish(d); return d

def eccentric():
    jr = P["journal_6800"] / 2
    za0, za1 = Z_DISK0, Z_DISK0 + DISK_T
    zb0, zb1 = za1 + COLLAR_T, za1 + COLLAR_T + DISK_T
    b = L.cyl_z("eccentric", 0, 0, END_R, Z_DISK0 - GAP, zb1 + GAP, n=96)
    L.union(b, L.cyl_z("journal_a", C.E, 0, jr, za0, za1, n=128))
    L.union(b, L.cyl_z("collar", 0, 0, COLLAR_R, za1 - 0.01, zb0 + 0.01, n=96))
    L.union(b, L.cyl_z("journal_b", -C.E, 0, jr, zb0, zb1, n=128))
    rod = L.cyl_z("rod", 0, 0, P["rod_bore"] / 2, -1, L_HOUSING + 1, n=64)
    L.cut(rod, L.box("flat", ROD_FLAT, 5, -5, 5, -2, L_HOUSING + 2))
    L.cut(b, rod); L.finish(b); return b

def check_disks():
    root = C.R - C.RP - C.CLEAR - C.E
    assert C.OUT_PCD_R - P["seat_bushing"] / 2 - P["seat_6800"] / 2 >= 1.5, "bushing seat too close to the 6800"
    assert root - C.OUT_PCD_R - P["seat_bushing"] / 2 >= 1.5, "bushing seat too close to the lobe root"
    assert 2 * C.OUT_PCD_R * math.sin(math.pi / C.N_OUT) - P["seat_bushing"] >= 1.5, "bushing seats too close"
    for name in ("disk-a", "disk-b"):
        o = PARTS[name]
        assert L.stats(o)["non_manifold"] == 0, name
        assert abs(bore_diameter(o, 0, 0, DISK_T / 2) - P["seat_6800"]) < 0.03, name

def check_eccentric():
    jr = P["journal_6800"] / 2
    assert END_R + C.E <= jr - 0.2, "a 6800 won't slide over the eccentric end"
    assert END_R - ROD_R >= 1.2, "eccentric end too thin round the rod"
    assert jr - C.E - ROD_R >= 1.5, "journal too thin round the rod"
    o = PARTS["eccentric"]
    assert L.stats(o)["non_manifold"] == 0
    za, zb = Z_DISK0 + DISK_T / 2, Z_MID + COLLAR_T / 2 + DISK_T / 2
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=za) - (C.E - jr)) < 0.05, "journal A not towards +x"
    assert abs(L.first_hit_x(o, 0, -20, r=0.2, z=zb) - (-C.E - jr)) < 0.05, "journal B not towards -x"

bpy.ops.wm.read_factory_settings(use_empty=True)
PARTS["disk-a"] = disk("disk-a", 0.0, 1)
PARTS["disk-b"] = disk("disk-b", C.DISK_B_PHASE, 2)
PARTS["eccentric"] = eccentric()
CHECKS += [check_disks, check_eccentric]

# --- Task 4 adds the housing and carriers here; Task 5 the bench parts and the assembly check ---

for check in CHECKS:
    check()
print("POC", json.dumps({n: L.stats(o) for n, o in PARTS.items()}))
for n, o in PARTS.items():
    L.export(o, os.path.join(OUT, n + ".stl"))
print("POC DONE")
