# NM26 mule: product design specification

This page lists the car's requirements. Each one has a number and a way to verify it: the code check that predicts it (see `REPORT.md`), and the physical test that confirms it (see `TEST_PLAN.md`). Change a target here first, then in the code.

**Top-level goal:** a drivable FSAE-lite mule. It meets the 2026 FSAE *safety* rules (structure, harness, brakes, shutdown, cockpit), so the team can learn and test on it. It is not a competition car, but at the team's request it now carries a rear wing with DRS (R15). It has no restrictor, noise test, SES/IAD or cost report.

**Constraints:**
- the 2026 FSAE rules (safety sections);
- a budget of roughly $9–15k;
- a 4130 tube frame built in-house (TIG);
- a used 450–510 cc single;
- 13″ wheels.

| # | Requirement | Target | Predicted (code) | Verified by |
|---|---|---|---|---|
| R1 | Roll structure strength, 6/5/9 kN hoop loads | FoS ≥ 1.2 vs welded yield | 1.28 main / 1.36 front, worst of 4 load directions; deflection ≤ 3.9 mm vs 25 (`fea.py`) | T1.2, T1.3 |
| R2 | Chassis torsional stiffness | ≥ 1500 N·m/deg (FSAE practice 1000–3000) | 2138 (`fea.py`) | T1.2 twist test |
| R3 | Frame under wheel, launch and pedal loads | FoS ≥ 1.2 | 1.26 / 1.22 / 1.31 (`loads.py`, `powertrain.py`, `brakes.py`) | T5.2, T7.2 |
| R4 | Harness mounts survive a crash | 20 g, FoS ≥ 1 vs welded UTS; tabs ≥ 15 kN | 1.17; 31.7 kN (`harness.py`) | T1.3, T4.3c |
| R5 | Rules geometry (hoops, helmet, SIS, IA, belts, templates) | every listed rule passes | 27 + 2 + 8 checks (`mule.py`, `cockpit.py`, `harness.py`) | T4.3, T4.3b |
| R6 | Mass and CG | ≤ 300 kg with driver; CG ≤ 345 mm; tilt ≥ 60° | 296 kg, 340 mm, 60.9° with the wing (`mass.py`) | T4.1, T4.2 |
| R7 | Ride | 3.0 / 2.6 Hz; +50 / −25 mm travel (rule: 50 mm total); motion ratio 0.7–1.0; springs in the MTB coil range | 0.72 / 0.75; 243 / 215 lb/in (`springs.py`, `rocker.py`) | T2.4, T2.5, T5.3 |
| R8 | Kinematics | RC 15–60 / 25–80 mm; camber gain −0.3 to −1.2 °/25 mm; bump steer ≤ 0.25° front and rear; front scrub ≤ 40 mm; front share of the lateral load transfer 0–12 points above the front weight share; outside tyre −2.0 to −0.3° to the ground at 1.5 g; compliance toe and camber ≤ 0.25° | 37/52 mm, −0.72/−0.75, 0.11° / 0.00°; 38 mm; 49.6 % vs 45 %; −0.9/−0.4°; 0.10 in / 0.18 out toe (`suspension.py`, `steering.py`, `roll.py`, `compliance.py`) | T2.2, T2.3, T2.7 |
| R9 | Steering | 23° inner lock; Ackermann 0–120 %; ratio 4–7:1; lock-to-lock ≤ 180°; rim force ≤ 120 N at 1.5 g; caster 3–7° | 50 %, 4.1:1, 178°, 95 N, 4.6° (`steering.py`, `sideview.py`) | T2.6 |
| R10 | Braking | lock all four with ≤ 600 N; 2000 N without failure; front locks first | 567 N; 296 bar; 59 % front (`brakes.py`) | T3.2–T3.4, T6.1 |
| R11 | Performance | 100–130 km/h top speed; 1st gear reaches traction | 117 km/h (`powertrain.py`, CRF450R ratios) | T5.1 |
| R12 | Durability | bearing L10 ≥ 3 × 2000 km; hub and upright FoS ≥ 1.5 | 271–512 Mrev; 5.1 / 1.7 (`uprights.py`) | T7.2 |
| R13 | Shutdown | any device kills ignition and fuel pump; master switch cuts everything | netlist simulation (`shutdown.py`) | T4.4 |
| R15 | Aero | Rear wing with DRS inside T.7; 200 N push ≤ 25 mm; mounts don't oscillate; DRS fails closed; no event slower than without the wing | all T.7 limits met in both flap positions; 0.1 mm; 159 Hz; spring return; autocross −0.67 s (`aero.py`, `lapsim.py`) | T4.5, T5.5 |
| R14 | Events (point mass, grip 1.3) | acceleration ≤ 5.0 s; skidpad ≤ 5.5 s; autocross average ≥ 40 km/h | 4.48 s; 5.12 s; 51 km/h (`lapsim.py`) | T5.1, T7.1 |

**Accepted non-requirements for the mule:**
- the FSAE hairpin turning circle (ours is 5.7 m radius; a hairpin needs 4.5 m);
- noise;
- cost report.

**Decisions and the reason for each:**

