"""3D beam FEA of the mule frame (rigid welded joints, 12-DOF Euler-Bernoulli elements).

Workflow per structural-analysis skill: material -> geometry -> loads -> constraints -> solve -> FoS.
Material per FSAE F.3.4.2: E=200 GPa, welded Sy=180 MPa (conservative at every node).

Load cases:
  1. Torsional stiffness: rear suspension pickups fixed, vertical couple on front pickups.
  2. Main hoop top load: 6 kN lateral + 5 kN rearward + 9 kN down (SES-style; verify vs current SES).
  3. Front hoop top load: same magnitudes.
Cases 2-3 support the car at its suspension pickups (translations only).
Run: python fea.py  (runs a cantilever self-check first)
"""
import numpy as np
import mule as m

E, G, SY_WELD = 200e3, 77e3, 180.0  # MPa (N/mm^2)

def props(s):
    od, t = m.SIZES[s]; idd = od - 2 * t
    I = np.pi / 64 * (od**4 - idd**4)
    return np.pi / 4 * (od**2 - idd**2), I, 2 * I, od / 2  # A, I, J, c

def k_local(L, A, I, J):
    k = np.zeros((12, 12))
    a, t = E * A / L, G * J / L
    for i, j, v in [(0, 0, a), (6, 6, a), (0, 6, -a), (3, 3, t), (9, 9, t), (3, 9, -t)]:
        k[i, j] = k[j, i] = v
    for (d, r), sgn in [((1, 5), 1), ((2, 4), -1)]:  # bending about local z (v,thz) and y (w,thy)
        c = [12 * E * I / L**3, 6 * E * I / L**2, 4 * E * I / L, 2 * E * I / L]
        d2, r2 = d + 6, r + 6
        ent = {(d, d): c[0], (d2, d2): c[0], (d, d2): -c[0],
               (d, r): sgn * c[1], (d, r2): sgn * c[1], (d2, r): -sgn * c[1], (d2, r2): -sgn * c[1],
               (r, r): c[2], (r2, r2): c[2], (r, r2): c[3]}
        for (i, j), v in ent.items():
            k[i, j] = k[j, i] = v
    return k

def rot(a, b):
    x = (b - a) / np.linalg.norm(b - a)
    ref = np.array([0, 1.0, 0]) if abs(x[1]) < 0.9 else np.array([1.0, 0, 0])
    z = np.cross(x, ref); z /= np.linalg.norm(z); y = np.cross(z, x)
    R = np.array([x, y, z]); T = np.zeros((12, 12))
    for i in range(4): T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
    return T

class Frame:
    def __init__(self, members):
        self.pts, self.el = [], []
        for a, b, s, role in members:
            self.el.append((self.nid(a), self.nid(b), s, role))
        self.P = np.array(self.pts)
    def nid(self, p):
        p = np.array(p, float)
        for i, q in enumerate(self.pts):
            if np.linalg.norm(p - q) < 1.0: return i
        self.pts.append(p); return len(self.pts) - 1
    def solve(self, loads, fixed):
        n = len(self.P); K = np.zeros((6 * n, 6 * n)); F = np.zeros(6 * n)
        cache = []
        for i, j, s, _ in self.el:
            A, I, J, c = props(s); a, b = self.P[i], self.P[j]; L = np.linalg.norm(b - a)
            T = rot(a, b); kl = k_local(L, A, I, J); kg = T.T @ kl @ T
            idx = np.r_[6 * i:6 * i + 6, 6 * j:6 * j + 6]
            K[np.ix_(idx, idx)] += kg; cache.append((idx, T, kl, A, I, c))
        for node, f in loads.items(): F[6 * node:6 * node + 3] += f
        fix = sorted({6 * nd + d for nd, dofs in fixed.items() for d in dofs})
        free = np.setdiff1d(np.arange(6 * n), fix)
        u = np.zeros(6 * n); u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
        stress = []
        for (idx, T, kl, A, I, c) in cache:
            f = kl @ (T @ u[idx])
            s = max(abs(f[0]) / A + np.hypot(f[4], f[5]) * c / I, abs(f[6]) / A + np.hypot(f[10], f[11]) * c / I)
            stress.append(s)
        return u, np.array(stress)
    def find(self, p):
        return int(np.argmin(np.linalg.norm(self.P - np.array(p, float), axis=1)))

