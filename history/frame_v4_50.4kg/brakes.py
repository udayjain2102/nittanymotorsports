"""Brakes and pedal box: caliper/master-cylinder sizing, balance-bar bias, lock-up pedal force, pedal travel and
BOTS position, rotor heat per stop, pedal/pivot/balance-bar strength and the frame under the T.3.2.2 2000 N pedal load.

Layout (side view, X fwd, Y up): floor-hinged brake pedal, pivot on a base plate bolted to the two pedal-box
cross tubes (mule.PB_X). The pedal leans back TILT from vertical; the balance bar sits in the pedal H_MC above the
pivot and pushes two forward-facing Tilton 78 master cylinders: FRONT circuit and REAR circuit, each with its own
reservoir (T.3.1.3/4). Throttle: mechanical cable (IC.3.3) -> no APPS/BSPD (those are ETC-only, IC.4).
Catalogue values (piston sizes, MC bores/stroke) from Wilwood/Tilton listings; pad mu, compliance and the
hydraulic pressure limit are ASSUMPTIONS - verify/measure. Run: python brakes.py
"""
import math
import numpy as np
import mule as m
import loads as L
import fea

IN = 25.4
def area(d): return math.pi / 4 * d * d

CALIPER = {"front": dict(name="Wilwood GP200, 2 x 1.25in opposed", piston=1.25 * IN, disc=0.25 * IN),
           "rear":  dict(name="Wilwood PS-1, 2 x 1.00in opposed",  piston=1.00 * IN, disc=0.20 * IN)}
PAD_MU, PAD_H = 0.40, 25.0           # pad friction (assumption: typical race pad cold-warm), pad radial height mm
R_EFF = 200.0 / 2 - PAD_H / 2        # rotor OD 200 (uprights.ROTOR_OD); effective radius at pad centre
MC_BORE = {"front": 0.625 * IN, "rear": 0.8125 * IN}  # Tilton 78-625 / 78-812 (rear up from 0.750 when the budget went 48 % front, 1 Oct)
MC_STROKE, MC_ROD, MC_BODY = 1.1 * IN, 25.0, 115.0     # stroke; clevis -> mount flange; flange -> front incl. fittings
RATIO = 4.5                          # pedal ratio (pad height / balance-bar height); 4.5 not 5 to cut the 2000 N pressure
H_PAD, TILT = 170.0, 10.0            # pad centre above the pivot, mm; pedal lean back from vertical, deg
H_MC = H_PAD / RATIO
PIVOT_UP = 25.0                      # pivot above the base plate top
SPLIT_RANGE = (0.40, 0.60)           # balance-bar adjuster range, fraction of pedal force to the front MC
F_LOCK_MAX = 700.0                   # N (ours): pedal force to lock all four at the design grip, a firm race stop.
                                     # Front lock pressure is fixed by the GP200 piston area; a 4-piston GP320 needs a >= 229 mm
                                     # rotor that does not fit the 13 in rim, so lower 2000 N pressure costs pedal force.
F_TEST = 2000.0                      # T.3.2.2
HYD_LIMIT = 300.0                    # bar at 2000 N: ASSUMED proof rating, UNVERIFIED - get MC, caliper and hose ratings in writing
OPERATING_MAX = 2000 / 14.504        # bar: Wilwood recommended maximum operating pressure, 2000 psi (wilwood.com ds793)
KNOCKBACK, COMPLIANCE = 0.25, 5.0    # mm pad clearance per piston; mm^3 per bar per circuit. ESTIMATE (audit 1 Oct: 0.6 was
                                     # far too stiff): pad compression ~0.1 mm/100 bar on 4 pistons + caliper flex + hoses. Measure (T3.3)
BOTS_TRAVEL = 55.0                   # BOTS trips at this pedal-pad travel, mm (55: still >= 10 mm clear at compliance 8)
PEDAL = dict(Sy=276.0, b=12.0, h=45.0, bore=19.05)   # 6061-T6 blade (Z-thick b, X-deep h), balance-bar sleeve bore
PIVOT = dict(d=8.0, Sy=940.0)        # M8 10.9 shoulder bolt, double shear
BAR = dict(d=5 / 8 * IN, Sy=655.0, e=25.0)   # 5/8in 4140 Q&T balance bar; MC clevises at +/-e from the pedal centre
ROTOR = dict(id=110.0, rho=7.85e-6, c=460.0, dT_max=150.0)  # steel rotor annulus; single stop from top speed
BRAKE_Z, THROTTLE_Z = -45.0, 65.0    # pedal centre planes (brake left of throttle)

def axle_loads(mu):
    """Front/rear axle normal load (N) braking at mu g."""
    w = L.MASS * L.G; f = w * (L.FRONT_SPLIT + mu * L.CG_H / m.WHEELBASE); return f, w - f

