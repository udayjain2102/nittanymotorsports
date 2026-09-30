# Work done: NM26 FSAE-lite mule

A record of everything Claude did on this project, from 27 to 30 September 2026 (30 September's work is summarised in section 7). The step-by-step engineering log, with
every method, result and error, is [`mule/docs/PROJECT_LOG.md`](mule/docs/PROJECT_LOG.md). This page is the overview.

**Starting point:** the concept CAD (`NM26_FSAE_Concept.step`) and the 2026 FSAE rules PDF.
**Result:** a complete, rules-checked design for a drivable test car (a "mule"), all generated from Python code:
- 166 automated design checks and 82 automated tests, all passing, also run by GitHub on every push;
- CAD in two levels of detail;
- shop data to build the frame;
- a physical test plan, a build plan, a bill of materials and a phased budget;
- the whole project on GitHub.

---

## 1. Design, by system

Every system is a Python script in `mule/` that computes the design and checks its own targets.

| System | Script | What was done | Key result |
|---|---|---|---|
| Concept review | — | Critiqued the concept STEP against the rules | 7 problems found (wheelbase too short, missing parts, etc.) |
| Frame layout and rules | `mule.py` | Parametric frame (146 tubes) built around the 95th-percentile driver template; 27 FSAE rule checks | 1750 mm wheelbase, 1220 mm tracks, 50.1 kg frame, 81 pieces |
| Frame strength | `fea.py` | 3D beam FEA with inertia relief; roll-hoop loads from FSAE AF4.1/AF4.2, worst of 4 directions | Main hoop FoS 1.28, front 1.36; torsion 2138 N·m/deg |
| Suspension kinematics | `suspension.py`, `sideview.py`, `roll.py` | Double wishbones front and rear; roll centres, camber, caster, anti-dive/squat, roll gradient, static camber, jacking, handling balance | RC 37/52 mm, caster 4.6°, scrub 38 mm, camber −2.5/−2.0°, LLTD 49.6 % front (mild understeer) |
| Loads into the frame | `loads.py`, `compliance.py` | Six-link upright statics for 10 load cases; link buckling; compliance steer | Worst frame FoS 1.26; toe change 0.10°/0.18° at 1.5 g |
| Springs, rockers, shocks | `springs.py`, `rocker.py` | Pushrod + bell-crank layout, 230×65 MTB coil shocks | Motion ratio 0.72/0.75, 3.0/2.6 Hz ride, ~243/215 lb/in springs |
| Steering | `steering.py`, `sideview.py` | Bump steer front and rear, Ackermann, 3D tyre clearance at lock, ratio, effort | Kaz rack, 4.1:1, 178° lock-to-lock, 95 N at the rim, rear bump steer 0.00° |
| Uprights and hubs | `uprights.py` | Bearing life, hub shaft, upright arms, wheel studs, rotor packaging | SKF 6209 bearings, 4140 hubs, 7075 uprights |
| Powertrain | `powertrain.py` | Gearing, chain, spool, CV shafts, engine mounts, launch load, toe-link/half-shaft clearance | Engine chosen: Honda CRF450R 2018+ (published 48 N·m torque); launch FoS 1.21. Gear ratios, size and mass are still generic |
| Brakes and pedal box | `brakes.py` | Caliper/MC sizing, balance bar, lock-up force, BOTS, 2000 N pedal test, rotor heat | Locks all four at 567 N; 296 bar at 2000 N (supplier ratings still needed) |
| Cockpit | `cockpit.py` | T.1.1 and T.1.2 templates swept through the whole model | Both pass (after moving the steering rack low and the front shocks) |
| Harness | `harness.py` | Belt angles, mounting tabs, 20 g crash load | Lap belt fixed from 15° to 55°; frame FoS 1.17 vs welded ultimate |
| Electrical | `shutdown.py` | 12 V shutdown circuit simulated as a netlist; wire and fuse sizing | Every shutdown device cuts ignition and fuel pump; 0.23 V drop |
| Mass and CG | `mass.py` | Item-by-item mass budget; tilt test | 296 kg with driver, CG 340 mm, tilt 60.9° (limit 60°) |
| Rear wing with DRS | `aero.py` | Two-element wing with a moving flap, inside rule T.7; mounts, oscillation, servo, fail-safe logic | 126 N at 60 km/h (assumed coefficients); mounts 159 Hz; flap closes on brake or power loss |
| Lap simulation | `lapsim.py` | Point-mass acceleration, skidpad, autocross; benchmark against FSAE Michigan 2025 results | 4.49 s / 5.17 s / 59.2 s (Michigan medians 4.62 / 5.52 / 55.7 s) |

## 2. Problems found and fixed along the way

These would have been expensive to discover after welding:
- **Roll hoops overstressed** (FoS < 1). Fixed with bracing and 1.25″ hoops.
- **Lap belt at 15°** (the rule needs 45–65°). Belt tabs moved under the hips.
- **Leg-room template (T.1.2) failed.** Fixed by moving the rack low under the shins and removing a cross tube.
- **Rear bump steer of 0.76° per 25 mm**, which would have made the car oversteer in corners. The rear toe link was re-aimed, giving 0.00°.
- **Handling balance:** 40 % of the load transfer was on the front with 45 % of the weight there (oversteer). Fixed by swapping the ride frequencies.
- **Wheel travel misread:** the design used ±50 mm, but rule V.3.1.1 asks for 50 mm total. Correcting it enabled better motion ratios.
- **Tilt test after adding the wing:** the margin fell to 0.25°, so the rear track was widened from 1180 to 1220 mm.
- **Engine decision came after the frame:** the plan chose the engine in step 3, but its mounts are welded in step 1. The engine choice now comes before the tube order.
- **Kit engine doesn't fit:** the Predator 420 + CVT is too tall and too long or wide for the 450 engine bay (see section 7).
- **GitHub checks failing on some runs:** the front rocker's geometry was being chosen by rounding (see section 7).
- Smaller issues: a backwards chain-line check, swapped Ackermann labels, a tube-coping order error, and tests that could never fail (removed).

## 3. Reviews against outside material

- **Kevin Hayward's design-review notes:**
  - closed scrub radius, motion ratio, lock-to-lock, static camber, roll-centre movement, compliance, lap simulation, Pugh matrices, buck plan and part numbering.
- **Reference papers:**
  - JCU 2020 rear suspension: added a solid-axle option to the design spec.
  - NAU 2025 suspension report: added the handling-balance check and the critical-fastener rule. Two of its rule limits are wrong for 2026.
  - Trinity 2020 final report: added a rear toe-link-to-drive-shaft clearance check.
- **Catalogue values checked online:** SKF bearings, DID chain, Kaz rack, FSAE hoop load case, FSAE Michigan 2025 results.
  - Wilwood and Tilton don't publish pressure ratings; ask them.

## 4. CAD

- **Simple model** (`mule/cad/simple/NM26_Mule.step`): every system in one colour, every part numbered `NM26-<system>-<nnn>`.
- **Detailed model** (`mule/cad/NM26_Assembly.step` + one STEP per part in `mule/cad/parts/`):
  - The "Go kart CAD assembly" Claude session built the detailed parts: treads, springs, CV boots, the 15-part engine and the brake-line and wiring routing.
  - This session:
    - made every part name unique and descriptive;
    - added a "contains" description to each part;
    - added the rear wing;
    - renamed the parts lists to match their STEP files.
- **Fusion 360:**
  - opened and checked each new model;
  - saved the current one to `adi laptop files > Nittany Motorsports > NM26_Assembly_v4`;
  - renamed every older version (v1, v2, simple v1–v3, concept) so the names say what they are.

## 5. Documents

In `mule/docs/`:
- `PDS.md`: 15 requirements with targets, results and how each is verified; design decisions; Pugh matrices; benchmark.
- `BUILD_PLAN.md`: design narrative per system, FSAE rules checklist, bill of materials, build order, buck plan.
- `TEST_PLAN.md`: 7 stages of physical tests with predicted values and pass criteria, based on the Trinity test-manual format.
- `BUDGET_PLAN.md`: five funding steps of about $2,500 or less, about $7.4–10.9k to a driving car with a used 450, with an upgrade path and price sources.
- `PARTS_LIST.md`: the parts the design uses, engine options with prices, and which script sizes each part.
- `PROJECT_LOG.md`: full chronological log.
- `REPORT.md`: generated list of every check and test.

Fabrication data in `mule/fab/`: cut sheet with cope angles, hoop bend programs, jig node coordinates, jig plan, cut list.

## 6. GitHub and tooling

- Created the repo contents at [udayjain2102/nittanymotorsports](https://github.com/udayjain2102/nittanymotorsports).
  - First pushed through the GitHub API, then through normal git once the Xcode licence was accepted.
- Made the repo easy to use:
  - README with a car picture, an "I just want to…" table, a quick start and a folder map;
  - `requirements.txt`;
  - `.gitattributes`, so generated files don't clutter diffs;
  - GitHub Actions, which run every design check and test on each push (passing).
- Organised the folders: `mule/docs/`, `mule/cad/`, `mule/cad/simple/`, `mule/fab/`, `mule/views/`, `mule/tests/`. Other teams' papers go in a local, git-ignored `references/`.
- Every file's contents are described in the root `README.md`.

## 7. 30 September: engine decision and GitHub fix

**Next steps decided.** From `WHATS_NEXT.md` and this file: do the free tasks first (supplier emails, asking other teams for used parts, funding requests for steps 0 and 1). The supplier emails are on hold for now. The engine had to be chosen before any frame tube is ordered, because the engine mounts are part of the frame.

**Kit engine checked, and it doesn't fit.** A new check in `powertrain.py` ("Option A", printed but not enforced) fits a Predator 420 kit engine and a Comet 40-series CVT on an adapter plate, using the 450's mounts. At the engine's listed size:

| Check | Engine | Space in the bay |
|---|---|---|
| Height under the fuel cell | 434 mm | 388 mm |
| Length, jackshaft to firewall | 351 mm | 330 mm |
| Width with the CVT, between the rear-ring tubes | 590 mm | 487 mm |

The CVT rating (8–18 hp) and the chain were fine. The listed size includes the fuel tank, muffler and air filter, so a bare engine would be smaller. Even so, making it fit would mean moving the fuel cell. A new test checks the fit function.

**Engine chosen: Honda CRF450R.** The user picked a 2017 or later model. Checking online showed that the 2017 has kick start as standard, with electric start only as an option kit; electric start became standard in 2018. The target is therefore a 2018 or later engine, or a 2017 that already has the kit.
- `powertrain.py` now uses the published torque, 48 N·m at 7000 rpm, instead of the 50 N·m placeholder. The acceleration prediction moves from 4.47 s to 4.49 s.
- The gear ratios, rev limit, size and mass are not published online. They are still generic until the service manual is in hand or an engine is measured.
- The budget to a driving car is now about $7,400–10,900 with a used 450.

**Parts list.** New `mule/docs/PARTS_LIST.md` covers:
- engine options: CRF450R old and new, CRF450X, YZ450F, KTM 450 and the Predator, with prices and whether each fits;
- every bought part the design is sized around: chain, sprockets, bearings, shocks, wheels, tyres, rack, brakes, harness and electrics.

**MATLAB isn't needed.** Everything runs in Python, and GitHub checks it on every push. MATLAB would only matter later, for logged data, for vehicle simulation in Simulink, or if the school requires it.

**GitHub checks fixed.** The frame-strength test had been failing on about half of the GitHub runs, with no code change between runs, and never on the laptop.
- *Cause:* running the check 8 times in parallel showed the failures only on certain server CPUs. On those machines, only the front load cases changed.
  - `rocker.py` picked the shock mounting point from two mirror-image solutions by "the smaller one". The two are exactly the same size, so the last digit of rounding decided which one was used.
  - On those CPUs it picked the other side, which gave a different front rocker. The frame safety factor then fell to 0.83 instead of 1.26.
- *Fix:* the side is now set explicitly for each axle, matching the design that was already validated, so no results changed. All 8 parallel runs then passed on every CPU type.
- *Also fixed:* the frame solver held the frame at three points that didn't stop it rotating. It now holds one point fully. Results are unchanged, and a new test catches the old version.
- `test_loads.py` now prints every load case if the frame check ever fails again.

**Tooling.** The Python environment with CadQuery had to be rebuilt in the session scratchpad; the old one was gone. The temporary debug branch on GitHub was deleted.

## 8. Still open (needs people, parts or suppliers)

1. **Brake pressure ratings in writing** from Wilwood, Tilton and the hose supplier: 296 bar needed, 300 bar assumed.
2. **CRF450R 2018+ data:** get the service manual (gear ratios, rev limit, mass) and measure an engine's mounts, output shaft and size into `ENGINE` in `powertrain.py` **before ordering tube**.
3. **Build the buck** and fit the drivers before cutting tube.
4. **Weigh parts as they arrive**: the tilt margin is 0.9°.
5. **Run TEST_PLAN stages 1–7** on the real car and put the measured numbers back into the code, especially the wing's aero coefficients.
