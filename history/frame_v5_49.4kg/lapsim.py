"""Point-mass event simulation: FSAE acceleration (D.9, 75 m) and skidpad (D.10), with a drag estimate, plus how much
each second-order choice (mass, CG height, grip, drag) is worth. A point mass has no tyre model or driver: treat the
times as a lower bound for comparing design options, not as a prediction.

Acceleration: from rest, force = min(rear-tyre traction with load transfer, engine torque through the gearing)
minus drag and rolling resistance, integrated at 1 ms; SHIFT_S of zero drive per upshift.
Skidpad: steady speed v = sqrt(grip x g x R) on the driving-line radius; one timed lap.
Autocross: quasi-steady lap of a representative course built to the D.11.1.1 layout rules (straights, hairpins, constant
turns, slalom, chicane, ~0.8 km): corner speed limit sqrt(grip g R), then forward (drive-limited) and backward
(brake-limited) passes inside the friction circle.
Benchmark: FSAE Michigan 2025 results (fsaeonline.com): acceleration best 4.169 / 10th 4.324 / median 4.617 s; skidpad
5.080 / 5.287 / 5.515 s; autocross 48.878 / 52.019 / 55.725 s (different course from ours: indicative only).
Run: python lapsim.py
"""
import math
import loads as L
import mule as m
import powertrain as PT

RHO, CDA, CRR = 1.2, 1.0, 0.02      # kg/m^3; drag area m^2 (open-wheel car, no wings: ASSUMPTION ~0.8-1.1); rolling coeff
SHIFT_S = 0.10                      # s without drive per upshift (mechanical shift, no cut)
TORQUE_TO_RPM = 8500                # placeholder curve: peak torque flat to here, then constant power to redline
P_MAX = 33e3                        # W: power cap for the 20 mm IC.2 restrictor (ASSUMED ~45 hp; the flat 48 N*m curve alone gave
                                    # 43 kW, more than a restricted 450 makes - audit 1 Oct). Dyno the engine (TEST_PLAN T5.1)
ROT_MASS = 0.08                     # rotating parts (wheels, driveline, engine through the gearbox) as extra mass, fraction (ours)
GRIP = 1.2                          # lap-sim grip for a mule on used tyres, no aero (was 1.3: the 2025 FSAE Michigan skidpad winner implies ~1.34 (5.080 s));
                                    # loads.MU = 1.5 stays for strength, where more grip is the safe side
SKID_R = 15.25 / 2 + 1.0                      # m: car centre 1 m outside the inner cones (TEST_PLAN T7.1)
TARGETS = {"accel": 5.5, "skidpad": 6.0}      # s (ours: mule sanity targets, not performance goals; re-set 1 Oct 2026 when the
                                              # restrictor cap, rotating mass and used-tyre grip made the sim honest: 5.0 / 5.5 before)

def wing(state, on=True):
    """(downforce area CL*S, drag area CD*S) in m^2 of the rear wing, from aero.py; zero with on=False."""
    import aero
    if on is None: on = aero.FITTED          # default: the car as built (base mule: no wing)
    if not on: return 0.0, 0.0
    c = aero.COEF[state]; return c["cl"] * aero.area(), c["cd"] * aero.area()

def torque(rpm):
    E = PT.ENGINE
    tq = E["peak_torque"] if rpm <= TORQUE_TO_RPM else E["peak_torque"] * TORQUE_TO_RPM / rpm
    return min(tq, P_MAX / (rpm * 2 * math.pi / 60))       # restrictor power cap

def accel(mass=L.MASS, cg_h=L.CG_H, grip=GRIP, cda=CDA, dist=75.0, dt=1e-3, aero_on=None):
    """Time (s) and exit speed (km/h) over dist metres from rest, DRS open (low drag) the whole run."""
    cla, cdw = wing("open", aero_on); cda = cda + cdw
    E = PT.ENGINE; r = m.TIRE_R_LOADED / 1000; fin = PT.REAR_T / PT.FRONT_T
    g, x, v, t, shift_left = 0, 0.0, 0.0, 0.0, 0.0; a = 0.0
    while x < dist:
        ratio = E["primary"] * E["gears"][g] * fin
        rpm = max(v / r * ratio * 60 / (2 * math.pi), 3000)                # clutch slips below 3000 rpm at launch
        if rpm > E["redline"] and g < len(E["gears"]) - 1: g += 1; shift_left = SHIFT_S; continue
        drive = 0.0 if shift_left > 0 else torque(rpm) * ratio / r
        rear = mass * L.G * (1 - L.FRONT_SPLIT) + mass * a * cg_h / m.WHEELBASE + 0.5 * RHO * cla * v * v   # + wing (all on the rear)
        F = min(drive, grip * rear) - 0.5 * RHO * cda * v * v - CRR * mass * L.G
        a = F / (mass * (1 + ROT_MASS)); v = max(v + a * dt, 0.0); x += v * dt; t += dt; shift_left -= dt
    return t, v * 3.6

