"""Rocker (bellcrank) design: pushrod -> rocker at a frame node -> shock to another frame node.

Planar rocker in the plane through the pivot P containing the pushrod direction and P->S (S = shock
chassis mount). Pushrod line passes H_P from P; the shock line is tangent to a circle of radius
ROCKER x H_P about P, so the rocker ratio (shock travel / pushrod travel) = springs.ROCKER at ride height.
Shock: SHOCK_EYE eye-to-eye, SHOCK_STROKE stroke, set at SAG of stroke at ride height.
Run: python rocker.py
"""
import math
import numpy as np
import mule as m
import springs

SHOCK_EYE, SHOCK_STROKE, SAG = 230.0, 65.0, 0.36   # mm; 230x65 MTB coil shock, static at 36 % of stroke (droop 25 / bump 50 mm)
H_P = {"front": 90.0, "rear": 60.0}                 # pushrod lever arm about the pivot, mm (rear 60 keeps the shock arm under 150 with the C2 pivot at r_top 328)
A_SHIFT = {"front": 20.0, "rear": 0.0}            # pushrod pickup moved along the pushrod line: front +10 % progressive (0 gives a linear front)
SHOCK_MOUNT = {"front": "fh_sis", "rear": "r_bot"}  # shock chassis end. Front: front hoop at SIS height, clear of the T.1.2 template
BRACKET = {"front": (80.0, 40.0, 0.0), "rear": (-80.0, -30.0, 40.0)}  # shock eye offset from its node (bracket), mm; grid-searched for clearance
SHOCK_R = 25.0                                      # shock body/spring radius for clearance
TANGENT_SIDE = {"front": -1, "rear": -1}            # which of the two mirror-image shock tangents (equal rocker size) to use

def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)

def design(axle):
    """Rocker geometry in 3D (right side): pivot P, pushrod pickup A, shock pickup B, shock mount S, plane basis."""
    *_, (_, U, _, pnode) = m.susp_links(axle)
    P, U = np.array(m.N[pnode], float), np.array(U, float)
    S = np.array(m.N[SHOCK_MOUNT[axle]], float) + np.array(BRACKET[axle])
    d = unit(P - U)                                  # pushrod direction, upright -> rocker
    e1 = d; e2 = unit((S - P) - np.dot(S - P, d) * d)  # in-plane basis
    to2 = lambda v: np.array([np.dot(v, e1), np.dot(v, e2)]); to3 = lambda w: P + w[0] * e1 + w[1] * e2
    s = to2(S - P); hs = springs.ROCKER[axle] * H_P[axle]; L = SHOCK_EYE - SAG * SHOCK_STROKE
    # tangent from S to the circle |x| = hs, then walk L along it from S. The two tangents are mirror images with
    # equal |B|, so the side is fixed explicitly: picking "the smaller" was decided by the last bit of rounding and
    # flipped the front rocker on some CI CPUs (frame FoS 0.83 instead of 1.26).
    ds = np.linalg.norm(s); t = math.sqrt(ds * ds - hs * hs)
    ang = math.atan2(-s[1], -s[0]) + TANGENT_SIDE[axle] * math.asin(hs / ds)   # direction from S along the tangent
    best = s + L * np.array([math.cos(ang), math.sin(ang)])
    g = dict(P=P, S=S, U=U, d=d, A2=np.array([A_SHIFT[axle], H_P[axle]]), B2=best, s2=s, to3=to3, to2=to2, L=L, tangent=t, axle=axle)
    # pushrod line (along e1) passes H_P from P; pick the side that COMPRESSES the shock in bump
    if shock_length(g, 5)[0] > shock_length(g, -5)[0]: g["A2"] = np.array([g["A2"][0], -g["A2"][1]])
    return g

def rot(v, th): c, s_ = math.cos(th), math.sin(th); return np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]])

def shock_length(g, wheel_t):
    """Shock eye-to-eye length at wheel travel wheel_t (mm, + bump)."""
    dp = (springs.motion(g["axle"], 0) - springs.motion(g["axle"], wheel_t))   # pushrod end moves toward the rocker by dp
    Lp = 400.0; U0 = g["A2"] - np.array([Lp, 0.0]); U = U0 + np.array([dp, 0.0])
    lo, hi = -1.2, 1.2   # rocker rotation that keeps the pushrod length
    f = lambda th: np.linalg.norm(rot(g["A2"], th) - U) - Lp
    for _ in range(80):
        mid = (lo + hi) / 2; (lo, hi) = (lo, mid) if f(lo) * f(mid) <= 0 else (mid, hi)
    th = (lo + hi) / 2
    return np.linalg.norm(rot(g["B2"], th) - g["s2"]), math.degrees(th)

