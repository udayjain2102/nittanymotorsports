"""FSAE 2026 frame-geometry rules that mule.py's own checks don't cover (see docs/RULES_MATRIX.md).

Every tube role in mule.MEMBERS is mapped to its rule category, then each rule is checked on the member graph:
tube size per job (F.3.2.1), triangulation (F.1.17, tested as a pin-jointed truss that must not fold), hoop shape
and lean (F.5.6.3, F.5.7, F.5.8), braces (F.5.9, F.6.3), mounts off the main hoop and braces (F.5.11.4), bulkhead
support (F.6.2.3), side impact (F.6.4), shoulder bar (F.6.5), main hoop brace supports (F.6.6), steering protection
(F.5.14), hips inside the Major Structure (T.1.3.1) and the open-wheel keep-out zones (V.1.1).
Rules are pass/fail constraints; nothing here is traded for weight.
Run: python frame_rules.py
"""
import math
import numpy as np
from scipy.spatial import Delaunay
import mule as m

# role -> rule category. Anything not listed is "structural" (F.3.2.1.o, Size C minimum).
CATEGORY = {
    "Front hoop": "front_hoop", "Main hoop": "main_hoop", "Shoulder harness bar": "shoulder_bar",
    "Upper side impact": "side_upper", "Lower side impact": "side_lower", "Diagonal side impact": "side_diag",
    "Front bulkhead": "bulkhead", "Front hoop brace": "fh_brace", "Main hoop brace": "mh_brace",
    "FBH support upper": "fbh_upper", "FBH support lower": "fbh_lower", "FBH support lower (pedal box)": "fbh_lower",
    "FBH support diagonal": "fbh_diag", "FBH support front-bay diagonal": "fbh_diag_front",
    "MH brace support upper": "mhs_upper", "MH brace support lower": "mhs_lower", "Rear side diagonal": "mhs_diag",
    "Rear bulkhead": "mhs_post",
    "Anti-sub floor cross": "harness", "Lap belt tab brace": "harness",
}
# F.3.2.1 minimum size per category (A = 1.0 x 0.095, B = 1.0 x 0.065, C = 1.0 x 0.049)
REQUIRED = {"front_hoop": "A", "main_hoop": "A", "shoulder_bar": "A", "side_upper": "B", "side_lower": "B",
            "side_diag": "B", "bulkhead": "B", "fh_brace": "B", "mh_brace": "B", "harness": "B"}
F341 = {"A": (11320, 173, 25.0, 2.0), "B": (8509, 114, 25.0, 1.2), "C": (6695, 91, 25.0, 1.2)}   # I, area, OD, wall
PRIMARY = {"front_hoop", "main_hoop", "shoulder_bar", "side_upper", "side_lower", "side_diag", "bulkhead",
           "fh_brace", "mh_brace", "fbh_upper", "fbh_lower", "fbh_diag", "fbh_diag_front", "mhs_upper", "mhs_lower", "mhs_diag", "mhs_post"}
HIP_HALF_WIDTH = 200.0   # mm, 95th-percentile male pelvis half-breadth (assumption; buck check confirms)
TOL = 1.0

def cat(role): return CATEGORY.get(role, "structural")
def key(p): return tuple(round(c, 1) for c in p)
def members(c): return [(np.array(a, float), np.array(b, float), s, r) for a, b, s, r in m.MEMBERS if cat(r) == c]

def meets(size, req):
    od, t = m.SIZES[size]; I, A = m.tube_props(size); rI, rA, rOD, rt = F341[req]
    return I >= rI and A >= rA and od >= rOD and t >= rt - 0.01

def chain(ms):
    """Order a set of segments into node paths (one per connected piece). Returns list of [points]."""
    adj = {}
    for a, b, *_ in ms:
        adj.setdefault(key(a), []).append(key(b)); adj.setdefault(key(b), []).append(key(a))
    seen, paths = set(), []
    for start in [k for k, v in adj.items() if len(v) == 1] + list(adj):
        if start in seen: continue
        path, cur, prev = [start], start, None
        seen.add(start)
        while True:
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            if not nxt: break
            prev, cur = cur, nxt[0]; path.append(cur); seen.add(cur)
        paths.append([np.array(p) for p in path])
    return paths

def angle_from_vertical(a, b):
    """Side-view (X-Y) angle of segment a-b from vertical, degrees."""
    return math.degrees(math.atan2(abs(b[0] - a[0]), abs(b[1] - a[1]) + 1e-9))

