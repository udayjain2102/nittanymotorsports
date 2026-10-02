"""Fabrication package for the mule frame.

- Pieces: collinear model members of the same size/role are one piece of tube; each roll hoop is one bent piece.
- Hoops: bend data as feed / rotation / bend (Y-B-C) on a CLR_BY_SIZE die, developed (cut) length.
- Straight pieces: cope (notch) data per end: which tube it lands on, included angle, phase between
  the two ends' notches, and cut length long-point to long-point.
- Nodes: every joint position for the jig, heights measured from the table (bottom of the lower rails).

Outputs fab/tube_cut_sheet.csv, fab/hoop_bend_program.csv, fab/jig_node_coordinates.csv, fab/jig_plan.png.
Run: python fab.py
"""
import csv, math, pathlib
import numpy as np
import mule as m

CLR_BY_SIZE = {"J": 127.0, "H": 101.6, "A": 76.2, "B": 76.2, "C": 76.2}   # bend die centreline radius (5" / 4" / 3"), >= 3 x OD (F.5.2.1)
EXT_GAP = 3.0       # mm a square-cut end runs past the outer face of the biggest tube coped onto it (audit: ends stopped at
                    # the node centre, so the lower half of every tube coped onto them landed on air)
TABLE_Y = m.Y_LOW - m.rad("Lower side impact")                                      # jig table = underside of the lower side-impact tubes
HOOP_ROLES = ("Main hoop", "Front hoop")
RANK = {"J": 5, "H": 4, "A": 3, "B": 2, "C": 1}

def key(p): return tuple(round(c, 1) for c in p)
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def collinear(u, v, tol_deg=1.0): return abs(np.dot(unit(u), unit(v))) > math.cos(math.radians(tol_deg))

def _order(segs):
    """Order a chain of segments (list of (a, b)) into a point list from one free end to the other."""
    adj = {}
    for a, b in segs:
        adj.setdefault(key(a), []).append(b); adj.setdefault(key(b), []).append(a)
    ends = [k for k, v in adj.items() if len(v) == 1]
    start = next(p for a, b in segs for p in (a, b) if key(p) == ends[0])
    pts, prev = [start], None
    while True:
        nxt = [q for q in adj[key(pts[-1])] if prev is None or key(q) != key(prev)]
        if not nxt: return pts
        prev = pts[-1]; pts.append(nxt[0])

def pieces():
    """Merge model members into physical pieces of tube."""
    out, used = [], set()
    for role in HOOP_ROLES:
        segs = [(a, b, s) for a, b, s, r in m.MEMBERS if r == role]
        # the top cross member of a hoop shares the role; the hoop is one continuous bent tube
        out.append(dict(role=role, size=segs[0][2], pts=_order([(a, b) for a, b, _ in segs]), bent=True))
        used.update(i for i, (_, _, _, r) in enumerate(m.MEMBERS) if r == role)
    # straight chains: same size+role, collinear, meeting at a node where only those two of the group meet
    groups = {}
    for i, (a, b, s, r) in enumerate(m.MEMBERS):
        if i not in used: groups.setdefault((s, r), []).append(i)
    for (s, r), idx in groups.items():
        parent = {i: i for i in idx}
        def find(i):
            while parent[i] != i: i = parent[i]
            return i
        at = {}
        for i in idx:
            a, b, _, _ = m.MEMBERS[i]; at.setdefault(key(a), []).append(i); at.setdefault(key(b), []).append(i)
        for k, lst in at.items():
            if len(lst) == 2:
                i, j = lst; ai, bi = m.MEMBERS[i][:2]; aj, bj = m.MEMBERS[j][:2]
                if collinear(np.subtract(bi, ai), np.subtract(bj, aj)): parent[find(i)] = find(j)
        chains = {}
        for i in idx: chains.setdefault(find(i), []).append(m.MEMBERS[i][:2])
        for segs in chains.values():
            out.append(dict(role=r, size=s, pts=_order(segs), bent=False))
    for n, p in enumerate(out): p["id"] = f"P{n + 1:02d}"
    return out