def analyse(axle):
    g = design(axle)
    L0, _ = shock_length(g, 0)
    Lb, thb = shock_length(g, springs.TRAVEL); Lr, thr = shock_length(g, -springs.DROOP)
    mr = lambda t: (shock_length(g, t - 1)[0] - shock_length(g, t + 1)[0]) / 2
    mr0, mrb, mrr = mr(0), mr(springs.TRAVEL - 1), mr(-springs.DROOP + 1)
    # shock body clearance to frame tubes (except the tubes meeting at its two ends)
    B3, S3 = g["to3"](g["B2"]), g["S"]; worst = (1e9, "")
    Sn = np.array(m.N[SHOCK_MOUNT[axle]], float)
    tubes = [(a, b, m.SIZES[sz][0] / 2, role) for a, b, sz, role in m.MEMBERS]
    tubes += [(p, q, (m.PUSHROD_TUBE if n == "pushrod" else m.SUSP_TUBE)[0] / 2, n) for n, p, q, _ in m.susp_links(axle)]
    for a, b, rad, role in tubes:
        a, b = np.array(a, float), np.array(b, float)
        if any(np.linalg.norm(x - y) < 1 for x in (a, b) for y in (g["P"], Sn)): continue   # tubes at the rocker pivot / bracket node
        for k in np.linspace(0, 1, 21):   # sample along the shock
            p = B3 + k * (S3 - B3); ab = b - a
            q = a + np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1) * ab
            gap = np.linalg.norm(p - q) - SHOCK_R - rad
            if gap < worst[0]: worst = (gap, role)
    return dict(g=g, L0=L0, stroke=Lr - Lb, Lmin=Lb, Lmax=Lr, rot=(thr, thb), mr0=mr0, prog=(mrb - mrr) / mr0,
                r_A=np.linalg.norm(g["A2"]), r_B=np.linalg.norm(g["B2"]), clearance=worst,
                A3=g["to3"](g["A2"]), B3=B3)

def reactions(axle, pushrod_force_on_rocker):
    """Split a pushrod force (vector on the rocker at A) into chassis loads: {pivot node: F, shock-mount node: F}."""
    r = analyse(axle); g = r["g"]; P, A, B, S = g["P"], r["A3"], r["B3"], g["S"]
    n = unit(np.cross(A - P, B - P)); w = unit(S - B); F = np.asarray(pushrod_force_on_rocker, float)
    fs = -np.dot(np.cross(A - P, F), n) / np.dot(np.cross(B - P, w), n)    # shock force magnitude along B->S
    FB = fs * w
    pnode = m.susp_links(axle)[-1][3]
    return {pnode: F + FB, SHOCK_MOUNT[axle]: -FB}, fs

def checks():
    out = []
    for axle in ("front", "rear"):
        r = analyse(axle); target = springs.MR[axle]
        out += [
            (f"{axle} shock stays in {SHOCK_EYE - SHOCK_STROKE:.0f}-{SHOCK_EYE:.0f} mm over +{springs.TRAVEL:.0f}/-{springs.DROOP:.0f} mm wheel",
             SHOCK_EYE - SHOCK_STROKE <= r["Lmin"] and r["Lmax"] <= SHOCK_EYE, f"{r['Lmin']:.0f}-{r['Lmax']:.0f} mm (static {r['L0']:.0f})"),
            (f"{axle} motion ratio within 10% of springs.py target", abs(r["mr0"] / target - 1) <= 0.10,
             f"{r['mr0']:.2f} vs {target:.2f}"),
            (f"{axle} ratio change over travel -5..+20% (not regressive)", -0.05 <= r["prog"] <= 0.20, f"{100 * r['prog']:+.0f}% (bump vs droop)"),
            (f"{axle} rocker swing < 35 deg each way", max(abs(x) for x in r["rot"]) < 35, f"{r['rot'][0]:+.0f}/{r['rot'][1]:+.0f} deg"),
            (f"{axle} shock body clears frame tubes >= 5 mm", r["clearance"][0] >= 5, f"{r['clearance'][0]:.0f} mm ({r['clearance'][1]})"),
            (f"{axle} rocker arms 40-150 mm", 40 <= r["r_A"] <= 150 and 40 <= r["r_B"] <= 150, f"pushrod arm {r['r_A']:.0f}, shock arm {r['r_B']:.0f} mm"),
        ]
    return out

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:58s} {d}")
    assert all(p for _, p, _ in res), "rocker check failed"
