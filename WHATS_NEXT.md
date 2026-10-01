# What's next

In order. Tick them off here as they're done. The costs come from [`mule/docs/BUDGET_PLAN.md`](mule/docs/BUDGET_PLAN.md), the parts from [`mule/docs/PARTS_LIST.md`](mule/docs/PARTS_LIST.md).
Last updated 2026-09-30. Engine chosen (CRF450R 2018+); total to a driving car is now about **$7,400–10,900**.

## This week (no money needed)
- [ ] Ask nearby FSAE teams for used 13″ wheels, slicks, MTB coil shocks, rod ends and uprights.
- [ ] Ask Keizer and Hoosier about FSAE sponsorship or discounts.
- [ ] Submit the funding request for **step 0 ($100–200)** and **step 1 ($1,100–1,600)**.
- [ ] Borrow or find a CRF450R 2018+ to measure (a dealer, a team member's bike or another FSAE team). The frame can't be finalised without its mount points.

## Frame quote
- [ ] Send the shop the whole `mule/quote/` folder (frame STEP, material list, shop data, cover note) for a preliminary quote, in 4130 and 1020 DOM.
- [ ] Frame topology redesign toward ~33 kg (now 45.3 kg): pickups on triangulated nodes, closed front ring that passes T.1.2, braced shoulder bar. Re-run `python quote_package.py` after.

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
- [ ] Weld the frame. Run TEST_PLAN stage 1 (weight, twist stiffness: predicted 1886 N·m/deg).
- [ ] Take photos and results to the next funding request.

## Steps 2–4: to a driving car
- [ ] Step 2, rolling chassis ($1,800–2,500): suspension, used shocks, fabricated steel uprights (re-check in `uprights.py`), used wheels and tyres, cheap rack. Then TEST_PLAN stage 2.
- [ ] Step 3, engine and drive ($2,600–4,000 with a used 450). This is over the ~$2,500 per request, so split it: **3a** the engine ($1,500–2,800, a running 2018+ CRF450R with electric start), then **3b** chain, sprockets, spool, CV shafts, cooling, exhaust and fuel. Check the engine against the measured numbers before 3b.
- [ ] Before step 4: email Wilwood (GP200, PS-1 calipers), Tilton (78-series master cylinders) and the hose supplier for their **maximum pressure ratings in writing**. We need at least 296 bar (4,290 psi). *(On hold for now.)*
- [ ] Step 4, brakes, safety and electrics ($1,800–2,600): buy only brake parts rated for 296 bar or more; buy the harness new. Then TEST_PLAN stages 3–6. **First drive.**

## After it drives
- [ ] Weigh the car and enter real masses in `mule/mass.py`: the tilt margin is only 0.9°.
- [ ] TEST_PLAN stage 7 (skidpad); put the measured grip back into `lapsim.py`.
- [ ] Upgrades, one request each: new tyres → Kaz rack → rear wing + DRS → data logging.

## Keeping the repo useful
- Every design change: edit the code, run `python report.py` in `mule/`, add a line to `mule/docs/PROJECT_LOG.md`, then commit and push (GitHub re-runs every check).
- A day's work goes into `WORKDONE.md` as a short summary; the detail stays in `PROJECT_LOG.md`.
- No MATLAB needed: everything runs in Python (see the README quick start for the setup).
- New Fusion uploads go in `adi laptop files > Nittany Motorsports` as the next version (`NM26_Assembly_v5`, …); move the old one out.
