"""Elbow (axis 3) and upper arm (docs/superpowers/specs/2026-11-17-elbow-upper-arm-design.md).
Elbow frame: origin on the elbow axis at the plates' mid-plane, y along the elbow axis towards plate A,
parts built in the head concept's pose (forearm level along +x, upper arm hanging along -z).
The forearm frame (forearm_dims) maps in as (x - ELBOW_FX, y, z + OFFSET). Elbow angle 0 = forearm straight up, 90 here."""
import forearm_dims as F

OFFSET, UPPER_L = 80.0, 220.0
ELBOW_FX = 40.0                              # just in front of axis 4's housing, so its compact, motor and mount counterweight the wrist
RANGE, STOPS = (-20.0, 150.0), (-22.5, 152.5)   # stop faces 0.25 past the plan's -22/+152 so -20/+150 keep 1 mm

B6810 = (25.0, 32.5, 7.0)                    # bore r, OD r, width
TUBE_OR, TUBE_IR = 4.5, 3.5                  # 9 x 7 aluminium
SOCKET_R, SOCKET_DEPTH, SOCKET_WALL = 4.6, F.SOCKET_DEPTH, 2.0
TUBE_CLEAR = 0.5                             # free space round each tube's open span
TUBE_STOCK = 125.0                           # half a 250 length

HOUSING_R, HOUSING_L = F.HOUSING_R, F.HOUSING_L
PLATE_GAP, PLATE_T, LIP_T = 60.0, 8.5, 1.5
Y_REAR = PLATE_GAP / 2                       # the elbow compact's rear face on plate A's inner face; its output runs to -y
Y_OUT = Y_REAR - F.PLATE_X[1]                # face of its output plate (the forearm's ax4-output-plate, printed again)
HUB_6810_Y = (-PLATE_GAP / 2, -PLATE_GAP / 2 - B6810[2])
NUT_AF, NUT_T = 5.8, 2.6

HUB_R, HUB_FLOOR = 27.5, 5.0                 # the disc's rim is the shoulder on the 6810's inner ring
HUB_DISC_Y = (Y_OUT, HUB_6810_Y[0] + 1.0)
HUB_END_Y = HUB_6810_Y[1] - LIP_T - 8.0      # the journal runs past plate B for the wires' window and the stop tab
HUB_BORE_R = 18.0

# The compact's Ø68 housing and axis 4's leave only 12 mm between them on plate A's side, so the tubes run in one
# plane on plate B's side, in front of the compact's output, where the hub's load already goes.
TUBE_PLANE_Y = -22.0
TUBE_ENDS = {                                # elbow-frame (x, z) of each tube's two socket mouths, collar end first
    "rear": ((-11.0, 36.0), (-46.0, 3.0)),
    "front": ((44.0, 53.0), (47.0, -10.0)),
    "middle": ((14.0, 52.0), (20.0, 33.0)),  # two tubes alone between two rigid ends make a four-bar; this one triangulates it
}

COLLAR_X = (F.OUTER_X[0] + F.OUTER_FLANGE_T, F.REAR_BRG_X[0] - 1.0)   # forearm frame: in front of the flange, clear of the rear 6701's seat
COLLAR_R, KEY_DISC_T = 26.0, 5.0
COLLAR_FREE_R = F.OUTER_REAR_R + 0.5         # past the clamp the collar stands off the outer tube
BOLT_HEAD_R, BOLT_HEAD_H = 2.75, 3.0         # the R30 bolts' heads on the outer tube's flange face
KEY_R, KEY_DEPTH = BOLT_HEAD_R + 0.35, BOLT_HEAD_H + 0.5
CLAMP_SCREW = (12.6, 21.0)                   # elbow x, |y| of the split clamp's two M3 x 20s
CLAMP_CB_Z, CLAMP_NUT_Z = 86.0, 72.5         # counterbore floor in the upper half; nut slot centre in the lower half
SPLIT_GAP = 1.0

M3_STOCK = (40, 45, 50)
ELBOW_TORQUE_NMM = 9.0e3                     # 1.5x the estimated static load, for part checks
FOREARM_N = 2.5 * 9.81 * 1.5                 # forearm, hand and tool with the same margin

