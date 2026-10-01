# NM26 mule: project log

This file records what was done, how it was done, and what came out, in the order it happened. The current design lives in the code. `README.md` explains how to run it, and `BUILD_PLAN.md` has the full narrative, the rules checklist, the BOM and the build sequence. If this log and the code disagree, the code wins: re-run `pytest -q tests`.

## Goal and scope
- Start: `NM26_FSAE_Concept.step` and `FSAE_Rules_2026_V1.pdf`. Goal: "a working go cart".
- Chosen scope: an **FSAE-lite mule**. It drives and meets the key safety rules (hoops, side impact, harness, brakes, shutdown, impact attenuator, firewall). It skipped aero at first (a DRS rear wing was added at the team's request in step 29), and it skips the intake restrictor, SES/IAD paperwork, noise and cost.
- Deliverables: build plan + BOM, rules checklist, real parametric CAD, critique of the concept. All of them are in `BUILD_PLAN.md`.
- Standing instruction: everything gets tests and documentation.

## Tooling
- Python 3.11 venv with `cadquery matplotlib numpy pytest`. Python 3.14 had no wheels for CadQuery; pip needed the sandbox disabled because of an SSL error.
- Axes: X forward (rear axle at X = 0), Y up (ground at 0), Z to the driver's right. Units are mm, N and kg. STEP exports are rotated +90° about X to Z-up for Fusion.
- Fusion notes (see memory): the user's Fusion is Y-up. To rotate there, use Move type Rotate about an Origin axis. I can't operate the macOS file picker. Fusion Simulation's results translator failed with an Autodesk server 500 error on every solve, so **the in-house beam FEA is the frame check**.

## Chronology (what, how, result)

| # | Step | Method | Result |
|---|---|---|---|
| 1 | Concept critique | Read the STEP and the rules | Found 7 issues: short wheelbase, missing parts, and others. See BUILD_PLAN §1. |
| 2 | Layout + frame (`mule.py`) | Parametric node/member model with the 95th-percentile driver template; 27 rule checks | Wheelbase 1750, tracks 1220/1180, hoops 1280/850, helmet clearance 65 mm |
| 3 | Frame FEA (`fea.py`) | 3D Euler beam, 12 DOF per element, rigid joints, welded Sy 180 MPa, cantilever self-check | Hoops failed at first (FoS < 1). Fixed with lateral diagonals, braces at the hoop top corners, 1.25×0.095 hoops, a front lower brace, and a wider front hoop top. |
| 4 | Fusion cross-check | Frame-only STEP with one body per tube (OCCT segfaulted fusing hollow tubes); Combine in Fusion; 9–10 mm mesh; Rosetta for local mesh | Solves ran, but the results translator failed with an Autodesk 500 error. Abandoned. |
| 5 | Belly pan, driver placeholder removed | 1.6 mm 5052 pan, two 25 mm drain holes | Done |
| 6 | Suspension (`suspension.py`) | Front-view double-wishbone kinematics, roll centre / instant centre, ±50 mm | Roll centre 35 mm front / 50 mm rear; camber gain −0.68 / −0.72° per 25 mm. Needed the lower pickups raised onto the verticals, and the verticals upsized to H. |
| 7 | Loads (`loads.py`) | Six-link upright statics: 3 g bump, 1.5 g corner, 1.5 g brake; Euler buckling; frame with **inertia relief** | The first frame FoS of 0.97 was an artefact of the supports. Inertia relief fixed that, and lower pickup crosses plus a rear rail brought it to 1.23. Rear pushrod went to 3/4×0.049. |
| 8 | Springs (`springs.py`) | Motion ratios, 2.6/2.8 Hz ride | Springs about 280 / 600 lb/in, stroke 59 / 50 mm |
| 9 | Rockers (`rocker.py`) | Bellcrank design, shock inside its stroke, bracket clash search | All 12 checks pass. Rear direct-acting would have needed a 1019 lb/in spring, so it got a rocker too. |
| 10 | Steering (`steering.py`) | Bump steer via kingpin rotation, Ackermann, 3D lock clearance | Bump steer ≤ 0.09°, Ackermann 64 %, rack travel 28.7 mm, lock 23° (sets the 10 mm gap). The rack was lowered to Y = 180 to clear the shins. |
| 11 | Fabrication (`fab.py`) | Collinear merge into pieces, Y-B-C bend programs, cope angles and phase, jig table | Hoops redrawn so their nodes lie on straight legs (the front hoop bends overlapped by 45 mm). The bigger tube always receives the cope. |
| 12 | Uprights (`uprights.py`) | Bearing statics and L10, hub von Mises, arm stress, stud slip | 16 checks pass. 6009-2RS bearings, 4140 hub 45/30, 7075 upright, 4×M12 on 100 PCD |
| 13 | Powertrain (`powertrain.py`) | Gearing, chain length, wrap and adjustment, clearances, CV angle, engine mount min-norm, launch FEA | 13 checks pass: 113 km/h, 60-link chain, CV 10.5°, launch FoS 1.21. **Engine values are placeholders.** |
| 14 | Brakes + pedal box (`brakes.py`) | Lock pressure per axle, balance-bar lever rule, compliance-based pedal travel, BOTS window, rotor ΔT, blade/pivot/bar stress, frame at 2000 N | 13 checks pass: lock at 551 N, balance 57 % front, 289 bar at 2000 N (limit unverified), BOTS at 45 mm, frame FoS 1.31 |
| 15 | Physical test plan (`TEST_PLAN.md`) | Reference 2020 FSAE test-plan format; every pass criterion taken from our scripts; `tests/test_test_plan.py` guards against drift | 7 stages, 26 tests. New finding: the 60° tilt margin is only 3° at the assumed 300 mm CG, so the CG must be measured ≤ 340 mm. |
| 16 | Generated report (`report.py` → `REPORT.md`) | Runs every module's checks, the FEA and loads, and pytest with a result-collecting plugin, then writes markdown tables. `NM26_Frame_FEA.step` was regenerated because it predated the pedal-box tubes. | 97/97 design checks, 45/45 tests pass |
| 17 | Catalogue values | Web search: SKF 6009-2RS1 C0 is 14.6 kN (not 15.2); DID 520VO is 35.6 kN | Bearing and chain values updated to catalogue |
| 18 | Cockpit templates (`cockpit.py`) | T.1.1 and T.1.2 templates from the rules drawings, swept through capsule models of the frame, rack, rockers, shocks and seat. The template "ceiling" only counts tubes over the template footprint. | **T.1.1 failed by 26 mm**, fixed by widening the cockpit 260 → 292. **T.1.2 failed at the front ring**. Two fixes were rejected: rack ahead of the pedals (4.4° bump steer) and ring top raised to 570 (ring posts bent, front-hoop FoS 0.66). Chosen: no ring-top cross, 1.5″ ring posts, front shock moved to the front hoop. Both pass. |
| 19 | Side view (`sideview.py`) | SVSA instant centres, caster/trail from the kingpin, pitch from ride rates, RC migration in heave, bump steer with the rack held at lock, rack ratio | Caster 4.6° (UBJ 19 mm rearward), trail 11.5 mm, anti 0 %, dive 26 mm, lock bump steer 0.11°, 5.5:1. Turning circle 5.7 m (hairpin needs 4.5; not a mule requirement). |
| 20 | Combined loads + mass/CG (`loads.py`, `mass.py`) | Corner+brake at μ, and a kerb strike in a 1 g corner. Item-by-item mass budget. | Budget 288 kg / CG 323 mm / 15.3 kg unsprung, so the assumptions went to CG 330 and 15 kg. Knock-ons: 6209 bearings, 0.75″ rear MC, rear lower rail and mid cross upsized. Tilt 61.3° (margin about 1°). |
| 21 | Harness (`harness.py`) | T.2 angles from the driver template, tab tear-out and weld, 20 g crash on the frame with inertia relief, checked against welded ultimate | **Lap belt was 15°** (needs 45–65°). Tabs moved under the hips (55°), with a tab brace and a floor cross; anti-sub floor cross with a V; 1.5″ shoulder bar. Crash FoS 1.17. |
| 22 | Shutdown and wiring (`shutdown.py`) | Netlist simulation of the kill relay; fuses vs ampacity; voltage drop; T.9 locations | All 14 checks pass; 0.23 V drop to pump and ignition |
| 23 | Design-review notes (Hayward, *Car Design Workshop*) | Compared each standard-practice target with the design | Applied: PDS, mass/CG budget, combined and kerb loads, bump steer at lock, caster, anti trade-off, RC migration, loaded radius. Gaps are listed under open items. |
| 24 | Fusion import of the updated STEP | Fusion Open, then the macOS picker (driven with full-screen control) | Imported upright; not yet saved to the cloud |
| 25 | Colour key | One `mule.COLORS` table drives the CAD colours, the README key (written by `report.py`) and `views/colour_key.png` | Red used to mean eight different things; now one colour per system |
| 26 | Hayward gaps (BUILD_PLAN §2m) | Grid searches on ball-joint inset/lean and the rocker pickup; new `roll.py` (static camber, RC in roll, jacking), `compliance.py` (pickup FEA plus link stretch, six-link upright), `lapsim.py` (point-mass acceleration and skidpad); Pugh matrices and a benchmark template in PDS; buck plan; CAD part numbers and `parts.csv` | Scrub 53 → 38 mm (tyre-to-arm gap at lock stops it lower). Motion ratio 0.59/0.50 → 0.72/0.75, after finding V.3.1.1 needs 50 mm *total* travel (now +50/−25). Lock-to-lock 233 → 179°. Camber −2.5/−2.0°. Compliance toe 0.10/0.13°. Acceleration 4.27 s, skidpad 4.81 s. 150 checks, 71 tests. |
| 27 | Remaining items | Web checks of catalogue values (SKF, DID, Kaz, AF4.1 hoop loads, FSAE Michigan 2025 results); hoop-load direction envelope; steering effort and kickback; rear bump steer check; autocross sim with calibrated grip; compliance source split | Found rear bump steer of 0.76°/25 mm, never checked before; fixed to 0.00°. Main hoop FoS 1.28 in the worst direction. Kaz rack with 85 mm arms: 178°, 95 N. Point-mass times: 4.49 / 5.17 / 59.2 s. Only supplier, part and team items remain. 153 checks, 73 tests. |
| 28 | Two reference PDFs (JCU 2020 rear-suspension paper; NAU 2025 FSAE suspension initial design report) | Compared each method and value with the design; checked the NAU numbers against the 2026 rules | Found two gaps: no front/rear load-transfer balance check (the NAU roll-stiffness method), and V.3.1.4 critical suspension fasteners missing from the checklist. Balance was really 40 % front vs 45 % weight (oversteer); fixed with 3.0/2.6 Hz ride, 49.6 %. Solid-axle option recorded in the PDS. The NAU report's wheelbase "< 1500 mm" and track "< 1550 mm" limits are wrong for 2026 (the rules set a 1525 mm minimum wheelbase and only a ≥ 75 % track ratio, V.1.3.2): not used. 154 checks, 73 tests. |
| 29 | Moveable rear wing (team request) | Read T.7 and IN.6.2 (moving aero is not banned; it must be stiff and must not oscillate); new `aero.py` (T.7 geometry at both flap positions, forces from assumed coefficients, axle split, mount FEA, first-mode frequency, servo and spring sizing, DRS logic); wing added to the CAD, mass budget, lap sim and 12 V circuit | The wing's 7.4 kg high up dropped the tilt angle to about 60.2°, so the rear track widened 1180 → 1220 mm (all checks re-run): tilt 60.9°. Design CG raised to 345 mm. Lighter mounts were rejected because they resonate at 15–29 Hz, near wheel hop. Brake pressure at 2000 N rose to 296 bar. Wing worth −0.67 s per autocross lap (point mass). |
| 30 | GitHub, file names, Trinity 2020 report | Pushed to github.com/udayjain2102/nittanymotorsports through the GitHub API (git on this Mac is blocked by the Xcode licence). Made every file name unique: `cad_parts.py` now names frame tubes by size, role, side and number (bottom to top), and tabs by the frame point they sit at; the two `parts.csv` files became `NM26_Mule_parts.csv` and `cad/NM26_Assembly_parts.csv`, the latter with a `contains` column. A root README says what every file holds. Read Trinity University's 2020 FSAE final report (the source of the test manual used earlier). | Their rear tie rods hit the drive axle; we had no check for that, so `powertrain.py` now checks the rear toe link against the CV half-shaft (boot included) over travel: 54 mm. The rest (steering wheel below the front-hoop top, caliper packaging, the test manual) was already covered. The detailed CAD had no rear wing (only the simple model did); `cad_parts.py` now builds it too (sub-assembly 07_aero), and `cad/` was regenerated with the wing and the 1220 mm rear track. |
| 31 | Folder reorganisation | Documents moved to `mule/docs/`, the simple CAD model, its parts list and the frame FEA model to `mule/cad/simple/`, the cut list to `mule/fab/`, and the reference papers to `references/` (kept out of git). The scripts stay together in `mule/` because they import each other. Output paths in `mule.py`, `frame_fea_export.py`, `report.py` and the test-plan guard were updated, as were the links in both READMEs; the root README gained a folder map. GitHub Actions (added in the same session) now runs `python report.py` on every push. | All outputs regenerated from the new paths; 166 checks and 80 tests pass. The Fusion model was first saved as `NM26_Assembly_DRS_wing` (see step 32 for the final naming). |
| 32 | Fusion project tidy-up, phased budget, work summary | Renamed every design in Fusion's `adi laptop files`, keeping them all: current `NM26_Assembly_v4` (+ `_part2`, `_part3`, Fusion's split of the large STEP) in the `Nittany Motorsports` folder; older ones renamed `NM26_Assembly_v1_no_wing`, `_v2_first_wing`, `NM26_Mule_simple_v1–v3`, `NM26_Frame_only_FEA_model`, `NM26_FSAE_Concept_original`, `_first_import_sideways`. Wrote `docs/BUDGET_PLAN.md` after checking prices online, plus the root `WORKDONE.md`. | The 10:17 PM upload never finished and vanished from Fusion. Budget: five funding steps of about $2,500 or less, about $6–9k to a driving car, with a 13 hp kit engine + CVT first (75 m about 6.9 s vs 4.5 s, autocross about 12 % slower) and a used 450 as the upgrade. |

