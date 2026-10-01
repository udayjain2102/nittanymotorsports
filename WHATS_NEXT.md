# What's next

In order. Tick them off here as they're done. The costs come from [`mule/docs/BUDGET_PLAN.md`](mule/docs/BUDGET_PLAN.md), the parts from [`mule/docs/PARTS_LIST.md`](mule/docs/PARTS_LIST.md).
Last updated 2026-10-01. Engine chosen (CRF450R 2018+); frame 44.3 kg (C2 node-mounted rear, merged), every check passing; total to a driving car about **$7,400–10,900**.

## This week (no money needed)
- [ ] Ask nearby FSAE teams for used 13″ wheels, slicks, MTB coil shocks, rod ends and uprights.
- [ ] Ask Keizer and Hoosier about FSAE sponsorship or discounts.
- [ ] Submit the funding request for **step 0 ($100–200)** and **step 1 ($1,100–1,600)**.
- [ ] Borrow or find a CRF450R 2018+ to measure (a dealer, a team member's bike or another FSAE team). The frame can't be finalised without its mount points.

## Frame quote and review
- [ ] Send the shop the whole `mule/quote/` folder (frame STEP, material list, shop data, cover note) for a preliminary quote, in 4130 and 1020 DOM.
- [ ] Ask the faculty advisor or an FSAE alum to review the roll-over criterion (welded 4130: 340 MPa yield, 410 MPa ultimate; `SIM_TO_REAL.md`) and the TIG procedure. If the shop quotes 1020 DOM, the criterion has to be redone for that steel.

## Clean-sheet frame designs (each on its own branch; `main` is now C2, 44.3 kg)
Realistic target with the current safety standards: **~44–45 kg** for the frame types tried so far; the 30s need a different packaging (see WORKDONE §8).
- [x] B1 front box ahead of the leg template: 51 kg, rejected (branch `clean-sheet-B`).
- [x] C1 "short" (branch `clean-sheet-short`): 46.5 kg, 74 pieces, torsion 2305 (main: 46.4 kg, 78, 2004). Same mass, stiffer, more margin, fewer pieces; helmet clearance thinner (54 vs 65 mm). **No weight win**; keep as the candidate if stiffness/fewer pieces matter more than 0.1 kg.
- [x] **C2 node-mounted rear** (branch `clean-sheet-C2`): **44.3 kg**, 73 pieces, torsion 1946, every check passing. −2.1 kg against `main`, the best concept so far. Thinner: robust tilt 60.3°, rear upright arm FoS 1.6. Combining it with C1's seat/front hoop is untested.
- [ ] C3 direct-acting front shocks: no front rockers (needs a new shock model in `rocker.py`/`springs.py`).
- [x] Winner so far: C2, merged into `main`; CAD, shop data and the quote package regenerated. If C3 or a C1+C2 combination beats it, merge that the same way.
- [ ] Give `frame_opt.py` a rule that a straight run of one tube keeps one size (it can currently size two collinear parts differently, which can't be coped).

## Before ordering frame tube: pin down the engine
The frame's engine mounts are welded in step 1, so the engine has to be known first.
- [x] Choose the engine: **Honda CRF450R 2018+** (electric start is standard from 2018; a 2017 only if it already has Honda's electric-start kit). The kit engine (Predator 420 + CVT) was ruled out: it does not fit the 450 bay (`python powertrain.py`, Option A).
- [x] Service-manual data in `ENGINE` in `powertrain.py`: primary 66/28, gears 32/15, 29/17, 27/19, 23/19, 24/23, dry mass 30.9 kg (2017–18 service manual p. 1-4/1-5). Rev limit not found yet.
- [ ] Measure the engine (or a borrowed one) for mount points, countershaft position and envelope; enter them in `ENGINE` and make `python report.py` pass **before** ordering tube.

## Step 0: mock-up ($100–200)
- [ ] Build the plywood/conduit buck (`mule/docs/BUILD_PLAN.md` §2m).
- [ ] Fit the tallest and the smallest driver; check the T.1.1/T.1.2 templates; time a 5 s exit.
- [ ] Fix anything that fails in `mule/mule.py` **before** ordering tube, and re-run `python report.py`.

## Step 1: frame ($1,100–1,600)
- [ ] Order 4130 tube from `mule/fab/tube_order_list.csv` (+25 %), plus tabs, plate and filler.
- [ ] Build the jig from `mule/fab/jig_node_coordinates.csv`; cut and cope from `mule/fab/tube_cut_sheet.csv`; bend hoops from `mule/fab/hoop_bend_program.csv`.
- [ ] Weld the frame. Run TEST_PLAN stage 1 (weight, twist stiffness: predicted 1946 N·m/deg FEA, pass ≥ 1000 measured).
- [ ] Take photos and results to the next funding request.

## Steps 2–4: to a driving car
- [ ] Step 2, rolling chassis ($1,800–2,500): suspension, used shocks, fabricated steel uprights (re-check in `uprights.py`), used wheels and tyres, cheap rack. Then TEST_PLAN stage 2.
- [ ] Step 3, engine and drive ($2,600–4,000 with a used 450). This is over the ~$2,500 per request, so split it: **3a** the engine ($1,500–2,800, a running 2018+ CRF450R with electric start), then **3b** chain, sprockets, spool, CV shafts, cooling, exhaust and fuel. Check the engine against the measured numbers before 3b.
- [ ] Before step 4: email Wilwood (GP200, PS-1 calipers), Tilton (78-series master cylinders) and the hose supplier for their **maximum pressure ratings in writing**. We need at least 296 bar (4,290 psi). *(On hold for now.)*
- [ ] Step 4, brakes, safety and electrics ($1,800–2,600): buy only brake parts rated for 296 bar or more; buy the harness new. Then TEST_PLAN stages 3–6. **First drive.**

## After it drives
- [ ] Weigh the car and enter real masses in `mule/mass.py`: the tilt margin is only 0.4–0.9°.
- [ ] TEST_PLAN stage 7 (skidpad); put the measured grip back into `lapsim.py`.
- [ ] Upgrades, one request each: new tyres → Kaz rack → rear wing + DRS → data logging.

## Keeping the repo useful
- After every test stage, run the real-to-sim loop in `mule/docs/SIM_TO_REAL.md`: record predicted vs measured, fix the model input that was wrong, re-run `report.py`.
- Weigh every part as it arrives and enter it in `mule/mass.py`: the tilt margin is only 0.3–0.8°.
- Every FSAE rule is a hard requirement. A design change must keep all automated checks passing, and `mule/docs/RULES_MATRIX.md` lists the build/inspection items to tick off.
- Every design change: edit the code, run `python report.py` in `mule/`, add a line to `mule/docs/PROJECT_LOG.md`, then commit and push (GitHub re-runs every check).
- A day's work goes into `WORKDONE.md` as a short summary; the detail stays in `PROJECT_LOG.md`.
- No MATLAB needed: everything runs in Python (see the README quick start for the setup).
- New Fusion uploads go in `adi laptop files > Nittany Motorsports` as the next version (`NM26_Assembly_v5`, …); move the old one out.
