"""Mass and CG budget: every significant item with its mass and centre position, summed to total mass, front split,
CG height and the rollover (tilt-test) angle. It then checks that the numbers every load case assumes (loads.MASS,
CG_H, FRONT_SPLIT, springs.UNSPRUNG) cover this budget.

Frame, pan, rotors and links are computed from the geometry. Everything else is an ESTIMATE for the part named:
weigh the real parts, enter the values here, and re-run pytest (TEST_PLAN T1.1 / T4.1 measure the result).
Run: python mass.py
"""
import math
import numpy as np
import mule as m
import powertrain as PT
import brakes as B
import uprights as U
import aero

DRIVER = dict(kg=80.0, dx=150.0, dy=150.0)     # typical team driver; whole-body CG ahead of / above the hip point (seated, 20 deg)
PER_CORNER = dict(wheel=4.5, tyre=5.0, upright=2.0, hub_bearings=1.8, caliper=0.6, studs=0.3, nuts=0.1)   # kg, estimates;
# upright 2.0 kg = fabricated steel (PARTS_LIST: first build), not the 1.2 kg 7075 part

def frame():
    kg = 0.0; mom = np.zeros(3)
    for a, b, s, _ in m.MEMBERS:
        mm = m.tube_props(s)[1] * math.dist(a, b) * m.STEEL_DENSITY
        kg += mm; mom += mm * (np.array(a) + np.array(b)) / 2
    return kg, mom / kg

def links_kg(axle):
    kg = 0.0
    for n, p, q, _ in m.susp_links(axle):
        od, t = m.PUSHROD_TUBE if n == "pushrod" else m.SUSP_TUBE
        kg += math.pi / 4 * (od**2 - (od - 2 * t) ** 2) * math.dist(p, q) * m.STEEL_DENSITY + 0.15   # + rod ends
    return kg

def rotor_kg(axle):
    return math.pi / 4 * (200.0**2 - B.ROTOR["id"] ** 2) * B.CALIPER[axle]["disc"] * B.ROTOR["rho"]

def items():
    """(name, kg, (x, y), sprung?) for the whole car with driver and full fuel."""
    fr_kg, fr_c = frame(); bx = PT.ENGINE["box"]
    out = [("frame (tube, from geometry)", fr_kg, (fr_c[0], fr_c[1]), True),
           ("weld, tabs, brackets (+8 % of tube)", 0.08 * fr_kg, (fr_c[0], fr_c[1]), True),
           ("engine CRF450R 2018+ (mass placeholder)", PT.ENGINE["mass"], ((bx[0] + bx[1]) / 2, (bx[2] + bx[3]) / 2), True),
           ("driver", DRIVER["kg"], (m.HIP[0] + DRIVER["dx"], m.HIP[1] + DRIVER["dy"]), True),
           ("fuel 6 L", 4.5, (m.X_MAIN - 13 - 115, 560.0), True),
           ("fuel cell, pump, lines", 2.5, (m.X_MAIN - 13 - 115, 560.0), True),
           ("spool, sprocket, carriers, chain", 8.0, (0.0, m.TIRE_OD / 2), True),
           ("CV half-shafts (2)", 4.0, (0.0, m.TIRE_OD / 2), True),
           ("radiator, fan, coolant", 5.0, (m.X_MAIN + 150, 350.0), True),
           ("exhaust and silencer", 5.0, (0.0, 450.0), True),
           ("battery, wiring, switches", 4.0, (m.X_MAIN + 60, 150.0), True),
           ("seat, harness, head restraint", 5.0, (m.HIP[0] - 60, 300.0), True),
           ("steering wheel, column, rack", 4.0, (m.RACK[0] - 150, 300.0), True),
           ("pedal box and master cylinders", 3.5, (m.X_PEDAL + 80, 200.0), True),
           ("rockers, shocks (4)", 4 * 1.2, (m.WHEELBASE / 2, 380.0), True),
           ("belly pan 1.6 mm 5052", belly_pan_kg(), (m.WHEELBASE / 2, m.Y_LOW - 13.5), True),
           ("firewall 1 mm aluminium", 1.5, (m.X_MAIN - 27, 380.0), True),
           # added 1 Oct 2026 (audit): items the budget was missing. No extinguisher: VE.2.3.2 forbids mounting one on the car.
           ("anti-intrusion plate 1.5 mm steel", aip_kg(), (m.IA[0], (m.Y_BH_BOT + m.Y_BH_TOP) / 2), True),
           ("impact attenuator (standard foam)", 0.5, ((m.IA[0] + m.IA[1]) / 2, (m.IA[2] + m.IA[3]) / 2), True),
           ("intake, airbox, 20 mm restrictor, throttle body", 2.0, ((bx[0] + bx[1]) / 2, bx[3] + 80), True),
           ("engine oil and coolant top-up (engine mass is dry)", 1.2, ((bx[0] + bx[1]) / 2, (bx[2] + bx[3]) / 2), True),
           ("chain guard / scatter shield (T.5.2.7)", 1.0, (150.0, m.TIRE_OD / 2), True),
           ("brake lines and fluid", 0.6, (m.WHEELBASE / 2, 200.0), True),
           ("bodywork: nose and side panels (fibreglass)", 3.0, (m.WHEELBASE * 0.6, 400.0), True)] + [(n, kg, c, True) for n, kg, c in aero.mass_items()]
    for axle, x in (("front", m.WHEELBASE), ("rear", 0.0)):
        corner = sum(PER_CORNER.values()) + rotor_kg(axle) + links_kg(axle) / 2
        out.append((f"{axle} corners x2 (wheel, tyre, upright, hub, rotor, caliper, half links)", 2 * corner, (x, m.TIRE_OD / 2), False))
        out.append((f"{axle} links inboard halves x2", links_kg(axle), (x - (120 if axle == "front" else -100), 250.0), True))
    return out

