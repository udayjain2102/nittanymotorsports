"""Side-view suspension and steering details: caster, mechanical trail, anti-dive / anti-squat, pitch under braking
and acceleration, roll-centre migration in heave, bump steer at full lock, steering ratio and turning circle.

Anti-dive (outboard front brakes) and anti-squat (inboard drive: chassis-mounted spool, so the reaction acts at the
wheel centre) come from the side-view swing arm: the side-view instant centre is where lines through each ball joint,
parallel to that wishbone's inner pivot axis, meet. Pitch uses the ride rate (wheel rate in series with the tyre).
Run: python sideview.py
"""
import math
import numpy as np
import mule as m
import loads as L
import springs
import suspension as S
import steering as st

CASTER_RANGE, TRAIL_RANGE = (3.0, 7.0), (5.0, 30.0)   # deg, mm (standard FSAE practice)
RACK_C = 4.71 * 25.4     # rack travel per pinion revolution, mm: Kaz Technologies FSAE rack, 4.71 in/rev, 82.5 mm total travel (kaztechnologies.com)
LOCK_TO_LOCK_MAX = 180.0 # deg, so the driver never moves hands on the wheel (review notes)
BRAKE_G, ACCEL_G = L.MU, 1.0

def kingpin(axle="front"):
    lbj, ubj = (np.array(p, float) for p in (m.susp_links(axle)[0][1], m.susp_links(axle)[2][1]))
    return lbj, ubj

def caster_trail(axle="front"):
    """Caster (deg, + = top rearward) and mechanical trail at the ground (mm, + = axis meets ground ahead of the patch)."""
    lbj, ubj = kingpin(axle); x0 = m.WHEELBASE if axle == "front" else 0.0
    caster = math.degrees(math.atan2(lbj[0] - ubj[0], ubj[1] - lbj[1]))
    xg = lbj[0] + (lbj[0] - ubj[0]) / (ubj[1] - lbj[1]) * lbj[1]
    return caster, xg - x0

def sv_ic(axle):
    """Side-view instant centre (x, y) or None if the pivot axes are parallel in side view."""
    s = m.SUSP[axle]; links = m.susp_links(axle)
    lines = []
    for (i0, i1), bj in ((s["inner_low"], links[0][1]), (s["inner_up"], links[2][1])):
        a, b = np.array(m.N[i0], float), np.array(m.N[i1], float); d = b - a
        lines.append((np.array([bj[0], bj[1]]), np.array([d[0], d[1]])))
    (p, u), (q, v) = lines
    det = u[0] * -v[1] - u[1] * -v[0]
    if abs(det) < 1e-9: return None, u[1] / u[0]
    t = ((q - p)[0] * -v[1] - (q - p)[1] * -v[0]) / det
    return p + t * u, None

def anti(axle):
    """Anti-dive (front, braking) or anti-squat (rear, inboard drive) in % of the pitch load transfer."""
    ic, slope = sv_ic(axle); x0 = m.WHEELBASE if axle == "front" else 0.0
    ref = np.array([x0, 0.0 if axle == "front" else m.TIRE_OD / 2])        # contact patch / wheel centre
    tan = abs(slope) if ic is None else abs((ic[1] - ref[1]) / (ic[0] - ref[0]))
    if axle == "front":
        bf = L.FRONT_SPLIT + BRAKE_G * L.CG_H / m.WHEELBASE              # brake bias = front load share at the limit
        return 100 * tan * bf * m.WHEELBASE / L.CG_H
    return 100 * tan * m.WHEELBASE / L.CG_H

def ride_rate(axle):
    kw = springs.size(axle)["wheel"]; return kw * springs.TIRE_K / (kw + springs.TIRE_K)