# ---------- hoop bending ----------
def bend_program(pts, clr):
    """Y-B-C bend program for a polyline of tangent-intersection points.
    Returns (rows [(feed Y mm, rotation B deg, bend C deg)], last feed mm, developed length mm, min feed mm)."""
    P = [np.asarray(p, float) for p in pts]
    # drop collinear interior points (straight runs through nodes)
    Q = [P[0]] + [P[i] for i in range(1, len(P) - 1) if not collinear(P[i] - P[i - 1], P[i + 1] - P[i], 0.5)] + [P[-1]]
    d = [unit(Q[i + 1] - Q[i]) for i in range(len(Q) - 1)]
    L = [np.linalg.norm(Q[i + 1] - Q[i]) for i in range(len(Q) - 1)]
    beta = [math.acos(np.clip(np.dot(d[i], d[i + 1]), -1, 1)) for i in range(len(d) - 1)]
    T = [clr * math.tan(b / 2) for b in beta]
    feeds = [L[0] - T[0]] + [L[i] - T[i - 1] - T[i] for i in range(1, len(L) - 1)] + [L[-1] - T[-1]]
    rows, prev_n = [], None
    for i, b in enumerate(beta):
        n = unit(np.cross(d[i], d[i + 1]))
        rot = 0.0 if prev_n is None else math.degrees(math.atan2(np.dot(np.cross(prev_n, n), d[i]), np.dot(prev_n, n)))
        rows.append((feeds[i], rot, math.degrees(b))); prev_n = n
    developed = sum(feeds) + sum(clr * b for b in beta)
    return rows, feeds[-1], developed, min(feeds)

# ---------- coping ----------
def cope_depths(d, r, e, R, n=180):
    """Distances along the piece axis (from the receiver axis) at which the surface of a tube (axis d, radius r)
    meets a receiver tube (axis e through the node, radius R). Returns (long point, short point)."""
    d, e = unit(d), unit(e)
    u = e - np.dot(e, d) * d
    u = unit(u) if np.linalg.norm(u) > 1e-9 else unit(np.cross(d, [1, 0, 0]) if abs(d[0]) < 0.9 else np.cross(d, [0, 1, 0]))
    v = np.cross(d, u); s_all = []
    for phi in np.linspace(0, 2 * math.pi, n, endpoint=False):
        off = r * (math.cos(phi) * u + math.sin(phi) * v)
        # |(s d + off) x e| = R  ->  quadratic in s
        a = np.cross(d, e); b = np.cross(off, e)
        A, B, C = np.dot(a, a), 2 * np.dot(a, b), np.dot(b, b) - R * R
        disc = B * B - 4 * A * C
        if A < 1e-12 or disc < 0: continue
        s_all.append((-B + math.sqrt(disc)) / (2 * A))
    return (min(s_all), max(s_all)) if s_all else (None, None)

def _axis_at(piece, k):
    """Local axis direction of a piece at node key k (segment touching k; average at a bend)."""
    P = piece["pts"]; ks = [key(p) for p in P]; i = ks.index(k)
    dirs = [unit(np.subtract(P[j + 1], P[j])) for j in (i - 1, i) if 0 <= j < len(P) - 1]
    return unit(sum(dirs)) if len(dirs) == 2 and np.dot(*dirs) > 0 else dirs[0]

def receiver(pcs, piece, k):
    """Best tube for this piece end at node k to cope onto: bigger first, then one it meets at >= 20 deg (a shallower
    cope can't be fitted), then through-tubes, heavier, longer."""
    cands = []; d = _axis_at(piece, k)
    for q in pcs:
        if q is piece: continue
        ks = [key(p) for p in q["pts"]]
        if k not in ks: continue
        through = 0 < ks.index(k) < len(ks) - 1
        od, t = m.SIZES[q["size"]]
        length = sum(np.linalg.norm(np.subtract(q["pts"][i + 1], q["pts"][i])) for i in range(len(q["pts"]) - 1))
        ang = math.degrees(math.acos(abs(np.clip(np.dot(d, _axis_at(q, k)), -1, 1))))
        cands.append(((od, ang >= 20, through, t, length), q))   # bigger tube always receives: can't cope 1.25" onto 1"
    return max(cands, key=lambda c: c[0])[1] if cands else None

