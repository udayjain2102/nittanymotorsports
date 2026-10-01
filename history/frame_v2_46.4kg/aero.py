"""Rear wing with a moveable flap (DRS): geometry inside the T.7 rules, aero forces, axle split, mounting-strut FEA
(IN.6.2 push test and the top-speed load), flap servo sizing, and the DRS control logic.

Wing: two elements (main plane + flap) between flat endplates, on two vertical struts from the rear-bulkhead top nodes,
braced forward to the main hoop top. The flap pivots at 30 % of its chord, near its centre of pressure. A servo opens it (low drag) only while the
driver holds the DRS button and the brakes are off; a return spring shuts it (high downforce) on button release,
on brake, or on any loss of power, so a failure leaves the car with full downforce.

AERO COEFFICIENTS ARE ASSUMPTIONS (typical two-element FSAE wing with endplates, aspect ratio ~2): replace them with
CFD or with the test in TEST_PLAN T5.5 before relying on them. Axes as mule.py (X fwd, Y up, Z right).
Run: python aero.py
"""
import math
import numpy as np
import mule as m
import fea

RHO = 1.2
MAIN = dict(chord=300.0, angle=10.0)                  # mm; deg, trailing edge up (inverted wing)
FLAP = dict(chord=170.0, closed=40.0, open=10.0, pivot=0.30, overlap=20.0, gap=12.0)   # angle to horizontal, deg
LE = (-64.4, 1000.0)                                  # main-plane leading edge (x, y), mm: open-flap TE stays inside T.7.5b
HALF_ZONE = m.TRACK_R / 2 - m.TIRE_W / 2              # T.7.6.3: inboard of the rear tyres' inner faces
ENDPLATE_T = 3.0
SPAN = 2 * (HALF_ZONE - 17.0)                         # between the endplates, 17 mm clear of the zone edge each side
COEF = {"closed": dict(cl=1.6, cd=0.30), "open": dict(cl=0.55, cd=0.10)}   # ASSUMPTIONS, on planform area
CP = 0.35                                             # centre of pressure, fraction of the total chord from the LE
FLAP_SHARE = 0.4                                      # fraction of the wing load carried by the flap (closed)
FLAP_CP_ERR = 0.10                                    # flap CP may sit this fraction of flap chord from the pivot
WING_KG, SERVO_KG = 3.5, 0.3                          # carbon/foam main + flap + endplates; servo and linkage (ESTIMATES)
STRUT = "C"                                           # 1.0 x 0.049 in 4130 struts and braces
SERVO_NM = 15.0                                       # servo stall torque, N*m (~150 kg*cm class, 12 V): buy at least this
SPRING_MARGIN = 1.3                                   # return spring torque / worst aero moment trying to open the flap

def section(state="closed"):
    """2D points (x, y): main LE, main TE, flap LE, flap pivot, flap TE for the flap state."""
    a = math.radians(MAIN["angle"]); le = np.array(LE)
    te = le + MAIN["chord"] * np.array([-math.cos(a), math.sin(a)])
    fle0 = te + np.array([FLAP["overlap"], FLAP["gap"]])            # flap LE, closed
    fc = math.radians(FLAP["closed"]); d0 = np.array([-math.cos(fc), math.sin(fc)])
    pivot = fle0 + FLAP["pivot"] * FLAP["chord"] * d0
    f = math.radians(FLAP[state]); d = np.array([-math.cos(f), math.sin(f)])
    fle = pivot - FLAP["pivot"] * FLAP["chord"] * d
    return dict(le=le, te=te, fle=fle, pivot=pivot, fte=fle + FLAP["chord"] * d)

def area():
    return SPAN * (MAIN["chord"] + FLAP["chord"]) / 1e6          # planform, m^2

def top_speed():
    import powertrain
    return powertrain.gearing()[1] / 3.6

def forces(v=None, state="closed"):
    """(downforce N, drag N) at v m/s (default: geared top speed)."""
    v = top_speed() if v is None else v; q = 0.5 * RHO * v * v
    c = COEF[state]; return q * area() * c["cl"], q * area() * c["cd"]

