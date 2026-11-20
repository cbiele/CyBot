# V2 low shoulder and flat stand: design

**Date:** 2026-11-20
**Replaces:** the body, shoulder and stand of `docs/superpowers/specs/2026-11-19-shoulder-base-design.md`, built on main up to `94a9a2e`. That build works on paper but stands far too tall. This design keeps what's still useful from it and lowers everything.

## Why

The first build put the shoulder axis 158 mm above the turntable, on tall walls over a square turntable, with the compact and motor hung outside wall A. On the render, most of the space between the walls under the shoulder is empty. The user wants the shoulder down close to the platform, so the arm can reach objects on the bench right next to its own base.

The arm lives on one bench, clamped down, and is rarely moved. The stand is about stiffness and low height, not portability.

## Goals

- **Reach the bench.** A tool on the wrist can touch the bench surface close to the base.
- **The lowest shoulder the parts allow.** No empty space under the shoulder between the walls.
- **The arm swings past level.** Move every obstruction that stops the upper arm going further than horizontal, fore and aft. Where parts still collide, report it as a soft limit, not a design rule.
- **A compact body:** the compact inside the arm, the motor mount built into a wall, a round platform.

## Non-goals

- **Wiring.** All the arm's wires will run in an external loom, sorted out later. Nothing needs routing through the shoulder or the hubs.
- **Portability.** The legs can still pull out, but nothing is designed around moving the arm.
- **The NEMA23.** It stays a drop-in fallback (see Shoulder torque), not the primary.
- **An electronics area.** It was dropped on 2026-11-20 (see below).

## Anti-goals

- A tall body or empty volume under the shoulder: the problem this design exists to fix.
- Reprinting the upper arm plates. They're printed and stay as they are, apart from drilling.

## Constraints (unchanged from the 2026-11-19 spec unless stated)

- **The upper arm plates** (`model/elbow/upper-plate-A/B`) are printed. They're 60 apart inside (`E.PLATE_GAP`), 8.5 thick, with a Ø65 6810 seat at the shoulder (lip on the inner face) and a round end r38 (`E.PLATE_R`). Drilling is fine; reprinting isn't.
- **The elbow motor** is inside the arm on plate A's inner face, about 71 mm from the shoulder axis. Its belt side stands out to `E.BELT_ENVELOPE_Y` past plate A and sweeps round the shoulder axis.
- **The gearbox:** a 20:1 compact (`cycloid_poc.py -- --m25-roll`), Ø68 × 38.6 (39.6 to the output face), with the elbow's output face (three M3 × 4.5 inserts on R6.5, three Ø5 dogs on R10.5) and a Ø5 input rod out of its rear face. The rod length is free.
- **Motors:**
  - Shoulder: a 17HS19-2004S1 (48 mm, 1.8°).
  - Base: another 17HS19-2004S1.
  - NEMA23 fallback for the shoulder: 57 square, 47.14 hole square, up to 76 long.
- **Belts in hand:**
  - Shoulder: 3M-420, 20T/80T, 80:1 overall, centres 131.9.
  - Base: 3M-477, 20T/130T ring, 6.5:1, centres 113.9.
- **Bearings:** 6810-2RS. Seven in hand, and the elbow uses one.
- **Legs:** four 250 mm lengths of 9 × 7 aluminium tube.
- **Printers:** P2S or A1, bed 256. PLA, and TPU for the pads. M3 bolts up to 50 mm, heat-set inserts for short screws.
- **Homing:** a TO-92 Hall sensor and a Ø6 × 3 magnet per axis.

## Decided

### The stand

