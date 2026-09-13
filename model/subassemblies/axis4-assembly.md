# axis4: stack order along the joint axis (1, 0, 0) (assembled coordinates, mm)

Parts in the order they sit along the axis; bearings listed under the part they seat in.

Order set by hand on the bench (2026-09-12, provisional until the gearbox is built); parts after the listed ones are unplaced.

- axis4_80TGT2-7mm  (centre +36.5, 19 mm long)
- axis4_housingNema  (centre +60.5, 25 mm long) [flipped]
- axis4_OPH  (centre +79.0, 12 mm long)
    - 6812zz  axis4_OPH / axis4_housingNema: inner ring on the OPH O60 boss x 73-83, outer ring in housingNema's O78 x 10 pocket; both OPHs export at the same x, positions are per the bench order
    - 6705zz  axis4_OPH / axis4_shaft2: O32 bore inside the short OPH, journal of the motor-end shaft piece; user fitted 2026-09-12 (the fourth 6705)
- axis4_shaft2  (centre +49.5, 13 mm long)
- axis4_disk1  (centre +62.5, 7 mm long)
    - 6705zz  axis4_disk1 / axis4_shaft3: disk bore x 60.5-64.5; disks exported concentric, eccentrics are at z 553/557
- axis4_diskCap  (centre +59.7, 2 mm long)
- axis4_shaft3  (centre +60.5, 9 mm long)
- axis4_disk2  (centre +69.5, 7 mm long)
    - 6705zz  axis4_disk2 / axis4_shaft: disk bore x 67.5-71.5
- axis4_diskCap.2  (centre +71.6, 2 mm long)
- axis4_shaft  (centre +71.5, 13 mm long)
- axis4_OPH2  (centre +89.0, 32 mm long)
    - 6812zz  axis4_OPH2 / axis4_housing: inner ring on the OPH2 O60 boss x 73-83, outer ring in the housing's O78 x 10 pocket (x 63-73 in the export); user fitted 2026-09-12
    - 6705zz  axis4_OPH2 / axis4_shaft: O32 bore 7 mm deep (x 73-80) in the OPH, shaft journal x 76-78
- axis4_housing  (centre +60.5, 25 mm long)
- axis4_axis5_holder  (centre +10.0, 160 mm long)
    - 6804zz x2  axis4_axis5_holder / axis3 side (O20 stub, mate TBD): O32 x 10 side pocket at y -38.8..49 on the elbow axis z 453; user fitted 2026-09-12
- axis4_Tube  (centre +192.0, 174 mm long)

## Hardware (PDF list + STL count)
- 6804zz x2 in the elbow holder's side pockets (O32 x 10, z 453, both faces): fitted 2026-09-12; inner ring rides a O20 stub from the axis-3 side
- 6812zz x2, one on each OPH's O60 boss, seated in the O78 x 10 pockets of housing and housingNema (fitted 2026-09-12). The elbow holder's own O78 pockets (x 75-85 and x -3..7) are not bearing seats in this arrangement; mate TBD
- 6705zz x4, all located: two disk bores, one inside each OPH (fitted 2026-09-12)
- pins 6x25 x6 (housing has 6 O6 through-holes)
- brass bushings 8x10x6 x12 (six O10 holes per disk)
- M4 rod (through the bushings) and M3 rod, M5x20
- axis4_OPH (short, ends x 85) and axis4_OPH2 (long, ends x 105 with the O60 tube seat) are alternatives: OPH2 for this axis, OPH for the axis-5 copy
- axis4_diskCap prints one per disk (x2 per gearbox), per the bench order 2026-09-12; second cap's assembled seat is a placeholder
- this folder prints twice: axis 4 here and the axis-5 pitch gearbox inside 6-axis5-6