def cp_point(state="closed"):
    s = section(state); return s["le"] + CP * (s["fte"] - s["le"])

def axle_split(v=None, state="closed"):
    """Change in (front, rear) axle load, N (+ = more load), from the wing's downforce and drag."""
    L_, D = forces(v, state); x, y = cp_point(state)
    dF = (L_ * x - D * y) / m.WHEELBASE                          # moments about the rear contact patch
    return dF, L_ - dF

def front_static():
    import loads as L
    return L.MASS * L.G * L.FRONT_SPLIT

def rules():
    """T.7 geometry checks at both flap states: [(name, ok, detail)]."""
    rear_tyre = -m.TIRE_OD / 2
    xs, ys = [], []
    for st in ("closed", "open"):
        s = section(st)
        for p in s.values():
            xs.append(p[0]); ys.append(p[1])
    ep_top, ep_rear = max(ys) + 15, min(xs) - 5                  # endplates wrap the profiles with 15 / 5 mm margin
    head_plane = m.X_MAIN + 13
    return [
        ("T.7.3.3 wing is behind the head-restraint plane (inside the rear aero zone)", max(xs) + 5 < head_plane, f"front {max(xs) + 5:.0f} vs plane x {head_plane:.0f}"),
        ("T.7.5b no more than 250 mm behind the rear tyres", ep_rear >= rear_tyre - 250, f"rear edge x {ep_rear:.0f} vs limit {rear_tyre - 250:.0f}"),
        ("T.7.6.3 inboard of the rear tyres' inner faces", SPAN / 2 + ENDPLATE_T <= HALF_ZONE, f"endplate outer face {SPAN / 2 + ENDPLATE_T:.0f} vs {HALF_ZONE:.0f} mm"),
        ("T.7.7.1a no higher than 1200 mm in either flap position", ep_top <= 1200, f"{ep_top:.0f} mm"),
    ]

def strut_members():
    """Wing-mount members (a, b, size, role): struts from the rear-bulkhead top nodes, a wing spar across their tops,
    braces forward to the main-hoop top, and one diagonal in the strut plane for side load."""
    x, top = -300.0, 1030.0
    out = []
    for sg in (1, -1):
        b, t = m.N["r_top"], (x, top, sg * 200.0)
        b = (b[0], b[1], sg * b[2]); h = m.N["mh_top"]; h = (h[0], h[1], sg * h[2])
        out += [(b, t, STRUT, "Wing strut"), (t, h, STRUT, "Wing brace to main hoop")]
    out += [((x, top, 200.0), (x, top, -200.0), "H", "Wing spar (main-plane mount)"),
            ((x, top, 200.0), (m.N["r_top"][0], m.N["r_top"][1], -m.N["r_top"][2]), STRUT, "Wing strut diagonal")]
    return out

def _solve(point_loads):
    fr = fea.Frame(m.MEMBERS + strut_members())
    sup = {fr.find(p): range(3) for p in fea.pickups(["r_lsus", "r_sus", "rr_lsus", "rr_sus", "ring_lsus", "ring_sus", "bh_lsus", "bh_sus"])}
    loads = {}
    for p, F in point_loads:
        k = fr.find(p); loads[k] = loads.get(k, 0) + np.asarray(F, float)
    u, st = fr.solve(loads, sup)
    return fr, u, st

def push_test(F=200.0):
    """IN.6.2.2: worst deflection (mm) of a wing mount under F N in each of 6 directions at a strut top."""
    worst = 0.0; p = (-300.0, 1030.0, 200.0)
    for d in np.vstack([np.eye(3), -np.eye(3)]):
        fr, u, _ = _solve([(p, F * d)]); k = fr.find(p)
        worst = max(worst, np.linalg.norm(u[6 * k:6 * k + 3]))
    return worst

def top_speed_fos(bump_g=3.0):
    """Safety factor (welded yield) of the whole structure with the closed-flap load at top speed x 1.5 plus the wing
    mass at bump_g, split over the two strut tops."""
    L_, D = forces(state="closed"); Wm = (WING_KG + SERVO_KG) * 9.81 * bump_g
    F = np.array([-1.5 * D, -1.5 * L_ - Wm, 0.0]) / 2
    _, _, st = _solve([((-300.0, 1030.0, 200.0), F), ((-300.0, 1030.0, -200.0), F)])
    return fea.SY_WELD / st.max()

