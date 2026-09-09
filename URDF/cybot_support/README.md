# quartit/cybot_support — pulled 2026-09-09

Source: https://github.com/quartit/cybot_support, branch main, commit ad06c348fb297bf35f9d50bf0bd9ee21768e5ca8
(last pushed 2022-10-13, no license declared: package.xml says TODO). Pulled
with the GitHub API; the repo's `meshes/` are byte-identical to
`../simplify/` and are not duplicated here.

## What the two URDFs actually are

- `urdf/cybot.urdf` is **not a Cybot description**. It is an ABB IRB1600ID
  xacro output (robot name `abb_irb1600id`) with every link drawn as a
  0.2 m cylinder and ABB-scale joint offsets: base 0.50 m, upper arm 0.70 m,
  forearm 0.489 m, wrist 0.20 m. It never references the mesh files. The author
  used it as a six-joint skeleton for MoveIt; only the joint axes (z, y, y, x,
  y, x) and the limits below carry over to Cybot.
- `urdf/ur5_rviz.urdf` is a stock UR5 visual description pointing at the
  `ur_description` package; an RViz test, unrelated to Cybot.

## Joint data worth keeping from cybot.urdf

| Joint | Axis | Lower (rad) | Upper (rad) | Velocity (rad/s) |
|---|---|---|---|---|
| 1 | z | −3.1416 | 3.1416 | 3.142 |
| 2 | y | −1.5708 | 2.6180 | 3.142 |
| 3 | y | −4.1539 | 1.3788 | 3.142 |
| 4 | x | −2.7925 | 2.7925 | 5.585 |
| 5 | y | −1.5708 | 2.3562 | 6.632 |
| 6 | x | −3.4907 | 3.4907 | 8.029 |

The limits are the ABB template's, not measured Cybot travel; treat them as
placeholders until the arm is swept for collisions.

## Real Cybot joint offsets (from the assembled model, mm, arm at zero pose)

Measured on `model/cybot-master.blend`, which was fitted to `../link_*.stl`:

| Joint | Axis | Location |
|---|---|---|
| 1 | z | base column at (0, 0), turntable bearings z 55 and 95 |
| 2 | y | (0, y, 203) |
| 3 | y | (0, y, 453) |
| 4 | x | (x, 0, 555) |
| 5 | y | (250, y, 555) |
| 6 | x | flange face at x 288.5, gripper beyond |

So the kinematic chain is: base → 203 mm up to joint 2 → 250 mm to joint 3 →
102 mm up and forward to the axis-4 roll line at z 555 → 250 mm along the
forearm to joint 5 → 38.5 mm to the axis-6 flange. These replace the ABB
offsets when a Cybot URDF is written for the firmware's kinematics.