def nodes_of(c): return {key(p) for a, b, *_ in members(c) for p in (a, b)}

def degree_primary():
    deg = {}
    for a, b, s, r in m.MEMBERS:
        if cat(r) in PRIMARY or cat(r) == "structural":
            for p in (a, b): deg[key(p)] = deg.get(key(p), 0) + 1
    return deg

def side_view_triangulated(node, hoop_cat, min_len=50.0):
    """F.5.6.3a: a structural non-hoop tube ends at the node and shows in side view (its X-Y projection is a real tube,
    not a cross member seen end-on)."""
    for a, b, s, r in m.MEMBERS:
        if cat(r) == hoop_cat or cat(r) not in STRUCTURAL: continue
        for p, q in ((a, b), (b, a)):
            if key(p) == key(node) and math.hypot(q[0] - p[0], q[1] - p[1]) >= min_len:
                return True
    return False

def bend_supports():
    """[(role, node, problem or "")] for the farthest-deviation point of every bent primary member (roll hoops excluded)."""
    out = []
    for c in sorted(PRIMARY - {"front_hoop", "main_hoop"}):
        ms = [mb for mb in members(c) if mb[0][2] * mb[1][2] > 0]   # one side only: cross tubes are separate members
        for path in chain(ms):
            if len(path) < 3: continue
            e0, e1 = path[0], path[-1]; line = (e1 - e0) / np.linalg.norm(e1 - e0)
            dev = [np.linalg.norm(np.cross(p - e0, line)) for p in path]
            i = int(np.argmax(dev))
            if dev[i] < 2.0: continue                                   # in a line (within 2 mm)
            node = path[i]; u, v = node - path[i - 1], path[i + 1] - node
            n = np.cross(u, v); n /= np.linalg.norm(n)
            own = {s for a, b, s, r in ms if key(node) in (key(a), key(b))}
            exempt = c in ("side_upper", "shoulder_bar")
            best = "no support tube"
            for a, b, s, r in m.MEMBERS:
                if cat(r) == c or cat(r) not in STRUCTURAL or key(node) not in (key(a), key(b)): continue
                d = np.subtract(b, a); d = d / np.linalg.norm(d)
                ang = math.degrees(math.asin(min(1.0, abs(float(np.dot(d, n))))))
                same = s in own
                if exempt or (same and ang <= 30): best = ""; break
                best = f"nearest support {r} ({s}) at {ang:.0f} deg from the plane" + ("" if same else f", size {s} not {'/'.join(sorted(own))}")
            out.append((ms[0][3], tuple(node), best))
    return out

def seg_gap(a, b, c, d):
    """Closest distance between segments a-b and c-d (3D), sampled finely enough for tubes (2 mm)."""
    a, b, c, d = (np.asarray(x, float) for x in (a, b, c, d))
    n = max(2, int(max(np.linalg.norm(b - a), np.linalg.norm(d - c)) / 2))
    s = np.linspace(0, 1, n)[:, None]
    P, Q = a + s * (b - a), c + s * (d - c)
    return float(np.min(np.linalg.norm(P[:, None, :] - Q[None, :, :], axis=2)))

def clashes(gap=3.0):
    """Tube pairs that share no node but come closer than their radii + gap (they would pass through each other)."""
    out = []; ms = list(m.MEMBERS)
    for i in range(len(ms)):
        a, b, s1, r1 = ms[i]
        for j in range(i + 1, len(ms)):
            c, d, s2, r2 = ms[j]
            if {key(a), key(b)} & {key(c), key(d)}: continue
            lo = np.minimum(np.minimum(a, b), np.minimum(c, d)); hi = np.maximum(np.maximum(a, b), np.maximum(c, d))
            if np.any(np.minimum(np.maximum(a, b), np.maximum(c, d)) - np.maximum(np.minimum(a, b), np.minimum(c, d)) < -60): continue
            need = m.SIZES[s1][0] / 2 + m.SIZES[s2][0] / 2 + gap
            g = seg_gap(a, b, c, d)
            if g < need: out.append((r1, r2, g, need))
    return out

THIGH, SHANK, LEG_R, KNEE_Z = 490.0, 500.0, 60.0, 120.0   # mm, 95th-percentile male hip-knee and knee-ankle joint lengths,
                                                         # leg radius, knee centre off the car centreline: ESTIMATES (buck check)
