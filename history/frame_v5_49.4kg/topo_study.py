"""Frame topology study (topo-experiment): greedily remove the heaviest member pair whose removal keeps every frame_opt gate
passing at current sizes, then run the robust gate. BAN lists roles kept for rule reasons. Run: python topo_study.py"""
import sys, numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import frame_opt as fo
key = lambda a, b, r: (r, tuple(sorted((round(a[0]), round(a[1]), abs(round(a[2]))) for a in (a, b))))
FULL = list(fo.BASE); cands = {}
for i, (a, b, s, r) in enumerate(FULL): cands.setdefault(key(a, b, r), set()).add(i)
def ev(gone):
    fo.BASE[:] = [e for i, e in enumerate(FULL) if i not in gone]
    try: return fo.evaluate({})
    except (np.linalg.LinAlgError, ValueError, StopIteration): return (False, 99, 0, 0, [])
BAN = ("Front bulkhead", "Anti-sub floor cross", "Lap belt tab brace")
gone, live = set(), [k for k in cands if k[0] not in BAN and ev(cands[k])[0]]
while True:
    res = [(ev(gone | cands[k]), k) for k in live]
    ok = [(r[3], k, r) for r, k in res if r[0]]
    if not ok: break
    kg, k, r = min(ok, key=lambda x: x[0]); gone |= cands[k]; live = [c for _, c, _ in ok if c != k]
    print(f"remove {k[0]} {k[1]} -> {kg:.2f} kg worst {r[1]:.3f} tors {r[2]:.0f}", flush=True)
g = ev(gone); print(f"NOMINAL pass={g[0]} {g[3]:.2f} kg worst {g[1]:.3f} tors {g[2]:.0f}")
fo.BASE[:] = [e for i, e in enumerate(FULL) if i not in gone]
g = fo.evaluate({}, robust=True); print(f"ROBUST pass={g[0]} {g[3]:.2f} kg worst {g[1]:.3f}")
