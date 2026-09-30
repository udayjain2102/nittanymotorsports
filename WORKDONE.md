# Work done: NM26 FSAE-lite mule

A record of everything Claude did on this project, from 27 to 30 September 2026. The step-by-step engineering log, with
every method, result and error, is [`mule/docs/PROJECT_LOG.md`](mule/docs/PROJECT_LOG.md). This page is the overview.

**Starting point:** the concept CAD (`NM26_FSAE_Concept.step`) and the 2026 FSAE rules PDF.
**Result:** a complete, rules-checked design for a drivable test car (a "mule"), all generated from Python code:
- 166 automated design checks and 80 automated tests, all passing, also run by GitHub on every push;
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
| Powertrain | `powertrain.py` | Gearing, chain, spool, CV shafts, engine mounts, launch load, toe-link/half-shaft clearance | Launch FoS 1.23; engine values are placeholders until one is chosen |
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
- `BUDGET_PLAN.md`: five funding steps of about $2,500 or less, about $6–9k to a driving car, with an upgrade path and price sources.
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

## 7. Still open (needs people, parts or suppliers)

1. **Brake pressure ratings in writing** from Wilwood, Tilton and the hose supplier: 296 bar needed, 300 bar assumed.
2. **Engine choice:** a 13 hp kit engine + CVT first (cheapest), or a used 450 now. Then measure it into `powertrain.py`.
3. **Build the buck** and fit the drivers before cutting tube.
4. **Weigh parts as they arrive**: the tilt margin is 0.9°.
5. **Run TEST_PLAN stages 1–7** on the real car and put the measured numbers back into the code, especially the wing's aero coefficients.
