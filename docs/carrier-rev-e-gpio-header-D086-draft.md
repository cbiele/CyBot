# Draft for Chopaka Labs — D-086 + Rev E spec §4.7

> **ADOPTED 2026-09-05** — committed to Chopaka main at 54efffe (ERC 0
> errors). The Chopaka repo is now the authority; this file is the Cybot-side
> record. Two founder amendments supersede the text below:
>
> 1. **`J_GPIO1` ships POPULATED on the first Rev E run** — a plain 1×10
>    2.54 mm pin header (not JST-XH), vertical, ~8–9 mm proud (right-angle
>    fallback if the enclosure objects). DNP is a per-run checkbox flipped
>    before regenerating `production/`, not a design property.
> 2. **The GPIO45 strap pulldown lives on the carrier:** `R_PD45`, 10 kΩ,
>    GPIO45→GND, permanent. The Cybot daughterboard must NOT add a second
>    pulldown and must budget ~0.33 mA whenever it drives GPIO45 high.
>    Conditioning, protection and terminations still belong to the
>    daughterboard.
>
> Also confirmed available to Cybot: `J_EXP1` (8-pin JST SH 1.0 mm: 3V3,
> TCA9535 P05/P06/P07/P15/P16/P17, GND) — expander spares, idle as
> driven-low outputs, fine for static I/O such as driver enables or limit
> switches.

Prepared 2026-09-05 from the Cybot project. Two blocks below: (1) a decision
entry in DECISIONS.md house style, to append after D-085; (2) a new §4.7 for
`docs/superpowers/specs/2026-08-31-carrier-rev-e-port-switching-design.md`,
plus a one-line addition to §7 Acceptance. Everything here was verified
against the Rev E schematic (`HelcatCarrierBoardPCB-PakaNodeV1.kicad_sch`,
commit c10ef45), the Heltec V4.2 schematic, and the V4.3.1 datasheet pin
table.

---

## Block 1 — DECISIONS.md entry

## D-086 — Rev E exposes the idle Heltec pins on a DNP header

**Date:** 2026-09-05
**Status:** Accepted (founder-approved 2026-09-05), copper pending in Rev E

Adds one **do-not-populate 1×10 0.1″ through-hole header (`J_GPIO1`)** to
the Rev E carrier, wired to the seven Heltec socket pins the carrier
otherwise leaves flagged no-connect, plus GND, 3V3 and VDD_5V. Zero BOM
lines, zero placement, no change to any populated net. Extends D-085's
"last spin before launch" without adding a first-article risk.

**Why.** The carrier is also the host for the founder's Cybot robot-arm
project (a 7-stepper, 3-encoder ESP-IDF build on the same Heltec V4). That
build needs roughly eleven GPIOs that the Rev D/E copper does not reach:
three for an I²S shift-register step/dir bus, one for a shared TMC2209
UART, two for a UART to a camera or motion board. Rev E connects only
GPIO4/5/6, 33, 43/44 and 47/48 to the socket; **GPIO26, 38, 39, 40, 41,
42 and 45 sit under no-connect flags** on pins that are physically
adjacent on `JP5`. Bringing them to a DNP header is the cheapest possible
moment to do it and the only moment before launch.

1. **Pins.** `J_GPIO1` pin 1 = GND, 2 = VDD_3V3, 3 = VDD_5V, 4 = GPIO26
   (`JP4.15`), 5 = GPIO45 (`JP5.6`), 6 = GPIO42 (`JP5.7`), 7 = GPIO41
   (`JP5.8`), 8 = GPIO40 (`JP5.9`), 9 = GPIO39 (`JP5.10`), 10 = GPIO38
   (`JP5.11`). Power on the end pins so a reversed header lands on rails
   that survive it (same rule as `J_EXP1`).
2. **DNP by construction.** The footprint carries a DNP attribute and is
   excluded from `production/` BOM and CPL. PakaNode ships with bare
   holes. Populating it is a bench/Cybot operation, never a PakaNode SKU
   variant, so D-028's "identical ports, no board variants" stays intact.
3. **What is deliberately not on it.** GPIO34 (drives the GNSS power FET
   gate through a 10 k pull-up — loaded, and already on the Heltec's own
   GNSS port), GPIO37/GPIO1 (VBAT divider), GPIO3/GPIO0/GPIO46 (strapping
   or boot), GPIO35/36/21 (firmware-owned LED, Vext, OLED reset). Nothing
   from J4/J5, the TMUX front end, or the expander bus is touched.
