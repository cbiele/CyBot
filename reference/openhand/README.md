# Yale OpenHand Project files (Model O, Model T, shared parts)

Snapshot of https://github.com/grablab/openhand-hardware at commit
b10197dcd79e7bcfa92c6d5a0bfa479e6a789fba (2025-03-25), pulled 2026-09-13.
Only the folders relevant to the Cybot gripper are kept: `model o`, `model t`,
`fingers` (finger designs and moulds), `common parts`, `couplings`, plus the
upstream README (`README-upstream.md`) and licence.

**Licence: CC BY-NC 3.0 (non-commercial).** Fine for the Cybot build and
derivatives; a commercial gripper product could not be based on these files
without permission from the Yale GRAB Lab. Attribution text required for
derivative works is in `LICENSE.md`.

## Why these

- **Model O**: three fingers in a 2+1 layout (two fingers on one side, one
  opposing) with a fourth actuator for abduction/adduction, so the same hand
  does a parallel-jaw pinch on bricks and a spherical grasp on round objects.
  Upstream uses four Dynamixels (`XM430/` current, `RX28-MX28/` older).
- **Model T**: four underactuated fingers on ONE actuator through a floating
  pulley tree (tendon differential), so every finger contact gets equal force.
  This differential is what lets the Cybot leadscrew close all three Model O
  fingers with one motor.
- **fingers/**: pivot-flexure (`pf`) and pivot-pivot (`pp`) finger variants and
  their moulds. Upstream casts flexures in Smooth-On urethane (hybrid
  deposition manufacturing); the Cybot plan is printed TPU flexures and pads,
  or the `pp` pin-joint fingers, which need no casting.

## File layout (upstream convention)

`a*` structural pieces top to bottom, `b*` gear/servo attachments, `c*` finger
mounts, `d*` optional pieces. Each model folder has `stl/` for printing and
SolidWorks part/assembly files for editing; `model o/RX28-MX28/step/` and
`model t/MX64/step/` carry STEP exports (the XM430 folders do not).

## Cybot intent

Take the Model O palm and 2+1 finger placement, the Model T single-tendon
differential, printed TPU fingers, and drive the tendon yoke from the CyBot
NEMA17 + T8 leadscrew (grip force from motor current); spread on a micro servo
or a manual detent first. See the conversation notes in docs/build-plan.md
when a gripper phase is planned; nothing is designed yet.

## Papers (reference/openhand/papers)

- `OpenHand_CAD_Guide.pdf`: how the SolidWorks configurations are organised.
- `Ma_ICRA2013.pdf`: "A Modular, Open-Source 3D Printed Underactuated Hand" (Model T; the paper to cite).
- `Ma_RAM2017.pdf`: Yale OpenHand Project overview, fabrication for ease of adoption.
- `Odhner_IJRR2014.pdf`: the iHY hand, Model O's ancestor: 2+1 layout, spread joint, grasp modes.