- **The fixed base is a squat round drum that sits on the bench.**
- **Five contact points:** the drum's underside and four feet.
- **The legs:** the four 250 mm tubes run out of sockets in the drum's side, about 15° below horizontal, at 90° spacing. Each is about 241 mm out and 65 mm down, so the sockets sit about 70–80 mm above the bench and the drum is about that tall.
- **The feet:** slip on the tube ends with TPU pads, and land level with the drum's underside, about 340 mm from the centre.
- **Clamping:** the feet keep their bench-clamp tabs. Stability comes from clamping (the user's ruling of 2026-11-20 stands), so tipping unclamped is reported, not asserted.
- **The base drive:**
  - It stays the same in principle: a direct belt from the base motor to a printed 130T ring under the turntable, 3M-477, ±170°.
  - **The base motor sits on top of the fixed base, as on V1,** not hanging underneath.
- **The turntable** turns on two 6810s on a fixed spigot rising from the drum, as in the first build.

### The platform and body

- **The turntable is round,** and as small as the walls and the shoulder motor allow. Nothing on it stands proud fore or aft of the arm's swing, so the arm can dip past its edge.
- **Two walls,** A and B, outside the arm plates as before, but only as tall as the low shoulder needs.

### The shoulder: compact inside the arm on a fixed axle

- **Wall A carries a fixed, hollow stub axle.** It passes through plate A's Ø65 seat, and a 6810 goes back into that seat, so plate A turns on the stub.
- **The compact's housing bolts to the stub's inner end.** The compact sits inside the arm, between the plates, and never turns. The ratio stays 80:1.
- **The compact's output drives hub B.** Hub B is locked to plate B and turns in wall B's 6810, as in the first build.
- **The input rod runs out through the stub's bore** to the 80T outside wall A. The rod is longer than the elbow's: as long as the stub, wall and pulley need.
- **The motor mount is built into a wall:**
  - a bracket that's part of wall A (or B)
  - a swappable motor plate that drops into it (NEMA17 now, NEMA23 later)
  - slotted along the belt line for tension
- **The motor can sit further out if it needs to.** With the axis this low it can't hang under the 80T, so the 131.9 belt runs roughly level, along the turntable, to the motor.
- **The wall's bracket carries the motor.** The motor doesn't need to rest on the turntable, so the turntable doesn't have to grow to reach it. The bracket can overhang the turntable's edge, but it must stay stiff under belt tension. *(The builder check asked about this; this is my reading of the user's words: "integrated into the walls… bring the motor out farther if needed".)*
- **The compact is a fresh print** (the user, 2026-11-20). Its housing's rear face can change so it bolts straight onto the stub's inner end, keeping the stub in one piece.

### Height and range

- **The shoulder axis goes as low as the parts allow.** The rough estimate is 50–60 mm above the turntable, set by the plates' r38 ends and the compact's r34.
- **The shoulder's range goes as far past ±90° as the body allows.** The stops sit at the mechanical limits.
- **The forearm folds wherever it can.** With the axis this low, it can't fold fully at ψ 0 without meeting the turntable, so it's a soft limit, not a hard rule.

### No electronics area

The user dropped it (2026-11-20). The driver boards sit off the arm and are wired through the external loom, so neither the turntable nor the drum carries them.

### Shoulder torque

- **The NEMA17 first** (the user's ruling of 2026-11-20 stands). The 23 is a fallback, chosen at the bench.
- **The bracket fits the 23 now:** it's sized for its 57 square and 76 length at both slot ends, so swapping is only a plate. *(My call.)*
- **Design torque stays 13.5 N·m** for the hub lock, the output link and the stops.
- **The shoulder driver's current is capped** so a stall can't apply more than 13.5 N·m at the output (the user, 2026-11-20). The 17HS19 is rated 0.59 N·m at 2.0 A, about 47 N·m through 80:1 before losses, so an uncapped stall could break the link.
  - The print sheet states the cap, and the report gives it.
  - The basis: holding torque scales roughly with current, so about 13.5 / 47 × 2.0 A, before losses. The bench confirms it.
- **The capacity estimate is the first build's:** the elbow's bench result scaled by 80:1 over 60:1, 4.76 N·m. *(My call.)* At the current cap, capacity is whichever of that and 13.5 is lower. The count of poses over capacity is reported and doesn't stop the build.

## What the checks must show

The first build's checks carry over where the parts carry over. They include the sweep against the elbow belt envelope in 1° steps at both slot ends, the belt centres at slot ±3, and fits and bed size. New or changed:

- **Bench reach:** report the poses where the tool on the wrist reaches the bench plane near the base, and how close to the base it gets.
- **Range:** report how far past ±90° the upper arm swings before anything on the body meets it, and set the stops there.
- **Soft limits over the whole range,**
  - computed at enough base angles φ to catch the legs, the base motor and anything else fixed that the turning arm can meet, not only φ 0
  - reported as one table
- **Capacity:** count the poses whose static shoulder load exceeds the motor's estimated capacity, separately from collisions.
- **The compact inside the arm:**
  - it clears the elbow motor, its slot ends and the cross members through the full elbow range
  - its output's link to hub B fits the roughly 20 mm left in the 60 gap
- **Tipping:** report the margin, with "clamp the feet" under 15 mm, as now.

## Lessons from the first build's final review (2026-11-20), to carry over

- **Screw heads must be reachable and seat.** The first build trapped the motor's screw heads between the swap plate and its bracket. Check every screw head has room at every slot position.
- **The drill jig must only fit one way.** The first jig's fences hung clear when it was turned 180°, so holes could be drilled in the wrong place on plates that can't be reprinted. Key it so that's impossible, and assert it.
- **Tension screws need tool access.** The base push screw sat in a 13 mm gap under the ring, where no key could turn it.
- **Parts that only work one way round** (like the stop collar) need a key or a clear note on the print sheet.

## What's reusable from the first build (`tools/blender/shoulder.py`, `shoulder_dims.py`)

- **Hub B and its plate lock:** drilled through plate B, with inserts in the flange.
- **The jig,** once it's keyed.
- **The stop collar** and the Hall pattern.
- **The base:** the spigot, spacer, cap and 130T ring stack.
- **The leg socket and foot idea:** the angles and drum change.
- **`head_concept.py -- --shoulder`,** the whole-arm check and renders.

**Not reusable:**
- hub A
- the compact cage outboard of wall A
- the separate motor bracket
- the square turntable
- the tall walls
- the fixed base with the motor hanging underneath
- the 45° legs

## Left to the builder

- **The exact shoulder height,** and how far past ±90° the range goes.
- **The stub axle's form,** how it fixes to wall A, and the bore for the rod.
- **How the compact's output links to hub B** inside the 20 mm.
- **Which wall carries the motor bracket.**
- **The belt's direction from the 80T,** and the drop-in plate's form.
- **The turntable's radius,** and the 6810 spacing on the spigot.
- **The drum's height and radius,** the leg sockets, the exact leg angle near 15°, and the feet.
- **Where the base motor sits on the drum.**