## Current results (all checks pass; see REPORT.md for every check and test)

| Area | Number |
|---|---|
| Frame | 146 members, 50.1 kg, 81 pieces (2 bent). Torsion 2138 N·m/deg. |
| Hoop loads 6/5/9 kN (AF4.1/AF4.2, worst of 4 directions) | Main FoS 1.28, front FoS 1.36; deflection ≤ 3.9 mm (limit 25) |
| Worst wheel-load case (10 cases) | FoS 1.26; worst link buckling FoS 4.3 |
| Launch | Frame FoS 1.23 |
| 2000 N pedal | Frame FoS 1.31; pedal 3.8, pivot 6.8, balance bar 2.1 |
| Harness crash, 20 g | Frame FoS 1.17 vs welded ultimate |
| Suspension | Roll centre 37/52 mm, motion ratio 0.72/0.75, ride 3.0/2.6 Hz, springs about 243/215 lb/in, LLTD 49.6 % front, bump steer ≤ 0.12° (0.27° at lock), caster 4.6°, scrub 38 mm, static camber −2.5/−2.0° |
| Steering | Kaz rack, 4.1:1, 178° lock-to-lock, Ackermann 50 %, 95 N rim force at 1.5 g; rear bump steer 0.00° |
| Compliance at 1.5 g | toe 0.10° in (front), 0.18° out (rear) |
| Events (point mass, grip 1.3) | acceleration 4.49 s, skidpad 5.17 s, autocross 59.2 s; FSAE Michigan 2025 medians 4.62 / 5.52 / 55.7 s |
| Mass | 296 kg with the rear wing, 46.1 % front, CG 340 mm; tilt 60.9° |
| Rear wing | 0.47 m², 126 N at 60 km/h closed (assumed coefficients), DRS spring-return, push 0.1 mm, 159 Hz; autocross −0.67 s |

