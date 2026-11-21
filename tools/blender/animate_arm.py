"""Builds head_concept.py's --shoulder scene (no checks, no renders), hangs each part group on an empty at its joint, keyframes
a tour of the arm's range and renders it to model/animation/: an MP4 and a .blend whose joint empties can be turned by hand.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/animate_arm.py -- --shoulder  (STILLS=1: key-pose PNGs only)
Poses aren't collision-checked; head_concept.py --shoulder does that."""
import bpy, math, os, sys
from mathutils import Matrix, Vector
HC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "head_concept.py")
OUTD = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "model", "animation")
sys.path.insert(0, os.path.dirname(HC))
src = open(HC).read().replace("    check(z_motor)\n", "    return\n", 1)
g = {"__file__": HC, "__name__": "head_concept_anim"}
exec(compile(src, HC, "exec"), g)
S, E = g["S"], g["E"]
COLS, SH_AT, ELBOW_AT = g["COLS"], g["SH_AT"], g["ELBOW_AT"]
scene = bpy.context.scene

for name in ("V1 arm kept", "V1 head (for comparison)"):
    for o in list(COLS[name].objects):
        bpy.data.objects.remove(o)

turning, still = g["phi_split"]()
upper = g["upper_arm_objs"]()
body, rest = g["past_elbow"]()
group = {}
for key, objs in (("still", still), ("base", turning), ("upper", upper), ("rest", rest), ("body", body)):
    for o in objs:
        group[o.name] = key
arm_cols = (g["SH_COL"], g["ELBOW_COL"], g["ELBOW_COMPACT_COL"])
for n, c in COLS.items():
    for o in c.objects:
        if o.name not in group:
            group[o.name] = "upper" if n in arm_cols else "still" if n == g["BASE_COL"] else "rest"


def empty(name, at, parent=None):
    e = bpy.data.objects.new(name, None); scene.collection.objects.link(e)
    e.empty_display_type, e.empty_display_size = 'ARROWS', 60
    e.location = at; e.rotation_mode = 'XYZ'
    if parent:
        e.parent = parent
        bpy.context.view_layer.update()
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    bpy.context.view_layer.update()
    return e


j1 = empty("J1 base (rotate Z)", (SH_AT.x, SH_AT.y, 0))
j2 = empty("J2 shoulder (rotate Y)", SH_AT, j1)
j3 = empty("J3 elbow (rotate Y)", ELBOW_AT, j2)
# Axis 4 turns the inner aluminium tube; the head bracket (with axis 5) is glued on its end, so it and everything past the
# pitch roll with it. Axis 6 turns the hand on the same line: its output, the adapter, the shell and the gripper's insides.
ROLLS = ("ax4 aluminium tube", "ax4 ax4-tube-hub", "ax4 ax4-output-plate", "ax4 carrier")
for n in group:
    if n.startswith(ROLLS) or n in [o.name for o in COLS["Wrist fixed"].objects] + [o.name for o in COLS["Axis 5 belted, 40:1"].objects]:
        group[n] = "roll"
for n in [o.name for c in ("Three-finger hand", "Gripper drive, past axis 6") for o in COLS[c].objects] + \
         [o.name for o in COLS["Structure placeholders"].objects if o.name.startswith(("adapter", "palm rear shell", "screw bulkhead"))] + ["ax6 carrier-front", "ax6 carrier-rear"]:
    group[n] = "ax6"
j4 = empty("J4 wrist roll (rotate X)", (g["PITCH_X"] - 60, 0, g["ROLL_Z"]), j3)
j5 = empty("J5 wrist pitch (rotate Y)", (g["PITCH_X"], 0, g["ROLL_Z"]), j4)
j6 = empty("J6 hand (rotate X)", (g["AX6_REAR_X"], g["AX6_Y"], g["ROLL_Z"]), j5)
holder = {"base": j1, "upper": j2, "rest": j3, "roll": j4, "body": j5, "ax6": j6}
for o in scene.objects:
    k = group.get(o.name)
    if k in holder:
        o.parent = holder[k]
        o.matrix_parent_inverse = holder[k].matrix_world.inverted()

