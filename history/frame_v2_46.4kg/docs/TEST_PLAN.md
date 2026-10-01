# NM26 mule: physical test plan

Every test has four parts:
- **Objective:** what the test proves.
- **Predicted:** the number the design code gives, and which script gives it.
- **Procedure:** how to run the test.
- **Pass:** the acceptance criterion.

When a measurement misses its prediction, go back to the named script: fix the assumption (mass, grip, compliance and so on) or fix the part, re-run `pytest -q tests`, then retest. Record every run in the results log at the end.

The format was adapted from a 2020 FSAE senior-design test plan; the numbers are ours. Rule references are to `FSAE_Rules_2026_V1.pdf`. `tests/test_test_plan.py` fails if a predicted number here drifts from the code.

## Order (each stage needs the ones before it)

```
1 Frame (bare)  ──►  2 Corners + suspension (car on stands)  ──►  3 Brakes + pedal box (static)
                                                                          │
4 Assembled car, static: weights/CG, tilt, egress, shutdown  ◄────────────┘
        │
        ▼
5 Low-speed running  ──►  6 Brake test (4-wheel lock)  ──►  7 Skidpad / handling
```

Nobody drives until stages 1–4 pass. Brakes (stage 3) and shutdown (stage 4) are hard gates.

**Equipment:**
- digital angle gauge;
- dial indicator with magnetic base;
- 0–100 bar and 0–350 bar brake pressure gauges with bleeder adapters;
- a force gauge or load cell (≥ 2500 N) with a pedal adaptor;
- 4 corner scales, or 2 bathroom scales used one axle at a time;
- toe plates or a string box;
- an IR thermometer;
- a phone with an accelerometer app (e.g. phyphox);
- a torque wrench and paint pen;
- cones and a 30 m tape;
- a stopwatch or phone timer;
- two people for every test (one operates, one records).

---

## Stage 1: frame (bare, on the jig, before paint)

### T1.1 Frame mass and node positions
- **Objective:** check that the frame was built as modelled.
- **Predicted:** 46.4 kg of tube (`mule.py`); welds, tabs and brackets add about 4 kg (`mass.py`). Node coordinates are in `fab/jig_node_coordinates.csv`.
- **Procedure:**
  1. Weigh the frame.
  2. Measure the 12 hardpoint nodes (suspension pickups, rocker and shock mounts) from the jig table. Use a height gauge and a tape from the jig datum.
- **Pass:**
  - mass 46–54 kg (tube plus about 4 kg of tabs and weld, ±8 %);
  - every suspension and rocker pickup within ±2 mm of `fab/jig_node_coordinates.csv`;
  - hoops within ±3 mm.

### T1.2 Torsional stiffness
- **Objective:** confirm the beam FEA, and find weak welds or joints.
- **Predicted:** 2004 N·m/deg (`fea.py`). The model has rigid joints, so the real frame will be softer: FSAE frames typically measure about ⅔ of rigid-joint FEA (≈1340), and `robustness.py`'s worst tolerance sample gives 1514. **Expect 1300–1500 measured.**
- **Procedure:**
  1. Bolt the rear pickups to a rigid fixture.
  2. Put a beam across the front lower pickups and hang weights at a measured arm, so torque T = W × arm. Use 200, 400 and 600 N·m.
  3. Measure the vertical movement of both beam ends with dial indicators. Twist angle = atan((d_left + d_right) / beam span).
  4. Unload and check the angle returns to zero.
- **Pass:**
  - ≥ 1000 N·m/deg measured (2 × the suspension roll stiffness of ~476 N·m/deg, so ~90 % of the load transfer reaches the tyres; `SIM_TO_REAL.md`);
  - linear within 10 % across the three loads;
  - returns to within 0.05°.
- **Then (real-to-sim):** record the measured/FEA ratio in the results log and use it for all later stiffness predictions.
- **If lower:** look for a missing or poor weld first; the rear bay diagonals and the engine-mount crosses matter most. Then check the model in `fea.py`.

