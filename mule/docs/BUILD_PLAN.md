# NM26 Mule — Critique, Rules Checklist, BOM, Build Plan

Goal: a car that drives and follows the FSAE 2026 **safety** rules (roll hoops, side impact, harness, brakes, shutdown, impact attenuator, firewall). It deliberately skips competition-only items (intake restrictor, aero, SES/IAD paperwork, noise test, cost report).

Files in this folder:
- `mule.py` — parametric frame (CadQuery). It runs 27 geometric rule checks and refuses to export if any check fails. Outputs `NM26_Mule.step`, `tube_order_list.csv` and `views/simple_*.svg`.
- `views.py` → `views/mule_3view.png` (side, top and front layout).
- `fea.py`: frame beam FEA. `suspension.py`: front-view suspension kinematics. `loads.py`: suspension link forces, link buckling, and frame stress under wheel loads. `springs.py`: spring and shock sizing. `steering.py`: bump steer, Ackermann, rack travel and full-lock clearance. Each script exits with an error if a target is missed.
- `NM26_Frame_FEA.step`: tubes only (93 bodies) for Fusion Simulation. In Fusion, Combine (Join) all bodies first.
- Axes match the concept STEP: X points forward (rear axle at 0), Y points up (ground at 0), Z points to the driver's right. All units are mm.

---

## 1. Critique of `NM26_FSAE_Concept.step`

The concept is a packaging sketch: 94 primitive solids (boxes and straight cylinders). It has no real nodes, no bends and no tube walls. Measured from the file:

| # | Issue in concept | Rule | Fix in mule |
|---|---|---|---|
| 1 | **No main hoop bracing.** The only tubes behind the main hoop meet it at Y≈550, about 600 mm below its top (1164). | F.5.9.4 (≤160 mm below top) | Braces attach 123 mm below the top and are straight back to the rear bulkhead (45° included angle) |
| 2 | **No upper side-impact member or diagonal.** There are only bottom rails between the hoops. | F.6.4.3–6 (3 members/side) | Upper at 320 mm above the lower tube bottom, plus lower and diagonal |
| 3 | Front bulkhead is 520 × 420 mm, which exceeds 400 × 350 without an X-brace | F.8.4.3 | Bulkhead is 385 × 335 outside, with a diagonal fitted anyway |
| 4 | No anti-intrusion plate between the IA and the bulkhead | F.8.1.1 | 1.5 mm steel AIP welded to the bulkhead |
| 5 | Engine block reaches X=−513 but the frame ends at −314, leaving 200 mm unprotected. The rear wing sits 405 mm behind the rear tires. | T.7.5b (≤250); good practice | Engine sits fully inside the frame; no wings on the mule |
| 6 | Main hoop sits 300 mm ahead of the rear axle, with the engine centred *on* the axle. That leaves no room for a chain or differential. (My first mule layout had the same problem; it's now fixed.) | packaging | Main hoop at X=520, which gives about 500 mm for the engine and a short chain to a spool at the axle |
| 7 | No pedals, brakes (rotors/calipers), fuel tank, firewall, harness points, master switch or rack in the model | T.1.8, T.2, T.3, IC.9 | All placed in the mule model or listed in the BOM |
| 8 | All frame tubes are the same 28 mm. There's no distinction between Size A, B and C. | F.3.2.1 | Sizes are assigned per role (see cut list) |
| 9 | Front wing and undertray add work for zero benefit on a mule | — | Deleted |

What's worth keeping from the concept: the 4-corner double-wishbone layout, the approximately 1.2 m tracks, the 530 mm (13") tires, and the rear single-cylinder engine pod.

## 2. Mule layout (from `mule.py`)

- Wheelbase **1750** (the concept had 1600; I stretched it to fit a 95th-percentile driver, the pedals, the engine and the chain). Track is 1220 front and rear (the rear was widened from 1180 for the rear wing's tilt margin, section 2n). Tires are 20.5×7-13.
- The driver sits upright at 20° (T.2.1.d), so a **5-point harness is allowed**. Hip-to-pedal distance is 915 mm.
- Main hoop top is at 1280 mm and front hoop top at 850 mm. Helmet clearance to the hoop line is **65 mm** (the rule needs ≥50).
- Lower side-impact tube bottom is 60 mm above the ground (V.1.4.2 requires ≤90 and prefers ≤75).
- The frame is **126 members, about 44.3 kg** of 4130 (section 2l explains the latest changes; the 2026-10-01 C2 rear puts the rear wishbone pickups on rail nodes). See `tube_order_list.csv` for tube lengths by size. Buy about 25% extra for notching scrap and mistakes.
- These changes came out of the FEA (see section 2b).
- Tube schedule after the 2026-10-01 optimisation (each tube at the smallest size its loads and its F.3.2.1 rule size allow; `frame_rules.py` checks the rule size per job):
  - 1.5″×0.095″: main hoop (AF4 roll-over), front suspension-ring posts (no top cross, T.1.2).
  - 1.25″×0.095″: front hoop, shoulder harness bar, rear bulkhead posts.
  - 1.0″×0.095″: diagonal side impact, upper bulkhead supports, rear suspension ring, engine-mount and main-hoop mid crosses, front pedal-box cross, front part of the lower main-hoop-brace support.
  - 1.0″×0.065″ (Size B): upper and lower side impact, front bulkhead, front and main hoop braces, harness tubes, lower bulkhead supports, rear pedal-box cross, front pickup cross.
  - 1.0″×0.049″ (Size C): main-hoop-brace supports, brace-plane diagonals, front hoop lower brace, cockpit floor V, rear rails, posts and diagonals.
  - Sized by `frame_opt.py` against every gate; re-run it after any geometry change.

Modelling limits to know before cutting tube:
- Hoops are drawn as straight segments between bend nodes. When you bend them, keep the radius ≥ 3×OD = 76 mm (F.5.2.1).
- Tubes overlap at the nodes; they aren't mitered in the model. Notch to the centreline nodes.
- A-arms, uprights, engine, seat and so on are placeholder boxes and tubes for packaging only.
- Suspension and steering geometry were designed afterwards (sections 2c, 2f, 2l).

## 2b. Frame FEA (`fea.py`)

`fea.py` is a 3D beam model of the frame: rigid welded joints, E = 200 GPa, and welded yield 180 MPa applied at every joint (rule F.3.4.2, which is conservative). It first checks itself against a textbook cantilever, and it fails if any case has a safety factor ≤ 1.

| Case | Original | Final |
|---|---|---|
| Torsional stiffness (chassis only, pickup-to-pickup) | 1373 N·m/deg | **2138 N·m/deg** (2004 after the 2026-10-01 weight optimisation, robustness fix and AF4 roll-over correction; 1946 with the C2 node-mounted rear) |
| Main hoop top load 6/5/9 kN: peak stress | 1009 MPa | **140 MPa (safety factor 1.28, worst of the 4 load directions)** |
| Front hoop top load 6/5/9 kN: peak stress | 867 MPa | **133 MPa (safety factor 1.36)** |

Changes that got there:
1. Lateral diagonal across the main hoop braces, and a matching one from the front hoop top to the front suspension ring. Before this, nothing held the hoops sideways.
2. Main and front hoop braces now attach at the hoop top corners instead of 110 mm (main) and 25 mm (front) below the top.
3. Roll hoops upsized to 1.25″×0.095″. Main hoop braces upsized to 1.0″×0.095″. Front bulkhead upper supports and both lateral diagonals upsized to Size B.
4. New front hoop lower brace from the front hoop bend node to the front suspension ring top, running above the driver's shins.
5. Front hoop top widened from ±130 to ±180 mm, which removes a sharp kink that was concentrating stress.
6. For fabrication, each hoop is now a knee bend plus two top corners on a 4″ CLR die. The old front-hoop shape had two bends 25 mm apart, which can't be bent. All braces now land at the hoop top corners.

Caveats:
- The hoop load magnitudes (6 kN lateral, 5 kN longitudinal, 9 kN vertical) are **my assumption of the SES load case. They are not in the rules PDF.** Check them against the current Structural Equivalency Spreadsheet (SES).
- The main hoop margin is thin: safety factor 1.28, when the 6 kN acts forward. The load case comes from FSAE AF4.1/AF4.2, and it passes in all four directions. Deflection is 3.9 mm or less against the 25 mm limit.
- Loads are applied at single points and the model is linear elastic. Cross-check in Fusion Simulation before cutting tube.

## 2c. Suspension (`suspension.py`)

Unequal-length double wishbones front and rear. Each A-arm's inboard pickups are frame nodes on the suspension-ring and bulkhead verticals: front at X=1630 and 2130, rear at X=200 and −300. These heights came from a grid search against the targets below.

| | Front | Rear | Target |
|---|---|---|---|
| Inboard pickup height, lower / upper | 140 / 340 mm | 150 / 340 mm | — |
| Ball joint height, lower / upper | 143 / 380 mm | 146 / 370 mm | Within 125 mm of hub centre (fits inside a 13″ wheel) |
| Roll centre height | 37 mm | 52 mm | Front 15–60, rear 25–80 |
| Camber gain in bump | −0.72°/25 mm (−1.48° at +50) | −0.75°/25 mm | −0.3 to −1.2° per 25 mm |
| Track change at +50 mm | −0.1 mm | +0.6 mm | Small |
| Static camber (shims) | −2.5° | −2.0° | −2 to −3.5° (review notes); outside tyre about −0.9° / −0.4° to the ground at 1.5 g (`roll.py`) |
| KPI / scrub radius | 9.6° / 38 mm | 3.8° / 55 mm | 0–10°; front scrub ≤ 40 mm, rear ≤ 80 mm (section 2m) |
| Wheel travel | +50 / −25 mm | +50 / −25 mm | V.3.1.1 requires 50 mm usable in total |

Notes:
- The pickups sit part-way up the verticals, not at existing nodes, so those verticals bend (front ring 1.5″×0.095″, rear ring 1.0″×0.095″ after the 2026-10-01 optimisation). This is the main reason the frame is heavier than documented FSAE frames; see `FRAME_RESEARCH.md`.
- No cross tubes at the pickup heights, because they would hit the driver's shins at the front and the engine at the rear.
- **Not done yet:** side-view geometry (caster, anti-dive, anti-squat). Steering is covered in section 2f and rockers in 2g.

## 2d. Suspension loads and springs (`loads.py`, `springs.py`)

Each upright is solved as a rigid body held by six two-force links: four A-arm legs, the tie rod or toe link, and the pushrod.

Assumptions: 300 kg with driver, CG 345 mm high, 45/55 front/rear weight, tyre grip μ = 1.5. These are set to cover the `mass.py` budget with the rear wing: 288 kg, CG 341 mm, 47 % front. Design cases: 3g bump, 1.5g cornering (outer wheel), 1.5g braking, combined cornering + braking at μ, and a kerb strike (2× load) while cornering at 1 g.

| Check | Result |
|---|---|
| Worst frame stress, all 10 cases | Safety factor **1.26** (welded yield, inertia relief with engine/driver/fuel masses, rockers). See sections 2g and 2j. |
| Link buckling | A-arms and tie rods 5/8″×0.035″, pushrods 3/4″×0.049″. Worst is the rear pushrod, safety factor **4.4**. |

Pushrod and rocker, with the shock mounted inboard on the rocker:

| | Front | Rear |
|---|---|---|
| Pushrod motion ratio × rocker ratio | 0.58 × 1.24 = 0.72 | 0.39 × 1.94 = 0.75 |
| Ride frequency target | 3.0 Hz | 2.6 Hz (front stiffer for handling balance, see §2m) |
| Wheel rate | 22.1 N/mm | 21.2 N/mm |
| Spring | **~243 lb/in** | **~215 lb/in** |
| Shock stroke for +50 / −25 mm wheel travel | 55 mm | 57 mm |
| Damping, ~30% of critical at the shock | 1.25 N·s/mm | 1.28 N·s/mm |

Shock choice: four mountain-bike coil shocks with at least 60 mm stroke (e.g. 230×65), springs about 250 lb/in front and 200–225 lb/in rear. Tune the ride frequency later by changing springs.

## 2e. Belly pan

A 1.6 mm 5052 aluminium floor closeout (rule T.1.7) runs under the whole frame, from the rear bulkhead to the front bulkhead, following the lower-rail outline. It has two 25 mm drain holes just ahead of the main hoop (rule T.5.5.4). The bottom sits 58.7 mm above the ground, and the pan bolts to tabs on the lowest tubes.

## 2f. Steering (`steering.py`)

The rack sits low, 180 mm above the ground at X = 1670, under the driver's shins. Its ends are at ±190 mm. The steering arms are 80 mm behind the axle and 190 mm high. The column runs down the centreline between the legs and needs two U-joints (T.1.3.3 requires them to be shielded).

| Check | Result |
|---|---|
| Bump steer over ±50 mm | ≤ 0.12° (target ≤ 0.25°) |
| Ackermann | 50 % (inner 23.0°, outer 20.6°) |
| Rack travel to lock | 29.6 mm each side (85 mm steering arms) |
| Rear bump steer (toe link) | 0.00° over ±50 mm: the toe link is aimed at the arms' instant centre (inner end 300 mm up, outer 323 mm) |
| Steering stop (inner wheel) | **23°**, turning radius about 4.7 m at the car centre |
| Tyre/rim to lower A-arm front leg at full lock | 10 mm, measured in 3D |

Clearance, not the rack, sets the lock. At 25° the gap drops to 6.5 mm, because the lower ball joint sits low inside the 13″ wheel. So 23° is too wide for the tightest FSAE hairpins (9 m minimum outside diameter), but fine for a mule. To get more lock, raise the lower ball joint or move the front lower pickup inboard. Either change needs `suspension.py` re-run.

The model spec rules V.3.2.4 (positive stops) and V.3.2.5 (≤ 7° free play) still have to be checked on the built car.

## 2g. Rockers and shocks (`rocker.py`)

Each corner uses a pushrod to a bellcrank rocker, and a 230×65 mm coil shock set at 36 % of its stroke at ride height (25 mm droop, 50 mm bump). The rocker pivots at the node where the pushrod already ended: front ring top and rear bulkhead top. The shock runs down the same vertical tube to a lower pickup node on a small bracket, so every rocker load lands on a frame joint.

| | Front | Rear |
|---|---|---|
| Rocker arms (pushrod / shock) | 92 / 112 mm | 70 / 143 mm |
| Shock mount | front hoop at side-impact height, bracket 80 mm forward and 40 mm up (moved out of the T.1.2 template, section 2l) | rear bulkhead lower pickup, bracket 60 mm rearward and 40 mm outboard |
| Shock length over +50 / −25 mm wheel travel | 169–224 mm (fits 165–230) | 167–225 mm |
| Motion ratio at ride / change bump vs droop | 0.72 / +10 % | 0.75 / +17 % |
| Rocker swing | +9 / −20° | −8 / +16° |
| Shock clearance to tubes and rods | 30 mm | 45 mm |

On its own, the front pushrod geometry gets 40 % softer toward bump. Moving the pushrod pickup 20 mm along the pushrod line turns that into a mild rise in stiffness (+10 %).

**Frame changes the rocker loads needed** (the rocker pivot sees about 10 kN in a rear 3g bump):
- A cross tube at the front and rear lower pickup nodes. The front one sits 140 mm up, under the driver's calves; the rear one is behind the engine.
- A rear lower pickup rail from the rear bulkhead to the rear suspension ring.
- The front ring top cross upsized to Size B. It was later removed so the T.1.2 template could pass (section 2l).

**Load method changed.** Wheel loads are now balanced by the car's inertia instead of pinning the other wheels. Pinning dumped the reaction into short tube stubs next to the pins; letting the whole other axle react swung the error the other way. Worst wheel-load case: safety factor **1.24**.

## 2h. Fabrication package (`fab.py` → `fab/`)

`fab.py` turns the model members into **73 physical pieces of tube**. Collinear runs are merged into one piece, and each roll hoop is a single bent tube (F.5.8.1).

| File | Contents |
|---|---|
| `fab/tube_cut_sheet.csv` | Every straight piece with its tube size and centreline length. Also: the cut length long-point to long-point (cut the stock ~10 mm long and fine-fit), which piece each end copes onto, the cope angle, the phase between the two notches, and where intermediate nodes (tabs, pickups) fall along the tube. |
| `fab/hoop_bend_program.csv` | Bend programs for both hoops as feed / rotation / bend (Y-B-C) on a 4″ CLR die, plus developed length. Main hoop is 2659 mm, front hoop 1868 mm; add 50 mm of grip at each end. The hoops are planar, so every rotation is 0. |
| `fab/jig_node_coordinates.csv` | Every joint: X from the rear axle, height above the jig table, and Z from the centreline. |
| `fab/jig_plan.png` | Top view with fixture posts at the lower nodes. |

Joint rules the script follows:
- The bigger tube always receives the cope.
- The 1.25″ tubes (hoops and the four suspension verticals) are square-cut at their end nodes, and the 1″ tubes cope onto them.
- Open ends are capped (F.5.3.3). The open lower ends of the roll hoops are allowed.

Suggested order: bend both hoops and check them against the bend sheet. Then set the lower nodes on the jig, then tack the side-impact and bulkhead pieces, then the braces.

## 2i. Uprights and hubs (`uprights.py`)

Each hub rotates on two SKF 6209-2RS1 bearings (45×85×19; the 6009 fell to s0 1.46 with the 330 mm CG) pressed into a machined 7075-T6 upright. The rear hub is splined for the CV. The wheel bolts to a 4×100 hub face 25 mm outboard of the wheel centre plane, and the 200 mm rotor sits just inboard of that face with the caliper on the upright. Section view: `views/suspension_corners.png`.

| Check (worst of 3g bump / 1.5g corner / 1.5g brake, and 830 N·m rear drive) | Front | Rear |
|---|---|---|
| Bearing static safety s0 (target ≥ 1.5) | 2.70 | 2.18 |
| Bearing L10 at 1 g cornering duty (need 3.7 Mrev) | 512 Mrev | 271 Mrev |
| Hub shaft, 4140, bending + torsion (target ≥ 1.5) | 10.7 | 5.1 |
| Upright arms, 28×18 mm section, 7075 (target ≥ 1.5) | 3.1 | 1.7 |
| Wheel-stud slip torque vs max wheel torque | 1469 vs 421 N·m | 1469 vs 849 N·m |
| Rotor + caliper radius vs rim barrel | 145 vs 155 mm | same |
| Upright-to-rotor gap | 12 mm | 12 mm |

- The hub is overhung (the wheel centre sits outboard of both bearings), so the inboard bearing load reverses.
- The rear drive torque assumes the spool puts all the rear-axle traction through one tyre.
- **Ball joints and rod ends:** buy static radial ratings of at least 2× these peak joint loads:

  | Joint | Front | Rear |
  |---|---|---|
  | Lower | 3.8 kN | 7.1 kN |
  | Upper | 1.0 kN | 1.5 kN |
  | Steer / toe | 1.3 kN | 2.4 kN |
  | Pushrod | 3.4 kN | 6.1 kN |

- **Verify:** the bearing ratings (C = 22.1 kN, C0 = 15.2 kN) against the supplier's catalogue.

## 2j. Powertrain (`powertrain.py`)

**Engine: Honda CRF450R 2018+.** From the 2017–18 service manual: primary 66/28, gears 32/15, 29/17, 27/19, 23/19, 24/23, dry mass 30.9 kg; published torque 48 N·m. Still generic until an engine is measured: redline 11 500 rpm, envelope X 150–470, countershaft position, mount points. Enter the measured values in `powertrain.ENGINE` and re-run `report.py`.

| Item | Value |
|---|---|
| Gearing | 13T / 50T on 520 chain (3.85). Top speed 113 km/h at redline. 1st gear gives 1000 N·m at the axle, above the 830 N·m traction limit. |
| Chain | 200 mm centre distance (min 185), 125° wrap on the front sprocket. 60 links puts the centre at 205 mm, inside the ±20 mm eccentric carrier adjustment. |
| Chain line | Z = −180 (left), outboard of the engine case and inboard of the spool posts (−222). 11 mm to the nearest frame tube, 126 mm above the ground. |
| Chain tension | 6.6 kN at the traction limit vs 35 kN breaking (verify the chain) |
| Scatter shield (T.5.2.7) | 2.66 mm steel, ≥ 51 mm wide, centred on the chain, covering sprocket to sprocket |
| Spool and CVs | Spool on eccentric bearing carriers bolted to a new vertical post each side at the axle station. Half-shafts are 257 mm long, 11.0° and 4.8 mm plunge at 50 mm bump. |
| Engine mounts | 6 points on the main-hoop base cross, main-hoop mid cross and rear-ring bottom cross, split into nodes at Z = ±130 (±100 failed once the cockpit widened) |
| Launch case | Full traction (830 N·m) through one rear tyre, plus the chain loop, inertia relief: frame safety factor **1.22** |

Frame changes this needed:
- Spool carrier posts with fore-aft braces to the rear ring (the chain pull is about 6 kN).
- A rear side bay diagonal.
- The engine-mount crosses at 1.0×0.095.
- The engine-bay rails at 1.0×0.065.

Moving the mounts outboard to Z = ±140 made things worse (1.06), because the load moved into the rails.

Engine, driver and fuel masses are now in the inertia-relief model. That moved the worst wheel-load case from 1.24 to 1.19 before the rail upsizes, and to 1.23 after. Adding the pedal-box floor tubes (section 2k) shifted stiffness and it is now 1.21, in the front ring top cross.

## 2k. Brakes and pedal box (`brakes.py`)

Layout: a floor-hinged 6061-T6 brake pedal at a **5:1 ratio**, leaning back 10°. Its pivot sits on a 6 mm base plate bolted to two new floor cross tubes. A balance bar in the pedal pushes two forward-facing Tilton 78 master cylinders, one for the front circuit and one for the rear, each with its own reservoir. The throttle pedal sits beside it and pulls a cable (mechanical throttle, IC.3.3), so the car needs no APPS or BSPD.

Part values came from Wilwood and Tilton listings. The pad friction (0.40), line compliance, and **the 300 bar pressure limit are assumptions**. Get the real pressure ratings for the master cylinders, calipers and hoses in writing before doing the 2000 N test.

| Item | Value |
|---|---|
| Calipers | Front Wilwood GP200 (1.25″ pistons), rear Wilwood PS-1 (1.00″), on the 200 mm rotors; pad effective radius 87.5 mm |
| Master cylinders | Front 5/8″, rear 0.75″ (27.9 mm stroke) |
| Lock all four at 1.5 g | **567 N** at the pedal (limit 600). Front 77 bar, rear 41 bar, 59 % front balance. |
| Balance | Both axles lock together at 54.9 % front on 1.5-grip tyres and 44.0 % on a 1.0-grip surface; the adjuster covers 40–60 %. Start at **57 % front** so the fronts lock first. |
| 2000 N pedal (T.3.2.2) | 296 bar front, 145 bar rear (limit 300 bar, unverified). Safety factors: pedal blade 3.8, pivot bolt 6.8, balance bar 2.1, frame 1.31. |
| Pedal travel | 18 mm at 2000 N. With one circuit lost, the pedal travels 74–84 mm before the master cylinder bottoms. |
| BOTS | Trips at **45 mm** pad travel: 26 mm beyond normal travel, at least 29 mm before either master cylinder bottoms |
| Rotor heat | One stop from top speed (117 km/h): +117 °C front, +50 °C rear |
| Packaging | The front of the master cylinders is at X = 2085. That keeps the pedal box 25 mm clear of the anti-intrusion plate without moving the bulkhead. |

Frame changes this needed:
- Two pedal-box cross tubes: the rear one is 1.0×0.065, and the front one (under the master cylinders) is 1.0×0.095.
- The footwell lower rails, from the front ring to the bulkhead, went from 1.0×0.049 to 1.0×0.065.

At that point the frame was 131 members and 46.7 kg; see section 2l for the current totals.

I tried putting the master cylinders 20 mm further forward first. That moved the bulkhead forward and cut the tyre's clearance to the lower A-arm at full lock to 7 mm. So I shortened the stack-up instead: 10° pedal lean and a 25 mm pushrod.

## 2l. Closing the open items: cockpit templates, side view, combined loads, mass/CG, harness, shutdown

This round checked the last unchecked rules and the review notes (Kevin Hayward's *Car Design Workshop* summary). Four of them found real problems in the layout, and all four are fixed.

**Cockpit templates (`cockpit.py`).** T.1.1 and T.1.2 are now modelled geometrically: the templates are swept through the frame, rack, rockers, shocks and seat.
- **T.1.1 (opening) failed by 26 mm.** The 550 mm-wide template didn't fit between the upper side-impact tubes. The cockpit half-width went from 260 to **292** mm, and the template now clears by 5 mm.
- **T.1.2 (leg template) failed at the front ring.** The ring-top cross tube, the footwell pickup cross, the rack and the front shocks all blocked it.
  - *Rejected, rack moved ahead of the pedals:* 4.4° bump steer and anti-Ackermann.
  - *Rejected, ring raised to 570 mm:* the ring posts bent, front-hoop FoS 0.66.
  - *Chosen:* keep the rack low (the kinematics decide where the rack goes) and let the template pass over it. The **front ring has no top cross tube**, and its posts are **1.5″×0.095″** to carry the bending. The **front shock moved to the front hoop** at side-impact height, clear of the template.

**Side view (`sideview.py`):**
- Caster **4.6°** and mechanical trail **11.5 mm**, from moving the upper ball joint 19 mm rearward.
- Anti-dive and anti-squat are **0 %**. The pivot axes are level; that's a deliberate choice, because the notes point out anti geometry makes the ride harsher.
- Dive is 26 mm at 1.5 g braking, and squat 12 mm at 1 g.
- Roll-centre migration is about 1.7 mm per mm of heave. The front roll centre reaches about −6 mm at full dive.
- Bump steer at full lock is **0.11°** over ±25 mm.
- Steering ratio is **4.1:1**: 178° lock-to-lock with the Kaz 4.71 in/rev rack and 85 mm steering arms, so no hand-over-hand (section 2m). Rim force is about 95 N at 1.5 g.
- *Known limit:* the kinematic turning circle is **5.7 m** radius at the outer tyre. FSAE hairpins (D.8) need 4.5 m, so the mule can't make a competition hairpin without sliding. Lock is capped at 23° by tyre clearance to the lower A-arm.

**Combined load cases (`loads.py`).** Two cases are added: cornering + braking at the friction limit, and a kerb strike (twice the load) while cornering at 1 g. Results:
- worst frame FoS **1.26**;
- worst link buckling FoS 4.4;
- uprights, all checks pass.

**Mass and CG budget (`mass.py`).** Every item is listed with a mass and position.
- **Result:** **288 kg**, **47.4 %** front, CG **323 mm**, unsprung **15.3 kg** per corner.
- **What that exposed:** the load cases had assumed CG 300 mm and 12 kg unsprung, both unconservative. They are now 330 mm and 15 kg, and a test fails if they stop covering the budget.
- **Knock-on fixes:**
  - hub bearings → **6209-2RS1**;
  - rear master cylinder → **0.75″**;
  - rear lower rail → 1.0×0.095;
  - main-hoop mid cross → 1.25×0.095.
- **Tilt test (IN.11):** the car rolls at **60.8°** against the required 60° (60.3° if every mass estimate errs the same way) (with the rear wing and the 1220 mm rear track; it was 61.3° before the wing). **That is the thinnest margin on the car**, so measure the CG early (TEST_PLAN T4.1).

**Harness (`harness.py`):**
- **Lap belt:** the old plan put the lap belts on the main-hoop base, which gave a **15° lap-belt angle** (T.2.5.4 needs 45–65°). The lap tabs moved onto the lower side-impact tubes under the hips, giving **55°**. Each tab has a brace up to the side-impact diagonal, and a floor cross ties the two tabs together.
- **Anti-sub:** on a new floor cross with a V back to the main hoop base, at **0°** from vertical.
- **Tabs:** 3.2 mm 4130 with M10 bolts, **31.7 kN** double tear-out (T.2.4.3 needs 15 kN).
- **Frame crash check (20 g on the driver):** FoS **1.17** against welded ultimate strength. Some local yielding is allowed in a crash; tearing is not. That needed the **1.5″ shoulder bar**, because 584 mm is now a long span.

**Shutdown and wiring (`shutdown.py`).** The circuit is simulated as a netlist:
- **Topology:** battery, then a 100 A fuse, then the rotary master switch. It carries all battery current and is placed on the driver's right, at the main hoop, at shoulder height. The E-stop, BOTS and inertia switch are in series with a normally-open kill relay that feeds ignition and the fuel pump.
- **Verified:**
  - opening any device kills ignition and the fuel pump;
  - the master switch kills everything;
  - every branch is fused, and every wire and switch carries at most its rating;
  - voltage drop to the pump and ignition is 0.23 V;
  - battery, master switch and brake light positions are legal.

**Frame totals now** (after the 2026-10-01 optimisation, robustness fix, AF4 roll-over correction and C2 node-mounted rear, see PROJECT_LOG): 126 members, **44.3 kg**, 73 pieces (2 bent). Torsion is **1946 N·m/deg** FEA (target ≥ 1500 FEA, ≥ 1000 measured). Safety factors, nominal and worst of 16 tube-tolerance samples (`robustness.py`):

| Case | Criterion | FoS nominal | FoS worst with tolerances |
|---|---|---|---|
| Main hoop roll-over (AF4 support) | welded 4130: yield 340 / ultimate 410 MPa | 1.09 | 1.14 (vs ultimate) |
| Front hoop roll-over (AF4 support) | as above | 1.02 | 1.00 (vs ultimate) |
| Wheel loads | FSAE welded yield 180 MPa, FoS 1.2 | 1.23 | 1.02 |
| Launch | as above | 1.26 | 1.10 |
| 2000 N pedal | as above | 1.32 | 1.18 |
| Harness crash | FSAE welded ultimate 300 MPa | 1.19 | 1.07 |

## 2m. Design-review gaps closed (Hayward, *Car Design Workshop*)

| Gap | Before | Now | How / file |
|---|---|---|---|
| Scrub radius (front) | 53 mm, KPI 4.8° | **38 mm**, KPI 9.6° | Lower ball joint 3 mm deeper in the wheel, upper one leaning 40 mm inboard (`mule.SUSP`). Lower still needs the lower arm's front leg moved: at 50 mm inset the tyre comes within 2 mm of it at full lock. Check limit is now ≤ 40 mm. |
| Motion ratio | 0.59 / 0.50 | **0.72 / 0.75** | Rule V.3.1.1 asks for 50 mm of usable travel *in total*, not ±50 mm. Travel is now 50 mm bump and 25 mm droop, so a 65 mm-stroke shock fits a 0.7+ ratio. Rocker ratios 1.24 / 1.94; rear pushrod arm 70 mm (`springs.MR`, `rocker.py`). Springs became ~175 / 257 lb/in; the balance fix below set them to ~243 / 215. |
| Lock-to-lock | 233° | **178°** | Kaz Technologies FSAE rack (4.71 in/rev, a real part) with the steering arms lengthened from 80 to 85 mm; ratio 4.1:1, Ackermann 50 %. A new check puts the rim force at 95 N at 1.5 g (limit 120 N) and the kickback at 9.3 N·m per 1 kN on one front tyre. |
| Static camber | not set | **−2.5° front, −2.0° rear** | `roll.py`: 1.5°/g roll gradient, so at 1.5 g the outside tyre sits at −0.9° / −0.4° to the ground. |
| Roll-centre movement in roll, jacking | not checked | RC stays above ground (23 / 36 mm at 1.5 g); lift < 1 mm | `roll.py`. The RC moves about 95 mm sideways per degree of roll, normal for a low RC. |
| Bracket and pickup stiffness | not modelled | toe 0.10° in (front), 0.18° out (rear) at 1.5 g; camber ≤ 0.04° | `compliance.py`: frame FEA at the pickups plus link stretch, upright solved on its six links. No arm or rod end is bent: every link is two-force, and the pushrods land on the uprights. The rear outside wheel toes *out*, a small oversteer effect. About half of that is link stretch and half frame flex. No single tube upsize changes it by more than 0.01°, and a clamp nearer the rear axle halves the frame part, so 0.18° is the conservative figure. TEST_PLAN T2.7 measures it. |
| Handling balance (from the NAU 2025 FSAE suspension report's roll-stiffness method) | not checked; really **40 % of the lateral load transfer on the front** with 45 % of the weight there, so the rear saturates first (oversteer) | **49.6 % front** | `roll.lltd()` (Milliken: elastic part split by roll stiffness, plus each axle's geometric part). Fixed by swapping the ride frequencies to 3.0 Hz front / 2.6 Hz rear. That breaks the old "rear stiffer for a flat ride" rule, but balance matters more on a light car. Springs are now ~243 / 215 lb/in and brake dive falls from 30 to 22 mm. A front anti-roll bar of about 100 N·m/deg would do the same, but it would have to cross the front ring top where the T.1.2 template passes, so it's left as a later tuning part. |
| Rear bump steer (found while doing the above) | not checked; really **0.76° toe-out per 25 mm** of bump (roll oversteer) | **0.00°** | `steering.py` now checks the rear too. The toe link is re-aimed at the rear arms' instant centre (`mule.SUSP['rear']['steer']`). |
| Lap simulation | none | acceleration 4.48 s, skidpad 5.12 s, autocross 58.6 s (51 km/h) | `lapsim.py`, point mass, grip 1.3 (calibrated: the 2025 Michigan skidpad winner implies 1.34). The autocross is a representative 0.8 km course built to the D.11.1.1 layout rules. Sensitivity: 0.1 grip = 0.16 s accel, 0.21 s skidpad, 2.4 s autocross; 10 kg = 0.01 s accel. A point mass has no tyre load sensitivity, so mass looks almost free; in reality it isn't. Drag alone would allow 146 km/h, above the 117 km/h gearing limit. |
| Benchmark, Pugh matrix | none | Pugh matrices, plus a benchmark against the FSAE Michigan 2025 event times, in `PDS.md` | The mule's point-mass times sit between the 10th-place car and the median. The vehicle-number columns (other teams' mass, stiffness, etc.) wait for published design reports. |
| Buck, part numbers | none | Buck plan below; every CAD body named `NM26-<system>-<nnn>`, listed in `NM26_Mule_parts.csv` (and `cad/NM26_Assembly_parts.csv` for the detailed model) | `mule.PART_CODE` |

**Full-scale buck (before cutting any tube).** Build it in a weekend from 2×4s, plywood and ¾″ EMT conduit, using `fab/jig_node_coordinates.csv` for the coordinates:
1. Floor board at the lower-rail outline. Mark the pedal face, the seat base and the hip point from `mule.py`.
2. Main hoop and front hoop from bent conduit, at their true stations and heights. Mark the front ring with its posts only; it has no top cross.
3. Seat from foam blocks at the 20° back angle. Add a pedal block at the pedal face and a steering wheel on a stick at `WHEEL_C`.
4. Seat the tallest and the smallest driver (V.2.1.1: 5th percentile female to 95th percentile male), each in a helmet and harness straps. Check four things:
   - the helmet is 50 mm below the line from the main hoop top to the front hoop top (F.5.6.6);
   - the T.1.1 and T.1.2 plywood templates pass (TEST_PLAN T4.3);
   - the heel and knee angles, pedal reach and the view over the wheels are comfortable;
   - each driver can get out to the side in under 5 s (IN.9.2.1), timed from hands on the wheel.
5. Record anything that fails. Move the node in `mule.py`, re-run `python report.py`, and only then order tube.

**Part numbers.** Every body in `NM26_Mule.step` is named `NM26-<system>-<nnn>_<description>`:

| Code | System |
|---|---|
| FRM | frame |
| SUS | suspension |
| WHL | wheels |
| UPR | uprights |
| BRK | brakes |
| STR | steering |
| PWT | powertrain |
| FUL | fuel |
| CKP | cockpit |
| BDY | body and crash |
| ELE | electrical |

Numbers are assigned in build order. `NM26_Mule_parts.csv` lists every part number with its name and colour; `cad/NM26_Assembly_parts.csv` does the same for the detailed model and says what each file contains. Freeze that list (copy it into the BOM) before making drawings or placing orders. After that, add new parts at the end instead of re-numbering.

## 2n. Rear wing with DRS (`aero.py`)

Added at the team's request. Aero is now in scope; see PDS R15.

**Layout.** A two-element wing with a fixed main plane (300 mm chord, 10°) and a moving flap (170 mm chord). The flap pivots at 30 % of its chord, close to where its aero load acts, so it takes little torque to move. It sits between 3 mm endplates, 1006 mm span, 0.47 m² planform.
- Mounting: two vertical 1.0×0.049″ struts from the rear-bulkhead top nodes carry a mounting spar. Each strut is braced forward to the main-hoop top, and one diagonal takes side load.
- Flap positions: closed at 40° (high downforce), open at 10° (DRS, low drag).
- CAD: every part is White and numbered `NM26-AER-nnn`.

**Rules (T.7), checked at both flap positions:**
- behind the head-restraint plane, so inside the rear aero zone;
- rear edge 9 mm inside the 250 mm limit behind the rear tyres (T.7.5b);
- endplates 14 mm inboard of the rear tyres' inner faces (T.7.6.3);
- top at 1188 mm, against the 1200 mm limit (T.7.7.1a).

Still to do at build: 5 mm radii on the leading edges, 3 mm on the vertical edges (T.7.1.4).

**Moving flap (DRS).** The rules don't ban a moving wing. T.7.1.3 and IN.6.2 only require it to be stiff and not oscillate. Control:
- a 12 V servo (at least 15 N·m stall, about 150 kg·cm) opens the flap only while the driver holds a button on the wheel **and** the brakes are off (brake-light switch);
- a return spring, sized at 1.3× the worst aero moment, shuts it on button release, on braking, and on any loss of power (master switch, fuse, servo failure);
- so every failure leaves full downforce. The servo runs on its own 7.5 A fused branch (`shutdown.py`).

**Aero numbers.** These are ASSUMED coefficients, not CFD: CL 1.6 / CD 0.30 closed, 0.55 / 0.10 open.

| | Closed | Open (DRS) |
|---|---|---|
| Downforce / drag at 60 km/h | 126 / 24 N | 43 / 8 N |
| Downforce at 117 km/h (top speed) | about 476 N | |

The wing sits behind the rear axle, so at top speed it adds 587 N to the rear axle and takes 110 N off the front (8 %). That shows up as mild understeer at high speed. TEST_PLAN T5.5 measures the real downforce.

**Mounts.**
- 200 N push (IN.6.2.2): 0.1 mm deflection, against 25 mm allowed.
- Top-speed load × 1.5 plus a 3 g bump: safety factor far above 1.5.
- First mode 159 Hz, well above wheel hop, so the wing won't oscillate (T.7.1.3b).
- Lighter layouts were tried: without the diagonal the mount drops to 29 Hz, and without the braces to 15 Hz, which is inside the wheel-hop range. So the full layout stays.

**What it cost elsewhere.**
- The wing, servo and struts add 7.4 kg high up. The CG rises from 323 to 340 mm.
- To keep the tilt test above 60°, the **rear track widened from 1180 to 1220 mm**. Every check was re-run. The tilt angle was 60.9° then; with the 44.3 kg frame it is 60.8°.
- Load cases now assume a 345 mm CG. Frame and uprights still pass.
- Brake pressure at the 2000 N pedal test rose to **296 bar**, against the unverified 300 bar limit, so the supplier ratings are now urgent.

**Lap-sim value** (point mass, wing closed in corners and braking, open on straights): autocross −0.67 s (about 1 %), skidpad −0.04 s, acceleration ±0.00 s. Most of the benefit is in faster corners, and it grows with speed.

## 3. Rules checklist (full FSAE 2026 rules: nothing is skipped or traded)

✅ = checked by code (`mule.py`, `frame_rules.py` and the other modules). ☐ = must be verified on the real part or at build. Every frame-relevant rule, with its status, is listed in [RULES_MATRIX.md](RULES_MATRIX.md).

**Vehicle (V)**
- ✅ V.1.2 Wheelbase ≥1525 · ✅ V.1.3.2 Track ratio ≥75% · ✅ V.1.4.2 Lower SIS ≤90 mm off the ground
- ☐ V.1.1c No bodywork within 75 mm fore/aft of the tires
- ☐ V.3.1.1 Shocks front and rear, ≥50 mm usable wheel travel with the driver seated
- ☐ V.3.1.5 / V.3.2.9 Rod ends in double shear or captured by a washer
- ☐ V.3.1.4 / T.8.2 Every suspension fastener is a Critical Fastener: SAE Grade 5, metric 8.8 or AN/MS; hex or socket head, not countersunk; positively locked (T.8.3); ≥ 2 full threads past any lock nut
- ☐ V.3.2.4 Positive steering stops · ☐ V.3.2.5 Steering free play <7° · ☐ V.3.3.2 Quick-release steering wheel · ☐ V.3.3.4 Round or oval wheel, no cutouts
- ☐ V.4.2.1 A center-lock single-nut hub needs a retainer (or just use 4-lug hubs)

**Chassis (F)**
- ✅ F.3.4.1 Tube sizes · ✅ F.5.8.4 Main hoop base width ≥380 · ✅ F.5.9.4/5 Brace attach and angle · ✅ F.6.3.4 Front hoop brace ≤50 mm below top
- ✅ F.5.7.4/5 Front hoop vs. steering wheel · ✅ F.5.6.4 Helmet ≥50 mm from the hoop lines · ✅ F.6.4.4 Upper side-impact height
- ☐ F.5.8.1 Main hoop is **one uncut bent piece** of steel · ☐ F.5.2.1 Bend radius ≥76 mm · ☐ F.5.3.3 Cap open tube ends
- ☐ F.5.15 Neck guard if a tube runs alongside the driver's neck
- ✅ F.8.4.2 / F.8.5.6 IA size and height · ✅ F.8.6.3 Pedals 25 mm from the AIP · ☐ F.8.2 AIP is 1.5 mm steel, welded with welds ≥25 mm long
- ☐ SES and IAD report (F.2, F.8.8): required paperwork. Using the Standard Foam IA means no crush test of our own (F.8.4.1, F.8.8.3).

**Cockpit and driver (T.1, T.2)**
- ✅ T.1.1 / T.1.2 Cockpit opening and cross-section templates (`cockpit.py`, section 2l) · ☐ confirm with plywood templates (TEST_PLAN T4.3b)
- ✅ T.1.5.1 Seat is above the lowest tube · ☐ T.1.3.3 Shield moving parts in the footwell · ☐ T.1.6 Heat shielding (8 mm insulation, 25 mm air gap, 0.4 mm metal shield)
- ☐ T.1.7 Floor closeout, gaps ≤3 mm · ☐ T.1.8 Firewall: rigid, nonflammable, sealed, grommeted, and tall enough (behind the driver and in front of the fuel and engine)
- ✅ T.2.6.1/2 Shoulder belt angle −8° and spacing 200 mm · ✅ T.2.5.4 Lap belt angle 55° · ✅ T.2.7.1 Anti-sub 0° · ✅ T.2.4.3/4 Tabs 3.2 mm, 31.7 kN tear-out, welded both sides (`harness.py`) · ☐ T.2.2 SFI 16.1/16.5 or FIA harness, in date
- ☐ T.2.8 Head restraint: CONFOR CF45, ≥38 mm thick, within 25 mm of the helmet · ☐ T.2.9 Roll-bar padding (SFI 45.1) wherever the helmet can touch

**Aero (T.7, IN.6.2)**
- ✅ T.7.3–T.7.7 Wing in the rear aero zone, ≤ 250 mm behind the rear tyres, inboard of the rear tyres, ≤ 1200 mm high, at both flap positions (`aero.py`)
- ✅ IN.6.2.2 200 N push ≤ 25 mm (calculated 0.1 mm) · ✅ T.7.1.3 mounts stiff, first mode 159 Hz · ☐ T.7.1.4 5 mm / 3 mm edge radii · ☐ T.7.1.5 no sharp edges · ☐ DRS fails closed: test on brake, button release and power off (TEST_PLAN T5.5)

**Brakes (T.3)**
- ✅ T.3.1.2 All 4 wheels, one pedal, able to lock all 4 (567 N at μ 1.5, `brakes.py`) · ✅ T.3.1.3/4 Two circuits (front/rear), one MC and reservoir each
- ✅ T.3.2.2 Pedal, pivot, balance bar and frame survive 2000 N (calculated) · ☐ confirm the MC, caliper and hose pressure rating ≥ 296 bar · ☐ T.3.2.1 Pedal is 6061-T6, machined
- ☐ T.3.1.7 Braided stainless lines only · ☐ T.3.1.9 Nothing on the sprung mass below the chassis · ☐ T.3.1.10 Brake fasteners are critical fasteners (T.8.2)
- ✅ T.3.3 BOTS position calculated (trips at 45 mm pad travel) · ☐ push-pull/flip switch, latches off, not driver-resettable, analog, opens the shutdown circuit · ☐ T.3.4 Red brake light on black, ≥15 cm², centreline, between wheel centre and shoulder height
- ✅ IC.3.3 Mechanical throttle cable (so no APPS/BSPD, which are ETC-only) · ☐ two return springs at the throttle body, positive pedal stop, cable ≥50 mm from the exhaust and guarded from the driver's feet

**Powertrain and shutdown (T.5, IC)**
- ☐ IC.1.1 Four-stroke engine ≤710 cc · ☐ T.5.2.7 Chain guard: 2.66 mm steel, 3× the chain width · ☐ T.5.2.10 Finger guards
- ☐ T.5.4.1 Plain water coolant only · ☐ T.5.5.2 Tilt to 45° without leaks · ☐ T.5.5.4 Two 25 mm drain holes
- ☐ IC.5.3 Fuel tank mounted solidly, not carrying structural loads, behind the firewall · ☐ IC.1.2 Fuel and intake inside the tire envelope
- ✅ IC.9 Shutdown circuit designed and simulated (`shutdown.py`): primary master switch (rotary, driver's right, at the main hoop, shoulder height, all battery current), 40 mm cockpit E-stop, BOTS and inertia switch in series with a normally-open kill relay feeding ignition and fuel pump · ☐ wire it and run TEST_PLAN T4.4
- ✅ T.9.4 Inertia switch included · ✅ T.9.2.1 Battery inside the structure below the shoulder bar · ☐ T.9.2.2 main fuse 100 A ≤ the battery's max discharge (check the battery you buy)
- ☐ IC.2 20 mm intake restrictor (already in the CAD airbox) and IC.7 noise limit: required. IC.4 electronic throttle rules apply only if an electronic throttle is fitted; the mechanical cable throttle complies.

**Equipment (VE)**
- ☐ VE.2.1 Orange 25–30 mm jacking bar at the rear · ☐ VE.2.2 Push bar · ☐ VE.2.3 Two 10BC dry-chemical fire extinguishers (off the car) · ☐ VE.3 Driver gear (helmet, suit, gloves)

## 4. Bill of materials (rough cost estimates, USD — check current prices)

Buying used where possible and machining uprights in-house, the total comes to roughly **$9–15k** in one go. **For a phased build in funding steps of about $2,500 or less (about $6–9k to a driving car), see [BUDGET_PLAN.md](BUDGET_PLAN.md).**

| Subsystem | Item | Qty | Est. $ | Notes |
|---|---|---|---|---|
| Frame | 4130 N round tube, 1.25×0.095 / 1.0×0.095 / 0.065 / 0.049 | ~6 / 4 / 17 / 21 m | 700–1,000 | Lengths from `tube_order_list.csv` plus 25% |
| | Tabs and plate (4130 0.090″, 0.125″), 1.5 mm AIP | — | 150 | |
| | TIG filler (ER70S-2), notcher holesaws | — | 200 | |
| Engine | Used 450–510 cc single (KTM 450/500 EXC-F, Yamaha WR450F, Honda CRF450X) with harness and ECU | 1 | 1,500–3,500 | Electric start preferred. Measure it and update `powertrain.py` `ENGINE`. |
| | 520 O-ring chain (60 links), 13T front / 50T rear sprockets, spool, eccentric bearing carriers, 2.66 mm steel chain guard | 1 set | 500–900 | See section 2j |
| | Tripod CV half-shafts (ATV/UTV or FSAE-supplier) | 2 | 400–1,000 | |
| | Radiator + fan, fuel cell (~6 L) + pump + filter, exhaust/muffler | — | 700–1,200 | |
| | Throttle cable/pedal, shifter (paddle cable or lever) | — | 150 | |
| Suspension | 4130 tube: A-arms/tie rods 5/8″×0.035″, pushrods 3/4″×0.049″; rod ends, spherical bearings | 8 A-arms + 4 rods | 600–900 | |
| | Shocks: MTB coil 230×65 mm, springs ~250 lb/in front / ~215 lb/in rear | 4 | 800–2,000 (300–600 used) | See sections 2d and 2g |
| | Rockers (machined 6061/7075 or 1/4″ steel plate), pivot bearings | 4 | 200–400 | Ratio 1.24 front, 1.94 rear; front shock mounts on the front hoop |
| | Uprights 7075-T6 (machined), hubs 4140 Q&T (rear splined for CV), 8× SKF 6209-2RS1 bearings, 200 mm rotors, 16× M12×1.5 10.9 studs | 4 corners | 800–2,000 | See section 2i |
| Steering | Rack ~380 mm between tie-rod ends with ≥ 30 mm travel each side and Kaz Technologies FSAE rack, 4.71 in/rev, $850 (4.1:1 overall with 85 mm arms, 178° lock-to-lock), 2 U-joints, quick-release, wheel, adjustable steering stops | — | 400–700 | See section 2f |
| Brakes | Tilton 78-625 (front) + 78-750 (rear) master cylinders, 2 remote reservoirs, 5/8″ 4140 balance bar with remote adjuster | 1 set | 400–700 | See section 2k |
| | Pedal box: 6061-T6 brake and throttle pedals (5:1), 6 mm base plate, MC bracket, M8 10.9 pivot bolts | 1 | 150–300 | Machined in-house |
| | Wilwood GP200 (front, 1.25″, 0.25″ disc) ×2, PS-1 (rear, 1.00″, 0.20″ disc) ×2; 200 mm steel rotors ×4 (6.35 / 5.08 mm) | — | 800–1,500 | |
| | Braided stainless -3 lines and fittings, DOT 4 fluid | — | 150–250 | |
| | BOTS switch, brake light, pressure switch | — | 60 | |
| Wheels | 13″ wheels + 20.5×7-13 FSAE slicks (used is fine) | 4 | 800–1,600 | |
| Safety | 5-point SFI 16.1 harness | 1 | 250–400 | |
| | Seat (foam-molded fiberglass), CONFOR CF45 head restraint, SFI 45.1 roll-bar padding | — | 300 | |
| | Standard Foam IA (Event Website) | 1 | 100–200 | |
| | Firewall (1 mm aluminum/steel), 1.6 mm 5052 belly pan (~2.4 × 0.6 m sheet), heat shielding | — | 250 | |
| | Master switch (≥100 A, rotary), 40 mm E-stop, inertia switch, 30 A kill relay, LiFePO4 OEM-style battery, 100 A ANL fuse, fuse box, TXL wire 18–12 AWG, 4 AWG battery cable | — | 300–400 | See section 2l / `shutdown.py` |
| | Fire extinguishers 2 lb 10BC ×2, jacking bar, push bar | — | 150 | |
| Aero | Rear wing: foam-core carbon or fibreglass main plane and flap, aluminium endplates, 1.0×0.049″ 4130 struts and braces, ≥ 15 N·m 12 V servo, return spring, flap bearings, wheel button, 7.5 A fuse | — | 600–1,200 | Section 2n / `aero.py` |

## 5. Build sequence

1. **Freeze the layout (1 week).** Seat a real tall driver and a real short driver in a plywood/2×4 mock-up at the `mule.py` dimensions. Adjust `HIP_Y`, `SEAT_BACK_DEG` and `H_MAIN`, then re-run until everything passes.
2. **Check the plywood cockpit templates (T.1.1, T.1.2) against the mock-up (1 day).** Suspension and steering are already designed (`suspension.py`, `steering.py`, `sideview.py`); pickup coordinates are in `fab/jig_node_coordinates.csv`.
3. **Frame jig and bends (1 week).** Laser-cut or plywood node fixtures on a flat table. Bend both hoops first, since they're single pieces.
4. **Weld the frame (3–4 weeks).** Work in this order: hoops and side impact, then front bulkhead, then rear box, then tabs (suspension, harness, engine, pedals). Check the templates (T.1.1, T.1.2) before welding the tabs.
5. **Rolling chassis (2 weeks).** Arms, uprights, hubs, steering, wheels. Set alignment: camber −2.5° front / −2.0° rear, zero toe to start.
6. **Powertrain and electrics (3 weeks).** Engine mounts, spool and carriers, chain alignment, chain guard, cooling, fuel, exhaust. Wiring loom per `shutdown.py`: wire gauges, fuses, and the kill-relay shutdown loop.
7. **Brakes and controls (1 week).** Bleed, test both circuits separately, BOTS, brake light.
8. **Safety fit-out (1 week).** Seat, harness, head restraint, padding, firewall, floor, heat shields.
9. **Self tech-inspection.** Run [TEST_PLAN.md](TEST_PLAN.md) stages 1–7 in order; stages 3 (brakes) and 4 (shutdown, tilt) must pass before anyone drives. Go through this checklist item by item, tilt to 45° with fluids in, and do a 4-wheel lock-up brake test.
10. **Shakedown.** Parking-lot laps at low speed, then build up. Keep a fire extinguisher at hand, have a spotter, and log what breaks.

Rough total: **14–16 weeks** with 4–6 active members.
