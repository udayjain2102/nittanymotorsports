# NM26 versions: what changed between each one

Two numbering schemes exist, so both are listed here:
- **Frame versions** (`frame_v1` to `frame_v5`) are frozen copies of the whole `mule/` folder in `history/`, each with a
  git tag of the same name. Numbers below come from running each frozen copy's own code (2026-10-03).
- **Fusion uploads** (`NM26_Assembly_v1` to `_v8`) are the CAD files in Fusion, `adi laptop files > Nittany Motorsports`
  (older ones in `adi laptop files`). Nothing has been deleted from either. Dates marked ≈ predate git and come from
  the project log, not timestamps.

## Which Fusion file shows which frame

| Fusion file | Uploaded | Frame inside | Wing | Notes |
|---|---|---|---|---|
| `NM26_FSAE_Concept_original` | ≈ 27 Sep | the team's concept STEP | no | Starting point; critiqued in BUILD_PLAN §1. `_first_import_sideways` is the same file before the Y-up fix |
| `NM26_Frame_only_FEA_model` | ≈ 27–28 Sep | early frame, tubes only | no | Fusion simulation cross-check; abandoned after an Autodesk server error on every solve |
| `NM26_Mule_simple_v1` to `_v3` | ≈ 27–29 Sep | early frame, simple model | no | Simple one-colour-per-system model during the first design pass; the repo does not record what differs between the three |
| `NM26_Assembly_v1_no_wing` | 29 Sep | pre-wing frame | no | First detailed assembly |
| `NM26_Assembly_v2_first_wing` | 29 Sep | first frame with the wing | yes | Rear wing and DRS added at the team's request (PROJECT_LOG step 29) |
| `NM26_Assembly_v3` | — | — | — | Does not exist: the 29 Sep 10:17 PM upload never finished and vanished from Fusion |
| `NM26_Assembly_v4` (+ `_part2`, `_part3`) | 29 Sep 10:28 PM | **frame v1**, 50.1 kg | yes | Detailed CAD pass (15-part engine, routing). Fusion split the large STEP into three files |
| `NM26_Assembly_v5` | 1 Oct 7:18 PM | **frame v3**, 44.3 kg | yes | C2 node-mounted rear. Frame v2 (46.4 kg) was never uploaded |
| `NM26_Assembly_v6` | 2 Oct 5:05 PM | **frame v4**, 50.4 kg | no | Post-audit frame. Still shows a stray magenta wire above the main hoop (DRS servo wiring left in the CAD) |
| `NM26_Assembly_v7` | 3 Oct | **frame v4**, 50.4 kg | no | Same as v6 without the stray DRS wires |
| `NM26_Assembly_v8` | 12 Oct | **frame v5**, 49.4 kg | no | Topology frame: front-bay diagonal pair gone, spool carrier posts end at the spool (upper half gone). **Current** |

## Frame versions at a glance

| | v1 | v2 | v3 | v4 | v5 |
|---|---|---|---|---|---|
| Date, commit | 30 Sep, `6958de2` | 1 Oct, `95d2f37` | 1 Oct, `fce6480` | 2 Oct, `d9d45c2` | 10 Oct, merge of `topo-experiment` |
| Frame tube mass | 50.1 kg | 46.4 kg | 44.3 kg | 50.4 kg | 49.4 kg |
| Members / cut pieces | 146 / 81 | 143 / 78 | 126 / 73 | 128 / 73 | 124 / 71 |
| Torsion (FEA) | 2138 N·m/deg | 2004 | 1946 | 2422 | 2399 |
| Roll-over FoS main / front | 1.28 / 1.36 * | 1.08 / 1.02 | 1.09 / 1.02 | 1.23 / 1.18 ** | 1.22 / 1.11 ** |
| Frontal impact 95 kN | not checked | not checked | not checked | 1.31 | 1.26 |
| 20 g harness FoS | 1.17 (80 kg driver) | 1.19 (80 kg) | 1.19 (80 kg) | 1.33 (100 kg) | 1.34 (100 kg) |
| Car with driver, CG, tilt | 294 kg, 340 mm, 60.9° | 290 kg, 339 mm, 60.9° | 288 kg, 341 mm, 60.8° | 301 kg, 325 mm, 61.9° | 300 kg, 325 mm, 61.9° |
| Rear wing | fitted | fitted | fitted | not fitted | not fitted |
| Brakes: lock force, 2000 N pressure | 567 N, 296 bar | 567 N, 296 bar | 567 N, 296 bar | 676 N, 267 bar | same as v4 |
| Lap sim: 75 m, skidpad | 4.48 s, 5.12 s | same | same | 5.05 s, 5.38 s *** | same as v4 |
| Design checks / tests | 166 / 82 | 210 / 92 | 210 / 92 | 228 / 97 | 232 / 97 |