# Masses that sit on the frame (kg), split evenly over the nodes they bolt to (both sides): engine on its mounts,
# driver on the seat/harness nodes, fuel near the main hoop, spool + sprocket on its carriers. Assumptions.
HOOP_DIRS = [(-5000, 6000), (5000, 6000), (-6000, 5000), (6000, 5000)]   # (fore/aft, lateral) N; X fwd, Z right

LUMPED = [(("em_fb", "em_ft", "em_rb"), 32.0), (("mh_bot", "fh_bot", "mh_bar"), 80.0), (("mh_sis",), 5.0), (("sp_c",), 8.0)]

def inertia_relief(fr, loads):
    """Balance applied nodal forces with a rigid-body acceleration field of the frame's tube mass plus LUMPED masses,
    as in the real car, instead of reacting them at arbitrary supports. Returns (balanced loads, supports): one node
    clamped in all 6 DOF, which carries ~zero load and only stops rigid-body motion. (A 3-2-1 set picked by distance
    from the CG once landed all on the front bulkhead plane, left K singular and gave CPU-dependent stresses in CI.)"""
    n = len(fr.P); mass = np.zeros(n)
    for i, j, s, _ in fr.el:
        L = np.linalg.norm(fr.P[j] - fr.P[i]); mm = props(s)[0] * L * 7.85e-6
        mass[i] += mm / 2; mass[j] += mm / 2
    for names, kg in LUMPED:
        ks = [fr.find(m.N[n]) for n in names] + [fr.find(m.mir(m.N[n])) for n in names]
        for k in ks: mass[k] += kg / len(ks)
    cg = (mass[:, None] * fr.P).sum(0) / mass.sum(); r = fr.P - cg
    Ft = sum(np.asarray(v, float) for v in loads.values())
    Mt = sum(np.cross(fr.P[k] - cg, np.asarray(v, float)) for k, v in loads.items())
    # unknowns a0 (3) and alpha (3): F_i = m_i (a0 + alpha x r_i)
    A = np.zeros((6, 6)); b = np.r_[Ft, Mt]
    for i in range(n):
        R = np.array([[0, r[i, 2], -r[i, 1]], [-r[i, 2], 0, r[i, 0]], [r[i, 1], -r[i, 0], 0]])  # alpha x r = R @ alpha
        A[:3, :3] += mass[i] * np.eye(3); A[:3, 3:] += mass[i] * R
        Rx = np.array([[0, -r[i, 2], r[i, 1]], [r[i, 2], 0, -r[i, 0]], [-r[i, 1], r[i, 0], 0]])  # r x (.)
        A[3:, :3] += mass[i] * Rx; A[3:, 3:] += mass[i] * Rx @ R
    x = np.linalg.solve(A, b); a0, al = x[:3], x[3:]
    out = {k: np.asarray(v, float).copy() for k, v in loads.items()}
    for i in range(n):
        out[i] = out.get(i, np.zeros(3)) - mass[i] * (a0 + np.cross(al, r[i]))
    return out, {0: range(6)}

def selfcheck():  # cantilever tip deflection vs P L^3 / 3EI
    L, P = 1000.0, 100.0
    fr = Frame([((0, 0, 0), (L / 2, 0, 0), "B", ""), ((L / 2, 0, 0), (L, 0, 0), "B", "")])
    u, _ = fr.solve({fr.find((L, 0, 0)): np.array([0, -P, 0])}, {fr.find((0, 0, 0)): range(6)})
    exact = P * L**3 / (3 * E * props("B")[1])
    assert abs(-u[6 * fr.find((L, 0, 0)) + 1] - exact) / exact < 1e-6, "beam element wrong"
    full = Frame(m.MEMBERS); ld, _ = inertia_relief(full, {0: np.array([1000.0, -2000.0, 500.0])})
    assert np.allclose(sum(ld.values()), 0, atol=1e-6), "inertia relief must balance the loads"

