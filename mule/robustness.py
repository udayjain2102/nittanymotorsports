"""Reality-gap check (docs/SIM_TO_REAL.md): re-run the models with realistic random tolerances instead of one nominal value.

Domain randomisation, NVIDIA-style, kept to *measured* ranges so the design isn't made needlessly heavy:
- Frame: every tube's wall +/-10 % (DOM / seamless mechanical tube tolerance), every joint moved up to 2 mm, and every
  tube's effective stiffness 60-100 % (stands in for weld and joint flexibility the rigid-joint FEA doesn't model).
  Gate: in EVERY sample, every frame strength case keeps FoS >= 1.0 against welded yield (no yield). The nominal design
  rule stays FoS >= 1.2; that 0.2 covers load uncertainty. Torsion: FSAE frames typically measure about 2/3 of rigid-joint
  FEA; the 60-100 % stiffness range models that joint flex, so the worst sampled torsion must stay >= 2x the suspension
  roll stiffness (Deakin: ~90 % of load transfer). 2/3 x nominal is shown as a cross-check, not stacked on top.
- Mass and tilt: every mass item +/-10 %. Brakes: pad friction 0.35-0.45. Lap sim: grip 1.3 +/- 0.1. Reported as bands
  so a single nominal number isn't mistaken for the truth.
Seeded, so results repeat. Run: python robustness.py
"""
import math, zlib
import numpy as np
import mule as m
import fea

N_FRAME, N_MASS, SEED = 16, 200, 2026          # frame_opt sizes against these samples, with a 5 % margin (OPT_MARGIN)
N_CHECK, SEED_CHECK, OPT_MARGIN = 32, 7, 1.08  # the reported gate uses a FRESH, larger set; margin 1.08 (1.05 still left launch at 0.99 on the fresh set). Audit 1 Oct: sizing and checking
                                               # on the same 16 draws gave FoS 1.00, and 0.97 on new seeds)
WALL, NODE, STIFF = 0.10, 2.0, (0.6, 1.0)
REAL_OVER_FEA = 2 / 3     # ASSUMED, no source found (audit): UDel measured ABOVE its FEA (FRAME_RESEARCH.md). Cross-check only

_SEED = [SEED]
def _rng(sample, key):
    """A random stream fixed by (seed, sample, geometry key): adding a tube elsewhere doesn't reshuffle this one's draw."""
    return np.random.default_rng([_SEED[0], sample, zlib.crc32(repr(key).encode())])

class _Perturbed:
    """Per-sample tube wall and stiffness factors, keyed by tube end points (before the joint shift)."""
    def __init__(self, sample): self.sample, self.f = sample, {}
    def get(self, a, b):
        k = tuple(sorted((tuple(np.round(a, 0)), tuple(np.round(b, 0)))))
        if k not in self.f:
            r = _rng(self.sample, k); self.f[k] = (1 + r.uniform(-WALL, WALL), r.uniform(*STIFF))
        return self.f[k]

def _section(s, wall):
    od, t = m.SIZES[s]; t = t * wall; idd = od - 2 * t
    I = np.pi / 64 * (od**4 - idd**4)
    return np.pi / 4 * (od**2 - idd**2), I, 2 * I, od / 2

def _patched_solve(pert):
    def solve(self, loads, fixed):
        n = len(self.P); K = np.zeros((6 * n, 6 * n)); F = np.zeros(6 * n); cache = []
        for i, j, s, _ in self.el:
            a, b = self.P[i], self.P[j]; wall, ks = pert.get(self._orig[i], self._orig[j])
            A, I, J, c = _section(s, wall); L = np.linalg.norm(b - a)
            T = fea.rot(a, b); kl = fea.k_local(L, A, I, J)
            idx = np.r_[6 * i:6 * i + 6, 6 * j:6 * j + 6]
            K[np.ix_(idx, idx)] += ks * (T.T @ kl @ T); cache.append((idx, T, ks * kl, A, I, c, ks * fea.E * I, L))
        for node, f in loads.items(): F[6 * node:6 * node + 3] += f
        fix = sorted({6 * nd + d for nd, dofs in fixed.items() for d in dofs})
        free = np.setdiff1d(np.arange(6 * n), fix)
        u = np.zeros(6 * n); u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
        st, buck = [], []
        for idx, T, kl, A, I, c, EI, L in cache:
            f = kl @ (T @ u[idx])
            st.append(max(abs(f[0]) / A + np.hypot(f[4], f[5]) * c / I, abs(f[6]) / A + np.hypot(f[10], f[11]) * c / I))
            buck.append(fea.euler_ratio(f[0], EI, L))     # thinner wall and joint flex lower the Euler load too
        self.buck = np.array(buck)
        if fea.RECORD is not None: fea.RECORD.append((self, self.buck))
        return u, np.array(st)
    return solve

def frame_cases():
    """Nominal-API calls of every frame strength case, returning {case: FoS}, plus torsion."""
    import loads, powertrain, brakes, harness, aero
    r = fea.run(verbose=False)
    out = {f"{k} roll-over (vs welded 4130 ultimate)": v * fea.SU_ROLL / fea.SY_ROLL for k, v in r["fos"].items()}
    out["wheel loads"] = loads.run(verbose=False)[2]
    out["launch"] = powertrain.launch_frame()[0]
    out["2000 N pedal"] = brakes.frame_2000N()[0]
    out["20 g harness (vs welded UTS)"] = harness.crash()[0]
    out["wing mounts / 1.5"] = aero.top_speed_fos() / 1.5
    out["frontal impact 95 kN (vs welded UTS)"] = fea.frontal()[0]
    return out, r["torsion"]

