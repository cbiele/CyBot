# Axis-1 spider base — design

Date: 2026-09-23. Status: approved in conversation, awaiting the implementation plan.

## 1. Summary

A printed standalone base for axis 1 that replaces the Cults base plate and its
motor holder: a Ø200 ring that the Cults `axis1-baseHolder` bolts to, four
separate truss arms that plug into the ring, and one of those arms carrying
the NEMA17 for the axis-1 belt drive with the motor mounted upside down above
its plate. Six PLA prints, four TPU foot pads, nothing below the base plane.
It stands on its own pads now and bolts to a plate later through the same foot
holes.

## 2. Why this shape

- **The Cults motor holder does not work with this motor.** Measured from
  the STL: it is a closed box with a 5 mm top plate, open only underneath, and
  its wall on the base side is solid top to bottom. The motor hangs under the
  plate and the pulley runs above it, 42 to 54 mm above the holder's foot. The
  rotating base's toothed band sits 30 to 41 mm above the base holder's foot.
  On a common plane the belt is about 11 mm off, and the 48 mm 17HS8401B
  pokes 14 mm below the holder's foot, 24 mm with its rear stub.
- **Motor upside down.** Motor on top of a plate, shaft down through it, the
  pulley hanging in free air at the band height. No pocket, no plate cutout,
  belt path with nothing in it, and the robot's centre of mass stays where the
  Cults design put it.
- **Ring plus separate arms.** Every part fits a 256 mm bed. The ring carries
  the base holder's bolt pattern; the arms carry the footprint. One arm file
  prints three times.
- **Height for stiffness, not clearance.** Static tipping depends on the
  centre of mass over the footprint, not its height, so the 35 mm ring costs
  nothing there. Arm bending is what the height buys: 260 mm arms with 35 mm
  rails at the root flex about 1.3 mm under 60 N at a foot, four times that at
  15 mm.
- **No cross struts.** Struts stiffen the frame against racking and add four
  joints; they do nothing against tipping or arm bending. The foot's outer
  face stays flat so a strut or a clamp can bear on it if the standalone test
  asks for one.

## 3. Scope

In: ring, plain arm, motor arm with its bracket, foot pad plug, generator
with self-tests, print rules, bench acceptance, hardware.

Out: the axis-1 stack itself (`2-axis1` prints unchanged except that
`axis1-stepperHolder` and `axis1-encoderHolder` are no longer used), the
belt length (measured on the built base, build plan phase D), the plate.

## 4. Architecture

```
ground ── 4 TPU pads ── 4 truss arms (260 mm) ── tenons into ── Ø200 ring (35 mm)
                          │                                        │ 8 × M5 on Ø141
                          └─ motor arm: bracket plate 53 mm up ──  axis1-baseHolder (Cults)
                                NEMA17 on top, shaft down,          rotatingBase1 band
                                3M 30T pulley at 30-41 mm ── belt ── 30-41 mm above ring top
```

Base plane = ring top face. All heights below are above that plane unless
stated. Arms at 0°, 90°, 180°, 270°; the motor arm at 180°, the Cults side.

## 5. Components

### 5.1 Ring

| Item | Value |
|---|---|
| Envelope | Ø200 outside, Ø50 centre hole, 35 mm tall |
| Construction | 4 mm top plate, 3 mm outer and inner walls, eight radial ribs, open underneath |
| Base holder bolts | 8 × Ø5.5 on Ø141 at the Cults angles: pairs at 11.3° and 33.7° from each 90° step; M5 hex nut pocket under each, reached from the open bottom; Cults M5 × 20 |
| Arm facets | at 0/90/180/270°, the outer wall flattened over 60 mm width (which puts the face at 95.4 mm radius) and thickened to an 18 mm deep boss |
| Mortise | 40 wide × 27 tall (z 4 to 31, a 4 mm sill below and the top plate above), 14 mm deep, blind: a 4 mm back wall closes it toward the cavity |
| Joint bolts | 2 × M5 × 20 per facet, radial through the back wall, heads inside the ring cavity, at mid-height, 28 mm apart so the holes clear the mortise cheeks, into cross nut pockets in the tenon |
| Mass | about 300 g |

The base holder's bottom flange is 10 mm thick with the Ø5.5 holes straight
through it and its Ø30 × 16 pockets at 22.5° + 45k, so no pocket lands on an
arm axis and the bolts come down from above.

### 5.2 Plain arm (×3)

| Item | Value |
|---|---|
| Length | 260 mm from the facet face (97 mm radius) to the foot end (357 mm) |
| Rails | 5 mm thick, 35 mm tall at the root tapering to 15 mm at the foot, 60 mm apart at the root spreading to 90 mm at the foot |
| Web | Warren diagonals 3 mm thick, four bays |
| Skin | 2 mm bottom skin, closing the section into a channel |
| Foot | 90 × 25 × 8 mm, Ø5.5 through the centre with a Ø10 × 3 counterbore on top; outer face flat and vertical |
| Root plate (added 2026-09-24) | 6 mm end plate closing the root of the channel section, full width and height; the tenon grows out of its outer face and the rails, skin and web start inside it |
| Tenon | 39.7 × 26.7 × 13.7 mm (0.3 mm under the mortise in every direction), two M5 cross nut pockets 6.5 mm from the end, open at the top so the nuts drop in before the tenon slides home |
| Mass | about 185 g |

Fits the A1 laid on the bed diagonal: length plus foot width over 1.41 is
under 250 mm. `ARM_LEN` is one constant in the generator.

### 5.3 Motor arm (×1)

The plain arm plus a bracket. Radii are from the base axis.