### T1.3 Weld inspection
- **Objective:** find weld defects before the car is loaded.
- **Procedure:** visual check plus dye penetrant on the following, and on every weld at a node the FEA reports at safety factor < 1.5:
  - all hoop joints;
  - the hoop brace ends;
  - the engine-mount crosses;
  - the spool posts;
  - the pedal box crosses;
  - the suspension pickup tabs;
  - the harness tabs and the lap-tab braces (`harness.py`).
- **Pass:**
  - no cracks, undercut or porosity;
  - weld length ≥ 25 mm on the AIP (F.8.2).

### T1.4 Frame 3D scan (digital twin)
- **Objective:** catch weld distortion before any suspension part is fitted.
- **Procedure:** scan the bare frame on the jig and off it (phone LiDAR app or the school's scanner). Align the scan to
  `cad/simple/NM26_Frame_FEA.step` and measure every pickup node.
- **Pass:** pickups within ±2 mm, hoops within ±3 mm (same as T1.1). If a pickup is out, enter the measured position in
  `mule.py` and re-run `report.py` before deciding to correct it with shims or a re-made tab.

---

## Stage 2: corners and suspension (car on stands, springs removed unless stated)

### T2.1 Wheel travel and bind
- **Objective:** the design travel, 50 mm bump and 25 mm droop, is free (V.3.1.1 needs 50 mm usable).
- **Predicted:** no lock-up over ±50 mm (`suspension.py`); the shock limits droop to 25 mm.
- **Procedure:**
  1. Remove the springs.
  2. Cycle each corner from droop to bump by hand.
  3. Check the rod-end angles, the CV plunge (rear) and the rocker swing (front +9/−20°, rear −8/+16°).
- **Pass:**
  - smooth, with no bind or contact;
  - every rod end short of its misalignment limit;
  - the CV does not bottom (predicted plunge 4.8 mm).

### T2.2 Camber gain
- **Predicted:** −0.72° front and −0.75° rear per 25 mm of bump (`suspension.py`). Set static camber to −2.5° front and −2.0° rear first (`roll.py`).
- **Procedure:** use the digital angle gauge on the hub face at −25, 0, +25 and +50 mm (droop stops at −25), measured at the wheel centre.
- **Pass:** within ±0.2° per 25 mm of the prediction.

### T2.3 Bump steer
- **Predicted:** no more than 0.12° of toe change over ±50 mm (`steering.py`).
- **Procedure:** fix the steering wheel at centre and measure toe with the plates at the same five heights.
- **Pass:** |toe change| ≤ 0.25° over ±50 mm. If not, shim the tie-rod outer end.
- **Rear:** repeat on each rear corner. The toe link is aimed at the arms' instant centre, so the prediction is 0.00°. If the toe change is over 0.25°, shim the toe-link outer end.

### T2.7 Compliance steer
- **Predicted** (`compliance.py`): at the 1.5 g corner load, 0.10° toe-in at the outside front wheel and 0.18° toe-out at the outside rear.
- **Procedure:**
  1. Car on stands with the springs in.
  2. Strap the wheel and pull its contact patch sideways, toward the car centre, with a ratchet strap and a load cell. Pull 1.5 kN front or 2.0 kN rear, about the design corner load.
  3. Read the toe from a laser or dial gauge on the rim at the front and rear of the wheel. Read it before, at full load, and after release.
- **Pass:**
  - under 0.25° toe change;
  - it returns to within 0.02° after release. If it doesn't, something is slipping: check the rod-end jam nuts and tabs.
- **Use:** the difference from the prediction is rod-end and bracket compliance the model leaves out. If the rear toe-out is over 0.25°, upsize the toe link or add a gusset at its frame tab.

### T2.4 Motion ratio and shock stroke
- **Predicted** (`rocker.py`, `springs.py`):

  | | Front | Rear |
  |---|---|---|
  | Motion ratio | 0.72 | 0.75 |
  | Shock length over +50 / −25 mm | 169–224 mm | 167–225 mm |
  | Static shock length | 207 mm | 207 mm |

- **Procedure:** fit the shock without its spring, then measure eye-to-eye at the five heights.
- **Pass:**
  - motion ratio within ±10 %;
  - the shock stays inside 165–230 mm.

### T2.5 Wheel rate
- **Predicted:** front 22.1 N/mm, rear 21.2 N/mm with the specified springs (about 243 / 215 lb/in; `springs.py`).
- **Procedure:**
  1. Fit the springs.
  2. Jack under the lower ball joint and read load vs. hub-to-frame travel at 3 loads.
- **Pass:** within ±15 %.

### T2.6 Steering lock, clearance and free play
- **Predicted** (`steering.py`):
  - inner wheel 23.0°, outer 20.6° (Ackermann 50 %);
  - rack travel 29.6 mm each side; 178° lock-to-lock with the Kaz rack (`sideview.py`);
  - tyre-to-lower-A-arm gap 10 mm at full lock;
  - caster 4.6° and mechanical trail 11.5 mm (`sideview.py`);
  - bump steer at full lock ≤ 0.27° over ±25 mm.
- **Procedure:**
  1. At full lock each way, measure both wheel angles on turn plates.
  2. With the corner at full bump and at full droop, measure the tyre and rim gap to the arms, rods and frame with a feeler or blocks.
  3. For free play (V.3.2.5), follow the reference plan's method:
     - lock the front wheels;
     - rock the steering wheel between the stops of the play with a consistent hand torque;
     - measure the arc at the rim and convert to degrees;
     - repeat 10 times.
- **Pass:**
  - the steering stops engage before any contact;
  - gap ≥ 10 mm everywhere;
  - free play mean + 2 standard deviations < 7°;
  - the steering wheel stays below the front hoop top at every angle (T.1.4.4).

### T2.8 Shock check before fitting (measure the black box)
- **Objective:** the used MTB shocks' damping and spring rate are unknown; measure them instead of assuming.
- **Procedure:** check each spring rate on a press with a scale (load at 3 deflections). For damping, use a shock dyno if
  one can be borrowed; otherwise a drop test: drop a known mass on the shock from a fixed height and film the rebound.
- **Pass:** spring rates within ±10 % of `springs.py` (≈243 / 215 lb/in); all four shocks of a pair match within 10 %.
  Enter the measured rates in `springs.py` and re-run `report.py`.

---

## Stage 3: brakes and pedal box (static)

Precondition: **the pressure ratings of the master cylinders, calipers and hoses are confirmed in writing to be ≥ 296 bar.** `brakes.HYD_LIMIT` is currently an unverified 300 bar. If the ratings are lower, stop, and redesign in `brakes.py` (a bigger caliper piston area lowers the test pressure) before T3.3.

### T3.1 Circuits, leaks and bleeding
- **Objective:** confirm two independent circuits with separate reservoirs (T.3.1.3/4).
- **Procedure:**
  1. Bleed both circuits.
  2. Hold 500 N on the pedal for 60 s.
  3. Open the front circuit only: the rear must still brake. Then repeat with the rear circuit open.
- **Pass:**
  - no pressure drop greater than 3 bar in 60 s;
  - each circuit works alone;
  - no leaks;
  - braided lines only (T.3.1.7).

### T3.2 Pedal force vs. line pressure (balance check)
- **Predicted:** balance bar at 56.9 % front, pedal ratio 5.0 (`brakes.pressures`).

  | Pedal force | Front | Rear |
  |---|---|---|
  | 200 N | 28.8 bar | 15.1 bar |
  | 500 N | 74.0 bar | 36.3 bar |
  | 1000 N | 143.8 bar | 75.5 bar |

- **Procedure:** fit gauges on a front and a rear bleeder, then apply each force with the load cell on the pad centre, 3 times each.
- **Pass:**
  - both pressures within ±10 % of the table;
  - front/rear ratio within ±3 % (set it with the balance adjuster).
- **If off:** a ratio error means the pedal geometry or the bar setting is wrong. Pressure too low on both circuits means friction or a mis-built pedal ratio.

### T3.3 2000 N pedal load (T.3.2.2)
- **Predicted** (`brakes.py`):
  - 296 bar front, 145 bar rear (the assumed 300 bar limit leaves only 4 bar: get the ratings in writing first);
  - pad travel 19 mm;
  - safety factors: pedal 3.8, pivot bolt 6.8, balance bar 2.1, frame 1.31.
- **Procedure:**
  1. Scribe a reference line on the pedal and the base plate.
  2. Ramp to 2000 N over 5 s using the load cell with a lever or press adaptor, and hold 10 s. Record the pressures and pad travel.
  3. Release, and re-measure the scribe.
  4. Dye-check the pedal-box crosses.
- **Pass:**
  - no leak;
  - no permanent set greater than 0.5 mm at the pad;
  - no cracking;
  - pad travel ≤ 30 mm.
- **If travel is high:** air in the system or compliant hoses. Update `brakes.COMPLIANCE` with the measured value.

### T3.4 Brake over-travel switch (T.3.3)
- **Predicted:**
  - trips at 45 mm of pad travel;
  - normal travel at 2000 N is 18 mm;
  - with a circuit lost, the MC bottoms at 84 mm (front circuit lost) or 74 mm (rear circuit lost).
- **Procedure:**
  1. With the ignition on (engine off, shutdown circuit live), press to 2000 N: the switch must not trip.
  2. Crack the front bleeder, press, and confirm the switch trips and the shutdown circuit opens. Repeat for the rear.
  3. Confirm the driver cannot reset it from the seat.
  4. Re-bleed afterwards.
- **Pass:**
  - trips in both lost-circuit cases;
  - never trips at 2000 N on an intact system;
  - latches off.

### T3.5 Throttle (IC.3.3, T.1.4.1)
- **Procedure:** check the following:
  - two return springs at the throttle body;
  - the pedal returns to closed with either spring removed;
  - a positive stop at full throttle;
  - the cable is ≥ 50 mm from the exhaust;
  - the cable is guarded from the feet.
- **Pass:** all yes.

---

## Stage 4: assembled car, static (all fluids, tallest driver)

### T4.1 Corner weights and CG height
- **Objective:** measure the three numbers every load case depends on.
- **Predicted by `mass.py`:** 296 kg with the driver and the rear wing, 46.1 % front, CG 340 mm.
- **Assumed by the load cases (`loads.py`):** 300 kg, 45 % front, CG 345 mm. They are set to cover the budget.
- **Procedure:**
  1. Weigh all four corners.
  2. For CG height, lift the rear axle by a measured height h (about 250 mm), with the suspension locked by replacing the shocks with solid links. Re-weigh the front.
  3. CG height = r + (ΔW_front × L) / (W × tan θ), where r is the axle height, L the wheelbase and θ the lift angle.
- **Pass:**
  - mass ≤ 300 kg;
  - front 42–50 %;
  - **CG height ≤ 345 mm** (the load-case assumption, with the rear wing; also see T4.2).
- **If outside:** put the measured masses in `mass.py` and the totals in `loads.py`, then re-run `pytest`. That re-checks the frame, uprights, brakes, springs and tilt.

### T4.2 Tilt test (IN.11)
- **Predicted:**
  - the car rolls at 60.5° (both tracks are now 1220 mm), from atan(half-track / CG height) with the assumed 345 mm CG;
  - it rolls at 60.9° with the 340 mm budget CG, rear wing included (`mass.py`);
  - at 60° the CG must be ≤ 352 mm.
- **This is the thinnest margin in the whole design:** about 1°, before tyre and spring compliance, which reduce it further.
- **Procedure:** use a tilt table or a strapped ramp, with a safety strap on the high side.
  1. Tilt to 45° with all fluids at maximum and the driver in: no leaks.
  2. Tilt to 60°: no lift-off.
- **Pass:** IN.11.2.1 and IN.11.2.2.
- **If it lifts:** lower the seat, fuel cell and battery, or widen the track, and update `mule.py`.

### T4.3 Driver checks and egress (IN.9)
- **Predicted:** helmet 65 mm below the hoop line (`mule.py`, rule ≥ 50).
- **Procedure:**
  1. Check each driver for helmet clearance with a straightedge across the hoops.
  2. Check the head restraint is within 25 mm of the helmet.
  3. Check the harness fit (T.2.5–T.2.7).
  4. Egress: with gloves and helmet, hands on the wheel, time to two feet on the ground. Record 3 tries.
- **Pass:**
  - clearance ≥ 50 mm;
  - every egress ≤ 5 s.

### T4.3b Cockpit templates (T.1.1, T.1.2)
- **Predicted:** both pass (`cockpit.py`). The opening template clears the upper side-impact tubes by 5 mm. The leg template goes over the rack and between the front ring posts; there is no ring-top cross tube, on purpose.
- **Procedure:** make both templates from 6 mm plywood to the rules drawings (pages 55–56). Insert the opening template horizontally from above, and the cross-section template vertically behind the steering column, sliding it to 100 mm behind the pedal face.
- **Pass:** both pass without removing anything the rules say must stay in (seat, firewall, harness, cables).

### T4.3c Harness installation (T.2)
- **Predicted** (`harness.py`):
  - lap belt at 55° (tabs on the lower side-impact tubes at x = 914);
  - anti-sub belt straight down (0° from vertical) to the floor-cross tab;
  - shoulder belts at −8°, 200 mm apart on the 1.5″ shoulder bar;
  - tabs: 3.2 mm 4130, 31.7 kN double tear-out.
- **Procedure:** with the driver belted in, measure each belt's side-view angle with the angle gauge.
- **Pass:**
  - lap 45–65°;
  - anti-sub ≤ 20° and in line with or ahead of the chest-to-groin line;
  - shoulder −20° to +10°;
  - lap belts pivot freely on shouldered bolts.

### T4.5 Rear wing: push test and DRS failsafe (IN.6.2, T.7)
- **Predicted** (`aero.py`): a 200 N push on the wing in any direction moves it at most 0.1 mm; the flap opens only with the button held and the brakes off.
- **Procedure:**
  1. Push the wing with a 200 N spring scale: up, down, fore, aft and sideways, at an endplate top and at the centre of the span. Measure the movement with a dial gauge on a stand.
  2. With the master switch on: hold the button, and the flap opens. Press the brake, and it shuts. Release the button, and it shuts. Hold the button and switch off the master switch, and it must shut on the spring.
  3. Measure every point of the wing and endplates against T.7.5–T.7.7 with the flap open and closed.
- **Pass:**
  - loaded deflection ≤ 25 mm and permanent set < 5 mm (IN.6.2.2);
  - the flap shuts in every failsafe case within 0.3 s;
  - top ≤ 1200 mm; edge radii 5 mm horizontal, 3 mm vertical (T.7.1.4).

### T4.4 Shutdown circuit and brake light
- **Procedure:** with the engine running at idle, check each of the following kills ignition and the fuel pump:
  - the primary master switch;
  - the cockpit E-stop;
  - the BOTS (T3.4);
  - the inertia switch, if fitted.

  Then check the brake light lights at ≤ 10 bar and is visible from 10 m in sunlight (T.3.4). It must be red on black, ≥ 15 cm², on the centreline.
- **Also:** with the engine off, open each series device (E-stop, BOTS, inertia switch) in turn and check that the kill relay drops; that ignition and fuel-pump feeds read 0 V; and that the brake light still works (`shutdown.py` netlist).
- **Pass:**
  - every device kills the engine within 1 s;
  - the relay drops for each device;
  - voltage at the pump and ignition is within 0.5 V of the battery (predicted 0.23 V drop);
  - the light passes.

### T4.5 Firewall and heat
- **Procedure:** after 10 minutes at fast idle, measure with the IR thermometer:
  - the engine side of the firewall;
  - the cockpit side;
  - the seat back;
  - the fuel cell.
- **Pass:**
  - cockpit side ≤ 60 °C;
  - no hot spot on the driver side above the exhaust.

---

## Stage 5: low-speed running (closed lot, cones, spotter, fire extinguishers on hand)

### T5.1 Gearing check (CRF450R 2018+ ratios from the service manual)
- **Predicted** at 5000 rpm (`powertrain.py`, CRF450R primary and gear ratios, 13/50 sprockets):

  | Gear | 1 | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|---|
  | Speed (km/h) | 24.8 | 31.0 | 37.2 | 43.7 | 50.7 |

- **Procedure:** hold 5000 rpm in 1st, 2nd and 3rd; log the speed with phone GPS.
- **Pass:** within ±5 % of the table. If not, the placeholder ratios are wrong: put the real ones in `powertrain.ENGINE`.
- **Later, once the engine is real:** time a 75 m standing start (D.9). The point-mass prediction is 4.48 s with DRS open (`lapsim.py`, lower bound; FSAE Michigan 2025 median 4.617 s). A real run 10–20 % slower is normal (launch, shifts, driver).

### T5.2 Shakedown and fastener check
- **Procedure:**
  - Drive 3 sessions of 10 minutes at 10, 25 and then 40 km/h maximum.
  - Before the first run, torque-stripe every critical fastener: suspension, steering, brakes, engine mounts, harness.
  - After each session, walk the car:
    - check the stripes;
    - check the chain slack (15–25 mm at mid-span);
    - look for leaks and rubbing.
  - Check the chain-to-frame gap under load (predicted 11 mm).
- **Pass:**
  - no stripe has moved;
  - no rubbing marks;
  - no leaks.

### T5.3 Ride frequency (bounce)
- **Predicted:**
  - natural frequency 3.0 Hz front / 2.6 Hz rear (`springs.py`);
  - with about 30 % damping, the observed decay frequency is about 2.86 / 2.48 Hz.
- **Procedure:**
  1. Tape the phone to the frame over the axle.
  2. Push down hard and release, 5 times per axle.
  3. Read the frequency from the spectrum.
- **Pass:**
  - within ±15 %;
  - settles in 1–2 cycles.

---

### T5.5 Wing downforce and DRS on track
- **Predicted** (`aero.py`, ASSUMED coefficients): at 60 km/h, 126 N of downforce closed and 43 N open. The rear axle gains about 1.2× the downforce, and the front loses the rest.
- **Procedure:**
  1. Put string potentiometers (or the rear shock sensors) on both rear shocks.
  2. Run steady 40, 50 and 60 km/h passes in both directions, flap closed, then open.
  3. Rear ride-height drop × rear ride rate gives the rear downforce.
  4. Also do a coast-down from 60 km/h in neutral with the flap closed and open; the difference is the wing drag.
- **Pass:** the flap stays still at speed (T.7.1.3b); DRS shuts every time the brakes are applied.
- **Use:** put the measured lift and drag coefficients in `aero.COEF`, and re-run `python report.py`. The lap sim and the axle split update from them.

## Stage 6: brake test (IN.14)

### T6.1 Four-wheel lock-up
- **Predicted:** lock all four at 567 N pedal on 1.5-grip tyres, 525 N on a 1.0-grip lot, with the fronts first at the 59 % front setting (`brakes.py`).
- **Procedure:**
  1. Build up in steps: 20, then 30, then 40 km/h, in a straight line with a spotter watching the wheels (or 4 chalk marks on the tyres).
  2. Log the pedal force with an in-car pedal load cell if available; otherwise log the line pressure.
  3. Adjust the balance bar until the fronts lock just before the rears.
- **Pass:**
  - all four lock;
  - the engine stays running (IN.14.2.2);
  - the car stays straight;
  - lock force ≤ 600 N.
- **Record** the lock pressure and the balance-bar setting, then put the implied grip back into `loads.py` `MU` if it is far from 1.5.

### T6.2 Rotor temperature
- **Predicted:** +31 °C front and +13 °C rear for one stop from 60 km/h. That is the full-speed prediction scaled by v²: 117 °C / 50 °C from 117 km/h.
- **Procedure:** measure the IR temperature of all four rotors immediately before and after one hard stop from 60 km/h.
- **Pass:**
  - within ±50 % of the prediction;
  - left and right within 20 %.

---

## Stage 7: skidpad and handling

### T7.1 Skidpad
- **Layout** (FSAE):
  - two 15.25 m inner-diameter circles, 18.25 m apart centre to centre;
  - a 3 m wide lane.
- **Predicted lap time on a line 1 m outside the inner cones** (R = 8.6 m): t = 2π√(R / (μg)).

  | Grip μ | 1.0 | 1.2 | 1.5 |
  |---|---|---|---|
  | Lap time (s) | 5.89 | 5.38 | 4.81 |

- **Procedure:** as in the reference plan: 2 laps right, then 2 laps left; time the 2nd and 4th laps. Add a 0.125 s penalty per cone. Do 4 runs per driver.
- **Pass:**
  - completes all laps with no spin;
  - left and right times within 5 %.
- **Same prediction** from `lapsim.py`: 5.12 s at μ 1.3 with the wing closed (R 8.62 m), the calibrated lap-sim grip; the table above is without the wing. FSAE Michigan 2025 median: 5.515 s.
- **Use:** implied lateral grip μ = 4π²R / (g t²). If it is much below 1.5, the design loads are conservative. If it is above, raise `MU` and re-check the frame.

### T7.2 Rear suspension durability
- **Procedure:** after every 30 minutes of running, dye-check the rear pushrod ends, the lower A-arm tabs and the spool-post welds. The rear pushrod is the most heavily loaded link: 6.1 kN peak, buckling FoS 4.4.
- **Pass:** no cracks.

---

## Results log (fill in; one row per run)

| Test | Date | Predicted | Measured (runs) | Pass? | Model input updated (real-to-sim loop, `SIM_TO_REAL.md`) |
|---|---|---|---|---|---|
| T1.1 mass | | 46.4 kg + 4 kg tabs | | | |
| T1.2 torsion | | 2004 N·m/deg FEA; expect 1300–1500 measured | | | |
| T2.2 camber gain F/R | | −0.72 / −0.75 °/25 mm | | | |
| T2.3 bump steer F/R | | ≤ 0.11° / 0.00° |
| T2.7 compliance toe at 1.5 g-equivalent side load F/R | | 0.10° in / 0.18° out | | | | | | |
| T2.4 motion ratio F/R | | 0.72 / 0.75 | | | |
| T2.5 wheel rate F/R | | 22.1 / 21.2 N/mm | | | |
| T2.6 free play | | < 7° | | | |
| T3.2 pressure @ 500 N F/R | | 74.0 / 36.3 bar | | | |
| T3.3 2000 N | | 296 / 145 bar, 19 mm | | | |
| T3.4 BOTS | | trips at 45 mm | | | |
| T4.1 mass / front % / CG | | 296 kg / 46 % / 340 mm | | | |
| T4.2 tilt 45° / 60° | | no leak / no roll | | | |
| T4.3 egress | | ≤ 5 s | | | |
| T5.1 speed @ 5000 rpm, 2nd | | 30.0 km/h | | | |
| T5.3 bounce F/R | | 2.86 / 2.48 Hz |
| T4.5 wing push (200 N) | | ≤ 0.1 mm, no set | | | |
| T5.5 wing downforce / DRS | | 126 N at 60 km/h closed; closes on brake | | | | | | |
| T6.1 lock force | | 567 N (μ 1.5), 525 N (μ 1.0) | | | |
| T6.2 rotor ΔT from 60 km/h | | 31 / 13 °C | | | |
| T7.1 skidpad lap | | 4.81–5.89 s | | | |
