"""Offset wrist (docs/superpowers/specs/2026-11-16-offset-wrist-axes5-6-design.md), in the forearm frame:
x along the roll axis from the axis 4 housing's rear face, y and z the head concept's world y and z
(roll axis at y = z = 0, z up at axis 4's home). The hand is on the -y side."""
import forearm_dims as F

PITCH_X = F.FLANGE_FACE + 44.0               # flange screw heads sunk in an 8 plate, then 2 clear of the axis 5 housing
AX5_REAR_Y = 19.3
AX5_MOTOR_ANGLE = 250.0                      # pancake back and down; the rails turn it square to the arm, so at 225 its corner reached the plate
BOLT_ANGLES = [45, 135, 225, 315]
AX5_TEETH, AX5_BELT = 60, 234                # 60:1: at 40:1 the layout needed 1.07 N·m against the pancake's measured 1.2

PLATE_X = (F.FLANGE_FACE, F.FLANGE_FACE + 8.0)
PLATE_R, PLATE_HALF_Z = 20.0, 20.0
BRIDGE_X1 = 254.0                            # plate to the mount's disc; past this it would cover a housing bolt
FLANGE_HOLE_R = 1.85                         # float so the flange bolts don't fight the 6705
FLANGE_CB_R, FLANGE_CB_DEPTH = 3.0, 4.0

BRG5_W = 4.0
BRG5_R_OUT, BRG5_R_IN = 16.0, 12.5           # 6705 on the outer tube's Ø25 end
BRG5_X = (F.OUTER_X[1] - 5.0, F.OUTER_X[1] - 1.0)
SKIRT_R, SKIRT_BORE_R = 18.5, 15.5

OUT_PLATE_Y = (-20.3, -25.3)
LB_Y, LB_R = (-25.8, -31.8), 24.0

AX6_Y = -64.0                                # at -60 the gripper bracket's post on R26 cuts into the L-bracket's base disc
AX6_REAR_X = PITCH_X + 25.0                  # puts the axis 6 module's centre of mass near the pitch axis
AX6_MOTOR_UP = True

HOUSING_R, BOLT_R, T8_HOUSING_L = 34.0, 30.0, 32.6