| Item | Value |
|---|---|
| Walls | 2 × 4.4 mm standing on the rails (inset 0.3 mm from the rail faces), from 108 to 177 mm radius, vertical |
| Plate | 5 mm, top face 53 mm above the ring top, underside at 48 |
| Motor axis | 139 mm radius, the Cults distance, so the ~620-3M belt estimate stands |
| Pattern | NEMA17, 31 mm square, four 3.4 × 8 mm radial slots for ±4 mm belt tension |
| Pilot | Ø23 |
| Motor | 17HS8401B on top, flange on the plate, body 53 to 101 mm, rear stub to 111 mm, leads outboard |
| Pulley | 3M 30T, 5 mm bore, on the 24 mm shaft below the plate; 6 mm hub against the plate underside at 42 to 48, teeth 30 to 42 mm above the ring top, shaft tip at 29 |
| Belt clearance | the belt runs cross the wall plane between 108 and 125 mm radius, so both walls have a window from 108 to 136 mm radius between 23 and 49 mm above the ring top; the plate bridges it. The wall at 108 mm radius is 23 mm clear of the Ø170 skirt |

### 5.4 Foot pad plug (×4, TPU)

Ø24 × 6 mm disc with a Ø5.8 × 8 mm peg ending in a Ø7 mushroom. Pushed up
through the foot hole from below; pulled out when an M5 × 25 goes through
instead. Lifts the spider 6 mm.

### 5.5 Cables

Down the base holder's Ø50 centre hole into the ring cavity, out between two
arms at ground level.

### 5.6 Hardware

| Part | Qty | Note |
|---|---|---|
| M5 × 20 + nut | 8 | arm joints, through the 4 mm back wall of each mortise |
| M5 × 20 + nut | 8 | base holder, already on the Cults list |
| M3 × 10 | 4 | motor |
| 3M 30T pulley, 5 mm bore, 12 mm | 1 | phase D list; confirm one is in hand |
| HTD 3M belt, about 620 mm | 1 | measure on the built base |
| M5 × 25 | 4 | only when a plate is used |

## 6. Generator

`tools/blender/spider_base.py`, run headless like the hand scripts, writes
`model/base/spider-ring.stl`, `spider-arm.stl`, `spider-arm-motor.stl`,
`spider-pad.stl`, and renders an assembled view with the Cults base holder and
rotating base placed on it. Self-tests, all asserted:

- every part manifold
- each arm's bounding box on the diagonal under 250 mm
- the four pattern holes land on a 31 mm square about the 139 mm axis
- pulley teeth computed at 30 to 42 mm above the ring top from the plate
  height, hub length and shaft length, and the shaft tip below the teeth
- a ray cast along the belt line from the pulley tangent to the rotating base
  band hits nothing but the two
- mortise minus tenon equals 0.3 mm in width, height and depth
- bore measurements use a median over rays offset from the polygon vertices, because a ray that
  lands exactly on a vertex passes through the mesh

## 7. Print rules

- Ring: top plate down, 0.2 mm, four walls, 30 % gyroid. Nut pockets print
  as blind hex holes facing up.
- Arms: flat on the skin, on the bed diagonal, 0.2 mm, five walls, 30 %.
  The motor arm's walls stand vertical and print with it.
- Pads: PolyFlex TPU95A on the A1, disc down.
- No supports on any part by design.
- About 1.1 kg of PLA for the set.

## 8. Risks

- **Tenon fit.** 0.3 mm total clearance is a guess for this printer; the
  first plain arm is the coupon. Too tight, sand; too loose, the bolts still
  clamp it and the ring's second bolt pair goes in.
- **Tipping at full reach.** The 715 mm footprint is close to balanced with
  the robot's mass near the axis. The bench test says whether a clamp on the
  far foot is routine; the foot is designed for one.
- **Belt height.** Derived from STL heights of parts whose native
  coordinates do not agree with each other. The band height is measured from
  the base holder's own geometry, which is trustworthy, but the first fit
  check is against the printed parts, with a 3 mm shim under the motor as the
  fallback.
- **Bracket wall stiffness.** Belt tension loads the walls in their own
  plane, the strong direction; a stall at 1.8 A puts under 100 N on them.

## 9. Rejected alternatives

- **Riser with the motor hanging below.** Needs a plate cutout, and the Cults
  holder's belt height is wrong on a common plane anyway.
- **Reusing `axis1-stepperHolder`.** See §2; the printed one is spare.
- **Cross struts between the feet.** No help with tipping or bending; kept
  as a bolt-on if the standalone test wants it.
- **Two crossed bars under a ring.** Every split is a joint; the motor well
  lands on a splice.
- **300 mm arms.** Only with a 50 mm foot on this bed.

## 10. Acceptance (bench)

1. Each tenon dry-fits its mortise by hand and seats to the boss face.
2. Bolted up, a straightedge across opposite arms shows the ring top flat
   within 0.5 mm.
3. With the base holder and rotating stages fitted, 60 N sideways on a foot
   with the luggage scale moves the ring under 1.5 mm.
4. Belt centred on the band, no rub on the near wall, no walk after one
   minute of axis 1 at bench speed on the Octopus.
5. Stands on its pads with the arm folded; with 2 kg held at 500 mm reach it
   stays or the far foot gets a clamp, and the result goes in the build plan.

## 11. Phasing

1. Generator, ring and one plain arm; dry-fit the tenon and set the clearance.
2. Remaining plain arms, the motor arm, the pads; bolt up, flatness check.
3. Base holder and rotating stages on; stiffness and tipping tests.
4. Motor, pulley, belt; axis 1 on the Octopus (X on MOTOR0).

## 12. Open items

- Whether a 30T 5 mm bore pulley is in hand or needs ordering.
- Belt length, measured on the built base.
- Whether the plate is still wanted at all; if so, a short arm set from the
  same generator.
