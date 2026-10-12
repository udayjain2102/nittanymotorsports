# Work done: NM26 mule

A record of the work done on this project, from 27 September to 10 October 2026 (30 September is section 7, 1 October section 8, the 1–2 October audit section 9, the Fusion uploads and version history section 10, the 5–10 October topology study section 11). The step-by-step engineering log, with
every method, result and error, is [`mule/docs/PROJECT_LOG.md`](mule/docs/PROJECT_LOG.md). This page is the overview.

**Starting point:** the concept CAD (`NM26_FSAE_Concept.step`) and the 2026 FSAE rules PDF.
**Result:** a complete, rules-checked design for a drivable test car (a "mule"), all generated from Python code:
- 232 automated design checks and 97 automated tests, all passing, also run by GitHub on every push;
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
| Frame layout and rules | `mule.py` | Parametric frame (124 members, 71 cut pieces) built around the 95th-percentile driver template; 28 FSAE rule checks | 1750 mm wheelbase, 1220 mm tracks, 49.4 kg frame after the topology study (50.4 kg after the audit; 44.3 kg C2 before it; 46.4 kg before the C2 rear; 50.1 kg before the 1 Oct optimisation) |
| Frame rules | `frame_rules.py` | 40 checks for every geometric FSAE frame rule (triangulation, tube size per job, bends, hoops, braces, supports, closed front bulkhead, harness tab tubes, side impact, shoulder bar, mounts, legs and leg clearance, open wheel, tube clashes) | All pass; each key check proven to fail when its rule is broken |
| Frame strength | `fea.py` | 3D beam FEA with inertia relief; roll-hoop loads 6/5/9 kN (legacy AF4), worst of 4 directions and 2 supports; frontal 95 kN; buckling in every case | Roll-over (welded 4130, under review): main 1.22, front 1.11; frontal 1.26; torsion 2399 N·m/deg FEA |
| Suspension kinematics | `suspension.py`, `sideview.py`, `roll.py` | Double wishbones front and rear; roll centres, camber, caster, anti-dive/squat, roll gradient, static camber, jacking, handling balance | RC 37/52 mm, caster 4.6°, scrub 38 mm, camber −2.5/−2.0°, LLTD 49.6 % front (mild understeer) |
| Loads into the frame | `loads.py`, `compliance.py` | Six-link upright statics for 10 load cases; link buckling; compliance steer | Worst frame FoS 1.26; toe change 0.10°/0.18° at 1.5 g |
| Springs, rockers, shocks | `springs.py`, `rocker.py` | Pushrod + bell-crank layout, 230×65 MTB coil shocks | Motion ratio 0.72/0.75, 3.0/2.6 Hz ride, ~282/208 lb/in springs |
| Steering | `steering.py`, `sideview.py` | Bump steer front and rear, Ackermann, 3D tyre clearance at lock, ratio, effort | Kaz rack, 4.1:1, 178° lock-to-lock, 95 N at the rim, rear bump steer 0.00° |
| Uprights and hubs | `uprights.py` | Bearing life, hub shaft, upright arms, wheel studs, rotor packaging | SKF 6209 bearings, 4140 hubs, 7075 uprights |
| Powertrain | `powertrain.py` | Gearing, chain, spool, CV shafts, engine mounts, launch load, toe-link/half-shaft clearance | Engine chosen: Honda CRF450R 2018+ (48 N·m; service-manual gear ratios and 30.9 kg); launch FoS 1.21; top speed 117 km/h. Engine size and mounts still generic until measured |
| Brakes and pedal box | `brakes.py` | Caliper/MC sizing, balance bar, lock-up force, BOTS, 2000 N pedal test, rotor heat | Locks all four at 676 N; 80 bar at lock-up, 267 bar at 2000 N (supplier proof ratings still needed) |
| Cockpit | `cockpit.py` | T.1.1 and T.1.2 templates swept through the whole model | Both pass (after moving the steering rack low and the front shocks) |
| Harness | `harness.py` | Belt angles, mounting tabs, 20 g crash load with a 100 kg driver | Lap belt fixed from 15° to 55°; frame FoS 1.33 vs welded ultimate |
| Electrical | `shutdown.py` | 12 V shutdown circuit simulated as a netlist; wire and fuse sizing | Every shutdown device cuts ignition and fuel pump; 0.23 V drop |
| Mass and CG | `mass.py` | Item-by-item mass budget; tilt test | 301 kg with driver, no wing, CG 325 mm, tilt 61.9° (limit 60°; 61.5° if the estimates err together) |
| Rear wing with DRS | `aero.py` | Two-element wing with a moving flap, inside rule T.7; mounts, oscillation, servo, fail-safe logic. **Not fitted on the base mule** (audit) | 126 N at 60 km/h (assumed coefficients); bolt-on would gain 0.62 s per autocross lap |
| Lap simulation | `lapsim.py` | Point-mass acceleration, skidpad, autocross with a 33 kW restrictor cap and rotating mass; benchmark against FSAE Michigan 2025 results | 5.05 s / 5.38 s / 62.5 s (Michigan medians 4.62 / 5.52 / 55.7 s) |

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
  - An earlier "Go kart CAD assembly" work session built the detailed parts: treads, springs, CV boots, the 15-part engine and the brake-line and wiring routing.
  - This pass:
    - made every part name unique and descriptive;
    - added a "contains" description to each part;
    - added the rear wing;
    - renamed the parts lists to match their STEP files.