def lock_pressure(mu):
    """Line pressure (bar) per circuit to lock the wheels on that axle at mu."""
    out = {}
    for ax, Fz in zip(("front", "rear"), axle_loads(mu)):
        T = mu * Fz / 2 * m.TIRE_OD / 2                         # N*mm per wheel
        out[ax] = T / (2 * PAD_MU * area(CALIPER[ax]["piston"]) * R_EFF) * 10
    return out

def lock_point(mu):
    """Balance split that locks both axles together, and the pedal force (N) to do it."""
    p = lock_pressure(mu); Ff, Fr = (p[a] / 10 * area(MC_BORE[a]) for a in ("front", "rear"))
    return Ff / (Ff + Fr), (Ff + Fr) / RATIO

def lock_force(mu, split):
    """Pedal force (N) to lock all four wheels at mu with the balance bar at split (the later axle governs)."""
    p = lock_pressure(mu)
    return max(p["front"] / 10 * area(MC_BORE["front"]) / split, p["rear"] / 10 * area(MC_BORE["rear"]) / (1 - split)) / RATIO

def pressures(F_pedal, split):
    Fb = F_pedal * RATIO
    return {"front": Fb * split / area(MC_BORE["front"]) * 10, "rear": Fb * (1 - split) / area(MC_BORE["rear"]) * 10}

def mc_stroke(ax, p_bar):
    """MC displacement (mm): take up pad clearance on all pistons of the circuit, then fluid compliance."""
    V = 2 * 2 * area(CALIPER[ax]["piston"]) * KNOCKBACK + COMPLIANCE * p_bar
    return V / area(MC_BORE[ax])

def pedal_travel(split, xf, xr):
    """Pad travel from MC strokes: balance-bar centre moves split*xf + (1-split)*xr (lever rule)."""
    return RATIO * (split * xf + (1 - split) * xr)

def geometry():
    """Side-view stack-up: pivot, balance bar, MC front end (X), pad height (Y)."""
    s, c = math.sin(math.radians(TILT)), math.cos(math.radians(TILT))
    y_base = m.N["pb0"][1] + m.rad("Pedal box cross (rear)") + 6.0   # cross tube top + 6 mm base plate
    x_piv = m.X_PEDAL + H_PAD * s; y_piv = y_base + PIVOT_UP
    x_bar = x_piv - H_MC * s
    return dict(piv=(x_piv, y_piv), bar=(x_bar, y_piv + H_MC * c), pad=(m.X_PEDAL, y_piv + H_PAD * c),
                mc_front=x_bar + MC_ROD + MC_BODY, y_base=y_base, n=np.array([c, -s, 0.0]))

def rotor_dT():
    import powertrain as PT
    v = PT.gearing()[1] / 3.6; E = 0.5 * L.MASS * v * v
    split_f = axle_loads(L.MU)[0] / (L.MASS * L.G)             # braking energy shared like the axle loads at the limit
    out = {}
    for ax, sh in (("front", split_f), ("rear", 1 - split_f)):
        mass = math.pi / 4 * (200.0**2 - ROTOR["id"]**2) * CALIPER[ax]["disc"] * ROTOR["rho"]
        out[ax] = sh / 2 * E / (mass * ROTOR["c"])
    return out

def strength(split):
    """FoS at F_TEST: pedal blade at the balance-bar section, pivot bolt (double shear), balance bar bending."""
    Fb = F_TEST * RATIO
    M = F_TEST * (H_PAD - H_MC)                                  # N*mm at the balance-bar section
    I = PEDAL["b"] * (PEDAL["h"]**3 - PEDAL["bore"]**3) / 12   # blade with the sleeve bore through it
    blade = PEDAL["Sy"] / (M * PEDAL["h"] / 2 / I)
    pivot = 0.577 * PIVOT["Sy"] / ((Fb - F_TEST) / (2 * area(PIVOT["d"])))
    Mb = split * (1 - split) * 2 * BAR["e"] * Fb               # bar pivots at the split point between clevises
    bar = BAR["Sy"] / (Mb * 32 / (math.pi * BAR["d"]**3))
    return dict(blade=blade, pivot=pivot, bar=bar)

def frame_2000N():
    """Foot pushes the pad (normal to the pedal) with F_TEST; the box reacts at its 4 bolt points (min-norm split);
    the driver's back reacts it into the seat mounts (main hoop base and mid nodes). Inertia relief balances the rest."""
    g = geometry(); fr = fea.Frame(m.MEMBERS)
    F = F_TEST * g["n"]; P = np.array([g["pad"][0], g["pad"][1], BRAKE_Z])
    pts = [np.array(m.N[f"pb{i}m"], float) * np.array([1, 1, s]) for i in (0, 1) for s in (1, -1)]
    A = np.zeros((6, 12))
    for i, p in enumerate(pts):
        for k in range(3):
            e = np.zeros(3); e[k] = 1; A[:3, 3 * i + k] = e; A[3:, 3 * i + k] = np.cross(p - P, e)
    f = np.linalg.pinv(A) @ np.r_[-F, np.zeros(3)]            # box mounts push the box with f
    loads = {}
    for i, p in enumerate(pts):
        k = fr.find(p); loads[k] = loads.get(k, 0) - f[3 * i:3 * i + 3]
    seat = [m.N["mh_bot"], m.mir(m.N["mh_bot"]), m.N["mh_sis"], m.mir(m.N["mh_sis"])]
    for p in seat:
        k = fr.find(p); loads[k] = loads.get(k, 0) - F / len(seat)
    _, st = fr.solve(*fea.inertia_relief(fr, loads)); j = int(np.argmax(st))
    return fea.SY_WELD / st[j], fr.el[j][3]

