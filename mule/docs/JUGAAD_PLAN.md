# NM26 mule: jugaad plan (smallest budget that still passes every rule)

*Jugaad* (जुगाड़): get it done with what you can find, borrow, scrounge or make. Funding will be smaller than
[`BUDGET_PLAN.md`](BUDGET_PLAN.md) assumes ($7.4–10.9k), so this is the cheapest route to a driving mule. The car's
design does not change except where a line says so, and **every FSAE 2026 rule stays a hard requirement**: jugaad is
for *where parts come from*, never for safety.

Prices: the engine and frame tube were looked up on 1 Oct 2026 (sources at the bottom); the rest are estimates. Check each before a funding request.

**What the price check showed:** the original budget was already lean. With real prices the cheap version costs about
**$6,200–10,700 if we pay for everything**, and drops to roughly **$4,000–6,000 only if the engine and tube are donated
or sponsored**. Donations and sponsorship are the real jugaad lever, not cheaper parts.

## The four big levers
| Lever | Saves (est.) | Status |
|---|---|---|
| **Engine: donated, borrowed or salvage.** Used running CRF450R engines list at about $2,500–3,100; whole running 2019–20 bikes $4,000–7,000; CRF450X is not cheaper. Only a crashed/salvage bike (insurance auctions, local dealers) or a donated engine beats $2,500. Kick-start-only engines (2002–2016) are cheap (~$1,500) but can't be started from the seat. | $0–2,500 if donated/salvaged | **Biggest lever.** Ask dealers, local riders, and the school's alumni for a crashed 2018+ bike. |
| **Frame tube: sponsored or local.** Our 9 sticks (20 ft) cost about $1,000–1,700 at listed prices, plus truck freight for 20 ft lengths. **1020 DOM is not cheaper than 4130** ($6.80–9.36/ft vs $5.35–9.50/ft listed); 1020's only advantage is easy MIG welding by the team (frame 45.3 kg, +1.0 kg, checked on branch `jugaad-1020`). | $1,000–1,900 if a steel distributor sponsors it; freight saved by buying locally | Ask local steel distributors and Keizer-type sponsors; pick the steel by **who can weld it**, not by price. |
| **Ask other FSAE teams** for used wheels, slicks, rod ends, calipers, racks, pedal boxes, seats: teams retire these every year. | $500–1,500 | Plan (already in WHATS_NEXT). |
| **Make, don't buy:** steel uprights, rockers, spool carriers, pedal box, seat (foam + fibreglass), jig (scrap steel/plywood), buck. | $300–700 | Already the plan for most of these. |

## Budget, jugaad version
| Step | What | Jugaad source | Est. $ |
|---|---|---|---|
| 0. Buck | Plywood/conduit mock-up | Scrap wood, borrowed conduit | 0–50 |
| 1. Frame | 9 sticks of tube (`quote/material_list.csv`), tabs, filler/gas, jig | Sponsored or local tube; tabs from scrap plate; school welder; hoops bent by a muffler/exhaust shop | 1,100–2,100 (≈ 100–400 if tube is sponsored) |
| 2. Rolling chassis | A-arms + rod ends, shocks, uprights, wheels, tyres, steering | Arms in-house; used MTB shocks; steel uprights; used FSAE wheels and slicks from teams; used rack from a team or junkyard | 800–2,200 |
| 3. Engine and drive | Engine, cooling, exhaust, wiring, chain, spool, CV shafts, fuel | Used CRF450R 2018+ engine ($2,500–3,100) or a donated/salvage one; used ATV CV shafts; spool carriers made in-house | 2,900–3,900 (≈ 400–1,400 if the engine is donated) |
| 4. Brakes, safety, electrics | Calipers, master cylinders, lines, harness, seat, impact attenuator, shutdown parts, extinguishers | Used calipers rebuilt; **rated** master cylinders; new harness; DIY seat | 1,350–2,400 |
| **Total to a driving car** | | | **about $6,200–10,700** paying for everything; **about $4,000–6,000** with a donated engine and sponsored tube (plan: $7.4–10.9k) |

The wide range is mostly the engine, the tube and how much other teams give. Each step is still its own small request.

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
2. Before applying: send sponsorship asks (engine, tube, wheels/tyres) and ask nearby teams; every yes comes straight off the request.
3. Steel: 4130 if someone can TIG it (lighter, same price); 1020 if the team MIGs it (weld coupons, advisor review, then merge `jugaad-1020`, snapshot first).

## Price sources (looked up 1 Oct 2026)
- Used CRF450R engines $2,550–3,060, 2019+ bottom end $1,615: [eBay CRF450R complete engines](https://www.ebay.com/b/Motorcycle-Scooter-Complete-Engines-for-Honda-CRF450R/171108/bn_1398521)
- Used 2019–20 CRF450R bikes about $4,000–7,000: [Cycle Trader](https://www.cycletrader.com/Used-Honda-Crf-450r/motorcycles-for-sale?make=Honda%7C2316874&model=CRF%7C764948699&trim=450R%7C3946&condition=U), [KBB 2019](https://www.kbb.com/motorcycles/honda/crf450r/2019/)
- CRF450X used bikes $3,495–4,500, used engine $4,750: [MotoHunt](https://motohunt.com/motorcycles-for-sale/Used/Honda-CRF450X), [eBay CRF450X](https://www.ebay.com/b/Engines-Parts-for-Honda-CRF450X/171107/bn_21602907)
- 1020 DOM 1″ × 0.065″: $6.80+ ([Metals 4 U](https://www.metals4uonline.com/1-000-od-x-065-wall-steel-round-tube-dom-1020/)), $9.36/ft ([All Metals](https://allmetalsinc.com/products/steel-round-tube-1-x-065-grade-dom))
- 4130 1″ × 0.065″: $5.35/ft ([Aircraft Spruce](https://www.aircraftspruce.com/catalog/mepages/4130tubing_un1.php)), $9.19/ft ([Rhodes Race Cars](https://www.rhodesracecars.com/1-OD-065-Wall--4130-Chromoly-Tubing_p_11706.html))