- **Fusion 360:**
  - opened and checked each new model;
  - saved the then-current one to `adi laptop files > Nittany Motorsports > NM26_Assembly_v4` (superseded by `NM26_Assembly_v5`, the 44.3 kg frame, on 1 Oct);
  - renamed every older version (v1, v2, simple v1–v3, concept) so the names say what they are.

## 5. Documents

In `mule/docs/`:
- `PDS.md`: 15 requirements (goal: the full FSAE 2026 rules, none traded) with targets, results and how each is verified; design decisions; Pugh matrices; benchmark.
- `BUILD_PLAN.md`: design narrative per system, FSAE rules checklist, bill of materials, build order, buck plan.
- `TEST_PLAN.md`: 7 stages of physical tests with predicted values and pass criteria, based on the Trinity test-manual format.
- `BUDGET_PLAN.md`: five funding steps of about $2,500 or less, about $7.7–11.6k to a driving car with a used 450 at list prices, with an upgrade path and price sources.
- `PARTS_LIST.md`: the parts the design uses, engine options with prices, and which script sizes each part.
- `SIM_TO_REAL.md`: how far to trust each simulation (valid range, error type, margin, the test that measures it) and the real-to-sim loop.
- `RULES_MATRIX.md`: every frame-relevant FSAE 2026 rule with its status (automated check, build/inspection item, or N/A and why).
- `FRAME_RESEARCH.md`: how lighter FSAE steel frames are built, with sources, applied to NM26.
- `PROJECT_LOG.md`: full chronological log.
- `REPORT.md`: generated list of every check and test.

Fabrication data in `mule/fab/`: tube order list, cut sheet with cope angles, hoop bend programs, jig node coordinates, jig plan. Shop quote package in `mule/quote/`.

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
- Gear ratios and engine mass then came from the 2017–18 CRF450R service manual (page 1-5, read on ManualsLib): primary 2.357 (66/28); gears 2.133, 1.706, 1.421, 1.211, 1.043; stock final drive 13/49; engine dry weight 30.9 kg for 2018 on. With our 13/50 sprockets, top speed is 117 km/h, and 1st gear still reaches the traction limit (928 against 859 N·m). The acceleration prediction is now 4.48 s. Still generic: rev limit, engine size and position, and output-shaft position, until an engine is measured.
- The budget to a driving car is now about $7,700–11,600 with a used 450 at list prices (re-priced tube, 1 Oct); the jugaad route is $6,200–10,700, or $4,000–6,000 with a donated engine and sponsored tube.

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

## 8. 1 October: frame weight

- **Frame optimised on the current layout: 50.1 → 45.3 kg, 81 → 78 pieces.** A new optimiser loads every frame
  strength case (roll-hoop loads, ten wheel-load cases, launch, 2000 N pedal, 20 g harness crash, wing mounts). It
  shrinks each tube group to the smallest size its own stresses and the rules allow. It also removed three tubes no rule
  needs: the front bulkhead X-brace, the front hoop floor cross and the lap-belt floor cross. Twist stiffness is now
  1886 N·m/deg (target ≥ 1500). All checks pass. The old frame is kept as git tag `frame-v1-50kg`.