def skidpad(grip=GRIP, aero_on=None):
    """Steady lap with the flap closed: m v^2 / R = grip (m g + q CL S)."""
    cla, _ = wing("closed", aero_on)
    v = math.sqrt(grip * L.G * SKID_R / (1 - grip * RHO * cla * SKID_R / (2 * L.MASS)))
    return 2 * math.pi * SKID_R / v, v * 3.6

BENCH = {"accel": (4.169, 4.324, 4.617), "skidpad": (5.080, 5.287, 5.515), "autocross": (48.878, 52.019, 55.725)}  # best, 10th, median

def min_path_radius():
    """Tightest car-centre path radius (m) the steering allows: kinematic turning circle less half track and tyre."""
    import sideview
    return sideview.turning_circle() - (m.TRACK_F / 2 + m.TIRE_W / 2) / 1000

def course():
    """Representative autocross (length m, radius m or None for straight), D.11.1.1: straights <= 60 m, hairpins
    >= 9 m outside diameter (car centre ~3.5 m radius, or the car's own minimum if larger), 23-45 m constant
    turns, 7.6-12.2 m slalom (10 m spacing ~ 12.5 m path radius), chicanes, decreasing-radius turn."""
    hp = max(3.5, min_path_radius()); arc = lambda R, deg: (R * math.radians(deg), R)
    segs = [(60, None), arc(hp, 180), (45, None), arc(15, 90), (50, 12.5), (45, None), arc(20, 180), (30, None),
            arc(10, 45), arc(10, 45), (60, None), arc(hp, 180), arc(15, 270), (40, None), arc(12, 90), arc(20, 90),
            arc(10, 90), (45, None), arc(11.5, 180), (40, None), (50, 12.5), (45, None), arc(hp, 180)]
    used = sum(L_ for L_, _ in segs); return segs + [(max(800 - used, 0), None)]

def wheel_force(v):
    """Best drive force (N) at speed v over all gears below redline (no shift time: ponytail, add SHIFT_S if it matters)."""
    E = PT.ENGINE; r = m.TIRE_R_LOADED / 1000; fin = PT.REAR_T / PT.FRONT_T; best = 0.0
    for gr in E["gears"]:
        ratio = E["primary"] * gr * fin; rpm = max(v / r * ratio * 60 / (2 * math.pi), 3000)
        if rpm <= E["redline"]: best = max(best, torque(rpm) * ratio / r)
    return best

def autocross(grip=GRIP, mass=L.MASS, cda=CDA, ds=0.5, aero_on=None):
    """Lap time (s) and average speed (km/h) of course(). Wing: flap closed in corners and under braking, DRS open on
    straights while accelerating. Downforce adds to the tyre load (grip x (mg + downforce))."""
    clc, cdc = wing("closed", aero_on); clo, cdo = wing("open", aero_on)
    pts = []
    for L_, R in course():
        pts += [R] * max(int(L_ / ds), 1)
    vtop = PT.gearing()[1] / 3.6; mg = mass * L.G
    def corner_v(R):      # m v^2 / R = grip (m g + q CL S)
        den = 1 - grip * RHO * clc * R / (2 * mass)
        return vtop if den <= 0 else min(vtop, math.sqrt(grip * L.G * R / den))
    vlim = [vtop if R is None else corner_v(R) for R in pts]
    def ax_avail(v, R, cl):   # fore-aft grip (N) left after cornering, with downforce
        N = mg + 0.5 * RHO * cl * v * v; ay = 0 if R is None else mass * v * v / R
        return math.sqrt(max((grip * N) ** 2 - ay ** 2, 0.0))
    v = list(vlim); v[0] = 0.0
    for i in range(1, len(v)):   # forward: accelerate
        R = pts[i - 1]; cl, cd = (clo, cdo) if R is None else (clc, cdc)
        u = v[i - 1]; drag = 0.5 * RHO * (cda + cd) * u * u + CRR * mg
        rear_share = (mg * (1 - L.FRONT_SPLIT) + 0.5 * RHO * cl * u * u) / (mg + 0.5 * RHO * cl * u * u)
        F = min(wheel_force(u), rear_share * ax_avail(u, R, cl)) - drag
        v[i] = min(vlim[i], math.sqrt(max(u * u + 2 * F / (mass * (1 + ROT_MASS)) * ds, 0.0)))
    for i in range(len(v) - 2, -1, -1):   # backward: brake
        u = v[i + 1]; dec = (ax_avail(u, pts[i + 1], clc) + 0.5 * RHO * (cda + cdc) * u * u) / mass
        v[i] = min(v[i], math.sqrt(u * u + 2 * dec * ds))
    t = sum(2 * ds / (v[i] + v[i + 1]) for i in range(len(v) - 1) if v[i] + v[i + 1] > 0)
    return t, len(pts) * ds / t * 3.6