bench_z = SH_AT.z + S.BENCH_Z
bpy.ops.mesh.primitive_plane_add(size=1800, location=(SH_AT.x + 150, 0, bench_z - 0.5))
bench = bpy.context.active_object; bench.name = "bench"
m = bpy.data.materials.new("bench"); m.diffuse_color = (0.80, 0.78, 0.74, 1); bench.data.materials.append(m)

FPS = 24
POSES = [   # (seconds, phi, psi, theta, pitch, roll, ax6): theta 90 = forearm level, psi 0 = upper arm straight up
    (0.0, 0, 0, 90, 0, 0, 0), (1.5, 0, 0, 90, 0, 0, 0),
    (3.5, 120, 0, 90, 0, 0, 0), (6.0, -120, 0, 90, 0, 0, 0), (7.5, 0, 0, 90, 0, 0, 0),
    (9.5, 0, 45, 120, 30, 0, 0), (11.5, 0, 5, 142, 50, 0, 0), (12.5, 0, 5, 142, 50, 0, 0),   # the tool on the bench, 161 mm out
    (14.5, 0, -60, 40, -40, 0, 0),
    (16.5, 0, 0, 0, 0, 0, 0), (17.5, 0, 0, 0, 0, 0, 0),                                       # standing tall
    (19.5, 0, 85, 20, 0, 0, 0), (22.5, 90, 85, 20, 0, 0, 0), (24.0, 90, 85, 20, 0, 0, 0),     # full reach, turning
    (26.5, 0, 0, 90, 0, 0, 0), (27.5, 0, 0, 90, 0, 0, 0),                                 # the wrist on its own
    (29.5, 0, 0, 90, 0, 90, 0), (32.5, 0, 0, 90, 0, -90, 0), (34.0, 0, 0, 90, 0, 0, 0),   # axis 4 roll
    (35.5, 0, 0, 90, 45, 0, 0),                                                              # axis 5 pitch
    (38.0, 0, 0, 90, 45, 0, 180), (41.5, 0, 0, 90, 45, 0, -180), (43.0, 0, 0, 90, 45, 0, 0),   # axis 6 turns the hand
    (44.5, 0, 0, 90, 45, 60, 90), (46.5, 0, 0, 90, 0, 0, 0), (47.5, 0, 0, 90, 0, 0, 0),
]
for t, phi, psi, th, pitch, roll, a6 in POSES:
    f = 1 + round(t * FPS)
    for e, axis, deg in ((j1, 2, phi), (j2, 1, psi), (j3, 1, th - 90.0), (j4, 0, roll), (j5, 1, pitch), (j6, 0, a6)):
        e.rotation_euler[axis] = math.radians(deg)
        e.keyframe_insert("rotation_euler", index=axis, frame=f)
scene.frame_start, scene.frame_end = 1, 1 + round(POSES[-1][0] * FPS)
scene.render.fps = FPS

cam = bpy.data.cameras.new("cam"); cam.type = 'ORTHO'; cam.ortho_scale = 1750; cam.clip_end = 6000
co = bpy.data.objects.new("camera", cam); scene.collection.objects.link(co); scene.camera = co
target = Vector((SH_AT.x + 120, 0, bench_z + 480))
d = Vector((1, -1.15, 0.65)).normalized()
co.location = target + d * 2500
co.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_shadows = True
scene.world = bpy.data.worlds.new("w"); scene.world.color = (0.93, 0.93, 0.95)
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
os.makedirs(OUTD, exist_ok=True)
g["frame_viewports"]()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTD, "cybot-arm-animated.blend"))
if os.environ.get("STILLS"):
    for t, *_ in POSES:
        scene.frame_set(1 + round(t * FPS))
        scene.render.filepath = os.path.join(OUTD, f"key-{t:04.1f}.png")
        if t < 26.0:
            continue
        bpy.ops.render.render(write_still=True)
else:
    scene.render.image_settings.media_type = 'VIDEO'
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format, scene.render.ffmpeg.codec = 'MPEG4', 'H264'
    scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = 'RGB', '8'   # 8-bit 4:2:0: what QuickTime plays
    scene.render.ffmpeg.constant_rate_factor, scene.render.ffmpeg.ffmpeg_preset, scene.render.ffmpeg.gopsize = 'HIGH', 'GOOD', FPS // 2
    scene.render.filepath = os.path.join(OUTD, "cybot-arm-tour.mp4")
    bpy.ops.render.render(animation=True)
print("ANIM DONE")