def design_split():
    """Balance setting: lock both axles together at the design grip, then 2 % more front so the fronts lock first."""
    return lock_point(L.MU)[0] + 0.02

def checks():
    s = design_split(); s_hi, _ = lock_point(L.MU); s_lo, _ = lock_point(1.0); F_lock = lock_force(L.MU, s)
    p_lock = lock_pressure(L.MU); p_test = pressures(F_TEST, s)
    x_f, x_r = mc_stroke("front", p_test["front"]), mc_stroke("rear", p_test["rear"])
    t_norm = pedal_travel(s, x_f, x_r)
    t_front_fail = pedal_travel(s, MC_STROKE, x_r); t_rear_fail = pedal_travel(s, x_f, MC_STROKE)
    g = geometry(); fos = strength(s); dT = rotor_dT(); ffos, where = frame_2000N()
    ang = math.degrees(t_front_fail / H_PAD)
    return [
        (f"lock all four at mu {L.MU} with <= {F_LOCK_MAX:.0f} N (T.3.1.2c)", F_lock <= F_LOCK_MAX,
         f"{F_lock:.0f} N at split {s:.3f} (front {p_lock['front']:.0f} bar, rear {p_lock['rear']:.0f} bar)"),
        ("balance split for mu 1.0-1.5 inside the adjuster", SPLIT_RANGE[0] <= min(s_lo, s_hi) and max(s_lo, s_hi) + 0.02 <= SPLIT_RANGE[1],
         f"{s_lo:.3f}-{s_hi:.3f} (+0.02 front margin), adjuster {SPLIT_RANGE[0]:.2f}-{SPLIT_RANGE[1]:.2f}"),
        (f"lock-up pressure <= Wilwood max operating {OPERATING_MAX:.0f} bar (2000 psi)", max(p_lock.values()) <= OPERATING_MAX,
         f"front {p_lock['front']:.0f}, rear {p_lock['rear']:.0f} bar"),
        (f"line pressure at {F_TEST:.0f} N <= {HYD_LIMIT:.0f} bar (T.3.2.2; ASSUMED proof rating, OPEN until written ratings)", max(p_test.values()) <= HYD_LIMIT,
         f"front {p_test['front']:.0f}, rear {p_test['rear']:.0f} bar: above the 138 bar operating rating, so the parts' proof rating decides"),
        ("MC stroke at 2000 N <= 50 % of stroke", max(x_f, x_r) <= 0.5 * MC_STROKE, f"front {x_f:.1f}, rear {x_r:.1f} of {MC_STROKE:.1f} mm"),
        ("BOTS: >= 10 mm beyond pedal travel at 2000 N", BOTS_TRAVEL >= t_norm + 10, f"trip {BOTS_TRAVEL:.0f} vs {t_norm:.1f} mm"),
        ("BOTS: trips >= 10 mm before either circuit's MC bottoms", BOTS_TRAVEL <= min(t_front_fail, t_rear_fail) - 10,
         f"front lost {t_front_fail:.0f}, rear lost {t_rear_fail:.0f} mm"),
        ("pedal swing at a lost circuit <= 30 deg", ang <= 30, f"{ang:.0f} deg"),
        ("pedal blade FoS >= 1.5 at 2000 N", fos["blade"] >= 1.5, f"{fos['blade']:.2f}"),
        ("pivot bolt FoS >= 1.5 at 2000 N", fos["pivot"] >= 1.5, f"{fos['pivot']:.2f}"),
        ("balance bar FoS >= 1.5 at 2000 N", fos["bar"] >= 1.5, f"{fos['bar']:.2f}"),
        ("frame FoS >= 1.2 at 2000 N pedal load", ffos >= 1.2, f"{ffos:.2f} ({where})"),
        ("MC front inside PEDAL_BOX_LEN (F.8.6.3 stack-up)", g["mc_front"] <= m.X_PEDAL + m.PEDAL_BOX_LEN,
         f"{g['mc_front']:.0f} vs {m.X_PEDAL + m.PEDAL_BOX_LEN:.0f}"),
        ("rotor temperature rise, one stop from top speed <= 150 C", max(dT.values()) <= ROTOR["dT_max"],
         f"front {dT['front']:.0f}, rear {dT['rear']:.0f} C"),
    ]

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:62s} {d}")
    print(f"design balance: {design_split():.3f} of pedal force to the front MC; pedal ratio {RATIO}")
    assert all(p for _, p, _ in res), "brake check failed"
