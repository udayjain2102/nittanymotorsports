# NM26 mule: phased budget

Goal: the best car we can drive for the least cash, funded in small steps. Each phase is a separate funding request
of about **$2,500 or less**. Each one ends with something you can show (a frame, a rolling chassis, a running car), and
the design already allows every later upgrade. Prices are estimates for late 2026: check them before each request.
Where a price was looked up, the source is listed at the bottom.

## Summary

| Phase | What you get | Request | Test it passes (TEST_PLAN) |
|---|---|---|---|
| 0. Plan and mock-up | Full-size plywood/conduit buck; drivers fitted; parts donations lined up | **$100–200** | T4.3 templates and egress on the buck |
| 1. Frame | Welded 4130 frame on the jig | **$1,350–2,300** (tube re-priced 1 Oct 2026) | T1: weight, twist stiffness, weld check |
| 2. Rolling chassis | Suspension, steering, uprights, wheels and tyres: it rolls and steers | **$1,800–2,500** | T2: travel, camber, bump steer, steering |
| 3. Engine and drive | Engine, chain drive, spool, CV shafts, fuel | **$1,300–1,900** (cheap engine) or $2,600–4,000 (used 450) | T5.1 gearing |
| 4. Brakes, safety, electrics | Brakes, harness, seat, crash foam, shutdown circuit: **it drives** | **$1,800–2,600** | T3, T4, T5, T6 |
| **Total to a driving car** | | **about $7,700–11,600** with a used 450 at list prices (the kit engine was ruled out: it does not fit the bay, see Phase 3). `JUGAAD_PLAN.md` gets this to $6,200–10,700, or $4,000–6,000 with a donated engine and sponsored tube | |
| 5. Upgrades (any order, later) | 450 engine, Kaz rack, rear wing + DRS, new tyres, data logging | $300–3,000 each | T5.5, T7 |

The old one-shot estimate was $9–15k. The savings come from: used wheels, tyres and shocks,
fabricated steel uprights instead of machined aluminium, a cheaper rack first, and the wing deferred.

## Phase 0: plan and mock-up ($100–200)
- Build the buck (BUILD_PLAN §2m) from plywood, 2×4s and ¾″ conduit. Fit the tallest and smallest drivers, check
  the T.1.1/T.1.2 templates and a 5 s exit. **Fixes to geometry are free now and expensive after welding.**
