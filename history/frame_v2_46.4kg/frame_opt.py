"""Frame tube-size optimiser: smallest tubes that pass every gate, written back into mule.py.

Each (role, size) group of mule.MEMBERS is moved along the ladder 1.5x0.095 > 1.25x0.095 > 1.0x0.095 > 1.0x0.065 > 1.0x0.049
(never below the F.3.2.1 size for its job). A sizing passes only if: every frame strength case is within its allowable
(roll-over vs welded 4130 yield, FoS 1.0; wheel loads, launch, 2000 N pedal vs FSAE welded yield, FoS 1.2; 20 g harness vs
FSAE welded ultimate; wing mounts FoS 1.5), torsion >= 1500 N*m/deg, hoop deflection <= 25 mm, every frame_rules.py and
compliance.py check passes, and (with robust=True) every robustness.py frame gate passes.
repair() upsizes the most-loaded group until it passes; greedy() then shrinks groups, heaviest first, while it still passes.
Run: python frame_opt.py   (prints the changes, applies them to mule.py, then run report.py)
"""
import re, pathlib
import numpy as np
import mule as m, fea, loads, powertrain, brakes, harness, aero, frame_rules, compliance

LADDER = ["J", "H", "A", "B", "C"]
ALLOW = {"roll-over": fea.SY_ROLL, "wheel": fea.SY_WELD / 1.2, "launch": fea.SY_WELD / 1.2, "pedal": fea.SY_WELD / 1.2,
         "harness": harness.UTS_WELD, "wing": fea.SY_WELD / 1.5}
BASE = list(m.MEMBERS)
_REC, _LABEL = [], [None]
_solve = fea.Frame.solve
def _recording_solve(self, ld, fx):
    u, st = _solve(self, ld, fx)
    if _LABEL[0]: _REC.append((_LABEL[0], [e[3] for e in self.el], [e[2] for e in self.el], st))
    return u, st

def floor(role): return LADDER.index(frame_rules.REQUIRED.get(frame_rules.cat(role), "C"))
def groups(): return sorted({(r, s) for _, _, s, r in BASE})
def apply(over): m.MEMBERS[:] = [(a, b, over.get((r, s), s), r) for a, b, s, r in BASE]
def mass(): return sum(fea.props(s)[0] * np.linalg.norm(np.subtract(b, a)) for a, b, s, _ in m.MEMBERS) * m.STEEL_DENSITY

def evaluate(over, robust=False):
    """(passes, worst utilisation, torsion, mass, per-case stress records)."""
    apply(over)
    for mod in (frame_rules, compliance):
        if not all(p for _, p, _ in mod.checks()): return False, 9.0, 0.0, mass(), []
    _REC.clear(); fea.Frame.solve = _recording_solve
    try:
        _LABEL[0] = "roll-over"; f = fea.run(verbose=False)
        for lab, fn in (("wheel", lambda: loads.run(verbose=False)), ("launch", powertrain.launch_frame),
                        ("pedal", brakes.frame_2000N), ("harness", harness.crash), ("wing", aero.top_speed_fos)):
            _LABEL[0] = lab; fn()
    finally:
        _LABEL[0] = None; fea.Frame.solve = _solve
    recs = _REC[1:]                      # the first solve is the 1000 N*m torsion stiffness case
    worst = max(st.max() / ALLOW[lab] for lab, _, _, st in recs)
    good = worst <= 1.0 and f["torsion"] >= 1500 and max(f["defl"].values()) <= 25
    if good and robust:
        import robustness
        good = all(p for n, p, _ in robustness.checks() if "tilt" not in n)
        if not good: worst = max(worst, 1.0 + 1e-3)
    return good, worst, f["torsion"], mass(), list(recs)

def most_loaded(recs, over, case=None):
    best = (0.0, None)
    for lab, roles, szs, st in recs:
        if case and lab != case: continue
        j = int(st.argmax()); u = st[j] / ALLOW[lab]
        if u > best[0]: best = (u, (roles[j], szs[j]))
    r, cur = best[1]
    return next(g for g in groups() if g[0] == r and over.get(g, g[1]) == cur)

def repair(over, robust=False, steps=60):
    import robustness
    case_of = {"roll-over": "roll-over", "wheel": "wheel", "launch": "launch", "2000 N": "pedal", "20 g": "harness", "wing": "wing"}
    for _ in range(steps):
        good, w, t, kg, recs = evaluate(over, robust)
        if good or w >= 9.0: return over
        case = None
        if robust and w <= 1.0 + 1e-3:          # nominal passes, a tolerance sample fails: upsize within that case
            samples = robustness.frame_samples(); keys = samples[0][0]
            failing = min(keys, key=lambda c: min(s[0][c] for s in samples))
            case = next(v for k, v in case_of.items() if k in failing)
            apply(over); good, w, t, kg, recs = evaluate(over)
        g = most_loaded(recs, over, case); cur = over.get(g, g[1]); i = LADDER.index(cur)
        if i == 0: print("cannot upsize", g); return over
        over = dict(over); over[g] = LADDER[i - 1]; print(f"  up   {g[0]} [{g[1]}] {cur}->{LADDER[i - 1]} (worst {w:.2f})", flush=True)
    return over

def greedy(over, robust=False):
    weight = lambda g: sum(fea.props(s)[0] * np.linalg.norm(np.subtract(b, a)) for a, b, s, r in BASE if (r, s) == g)
    changed = True
    while changed:
        changed = False
        for g in sorted(groups(), key=lambda g: -weight(g)):
            cur = over.get(g, g[1]); i = LADDER.index(cur)
            if i >= floor(g[0]): continue
            trial = dict(over); trial[g] = LADDER[i + 1]
            good, w, t, kg, _ = evaluate(trial, robust)
            if good:
                over, changed = trial, True
                print(f"  down {g[0]} [{g[1]}] {cur}->{LADDER[i + 1]}: {kg:.2f} kg, worst {w:.2f}", flush=True)
    return over

def write(over, path=pathlib.Path(__file__).parent / "mule.py"):
    """Apply size changes to mule.py's member tables (every tuple ending in '"<size>", "<role>")')."""
    s = path.read_text()
    for (role, old), new in over.items():
        if new != old:
            s = re.sub(r'"%s", "%s"\)' % (old, re.escape(role)), f'"{new}", "{role}")', s)
    path.write_text(s)

if __name__ == "__main__":
    over = repair({}, robust=True)
    over = greedy(over, robust=True)
    good, w, t, kg, _ = evaluate(over, robust=True)
    print(f"RESULT pass={good} mass {kg:.2f} kg torsion {t:.0f} worst {w:.2f}")
    print({g: v for g, v in over.items() if v != g[1]})
    if good: write(over); print("written to mule.py; now run report.py")
