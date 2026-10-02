# NM26 mule: parts list (candidates)

The bought parts the design is built around, and the options still open. The full bill of materials with quantities
is in `BUILD_PLAN.md` §4, and the costs per funding step are in `BUDGET_PLAN.md`. Prices were looked up on 2026-09-30:
check them before ordering. **Status:** *chosen* = the code is sized for it; *candidate* = still to decide.

## Engine (decide before ordering frame tube)

The frame is built around a 450 cc single (`powertrain.py` envelope 320 × 340 × 340 mm, mounts `em_fb`/`em_ft`/`em_rb`).
Whatever engine is chosen, measure it into `powertrain.py` and make `python report.py` pass before buying mounts and chain.

| Option | Power | Start | Price seen | Fits the 450 bay? | Notes |
|---|---|---|---|---|---|
| **Honda CRF450R 2018+** (used engine), **chosen** | ~53 hp, 48 N·m @ 7000 | electric | ~$2,800 new crate; used varies | yes (it is the design basis) | A common FSAE single-cylinder engine; lots of parts and service info. 2017 has kick start standard (electric start was an option kit): only buy a 2017 with the kit fitted |
| Honda CRF450R 2002–2017 (used engine) | ~45 hp | **kick only** | $1,500–1,600 (eBay, 2005/2007 running) | yes | Cheapest real option, but needs an electric-start conversion: nobody can kick-start from a seat |
| Honda CRF450X (used engine) | ~40 hp | electric | used bikes $3,500+ | yes | Wider-ratio enduro gearbox, softer tune: easy to drive |
| Yamaha YZ450F 2018+ (used engine) | ~50 hp | electric | ~$4,300 (2022, eBay) | check: rearward-tilted cylinder | Measure the envelope; intake faces forward |
| KTM / Husqvarna 450 SX-F | ~55 hp | electric | check | check | Light, but parts cost more |
| Predator 420 + Comet 40-series CVT (kit) | 13 hp | pull / electric kit | ~$380 engine + CVT | **no** (`python powertrain.py`, Option A) | By its listed size it is too tall for the space under the fuel cell (434 vs 388 mm) and too long or too wide once the CVT is added. The listed size includes the fuel tank, muffler and air filter, so measure the bare engine before ruling it out |

**Chosen 2026-09-30: Honda CRF450R 2018+.** From the 2017–18 service manual (now in `powertrain.py`): primary 2.357 (66/28), gears
2.133 / 1.706 / 1.421 / 1.211 / 1.043, stock sprockets 13/49, dry mass 30.9 kg. Still needed from a real engine: mount points,
countershaft position and envelope; rev limit not found yet.

## Drivetrain (chosen)

| Part | Choice | Source / check |
|---|---|---|
| Chain | DID 520VO O-ring, 60 links, 35.6 kN | `powertrain.py` |
| Sprockets | 13 T front, 50 T rear (520 pitch) | `powertrain.py` |
| Spool | Steel spool, eccentric carriers ±20 mm | `powertrain.py`, `cad_parts.py` |
| Half-shafts | Used ATV/UTV tripod CV shafts (≤22° and ≤20 mm plunge needed; design uses 10° and 4.5 mm) | `powertrain.py` |
| CVT (kit option only) | Comet 40-series TAV, rated 8–18 hp, 1″ crank bore. The 30-series is only rated 3–8 hp | [GoPowerSports](https://www.gopowersports.com/40-series-torque-converter-kit-bolt-on-8hp-18hp/), [Go Kart Supply](https://www.gokartsupply.com/4044seri.htm) |

## Chassis (chosen)

| Part | Choice | Source / check |
|---|---|---|
| Frame tube | 4130: 1.25×0.095, 1.0×0.095, 1.0×0.065, 1.0×0.049 in | `fab/tube_order_list.csv` |
| Wheel bearings | SKF 6209-2RS1 (45×85×19 mm) | `uprights.py` |
| Hubs | 4140 Q&T, turned in-house | `uprights.py` |
| Uprights | Fabricated steel first, machined 7075 later | `uprights.py` (re-check steel before cutting) |
| Shocks | 230×65 mm MTB coil shocks, springs ~243 lb/in front / ~215 lb/in rear; used is fine | `springs.py` |
| Rod ends / ball joints | Static rating ≥ 2× the joint loads printed by `python uprights.py` | `uprights.py` |
| Wheels | 13″ FSAE; used first, or Keizer ($175–375 each) | [Keizer](https://keizerwheels.com/product-category/fsae/13-fsae/) |
| Tyres | 20.5×7.0-13 slicks; used first, then new Hoosiers (ask about the FSAE discount) | `mule.py` |
| Steering rack | Cheapest rack with 25–35 mm travel each side first; Kaz FSAE rack ($850) later | `steering.py`, [Kaz](https://www.kaztechnologies.com/steering-rack) |

## Brakes (chosen, pending pressure ratings)

Every hydraulic part needs a written proof rating covering **267 bar** (the 2000 N pedal test, T.3.2.2); Wilwood's published maximum operating pressure is 2000 psi (138 bar), and lock-up needs 80 bar.

| Part | Choice | Source / check |
|---|---|---|
| Front calipers | Wilwood GP200, 2 × 1.25 in pistons (~$282 each) | `brakes.py`, [RaceChoice](https://racechoice.com/wilwood-120-12178-gp200-billet-caliper/) |
| Rear calipers | Wilwood PS-1, 2 × 1.00 in pistons | `brakes.py` |
| Master cylinders | Tilton 78-625 (front), 78-750 (rear), with balance bar | `brakes.py` |
| Rotors | 200 mm OD, made in-house or bought | `uprights.py` |

## Safety and electrics (chosen)

| Part | Choice | Note |
|---|---|---|
| Harness | 5-point SFI, **new** | `harness.py`; never buy used |
| Electrics | Battery, master switch ≥ 100 A, E-stop, inertia switch, BOTS, kill relay ≥ 30 A, fuses | `shutdown.py` has every rating and wire gauge |
| Crash | Standard foam impact attenuator + anti-intrusion plate | `BUILD_PLAN.md` §3 |
| Fire extinguishers | 2 | `BUDGET_PLAN.md` phase 4 |

## Price sources for this page
- Predator 420 size and torque: [Harbor Freight](https://www.harborfreight.com/13-hp-420cc-ohv-horizontal-shaft-gas-engine-epa-60340.html), [Predator](https://predatorbrand.com/420cc-predator-engine/)
- CRF450R power, torque: [UltimateSpecs](https://www.ultimatespecs.com/motorcycles-specs/honda/honda-crf450r-2017); electric start standard from 2018: [Ultimate Motorcycling](https://ultimatemotorcycling.com/2017/05/10/2018-honda-crf450r-unveiled-now-electric-start/); stock sprockets 13/49: [Vital MX](https://www.vitalmx.com/forums/Tech-Help-Race-Shop,42/CRF-2017-drive-and-gear-ratios,1314714)
- Used 450 engines: [eBay CRF450R engines](https://www.ebay.com/b/Motorcycle-Scooter-Complete-Engines-for-Honda-CRF450R/171108/bn_1398521), [eBay YZ450F engines](https://www.ebay.com/b/Complete-Engines-for-Yamaha-YZ450F/171108/bn_21454774)
- Others as listed in `BUDGET_PLAN.md`.
