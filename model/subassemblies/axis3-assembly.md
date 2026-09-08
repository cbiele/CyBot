# axis3: stack order along the joint axis (0, 1, 0) (assembled coordinates, mm)

Parts in the order they sit along the axis; bearings listed under the part they seat in.

- axis3-GT2-stepper  (centre -40.0, 39 mm long)
- axis3-OPH2  (centre -37.4, 21 mm long)
    - 6804zz  axis3-OPH2 / axis2-shaft (second set)
- axis3-holder2  (centre -11.0, 35 mm long)
    - 6813zz  axis3-holder2 / axis3-OPH2: mirror, with mainBody1's pocket
- axis3-disk1  (centre -8.6, 10 mm long)
    - 6804zz  axis3-disk1 / eccentric shaft: disk centre bore; disks are exported concentric with the axis, not on eccentrics
    - 688rs x6  axis3-disk1 / M4 rod: O16 pockets open toward +y on this gearbox
- axis3-disk2  (centre +0.4, 10 mm long)
    - 6804zz  axis3-disk2 / eccentric shaft: disk centre bore; disks are exported concentric with the axis, not on eccentrics
    - 688rs x6  axis3-disk2 / M4 rod: O16 pockets open toward +y on this gearbox
- axis3-disk3  (centre +9.4, 10 mm long)
    - 6804zz  axis3-disk3 / eccentric shaft: disk centre bore; disks are exported concentric with the axis, not on eccentrics
    - 688rs x6  axis3-disk3 / M4 rod: O16 pockets open toward +y on this gearbox
- axis3-holder1  (centre +12.2, 33 mm long)
    - 6813zz  axis3-holder1 / axis3-OPH1: O85 step 5 mm deep in the holder (y 23-28) plus 5 mm in mainBody2's pocket (y 28-33); inner ring on the OPH O65 boss
- axis3-OPH1  (centre +37.4, 21 mm long)
    - 6804zz  axis3-OPH1 / axis2-shaft (second set): O32 bore 11 mm deep in the OPH
- axis3-GT2-encoder  (centre +51.9, 16 mm long)

## Hardware (PDF list + STL count)
- 6813zz x2, 6804zz x5, 688rs x18 (all located)
- M6x50 pins: each holder has 14 O6 + 7 O5.8 holes
- M4 threaded rod x6, M6x70 x6
- NOT IN THIS FOLDER: eccentric shafts = a second print of axis2-shaft1..4 (PDF: same shaft files for both gears); diskCap = likely 3 more axis2-diskCap (same O80 recess and O57 pitch circle, unverified)
- STACK UNVERIFIED: OPH1 (y 27-47) overlaps the encoder pulley and its O65 boss (y 31-47) misses the 6813 seat (y 23-33); re-seat when this joint is built