4. **Consequences.** GPIO39–42 are the ESP32-S3 JTAG pins and GPIO38 is
   GNSS RX. An unpopulated header is high-impedance and changes nothing
   for PakaNode. A *populated* header means: no external JTAG debugger
   (USB-Serial-JTAG over the Heltec USB-C remains, which is already the
   console path per D-084 Phase A), and no L76K GNSS on GPIO38 (a Cybot
   build carries no GPS; PakaNode never populates the header). GPIO45 is
   the VDD_SPI strap — any load on it needs a 10 k pulldown so the boot
   level stays defined, same rule as the old `IO_CTRL1` note.

**Out of scope:** motor supply, drivers, shift registers, any populated
part. Those belong on a daughterboard that plugs into `J_GPIO1` and
`J_EXP1`. 24 V never touches the carrier.

**Layout note:** `JP5` pins 6–11 are contiguous, so the six GPIO traces
run as one short parallel bus beside the socket; GPIO26 is a single trace
from the `JP4` row. Place `J_GPIO1` on the board edge nearest `JP5`
wherever the Rev E part additions leave room. No rotation-sweep entry is
needed (nothing is placed), but the footprint still goes through the JLC
placement preview so the DNP flag is confirmed to suppress it.

---

## Block 2 — Rev E spec addition

### 4.7 `J_GPIO1` — idle Heltec pins on a DNP header (D-086)

A 1×10 0.1″ through-hole header, **do-not-populate**, breaking out the
Heltec socket pins the carrier otherwise leaves no-connect. Bare holes on
every PakaNode; populated only on bench or Cybot builds.

| `J_GPIO1` pin | Net | Heltec socket pin | GPIO | Notes |
|---:|---|---|---|---|
| 1 | `GND` | JP5.1 | — | End pin (reversal-safe) |
| 2 | `VDD_3V3` | JP5.2 | — | Always-on 3.3 V |
| 3 | `VDD_5V` | JP4.2 | — | USB/solar 5 V rail |
| 4 | `GPIO26` | JP4.15 | 26 | Clean GPIO, no onboard function |
| 5 | `GPIO45` | JP5.6 | 45 | VDD_SPI strapping pin — output only, 10 k pulldown on any load |
| 6 | `GPIO42` | JP5.7 | 42 | MTMS (JTAG); GNSS_RST on the Heltec GNSS port |
| 7 | `GPIO41` | JP5.8 | 41 | MTDI (JTAG); GNSS_PPS |
| 8 | `GPIO40` | JP5.9 | 40 | MTDO (JTAG); GNSS_Wakeup |
| 9 | `GPIO39` | JP5.10 | 39 | MTCK (JTAG); GNSS_TX |
| 10 | `GPIO38` | JP5.11 | 38 | GNSS_RX; no JTAG function |

**Rules.**
- DNP attribute set; excluded from `production/` BOM and CPL. Verify on
  the JLC placement preview that it does not appear.
- Nets are new global labels (`GPIO26`, `GPIO38` … `GPIO45`) that touch
  nothing else on the board. Replace the seven existing no-connect flags
  on those socket pins; ERC must stay clean.
- No pulls, no series resistors, no protection on the carrier. The
  consumer daughterboard owns all of that (GPIO45's pulldown included).
- Pins 6–9 duplicate the ESP32-S3 JTAG lines. Populating the header
  forfeits an external JTAG probe; USB-Serial-JTAG is unaffected.
- Pins 6–10 duplicate the Heltec's SH1.25 GNSS port. A build using both
  gets the same six GPIOs twice — that is fine as long as only one
  consumer drives each.

**Excluded on purpose:** GPIO34 (loaded by the GNSS FET gate), GPIO1/37
(battery divider), GPIO0/3/46 (boot/strapping), GPIO21/35/36
(firmware-owned). GPIO43/44 and GPIO4/5/6 are already committed to the
ports and solar gate.

### §7 Acceptance — add one line

11. `J_GPIO1` is absent from the JLC placement preview and the fabricated
    board has ten bare plated holes at its location, each continuous to
    the Heltec socket pin in the §4.7 table (bench continuity check on
    the first article).