def pitch():
    """Front dive under BRAKE_G and rear squat under ACCEL_G (mm at the wheel), and pitch angle (deg)."""
    w = L.MASS * L.G
    dF_b = w * BRAKE_G * L.CG_H / m.WHEELBASE / 2 * (1 - anti("front") / 100)
    dF_a = w * ACCEL_G * L.CG_H / m.WHEELBASE / 2 * (1 - anti("rear") / 100)
    dive, squat = dF_b / ride_rate("front"), dF_a / ride_rate("rear")
    ang = math.degrees(math.atan((dive + w * BRAKE_G * L.CG_H / m.WHEELBASE / 2 / ride_rate("rear")) / m.WHEELBASE))
    return dive, squat, ang

def rc_migration(axle, t=25.0):
    """Roll-centre height change (mm) from static to +/-t mm heave (relative to the ground)."""
    g = S.geom(axle); rc0 = S.analyse(g)["rc"]; out = []
    for tt in (-t, t):
        lo, hi = -0.8, 0.8
        for _ in range(60):
            mid = (lo + hi) / 2; f, _ = S.upright(g, mid)
            (lo, hi) = (mid, hi) if f(g["C"])[1] - g["C"][1] - tt < 0 else (lo, mid)
        f, _ = S.upright(g, (lo + hi) / 2)
        Bl, Bu, C = f(g["Bl"]), f(g["Bu"]), f(g["C"])
        ic = S.line_x(g["Al"], Bl, g["Au"], Bu)
        rc = S.line_x(C, ic, (0, 0), (0, 1))[1] if ic else C[1]
        out.append(rc - C[1] - rc0)
    return out

def bump_steer_at_lock(t=25.0):
    """Toe change (deg) over +/-t mm with the rack at full-lock travel, both directions."""
    travel = st.ackermann()[0]; worst = 0.0
    g = S.geom("front"); lbj0, ubj0, so, si0 = st.points(); L0 = np.linalg.norm(so - si0)
    for rack in (travel, -travel):
        si = si0 + np.array([0, 0, rack]); base = None
        for tt in (0.0, -t, t):
            lo, hi = -0.8, 0.8
            for _ in range(60):
                mid = (lo + hi) / 2; f, _ = S.upright(g, mid)
                (lo, hi) = (mid, hi) if f(g["C"])[1] - g["C"][1] - tt < 0 else (lo, mid)
            f, _ = S.upright(g, (lo + hi) / 2)
            mv = lambda p: np.array([p[0], *reversed(f((p[2], p[1])))])
            lbj, ubj, sp = mv(lbj0), mv(ubj0), mv(so); d = 0.0
            for _ in range(30):
                r = np.linalg.norm(st.steer_rot(sp, lbj, ubj, d) - si) - L0
                dr = (np.linalg.norm(st.steer_rot(sp, lbj, ubj, d + 1e-5) - si) - L0 - r) / 1e-5
                d -= r / dr
            if base is None: base = d
            else: worst = max(worst, abs(math.degrees(d - base)))
    return worst

def steering_ratio():
    """Overall ratio (steering-wheel deg per mean road-wheel deg) and steering-wheel angle to full lock (deg)."""
    travel, inner, outer, _ = st.ackermann()
    sw = travel / RACK_C * 360
    return sw / ((inner + outer) / 2), sw

PNEU_TRAIL = 15.0        # mm, tyre pneumatic trail in a hard corner (ASSUMPTION; it shrinks toward the grip limit)
RIM_FORCE_MAX = 120.0    # N, total on the steering-wheel rim at the design lateral g (ours: unassisted, both hands)

def steering_effort(g_lat=L.MU):
    """Steering-wheel torque (N*m) and rim force (N, both hands) to hold a steady g_lat corner: the front tyres' side
    force acts at the mechanical plus pneumatic trail behind the kingpins, divided by the overall steering ratio.
    Friction in the rack and U-joints is ignored (it hides some of this torque from the driver)."""
    Fy = g_lat * L.MASS * L.G * L.FRONT_SPLIT                       # both front tyres, N
    T_kp = Fy * (caster_trail()[1] + PNEU_TRAIL) / 1000              # N*m about the two kingpins
    T_sw = T_kp / steering_ratio()[0]
    return T_sw, T_sw / (m.WHEEL_DIA / 2000)

