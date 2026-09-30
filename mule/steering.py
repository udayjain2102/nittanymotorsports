"""Front steering: bump steer, Ackermann, lock angle / rack travel, tyre clearance at full lock.

Kingpin = line through the ball joints. The upright moves in bump per suspension.py (front view);
toe change = steer angle about the kingpin that keeps the tie rod at constant length.
Run: python steering.py
"""
import math
import numpy as np
import mule as m
import suspension as S

LOCK_DEG = 23.0      # inner-wheel lock (steering stop): 25 deg leaves only 6.5 mm tyre-to-lower-arm gap
RACK_TRAVEL_MAX = 35.0   # mm each side; common FSAE quick racks

def points(axle="front"):
    (_, lbj, _, _), _, (_, ubj, _, _), _, (_, so, si, _), _ = m.susp_links(axle)   # kingpin includes caster
    return np.array(lbj, float), np.array(ubj, float), np.array(so, float), np.array(si, float)

def steer_rot(p, lbj, ubj, d):
    """Rotate point p about the kingpin axis by d rad (Rodrigues)."""
    k = (ubj - lbj) / np.linalg.norm(ubj - lbj); v = p - lbj
    return lbj + v * math.cos(d) + np.cross(k, v) * math.sin(d) + k * np.dot(k, v) * (1 - math.cos(d))

def bump_steer(travels=(-50, -25, 25, 50), axle="front"):
    """Toe change (deg, + = toe-out) of the right wheel vs wheel travel (mm). Rear: the toe link plays the tie rod."""
    g = S.geom(axle); lbj0, ubj0, so, si = points(axle); L0 = np.linalg.norm(so - si)
    out = {}
    for t in travels:
        lo, hi = -0.8, 0.8
        for _ in range(60):
            mid = (lo + hi) / 2; f, _ = S.upright(g, mid)
            (lo, hi) = (mid, hi) if f(g["C"])[1] - t < 0 else (lo, mid)
        f, _ = S.upright(g, (lo + hi) / 2)
        mv = lambda p: np.array([p[0], *reversed(f((p[2], p[1])))])   # (x, y, z) with (z, y) moved
        lbj, ubj, sp = mv(lbj0), mv(ubj0), mv(so)
        d = 0.0
        for _ in range(20):   # Newton: steer angle that restores tie-rod length
            r = np.linalg.norm(steer_rot(sp, lbj, ubj, d) - si) - L0
            dr = (np.linalg.norm(steer_rot(sp, lbj, ubj, d + 1e-5) - si) - L0 - r) / 1e-5
            d -= r / dr
        out[t] = math.degrees(d)   # + about the kingpin (points up) swings the arm (behind axle) outboard = toe-out
    return out

def ackermann():
    """Inner/outer wheel angles at LOCK_DEG inner and % Ackermann, from the arm geometry (plan view)."""
    lbj, ubj, so, si = points(); L0 = np.linalg.norm(so - si)
    def wheel_angle(rack_dz):   # right wheel; rack moves by rack_dz along +z
        sin_ = si + np.array([0, 0, rack_dz]); d = 0.0
        for _ in range(30):
            r = np.linalg.norm(steer_rot(so, lbj, ubj, d) - sin_) - L0
            dr = (np.linalg.norm(steer_rot(so, lbj, ubj, d + 1e-5) - sin_) - L0 - r) / 1e-5
            d -= r / dr
        return math.degrees(d)
    # right wheel: + angle about the up-pointing kingpin steers it left (it is then the OUTER wheel);
    # find the rack travel that puts the right wheel at LOCK_DEG steering right (INNER wheel)
    lo, hi = 0.0, 80.0
    sgn = 1 if wheel_angle(1.0) < 0 else -1          # rack direction that steers the right wheel right
    for _ in range(60):
        mid = (lo + hi) / 2; (lo, hi) = (mid, hi) if -wheel_angle(sgn * mid) < LOCK_DEG else (lo, mid)
    travel = (lo + hi) / 2
    inner, outer = -wheel_angle(sgn * travel), wheel_angle(-sgn * travel)
    ideal_outer = math.degrees(math.atan(1 / (1 / math.tan(math.radians(inner)) + m.TRACK_F / m.WHEELBASE)))
    pct = 100 * (inner - outer) / (inner - ideal_outer)
    return travel, inner, outer, pct

def seg_dist(p, a, b):
    ab = b - a; t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1); return np.linalg.norm(p - (a + t * ab))

RIM_R = 165.0   # 13" rim lip radius; inside it the arms are in the wheel barrel by design

def lock_clearance():
    """Min 3D gap (mm) from the inner face of the tyre/rim (radius RIM_R..tyre OD) at +/-LOCK_DEG to every
    A-arm leg, tie rod, pushrod and nearby frame tube (tube radii subtracted)."""
    lbj, ubj, _, _ = points(); wz = m.TRACK_F / 2; r = m.TIRE_OD / 2; zi = wz - m.TIRE_W / 2
    ring = [np.array([m.WHEELBASE + rr * math.cos(a), r + rr * math.sin(a), zi])
            for rr in (RIM_R, (RIM_R + r) / 2, r) for a in np.linspace(0, 2 * math.pi, 72, endpoint=False)]
    segs = [(n, np.array(p, float), np.array(q, float), (m.PUSHROD_TUBE if n == "pushrod" else m.SUSP_TUBE)[0] / 2)
            for n, p, q, _ in m.susp_links("front")]
    segs += [(role, np.array(a, float), np.array(b, float), m.SIZES[sz][0] / 2) for a, b, sz, role in m.MEMBERS
             if min(a[0], b[0]) < m.WHEELBASE + r + 50 and max(a[0], b[0]) > m.WHEELBASE - r - 50]
    worst = (1e9, "")
    for sgn in (1, -1):
        for p in ring:
            q = steer_rot(p, lbj, ubj, sgn * math.radians(LOCK_DEG))
            for n, a, b, rad in segs:
                d = seg_dist(q, a, b) - rad
                if d < worst[0]: worst = (d, n)
    return worst

def checks():
    bs = bump_steer(); bsr = bump_steer(axle="rear"); travel, inner, outer, pct = ackermann(); gap, what = lock_clearance()
    return [
        ("bump steer |toe| <= 0.25 deg over +/-50 mm", max(abs(v) for v in bs.values()) <= 0.25,
         ", ".join(f"{t:+d}: {v:+.2f}" for t, v in bs.items()) + " deg"),
        ("rear bump steer |toe| <= 0.25 deg over +/-50 mm (toe link)", max(abs(v) for v in bsr.values()) <= 0.25,
         ", ".join(f"{t:+d}: {v:+.2f}" for t, v in bsr.items()) + " deg"),
        (f"rack travel for {LOCK_DEG:.0f} deg inner lock <= {RACK_TRAVEL_MAX:.0f} mm", travel <= RACK_TRAVEL_MAX, f"{travel:.1f} mm each side"),
        ("Ackermann 0-120 %", 0 <= pct <= 120, f"inner {inner:.1f} / outer {outer:.1f} deg = {pct:.0f} %"),
        ("tyre/rim clears arms, rods, frame at full lock (3D)", gap >= 10, f"min gap {gap:.0f} mm ({what})"),
    ]

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:52s} {d}")
    assert all(p for _, p, _ in res), "steering check failed"