def aip_kg():
    """F.8.4 anti-intrusion plate over the front bulkhead, 1.5 mm steel."""
    return (m.Y_BH_TOP - m.Y_BH_BOT + 25.4) * (2 * m.Z_BH + 25.4) * 1.5 * m.STEEL_DENSITY

def belly_pan_kg():
    outline = [m.N[k] for k in ("r_bot", "rr_bot", "mh_bot", "fh_bot", "ring_bot", "bh_bot")]
    xs = [p[0] for p in outline]; zs = [p[2] + m.rad("Lower side impact") for p in outline]
    area = 2 * sum((xs[i] - xs[i + 1]) * (zs[i] + zs[i + 1]) / 2 for i in range(len(xs) - 1))
    return abs(area) * m.PAN_T * 2.68e-6

def summary():
    it = items(); kg = sum(i[1] for i in it)
    x = sum(i[1] * i[2][0] for i in it) / kg; y = sum(i[1] * i[2][1] for i in it) / kg
    unsprung = sum(i[1] for i in it if not i[3]) / 4
    tilt = min(math.degrees(math.atan(tr / 2 / y)) for tr in (m.TRACK_F, m.TRACK_R))
    return dict(kg=kg, front=x / m.WHEELBASE, cg_h=y, unsprung=unsprung, tilt=tilt)

def checks():
    import loads as L, springs
    s = summary()
    return [
        ("loads.MASS covers the budget (>= total)", L.MASS >= s["kg"], f"budget {s['kg']:.0f} kg vs assumed {L.MASS:.0f}"),
        ("loads.CG_H covers the budget (>= CG height)", L.CG_H >= s["cg_h"], f"budget {s['cg_h']:.0f} mm vs assumed {L.CG_H:.0f}"),
        ("loads.FRONT_SPLIT within 3 % of the budget", abs(L.FRONT_SPLIT - s["front"]) <= 0.03, f"budget {100 * s['front']:.1f} % vs assumed {100 * L.FRONT_SPLIT:.0f} %"),
        ("springs.UNSPRUNG within 1.5 kg of the budget", abs(springs.UNSPRUNG - s["unsprung"]) <= 1.5, f"budget {s['unsprung']:.1f} kg vs assumed {springs.UNSPRUNG:.1f}"),
        ("tilt test IN.11.2.2: rollover angle >= 60 deg", s["tilt"] >= 60, f"{s['tilt']:.1f} deg (CG {s['cg_h']:.0f} mm)"),
    ]

if __name__ == "__main__":
    for n, kg, (x, y), sp in sorted(items(), key=lambda i: -i[1]):
        print(f"{kg:6.1f} kg  x={x:6.0f}  y={y:4.0f}  {'sprung  ' if sp else 'unsprung'}  {n}")
    s = summary(); print(f"TOTAL {s['kg']:.1f} kg, front {100 * s['front']:.1f} %, CG height {s['cg_h']:.0f} mm, unsprung {s['unsprung']:.1f} kg/corner")
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:50s} {d}")
    assert all(p for _, p, _ in res), "mass budget check failed"
