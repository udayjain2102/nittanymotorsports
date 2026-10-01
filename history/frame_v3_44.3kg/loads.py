"""Suspension link loads -> A-arm sizing -> frame check under wheel loads.

Upright = rigid body held by 6 two-force links (4 A-arm legs, tie rod / toe link, pushrod).
Contact-patch force for each design case -> link forces (6x6 solve) -> chassis reactions
applied at frame nodes in the beam FEA (other three corners held at their pickups).
Mass/CG/load factors are mule assumptions; change them here.
Run: python loads.py  (self-check: pure vertical load through a vertical link set)
"""
import numpy as np
import mule as m
import fea

MASS, CG_H, FRONT_SPLIT, G = 300.0, 345.0, 0.45, 9.81   # kg (car+driver), mm, -, m/s^2; mass.py budget with the rear wing: 296 kg, 340 mm, 46 %
MU = 1.5                                                  # tyre grip for design cases
A_ARM = m.SUSP_TUBE

def corner(axle):
    x = m.WHEELBASE if axle == "front" else 0.0
    return (x, 0.0, (m.TRACK_F if axle == "front" else m.TRACK_R) / 2), m.susp_links(axle)

def link_forces(C, links, F):
    """Tension-positive force in each link for contact-patch force F (N) at C."""
    A = np.zeros((6, 6)); b = np.zeros(6)
    for i, (_, p, q, _) in enumerate(links):
        u = np.subtract(q, p); u = u / np.linalg.norm(u)
        A[:3, i] = u; A[3:, i] = np.cross(np.subtract(p, C), u)
    b[:3] = -np.asarray(F)
    return np.linalg.solve(A, b)

def cases(axle):
    """Contact-patch forces (Fx fwd, Fy up, Fz outward-right) on the right (outer-in-left-turn) wheel."""
    w = MASS * G; share = FRONT_SPLIT if axle == "front" else 1 - FRONT_SPLIT
    tr = m.TRACK_F if axle == "front" else m.TRACK_R
    static = w * share / 2
    lat = static + w * share * MU * CG_H / tr                      # outer wheel in a MU-g corner
    brake_fz = static + (w * MU * CG_H / m.WHEELBASE / 2) * (1 if axle == "front" else -1)
    # combined: friction circle at MU, 0.8 lateral + 0.6 braking; kerb: 2x the 1 g-corner load while cornering at 1 g
    ay, ax = 0.8 * MU, 0.6 * MU
    comb = static + w * share * ay * CG_H / tr + (w * ax * CG_H / m.WHEELBASE / 2) * (1 if axle == "front" else -1)
    lat1 = static + w * share * 1.0 * CG_H / tr
    return {
        "3g bump": (0, 3 * static, 0),
        f"{MU}g corner": (0, lat, -MU * lat),                     # tyre pushes car toward the turn centre (-Z)
        f"{MU}g brake": (-MU * brake_fz, brake_fz, 0),
        "corner+brake": (-ax * comb, comb, -ay * comb),
        "kerb in 1g corner": (0, 2 * lat1, -1.0 * lat1),
    }

def euler(L, od=A_ARM[0], t=A_ARM[1], E=200e3):
    i = np.pi / 64 * (od**4 - (od - 2 * t)**4); return np.pi**2 * E * i / L**2

def selfcheck():
    C = (0, 0, 0)
    o, px, pz = (0, 0, 0), (1, 0, 0), (0, 0, 1)   # 3-2-1 support: xyz at o, yz at px, y at pz
    links = [("a", o, (0, 1, 0), ""), ("b", o, (1, 0, 0), ""), ("c", o, (0, 0, 1), ""),
             ("d", px, (1, 1, 0), ""), ("e", px, (1, 0, 1), ""), ("f", pz, (0, 1, 1), "")]
    f = link_forces(C, links, (0, -100, 0))   # push down at origin: link a (vertical) carries it in tension
    assert abs(f[0] - 100) < 1e-6 and np.allclose(f[1:], 0, atol=1e-6)

def run(verbose=True):
    """All axles x cases. Returns (worst link buckling FoS, which link, worst frame FoS)."""
    say = print if verbose else (lambda *a, **k: None)
    frame = fea.Frame(m.MEMBERS)
    worst_fos, worst_link = 9e9, 9e9
    for axle in ("front", "rear"):
        C, links = corner(axle)
        for case, F in cases(axle).items():
            f = link_forces(C, links, F)
            say(f"{axle:5s} {case:11s} Fz={F[1]/1e3:5.2f} kN | " +
                  ", ".join(f"{n.split()[0]} {v/1e3:+.1f}" for (n, *_), v in zip(links, f)) + " kN")
            for (n, p, q, _), v in zip(links, f):
                if v < 0:   # every link is a two-force member: check the compressed ones for Euler buckling
                    od, t = m.PUSHROD_TUBE if n == "pushrod" else A_ARM
                    fos = euler(np.linalg.norm(np.subtract(q, p)), od, t) / -v
                    if fos < worst_link: worst_link, worst_name = fos, f"{axle} {n} ({case})"
            loads = {}
            for (n, p, q, node), v in zip(links, f):
                u = np.subtract(q, p); u = u / np.linalg.norm(u)
                if n == "pushrod":   # pushrod -> rocker: split into rocker pivot + shock mount (shock mount is a frame node)
                    import rocker     # local import: rocker -> springs -> loads
                    split, _ = rocker.reactions(axle, -v * u)
                    for nd, F in split.items():
                        k = frame.find(m.N[nd]); loads[k] = loads.get(k, 0) + F
                    continue
                k = frame.find(m.N[node]); loads[k] = loads.get(k, 0) - v * u      # link pulls chassis toward upright
            u, st = frame.solve(*fea.inertia_relief(frame, loads))   # wheel loads balanced by the car's inertia
            j = int(np.argmax(st)); fos = fea.SY_WELD / st[j]; worst_fos = min(worst_fos, fos)
            say(f"      frame: max {st[j]:.0f} MPa in '{frame.el[j][3]}' (FoS {fos:.2f})")
    say(f"worst link buckling FoS {worst_link:.1f} in {worst_name}; frame worst FoS {worst_fos:.2f} (welded Sy)")
    return worst_link, worst_name, worst_fos

if __name__ == "__main__":
    selfcheck()
    wl, _, wf = run()
    assert wl > 2 and wf > 1.0, "suspension load case fails"
