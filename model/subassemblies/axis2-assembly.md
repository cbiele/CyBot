# axis2: stack order along the joint axis (0, 1, 0) (assembled coordinates, mm)

Parts in the order they sit along the axis; bearings listed under the part they seat in.

- axis2-GT2-stepper  (centre -51.8, 18 mm long)
- axis2-holder1  (centre -39.0, 20 mm long)
- axis2-housing2  (centre -12.2, 36 mm long)
    - 6813zz  axis2-housing2 / axis2-OPH1: outer ring in the housing's 5 mm deep O85 step, inner ring on the OPH's 10 mm O65 boss
- axis2-OPH1  (centre -26.5, 16 mm long)
    - 6804zz  axis2-OPH1 / axis2-shaft4: shaft end support, O32 bore in the OPH, O20 journal on shaft4
- axis2-shaft4  (centre -18.8, 16 mm long)
- axis2-diskCap  (centre -14.9, 6 mm long)
- axis2-disk3  (centre -12.0, 12 mm long)
    - 6804zz  axis2-disk3 / eccentric shaft: disk centre bore on the O20 eccentric (2 mm throw)
    - 688rs x6  axis2-disk3 / M4 rod: pressed into the disk's O16 pocket (opens toward -y); the M4 rod rolls inside the 8 mm bore with 4 mm clearance = 2 x eccentricity
- axis2-shaft3  (centre -5.5, 12 mm long)
- axis2-diskCap.2  (centre -4.1, 6 mm long)
- axis2-disk2  (centre -1.0, 12 mm long)
    - 6804zz  axis2-disk2 / eccentric shaft: disk centre bore on the O20 eccentric (2 mm throw)
    - 688rs x6  axis2-disk2 / M4 rod: pressed into the disk's O16 pocket (opens toward -y); the M4 rod rolls inside the 8 mm bore with 4 mm clearance = 2 x eccentricity
- axis2-shaft2  (centre +5.5, 12 mm long)
- axis2-diskCap.3  (centre +7.6, 6 mm long)
- axis2-disk1  (centre +10.0, 12 mm long)
    - 6804zz  axis2-disk1 / eccentric shaft: disk centre bore on the O20 eccentric (2 mm throw)
    - 688rs x6  axis2-disk1 / M4 rod: pressed into the disk's O16 pocket (opens toward -y); the M4 rod rolls inside the 8 mm bore with 4 mm clearance = 2 x eccentricity
- axis2-shaft1  (centre +18.8, 16 mm long)
- axis2-OPH2  (centre +25.5, 16 mm long)
    - 6804zz  axis2-OPH2 / axis2-shaft1: shaft end support, encoder side
- axis2-housing1  (centre +12.2, 36 mm long)
    - 6813zz  axis2-housing1 / axis2-OPH2: same on the encoder side
- axis2-holder2  (centre +39.0, 20 mm long)
- axis2-GT2-encoder  (centre +39.5, 41 mm long)

## Hardware (PDF list + STL count)
- 6813zz x2
- 6804zz x5
- 688rs x18
- M6x50 pins x12 in the housing halves' O6 holes (12 pins = the PDF's 1:23; axis 3 with 14 is the 1:20)
- M4 threaded rod (3.85 mm): 3 lengths through the shaft train's small holes lock the cam pieces and become the pulley studs; 6 lengths (~68 mm) float through the 688s and the OPH rim holes
- M6x70 x12 (PDF): six per side clamp holder + body plate + housing half