## Model versions (what each exported STEP contains)

| Version (step) | New in the model |
|---|---|
| 2 | Frame, driver template, tyres, pedal/seat/IA placeholder boxes |
| 3–5 | Hoop fixes (braces, 1.25″ hoops), belly pan; driver dummy removed. This is the copy first imported to Fusion (rotated to upright there). |
| 6–10 | A-arms, pushrods, rockers and shocks, steering rack and tie rods |
| 12 | Uprights, hubs, rotors, calipers |
| 13 | Engine placeholder, sprockets, chain, spool, bearing carriers, CV half-shafts, spool posts, engine-mount crosses |
| 14 | Real pedal box (pedals, balance bar, master cylinders, reservoirs) and its floor crosses |
| 18–22 | Cockpit 584 mm wide; front ring without a top cross and with 1.5″ posts; front shocks on the front hoop; lap tabs, braces and floor cross; anti-sub floor cross and V; 1.5″ shoulder bar; upsized mid cross and rear rail; 6209 bearings; caster; battery, switches, relay and brake light |
| 25 | Same geometry, colours by system (README colour key) |
| 26 | Front ball joints moved (scrub 38 mm), new rocker geometry (motion ratio 0.72/0.75), part numbers in every body name |
| 27 | 85 mm front steering arms; rear toe link raised to 300/323 mm (rear bump steer 0) |
| 29 | Rear wing with DRS flap, struts and servo (Lime, NM26-AER); rear track 1220 mm; ride 3.0/2.6 Hz springs |