def pickups(names):
    return [q for n in names for q in (m.N[n], m.mir(m.N[n]))]

def report(fr, st, title):
    for j in np.argsort(st)[-4:-1][::-1]:
        print(f"      also {st[j]:.0f} MPa  {fr.el[j][3]} ({fr.el[j][2]})")
    k = int(np.argmax(st)); _, _, s, role = fr.el[k]
    print(f"{title}: max stress {st[k]:.0f} MPa in '{role}' (size {s}), FoS vs welded Sy = {SY_WELD / st[k]:.2f}")
    return SY_WELD / st[k]

def run(verbose=True):
    """Torsional stiffness + both hoop load cases. Returns {"torsion": N*m/deg, "fos": {case: FoS}, "defl": {case: mm}}."""
    say = print if verbose else (lambda *a, **k: None)
    fr = Frame(m.MEMBERS)
    say(f"{len(fr.P)} nodes, {len(fr.el)} elements")
    rear = [fr.find(p) for p in pickups(["r_lsus", "r_sus", "rr_lsus", "rr_sus"])]
    front = pickups(["ring_lsus", "ring_sus", "bh_lsus", "bh_sus"])
    # 1. torsion: 1000 N*m couple split over front pickups, rear pickups fixed
    T = 1.0e6; zsep = np.mean([abs(p[2]) for p in front]) * 2
    Fv = T / zsep / 4  # per node, 4 nodes per side
    loads = {fr.find(p): np.array([0, Fv if p[2] > 0 else -Fv, 0]) for p in front}
    u, st = fr.solve(loads, {n: range(6) for n in rear})
    dy = np.mean([u[6 * fr.find(p) + 1] for p in front if p[2] > 0]) - np.mean([u[6 * fr.find(p) + 1] for p in front if p[2] < 0])
    out = {"torsion": T / 1e3 / np.degrees(np.arctan(dy / zsep)), "fos": {}, "defl": {}}
    say(f"Torsional stiffness (chassis only, pickup-to-pickup): {out['torsion']:.0f} N*m/deg")
    # 2/3. hoop top loads, car supported at all suspension pickups (translations)
    sup = {fr.find(p): range(3) for p in pickups(["r_lsus", "r_sus", "rr_lsus", "rr_sus", "ring_lsus", "ring_sus", "bh_lsus", "bh_sus"])}
    # FSAE Alternative Frame rules AF4.1/AF4.2 (the SES basis): Fx 6.0, Fy 5.0, Fz -9.0 kN at the hoop top, no failure,
    # deflection <= 25 mm. Which horizontal axis gets 6 kN, and fore/aft sign, are enveloped: worst of four cases.
    for name, top in [("Main hoop", "mh_top"), ("Front hoop", "fh_top")]:
        worst = None
        for fx, fz in HOOP_DIRS:
            ld = {fr.find(p): np.array([fx, -9000, fz]) / 2 for p in (m.N[top], m.mir(m.N[top]))}
            u, st = fr.solve(ld, sup); d = np.linalg.norm(u.reshape(-1, 6)[:, :3], axis=1).max()
            if worst is None or st.max() > worst[1].max(): worst = (fx, st)
            out["defl"][name] = max(out["defl"].get(name, 0.0), d)
        fx, st = worst
        out["fos"][name] = report(fr, st, f"{name} 6/5/9 kN envelope (worst: {fx / 1e3:+.0f} kN fore/aft)") if verbose else SY_WELD / st.max()
        say(f"   max deflection {out['defl'][name]:.1f} mm (limit 25)")
    return out

if __name__ == "__main__":
    selfcheck()
    assert min(run()["fos"].values()) > 1.0, "frame yields under hoop load case"
