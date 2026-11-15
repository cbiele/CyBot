"""Axial stack of the axis 4 forearm (docs/superpowers/specs/2026-11-15-axis4-forearm-tube-design.md).
Forearm frame: x along the roll axis, x=0 the 20:1 compact housing's rear face (cycloid_poc.py's z)."""

HOUSING_L, HUB_FACE, HOUSING_R = 38.6, 39.6, 34.0
BOLT_R, BOLT_ANGLES = 30.0, [45, 135, 225, 315]
INSERT_PCD_R, INSERT_ANGLES = 6.5, [90, 210, 330]

TUBE_L, TUBE_R = 190.0, 5.5                  # 9 x 11 aluminium, the drive shaft only
SOCKET_DEPTH = 15.0
BRG_W, BRG_SEAT_R, LIP_R = 4.0, 9.0, 7.2     # 6701 on tube-end-sleeve; lip clears the inner ring as on the T8 carriers
BRG_PLAY, LAND_T = 0.2, 0.3
LAND_R0, LAND_R1 = 6.0, 6.9                  # hubs bear on the 6701 inner ring only

PLATE_X, PLATE_R = (39.6, 44.6), 14.0
DOG_PCD_R, DOG_R, DOG_H, DOG_ANGLES = 10.5, 2.5, 4.0, [30, 150, 270]
HUB_X, HUB_R = (45.1, 62.1), 14.0

TUBE_X = (HUB_X[1] - SOCKET_DEPTH, HUB_X[1] - SOCKET_DEPTH + TUBE_L)
REAR_BRG_X = (HUB_X[1] + LAND_T + BRG_PLAY, HUB_X[1] + LAND_T + BRG_PLAY + BRG_W)
TUBE_SPARE = 1.5                             # the wrist socket runs past the tube end: the play is set at glue-up with a 0.3 shim, not by a hand-cut length
WRIST_X = (TUBE_X[1] - SOCKET_DEPTH, TUBE_X[1] + TUBE_SPARE + 3.0)
WRIST_R, FLANGE_INSERT_R, FLANGE_ANGLES = 15.0, 11.0, [45, 135, 225, 315]
FLANGE_FACE = WRIST_X[1]
FRONT_BRG_X = (WRIST_X[0] - LAND_T - BRG_PLAY - BRG_W, WRIST_X[0] - LAND_T - BRG_PLAY)

OUTER_X = (HOUSING_L, FRONT_BRG_X[1])
OUTER_FLANGE_T, OUTER_REAR_R, OUTER_R, OUTER_HUB_BORE_R = 5.0, 18.0, 12.5, 15.0
SEAT_CONE_X0 = REAR_BRG_X[0] - (OUTER_HUB_BORE_R - BRG_SEAT_R)   # 45° from the hub bore down to the rear seat: a flat step would print as a 6 mm overhang
HUB_CHAMFER_X0 = SEAT_CONE_X0 + (OUTER_HUB_BORE_R - 1.0 - HUB_R)  # the hub's front follows the cone 1.0 inside it
