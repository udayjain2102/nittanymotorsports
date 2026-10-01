# Sim to real: how NM26 handles the reality gap

Every number in this project comes from a model. A model is a simplification, so there is always a gap between it and
the real car. This page lists, for every simulation: where its results are valid, what kind of error it carries, what
margin covers that error, and which physical test will measure the real value. It follows NVIDIA's sim-to-real course
([Isaac Lab: transferring policies from simulation to reality](https://docs.nvidia.com/learning/physical-ai/getting-started-with-isaac-lab/latest/transferring-robot-learning-policies-from-simulation-to-reality/index.html)),
translated from robots to a race car.

## The three kinds of error (NVIDIA's terms)
- **Approximation errors:** the maths is simplified (beam elements, rigid joints, a point-mass car).
- **Model errors:** the inputs are wrong (tube wall tolerance, estimated masses, assumed tyre grip or pad friction).
- **Unmodelled dynamics:** effects left out entirely (weld softening, joint flex, damper behaviour, tyre temperature).

## The three ways to close the gap, and what we do for each
| NVIDIA approach | Meaning | NM26 |
|---|---|---|
| **Domain randomisation** | Re-run the model across realistic variations, not one nominal value | `robustness.py`: tube walls ±10 %, joints ±2 mm, tube stiffness 60–100 % (joint flex), masses ±10 % (independent and correlated), pad friction 0.35–0.45, grip ±0.1. Checked on every push |
| *…but measured, not maximal* | Too much variation gives a cautious, mediocre design | Ranges come from tube specs and published FEA-vs-test data, not huge blanket safety factors |
| **Real-to-sim / system identification** | Measure the real hardware, tune the model to match | `TEST_PLAN.md` stages measure mass, stiffness, grip, drag, brake pressure. Each result goes back into the code (see the loop below) |
| **Regularisation** | Penalise aggressive "optimal in sim, breaks in reality" solutions | The weight optimiser may not leave tubes at 100 % of nominal; every result must pass the robustness gates, and every FSAE rule (`RULES_MATRIX.md`) |
| **Privileged information** | Simulation sees what sensors can't; use it to train what the real system measures | The FEA knows the load in every tube. Use it to pick where strain gauges and data logging go (the highest-utilised tubes) |

## Every simulation: validity, gap, margin, measurement
| Model | Valid for | Main gap (type) | Margin covering it | Measured by |
|---|---|---|---|---|
| Frame FEA (`fea.py`) and load cases | Static loads, linear elastic, below yield | Rigid joints, beam elements (approximation); wall tolerance (model); weld heat-affected zone, joint flex (unmodelled) | Welded yield 180 MPa everywhere (F.3.4.2, conservative); nominal FoS ≥ 1.2; **robust FoS ≥ 1.0 in every tolerance sample** | TEST_PLAN T1 (twist test), T7 (strain gauges later) |
| Frame torsion | Pickup-to-pickup stiffness | FEA typically reads ~1.5× the measured value (FSAE practice) | **Worst sampled torsion ≥ 2 × suspension roll stiffness** (Deakin: ~90 % of load transfer reaches the tyres) | T1.2 twist rig |
| Weight optimiser | The listed load cases only | Sizes tubes to the limit of what's modelled; fatigue not modelled | Robustness gates, all FSAE rules, durability over 1 kg savings (no thin unregulated tubes) | Crack inspection after shakedown (T7) |
| Suspension kinematics (`suspension.py`, `steering.py`, `sideview.py`) | ±50 mm travel, quasi-static | Front-view 2D (approximation); pickup position after welding ±1–2 mm (model) | Shims for camber; adjustable toe links; `compliance.py` adds frame and link flex | T2 (travel, camber, bump steer) |
| Springs and dampers (`springs.py`, `rocker.py`) | Ride frequencies, motion ratios | MTB shock damping unknown (unmodelled) | Adjustable spring preload; shock choice from a range | **Add:** shock drop test / dyno before fitting (T2) |
| Lap sim (`lapsim.py`) | Steady-state point mass | No transients, no tyre load sensitivity (approximation); grip 1.3 from one benchmark (model) | Times treated as lower bounds; band: grip 1.2 → 1.4 gives accel 4.63 → 4.36 s, skidpad 5.34 → 4.93 s | T7.1 skidpad → measured grip back into `lapsim.GRIP` |
| Aero / DRS (`aero.py`) | Steady flow | Lift and drag coefficients assumed, no CFD (model); wake from driver and hoop (unmodelled) | Wing must not slow any event even with the assumed numbers; mounts FoS 22 | T5.5 coast-down / downforce test |
| Brakes (`brakes.py`) | Static pressure balance | Pad friction 0.40 assumed; supplier pressure ratings unverified (model); fade (unmodelled) | Lock-all-four force 504–648 N over pad friction 0.45–0.35; parts must be rated ≥ 296 bar **in writing** | T3 (pressure, lock-up) |
| Mass and CG (`mass.py`) | Item list | Every mass is an estimate (model); fluids, fasteners, wiring (unmodelled) | Tilt ≥ 60° checked with masses ±10 % independent (5th percentile 60.7°) **and** all errors in the worst direction (60.3°) | **Weigh every part as it arrives**; T4.1 corner weights, T4.2 tilt |
| Powertrain (`powertrain.py`) | Gearing, chain, launch | CRF450R mounts, envelope, rev limit not measured (model) | Launch case at the traction limit (worst case) | Measure the engine; T5.1 |

## The real-to-sim loop (do this after every test stage)
1. Run the test in `TEST_PLAN.md` and record the measured value next to the predicted one.
2. If they differ by more than the test's tolerance, find which input was wrong (not just which output).
3. Change that input in the code (`mass.py` masses, `lapsim.GRIP`, `aero.py` coefficients, `brakes.PAD_MU`, frame stiffness factor).
4. Run `python report.py`. If a check now fails, fix the design or the next stage's plan before continuing.
5. Log it in `PROJECT_LOG.md`: model vs measured, what changed.

## Tests added because of this review
- **Frame 3D scan after welding** (phone LiDAR or a school scanner): compare with CAD to catch weld distortion before
  fitting suspension (digital-twin idea).
- **Shock drop or dyno test** of the used MTB shocks before fitting (actuator-modelling idea: measure the black box).
- **Corner-weight scales** at T4.1, so the tilt margin uses measured mass, not estimates.
- **Strain gauges or data logging** on the tubes the FEA says are most loaded, when the data-logging upgrade happens.

## NVIDIA's practical tips, applied
- *Understand the system deeply; use test stands and load cells:* the torsion rig, corner scales and brake gauge in the
  test plan.
- *Don't assume one success carries over:* each subsystem is tested alone before the next stage (TEST_PLAN order).
- *Start simple, add complexity on evidence:* low-speed parking-lot shakedown first, with a spotter and an extinguisher.
- *First deployment is the riskiest:* the first drive follows TEST_PLAN stages 3–4 (brakes, shutdown, tilt), all passed.
