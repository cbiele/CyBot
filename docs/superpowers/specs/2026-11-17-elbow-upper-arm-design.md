# Elbow (axis 3) and upper arm

Date: 2026-11-17. Status: draft for the user's review.

## Intent

The forearm (axis 4) and the offset wrist (axes 5 and 6) are printed and nearly assembled. Everything from the elbow forward weighs about 1.3 kg before the hand (the user's scale, with the T8 cut to length), far less than V1. This design adds the elbow and a new upper arm to carry that forearm, so the whole arm can come together and the weak links can be found by running it. Torque gets tuned afterwards by swapping motors, not by up-front oversizing.

The shoulder end of the upper arm is designed here only as a bearing interface; the shoulder's drive is the next design.

## Goals

- Axis 3 lifts the forearm, wrist, hand and a light tool (100–200 g) through about 170°: from 20° back past vertical to 150° forward of it. Home is the forearm straight up, in line with the upper arm.
- Light and stiff: every gram here loads the shoulder.
- The forearm's weight is carried on both sides of the elbow, so the compact's own bearings only turn it.
- A motor can be swapped for a longer NEMA17 later without redesigning the plates.
- Wires can pass through the centre of the elbow and the shoulder.

## Non-goals

- The shoulder drive (axis 2): its motor (the user wants to try a 48 mm NEMA17 first, as on the elbow, stepping up to a NEMA23 only if it falls short), gearbox and mounting to the body come next. This design fixes only the upper arm's side of the shoulder bearings.
- A counterbalance spring. Decided against for now; added only if the bench shows the motor short.
- Encoders. Homing is by Hall sensor.
- Changes to the built forearm and wrist parts. The bracket attaches without taking anything apart.

## Anti-goals

- A beefier or new cycloidal. The user stress-tested the 20:1 compact by hand with a lot of force and it held; it is not the weak link.
- Sizing the elbow up-front for a 500 g payload. The payload is light tools.

## Constraints

- **Forearm attachment point:** the elbow attaches to the axis 4 compact's housing at the back of the forearm (`tools/blender/forearm_dims.py`, `forearm_tube.py`; spec `2026-11-15-axis4-forearm-tube-design.md`). The housing is Ø68 × 38.6, with four M3 through-holes on R30 at 45° + 90k. The fixed outer tube bolts to its front on those holes, and `model/forearm-tube/ax4-motor-mount-60T.stl` bolts to its rear, with the axis 4 pancake on top. The housing does not rotate; the drive tube inside it does.
- **Forearm mass:** about 1.3 kg forward of the elbow without the hand. The hand is about 0.4 kg; the tool 100–200 g. The wrist pitch axis is 276.6 mm along the forearm from the front of the axis 4 compact's housing (forearm x).
- **Elbow gearbox:** the 20:1 compact (`tools/blender/cycloid_poc.py`, no flags), built with the short eccentric and the lip between the disk bearings, as on axis 5. Output face: three M3 × 3 × 4.5 inserts on R6.5 at 90°, 210°, 330°, and the forearm's output plate pattern of three dogs (Ø5 × 4) on R10.5 at 30°, 150°, 270°.
- **Elbow motor:** a 48 mm 17HS8401B NEMA17 (42.3 square, Ø5 shaft, M3 on a 31 mm square).
- **Belt:** a 3M 20T on the motor and a printed 3M 60T on the compact's Ø5 input rod, over a 420-3M-9 belt: 60:1 total, centres about 149 mm. The 60T fixes to the rod like the axis 4 and 5 60Ts (radial heat-set insert and set screw on a flat).
- **Axis 4's bolt stack is full:** the four R30 bolts run through the outer tube's 5 mm flange, the 38.6 housing and the 6 mm `ax4-motor-mount-60T`, 49.6 mm on an M3 × 50. Nothing can be added to that stack, and the compact's printed housing must not be clamped (it carries the gearbox).
- **Outer tube** (fixed, printed, built): flange at the housing's front face, then a Ø36 rear section holding the rear 6701, then Ø25 out to the wrist.
- **Bearings in hand:** 8 × 6810-2RS (50 × 65 × 7, measured).
- **Aluminium tube in hand:** 9 OD × 7 ID, 250 mm lengths (can be cut, for example into 125s).
- **Measured torque:** a pancake at 40:1 on a compact held about 1.2 N·m (torque test, 2026-11-15), and the pancake skipped, not the compact. Nothing has been measured with the 17HS8401B. My estimate, about 7 N·m at 60:1, already starts from that measured figure (scaled by the two motors' holding torques and the ratio), not from the datasheet.
- **Load:** my estimate is about 5.5–6 N·m static with the forearm level, hand and 200 g tool on. The layout check computes it from the parts.
- **Printers:** Bambu P2S or A1, bed 225 × 255. PLA. The user's M3 bolts go up to 50 mm (40, 45 and 50 in stock); longer joints end in hex nut pockets, short screws go into heat-set inserts.

## Decided by the user

- Redesign everything above the shoulder drive: V1 is a reference, not a constraint.
- **Gearbox:** the 20:1 compact, unchanged.
- **Motor:** the 48 mm 17HS8401B. If the elbow comes up short, swap to a longer NEMA17 (the mount must allow that).
- **Belt:** 3M 20T/60T on the 420-3M (60:1), motor below the elbow on the upper arm. A belt tensioner.
- **Upper arm:** 220 mm, shoulder axis to elbow axis. Two side plates, each printed in one piece (on the bed diagonal if needed).
- **Elbow layout (layout B from the 2026-11-15 mockups):** the compact sits between the plates. Its rear face and the motor's face bolt to plate A's inner face. Both pulleys and the belt run outside plate A. The forearm bracket bolts to the compact's output and is carried on its other side by a bearing in plate B.
- **Elbow support bearing:** a 6810 in plate B.
- **Shoulder end:** two 6810s, spaced apart on a Ø50 hollow hub, one in each side plate, so the arm's bending load goes into the bearings, not the shoulder gearbox. The body holds the hub from both sides of the upper arm, as on V1. The shoulder drive fits into this later.
- **Forearm offset:** the forearm's roll axis sits 80 mm from the elbow axis (V1: 102). The axis 4 compact and its motor sit slightly behind the elbow axis as a partial counterweight.
- **Forearm bracket:** a printed collar on the forearm's outer tube, in front of axis 4's housing, and a printed elbow hub, joined by 9 × 7 aluminium tubes glued into sockets. The tubes run in a V, two per side, landing in front of and behind the elbow axis, so the elbow's torque goes mostly along the tubes rather than bending them at their sockets. The elbow hub bolts to the compact's output on plate A's side and turns in the 6810 on plate B's side.
- **Upper arm framing:** 9 × 7 aluminium tube can be used between the plates as supports or framing, cut from the 250 mm stock (for example 125 mm halves).
- **Bench stand:** a simple printed stand holds the upper arm by its shoulder hub at a few fixed shoulder angles, so the elbow can run before the shoulder drive exists.
- **Range:** 20° back past vertical to 150° forward, home straight up.
- **Homing:** Hall sensor and magnet.
- No counterbalance spring for now.

## My calls (the user has not reviewed these)

- **Belt tension:** slotted motor holes in plate A for tensioning, plus a screw-adjusted idler. No spring.
- **Hard stops:** printed, just past each end of the range (−22° and +152°), on the bracket and a plate.
- **Hall homing:** the magnet on the bracket, the sensor on plate B.
- **Cross members:** aluminium tube spacers between the side plates (in printed bosses, bolted or glued), at least one near each end, so the plates stay parallel. A plate can come off for service if they're bolted.
- **Wires:** through the bore of plate B's 6810 at the elbow and the Ø50 hub at the shoulder. Exact routing is the builder's.
- **Collar grip:** the collar sits against the front face of the outer tube's flange, with recesses keyed over the four R30 bolt ends so it can't turn, and a light split clamp on the Ø36 section. The clamp stays off the rear 6701's seat. The collar adds nothing to the bolt stack, and the built axis 4 parts are unchanged. The forearm's weight goes from the collar into the outer tube, through its flange and bolts into the housing, the same path the wrist's weight already uses.
- **Tube joints:** epoxy or CA in printed sockets about 15 mm deep, as on the forearm's glued joints. The check reports each tube's axial load and bending at the socket at the worst pose.
- **Output joint:** about 9 N·m (1.5× the static load) through the compact's output face is far more than the forearm's axis 4 joint carries. The torque should go through the dogs, not the three M3 inserts; the builder checks the dogs' bearing stress in PLA and enlarges them, or adds more on the hub's side, as needed. The 6810 side of the hub also shares the bending load.
- **Shoulder hub on the belt side:** the elbow motor sits about 71 mm from the shoulder axis, and its 20T, idler and belt stand out about 15–20 mm from plate A. On that side the hub runs out beyond the belt plane, so the body's support sits outside the belt with a clear gap, and nothing sweeps into the body at any shoulder angle. This design defines the hub's length, both end interfaces and that cleared envelope; the shoulder drive designs to them.
- **Spare capacity:** plate A's motor mount leaves room for a NEMA17 up to 60 mm long. No spring anchors or alternative pulleys are designed in.
- **Run current:** the 17HS8401B runs at its rated current on whichever Octopus driver it's given; that's a firmware setting, not part of this design.
- **Stand:** clamps to the bench with the user's Irwin clamps, as the base legs do, and pins the hub at home, 0°, 45° and 90° of shoulder pitch.
- **Generator and checks:** a new script in `tools/blender/` in the style of `wrist.py`: STLs in `model/elbow/`, checks for non-manifold, bearing seats, belt centres, clearances through the whole range (the forearm and wrist against the upper arm), and a report of the elbow torque at the worst pose against the estimated capacity. Then lay it out in `head_concept.py` with the offset wrist.

## Left to the builder

- Plate shapes, thicknesses, lightening, and how the cross members join.
- The collar and hub shapes, the tubes' exact angles and lengths, and whether a tube or two crosses between the two V's, as long as the hub carries load on both sides of the elbow.
- The stand's shape.
- The idler's position and the slot length.
- The shoulder hub's exact form and the spacing between its two 6810s, leaving room for a drive.
- The hard stops' and the Hall sensor's exact positions.
- Print orientations and a print sheet, as for the wrist.
