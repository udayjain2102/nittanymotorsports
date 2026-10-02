"""Compliance steer and camber: how far the wheel toes and cambers because the links stretch and the frame pickups
deflect under the design corner load (bracket and pickup stiffness).

Method, per corner (right wheel = outside in a left turn), for the MU-g corner case of loads.py:
  1. link forces from loads.link_forces;
  2. the frame is clamped at the front and main hoop bases (like a K&C rig clamping the tub), and the link reactions are
     applied at their pickups (pushrod: split over rocker pivot and shock mount, as in loads.py). Beam FEA gives the
     pickup deflections;
  3. every link is a two-force member (pushrod on the upright, so no rod end or arm sees bending); each link gets
     its axial stretch F L / (E A);
  4. the upright is a rigid body on six links: the small motion (translation v, rotation w) that matches the six
     link-length changes gives toe (w about the vertical) and camber (w about the fore-aft axis).
Run: python compliance.py
"""
import math
import numpy as np
import mule as m
import fea
import loads as L

E = 200e3                  # MPa, steel links
CLAMP = ("fh_bot", "mh_bot")
LIMIT_DEG = 0.25           # toe and camber at the design corner load (ours; review notes: keep compliance small)

def corner(axle):
    C, links = L.corner(axle); case = f"{L.MU}g corner"; F = L.cases(axle)[case]
    f = L.link_forces(C, links, F); frame = fea.Frame(m.MEMBERS); loads = {}
    for (n, p, q, node), v in zip(links, f):
        u = np.subtract(q, p) / np.linalg.norm(np.subtract(q, p))
        if n == "pushrod":
            import rocker
            for nd, Fv in rocker.reactions(axle, -v * u)[0].items():
                k = frame.find(m.N[nd]); loads[k] = loads.get(k, 0) + Fv
        else:
            k = frame.find(m.N[node]); loads[k] = loads.get(k, 0) - v * u
    fixed = {frame.find(p): range(6) for n in CLAMP for p in (m.N[n], m.mir(m.N[n]))}
    disp, _ = frame.solve(loads, fixed)
    # ponytail: pushrod end takes the rocker pivot's deflection (rocker assumed rigid); add rocker flex if it matters
    A = np.zeros((6, 6)); b = np.zeros(6)
    for i, ((n, p, q, node), v) in enumerate(zip(links, f)):
        Lk = math.dist(p, q); u = np.subtract(q, p) / Lk
        od, t = m.PUSHROD_TUBE if n == "pushrod" else m.SUSP_TUBE
        area = math.pi / 4 * (od**2 - (od - 2 * t) ** 2)
        k = frame.find(m.N[node]); dq = disp[6 * k:6 * k + 3]
        stretch = v * Lk / (E * area)
        r = np.subtract(p, C)
        A[i, :3] = u; A[i, 3:] = np.cross(r, u)          # u . (v + w x r) = (w) . (r x u)
        b[i] = np.dot(u, dq) - stretch
    x = np.linalg.solve(A, b); w = x[3:]
    # toe: + about the vertical turns the right wheel's front inboard = toe-in
    return dict(toe=math.degrees(w[1]), camber=math.degrees(w[0]), move=np.linalg.norm(x[:3]), case=case,
                stretch=max(abs(v) * math.dist(p, q) / (E * math.pi / 4 * (m.SUSP_TUBE[0]**2 - (m.SUSP_TUBE[0] - 2 * m.SUSP_TUBE[1])**2))
                            for (n, p, q, _), v in zip(links, f) if n != "pushrod"))

def checks():
    out = []
    for a in ("front", "rear"):
        r = corner(a)
        out.append((f"{a} compliance at {r['case']}: toe and camber <= {LIMIT_DEG} deg (ours)",
                    abs(r["toe"]) <= LIMIT_DEG and abs(r["camber"]) <= LIMIT_DEG,
                    f"toe {abs(r['toe']):.3f} {'in' if r['toe'] > 0 else 'out'}, camber {r['camber']:+.3f} deg; worst arm stretch {r['stretch']:.3f} mm"))
    return out

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:60s} {d}")
    assert all(p for _, p, _ in res), "compliance check failed"