## Errors hit and how they were fixed
- **Layout and frame:**
  - The engine sat on the axle and the helmet was too close to the hoop line. Fixed by stretching the wheelbase and re-tuning the seat angle and hoops.
  - The hoops were overstressed (see step 3).
  - When the hoop nodes moved onto straight legs, front hoop FoS fell to 1.09. Moving the lower brace to the hoop top fixed it.
- **Tube joints:**
  - 1.25″ tubes were being coped onto 1″ tubes. Changed the receiver ranking and square-cut those ends.
- **Clearance and packaging:**
  - The rear-ring top cross passed through the engine, so it was removed.
  - A plan-view clearance check gave false positives, so I replaced it with a true 3D check.
  - The Ackermann inner/outer labels were swapped; fixed.
- **Chain and launch:**
  - The chain-line check logic was backwards; fixed.
  - Launch failures were fixed by upsizing the engine-mount crosses and the rails.
  - Mounts at Z = ±140 were worse (FoS 1.06), so they were reverted to ±100.
- **Pedal box:**
  - The first stack-up moved the bulkhead forward 20 mm, and tyre-to-A-arm lock clearance dropped to 7 mm. I shortened the stack-up instead (10° lean, 25 mm pushrod) and kept the bulkhead at X = 2130.
- **Test bugs fixed along the way:**
  - the rocker pivot sign;
  - the overhung-bearing assumption;
  - tautological asserts, which were removed. That includes one "always True" brake check.

## Open items

Everything left needs parts, a supplier or a person. None of it can be done in the code.

- **Verified against sources (2026-09-29):**
  - SKF 6209-2RS1 ratings: C 35.1 kN, C0 21.6 kN (SKF data).
  - DID 520VO chain: 8,000 lbf = 35.6 kN (didchain.com).
  - Hoop load case: 6.0 / 5.0 / −9.0 kN, from FSAE Alternative Frame rules AF4.1/AF4.2. The code now takes the worst of the four axis assignments.
  - Kaz Technologies rack: 4.71 in/rev, 82.5 mm travel (kaztechnologies.com).
  - FSAE Michigan 2025 event times (fsaeonline.com).
- **Needs a supplier's written answer** (not published online):
  - maximum pressure for the Wilwood GP200 / PS-1 calipers, the Tilton 78-series master cylinders and the hoses. At 2000 N (T.3.2.2) the design reaches 296 bar ≈ 4,290 psi, only 4 bar under the assumed 300 bar limit. If a part is rated lower, use a bigger MC bore (this raises the lock-up pedal force) or pick parts rated higher.
- **Needs the real parts:**
  - the engine values (`powertrain.ENGINE`, placeholder);
  - the item masses in `mass.py`: weigh them, because the CG decides the tilt margin (about 1°);
  - pad μ and line compliance (bench);
  - battery max discharge and switch ratings.
- **Needs a decision:** the engine for funding step 3: a 13 hp kit engine + CVT first (cheapest, see `docs/BUDGET_PLAN.md`) or a used 450 now.
- **Needs the team:**
  - build the buck (BUILD_PLAN §2m) before cutting tube;
  - freeze `cad/NM26_Assembly_parts.csv` into the BOM before ordering;
  - fill the other-teams columns of the PDS benchmark from published design reports;
  - run TEST_PLAN.md stages 1–7. T2.7 measures the compliance toe, predicted 0.18° out at the rear.
- **Decided, with the reason recorded:**
  - front scrub stays 38 mm: going lower needs a frame-pickup move (PDS Pugh matrix);
  - no rear wing (PDS Pugh matrix: tilt margin);
  - turning circle 5.7 m (a competition hairpin needs 4.5 m);
  - anti-dive and anti-squat 0 %;
  - the lap sim is a point mass: it has no tyre load sensitivity or transients, so treat its times as lower bounds;
  - seat shell and firewall are CAD placeholders, built to the checklist rules.
- **Cleanup:** the 1.4 GB scratch venv (CadQuery) is still needed to regenerate the CAD. Delete it when the design is frozen.