import cycloid_math as _C
BELT_C = round(_C.belt_centre_distance(20, 60, 420, pitch=3.0), 2)
MOTOR_Z, MOTOR_SLOT = -BELT_C, 3.0           # the 17HS8401B's axis on the upper arm, +-3 of tensioning travel
MOTOR_SQ, MOTOR_HOLE, MOTOR_PILOT_R, MOTOR_SHAFT_L = 42.3, 15.5, 11.0, 24.0
MOTOR_L, MOTOR_L_MAX = 48.0, 60.0            # plate B has a window so a longer NEMA17 passes through it
PLATE_R, SHOULDER_Z = 38.0, -UPPER_L
PULLEY_GAP, PULLEY_H, PULLEY_HUB = 1.0, 21.5, 7.0   # htd3m_pulley: hub towards plate A, so the 20T's set screw lands on the shaft
PULLEY_Y0 = Y_REAR + PLATE_T + PULLEY_GAP
TEETH_Y = (PULLEY_Y0 + PULLEY_HUB + 1.5, PULLEY_Y0 + PULLEY_HUB + 1.5 + 11.5)
BELT_PLANE_Y = sum(TEETH_Y) / 2
R20_OD, R60_OD, BELT_T = 18.34 / 2, 56.53 / 2, 2.4
ROLLER_R, ROLLER_FLANGE_R, ROLLER_Y = 8.0, 10.0, (TEETH_Y[0] - 1.0, TEETH_Y[1] + 1.0)
IDLER_AT, IDLER_SLOT = (26.5, MOTOR_Z / 2), 3.0     # on the belt's back on the +x span, slotted along x; M3 x 30 axle
IDLER_BOSS_R = 7.0
BELT_ENVELOPE_Y = Y_REAR + PLATE_T + PULLEY_GAP + PULLEY_H + 3.5 + 2.0   # pulley tops plus the idler bolt's head, plus 2
SHOULDER_6810_Y = ((Y_REAR, Y_REAR + B6810[2]), (-Y_REAR, -Y_REAR - B6810[2]))
LIP_IN_R = 28.5                              # bears on the outer ring only
CROSS_MEMBERS = [(27.0, -95.0), (-27.0, -95.0), (27.0, -176.0), (-27.0, -176.0)]   # the lower pair clear of the stand's index holes
CM_HOLE_R = TUBE_OR + 0.1
WINDOW = (16.0, -45.0, -118.0)               # lightening: |x|, z top, z bottom
TAB_PHI, TAB_HALF, TAB_R, TAB_Y = 270.0, 12.0, (27.0, 33.0), (-PLATE_GAP / 2 - PLATE_T - 0.5, HUB_END_Y)   # hard-stop tab on the hub's journal end, outside plate B
STOP_BLOCK_DEG, STOP_R = 8.0, (26.0, 33.5)
MAGNET_R, MAGNET_D = 3.0, 3.0                # Ø6 x 3, in the tab's outer face
SENSOR = (4.6, 3.6, 1.6)                     # TO-92 Hall: width, height, thickness; its face 1.5 from the magnet at home
SENSOR_GAP = 1.5

# Shoulder: both 6810s go in from the plates' outer faces against lips on the inner faces; the hub's shoulder (plate A side)
# and a pinch clamp (plate B side) push the inner rings inwards, so the pair is held in an X.
SHOULDER_HUB_R, SHOULDER_BORE_R = B6810[0], 22.0
SHOULDER_SHOULDER_R = 27.5
SHOULDER_HUB_Y = (-Y_REAR - PLATE_T - 10.5, BELT_ENVELOPE_Y + 8.0)   # past plate B by the clamp; past the belt by 8 on plate A's side
HUB_END_R, HUB_END_T = 34.0, 7.0
HUB_END_INSERT_R, HUB_END_ANGLES, HUB_END_INSERT_DEPTH = 29.0, [45, 135, 225, 315], 5.0   # the body's and the shoulder drive's interface
CLAMP_Y = (SHOULDER_HUB_Y[0], -Y_REAR - PLATE_T - 0.5)
CLAMP_SPLIT, CLAMP_PINCH = 1.5, (HUB_END_R - 3.5)
INDEX_R, INDEX_HOLE_R, INDEX_PIN_DEG, INDEX_ANGLES = 40.0, 2.1, 45.0, (0.0, 45.0, 90.0)   # Ø4 pin; shoulder pitch 0 = upper arm straight up
STAND_T, STAND_BASE_Z, STAND_BASE_T = 8.0, SHOULDER_Z - 55.0, 10.0
STAND_PAD = (40.0, 60.0)