- Line up free and cheap parts before spending:
  - ask FSAE teams nearby for used 13″ wheels, used slicks (teams replace tyres long before they're worn out),
    shocks, rod ends and uprights;
  - ask about material and part sponsorship (Keizer ran a sponsorship program for FSAE teams);
  - Hoosier reportedly discounts FSAE tyres; ask before buying.
- Get the brake pressure ratings in writing (proof rating covering 267 bar at 2000 N) before Phase 4 parts are chosen.

## Phase 1: frame ($1,350–2,300)
| Item | Est. $ |
|---|---|
| 4130 tube: 1.5/1.25/1.0 in sizes per `fab/tube_order_list.csv` + 25 % (9 × 20 ft sticks, `quote/material_list.csv`) | 1,000–1,700 + freight (re-priced 1 Oct 2026, see `JUGAAD_PLAN.md`; was 700–1,000) |
| Tabs, plate, anti-intrusion plate | 150 |
| TIG filler, notcher hole saws, jig lumber/steel | 200–300 |
| Bend service for the two hoops (if the school has no bender) | 0–150 |

Deliverable: the frame on its wheels-off stand, T1 twist test (predicted 2422 N·m/deg FEA, ≥ 1000 measured). This is the strongest thing
to show the next approver.

## Phase 2: rolling chassis ($1,800–2,500)
| Item | Cheap choice | Est. $ | Upgrade later |
|---|---|---|---|
| A-arms, tie rods, pushrods | 4130 tube, rod ends, ball joints | 500–700 | — |
| Shocks ×4 | **Used** 230×65 MTB coil shocks, springs ~250 front / ~215 rear lb/in | 300–600 | New/tunable dampers |
| Rockers ×4 | ¼″ steel plate, cut and drilled in-house | 60–120 | Machined aluminium |
| Uprights, hubs ×4 | **Fabricated steel uprights** (plate + tube, welded in the jig) instead of machined 7075; hubs turned from 4140; SKF 6209 bearings | 400–700 | Machined 7075 uprights |
| Wheels ×4 | **Used** 13″ FSAE wheels (new Keizer 13″ FSAE wheels list at about $175–375 each) | 0–700 | New wheels |
| Tyres ×4 | **Used** 20.5×7-13 slicks from another team | 0–300 | New Hoosiers |
| Steering | Cheapest rack that fits: 25–35 mm travel each side, re-check the ratio in `sideview.py`; column, 2 U-joints, quick release | 200–350 | Kaz FSAE rack ($850) |

The fabricated uprights must be re-checked in `uprights.py` (swap the material and section) before cutting.

## Phase 3: engine and drive ($1,300–1,900 cheap / $2,600–4,000 used 450)
**Option A, cheap kit engine (ruled out 2026-09-30: it does not fit the engine bay, see below; kept for the record):** a 13 hp, 420 cc
single-cylinder kit engine (about $380 new) with a go-kart CVT rated for 13 hp or more. The common Comet 30-series kits are rated for only 3–8 hp, so check the rating. Air-cooled,
pull or electric start, no gearbox, no radiator, no ECU. Point-mass estimate in our car: **75 m in about 6.9 s
(450 single: 4.5 s), autocross about 12 % slower**, because autocross is mostly grip-limited. Good for learning to drive
and tune the chassis.

| Item | Est. $ |
|---|---|
| 420 cc kit engine + CVT | 700–900 |
| Chain, sprockets, spool, eccentric carriers (reused later) | 400–600 |
| CV half-shafts (used ATV/UTV) | 150–300 |
| Small fuel tank, lines, throttle cable | 60–120 |

**Option B, used 450 now:** a used running 450 engine is about $1,500–2,800 (a new Honda crate engine is
listed at about $2,800; complete used bikes are $3,500+). Add cooling, exhaust and wiring: $2,600–4,000 in total.

Either way, the frame keeps the 450 engine bay and mount nodes. **Update 2026-09-30:** the adapter-plate check
(`python powertrain.py`, Option A) shows that the Predator 420 + CVT does **not** fit that bay at its listed size: it is too
tall for the space under the fuel cell, and too long or too wide once the CVT is added. Unless a measured bare engine is
smaller, Option A needs the fuel cell moved, so Option B is now the recommendation. See `PARTS_LIST.md`.
**Before buying**, the chosen engine goes into `powertrain.py` and `report.py` must pass: mounts, chain line, gearing and launch load.

## Phase 4: brakes, safety, electrics: first drive ($1,800–2,600)
| Item | Est. $ | Note |
|---|---|---|
| Calipers ×4 | 500–800 | Wilwood GP200 lists at about $280 each; PS-1s for the rear are cheaper. Used calipers are fine if rebuilt. |
| Master cylinders ×2, reservoirs, balance bar | 250–450 | Only parts with a written proof rating ≥ 267 bar (T.3.2.2) |
| Rotors, lines, fittings, fluid, BOTS, brake light | 250–400 | |
| Pedal box (machined/fabricated in-house) | 80–150 | |
| 5-point SFI harness | 250–400 | Buy new: never used harnesses |
| Seat (foam-moulded), head restraint, padding | 100–250 | |
| Standard foam impact attenuator, AIP | 100–200 | |
| Battery, master switch, E-stop, inertia switch, relay, wire, fuses | 250–350 | Per `shutdown.py` |
| Fire extinguishers ×2, firewall, belly pan sheet | 250–350 | |

Deliverable: **the car drives.** Run TEST_PLAN stages 3–6.

## Phase 5: upgrades (each its own small request, in this order)
1. **Used 450 engine** (Option B above) if Phase 3 used the kit engine: biggest performance gain.
2. **New tyres**: grip is worth ~2.4 s per autocross lap per 0.1 of grip (`lapsim.py`), far more than anything else.
3. **Kaz FSAE rack** ($850): faster steering, 178° lock-to-lock.
4. **Rear wing + DRS** ($600–1,200): about −0.62 s per autocross lap (assumed coefficients). It adds 7.4 kg high up, so re-check the tilt test.
5. Data logging (GPS + accelerometer + shock pots): turns the test plan into measured numbers.

## Price sources (looked up 2026-09-30; verify before ordering)
- 13 hp 420 cc engine, about $380: [Harbor Freight](https://www.harborfreight.com/13-hp-420cc-ohv-horizontal-shaft-gas-engine-epa-60340.html)
- Honda CRF450R crate engine, about $2,800: [oemdirtbikeparts.com](https://oemdirtbikeparts.com/product/dirt-bike-engine-for-sale-complete-crate-motor-new-oem/honda-2023-crf450r/); used CRF450X bikes $3,500+: [MotoHunt](https://motohunt.com/motorcycles-for-sale/Used/Honda-CRF450X)
- Comet 30-series CVT rated for 3–8 hp: [Go Kart Supply](https://www.gokartsupply.com/asymapp.htm)
- Wilwood GP200 caliper, about $282: [RaceChoice](https://racechoice.com/wilwood-120-12178-gp200-billet-caliper/)
- Keizer 13″ FSAE wheels, $175–375 each: [Keizer](https://keizerwheels.com/product-category/fsae/13-fsae/)
- Kaz FSAE rack, $850: [Kaz Technologies](https://www.kaztechnologies.com/steering-rack)