def legs_outside(n=12):
    """T.1.3.2: leg surface points ahead of the front hoop that fall outside the structural tubing projected in side view
    (X-Y) and front view (Z-Y). Knee from a two-link leg, hip at mule.HIP, ankle just behind the pedal face."""
    hip = np.array(m.HIP, float); ank = np.array([m.X_PEDAL - 50.0, m.N["pb0"][1] + 110.0])
    d = np.linalg.norm(ank - hip); a = (THIGH**2 - SHANK**2 + d**2) / (2 * d); h = math.sqrt(max(THIGH**2 - a**2, 0.0))
    u = (ank - hip) / d; knee = hip + a * u + h * np.array([-u[1], u[0]])      # knee rises above the hip-ankle line
    pts = [p for s in np.linspace(0, 1, n) for p in (hip + s * (knee - hip), knee + s * (ank - knee))]
    pts = [p for p in pts if p[0] >= m.X_FRONT]
    ahead = [(a_, b_) for a_, b_, s, r in m.MEMBERS if cat(r) in STRUCTURAL and min(a_[0], b_[0]) >= m.X_FRONT - 1]
    side = Delaunay(np.array([(q[0], q[1]) for a_, b_ in ahead for q in (a_, b_)]))
    front = Delaunay(np.array([(q[2], q[1]) for a_, b_ in ahead for q in (a_, b_)]))
    out_s = [p for p in pts if side.find_simplex((p[0], p[1] + LEG_R)) < 0]
    out_f = [p for p in pts for z in (KNEE_Z + LEG_R, -(KNEE_Z + LEG_R)) if front.find_simplex((z, p[1] + LEG_R)) < 0]
    return out_s, out_f, knee + np.array([0, LEG_R])

def leg_clearance(margin=10.0, n=24):
    """Smallest (tube surface to leg surface) gap, mm, and the tube: each leg is a LEG_R capsule hip -> knee -> ankle ->
    toe at the pedal face, at z = +-KNEE_Z. The T.1.2 template may rise over a tube; the legs can't (topology search find)."""
    hip = np.array(m.HIP, float); ank = np.array([m.X_PEDAL - 50.0, m.N["pb0"][1] + 110.0])
    knee = legs_outside()[2] - np.array([0, LEG_R]); toe = np.array([m.X_PEDAL, ank[1] + 150.0])   # toe: estimate
    worst = (1e9, "")
    for zs in (KNEE_Z, -KNEE_Z):
        leg = [np.array([*p, zs]) for p in (hip, knee, ank, toe)]
        for a, b, s, r in m.MEMBERS:
            a, b = np.array(a, float), np.array(b, float)
            for q in a + np.linspace(0, 1, n)[:, None] * (b - a):
                for u, v in zip(leg, leg[1:]):
                    t = np.clip(np.dot(q - u, v - u) / np.dot(v - u, v - u), 0, 1)
                    g = np.linalg.norm(q - (u + t * (v - u))) - LEG_R - m.SIZES[s][0] / 2
                    if g < worst[0]: worst = (g, r)
    return worst

# ---------- triangulation (F.1.17): each side, in side view, must be a truss that cannot fold ----------
STRUCTURAL = PRIMARY | {"structural", "harness"}   # F.1.17: triangles may use any Structural (Size C or larger) tube

