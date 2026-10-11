"""Frame topology search (topo-experiment): ground-structure moves with re-sizing.

Moves: add a size-C tube between two existing nodes (same side, mirrored; or a node to its mirror), or remove a
non-rule tube. Every move is re-sized with frame_opt.repair() + greedy() (all load cases, rules, torsion, deflection)
and must pass the geometry checks (cockpit templates, engine bay, steering, rockers, ...). Each round accepts the move
that gives the lowest mass; it stops when no move saves >= MIN_GAIN kg. The final design is re-sized against the robust
(tolerance) gate. Additions are screened first at fixed sizes (one solve each); the best SHORTLIST get the full re-size.
Run: python topo_search.py   (writes topo_search.json; nothing in mule.py changes)
"""
import contextlib, io, itertools, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import mule as m, frame_opt as fo, frame_rules, report

MIN_GAIN, SHORTLIST, ROUNDS, LMIN, LMAX = 0.10, 24, 8, 150.0, 1000.0
GEOM = [mod for mod, _ in report.MODULES if mod.__name__ not in ("fea", "robustness", "lapsim", "cockpit")]   # cockpit: 29 s, checked on winners only
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topo_search.json")

def build(spec):
    side, cross, diag = spec; out = []
    for a, b, s, r in side: out += [(m.node(a), m.node(b), s, r), (m.mir(m.node(a)), m.mir(m.node(b)), s, r)]
    for a, s, r in cross: out.append((m.node(a), m.mir(m.node(a)), s, r))
    for a, b, s, r in diag: out.append((m.node(a), m.node(b), s, r))
    return out

def quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()): return fn(*a)

def geom_ok(members, cockpit=False):
    m.MEMBERS[:] = members
    mods = GEOM + ([__import__("cockpit")] if cockpit else [])
    try: return all(all(p for _, p, _ in quiet(mod.checks)) for mod in mods)
    except Exception: return False

def resize(spec, robust=False):
    """(mass, sized spec) after repair + greedy, or (inf, None) if it can't pass."""
    fo.BASE[:] = build(spec)
    if not geom_ok(list(fo.BASE)): return float("inf"), None
    try:
        over = quiet(fo.repair, {}, robust); over = quiet(fo.greedy, over, robust)
        good, w, t, kg, _ = fo.evaluate(over, robust)
    except (np.linalg.LinAlgError, ValueError, StopIteration): return float("inf"), None
    if not good: return float("inf"), None
    sz = lambda s, r: fo.sized(over, r, s)
    side, cross, diag = spec
    return kg, ([(a, b, sz(s, r), r) for a, b, s, r in side], [(a, sz(s, r), r) for a, s, r in cross],
                [(a, b, sz(s, r), r) for a, b, s, r in diag])

def apply_move(spec, mv):
    side, cross, diag = (list(x) for x in spec)
    if mv[0] == "add-side": side.append((mv[1], mv[2], "C", f"Topo diagonal {mv[1]}-{mv[2]}"))
    elif mv[0] == "add-cross": cross.append((mv[1], "C", f"Topo cross {mv[1]}"))
    elif mv[0] == "rm-side": side = [e for e in side if (e[0], e[1], e[3]) != mv[1:]]
    elif mv[0] == "rm-cross": cross = [e for e in cross if (e[0], e[2]) != mv[1:]]
    elif mv[0] == "rm-diag": diag = [e for e in diag if (e[0], e[1], e[3]) != mv[1:]]
    return side, cross, diag

def screen(args):
    """Fixed-size solve with the move: worst utilisation and torsion (additions only)."""
    spec, mv = args
    fo.BASE[:] = build(apply_move(spec, mv))
    if not geom_ok(list(fo.BASE)): return mv, None
    try: good, w, t, kg, _ = fo.evaluate({})
    except (np.linalg.LinAlgError, ValueError, StopIteration): return mv, None
    return mv, (w, t, kg) if w < 9 else None

def full(args):
    spec, mv = args
    try: kg, new = resize(apply_move(spec, mv))
    except Exception as e: print(f"    error {mv}: {e!r}", flush=True); kg, new = float("inf"), None
    return mv, kg, new

