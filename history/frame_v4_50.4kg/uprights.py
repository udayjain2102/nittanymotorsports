"""Uprights and hubs: bearing loads/life, hub shaft, upright arms, wheel studs, rotor/caliper packaging.

Layout per corner (hub axis = Z through the wheel centre W):
  wheel face (hub flange) at W + WHEEL_OFFSET, rotor bolted just inboard of it, then the upright:
  outboard bearing, inboard bearing (spacing BRG_SPACING), a hub that rotates in them (rear: splined for the CV).
Upright arms run from the bearing housing to the ball joints, steering/toe arm and pushrod pickup.
Loads: loads.cases() at the contact patch + loads.link_forces() at the hardpoints; rear drive torque
is traction-limited. Bearing ratings are catalogue values for the named part: VERIFY with the supplier.
Run: python uprights.py
"""
import math
import numpy as np
import mule as m
import loads as L

WHEEL_OFFSET = 25.0    # hub mounting face outboard of the wheel centre plane, mm (13" x 7" FSAE wheel)
ROTOR_GAP = 20.0       # rotor plane inboard of the hub face
BRG_TO_ROTOR = 29.0    # outboard bearing centre inboard of the rotor plane (6209: 27 left 9.5 mm to the rotor)
BRG_SPACING = 55.0     # bearing centre-to-centre
BEARING = dict(name="SKF 6209-2RS1 (45x85x19 deep groove)", d=45.0, D=85.0, B=19.0, C=35.1e3, C0=21.6e3)  # N, SKF catalogue (6009: s0 1.46 at CG 330)
HUB = dict(od=45.0, id=30.0, Sy=655.0)          # hub shaft through the bearings: 4140 Q&T, bore for the CV spline
UPRIGHT = dict(Sy=503.0, w=28.0, t=18.0, wall=8.0)   # 7075-T6 machined; arm section w x t (mm); housing wall
ROTOR_OD, CALIPER_H, RIM_BARREL_R = 200.0, 45.0, 155.0   # mm
STUDS = dict(n=4, pcd=100.0, As=84.3, Sp=830.0, mu=0.15, preload=0.7)   # M12x1.5 class 10.9, 4x100
LIFE_KM, LIFE_SF = 2000.0, 3.0                    # mule running, and margin on L10

def geom(axle):
    x = m.WHEELBASE if axle == "front" else 0.0; wz = (m.TRACK_F if axle == "front" else m.TRACK_R) / 2
    r = m.TIRE_OD / 2; face = wz + WHEEL_OFFSET; rot = face - ROTOR_GAP
    zo = rot - BRG_TO_ROTOR; zi = zo - BRG_SPACING
    return dict(x=x, r=r, W=np.array([x, r, wz]), C=np.array([x, 0.0, wz]), face=face, rotor=rot, zo=zo, zi=zi)

def bearing_loads(g, F):
    """Contact-patch force F -> (outboard radial N, inboard radial N, axial N). Axial taken by the inboard bearing;
    torque about the hub axis goes to the rotor/driveline, not the bearings."""
    po = np.array([g["x"], g["r"], g["zo"]]); pi = np.array([g["x"], g["r"], g["zi"]])
    # unknowns: Ro_x, Ro_y, Ri_x, Ri_y, A_z ; equations: sum F (3), sum M about W, x and y components (2)
    A = np.zeros((5, 5)); rhs = np.zeros(5); F = np.asarray(F, float)
    for col, (p, comp) in enumerate([(po, 0), (po, 1), (pi, 0), (pi, 1), (pi, 2)]):
        f = np.zeros(3); f[comp] = 1.0
        A[:3, col] = f; A[3:, col] = np.cross(p - g["W"], f)[:2]
    rhs[:3] = -F; rhs[3:] = -np.cross(g["C"] - g["W"], F)[:2]
    x = np.linalg.solve(A, rhs)
    return math.hypot(x[0], x[1]), math.hypot(x[2], x[3]), abs(x[4])

def equiv(Fr, Fa):
    """Deep-groove equivalent dynamic and static loads (ISO 281/76 simplified)."""
    P = Fr if Fa / max(Fr, 1e-9) <= 0.25 else 0.56 * Fr + 1.6 * Fa
    return P, max(Fr, 0.6 * Fr + 0.5 * Fa)

def drive_torque():
    """Worst drive torque through one rear hub, N*m: spool + inside wheel unloaded -> one tyre carries the whole
    rear axle load (with 1 g accel transfer) at grip MU."""
    w = L.MASS * L.G; rear = w * (1 - L.FRONT_SPLIT) + w * 1.0 * L.CG_H / m.WHEELBASE
    return L.MU * rear * (m.TIRE_OD / 2) / 1000

def shaft_fos(g, F, T=0.0):
    """Hub shaft von Mises FoS at the outboard bearing (bending from F about that section + torsion T in N*m)."""
    arm = g["C"] - np.array([g["x"], g["r"], g["zo"]])
    M = np.linalg.norm(np.cross(arm, F)[:2])        # bending moment about axes normal to the hub axis, N*mm
    do, di = HUB["od"], HUB["id"]; I = math.pi / 64 * (do**4 - di**4); J = 2 * I
    s = M * (do / 2) / I; tau = T * 1000 * (do / 2) / J
    return HUB["Sy"] / math.sqrt(s * s + 3 * tau * tau)