def side_mechanisms(sign=1, cats=STRUCTURAL):
    """Number of Primary Structure joints that can move (non-rigid modes) when one side's members (z * sign > 0, cross members excluded),
    projected to side view (X, Y) and treated as a pin-jointed 2D truss. Straight runs through a node are merged first,
    so a node in the middle of a straight tube doesn't count as a hinge."""
    k2 = lambda p: (round(p[0], 0), round(p[1], 0))
    segs = [(k2(a), k2(b)) for a, b, s, r in m.MEMBERS
            if cat(r) in cats and a[2] * sign > 1 and b[2] * sign > 1 and k2(a) != k2(b)]
    segs = list({tuple(sorted(sg)) for sg in segs})
    changed = True
    while changed:
        changed = False
        adj = {}
        for i, (a, b) in enumerate(segs):
            adj.setdefault(a, []).append(i); adj.setdefault(b, []).append(i)
        for n, idx in adj.items():
            if len(idx) != 2: continue
            (a1, b1), (a2, b2) = segs[idx[0]], segs[idx[1]]
            o1 = a1 if b1 == n else b1; o2 = a2 if b2 == n else b2
            u, v = np.subtract(n, o1), np.subtract(o2, n)
            if abs(u[0] * v[1] - u[1] * v[0]) / (np.linalg.norm(u) * np.linalg.norm(v)) < 0.02:
                segs = [sg for i, sg in enumerate(segs) if i not in idx] + [tuple(sorted((o1, o2)))]; changed = True; break
    nodes = sorted({p for sg in segs for p in sg}); ix = {p: i for i, p in enumerate(nodes)}
    K = np.zeros((2 * len(nodes), 2 * len(nodes)))
    for a, b in segs:
        d = np.subtract(b, a); L = np.linalg.norm(d); e = d / L; k = np.outer(e, e) / L
        for i, j, sg in ((ix[a], ix[a], 1), (ix[b], ix[b], 1), (ix[a], ix[b], -1), (ix[b], ix[a], -1)):
            K[2 * i:2 * i + 2, 2 * j:2 * j + 2] += sg * k
    # a straight tube running through a joint can't kink there: keep the joint on the line of its two collinear neighbours
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    for n, nb in adj.items():
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                u, v = np.subtract(n, nb[i]), np.subtract(nb[j], n)
                if abs(u[0] * v[1] - u[1] * v[0]) / (np.linalg.norm(u) * np.linalg.norm(v)) < 0.02 and np.dot(u, v) > 0:
                    t = np.linalg.norm(u) / (np.linalg.norm(u) + np.linalg.norm(v)); d = (u + v) / np.linalg.norm(u + v)
                    nperp = np.array([-d[1], d[0]]); g = np.zeros(2 * len(nodes))
                    g[2 * ix[n]:2 * ix[n] + 2] += nperp
                    g[2 * ix[nb[i]]:2 * ix[nb[i]] + 2] -= (1 - t) * nperp
                    g[2 * ix[nb[j]]:2 * ix[nb[j]] + 2] -= t * nperp
                    K += np.outer(g, g) / (np.linalg.norm(u) + np.linalg.norm(v))
    w, V = np.linalg.eigh(K)
    P = np.array(nodes, float); c = P.mean(0)
    rigid = np.array([np.tile([1.0, 0.0], len(nodes)), np.tile([0.0, 1.0], len(nodes)),
                      np.ravel([[-(y - c[1]), x - c[0]] for x, y in P])]).T
    Q, _ = np.linalg.qr(rigid)
    prim = {k2(p) for a, b, s_, r in m.MEMBERS if cat(r) in PRIMARY for p in (a, b)}
    zero = V[:, w < w.max() * 1e-9]
    zero = zero - Q @ (Q.T @ zero)                       # remove rigid-body motion
    U, sv, _ = np.linalg.svd(zero, full_matrices=False) if zero.size else (np.zeros((len(w), 0)), np.zeros(0), None)
    moving = set()
    for i in range(int(np.sum(sv > 1e-6))):
        mv = np.linalg.norm(U[:, i].reshape(-1, 2), axis=1)
        moving |= {nodes[j] for j in np.flatnonzero(mv > 1e-3 * mv.max())}
    prim_moving = sorted(moving & prim)
    names = {k2(p): n for n, p in m.N.items()}
    return len(prim_moving), [names.get(q, q) for q in prim_moving], len(nodes)

# ---------- envelopes ----------
def hull(points): return Delaunay(np.array(points, float))
def inside(h, p): return h.find_simplex(np.asarray(p, float)) >= 0

def primary_points(exclude_above_sis=False):
    pts = []
    y_sis_top = m.Y_SIS + m.rad("Upper side impact")
    for a, b, s, r in m.MEMBERS:
        c = cat(r)
        if c not in PRIMARY: continue
        if exclude_above_sis and (c == "mh_brace" or (c in ("main_hoop", "shoulder_bar") and min(a[1], b[1]) >= y_sis_top - TOL)):
            continue
        pts += [a, b]
    return pts

def mount_points():
    """Engine and suspension mount points (F.5.11.4)."""
    import rocker
    pts = {}
    for axle in ("front", "rear"):
        for n, p, q, node in m.susp_links(axle):
            pts[f"{axle} {n} inboard"] = np.array(q, float)
        pts[f"{axle} shock frame end"] = np.array(rocker.design(axle)["S"], float)
    for n in ("em_fb", "em_ft", "em_rb"):
        pts[f"engine mount {n}"] = np.array(m.N[n], float)
    return pts

