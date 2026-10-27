"""Cycloid geometry for the compact POC (docs/superpowers/specs/2026-10-25-compact-cycloid-poc-design.md),
in plain Python so pytest runs it outside Blender. Frame: housing axis on z. At input angle theta disk A's
centre is at E(cos theta, sin theta) and the disks and output turn -theta/N. Disk B rides the opposite
eccentric, which is disk A turned half a lobe, so its lobes are cut DISK_B_PHASE round from its holes."""
import math

N = 20                                  # lobes; N + 1 ring pins
R = 25.0                                # ring pin circle radius
RP = 1.6                                # ring pins: 3 x 18 spring pins, about 3.2 uncompressed where the lobes run
CLEAR = 0.15                            # outline held off the pins for print tolerance
OUT_PCD_R = 16.0                        # output pins and the disks' bushing seats
OUT_PIN_R = 2.15                        # output pins: 4 x 20 spring pins, about 4.3 uncompressed (a free fit took 4.37 in the hand)
BUSHING_BORE_R = 3.0                    # 6 x 8 x 5 sintered bronze
PIN_RUN_CLEAR = 0.1                     # diametral, pin in bushing
E = BUSHING_BORE_R - OUT_PIN_R - PIN_RUN_CLEAR / 2   # eccentricity, 0.8
N_OUT = 6
DISK_B_PHASE = math.pi / N
DISK_ZONE_BORE_R = 25.75                # housing round the disks: lobe tips sweep out to R - RP - CLEAR + 2E
STEPS_PER_DEG = 200 * 16 * 2 * N / 360  # 2:1 belt, then 1:N
GT2_FLANGE_T, GT2_TEETH_W = 1.0, 7.5     # printed 40T (gt2_pulley.py): free flange, then teeth for a 6 mm belt
MOTOR_SLOT = 3.5                        # bench motor travel each way: a 232 belt +-6 mm moves the motor 3.01


def profile(n=720, phase=0.0, clear=CLEAR):
    """Disk outline about its own centre; phase turns the lobes (rad)."""
    np_, rp = N + 1, RP + clear
    c, s = math.cos(phase), math.sin(phase)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        psi = math.atan2(math.sin((1 - np_) * t), R / (E * np_) - math.cos((1 - np_) * t))
        x = R * math.cos(t) - rp * math.cos(t + psi) - E * math.cos(np_ * t)
        y = -R * math.sin(t) + rp * math.sin(t + psi) + E * math.sin(np_ * t)
        pts.append((c * x - s * y, s * x + c * y))
    return pts


def _pose(disk, theta):
    sign = 1 if disk == "A" else -1
    return sign * E * math.cos(theta), sign * E * math.sin(theta), -theta / N


def disk_outline(disk, theta, n=1440):
    cx, cy, rot = _pose(disk, theta)
    c, s = math.cos(rot), math.sin(rot)
    pts = profile(n, phase=0.0 if disk == "A" else DISK_B_PHASE)
    return [(cx + c * x - s * y, cy + s * x + c * y) for x, y in pts]


def ring_pins():
    return [(R * math.cos(2 * math.pi * k / (N + 1)), R * math.sin(2 * math.pi * k / (N + 1))) for k in range(N + 1)]


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _inside(p, poly):
    x, y = p
    hit = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def pin_gaps(outline):
    """Gap from each ring pin's surface to the outline; negative means the pin cuts into the disk."""
    gaps = []
    for p in ring_pins():
        d = min(_seg_dist(p, outline[i], outline[(i + 1) % len(outline)]) for i in range(len(outline)))
        gaps.append((-d if _inside(p, outline) else d) - RP)
    return gaps


def self_intersections(pts):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    n, count = len(pts), 0
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            c, d = pts[j], pts[(j + 1) % n]
            if max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]):
                continue
            if max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]):
                continue
            if ccw(a, b, c) * ccw(a, b, d) < 0 and ccw(c, d, a) * ccw(c, d, b) < 0:
                count += 1
    return count


def bushing_centres(disk, theta):
    cx, cy, rot = _pose(disk, theta)
    return [(cx + OUT_PCD_R * math.cos(2 * math.pi * k / N_OUT + rot), cy + OUT_PCD_R * math.sin(2 * math.pi * k / N_OUT + rot))
            for k in range(N_OUT)]


def output_pins(theta):
    rot = -theta / N
    return [(OUT_PCD_R * math.cos(2 * math.pi * k / N_OUT + rot), OUT_PCD_R * math.sin(2 * math.pi * k / N_OUT + rot))
            for k in range(N_OUT)]


def belt_centre_distance(z1, z2, length, pitch=2.0):
    d1, d2 = z1 * pitch / math.pi, z2 * pitch / math.pi
    lo, hi = (d1 + d2) / 2, length
    for _ in range(80):
        c = (lo + hi) / 2
        if 2 * c + math.pi * (d1 + d2) / 2 + (d2 - d1) ** 2 / (4 * c) < length:
            lo = c
        else:
            hi = c
    return lo