- **Limits found:**
  - Shortening the rear overhang saves only ~0.2 kg, so it isn't worth it.
  - Thinner 0.75″ tubes for the rear box save 1 kg but hurt durability, so they weren't applied.
  - Even the best case of a front-ring redesign reaches only ~44.9 kg.
  - This layout's floor is 38 kg (every tube at the rule minimum, which fails strength).
  - Getting to ~33 kg needs a clean-sheet layout.
- **Shop quote package** in `mule/quote/`: frame STEP (169 parts), material list, cut sheet, bend programs, jig data and
  a cover note asking for quotes in 4130 and 1020 DOM. Rebuilt by `python quote_package.py`.
- **Research:** `mule/docs/FRAME_RESEARCH.md` sums up how lighter FSAE frames are built, with sources. Light frames
  (~32 kg) use about as much tube as ours but nearly all 1″ × 0.049″, because their suspension pickups sit on nodes.
  The three reference reports (Trinity, JCU, NAU) were re-read for frame lessons.
- **FSAE rules made non-negotiable:** an audit of every frame-relevant 2026 rule (V.1, F, T.1, T.2) found about 20
  geometric rules nothing checked. `frame_rules.py` now checks them (34 checks): tube size per job, side-view
  triangulation, hoop shape and lean, braces, bent-member supports, no mounts on the main hoop or its braces, bulkhead and
  brace supports, side impact, shoulder bar, steering protection, hips inside the Major Structure, open-wheel zones.
  Tests prove each key check fails when its rule is broken. The current frame passes all of them.
  `mule/docs/RULES_MATRIX.md` lists every rule with its status (83 automated, 94 build/inspection items, 45 not
  applicable, 15 definitions). The build plan's "FSAE-lite" skips are gone: SES/IAD paperwork, the 20 mm restrictor and
  the noise limit are now required items.
- **Reality gap (sim to real), after NVIDIA's Isaac Lab course:** `robustness.py` re-runs every frame load case in 16
  seeded samples with tube walls ±10 %, joints ±2 mm and 60–100 % tube stiffness (joint flex), and checks tilt with mass
  errors and brake/lap-time bands. It found that the optimised frame had no real-world slack in the 20 g harness case
  (FoS 0.96). Fix: shoulder bar back to 1.5″ and the side-impact diagonal to 1.0″ × 0.095″, so the frame is **46.2 kg**
  (+0.9 kg) and every case stays ≥ 1.03 under tolerances. The twist test now passes at ≥ 1000 N·m/deg *measured*
  (real frames measure ~⅔ of FEA). New tests: frame 3D scan, shock check, and a real-to-sim column in the results log.
  `docs/SIM_TO_REAL.md` explains it all.
- **Roll-over model error found and fixed:** the 6/5/9 kN roll-over cases (from FSAE's Alternative Frame rules AF4)
  held the car at its suspension mounts, which let the load leak into the suspension posts. With AF4's own support (hoop
  bottoms fixed; inertia relief, which AF5.6 allows, agrees within 2 %), the old frame reached only FoS 0.48 / 0.43 against
  the FSAE welded yield. The user chose criterion A: real 4130, weld-limited (85 % of ER70S-2 filler minimums = 340 MPa
  yield / 410 MPa ultimate, per MIL-HDBK-5 practice), FoS ≥ 1.0 nominal and ≥ 1.0 vs ultimate under tolerances. The new
  `frame_opt.py` re-sized the frame under every gate: main hoop 1.5″, upper bulkhead supports 1.0″ × 0.095″, others
  smaller, so the frame is **46.4 kg** (+0.2 kg). This was a real safety gap in the model, not a rules gap: steel tube
  frames don't need AF4 FEA to be legal.
- **Where the weight comes from (measured, not guessed):**
  - Dropping any single strength case saves at most ~2 kg.
  - Relaxing every self-imposed criterion (tolerance check, 20 g harness, FoS 1.2) gets only to 42 kg, with zero margin. Not recommended.
  - Deleting tubes and re-sizing saves ~1 kg, and that version fails the tolerance check.
  - A shorter wheelbase barely changes tube length (the front of the frame follows the driver, not the axle), and it hurts brakes and steering.
  - The weight is set by the ~43 m of tube this layout type needs. The 30–32 kg frames in research use lighter load cases or packaging (10″ wheels, narrow track).