def _with_buckling():
    """frame_cases() plus one entry: the worst Euler load / compression over every case (thin walls, joint flex)."""
    (out, tors), bf, role = fea.buckle_fos(frame_cases)
    out["buckling, all cases (Euler / compression)"] = bf
    return out, tors

def frame_samples(n=N_FRAME, seed=SEED):
    orig_solve, orig_init = fea.Frame.solve, fea.Frame.__init__; res = []; _SEED[0] = seed
    try:
        for i in range(n):
            pert = _Perturbed(i)
            def init(self, members, _i=i, _pert=pert):
                orig_init(self, members)            # joints are merged first, so every member stays connected
                self._orig = self.P.copy()
                for j, p in enumerate(self.P):
                    self.P[j] = p + _rng(_i, ("node",) + tuple(np.round(p, 0))).uniform(-NODE, NODE, 3)
            fea.Frame.__init__ = init
            fea.Frame.solve = _patched_solve(pert)
            res.append(_with_buckling())
    finally:
        fea.Frame.solve, fea.Frame.__init__ = orig_solve, orig_init; _SEED[0] = SEED
    return res

def roll_stiffness():
    import roll
    _, k = roll.roll_gradient()
    return sum(k.values()) / 1e3 * math.pi / 180      # N*mm/rad -> N*m/deg

def mass_band(n=N_MASS, seed=SEED):
    """Tilt angle and total mass with every mass item scaled by U(0.9, 1.1)."""
    import mass
    rng = np.random.default_rng(seed); items = mass.items(); tilts, kgs = [], []
    for _ in range(n):
        tot = mz = my = 0.0
        for row in items:
            k = row[1] * rng.uniform(0.9, 1.1); x, y = row[2]
            tot += k; my += k * y
        cg_h = my / tot
        tilts.append(math.degrees(math.atan(m.TRACK_R / 2 / cg_h))); kgs.append(tot)
    return np.percentile(tilts, [5, 50, 95]), np.percentile(kgs, [5, 50, 95])

def tilt_correlated(err=0.10):
    """Worst correlated estimate error: every item above the nominal CG err heavier, every item below err lighter."""
    import mass
    items = mass.items(); cg = sum(r[1] * r[2][1] for r in items) / sum(r[1] for r in items)
    w = [(r[1] * (1 + err if r[2][1] > cg else 1 - err), r[2][1]) for r in items]
    h = sum(k * y for k, y in w) / sum(k for k, _ in w)
    return math.degrees(math.atan(m.TRACK_R / 2 / h)), h - cg

def brake_band():
    """Pedal force to lock all four wheels at pad friction 0.45 / 0.40 (nominal) / 0.35."""
    import brakes, loads
    mu0 = brakes.PAD_MU; out = {}
    try:
        for mu in (0.45, mu0, 0.35):
            brakes.PAD_MU = mu; out[mu] = brakes.lock_force(loads.MU, brakes.design_split())
    finally:
        brakes.PAD_MU = mu0
    return out

def lap_band():
    import lapsim
    g0 = lapsim.GRIP
    return {round(g, 2): (lapsim.accel(grip=g)[0], lapsim.skidpad(g)[0]) for g in (g0 - 0.1, g0, g0 + 0.1)}

def frame_gate(n=N_CHECK, seed=SEED_CHECK, need=1.0):
    """[(name, ok, detail)] for every frame case over n tolerance samples, plus the samples (for the torsion check)."""
    samples = frame_samples(n, seed); R = []
    worst = {c: min(s[0][c] for s in samples) for c in samples[0][0]}
    for c, v in worst.items():
        R.append((f"robust: {c} FoS >= {need:.2f} in all {len(samples)} tolerance samples (seed {seed}; walls ±10 %, joints ±2 mm, stiffness 60-100 %)",
                  v >= need, f"worst {v:.2f}"))
    return R, samples

def checks():
    R, samples = frame_gate()
    tors = min(s[1] for s in samples); need = 2 * roll_stiffness()
    R.append(("robust: worst sampled torsion (joint flex modelled) >= 2 x suspension roll stiffness",
              tors >= need, f"{tors:.0f} vs {need:.0f} N*m/deg (cross-check: 2/3 x nominal FEA = {REAL_OVER_FEA * fea.run(verbose=False)['torsion']:.0f})"))
    (t5, t50, t95), (k5, k50, k95) = mass_band()
    R.append(("robust: tilt >= 60 deg with every mass item ±10 % (5th percentile)", t5 >= 60,
              f"5/50/95 %: {t5:.1f} / {t50:.1f} / {t95:.1f} deg; mass {k5:.0f}-{k95:.0f} kg"))
    tc, dh = tilt_correlated()
    R.append(("robust: tilt >= 60 deg if mass estimates err together (high items +10 %, low items -10 %)", tc >= 60,
              f"{tc:.1f} deg (CG {dh:+.0f} mm). Weigh parts as they arrive; IN.11.2 is a hard rule"))
    return R

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:100s} {d}")
    print("lap-time band (grip -> accel, skidpad s):", {g: tuple(round(x, 2) for x in v) for g, v in lap_band().items()})
    print("lock-all-four pedal force by pad friction:", {mu: round(float(np.ravel(f)[0])) for mu, f in brake_band().items()})