def cope_ends(pcs):
    rows = []
    for p in pcs:
        od, t = m.SIZES[p["size"]]; r = od / 2
        P = p["pts"]; Lc = sum(np.linalg.norm(np.subtract(P[i + 1], P[i])) for i in range(len(P) - 1))
        ends = []
        for idx, inward in ((0, unit(np.subtract(P[1], P[0]))), (-1, unit(np.subtract(P[-2], P[-1])))):
            k = key(P[idx]); q = receiver(pcs, p, k)
            if q is None: ends.append(None); continue
            e = _axis_at(q, k); R = m.SIZES[q["size"]][0] / 2
            ang = math.degrees(math.acos(abs(np.clip(np.dot(inward, e), -1, 1))))
            if R < r - 0.05:   # every tube here is smaller: square-cut past the node, cap it; the others cope onto this one
                ext = end_extension(pcs, p, k)
                ends.append(dict(node=k, recv=None, angle=90.0, long=-ext, short=-ext, e=e, inward=inward)); continue
            lp, sp = cope_depths(-inward, r, e, R)   # piece axis pointing toward the node
            ends.append(dict(node=k, recv=q, angle=ang, long=lp, short=sp, e=e, inward=inward))
        rows.append((p, Lc, ends))
    return rows

def end_extension(pcs, piece, k):
    """How far (mm) a piece that is the biggest tube at node k must run past the node so every tube coped onto it lands
    on tube: the largest other tube's radius plus EXT_GAP."""
    others = [m.SIZES[q["size"]][0] / 2 for q in pcs if q is not piece and k in [key(p) for p in q["pts"]]]
    return (max(others) + EXT_GAP) if others else 0.0

def corner_offset(pts, clr):
    """{node key: (point on the real bent tube nearest the corner, distance mm)} for each bend of a bent piece: the model's
    corner is the tangent intersection, which sits CLR (1/cos(b/2) - 1) outside the real tube."""
    P = [np.asarray(q, float) for q in pts]; out = {}
    for i in range(1, len(P) - 1):
        u, v = unit(P[i] - P[i - 1]), unit(P[i + 1] - P[i])
        if collinear(u, v, 0.5): continue
        b = math.acos(np.clip(np.dot(u, v), -1, 1)); off = clr * (1 / math.cos(b / 2) - 1)
        out[key(P[i])] = (P[i] + off * unit(v - u), off)
    return out

def phase(end_a, end_b):
    """Rotation between the two notches around the tube axis (deg, 0-180)."""
    d = end_a["inward"]
    pa = end_a["e"] - np.dot(end_a["e"], d) * d; pb = end_b["e"] - np.dot(end_b["e"], d) * d
    if np.linalg.norm(pa) < 1e-6 or np.linalg.norm(pb) < 1e-6: return 0.0
    return math.degrees(math.acos(abs(np.clip(np.dot(unit(pa), unit(pb)), -1, 1))))

SQUARE = "square cut at node, cap end (F.5.3.3)"
def recv_label(end): return end["recv"]["id"] if end["recv"] else SQUARE

def node_names():
    names = {}
    for n, p in m.N.items():
        names[key(p)] = n + "_R"; names[key(m.mir(p))] = n + "_L"
    return names

def extended(pcs, p):
    """A bent piece's polyline with both legs run past their end nodes (end_extension)."""
    P = [np.asarray(q, float) for q in p["pts"]]
    a = P[0] + end_extension(pcs, p, key(P[0])) * unit(P[0] - P[1])
    b = P[-1] + end_extension(pcs, p, key(P[-1])) * unit(P[-1] - P[-2])
    return [a] + P[1:-1] + [b]