- **Clean-sheet designs, each on its own branch (the 46.4 kg frame was `main` until C2 was merged):**
  - *B1 front box* (branch `clean-sheet-B`): front suspension station ahead of the leg template with a top cross. 51 kg, **rejected**.
  - *C1 "short"* (branch `clean-sheet-short`): seat 15°, front hoop 900 mm, rear end −200 mm, front rocker re-tuned,
    rear side-bay diagonal removed. After the last optimiser pass (rear engine-mount cross to 1.5″ for launch): **46.5 kg,
    74 pieces, torsion 2305 N·m/deg**, every check passing. Same mass as `main`, 15 % stiffer, more tolerance margin, 4
    fewer pieces; helmet clearance thinner (54 vs 65 mm, limit 50). The shorter layout does not save weight.
  - *C2 node-mounted rear* (branch `clean-sheet-C2`): rear wishbone pickups moved onto the main-hoop-brace support
    rail joints (rear lower rail raised to 150 mm, rear top to 328 mm, so the suspension geometry is unchanged), the
    pickup rail and cross deleted, rear rocker re-tuned. The rear posts no longer bend and drop to 1.0″ × 0.049″.
    **44.3 kg, 73 pieces, torsion 1946 N·m/deg**, every check passing: 2.1 kg lighter than `main`. `fab.py` was also
    fixed to cope a tube onto a neighbour it meets at 20° or more.
  - **C2 merged into `main`** (1 October): CAD (simple and detailed), shop data, drawings, frame STEP and the shop
    quote package regenerated; 89 leftover part files of the old frame removed from `cad/parts/`.
  - *C3 direct-acting front shocks*: feasibility check only. The front frame is too narrow: the nearest frame point is
    384 mm from the upright, against a 207–223 mm shock. It would need an outrigger tower on each side (~1.2 kg), roughly
    cancelling the rockers it removes, so it wasn't built.
- **Tooling:** the session scratchpad (Python environment, scratch optimiser) was wiped once. The optimiser now lives in
  the repo as `frame_opt.py` so it can't be lost.

## 9. 1–2 October: full audit, then fixes

**Audit.** Four read-only reviews (frame and FEA; vehicle dynamics, brakes and powertrain; documents and planning;
tests, CI and outputs) went through the whole repo. Their main points, checked against the rulebook:
- the roll-hoop pass rested on a self-chosen welded-4130 strength and on legacy AF4 loads (the 2026 rules have no AF
  section; F.3.4.2 gives 180/300 MPa for any steel in SES calculations);
- two rule checks were too loose (F.5.2.3 bent tubes, F.5.6.3 hoop bends) and hid real violations;
- no frontal-impact case, no buckling check, a harness case with an 80 kg driver whose own mass relieved the load, and a
  tolerance check the optimiser had been tuned against;
- the mass budget missed about 10 kg of parts, the brake compliance was about 8× too stiff, the lap sim had an
  unrestricted engine, and many documents quoted stale numbers.

**Fixes (branch `audit-fixes`).**
- Rear wing and DRS **not fitted** on the base mule (mount points and checks kept; bolt-on later). Tilt 60.8° → 61.9°.
- Mass budget completed: anti-intrusion plate, impact attenuator, intake and restrictor, oil, chain guard, brake lines,
  bodywork, steel uprights. Car 301 kg, 48 % front. Load cases now 310 kg.
- Brakes: compliance 5 mm³/bar (estimate), pedal ratio 4.5, rear master cylinder 13/16″, over-travel switch at 55 mm.
  2000 N pressure 316 → 267 bar; lock-up 80 bar, inside Wilwood's published 138 bar operating limit.
- Frame rules: F.5.2.3 and F.5.6.3 checks rewritten to the rule text and met (straight upper bulkhead support, new hoop
  bend tube, ring cross sized to the lower support); F.5.2.1 bend radius, T.1.3.2 legs and a tube clash check added (the
  clash check found the bulkhead diagonal running through the pedal-box node, so it moved).
- Frame strength: frontal impact 95 kN (F.8.7.2), buckling in every case, inertia-relief roll-over, 100 kg harness
  driver, report check on 32 fresh tolerance samples with the optimiser sizing on its own 16 at a 1.08 margin.
