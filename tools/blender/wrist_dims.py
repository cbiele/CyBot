"""Offset wrist (docs/superpowers/specs/2026-11-16-offset-wrist-axes5-6-design.md), in the forearm frame:
x along the roll axis from the axis 4 housing's rear face, y and z the head concept's world y and z
(roll axis at y = z = 0, z up at axis 4's home). The hand is on the -y side."""
import math
import forearm_dims as F

HOUSING_R, BOLT_R, T8_HOUSING_L = 34.0, 30.0, 32.6

BRG5_W = 4.0
BRG5_R_OUT, BRG5_R_IN = 16.0, 12.5           # 6705 on the outer tube's Ø25 end
BRG5_X = (F.OUTER_X[1] - 5.0, F.OUTER_X[1] - 1.0)
SKIRT_R = 18.5
SHOULDER_R = 14.0                            # bears on the 6705's outer ring only: the inner ring is fixed, the bracket turns

BOSS_X = (BRG5_X[0], F.FLANGE_FACE)          # the bracket is glued on the drive tube in the old wrist hub's place
FILL_HALF_Z = 16.0
PITCH_X = round(F.FLANGE_FACE + 1.0 + HOUSING_R, 2)   # the boss's flat front, over the tube's end, 1 clear of the housing's nearest line (z 0)
AX5_REAR_Y = 19.3
AX5_MOTOR_ANGLE = 180.0                      # straight back along the forearm, beside the outer tube
PANCAKE_OUTBOARD = True                      # rolling with axis 4 it can't straddle the fixed tube, so its body faces out
BOLT_ANGLES = [45, 135, 225, 315]
AX5_TEETH, AX5_BELT = 60, 234                # 60:1: at 40:1 the layout needed 1.07 N·m against the pancake's measured 1.2

ARM_HALF_W = 28.0
MP_WALL_V = (21.5, 28.0)                     # outside the pancake's 42.3 square
MP_SCREW_V = 24.5
MP_LOCAL_Z = {"plate": (-23.5, -17.5), "walls": (-17.5, -6.0)}   # the old mount mirrored about the belt plane at -11.75

OUT_PLATE_Y = (-20.3, -25.3)
LB_Y, LB_R = (-25.8, -31.8), 24.0

AX6_Y = -64.0                                # at -60 the gripper bracket's post on R26 cuts into the L-bracket's base disc
AX6_REAR_X = PITCH_X + 25.0                  # puts the axis 6 module's centre of mass near the pitch axis
AX6_MOTOR_UP = True