\* v1's roll-over case held the car at its suspension pickups, which hid about 2.5× the hoop stress (fixed in v2).
\*\* v4 takes the worse of two supports (hoop bases fixed, and inertia relief); v2 and v3 used hoop bases only.
\*\*\* v4 adds the 20 mm restrictor power cap, rotating mass and used-tyre grip; v1–v3 had an unrestricted engine.

Unchanged across all five: wheelbase 1750 mm, tracks 1220 / 1220 mm, main hoop 1280 mm and front hoop 850 mm high,
main hoop at X 520, front hoop at X 1321, front bulkhead at X 2130, rear end at X −300.

Tube sizes: J = 1.5 × 0.095 in, H = 1.25 × 0.095, A = 1.0 × 0.095, B = 1.0 × 0.065, C = 1.0 × 0.049.

---

## v1 → v2: tube sizes optimised (50.1 → 46.4 kg)

**Why:** first weight pass. An optimiser shrank every tube group to the smallest size its loads and its rule size
allowed, then the roll-over model was corrected and the frame re-sized (commits `ab8949d`, `8b3a240`, `c05d7ad`).
- **Roll-over model fixed:** the hoop loads were reacted at the hoop bases instead of the suspension pickups, and the
  hoops were sized to welded 4130 (340 MPa). The hoop safety factors fell from 1.28 / 1.36 to 1.08 / 1.02 because the
  old number was flattering, not because the frame got weaker.
- **Tubes removed (3):** front bulkhead diagonal, front hoop base floor cross, lap-belt floor cross. No rule needs them.
- **Upsized:** main hoop H → J; diagonal side impact B → A; upper bulkhead supports B → A; lower bulkhead supports C → B;
  rear suspension ring H → A; main hoop mid cross H → A.
- **Downsized:** shoulder bar J → H; main hoop braces A → B; front bulkhead (6 of 8 tubes) H → B; MH brace supports
  B → C (upper, and 4 of 6 lower); rear lower pickup rail, rear pickup cross, rear side-bay diagonals, spool posts and
  spool braces B → C; front hoop lower brace B → C; both brace-plane diagonals to C.
- Torsion 2138 → 2004 N·m/deg. Geometry (node positions) unchanged.

## v2 → v3: C2 node-mounted rear (46.4 → 44.3 kg)

**Why:** the weight study found the rear posts were heavy because the wishbone pickups sat mid-post, in bending. C2 put
the rear pickups on the main-hoop-brace support rail nodes (branch `clean-sheet-C2`, merged 1 Oct).
- **Rear rail raised:** rear lower rail now at 150 mm (`rr_bot` and `r_bot` up 63 and 40 mm; spool-post foot up 54 mm;
  rear-ring engine mount up 63 mm). Rear top nodes lowered 9–22 mm.
- **Tubes removed (17):** the rear lower pickup rail (4), the rear pickup cross, the rear-ring pickup posts (4 of 6), two
  rear side diagonals, two spool-post pieces and four rear bulkhead pieces. The pickup nodes `r_lsus`, `r_sus`,
  `rr_lsus`, `rr_sus` no longer exist.
- **Resized:** MH brace support upper C → B; rear bulkhead H/C mix → all C; rear-ring bottom cross A → H.
- Rear toe compliance became the binding limit (0.227° vs 0.25°). Torsion 2004 → 1946 N·m/deg.

## v3 → v4: audit fixes (44.3 → 50.4 kg)

