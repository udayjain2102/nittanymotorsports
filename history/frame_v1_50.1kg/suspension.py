"""Front-view double-wishbone kinematics for the mule (per axle, right side, chassis frame).

Inboard pivots = mean (z, y) of the two frame pickups (valid while pivot axes run ~fore/aft).
Solves the 4-bar (lower arm, upright, upper arm) through +/-50 mm wheel travel and reports
roll centre, camber gain, KPI, scrub, and packaging inside a 13" wheel.
Run: python suspension.py   (self-check: equal parallel arms -> zero camber gain, RC on ground)
"""
import math
import mule as m

def inner(names):
    ps = [m.N[n] for n in names]
    return (sum(p[2] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))

def geom(axle):
    s = m.SUSP[axle]; tr = m.TRACK_F if axle == "front" else m.TRACK_R
    wz, r = tr / 2, m.TIRE_OD / 2
    return dict(Al=inner(s["inner_low"]), Au=inner(s["inner_up"]),
                Bl=(wz - s["inset"], s["lbj_y"]), Bu=(wz - s["inset"] - s["ubj_lean"], s["ubj_y"]),
                C=(wz, 0.0), W=(wz, r))

def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def rot(v, t): c, s = math.cos(t), math.sin(t); return (c * v[0] - s * v[1], s * v[0] + c * v[1])
def dist(a, b): return math.hypot(*sub(a, b))
def ang(v): return math.atan2(v[1], v[0])

def circles(p0, r0, p1, r1, near):
    d = dist(p0, p1)
    if d > r0 + r1 or d < abs(r0 - r1): return None
    a = (r0**2 - r1**2 + d**2) / (2 * d); h = math.sqrt(max(r0**2 - a**2, 0))
    u = ((p1[0] - p0[0]) / d, (p1[1] - p0[1]) / d); mpt = (p0[0] + a * u[0], p0[1] + a * u[1])
    cand = [(mpt[0] + h * -u[1], mpt[1] + h * u[0]), (mpt[0] - h * -u[1], mpt[1] - h * u[0])]
    return min(cand, key=lambda q: dist(q, near))

def upright(g, d):
    """Lower arm rotated d rad -> function mapping a static upright point (z, y) to its new position."""
    Bl = add(g["Al"], rot(sub(g["Bl"], g["Al"]), d))
    Bu = circles(g["Au"], dist(g["Au"], g["Bu"]), Bl, dist(g["Bl"], g["Bu"]), g["Bu"])
    if Bu is None: return None, 0.0
    a = ang(sub(Bu, Bl)) - ang(sub(g["Bu"], g["Bl"]))
    return (lambda p: add(Bl, rot(sub(p, g["Bl"]), a))), a

def pose(g, d):
    """Rotate lower arm by d rad; return (contact patch, camber change deg) or None if locked."""
    f, a = upright(g, d)
    if f is None: return None
    return f(g["C"]), -math.degrees(a)  # CCW upright rotation tips top inboard = negative camber

def at_travel(g, t):
    lo, hi = -0.8, 0.8  # lower-arm rotation bracket (rad)
    f = lambda d: (pose(g, d)[0][1] - g["C"][1] - t) if pose(g, d) else None
    flo, fhi = f(lo), f(hi)
    if flo is None or fhi is None or flo * fhi > 0: return None
    for _ in range(60):
        mid = (lo + hi) / 2; fm = f(mid)
        if fm is None: return None
        lo, flo = (mid, fm) if fm * flo > 0 else (lo, flo); hi = mid if fm * flo <= 0 and lo != mid else hi
    return pose(g, (lo + hi) / 2)

def line_x(p1, p2, q1, q2):
    d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
    if abs(d) < 1e-9: return None
    t = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d
    return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))

def analyse(g):
    ic = line_x(g["Al"], g["Bl"], g["Au"], g["Bu"])
    rc = g["C"][1] if ic is None else line_x(g["C"], ic, (0, 0), (0, 1))[1]
    res = {"ic": ic, "rc": rc}
    for t in (-50, -25, 25, 50):
        p = at_travel(g, t); res[t] = None if p is None else (p[1], p[0][0] - g["C"][0])
    k = sub(g["Bu"], g["Bl"]); res["kpi"] = math.degrees(math.atan2(-k[0], k[1]))
    res["scrub"] = g["C"][0] - (g["Bl"][0] - k[0] * g["Bl"][1] / k[1])  # +: axis meets ground inboard of patch
    return res

TARGETS = {"front": (15, 60), "rear": (25, 80)}  # roll-centre height window, mm

def checks():
    out = []
    for axle in ("front", "rear"):
        g = geom(axle); r = analyse(g); lo, hi = TARGETS[axle]
        out.append((f"{axle} roll centre {lo}-{hi} mm", lo <= r["rc"] <= hi, f"{r['rc']:.0f} mm"))
        ok50 = all(r[t] is not None for t in (-50, -25, 25, 50))
        out.append((f"{axle} no lock-up over +/-50 mm (V.3.1.1: 50 mm usable; design +50/-25)", ok50, ""))
        if ok50:
            gain = r[25][0]
            out.append((f"{axle} camber gain -1.2..-0.3 deg per 25 mm bump", -1.2 <= gain <= -0.3,
                        f"{gain:+.2f} deg @+25, {r[50][0]:+.2f} @+50, {r[-50][0]:+.2f} @-50; track {r[50][1]:+.1f} mm @+50"))
        for bj in ("Bl", "Bu"):
            dy = abs(g[bj][1] - g["W"][1]); dz = g["W"][0] - g[bj][0]
            out.append((f"{axle} {bj} inside 13in wheel (|dy|<=125, 30<=inset<=110)", dy <= 125 and 30 <= dz <= 110,
                        f"dy={dy:.0f} inset={dz:.0f}"))
        smax = 40 if axle == "front" else 80   # front: steering effort and kickback; lower is limited by tyre-to-arm gap at lock
        out.append((f"{axle} KPI 0-10 deg, scrub 0-{smax} mm", 0 <= r["kpi"] <= 10 and 0 <= r["scrub"] <= smax,
                    f"KPI {r['kpi']:.1f} deg, scrub {r['scrub']:.0f} mm"))
    return out

def selfcheck():
    g = dict(Al=(200, 100), Bl=(500, 100), Au=(200, 350), Bu=(500, 350), C=(560, 0), W=(560, 260))
    r = analyse(g)
    assert r["ic"] is None and abs(r[25][0]) < 1e-6, "parallel equal arms must give zero camber gain"

if __name__ == "__main__":
    selfcheck()
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:58s} {d}")
    for axle in ("front", "rear"):
        g = geom(axle); print(axle, {k: tuple(round(v) for v in val) for k, val in g.items()})
    assert all(p for _, p, _ in res), "suspension check failed"