- **Frame re-sized: 44.3 → 50.4 kg** (73 pieces, torsion 2422 N·m/deg). With the crash cases at the welded-4130 410 MPa
  instead of F.3.4.2's 300 MPa it would be 46.65 kg; that is the advisor's call. At F.3.4.2's 180 MPa for the roll-over
  case no tube on the ladder works, which is why that criterion stays open.
- Lap sim: 33 kW restrictor cap (assumed), rotating mass, grip 1.2: acceleration 5.05 s, skidpad 5.38 s, autocross 62.5 s.
- Shop data: tube ends run past their joints, hoop-corner jig points on the real bend; quote note specifies ER70S-2,
  mill certs and end caps.
- 228/228 checks, 97/97 tests.

## 10. 2–3 October: Fusion uploads and version history

- `NM26_Assembly_v6` (2 Oct; renamed `_v6_stray_wire_superseded` on 12 Oct) and `NM26_Assembly_v7` (3 Oct) uploaded to Fusion, `adi laptop files > Nittany Motorsports`.
  Both are the 50.4 kg post-audit frame without the wing. v6 still drew the DRS servo wire up to where the wing was;
  the detailed CAD now drops that wiring when the wing isn't fitted, and v7 is clean. Frame v5 (section 11) went up as `NM26_Assembly_v8` on 12 Oct.
- `mule/docs/VERSIONS.md` records what changed between every frame version and which Fusion file shows which frame.
  Each frozen `history/` copy was re-run with its own code, so the numbers are measured, not copied from old docs.
- Writing it showed one change not reported before: straightening the upper bulkhead support moved the front upper
  suspension pickup 25 mm outboard (lower 5 mm). Every suspension and steering check still passes.
- Documentation sweep: module descriptions in both READMEs, the build plan's brake and wing items, and the frame
  research table brought to the post-audit design.

## 11. 5–10 October: topology study, frame v5 (49.4 kg)

- With tube sizes at their optimum, the next saving had to come from the layout. `topo_study.py` removed members one
  pair at a time while every gate still passed; two tubes came out (the FBH-support front-bay diagonal and the upper
  spool carrier post): **50.4 → 49.4 kg**, 71 pieces, torsion 2399 N·m/deg.
- `topo_search.py` then tried adding every possible new diagonal and re-sizing. Against the tolerance gate every frame
  must pass, the best layout with new tubes was 49.36 kg for 8 extra tubes, so none were added.
- The study exposed four check gaps, now closed: the front bulkhead must be a closed perimeter (F.6.2), harness tab nodes
  must sit on harness-size tube (F.3.2.1), no tube within 10 mm of the driver's legs, and no tube through the engine
  box away from its mounts. 228 → 232 checks.
- Margins are thinner than v4: front hoop roll-over 1.11 (was 1.18), frontal impact 1.26 (was 1.31), all above 1.0.
- Merged into `main` on 10 Oct with the CAD, shop data and quote package regenerated; frozen copy
  `history/frame_v5_49.4kg`. Details: `mule/docs/VERSIONS.md`.

## 12. Still open (needs people, parts or suppliers)

1. **Brake pressure ratings in writing** from Wilwood, Tilton and the hose supplier: proof rating covering 267 bar (the 2000 N test); 300 bar assumed.
2. **Measure a CRF450R 2018+:** its mounts, output shaft and size go into `ENGINE` in `powertrain.py` **before ordering tube** (gear ratios and mass are already in, from the service manual).
3. **Build the buck** and fit the drivers before cutting tube.
4. **Weigh parts as they arrive**: the tilt margin is about 1.5–1.9° with the wing off (61.9° nominal, 61.5° if mass estimates all err the same way).
5. **Faculty / alumni review** of the roll-over criterion (welded 4130 at 340/410 MPa; 180 MPa is infeasible) and of the crash-case criterion (300 MPa gave 50.4 kg before the topology study, now 49.4 kg; 410 MPa gave 46.65 kg on the pre-topology layout), and the weld procedure; it assumes 4130 with ER70S-2 filler, so revisit it if the shop quotes 1020 DOM.
6. **Run TEST_PLAN stages 1–7** on the real car and put the measured numbers back into the code, especially the wing's aero coefficients.