def kickback(dFx=1000.0):
    """Steering-wheel torque (N*m) from a dFx (N) fore-aft force on one front tyre (a kerb, a bump, one wheel braking
    harder) acting on the scrub radius."""
    return dFx * S.analyse(S.geom("front"))["scrub"] / 1000 / steering_ratio()[0]

def turning_circle():
    """Kerb-to-kerb radius (m) of the outer front tyre's outside edge at full lock (kinematic, no slip)."""
    _, inner, _, _ = st.ackermann()
    rc = m.WHEELBASE / math.tan(math.radians(inner)) + m.TRACK_F / 2          # rear-axle centre radius
    return math.hypot(m.WHEELBASE, rc + m.TRACK_F / 2 + m.TIRE_W / 2) / 1000

def checks():
    cas, trail = caster_trail(); ad, asq = anti("front"), anti("rear"); dive, squat, ang = pitch()
    rcf, rcr = rc_migration("front"), rc_migration("rear"); bsl = bump_steer_at_lock()
    ratio, sw = steering_ratio()
    return [
        (f"front caster {CASTER_RANGE[0]:.0f}-{CASTER_RANGE[1]:.0f} deg", CASTER_RANGE[0] <= cas <= CASTER_RANGE[1], f"{cas:.1f} deg"),
        (f"front mechanical trail {TRAIL_RANGE[0]:.0f}-{TRAIL_RANGE[1]:.0f} mm", TRAIL_RANGE[0] <= trail <= TRAIL_RANGE[1], f"{trail:.1f} mm"),
        ("anti-dive / anti-squat 0-40 %", 0 <= ad <= 40 and 0 <= asq <= 40, f"anti-dive {ad:.0f} %, anti-squat {asq:.0f} %"),
        ("dive at 1.5 g braking <= 60 % of bump travel", dive <= 0.6 * springs.TRAVEL, f"{dive:.0f} mm front, pitch {ang:.2f} deg"),
        ("squat at 1 g acceleration <= 60 % of bump travel", squat <= 0.6 * springs.TRAVEL, f"{squat:.0f} mm rear"),
        ("roll-centre migration <= 2 mm per mm of heave (+/-25 mm)", max(map(abs, rcf + rcr)) <= 2 * 25,
         f"front {rcf[0]:+.0f}/{rcf[1]:+.0f}, rear {rcr[0]:+.0f}/{rcr[1]:+.0f} mm; front RC at full dive "
         f"{S.analyse(S.geom('front'))['rc'] + rcf[1] * dive / 25:.0f} mm"),
        ("bump steer at full lock <= 0.5 deg over +/-25 mm", bsl <= 0.5, f"{bsl:.2f} deg"),
        ("overall steering ratio 4-7 : 1", 4 <= ratio <= 7, f"{ratio:.1f}:1, {sw:.0f} deg to full lock"),
        (f"lock-to-lock <= {LOCK_TO_LOCK_MAX:.0f} deg (no hand-over-hand)", 2 * sw <= LOCK_TO_LOCK_MAX, f"{2 * sw:.0f} deg"),
        (f"steering rim force at {L.MU} g <= {RIM_FORCE_MAX:.0f} N (ours)", steering_effort()[1] <= RIM_FORCE_MAX,
         f"{steering_effort()[1]:.0f} N ({steering_effort()[0]:.1f} N*m); kickback {kickback():.1f} N*m per 1 kN on one front tyre"),
    ]

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:52s} {d}")
    print(f"turning circle (outer tyre edge, kinematic): radius {turning_circle():.2f} m - FSAE hairpins need <= 4.5 m (D.8), not a mule requirement")
    assert all(p for _, p, _ in res), "side-view check failed"