## 2026-09-29 (late) - detailed CAD: one file per part + assembly (`cad_parts.py`)
- **Ask:** a final Fusion model at the realism of a rendered FSAE corner (treaded tyre, CV boots, coil springs, finned motor), with every part in its own file and one final assembly.
- **Done:** `cad_parts.py` reuses the mule.py geometry (nodes, links, `rocker.analyse`, `brakes.geometry`, `powertrain.sprockets`, `shutdown.LOC`) and models each part with its features. Output in `cad/`: 258 part STEPs (positioned, Z-up), `NM26_Assembly.step` (28 MB, 9 sub-assemblies, 302 solids), `parts.csv`, `view_*.svg/png`. Part numbers stay `NM26-<sys>-<nnn>`, restarting from 001 in this model (the frame is now 172 tube/bracket parts, not 5 size groups, so numbers differ from the primitive model's `parts.csv`).
- **Bug found and fixed:** CadQuery's `Assembly.add(sub)` copies the sub-assembly, so parts added to a sub-assembly afterwards never reached the root (the first assembly STEP was 3 KB, empty). Sub-assemblies are now filled first and attached in `Build.finish()`.
- **Checks:** every solid `isValid()` with positive volume (asserted in the script); part and assembly STEPs re-imported and bounding boxes confirmed Z-up (tyre z 0..521, car height 1296); `tests/test_cad_parts.py` (2 tests) checks files = csv = assembly products. 80 tests pass.
- **Simplifications (placeholders, same as before):** engine is a finned generic single, not a chosen engine; chain is two straight runs (no wrap or links); coil-over spring is a second solid in its part file (not fused to the damper); frame tubes are straight between bend nodes (hoops are bent in reality); no fasteners other than lug nuts and wheel studs.
- Rendering: ImageMagick's SVG renderer produced blank PNGs for the CadQuery SVGs; `view_*.png` were rasterised from the SVG paths with matplotlib instead.

## 2026-09-29 (late) - engine, real component shapes and routing (`cad_detail.py`)
- **Ask:** make the engine realistic, replace the remaining box placeholders with the shape each part really has, and show roughly where every brake line, cable and wire runs. Include the other session's wing/DRS and unique-name changes (they were already in `cad_parts.py`; this builds on them).
- **Done:** `cad_detail.py` (imported by `cad_parts.py`): engine as 15 parts with mounts to em_fb/em_ft/em_rb; seat shell, head restraint, pedal box, dash, fuel cell (in-tank pump, filler, breather, outlet), firewall with flanges and grommets, master switch, E-stop, inertia switch, kill relay, brake light, battery, BOTS, ECU, fan, DRS servo as real shapes; `routes()` = 23 runs (6 brake-line segments, throttle cable, fuel line, 15 wires from `shutdown.WIRES` plus the dash DRS button and the ground strap) as tubes along the frame, also tabulated in `cad/ROUTING.md`. Assembly now 310 parts in 10 sub-assemblies (`08_routing` new).
- **Layout decisions the geometry forced:** the fuel cell floor is 10 mm above the engine envelope, so the intake goes rearward (throttle body + airbox behind the head, restrictor snorkel on top) and the exhaust leaves the front of the head, drops down the right side and runs back to a muffler at the right rear (x -40..-240, y 360, z 120), placed to clear the spool, toe link, pushrod and wing struts. Rear brake line runs along the LEFT lower side-impact rail (chain is on the left too, but the line sits inside the rail); throttle cable runs the right rail through the right firewall grommet.
- **Checks:** every solid valid with positive volume; `pytest` 80/80 (unique names, csv = files = assembly products); stale part files from earlier numbering pruned. Not checked: collisions between routes and moving parts (wishbones, pushrods) - the runs are drawn as straight segments with corner spheres and are meant as a routing plan, not bend-true lines.
- **Colours (later the same evening):** the wing was lime next to the green seat and the routing shared the brake purple / electrical pink, so `mule.COLORS` gained `hydraulic` (Gold: brake lines, throttle cable) and `wiring` (Magenta: harness), both part code RTG, and `aero` became White. Routing part numbers are now NM26-RTG-nnn. Regenerated: 310 parts, 166 checks, 80 tests.

## 2026-09-30 - engine decision moved ahead of the frame; kit-engine fit check; parts list
- **Ask:** decide next steps from WHATS_NEXT/WORKDONE, check the kit-engine adapter-plate idea, and make a parts list.
- **Found:** the engine choice was scheduled for step 3, but the engine mounts (`em_fb`/`em_ft`/`em_rb`) are welded in step 1. `WHATS_NEXT.md` now puts the engine decision before the tube order.
- **Done:** `powertrain.py` Option A (`KIT`, `CVT`, `kit_bay`, `kit_fit`, `kit_checks`). It fits a horizontal-shaft kit engine + go-kart CVT on an adapter plate on the 450 mounts, crank across the car, and tries both yaw orientations. It is printed by `python powertrain.py` but not asserted, because the option is not selected. One new test in `tests/test_powertrain.py`.
- **Result:** Predator 420 at its listed size (480 × 434 × 351 mm, which includes the tank, muffler and filter) fails. The height is 434 mm against 388 mm under the fuel cell. The length is 351 mm against 330 mm between the jackshaft and the firewall, and with the CVT the width is 590 mm against 487 mm between the rear-ring tubes. The Comet 40-series CVT rating (8–18 hp) is fine. Recommendation changed to a used electric-start 450; `BUDGET_PLAN.md` updated.
- **Added:** `docs/PARTS_LIST.md`: engine candidates with prices, and the chosen drivetrain, chassis, brake and safety parts with the script that sizes each one.

## 2026-09-30 - engine chosen: Honda CRF450R 2018+
- **Decision (user):** CRF450R "2017+". Online check: the 2017 has kick start as standard (electric start was an optional kit); electric start is standard from 2018. So the target is 2018+, or a 2017 with the kit fitted.
- **Done:** `ENGINE` in `powertrain.py` named, peak torque 48 N·m @ 7000 rpm (published) replaces the 50 N·m placeholder. Redline, primary and gear ratios, envelope, countershaft and mass are still generic: gear ratios are not published online, so they need the service manual. Stock bike sprockets are 13/49 (ours 13/50).
- WHATS_NEXT, PARTS_LIST and the mass label updated.

## 2026-09-30 - flaky CI fixed: rocker tangent picked by rounding
- **Symptom:** GitHub Actions failed about half the runs on unchanged code, always `test_loads.py` with frame FoS 0.829 (every local run: 1.26).
- **Found with an 8-job CI matrix:** failures only on some runner CPUs (mostly newer AVX-512 ones), and only the front load cases changed. The front rocker's shock pickup was different there. `rocker.design` chose between two mirror-image tangent solutions by "the smaller |B|", but the two are exactly equal in theory (111.52318241153715 vs ...714 locally), so the last bit of rounding picked the side.
- **Fix:** `rocker.TANGENT_SIDE` fixes the side per axle (front −1, rear +1: the sides the design was validated with). Every check value is unchanged locally.
- **Also fixed on the way:** `fea.inertia_relief` chose 3-2-1 supports that all sat on the front bulkhead plane and did not stop rotation about Y and Z (singular stiffness matrix). It now clamps one node in 6 DOF; results unchanged; new test `test_inertia_relief_stress_independent_of_support_node` fails on the old code. This was not the CI cause.
- `test_loads.py` now prints every load case when the frame check fails.
- Also: the CRF450R torque (48 N·m) moves the acceleration prediction from 4.47 s to 4.49 s; TEST_PLAN and PDS updated.

## 2026-09-30 - folder clean-up and clearer file names
- Renamed generated files to say what they are (generators, tests and docs updated): `fab/cutlist.csv` → `fab/tube_order_list.csv`, `fab/cut_sheet.csv` → `fab/tube_cut_sheet.csv`, `fab/nodes.csv` → `fab/jig_node_coordinates.csv`, `fab/hoop_bends.csv` → `fab/hoop_bend_program.csv`, `views/corners.png` → `views/suspension_corners.png`, and the simple-model drawings `views/{front,iso,side,top}.svg` → `views/simple_*.svg` (so they aren't confused with the detailed model's `cad/view_*.svg`).
- Local (git-ignored) reference PDFs renamed: `JCU_2020_FSAE_rear_suspension_design.pdf`, `NAU_2025_FSAE_suspension_initial_design_report.pdf`.
- `.gitattributes` paths fixed (they still pointed at pre-reorganisation locations); stale `mule/.pytest_cache` removed.
- Kept as is: Python module names (each already names its system) and every CAD file. Fusion versions stay in the Fusion project, and older STEP versions stay in git history.
- 166/166 checks, 82/82 tests.

## 2026-09-30 - CRF450R 2018+ gear ratios from the service manual
- **Source:** the 2017–18 CRF450R/RX service manual on ManualsLib, pages 1-4 and 1-5. The scan's text is garbled, but each ratio is printed with its tooth counts and they agree exactly: primary 2.357 (66/28); gears 2.133 (32/15), 1.706 (29/17), 1.421 (27/19), 1.211 (23/19), 1.043 (24/23); final 3.769 (13/49) R, 3.846 (13/50) RX. Engine dry weight 30.9 kg for "after '17". Honda's 2018 spec page confirms electric start and 13/49. The widely quoted 2.739 / 1.800 … set is the 2004 model's, not 2018's.
- **Entered** in `powertrain.ENGINE` (ratios as fractions of teeth, mass 30.9). Top speed 110 → 117 km/h at the placeholder 11,500 rpm; 1st gear 928 vs 859 N·m traction (pass); acceleration 4.48 s; rotor heat and wing top-speed loads rise with top speed (all pass). TEST_PLAN T5.1 table, T6.2, PDS, BUILD_PLAN, READMEs, WORKDONE and WHATS_NEXT updated.
- Still generic: rev limit, engine envelope, mount and countershaft positions.

## 2026-10-01 - frame weight optimisation, step 1: right-size tubes on the current layout (50.1 -> 45.3 kg)
- **Method:** a scratch optimiser loaded every frame strength case in one process (hoop loads AF4.1/4.2, the 10 wheel-load cases, full-traction launch, 2000 N pedal, 20 g harness crash, wing mounts), recorded the stress in every member, and greedily stepped each (role, size) group down the ladder 1.5×0.095 → 1.25×0.095 → 1.0×0.095 → 1.0×0.065 → 1.0×0.049. It never went below the F.3.2.1 rule minimum for that role, and every step had to keep all cases at FoS ≥ 1.2 (harness ≥ 1.0 vs welded UTS, wing ≥ 1.5), torsion ≥ 1500 N·m/deg and hoop deflection ≤ 25 mm. Then it tried removing tubes that no rule requires.
- **Applied:**
  - downsized: front bulkhead verticals 1.25×0.095 → 1.0×0.065 (rule size B); shoulder harness bar 1.5 → 1.25×0.095; rear suspension ring 1.25 → 1.0×0.095; MH brace-plane diagonal 0.095 → 0.065; FBH support upper, MH brace supports (outer parts), rear lower pickup rail, rear pickup cross, rear side-bay diagonal, spool carrier posts and braces, and the FH brace-plane diagonal 0.065 → 0.049.
  - removed: front bulkhead X-brace (F.8.4.3 needs one only above 400 × 350 mm; ours is 385 × 335), front hoop base cross, lap-belt floor cross.
- **Result:** 143 members, 45.3 kg, 78 pieces; torsion 2138 → 1886 N·m/deg; FoS: main hoop 1.22, front hoop 1.27, wheel loads 1.22, launch 1.26, pedal 1.32, harness 1.08 (vs welded UTS). All 166 checks pass.
- **Also tried:** shortening the rear overhang (rear bulkhead at −200 or −175 instead of −300). It saves only ~0.2 kg, because the launch case then needs heavier MH brace supports and engine crosses, and it brings the chain within 5 mm of the rear tubes. Not applied.
- **Why it stops at ~45 kg:** the hoops and shoulder bar are set by the 20 g harness and hoop loads (thinner fails by 24–29 %), the suspension pickups sit mid-span on bending "ring" posts, and ~20 kg is rule-minimum tube. Published 4130 FSAE frames are ~30–33 kg, so the next step is a topology redesign (pickups on triangulated nodes, a closed front ring that still passes T.1.2, a braced shoulder bar), not tube sizes.

## 2026-10-01 - FSAE rules audit: frame_rules.py and RULES_MATRIX.md
- **Ask:** every FSAE rule must be met; nothing can be traded for weight.
- **Audit:** 265 rule items in V.1, F, T.1, T.2 of the 2026 rulebook were classified. About 20 geometric frame rules had
  no check. `frame_rules.py` adds 34 checks:
  - tube size per job (F.3.2.1);
  - side-view triangulation (F.1.17 / F.5.6.2);
  - hoop bends at nodes, one-piece hoops from the lowest member, hoop lean;
  - braces (count, straight, direction, end nodes);
  - bent multi-tube members supported at kinks (F.5.2.3);
  - no engine or suspension mounts on the main hoop or its braces (F.5.11.4);
  - front bulkhead support geometry (F.6.2.3);
  - side impact members (F.6.4);
  - shoulder bar (F.6.5);
  - main hoop brace supports (F.6.6);
  - steering rack inside the Primary Structure (F.5.14);
  - hips inside the Major Structure (T.1.3.1, 200 mm hip half-width assumed);
  - open-wheel zones (V.1.1).
- **Triangulation test, how it was made fair:**
  - A full 3D pin-jointed truss fails any open-cockpit frame, because the hoops carry side loads in bending, which the rules allow.
  - The test is therefore per side, in side view, using every structural tube (F.1.17 counts Structural tubes).
  - Only movement of Primary Structure joints counts.
  - A straight tube running through a joint is held straight there. Without this, mid-post joints show up as false hinges.
- `tests/test_frame_rules.py` breaks the rules one at a time (diagonal removed, main hoop undersized, brace kinked,
  mount on a brace, tube in the tyre zone) and confirms each check fails.
- The current frame passes all checks. `report.py` runs them: 200 checks, 88 tests.
- `docs/RULES_MATRIX.md` lists every rule: 83 automated, 94 build/inspection, 45 N/A (with the reason), 15 definitions.
  The BUILD_PLAN §3 "FSAE-lite" skips are now required items: SES/IAD paperwork, the 20 mm restrictor and the noise limit.

## 2026-10-01 - documentation sweep
- Every doc now follows two decisions: the full FSAE 2026 rules are hard constraints, and the engine is the CRF450R.
- "FSAE-lite" wording removed from all titles, plus the README, the module README and the PDS goal. The PDS constraints
  now name the full rules, the phased budget and the CRF450R. Its old "accepted non-requirements" list is now open items:
  the turning circle, noise, the restrictor and the competition paperwork (SES, IAD, cost report).
- Current results updated everywhere: PDS R1/R3/R4/R5/R6, BUILD_PLAN tube schedule and engine data, budget wording (the
  kit engine is ruled out), and the module and file tables (`frame_rules.py`, `quote_package.py`, RULES_MATRIX,
  FRAME_RESEARCH, `quote/`).

## 2026-10-01 - reality gap: robustness.py, SIM_TO_REAL.md, frame margin restored (45.3 -> 46.2 kg)
- **Ask:** apply sim-to-real thinking (NVIDIA Isaac Lab course: approximation / model / unmodelled errors; domain
  randomisation, real-to-sim, regularisation) to every simulation.
- **`robustness.py` (domain randomisation, kept to measured ranges):**
  - frame: 16 samples with tube walls ±10 %, joints ±2 mm and per-tube stiffness 60–100 % (joint flex);
  - each tube's random draw is fixed by a hash of its position, so adding a tube elsewhere doesn't reshuffle the others;
  - joints are moved after the FEA merges them, so the wing struts stay attached. An earlier version broke this and gave a fake wing FoS of 0.03;
  - gates: every case FoS ≥ 1.0 in every sample, and worst torsion ≥ 2 × roll stiffness (953);
  - joint flex is counted once: the earlier version also applied ⅔ on top, which double-counted it;
  - tilt checked with ±10 % mass errors, independent (5th percentile 60.7°) and correlated (60.3°);
  - bands reported for brakes (504–648 N lock force at pad friction 0.45–0.35) and lap times (grip ±0.1).
- **Finding:** the optimised frame failed the 20 g harness case under tolerances (worst 0.96).
  - The lower side impact at the lap tab, then the shoulder bar, then the diagonal side impact limited it.
  - Restoring the lap-belt floor cross alone didn't fix it.
  - The lightest passing fix is shoulder bar 1.5″ and diagonal side impact 1.0″ × 0.095″, with no lap cross. That gives 46.2 kg and a worst harness FoS of 1.08.
  - `tests/test_robustness.py` confirms the old 1.25″ bar fails.
- **Docs:**
  - `docs/SIM_TO_REAL.md`: per-model validity, gap type, margin, measurement, and the real-to-sim loop.
  - TEST_PLAN:
    - twist pass is now ≥ 1000 measured (expect 1300–1500), instead of ≥ 1500;
    - mass pass is now 46–54 kg;
    - new T1.4 frame 3D scan and T2.8 shock check;
    - the results log has a "model input updated" column.
  - PDS, BUILD_PLAN, budget, READMEs and WORKDONE carry the new numbers.
- 210 checks, 91 tests.

## 2026-10-01 - roll-over model error: AF4 support, welded-4130 criterion, frame_opt.py (46.2 -> 46.4 kg)
- **Found while working on clean-sheet concept C1:** the roll-over cases in `fea.run` held the car at its suspension
  pickups. AF4.1/AF4.2, where the 6/5/9 kN loads come from, fix translations at the bottom nodes of both roll hoops
  ([FSAE forum](https://www.fsae.com/forums/archive/index.php/t-11827.html)), and AF5.6 allows inertia relief instead.
  Both give the same answer (369 vs 371 MPa main, 422 vs 416 front). The old support gave 146 / 142 MPa. The frame was
  far weaker in roll-over than reported: FoS 0.48 / 0.43 against the FSAE welded yield.
- **Criterion (user chose option A):** AF4's own pass criterion is "no failure" (load below tensile, compressive, shear
  or buckling capacity) with no margin factor.
  - Base 4130 normalized tube: Fty 75 / Ftu 95 ksi (MIL-HDBK-5J).
  - No public welded-4130 table exists (Abbott Aerospace says so too). Welds are therefore taken at 85 % of the ER70S-2
    filler minimums (AWS A5.18: 58 / 70 ksi), the weld-allowable rule MIL-HDBK-5 uses. That gives `fea.SY_ROLL` = 340 MPa
    and `SU_ROLL` = 410 MPa.
  - Gates: nominal FoS ≥ 1.0 on 340, and FoS ≥ 1.0 on 410 in every tolerance sample.
  - All other load cases keep the FSAE welded values (180 MPa, FoS 1.2).
  - The criterion is only valid for 4130 with ER70S-2 filler; revisit it if 1020 DOM is chosen.
- **`frame_opt.py`:** the scratch optimiser was lost when the session scratchpad was wiped, so it now lives in the repo.
  It re-sized the frame under every gate: main hoop 1.25 → 1.5″, upper bulkhead supports 0.049 → 0.095 wall, lower
  bulkhead support 0.049 → 0.065. Shrunk: main hoop braces 0.095 → 0.065, shoulder bar 1.5 → 1.25″, front hoop lower brace,
  MH brace-plane diagonal, main hoop mid cross. Result: 46.4 kg, torsion 2004.
- The robustness test that expected the 1.25″ shoulder bar to fail was removed: the bar now passes because its neighbours
  are stronger.
- New: `tests/test_frame_opt.py`. CAD, shop data, quote package and docs regenerated.

## 2026-10-01: clean-sheet C2 "node-mounted rear" (branch `clean-sheet-C2`, from `main`)
- Rear wishbone pickups moved from mid-post nodes (rr_lsus/rr_sus, r_lsus/r_sus) onto the main-hoop-brace support rail
  nodes: lower on rr_bot/r_bot, upper on rr_top/r_top. The rear lower rail now runs at 150 mm (`Y_RLOW`, kinks up at
  rr_bot) and the rear top at 328 mm (`Y_REAR_TOP`), so the pickup heights match `main`: rear RC 50 mm, camber gain
  −0.70°/25 mm, bump steer 0.00° (toe link unchanged).
- Deleted: rear lower pickup rail, rear pickup cross, mid-post nodes, the rr_top→r_bot half of the rear side diagonal
  (19° cope; the bay is triangulated by the spool braces and the side-bay diagonal, which now runs r_top→sp_bot).
- Rear rocker re-tuned for the lower pivot: pushrod arm 60 mm, shock bracket (−80, −30, +40) on r_bot, other tangent;
  shock arm 135 mm, clearance 72 mm, +11 % progression.
- `fab.py`: a tube end now copes onto a same-size tube it meets at ≥ 20° before a heavier one it meets shallower (the
  main-hoop brace was being coped onto the lateral brace-plane diagonal at 12°). `fea.py`/`aero.py` take the rear
  pickups from `mule.SUSP` instead of a hard-coded list.
- `frame_opt.py`: rear posts fell to 1.0″ × 0.049″ (they no longer bend), rear-ring bottom cross up to 1.25″ (launch):
  43.6 kg. Rear toe compliance was then 0.249° (limit 0.25), so Rear susp ring → 1.0″ × 0.095″ and MH brace support
  upper → 1.0″ × 0.065″ (+0.6 kg) for 0.227°.
- Result: **44.3 kg, 126 members, 73 pieces, torsion 1946 N·m/deg**; 210/210 checks, 92/92 tests. Against `main`
  (46.4 kg, 78 pieces, 2004): −2.1 kg, −5 pieces, −3 % torsion. Thinner: robust tilt 60.3° (60.4), rear upright arm
  FoS 1.6 (1.8); front hoop roll-over and wheel-load tolerance margins unchanged (1.00 / 1.02).

## 2026-10-01: C2 merged into `main`
- `clean-sheet-C2` merged. Regenerated: `mule.py` (simple CAD, tube order list, views), `fab.py` (cut sheet, bend
  programs, jig), `views.py`, `frame_fea_export.py`, `cad_parts.py` (290 detailed parts), `quote_package.py`
  (152-part frame weldment STEP, material list), `report.py` (210/210 checks, 92/92 tests).
- `cad_parts.py` doesn't delete part files it no longer writes: 89 old-frame STEP files in `cad/parts/` broke the
  quote package's part count and were removed (only files named in `NM26_Assembly_parts.csv` are kept).
- Docs updated to 44.3 kg / 126 members / 73 pieces / 1946 N·m/deg: BUILD_PLAN, PDS, BUDGET_PLAN, FRAME_RESEARCH,
  TEST_PLAN, WHATS_NEXT, WORKDONE.

## 2026-10-01: file history kept (user rule: nothing is ever deleted)
- The 89 old-frame part files removed from `cad/parts/` after the C2 merge were restored from git (byte-identical) and
  moved into `history/frame_v2_46.4kg/cad/parts/`, so `cad/parts/` holds only the current frame.
- New top-level `history/` with a frozen copy of `mule/` for each frame version (`frame_v1_50.1kg`, `frame_v2_46.4kg`,
  `frame_v3_44.3kg`), made by the new `snapshot.py`, which never overwrites. Git tags with the same names.
- `quote_package.py` now builds the frame weldment STEP from the parts list (`cad/NM26_Assembly_parts.csv`) instead of
  every `NM26-FRM-*.step` in the folder, so stray old files can't get into the shop package. Output unchanged.