**Why:** a full audit (WORKDONE §9) found rule checks looser than the rule text, missing load cases, and an
incomplete mass budget. All changes were on branch `audit-fixes`, merged 2 Oct.

Geometry:
- **Upper bulkhead support straightened (F.5.2.3):** the suspension-ring top `ring_top` moved from (1630, 395, 220) to
  (1630, 383, 249) so it lies on the straight line from the bulkhead top to the front hoop. The ring posts follow it,
  so the **front upper inboard pickup moved 25 mm outboard** (`ring_sus` z 220 → 245) and the front lower one 5 mm
  (`ring_lsus` z 220 → 225). All suspension, steering and compliance checks still pass with the moved pickups.
- **New tubes (2):** main hoop bend support from the shoulder-bar node to the rear-ring top (F.5.6.3, C, one each side).
  The ring-bottom cross is not new: it became its own role and went C → A to match the lower support it braces (F.5.2.3).
- **Bulkhead diagonal moved:** bottom-front to top-rear became top-front to bottom-rear on each side, because the old
  one passed through the pedal-box node (new tube clash check).

Tube sizes (re-sized against frontal impact, buckling, a 100 kg harness driver and fresh tolerance samples):
- **Upsized:** upper and lower side impact B → H; FBH upper supports A → H; FBH lower supports B → A; main hoop base
  and mid crosses A → H; shoulder bar H → J; main hoop braces B → A; MH brace support upper B → A; spool braces C → B.
- **Downsized:** diagonal side impact A → B; rear suspension ring A → C; front pickup cross B → C.

Rest of the car:
- Rear wing and DRS not fitted (mounts and checks kept for a bolt-on later); tilt 60.8° → 61.9°.
- Mass budget completed (anti-intrusion plate, impact attenuator, intake and restrictor, oil, chain guard, brake lines,
  bodywork, steel uprights); 288 → 301 kg.
- Brakes: pedal ratio 5.0 → 4.5, rear master cylinder 0.750 → 0.8125 in, over-travel switch 45 → 55 mm, realistic
  fluid compliance; lock force 567 → 676 N, 2000 N pressure 296 → 267 bar.
- Lap sim made realistic (restrictor cap, rotating mass, grip 1.2).
- Shop data: tube ends run past their joints, hoop-corner jig points on the real bend; quote note specifies filler.
- Design checks 210 → 228, tests 92 → 97.

## v4 → v5: topology experiment (50.4 → 49.4 kg)

**Why:** with tube sizes at their optimum, the next saving had to come from the layout. A removal study and a
ground-structure search (try every new tube, re-size, keep the lightest) ran on branch `topo-experiment`, merged 10 Oct.
- **Tubes removed (4 members, 2 fewer cut pieces):** the FBH-support front-bay diagonal (`bh_top` → `ring_bot`) and the upper
  spool carrier post (`sp_c` → `sp_top`). No node moved.
- **No tubes added:** the best layout with new diagonals was 49.36 kg with 8 extra tubes; not worth it.
- Front hoop roll-over FoS 1.18 → 1.11 and frontal impact 1.31 → 1.26: thinner, still above 1.0 under the robust gate.
- **New checks (4):** front bulkhead is a closed perimeter (F.6.2); harness tab nodes sit on harness-size tube (F.3.2.1);
  no tube within 10 mm of the driver's legs; no tube through the engine box away from its mounts.
- Open: the rear-ring bottom cross sits inside the generic engine box; re-check when the CRF450R is measured.
- Design checks 228 → 232, tests 97.

## Other branches (not frame versions)

| Branch | Frame | Status |
|---|---|---|
| `clean-sheet-B` | B1 front box ahead of the leg template, 51 kg | Rejected (local only) |
| `clean-sheet-short` | C1 short, 46.5 kg | No weight win; kept |
| `clean-sheet-C2` | C2, 44.3 kg | Merged as frame v3 |
| `clean-sheet-C3` | direct-acting front shocks | Checked, not built (empty branch) |
| `topo-experiment` | removal + topology search, 49.4 kg | Merged as frame v5 |
| `jugaad-1020` | C2 in 1020 DOM, 45.3 kg | Sized before the audit gates; must be re-run |
