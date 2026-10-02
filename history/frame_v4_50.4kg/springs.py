"""Spring/damper sizing for pushrod + rocker: pushrod motion ratio from the suspension kinematics, x rocker
ratio (shock travel / pushrod travel) -> spring rate for a target ride frequency and shock stroke. Run: python springs.py"""
import math
import mule as m
import suspension as S
import loads as L

RIDE_HZ = {"front": 3.0, "rear": 2.6}   # front stiffer: puts ~50 % of the lateral load transfer on the front (roll.lltd), mild understeer with no anti-roll bar
UNSPRUNG = 15.0                          # kg per corner (wheel, tyre, upright, brake, half arms); mass.py budget 15.3
TIRE_K = 120.0                           # N/mm, 20.5x7-13 at ~12 psi (assumption)
TRAVEL, DROOP = 50.0, 25.0               # bump / droop, mm. V.3.1.1 asks for 50 mm usable in total; 75 here
MR = {"front": 0.72, "rear": 0.75}       # shock mm per wheel mm (review target 0.7-1.0); 75 mm x 0.75 = 56 mm fits the 65 mm stroke

def motion(axle, t):
    """Pushrod length (mm) with the wheel at travel t (mm, + = bump)."""
    g = S.geom(axle); _, links = L.corner(axle); _, p, q, _ = links[-1]   # pushrod: upright pt p, rocker pivot q
    lo, hi = -0.8, 0.8
    for _ in range(60):   # bisection on lower-arm angle for this wheel travel
        mid = (lo + hi) / 2; f, _ = S.upright(g, mid)
        (lo, hi) = (mid, hi) if f(g["C"])[1] - t < 0 else (lo, mid)
    f, _ = S.upright(g, (lo + hi) / 2); z, y = f((p[2], p[1]))
    return math.dist((p[0], y, z), q)

def pushrod_ratio(axle): return (motion(axle, -1) - motion(axle, 1)) / 2   # pushrod mm per wheel mm

ROCKER = {a: MR[a] / pushrod_ratio(a) for a in MR}   # rocker ratio (shock / pushrod travel) that gives MR

def size(axle):
    share = L.FRONT_SPLIT if axle == "front" else 1 - L.FRONT_SPLIT
    sprung = L.MASS * share / 2 - UNSPRUNG
    pr = pushrod_ratio(axle); mr = pr * ROCKER[axle]
    ride = sprung * (2 * math.pi * RIDE_HZ[axle]) ** 2 / 1000   # N/mm at the wheel incl. tyre
    wheel = ride * TIRE_K / (TIRE_K - ride)                    # remove tyre in series
    spring = wheel / mr ** 2
    stroke = (motion(axle, -DROOP) - motion(axle, TRAVEL)) * ROCKER[axle]
    crit = 2 * math.sqrt(spring * 1000 * sprung / mr**2) / 1000  # N*s/mm critical damping at the shock (approx)
    return dict(pr=pr, mr=mr, sprung=sprung, wheel=wheel, spring=spring, lbs_in=spring * 5.71, stroke=stroke,
                static=motion(axle, 0), damp=0.3 * crit)

if __name__ == "__main__":
    for axle in ("front", "rear"):
        r = size(axle)
        assert 170 <= r["lbs_in"] <= 700 and r["stroke"] <= 60, "spring/stroke outside common MTB shock range"
        assert 0.3 < r["mr"] < 1.2, "shock motion ratio out of sane range"
        print(f"{axle}: pushrod ratio {r['pr']:.2f} x rocker {ROCKER[axle]:.2f} = motion ratio {r['mr']:.2f}, sprung {r['sprung']:.0f} kg/corner, wheel rate {r['wheel']:.1f} N/mm, "
              f"spring {r['spring']:.0f} N/mm ({r['lbs_in']:.0f} lb/in), shock stroke for +{TRAVEL:.0f}/-{DROOP:.0f} mm: {r['stroke']:.0f} mm, "
              f"pushrod length {r['static']:.0f} mm, ~30% critical damping {r['damp']:.2f} N*s/mm")
