"""Cockpit templates (FSAE 2026 T.1.1 opening, T.1.2 internal cross section) as geometric pass/fail checks.

T.1.1: a horizontal plan-view template (600 long, 400 wide at the front, 550 at 100 mm from the rear, 350 at the
rear) is lowered between the hoops, with fore/aft translation allowed, until it is 25 mm below the lowest top of the
side-impact structure AND <= 320 mm above the lowest point inside the cockpit. Steering wheel, column, seat and padding
removed; the firewall stays.
T.1.2: a vertical 350 x 350 template (50 mm corner chamfers) is carried from behind the steering column to 100 mm
behind the rearmost pedal face (pedals fully forward), moving vertically as needed. The seat stays; the steering
column may pass through the 50 mm centre band. The semicircular notches are ignored (conservative: bigger template).
Obstacles: frame tubes, the steering rack, front rockers/shocks/pushrods, the seat base. Run: python cockpit.py
"""
import numpy as np
import mule as m

T11 = np.array([(0, 200), (500, 275), (600, 175), (600, -175), (500, -275), (0, -200)], float)  # (x from front -> rear, z)
T12_W, T12_H, T12_C = 350.0, 350.0, 50.0
STEP = 5.0

def obstacles():
    """Segments (a, b, radius, name): frame tubes, rack, front rocker arms, shocks and pushrods."""
    out = [(np.array(a, float), np.array(b, float), m.SIZES[s][0] / 2, r) for a, b, s, r in m.MEMBERS]
    x, y, z = m.RACK
    out.append((np.array([x, y, -z]), np.array([x, y, z]), m.RACK_R, "steering rack"))
    import rocker
    r = rocker.analyse("front"); P, A, B, S = r["g"]["P"], r["A3"], r["B3"], r["g"]["S"]
    for f in (lambda p: np.asarray(p, float), lambda p: np.array(m.mir(tuple(p)), float)):
        out += [(f(P), f(A), 12.0, "front rocker"), (f(P), f(B), 12.0, "front rocker"), (f(B), f(S), 25.0, "front shock")]
        for n, p, q, _ in m.susp_links("front"):
            if n == "pushrod": out.append((f(p), f(q), m.PUSHROD_TUBE[0] / 2, "front pushrod"))
    return out

def _samples(obs, step=4.0):
    """Points along every obstacle with their radius (sampled capsules)."""
    pts, rad, names = [], [], []
    for a, b, r, n in obs:
        k = max(2, int(np.linalg.norm(b - a) / step) + 1)
        for t in np.linspace(0, 1, k): pts.append(a + t * (b - a)); rad.append(r); names.append(n)
    return np.array(pts), np.array(rad), names

def _in_poly(p, poly):
    x, y = p; inside = False
    for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): inside = not inside
    return inside

def _edge_dist(p, poly):
    d = 1e9
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        ab = b - a; t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1); d = min(d, np.linalg.norm(p - (a + t * ab)))
    return d

def _hits(poly, circles):
    """(worst clearance mm, index) of circles (centre 2D, radius) against a polygon; negative = overlap."""
    worst, wi = 1e9, -1
    for i, (c, r) in enumerate(circles):
        g = -_edge_dist(c, poly) - r if _in_poly(c, poly) else _edge_dist(c, poly) - r
        if g < worst: worst, wi = g, i
    return worst, wi

