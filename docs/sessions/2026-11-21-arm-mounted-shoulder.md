# Session handoff: arm-mounted shoulder and V1-style base (2026-11-21)

## State

- **Spec:** `docs/superpowers/specs/2026-11-21-arm-mounted-shoulder-v1-base-design.md` (0fad9f6, approved).
- **Plan:** `docs/superpowers/plans/2026-11-21-arm-mounted-shoulder-v1-base.md`. It ran inline on main; the user approved committing per task without asking.
- **Commits (all local, not pushed):**
  - 47c8e5a: Task 0, the bench-reach sweep over φ, plus the plan
  - 52211e7: Task 1, the upper plates
  - bf263c5: Tasks 2 and 3, the shoulder joint and the base
  - ef95e8b: Task 4, `head_concept --shoulder`
  - 3c1dbb4: Task 5, the print sheets and plates
- **Ledger, with every ruling:** `.superpowers/sdd/2026-11-21-arm-mounted-shoulder-v1-base/progress.md`. The final review isn't in it yet.
- **All generators pass:** `elbow.py` (ELBOW DONE), `shoulder.py` (SHOULDER DONE, about 2 min), `head_concept.py -- --shoulder` (HEAD DONE, about 49 min). The other five head variants are identical to their baselines.

## What got built

- **Shoulder:**
  - The compact's rear face bolts to plate B; the NEMA17 sits on plate B at elbow z −88.1 (131.9 from the shoulder). The 20T/80T belt runs outside plate B, with no idler.
  - The fixed `shoulder-hub` turns in plate A's 6810. The keyed `shoulder-lug` clamps that bearing and carries the stop tab and the magnet.
  - Three tubes run from the lug to `shoulder-socket-bracket`, which sits on an ear of the turntable. There's no room for a V, so the tubes run sideways to two towers.
  - `shoulder-rod-post` carries a 625 on the input rod, which stands 43.5 out of the housing.
  - The stops are at ±93, with the blocks on plate A.
- **Base:**
  - `base-ring-130T` and its cylinder are one part. They run on two 6810s in the drum's hub tube, 50 apart, clamped by `base-spacer` and `base-retainer`.
  - The ring's thick top flange keeps the stop tab above the belt.
  - The base motor hangs under the shelf, turned 45° (so its screws sit between the belt's spans), beside the drum's flat at r80. It has a clamp plate and no push screw.
  - The shoulder axis is 156.5 above the bench (it was 219.5).
- **Whole-arm results:**
  - Bench reach is 161 mm at φ 0, and 219 mm at the worst φ.
  - 2448 of 3885 poses are over the NEMA17's capacity (worst 12.5 N·m).
  - Tipping margin is −81 mm: clamp the feet.

## Next: the final review's fix pass (one pass, each fix gets a failing check first)

**Critical:**
1. **The base spacer can't be fitted in the order the sheet gives.** The spacer is r26.8 and the lower 6810's bore is r25. New order:
   1. Upper 6810 in from the top.
   2. Lower the cylinder through it.
   3. Tip the drum and slide the spacer up through the open lower seat.
   4. Press the lower 6810 onto the cylinder and into its seat.
   5. Fit the retainer.
   - This touches `model/shoulder/PRINT.md` step 2, and possibly a check that the spacer passes the lower seat.
2. **The bracket's tubes can't be assembled.**
   - The sockets are blind, the tubes point different ways, and there's no slack.
   - Fix: bore the front tower's sockets through, as on the elbow (`THROUGH_SOCKET`), re-cut the tubes, and hang the bracket on the rear tube first. Alternatively, split the bracket.
   - Add an insertion check: each tube can slide in along its axis with the others in place.

**Important:**
3. **No screw-access check for the shoulder motor's four M3s against `sh_belt_envelope(±1)`.**
   - The plan required one. Its two inboard screws likely sit under the 80T belt hull by about 1 mm.
   - The fix may be a 45° motor turn, as on the base.
4. **The rear bracket tower bends at about 17 MPa** (218 N, 61 mm up, a 19 × 13 section), against the 10 MPa rule.
   - Deepen it, or bridge the two towers.
   - Add a bending assert.
5. **`head_concept.shoulder_body()` doesn't draw the three bracket tubes**, so soft limits, reach and tipping miss them. Add them from `S.TUBE_ENDS` to `SH_COL`.
6. **The sheet's order clamps the feet in step 1,** then needs the drum tipped or lifted (the spacer, and the motor offered up from below, which hangs 8.5 off the bench). Move the clamping to the end.

**Minor (ledger as deferred unless they're cheap):**
- **Post lip:** the sheet says 1.5, the code says 1.0.
- **Cross members:** they're glued in two places (elbow sheet step 6 and shoulder sheet step 4).
- **Checks that can't fail:**
  - `flat_gap` is pure arithmetic.
  - The "motor and compact once" count uses a literal list.
  - `base_screws_reached_at_phi` is hardcoded.
- **Base gaps:** ≥1.0 is checked only every 10°, and the legs against the motor are checked for overlap only.
- **Rod side load:** it omits the plan's half arm weight. Ledger a ruling.
- **The post over-constrains the rod:** slot the post's holes and tighten it last.
- **`SH_MOTOR_L_MAX` 59:** the elbow idler's nut is in the way. Drop the claim.
- **Sheet notes:**
  - which way the motor connector faces
  - ream the lug inserts after pressing
- **Dead constants:** `HUB_SHOULDER_R`, `WALL_LIP_R`, `BODY_MIN`, `M5_CLEAR_R`, `PULLEY80_Y`, a stale "plate 5" comment, and plate B's obsolete index holes.
- **Stale renders:** they're still from de9edf8. Re-run `head_concept.py -- --shoulder` after the fixes.

**Reviewer declined to judge:**
- the printability of the ring's lower cone overhang
- the axial stack between the two hubs
- the compact's output bearing taking plate B's share of the arm moment
- the look of the sideways-tower bracket, which is the user's call

## Gotchas

- **Exact booleans:**
  - Seams from a chamfer added with `union` plus a 0.01 overlap break later cuts. Use `hull([...])`.
  - A cone with 192 segments put an edge on a 90° counterbore's line. Use n=190.
  - A cut that ends exactly on a face leaves open edges.
- **`min_gap` measures one way, vertex to face.** It misses clearances between a box and a cylinder side by side. Use `box_gap` (elbow.py) or both directions.
- **After a `--shoulder` run, don't `git checkout -- model/head-concept/` wholesale:** that wipes the fresh shoulder renders.
- **The Bambu profiles in the scratchpad were lost and rebuilt.** `bambu/flatten.py` writes them with `"from": "system"`. The plate script is `scratchpad/plates9.sh`.
- **Scratch runners:** `scratchpad/run_shoulder_scratch.py` and `run_elbow_scratch.py` redirect OUT and ELBOW, so a check can run without touching `model/`.
- **Never commit the user's unrelated work:** the hand files, `spider_base.py`, `model/base/spider-arm-motor.stl`, `hand_lib.py`, the 2026-09 docs, `CyBoT notes.pages`, `exploded.png`, `finger-coupon-scene.blend`, `result.json`, `.superpowers/`.
