# NM26 mule: jugaad plan (smallest budget that still passes every rule)

*Jugaad* (जुगाड़): get it done with what you can find, borrow, scrounge or make. Funding will be smaller than
[`BUDGET_PLAN.md`](BUDGET_PLAN.md) assumes ($7.4–10.9k), so this is the cheapest route to a driving mule. The car's
design does not change except where a line says so, and **every FSAE 2026 rule stays a hard requirement**: jugaad is
for *where parts come from*, never for safety.

Prices are estimates (1 Oct 2026), **not looked up**: check each one before a funding request.

## The four big levers
| Lever | Saves (est.) | Status |
|---|---|---|
| **Donor bike:** buy a whole crashed or non-running CRF450R 2018+ instead of an engine plus parts. Use the engine, ECU, wiring, radiator, fuel pump, throttle body, exhaust, chain and sprockets; sell the forks, shock, wheels, plastics and frame to get money back. | $1,000–1,500 | Plan. Check the engine turns over and the title/VIN is clean before buying. |
| **1020 DOM tube, MIG-welded by the team** instead of 4130 + TIG. | $250–400 on tube, plus easier welding | **Checked:** frame 45.3 kg (+1.0 kg), every check passes (branch `jugaad-1020`, PROJECT_LOG). Needs a weld test coupon and an advisor's OK on the criterion. |
| **Ask other FSAE teams** for used wheels, slicks, rod ends, calipers, racks, pedal boxes, seats: teams retire these every year. | $500–1,500 | Plan (already in WHATS_NEXT). |
| **Make, don't buy:** steel uprights, rockers, spool carriers, pedal box, seat (foam + fibreglass), jig (scrap steel/plywood), buck. | $300–700 | Already the plan for most of these. |

## Budget, jugaad version
| Step | What | Jugaad source | Est. $ |
|---|---|---|---|
| 0. Buck | Plywood/conduit mock-up | Scrap wood, borrowed conduit | 0–50 |
| 1. Frame | 1020 DOM tube (`fab/tube_order_list.csv` + 25 %), tabs, MIG wire/gas, jig | Local steel supplier; tabs from scrap plate; school MIG welder; hoops bent by a muffler/exhaust shop | 600–1,100 |
| 2. Rolling chassis | A-arms + rod ends, shocks, uprights, wheels, tyres, steering | Arms in-house; used MTB shocks; steel uprights; used FSAE wheels and slicks from teams; used rack from a team or junkyard | 800–2,200 |
| 3. Engine and drive | Engine and everything around it, spool, CV shafts, fuel | Donor CRF450R (net of resale); used ATV CV shafts; spool carriers made in-house | 1,300–2,600 |
| 4. Brakes, safety, electrics | Calipers, master cylinders, lines, harness, seat, impact attenuator, shutdown parts, extinguishers | Used calipers rebuilt; **rated** master cylinders; new harness; DIY seat | 1,350–2,400 |
| **Total to a driving car** | | | **about $4,000–8,300** (plan: about $7.4–10.9k) |

The wide range is mostly the donor bike and how much other teams give. Each step is still its own small request.

## Never jugaad (buy new, rated, or inspected)
- **Harness:** new, in-date, SFI/FIA rated (T.2). Helmet and driver gear: rated.
- **Roll hoops and welds:** rule tube sizes; weld test coupons cut and bent before the frame; advisor review of the
  welded-1020 criterion (294/394 MPa) before tube is ordered.
- **Brake hydraulics:** every master cylinder, caliper, hose and fitting needs a **written pressure rating** above the
  2000 N test pressure (296 bar now; 237 bar at pedal ratio 4.0, which raises lock-up force to 709 N). Donor-bike or
  used brake parts are fine **only** with that rating.
- **Impact attenuator:** the standard FSAE foam unit; anti-intrusion plate to spec.
- **Shutdown circuit:** master switch, E-stop, BOTS, inertia switch must meet the rules (`shutdown.py`).
- **Fuel system:** no leaks, rule-compliant lines and tank.

## Weight cost of jugaad
1020 frame +1.0 kg. Steel uprights instead of 7075 add weight at each corner (re-check in `uprights.py` and
`mass.py`). The tilt margin is thin (60.8°, 60.3° if every estimate errs the same way), so **weigh every part** and
re-run `mass.py` as it arrives.

## Next
1. Funding limit → pick the steps it covers; this table becomes the request list.
2. Price the four levers for real (donor bike listings, local 1020 DOM per foot, team giveaways).
3. If 1020 is chosen: weld coupons, advisor review, then merge `jugaad-1020` the usual way (snapshot first).
