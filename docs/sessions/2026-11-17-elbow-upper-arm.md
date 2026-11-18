# Session 2026-11-17: elbow and upper arm

## Done
Pushed to origin/main, ending at 2727abf.
- **Spec:** `docs/superpowers/specs/2026-11-17-elbow-upper-arm-design.md`.
- **Plan:** `docs/superpowers/plans/2026-11-17-elbow-upper-arm.md`. All six tasks were built, then given a final review and one fix pass.
- **Generator:** `tools/blender/elbow.py` and `elbow_dims.py`. The in-script asserts are the tests; it prints `ELBOW DONE`.
- **Parts:** in `model/elbow/` (STLs in print pose), plus `poses.json` (each STL back into the elbow frame), `PRINT.md` and `print/*.3mf` (five P2S plates).
- **Layout:** `head_concept.py -- --elbow` puts the elbow at world (76.4, 0, 475), with ROLL_Z 555 kept. The sweep from −20° to +150° is clean. The worst load is 5.16 N·m against 7.02, so 1.36×. Renders are in `model/head-concept/elbow/`.
- **The user approved:** the single-plane tube truss on plate B's side (three tubes: rear, front, middle).

## Key frames and numbers
- **Elbow frame:** origin on the elbow axis at the plates' mid-plane, y towards plate A, pose = forearm level along +x and upper arm down −z. The shoulder is at (0, 0, −220).
- **Rotation:** `rot_elbow(θ) = Rotation(θ−90, Y)`. θ 0 is the forearm straight up.
- **Forearm offset:** 80 mm, with ELBOW_FX 40.
- **Plates:** 60 apart, 8.5 thick.
- **Belt:** 20T/60T 3M on the 420, centres 148.77.

## Next (the user's ask)
**Model this in Blender.** That means bringing the elbow and upper arm into the master assembly (`model/cybot-master.blend`, rebuilt from `model/placements.json` by `apply_placements.py`; see the memory note cybot-model-files) and/or the Blender MCP scene.
- Use `model/elbow/poses.json` plus the elbow-to-world translation above to place the STLs.
- `head-concept-elbow.blend` (git-ignored) already holds the full layout and could be the starting point.

## Deferred minors
- The hub's wire window can line up with the stop blocks at −20/150.
- Plate B's elbow lip is an overhang.
- The dog holes are +0.15.
- The clamp's pinch screw has no spot face.
- `head_concept.elbow_fixed()` excludes the 60T and belt without saying why.
- There's dead code in `idler()` and `span_line_x()`.