| Decision | Chosen | Rejected, and why |
|---|---|---|
| Steering rack position | Low, under the shins, with the leg template passing over it | Ahead of the pedals: 4.4° bump steer and anti-Ackermann |
| Front ring top | No cross tube; 1.5″ posts | Raised 570 mm cross: the posts bend (FoS 0.66) |
| Throttle | Mechanical cable | Electronic: needs APPS and BSPD |
| Anti-dive / anti-squat | 0 % | More anti gives a harsher ride; not needed on a mule |
| Final drive | Chain to a spool | Differential: cost and complexity |
| Rear suspension | Independent double wishbone, pushrod | Solid (beam) axle on trailing arms, as in the JCU 2020 paper: cheaper and simpler, but no camber gain in roll, and the axle adds unsprung mass. The spool already gives the solid-axle drive benefit. |
| Handling balance | Front ride 3.0 Hz, rear 2.6 Hz (LLTD 49.6 % front) | Rear stiffer (2.8/2.6): LLTD 40 %, oversteer. Front anti-roll bar: it would cross the T.1.2 template at the ring top, so it's kept as a later tuning part. |

## Pugh matrices

Each option is scored against the first column, the datum: + better, 0 same, − worse. The scores are the team's judgement, and the numbers they rest on come from the code. Re-score when a number changes.

**Wheel travel and motion ratio** (datum: ±50 mm travel at 0.59 / 0.50, the old design)

| Criterion | ±50 mm, MR 0.59 / 0.50 (datum) | **+50 / −25 mm, MR 0.72 / 0.75 (chosen)** | ±50 mm, 250×75 shock, MR 0.72 |
|---|---|---|---|
| Meets V.3.1.1 (50 mm usable) | 0 | 0 (75 mm) | 0 |
| Damper resolution and friction (higher MR is better) | 0 | + | + |
| Spring rate in the MTB range | 0 | + (243 / 215 lb/in after the balance fix) | + |
| Droop for rough test lots | 0 | − (25 mm) | 0 |
| Packaging and cost | 0 | 0 (same shock) | − (longer shock hits the T.1.2 template and the rocker needs re-packaging) |
| **Total** | 0 | **+1** | +1, with more risk |

**Front scrub radius** (datum: 53 mm, the old design)

| Criterion | Inset 65, lean 20 (datum) | **Inset 62, lean 40 (chosen)** | Inset 45, lean 35, move the lower-arm front leg |
|---|---|---|---|
| Scrub (steering effort, kickback) | 0 | + (38 mm) | + + (24 mm) |
| KPI (camber loss at lock, jacking) | 0 | − (9.6°) | − (8.4°) |
| Tyre-to-arm gap at lock | 0 | 0 (10 mm) | − (needs frame-node changes; FEA, templates and fab re-run) |
| Build risk / rework | 0 | 0 | − |
| **Total** | 0 | **+0 (better scrub, same risk)** | −1 |

**Rear wing** (datum: no aero, the mule scope). *Superseded:* the team asked for a moving rear wing, so it's built. The tilt objection is answered by widening the rear track to 1220 mm; the design keeps 0.9° of tilt margin.

| Criterion | No wing (datum) | Rear wing |
|---|---|---|
| Grip at autocross speeds (40–60 km/h) | 0 | + (small: downforce rises with speed squared) |
| Tilt margin (61.3° vs 60°) | 0 | − − (5–8 kg high up) |
| Cost, design and test effort | 0 | − |
| Rules to meet (T.7 aero dimensions, mounting) | 0 | − |
| **Total** | 0 | **−3** |

Revisit the wing only after the tilt margin grows (weigh the parts) and the car runs reliably.

## Benchmark

**Event times, FSAE Michigan 2025** (official results, [fsaeonline.com](https://www.fsaeonline.com/CompResources/2025/c796a916-c2e8-4ce6-bae3-c79f36776556/FSAE_2025_MI5_results.pdf), about 72 cars per event):

| Event | Best | 10th | Median | NM26 mule, point mass at grip 1.3 |
|---|---|---|---|---|
| Acceleration, 75 m | 4.169 s | 4.324 s | 4.617 s | 4.48 s (CRF450R torque and ratios) |
| Skidpad | 5.080 s | 5.287 s | 5.515 s | 5.17 s |
| Autocross | 48.878 s | 52.019 s | 55.725 s | 59.2 s on our own 0.8 km course, so indicative only |

A point mass has no driver, no tyre warm-up and no transients, so real times will be slower. The comparison says the mule is a mid-field-class car on paper, which is enough for a test car.

**Vehicle numbers from other teams** (to fill in from published design reports; none are invented here):

| Quantity | NM26 mule (code) | Team A | Team B | Team C |
|---|---|---|---|---|
| Mass with driver | 296 kg | | | |
| CG height | 340 mm | | | |
| Wheelbase / track F/R | 1750 / 1220 / 1220 mm | | | |
| Frame torsion | 2138 N·m/deg | | | |
| Ride frequency F/R | 3.0 / 2.6 Hz | | | |
| Motion ratio F/R | 0.72 / 0.75 | | | |
| Scrub / KPI / caster | 38 mm / 9.6° / 4.6° | | | |
| Steering ratio, lock-to-lock | 4.1:1, 178° | | | |