def write(out=pathlib.Path(__file__).parent / "fab"):
    out.mkdir(exist_ok=True); pcs = pieces(); nn = node_names()
    with open(out / "tube_cut_sheet.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["piece", "role", "tube (in)", "centreline length mm", "cut length mm (long point to long point)",
                    "end A node", "end A copes onto", "end A angle deg", "end B node", "end B copes onto", "end B angle deg",
                    "notch phase deg", "intermediate nodes (mm from end A)"])
        for p, Lc, ends in cope_ends(pcs):
            if p["bent"]: continue
            a, b = ends; cut = Lc - (a["long"] if a else 0) - (b["long"] if b else 0)
            inter, acc = [], 0.0
            for i in range(1, len(p["pts"]) - 1):
                acc += np.linalg.norm(np.subtract(p["pts"][i], p["pts"][i - 1]))
                inter.append(f"{nn.get(key(p['pts'][i]), '?')}@{acc - (a['long'] if a else 0):.0f}")
            od, t = m.SIZES[p["size"]]
            w.writerow([p["id"], p["role"], f"{od / 25.4:.3f} x {t / 25.4:.3f}", f"{Lc:.1f}", f"{cut:.1f}",
                        nn.get(a["node"], "?"), recv_label(a), f"{a['angle']:.1f}",
                        nn.get(b["node"], "?"), recv_label(b), f"{b['angle']:.1f}", f"{phase(a, b):.0f}", " ".join(inter)])
    with open(out / "hoop_bend_program.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["piece", "hoop", "tube (in)", "CLR mm", "step", "feed Y mm", "rotate B deg", "bend C deg"])
        for p in pcs:
            if not p["bent"]: continue
            clr = CLR_BY_SIZE[p["size"]]; rows, last, dev, _ = bend_program(extended(pcs, p), clr)
            od, t = m.SIZES[p["size"]]
            for i, (y, b, c) in enumerate(rows, 1):
                w.writerow([p["id"], p["role"], f"{od / 25.4:.3f} x {t / 25.4:.3f}", clr, i, f"{y:.1f}", f"{b:.1f}", f"{c:.1f}"])
            w.writerow([p["id"], p["role"], "", clr, "end", f"{last:.1f}", "", f"developed length {dev:.0f} mm (+50 mm grip each end)"])
            ex = [end_extension(pcs, p, key(q)) for q in (p["pts"][0], p["pts"][-1])]
            w.writerow([p["id"], p["role"], "", "", "note", "", "", f"legs run {ex[0]:.0f} / {ex[1]:.0f} mm past the lower rail nodes so the rails land on tube; cap the ends (F.5.3.3)"])
    with open(out / "jig_node_coordinates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node", "X fwd from rear axle mm", "height above table mm", "Z right of centreline mm", "note"])
        real = {}
        for p in pcs:
            if p["bent"]: real.update(corner_offset(p["pts"], CLR_BY_SIZE[p["size"]]))
        for k, n in sorted(nn.items(), key=lambda kv: (kv[0][0], kv[0][2])):
            if k in real:
                q, off = real[k]
                w.writerow([n, f"{q[0]:.1f}", f"{q[1] - TABLE_Y:.1f}", f"{q[2]:.1f}",
                            f"on the bent hoop (model corner is {off:.0f} mm outside the tube); tubes here weld to the bend"])
            else:
                w.writerow([n, f"{k[0]:.1f}", f"{k[1] - TABLE_Y:.1f}", f"{k[2]:.1f}", ""])
    jig_plan(out / "jig_plan.png", pcs, nn)
    return pcs

def jig_plan(path, pcs, nn):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 6))
    for p in pcs:
        P = np.array(p["pts"]); ax.plot(P[:, 0], P[:, 2], color="0.75" if p["bent"] else "0.5", lw=1)
    low = [k for k in nn if k[1] - TABLE_Y < 60]
    for k in low:
        ax.plot(k[0], k[2], "o", color="tab:red", ms=5)
        ax.annotate(f"{nn[k]}\n({k[0]:.0f}, {k[2]:.0f}) h{k[1] - TABLE_Y:.0f}", (k[0], k[2]), fontsize=6,
                    xytext=(3, 3), textcoords="offset points")
    ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_xlabel("X fwd from rear axle (mm)"); ax.set_ylabel("Z right (mm)")
    ax.set_title("Jig plan (top view): red = fixture posts at lower nodes; label = node (X, Z), h = tube-centreline height above table (mm)")
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)

if __name__ == "__main__":
    pcs = write()
    bent = [p for p in pcs if p["bent"]]
    for p in bent:
        rows, last, dev, mn = bend_program(extended(pcs, p), CLR_BY_SIZE[p["size"]])
        print(f"{p['id']} {p['role']}: {len(rows)} bends, developed {dev:.0f} mm, shortest straight {mn:.0f} mm")
        assert mn >= 0, f"{p['role']}: bends overlap (straight between bends < 0) - fix hoop geometry"
    print(f"{len(pcs)} pieces ({len(bent)} bent); wrote fab/tube_cut_sheet.csv, fab/hoop_bend_program.csv, fab/jig_node_coordinates.csv, fab/jig_plan.png")