def opening():
    """T.1.1. Returns (min over heights of the best clearance at that height, height, blocking obstacle)."""
    P, R, names = _samples(obstacles())
    y_final = min(m.Y_SIS + 12.7 - 25, (m.Y_LOW - 12.7) + 320)
    x_lo, x_hi = m.X_MAIN + 15.9, m.X_FRONT - 15.9          # hoop faces bound the fore/aft travel
    worst = (1e9, None, "")
    for y in np.arange(m.H_FRONT, y_final - 1e-6, -STEP)[::-1]:
        sel = np.abs(P[:, 1] - y) < R
        circ = [((p[0], p[2]), np.sqrt(r * r - (p[1] - y) ** 2)) for p, r in zip(P[sel], R[sel])]
        idx = np.flatnonzero(sel); best = (-1e9, "")
        for xf in np.arange(x_lo + 600, x_hi + 1e-6, STEP):       # template front edge at xf, rear at xf - 600
            poly = np.c_[xf - T11[:, 0], T11[:, 1]]
            g, i = _hits(poly, circ) if circ else (1e9, -1)
            if g > best[0]: best = (g, names[idx[i]] if i >= 0 else "")
        if x_hi - x_lo < 600: best = (-1e9, "hoops closer than 600 mm")
        if best[0] < worst[0]: worst = (best[0], y, best[1])
    return worst

def t12_poly(y0):
    """T.1.2 template outline as (z, y) points, bottom edge at y0."""
    c, w, h = T12_C, T12_W / 2, T12_H
    return np.array([(-w + c, y0), (w - c, y0), (w, y0 + c), (w, y0 + h - c), (w - c, y0 + h), (-w + c, y0 + h),
                     (-w, y0 + h - c), (-w, y0 + c)])

def ceiling(x, floor):
    """Lowest underside of a tube spanning the template's full width at station x (the template can't be lifted over
    a tube that crosses the whole cockpit: it would leave the chassis). Floor-level tubes (< floor + 150) don't count."""
    c = 1e9
    for a, b, s, _ in m.MEMBERS:
        a, b = np.array(a, float), np.array(b, float)
        if min(a[2], b[2]) > -T12_W / 2 or max(a[2], b[2]) < T12_W / 2 or (a[0] - x) * (b[0] - x) > 0: continue
        if abs(b[0] - a[0]) < 1e-9: y, z = min(a[1], b[1]), 0.0
        else:
            t = (x - a[0]) / (b[0] - a[0]); y, z = a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])
        if y > floor + 150 and abs(z) <= T12_W / 2: c = min(c, y - m.SIZES[s][0] / 2)   # only where it is over the template
    return c

def cross_section():
    """T.1.2. Returns (min over stations of the best clearance, X station, blocking obstacle, best bottom height)."""
    P, R, names = _samples(obstacles())
    keep = np.array([n != "steering column" for n in names])
    x0, x1 = m.WHEEL_C[0], m.X_PEDAL - 100
    worst = (1e9, None, "", None)
    for x in np.arange(x0, x1 + 1e-6, STEP):
        sel = (np.abs(P[:, 0] - x) < R) & keep
        circ = [((p[2], p[1]), np.sqrt(r * r - (p[0] - x) ** 2)) for p, r in zip(P[sel], R[sel])]
        floor = m.SEAT_Y0 + 6 if x <= m.X_PEDAL - 450 else m.Y_LOW - 12.7   # seat base top, else pan top
        ceil = ceiling(x, floor)
        idx = np.flatnonzero(sel); best = (-1e9, "", None)
        for y0 in np.arange(floor, 700, STEP):
            poly = t12_poly(y0)
            g, i = _hits(poly, circ) if circ else (1e9, -1)
            g = min(g, y0 - floor, ceil - (y0 + T12_H))
            if g > best[0]: best = (g, names[idx[i]] if i >= 0 else "floor/seat", y0)
            if g >= 10: break                                          # lowest position with 10 mm is enough
        if best[0] < worst[0]: worst = (best[0], x, best[1], best[2])
    return worst

def checks():
    g1, y1, n1 = opening(); g2, x2, n2, y2 = cross_section()
    return [("T.1.1 cockpit opening template passes (>= 0 mm)", g1 >= 0, f"worst {g1:.0f} mm at y={y1:.0f} ({n1})"),
            ("T.1.2 cross-section template passes to 100 mm behind the pedals (>= 0 mm)", g2 >= 0,
             f"worst {g2:.0f} mm at x={x2:.0f} ({n2})")]

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:74s} {d}")
    assert all(p for _, p, _ in res), "cockpit template check failed"
