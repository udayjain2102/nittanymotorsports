# What's next

In order. Tick them off here as they're done. The costs come from [`mule/docs/BUDGET_PLAN.md`](mule/docs/BUDGET_PLAN.md).

## This week (no money needed)
- [ ] Email Wilwood (GP200, PS-1 calipers), Tilton (78-series master cylinders) and the hose supplier for their **maximum pressure ratings in writing**. We need at least 296 bar (4,290 psi).
- [ ] Decide the engine for funding step 3: **13 hp kit engine + CVT first** (cheapest, ~$700–900) or a **used 450** now (~$1,500–2,800).
- [ ] Ask nearby FSAE teams for used 13″ wheels, slicks, MTB coil shocks, rod ends and uprights.
- [ ] Ask Keizer and Hoosier about FSAE sponsorship or discounts.
- [ ] Submit the funding request for **step 0 ($100–200)** and **step 1 ($1,100–1,600)**.

## Step 0: mock-up ($100–200)
- [ ] Build the plywood/conduit buck (`mule/docs/BUILD_PLAN.md` §2m).
- [ ] Fit the tallest and the smallest driver; check the T.1.1/T.1.2 templates; time a 5 s exit.
- [ ] Fix anything that fails in `mule/mule.py` **before** ordering tube, and re-run `python report.py`.

## Step 1: frame ($1,100–1,600)
- [ ] Order 4130 tube from `mule/fab/cutlist.csv` (+25 %), plus tabs, plate and filler.
- [ ] Build the jig from `mule/fab/nodes.csv`; cut and cope from `mule/fab/cut_sheet.csv`; bend hoops from `mule/fab/hoop_bends.csv`.
- [ ] Weld the frame. Run TEST_PLAN stage 1 (weight, twist stiffness: predicted 2138 N·m/deg).
- [ ] Take photos and results to the next funding request.

## Steps 2–4: to a driving car
- [ ] Step 2, rolling chassis ($1,800–2,500): suspension, used shocks, fabricated steel uprights (re-check in `uprights.py`), used wheels and tyres, cheap rack. Then TEST_PLAN stage 2.
- [ ] Step 3, engine and drive ($1,300–1,900 kit engine): enter the chosen engine in `powertrain.py` and make `report.py` pass **before** buying the mounts and chain.
- [ ] Step 4, brakes, safety and electrics ($1,800–2,600): buy only brake parts rated for 296 bar or more; buy the harness new. Then TEST_PLAN stages 3–6. **First drive.**

## After it drives
- [ ] Weigh the car and enter real masses in `mule/mass.py`: the tilt margin is only 0.9°.
- [ ] TEST_PLAN stage 7 (skidpad); put the measured grip back into `lapsim.py`.
- [ ] Upgrades, one request each: used 450 engine → new tyres → Kaz rack → rear wing + DRS → data logging.

## Keeping the repo useful
- Every design change: edit the code, run `python report.py` in `mule/`, add a line to `mule/docs/PROJECT_LOG.md`, then commit and push (GitHub re-runs every check).
- New Fusion uploads go in `adi laptop files > Nittany Motorsports` as the next version (`NM26_Assembly_v5`, …); move the old one out.