def seg_interior_dist(p, a, b, end_clear=20.0):
    ab = b - a; L = np.linalg.norm(ab); t = np.dot(p - a, ab) / L
    if t < end_clear or t > L - end_clear: return 1e9
    return np.linalg.norm(p - (a + ab * t / L))

# ---------- checks ----------
def checks():
    R = []
    def ok(name, cond, detail=""): R.append((name, bool(cond), detail))

    import fab
    tight = [f"{p['role']} CLR {fab.CLR_BY_SIZE[p['size']]:.0f} < 3 x {m.SIZES[p['size']][0]:.1f}" for p in fab.pieces()
             if p["bent"] and fab.CLR_BY_SIZE[p["size"]] < 3 * m.SIZES[p["size"]][0]]
    ok("F.5.2.1 every bend radius (tube centreline) >= 3 x tube OD", not tight, "; ".join(tight) or
       ", ".join(f"{s}: CLR {fab.CLR_BY_SIZE[s]:.0f} vs {3 * m.SIZES[s][0]:.0f}" for s in sorted({p["size"] for p in fab.pieces() if p["bent"]})))
    cl = clashes()
    ok("frame tubes that share no joint stay >= 3 mm apart (no tube passes through another; ours, fab)", not cl,
       "; ".join(f"{a} / {b} {g:.1f} vs {n:.1f} mm" for a, b, g, n in cl) or "none")
    bad = sorted({f"{r} ({s} needs {REQUIRED.get(cat(r), 'C')})" for a, b, s, r in m.MEMBERS if not meets(s, REQUIRED.get(cat(r), "C"))})
    ok("F.3.2.1 every tube meets the size its job requires", not bad, "all OK" if not bad else "; ".join(bad))

    for sg, side in ((1, "right"), (-1, "left")):
        mech, which, nn = side_mechanisms(sg)
        ok(f"F.1.17 / F.5.6.2 Primary Structure triangulated in side view ({side}): no primary joint can move in a pin-jointed truss", mech == 0,
           f"{nn} joints; " + (f"movable primary joints: {', '.join(map(str, which))}" if which else "none movable"))

    deg = degree_primary()
    y_brace = {}
    for c, top in (("main_hoop", "mh_brace"), ("front_hoop", "fh_brace")):
        ys = [max(a[1], b[1]) for a, b, *_ in members(top)]
        y_brace[c] = min(ys) if ys else 1e9
        bends_ok = True; bad_bends = []
        for path in chain(members(c)):
            for i in range(1, len(path) - 1):
                u, v = path[i] - path[i - 1], path[i + 1] - path[i]
                kink = math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
                if kink > 1 and path[i][1] < y_brace[c] - TOL and not side_view_triangulated(path[i], c):
                    bends_ok = False; bad_bends.append(f"y {path[i][1]:.0f}")
        ok(f"F.5.6.3 {c.replace('_', ' ')} bends below its braces are at nodes triangulated in side view", bends_ok,
           ", ".join(bad_bends) or "all triangulated")

    # F.5.2.3 a primary member made of tubes not in a line (other than the roll hoops) needs a support tube at the point
    # of greatest deviation from the line joining its ends (a), ending at a chassis node (b), and (c, except the upper side
    # impact member and the shoulder bar) of the same diameter and thickness, within 30 deg of the bent member's plane.
    unsupported = [f"{r} at ({x:.0f}, {y:.0f}, {z:.0f}): {why}" for r, (x, y, z), why in bend_supports() if why]
    ok("F.5.2.3 every bent primary member has a same-size support tube within 30 deg of its plane at its farthest point",
       not unsupported, "; ".join(unsupported) or "all supported")

    low = min(min(a[1], b[1]) for a, b, *_ in members("side_lower"))
    y_sis_top = max(max(a[1], b[1]) for a, b, *_ in members("side_upper")) + m.rad("Upper side impact")
    for c, name, lim in (("front_hoop", "F.5.7", 20.0), ("main_hoop", "F.5.8", 10.0)):
        paths = chain(members(c))
        ends = [p for path in paths for p in (path[0], path[-1])]
        ok(f"{name}.3/{name}.2 {c.replace('_', ' ')} is one piece from the lowest frame member side to side",
           len(paths) == 1 and all(abs(p[1] - low) < 30 for p in ends), f"{len(paths)} piece(s), ends at y {[round(p[1]) for p in ends]}")
        upper = [(a, b) for a, b, *_ in members(c) if min(a[1], b[1]) >= m.Y_SIS - TOL and abs(a[1] - b[1]) > 1]
        worst = max((angle_from_vertical(a, b) for a, b in upper), default=0.0)
        ok(f"{name} {c.replace('_', ' ')} above the upper side impact < {lim:.0f} deg from vertical", worst < lim, f"{worst:.1f} deg")
    lower_mh = [(a, b) for a, b, *_ in members("main_hoop") if max(a[1], b[1]) <= m.Y_SIS + TOL and abs(a[1] - b[1]) > 1]
    rear_lean = max((math.degrees(math.atan2((a[0] if a[1] > b[1] else b[0]) - (b[0] if a[1] > b[1] else a[0]), abs(a[1] - b[1]))) * -1 for a, b in lower_mh), default=0.0)
    ok("F.5.8.3b main hoop below the upper side impact not rearward > 10 deg", rear_lean <= 10, f"{rear_lean:.1f} deg")

    # braces
    for c, hoop, name, fwd in (("mh_brace", "main_hoop", "F.5.9", None), ("fh_brace", "front_hoop", "F.6.3", True)):
        ms = members(c); paths = chain(ms)
        straight = all(len(p) == 2 or truss_line(p) for p in paths)
        ok(f"{name} two {c.replace('_', ' ')}s, one per side, each straight", len(paths) == 2 and straight, f"{len(paths)} brace(s)")
        top = max(nodes_of(hoop), key=lambda k: k[1])
        if fwd:
            ok("F.6.3.2 front hoop braces extend forward", all(max(p[0][0], p[-1][0]) > top[0] for p in paths))
            bh = nodes_of("bulkhead"); feet = [min((tuple(p[0]), tuple(p[-1])), key=lambda q: -q[0]) for p in paths]
            ok("F.6.3.3 front hoop braces end at the bulkhead or a triangulated node",
               all(key(f) in bh or deg.get(key(f), 0) >= 3 for f in feet))
        else:
            hoop_body = np.mean([p[0] for p in nodes_of("main_hoop")]) - top[0]
            feet_x = [min((p[0], p[-1]), key=lambda q: q[1])[0] - top[0] for p in paths]
            ok("F.5.9.3 main hoop and its braces on opposite sides of the vertical through the top",
               all(abs(hoop_body) < 5 or np.sign(fx) != np.sign(hoop_body) for fx in feet_x), f"hoop body dx {hoop_body:.0f}")
    fh_upper = [(a, b) for a, b, *_ in members("front_hoop") if min(a[1], b[1]) >= m.Y_SIS - TOL and abs(a[1] - b[1]) > 1]
    lean_back = max(((max(a, b, key=lambda q: q[1])[0] - min(a, b, key=lambda q: q[1])[0]) for a, b in fh_upper), default=0)
    ok("F.6.3.5 front hoop above the side impact does not lean rearward > 10 deg (else extra braces)",
       all(angle_from_vertical(a, b) <= 10 or (max(a, b, key=lambda q: q[1])[0] >= min(a, b, key=lambda q: q[1])[0]) for a, b in fh_upper))

    # F.5.11.4 no engine / suspension mounts on the main hoop braces or the main hoop above its other nodes
    spans = [(a, b) for a, b, *_ in members("mh_brace")] + \
            [(a, b) for a, b, *_ in members("main_hoop") if min(a[1], b[1]) >= m.Y_SIS - TOL]
    hits = [n for n, p in mount_points().items() for a, b in spans
            for q in (p, np.array(m.mir(tuple(p)))) if seg_interior_dist(q, a, b) < 20]
    ok("F.5.11.4 no engine or suspension mounts on the main hoop or brace spans", not hits, ", ".join(sorted(set(hits))) or "none")

    # F.6.2.3 front bulkhead support
    bh_top = max(a[1] for a, b, *_ in members("bulkhead") for a in (a, b)); bh_bot = min(a[1] for a, b, *_ in members("bulkhead") for a in (a, b))
    fh = nodes_of("front_hoop"); bh = nodes_of("bulkhead")
    up = chain(members("fbh_upper"))
    up_ok = any(abs(max(p[0], p[-1], key=lambda q: q[0])[1] + m.rad("FBH support upper") - (bh_top + m.rad("Front bulkhead"))) <= 50
                and key(min(p[0], p[-1], key=lambda q: q[0])) in fh
                and (y_sis_top - (min(p[0], p[-1], key=lambda q: q[0])[1] + m.rad("FBH support upper"))) <= 50 for p in up)
    ok("F.6.2.3a upper bulkhead support within 50 mm of the bulkhead top and of the upper side impact at the front hoop", up_ok)
    lo = chain(members("fbh_lower"))
    lo_ok = any(abs(max(p[0], p[-1], key=lambda q: q[0])[1] - bh_bot) < TOL and key(min(p[0], p[-1], key=lambda q: q[0])) in fh
                and abs(min(p[0], p[-1], key=lambda q: q[0])[1] - low) < 30 for p in lo)
    ok("F.6.2.3c lower bulkhead support from the bulkhead base to the front hoop base", lo_ok)
    ok("F.6.2.3d bulkhead support diagonal fitted (triangulation checked by the truss test)", len(members("fbh_diag")) + len(members("fbh_diag_front")) >= 2)
    deg = {}
    for a, b, *_ in members("bulkhead"):
        for p in (a, b): deg[key(p)] = deg.get(key(p), 0) + 1
    open_ = [n for n, d in deg.items() if d < 2]
    ok("F.6.2 front bulkhead is a closed perimeter (the AIP mounts around it)", not open_, f"{len(open_)} open ends" if open_ else "closed")
    tabs = [m.N["lap"], m.mir(m.N["lap"]), m.N["as_c"]]   # lap and anti-sub belt tab nodes (harness.py)
    weak = [key(t) for t in tabs if not any(meets(s, REQUIRED["harness"]) for a, b, s, _ in m.MEMBERS
                                            if key(t) in (key(a), key(b)))]
    ok("F.3.2.1 every lap / anti-sub tab node sits on a harness-size (or larger) tube", not weak, ", ".join(map(str, weak)) or "all")
    tops = [max(p[0], p[-1], key=lambda q: q[0]) for p in up]
    rise = max(t[1] + m.rad("FBH support upper") - y_sis_top for t in tops)
    ok("F.6.2.3b upper bulkhead support <= 100 mm above the upper side impact, or triangulated back (side-view truss test)",
       rise <= 100 or all(side_mechanisms(sg)[0] == 0 for sg in (1, -1)), f"{rise:.0f} mm")

    # F.6.4 side impact
    mh, fhn = nodes_of("main_hoop"), nodes_of("front_hoop")
    for c, label in (("side_upper", "upper"), ("side_lower", "lower")):
        ok_c = all(len(p) >= 2 and {key(p[0]), key(p[-1])} & mh and {key(p[0]), key(p[-1])} & fhn for p in chain(members(c)))
        ok(f"F.6.4.4/5 {label} side impact connects the main hoop and front hoop", ok_c and len(chain(members(c))) == 2)
    dg = chain(members("side_diag")); su, sl = nodes_of("side_upper"), nodes_of("side_lower")
    ok("F.6.4.6 diagonal side impact joins upper and lower members between the hoops",
       len(dg) == 2 and all(({key(p[0]), key(p[-1])} & su) and ({key(p[0]), key(p[-1])} & sl)
                            and m.X_MAIN - TOL <= min(p[0][0], p[-1][0]) and max(p[0][0], p[-1][0]) <= m.X_FRONT + TOL for p in dg))
    ok("F.6.4.3 three or more side impact members each side", min(len(members(c)) for c in ("side_upper", "side_lower", "side_diag")) >= 2)

    # F.6.5 shoulder bar
    sbp = chain(members("shoulder_bar"))
    ends_on_mh = len(sbp) == 1 and key(sbp[0][0]) in mh and key(sbp[0][-1]) in mh
    ok("F.6.5.1 shoulder harness bar is one piece attached to the main hoop both sides", ends_on_mh)
    straight = len(sbp) == 1 and truss_line(sbp[0])
    ok("F.6.5.2 shoulder bar straight (a bent bar would need braces at the bends)", straight)
    inner = {key(p) for path in sbp for p in path[1:-1]}
    others = [r for a, b, s, r in m.MEMBERS if cat(r) != "shoulder_bar" and (key(a) in inner or key(b) in inner)]
    ok("F.6.5.3 shoulder bar loaded only by the shoulder harness", not others, ", ".join(others) or "only harness tabs")

    # F.6.6 main hoop brace supports
    feet = [min((p[0], p[-1]), key=lambda q: q[1]) for p in chain(members("mh_brace"))]
    upper_ok = all(any({key(f), key(np.array(m.N["mh_sis"]))} <= {key(p[0]), key(p[-1])} or
                       {key(f), key(np.array(m.mir(m.N["mh_sis"])))} <= {key(p[0]), key(p[-1])} for p in chain(members("mhs_upper"))) for f in feet)
    ok("F.6.6.2a upper brace support runs from the brace foot to the upper side impact node on the main hoop", upper_ok)
    lower_ends = {key(p[0]) for p in chain(members("mhs_lower"))} | {key(p[-1]) for p in chain(members("mhs_lower"))}
    ok("F.6.6.2b lower brace support ends at the lower side impact node on the main hoop",
       key(np.array(m.N["mh_bot"])) in lower_ends and key(np.array(m.mir(m.N["mh_bot"]))) in lower_ends)

    # F.5.14 steering rack inside the Primary Structure; T.1.3.1 hips inside the Major Structure
    H = hull(primary_points()); x, y, z = m.RACK
    rack_in = all(inside(H, (x, y, s * (z + m.RACK_R))) for s in (1, -1))
    ok("F.5.14 steering rack inside the Primary Structure (no separate protection needed)", rack_in, f"rack ends z ±{z + m.RACK_R:.0f}")
    Hm = hull(primary_points(exclude_above_sis=True)); hx, hy = m.HIP
    pts = [(hx + 100 * math.cos(t), hy + 100 * math.sin(t), zz) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)
           for zz in (0.0, HIP_HALF_WIDTH, -HIP_HALF_WIDTH)]
    out = [p for p in pts if not inside(Hm, p)]
    ok("T.1.3.1 driver's hips inside the Major Structure", not out, f"{len(out)} of {len(pts)} hip points outside (hip half-width {HIP_HALF_WIDTH:.0f} assumed)")
    out_s, out_f, knee = legs_outside()
    ok("T.1.3.2 driver's legs ahead of the front hoop inside the structural tubing in side and front view (95th male, estimated)",
       not out_s and not out_f, f"knee top at x {knee[0]:.0f}, y {knee[1]:.0f}; {len(out_s)} side-view / {len(out_f)} front-view leg points outside")
    g, who = leg_clearance()
    ok("T.1.3.2 / ours: no tube within 10 mm of the driver's legs and feet (95th male capsules, estimated)", g >= 10, f"{g:.0f} mm ({who})")

    # V.1.1 open wheel: frame and impact attenuator out of the tyre zones (wing: aero.py T.7.6.3)
    zin, zout = m.TRACK_F / 2 - m.TIRE_W / 2, m.TRACK_F / 2 + m.TIRE_W / 2
    r = m.TIRE_OD / 2; clash = []
    for xa, label in ((0.0, "rear"), (m.WHEELBASE, "front")):
        for a, b, s, ro in m.MEMBERS:
            od = m.SIZES[s][0] / 2
            for t in np.linspace(0, 1, 25):
                p = np.array(a) + t * (np.array(b) - np.array(a))
                if abs(p[2]) + od > zin and abs(p[2]) - od < zout and abs(p[0] - xa) < r + 75 + od:
                    clash.append(f"{ro} ({label})"); break
        ia = m.IA
        if label == "front" and ia[4] > zin and ia[1] > xa - r - 75 and ia[0] < xa + r + 75:
            clash.append("impact attenuator")
    ok("V.1.1 nothing in the tyre zones: above, beside, or within 75 mm fore/aft (frame, attenuator)", not clash, ", ".join(sorted(set(clash))) or "clear")
    return R

def truss_line(path):
    """True if a node path is straight (all points on one line)."""
    a, b = path[0], path[-1]; d = (b - a) / np.linalg.norm(b - a)
    return all(np.linalg.norm((p - a) - np.dot(p - a, d) * d) < 1.0 for p in path)

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:95s} {d}")
    assert all(p for _, p, _ in res), "frame rule check failed"