F_MIN_HZ = 25.0                                        # wing-on-mount first mode above wheel hop (~12-18 Hz) (ours)

def mount_frequency():
    """Lowest natural frequency (Hz) of the wing mass on its mounts: stiffness from equal loads at both strut tops,
    in each axis, with the wing as a rigid lumped mass."""
    p = (-300.0, 1030.0, 200.0); kmin = 1e18
    for d in np.eye(3):
        fr, u, _ = _solve([(p, 100 * d), ((p[0], p[1], -p[2]), 100 * d)]); k = fr.find(p)
        kmin = min(kmin, 200 / abs(np.dot(u[6 * k:6 * k + 3], d)))
    return math.sqrt(kmin * 1000 / (WING_KG + SERVO_KG)) / (2 * math.pi)

def hinge_moments(v=None):
    """(worst aero moment about the flap pivot N*m, spring torque N*m, servo torque needed N*m)."""
    L_, _ = forces(v, "closed")
    m_aero = FLAP_SHARE * L_ * FLAP_CP_ERR * FLAP["chord"] / 1000
    spring = SPRING_MARGIN * m_aero
    return m_aero, spring, 2.0 * (spring + m_aero)

def drs_open(button, brake, powered=True):
    """Flap command: open only while the button is held, the brakes are off and the servo has power."""
    return bool(button and not brake and powered)

def strut_kg():
    return sum(fea.props(s)[0] * math.dist(a, b) for a, b, s, _ in strut_members()) * m.STEEL_DENSITY

def mass_items():
    """(name, kg, (x, y)) for mass.py."""
    s = section("closed"); c = (s["le"] + s["fte"]) / 2
    return [("rear wing (main, flap, endplates)", WING_KG, (c[0], c[1])),
            ("DRS servo, spring, linkage", SERVO_KG, (s["pivot"][0], s["pivot"][1])),
            ("wing struts and braces (steel)", strut_kg(), (-300.0 + 400, 900.0))]

def checks():
    v60 = 60 / 3.6; Lc, Dc = forces(v60, "closed"); Lo, Do = forces(v60, "open")
    fF, fR = axle_split(); ma, sp, need = hinge_moments(); push = push_test(); fos = top_speed_fos()
    out = rules() + [
        ("IN.6.2.2 200 N push on a wing mount deflects <= 25 mm (any direction)", push <= 25, f"{push:.1f} mm"),
        (f"T.7.1.3b wing does not oscillate: mount frequency >= {F_MIN_HZ:.0f} Hz (ours, above wheel hop)", mount_frequency() >= F_MIN_HZ,
         f"{mount_frequency():.0f} Hz"),
        ("wing mounts: top-speed load x 1.5 + 3 g bump, FoS >= 1.5 vs welded yield", fos >= 1.5, f"FoS {fos:.2f}"),
        (f"flap servo stall torque >= 2 x (spring + aero moment) at top speed", SERVO_NM >= need,
         f"servo {SERVO_NM:.0f} vs {need:.1f} N*m (aero {ma:.1f}, spring {sp:.1f})"),
        ("DRS reduces wing drag >= 50 %", Do <= 0.5 * Dc,
         f"at 60 km/h: closed {Lc:.0f} N down / {Dc:.0f} N drag, open {Lo:.0f} / {Do:.0f} N (ASSUMED coefficients)"),
        ("front axle keeps >= 90 % of its static load at top speed (ours: limits high-speed understeer)", 1 + fF / front_static() >= 0.9,
         f"front {fF:+.0f} N ({100 * fF / front_static():+.0f} %), rear {fR:+.0f} N at {top_speed() * 3.6:.0f} km/h, closed flap"),
    ]
    return out

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:74s} {d}")
    print(f"planform {area():.3f} m^2, struts {strut_kg():.1f} kg; section closed {({k: tuple(np.round(v)) for k, v in section().items()})}")
    assert all(p for _, p, _ in res), "aero check failed"