def sensitivity():
    """Change in acceleration and skidpad time for one step of each parameter (s)."""
    t0 = accel()[0]
    return {"+10 kg": accel(mass=L.MASS + 10)[0] - t0, "+25 mm CG": accel(cg_h=L.CG_H + 25)[0] - t0,
            "+0.1 drag area": accel(cda=CDA + 0.1)[0] - t0, "-0.1 grip (accel)": accel(grip=GRIP - 0.1)[0] - t0,
            "-0.1 grip (skidpad)": skidpad(GRIP - 0.1)[0] - skidpad()[0],
            "+10 kg (autocross)": autocross(mass=L.MASS + 10)[0] - autocross()[0],
            "-0.1 grip (autocross)": autocross(grip=GRIP - 0.1)[0] - autocross()[0]}

def drag_top_speed():
    """Speed (km/h) where drag + rolling use all the (placeholder) peak power."""
    P = min(PT.ENGINE["peak_torque"] * TORQUE_TO_RPM * 2 * math.pi / 60, P_MAX); lo, hi = 1.0, 100.0
    for _ in range(60):
        v = (lo + hi) / 2; (lo, hi) = (v, hi) if (0.5 * RHO * CDA * v**3 + CRR * L.MASS * L.G * v) < P else (lo, v)
    return v * 3.6

def checks():
    ta, va = accel(); ts, vs = skidpad(); tx, vx = autocross(); b = BENCH
    gain = {"accel": accel(aero_on=False)[0] - accel(aero_on=True)[0], "skidpad": skidpad(aero_on=False)[0] - skidpad(aero_on=True)[0],
            "autocross": autocross(aero_on=False)[0] - autocross(aero_on=True)[0]}
    return [
        (f"acceleration 75 m <= {TARGETS['accel']} s (ours; point mass, lower bound)", ta <= TARGETS["accel"], f"{ta:.2f} s, {va:.0f} km/h at the line (Michigan 2025 median {b['accel'][2]})"),
        (f"skidpad lap <= {TARGETS['skidpad']} s (ours; point mass at grip {GRIP})", ts <= TARGETS["skidpad"],
         f"{ts:.2f} s at {vs:.0f} km/h, R {SKID_R:.2f} m (Michigan 2025 median {b['skidpad'][2]})"),
        ("autocross average speed >= 40 km/h (low end of the D.11.1.1 course design speed)", vx >= 40,
         f"{tx:.1f} s, {vx:.0f} km/h on our 0.8 km course; hairpins at {max(3.5, min_path_radius()):.1f} m radius "
         f"(car minimum {min_path_radius():.1f} m) (Michigan 2025: best {b['autocross'][0]}, median {b['autocross'][2]} s, other course)"),
        ("drag does not limit top speed (drag-limited speed > geared top speed)", drag_top_speed() > PT.gearing()[1],
         f"drag-limited {drag_top_speed():.0f} vs geared {PT.gearing()[1]:.0f} km/h (drag area {CDA} m^2)"),
        ("bolt-on rear wing with DRS would not slow any event (vs no wing; ASSUMED coefficients, wing not fitted on the base mule)", min(gain.values()) >= 0,
         ", ".join(f"{k} {-v:+.2f} s" for k, v in gain.items()) + " with the wing"),
    ]

if __name__ == "__main__":
    for n, p, d in checks(): print(("PASS " if p else "FAIL ") + f"{n:66s} {d}")
    for k, v in sensitivity().items(): print(f"  {k:22s} {v:+.3f} s")