def candidates(spec):
    side, cross, diag = spec
    names = sorted({n for a, b, *_ in side for n in (a, b)})
    have = {frozenset((a, b)) for a, b, *_ in side}; crossed = {a for a, *_ in cross}
    pts = [np.array(m.node(n)) for n in names] + [np.array(m.mir(m.node(n))) for n in names]
    def clear(p, q):   # no other node on the tube's line (it would just duplicate existing tubes)
        d = q - p; L = np.linalg.norm(d)
        for x in pts:
            t = np.dot(x - p, d) / L**2
            if 1e-3 < t < 1 - 1e-3 and np.linalg.norm(p + t * d - x) < 15: return False
        return True
    adds = []
    for a, b in itertools.combinations(names, 2):
        p, q = np.array(m.node(a)), np.array(m.node(b)); L = np.linalg.norm(q - p)
        if frozenset((a, b)) not in have and LMIN <= L <= LMAX and clear(p, q): adds.append(("add-side", a, b))
    for a in names:
        p = np.array(m.node(a)); q = np.array(m.mir(m.node(a))); L = np.linalg.norm(q - p)
        if a not in crossed and LMIN <= L <= LMAX and clear(p, q): adds.append(("add-cross", a))
    rule = lambda r: frame_rules.cat(r) != "structural"
    rms = ([("rm-side", a, b, r) for a, b, s, r in side if not rule(r)] + [("rm-cross", a, r) for a, s, r in cross if not rule(r)]
           + [("rm-diag", a, b, r) for a, b, s, r in diag if not rule(r)])
    return adds, rms

def log(msg, rec=None):
    print(msg, flush=True)
    if rec is not None:
        with open(OUT, "w") as f: json.dump(rec, f, indent=1)

if __name__ == "__main__":
    t0 = time.time()
    if "--resume" in sys.argv:   # continue from the last accepted round in topo_search.json
        rec = json.load(open(OUT)); keep = int(sys.argv[sys.argv.index("--resume") + 1]) if len(sys.argv) > 2 else len(rec["rounds"])
        rec["rounds"] = rec["rounds"][:keep]; spec = (list(m.SIDE), list(m.CROSS), list(m.DIAG)); kg, spec = resize(spec)
        for r in rec["rounds"]: kg, spec = resize(apply_move(spec, tuple(r["move"])))   # replay against the current checks
        log(f"resume after {keep} accepted moves: {kg:.2f} kg")
    else:
        spec = (list(m.SIDE), list(m.CROSS), list(m.DIAG))
        start_kg = fo.evaluate({})[3]
        kg, spec = resize(spec)
        rec = {"start_kg": start_kg, "resized_kg": kg, "rounds": []}
        log(f"start {start_kg:.2f} kg; re-sized only: {kg:.2f} kg ({time.time()-t0:.0f} s)", rec)
    with ProcessPoolExecutor(9) as pool:   # a dead worker raises BrokenProcessPool instead of hanging (multiprocessing.Pool hung)
        for rnd in range(len(rec["rounds"]), ROUNDS):
            adds, rms = candidates(spec)
            sc = [(mv, r) for mv, r in pool.map(screen, [(spec, mv) for mv in adds]) if r]
            sc.sort(key=lambda x: x[1][0] + x[1][2] / 100)   # lowest worst utilisation, ties to lighter
            short = [mv for mv, _ in sc[:SHORTLIST]]
            log(f"round {rnd+1}: {len(adds)} additions ({len(sc)} fit), {len(rms)} removals; full re-size of {len(short) + len(rms)}")
            res = sorted((r for r in pool.map(full, [(spec, mv) for mv in short + rms]) if r[2]), key=lambda r: r[1])
            for mv, k, _ in res[:8]: log(f"    {k:6.2f} kg  {mv}")
            win = next(((mv, k, new) for mv, k, new in res if k < kg - MIN_GAIN and geom_ok(build(new), cockpit=True)), None)
            if not win: log("no move saves enough; stop"); break
            mv, kg, spec = win
            rec["rounds"].append({"move": mv, "kg": kg}); rec["spec"] = spec
            log(f"  ACCEPT {mv}: {kg:.2f} kg ({time.time()-t0:.0f} s)", rec)
    rk, rspec = resize(spec, robust=True)
    rec.update(robust_kg=rk, spec=rspec or spec, robust_pass=rspec is not None)
    log(f"FINAL nominal {kg:.2f} kg; robust re-size {rk:.2f} kg pass={rspec is not None} ({time.time()-t0:.0f} s)", rec)