def arm_fos(g, point, force):
    """Upright arm from the bearing housing to a hardpoint as a cantilever: FoS on 7075 yield."""
    hub_r = BEARING["D"] / 2 + UPRIGHT["wall"]
    p = np.asarray(point, float); d = p - np.array([g["x"], g["r"], p[2]])   # radial vector from hub axis
    L_arm = max(np.linalg.norm(d) - hub_r, 1.0); u = d / np.linalg.norm(d)
    f_perp = np.linalg.norm(force - np.dot(force, u) * u); f_ax = abs(np.dot(force, u))
    w, t = UPRIGHT["w"], UPRIGHT["t"]; A = w * t; Z = min(w * t * t, t * w * w) / 6
    return UPRIGHT["Sy"] / (f_perp * L_arm / Z + f_ax / A), L_arm

def stud_slip_torque():
    s = STUDS; clamp = s["preload"] * s["Sp"] * s["As"]
    return s["n"] * clamp * s["mu"] * (s["pcd"] / 2) / 1000     # N*m before the wheel slips on the hub

def analyse(axle):
    g = geom(axle); C, links = L.corner(axle)
    out = dict(g=g, static_s0=9e9, arm=(9e9, ""), shaft=9e9, joints={})
    cs = L.cases(axle)
    for case, F in cs.items():
        F = np.asarray(F, float); ro, ri, a = bearing_loads(g, F)
        for Fr, Fa in ((ro, 0.0), (ri, a)):
            out["static_s0"] = min(out["static_s0"], BEARING["C0"] / equiv(Fr, Fa)[1])
        T = drive_torque() if (axle == "rear" and "brake" not in case) else 0.0
        out["shaft"] = min(out["shaft"], shaft_fos(g, F, T))
        f = L.link_forces(C, links, F)
        byjoint = {}
        for (n, p, q, _), v in zip(links, f):
            u = np.subtract(q, p) / np.linalg.norm(np.subtract(q, p)); key = tuple(np.round(p, 1))
            byjoint.setdefault(key, [n.split()[0], np.zeros(3)])[1] += v * u          # link pulls the upright
        for key, (n, force) in byjoint.items():
            fos, arm = arm_fos(g, key, force)
            if fos < out["arm"][0]: out["arm"] = (fos, f"{n} arm {arm:.0f} mm ({case})")
            out["joints"][n] = max(out["joints"].get(n, 0), np.linalg.norm(force))
    # life at a 1 g combined-cornering duty point on this (outer) wheel
    w = L.MASS * L.G; share = L.FRONT_SPLIT if axle == "front" else 1 - L.FRONT_SPLIT
    tr = m.TRACK_F if axle == "front" else m.TRACK_R
    fz = w * share / 2 + w * share * 1.0 * L.CG_H / tr
    ro, ri, a = bearing_loads(g, (0.0, fz, -fz))
    P = max(equiv(ro, 0)[0], equiv(ri, a)[0])
    out["L10"] = (BEARING["C"] / P) ** 3                        # million revs
    out["need"] = LIFE_SF * LIFE_KM * 1e3 / (math.pi * m.TIRE_OD / 1000) / 1e6
    out["max_wheel_T"] = max(drive_torque() if axle == "rear" else 0.0,
                             max(abs(F[0]) for F in cs.values()) * m.TIRE_OD / 2 / 1000)
    return out

def checks():
    res = []
    slip = stud_slip_torque()
    for axle in ("front", "rear"):
        r = analyse(axle); g = r["g"]; s = m.SUSP[axle]; wz = g["W"][2]; zb = wz - s["inset"]
        res += [
            (f"{axle} bearing static safety s0 >= 1.5 (all cases)", r["static_s0"] >= 1.5, f"{r['static_s0']:.2f} ({BEARING['name']})"),
            (f"{axle} bearing L10 >= {LIFE_SF:.0f}x {LIFE_KM:.0f} km", r["L10"] >= r["need"], f"{r['L10']:.0f} vs {r['need']:.1f} Mrev"),
            (f"{axle} hub shaft FoS >= 1.5 (bending + torsion)", r["shaft"] >= 1.5, f"{r['shaft']:.1f}"),
            (f"{axle} upright arms FoS >= 1.5 (7075-T6)", r["arm"][0] >= 1.5, f"{r['arm'][0]:.1f} ({r['arm'][1]})"),
            (f"{axle} wheel studs slip torque >= 1.5x max wheel torque", slip >= 1.5 * r["max_wheel_T"], f"{slip:.0f} vs {r['max_wheel_T']:.0f} N*m"),
            (f"{axle} rotor + caliper inside rim barrel", ROTOR_OD / 2 + CALIPER_H <= RIM_BARREL_R - 5, f"{ROTOR_OD / 2 + CALIPER_H:.0f} vs {RIM_BARREL_R:.0f} mm"),
            (f"{axle} upright body clears rotor >= 10 mm", g["rotor"] - (g["zo"] + BEARING["B"] / 2 + UPRIGHT["wall"]) >= 10,
             f"{g['rotor'] - (g['zo'] + BEARING['B'] / 2 + UPRIGHT['wall']):.0f} mm"),
            (f"{axle} ball joints within the bearing housing span", g["zi"] - 30 <= zb - s["ubj_lean"] and zb <= g["zo"] + 30,
             f"BJs z {zb - s['ubj_lean'] - wz:+.0f}/{zb - wz:+.0f}, bearings {g['zi'] - wz:+.0f}/{g['zo'] - wz:+.0f} mm from wheel centre"),
        ]
    return res

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:56s} {d}")
    for axle in ("front", "rear"):
        j = analyse(axle)["joints"]
        print(f"{axle} joint loads (max over cases) -> spherical bearing/rod end static rating >= 2x: " +
              ", ".join(f"{k} {v / 1e3:.1f} kN" for k, v in j.items()))
    print(f"rear traction-limited drive torque (one wheel, spool) {drive_torque():.0f} N*m")
    assert all(p for _, p, _ in res), "upright/hub check failed"
