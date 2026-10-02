"""Harness installation (FSAE 2026 T.2): belt geometry, tab design, and the frame under a crash harness load.

Geometry (side view, upright driving position): lap belts from tabs on the lower side-impact tubes (mule "lap"
nodes) to the pelvis at the hip point; shoulder belts from the shoulder bar to the shoulders; the 5-point anti-sub
belt from the buckle (ahead of the hip) straight down to the floor-cross tab ("as_c").
Tabs: 4130 plate, bolt tabs checked in double tearout (T.2.4.3); welded both sides of the base (T.2.4.4c).
Crash case: 20 g frontal on the driver, shared shoulder 45 % / lap 45 % / anti-sub 10 % (assumed split), balanced by
inertia relief so the harness mounts see their local loads (the impact-attenuator path is covered by F.8, not here).
FoS against welded ultimate (no rupture); welded yield is reported. Run: python harness.py
"""
import math
import numpy as np
import mule as m
import fea

TAB = dict(t=3.2, e=20.0, hole=10.5, Su=560.0, weld_leg=3.0, weld_len=40.0, weld_Su=480.0)   # 1/8in 4130, 3/8in bolt
BOLTS = {"lap": 10.0, "shoulder": 10.0, "anti-sub": 8.0}       # mm (T.2.5.8, T.2.6.4, T.2.7.5 minimums: 10 / 10 / 8)
BUCKLE = (m.HIP[0] + 120, m.HIP[1] + 60)                       # 5-point buckle / anti-sub belt top, side view
CRASH_G, DRIVER_KG = 20.0, 100.0   # 100 kg: ~95th-percentile US male, the template the cockpit is sized to (V.2.1.1); was 80 (audit)
UTS_WELD = 300.0                  # MPa, F.3.4.2 welded ultimate: a crash may yield the tubes but must not break them
SPLIT = {"shoulder": 0.45, "lap": 0.45, "anti-sub": 0.10}

def lap_angle():
    return math.degrees(math.atan2(m.HIP[1] - m.N["lap"][1], m.HIP[0] - m.N["lap"][0]))

def anti_sub_angle():
    """Anti-sub belt angle from vertical (deg, + = mount ahead of the buckle)."""
    return math.degrees(math.atan2(m.N["as_c"][0] - BUCKLE[0], BUCKLE[1] - m.N["as_c"][1]))

def shoulder_angle():
    return math.degrees(math.atan2(m.SHOULDER_BAR_Y - m.SHOULDER[1], m.SHOULDER[0] - m.X_MAIN))

def tab_tearout():
    """Double-tearout strength (N) of one tab: two shear planes from the hole edge to the tab end."""
    return 2 * TAB["t"] * (TAB["e"] - TAB["hole"] / 2) * 0.6 * TAB["Su"]

def tab_weld():
    """Fillet weld both sides of the tab base (N), throat 0.707 x leg, shear 0.6 x filler UTS."""
    return 2 * TAB["weld_len"] * 0.707 * TAB["weld_leg"] * 0.6 * TAB["weld_Su"]

def crash():
    """Frame FoS vs welded yield under the crash harness load; also returns where."""
    fr = fea.Frame(m.MEMBERS); F = DRIVER_KG * CRASH_G * 9.81
    loads = {}
    def pull(node, target, frac):
        p = np.array(node, float); u = np.array(target, float) - p; u /= np.linalg.norm(u)
        k = fr.find(p); loads[k] = loads.get(k, 0) + F * frac * u
    for s in (1, -1):
        sb = (m.X_MAIN, m.SHOULDER_BAR_Y, s * m.BELT_Z)
        pull(sb, (m.SHOULDER[0], m.SHOULDER[1], s * m.BELT_Z), SPLIT["shoulder"] / 2)
        lap = m.N["lap"] if s > 0 else m.mir(m.N["lap"])
        pull(lap, (m.HIP[0], m.HIP[1], s * 180.0), SPLIT["lap"] / 2)
    pull(m.N["as_c"], (BUCKLE[0], BUCKLE[1], 0.0), SPLIT["anti-sub"])
    _, st = fr.solve(*fea.inertia_relief(fr, loads, without_driver=True)); j = int(np.argmax(st))   # driver's inertia is the load
    return UTS_WELD / st[j], fr.el[j][3], fea.SY_WELD / st[j]

def checks():
    la, aa, sa = lap_angle(), anti_sub_angle(), shoulder_angle()
    tear, weld = tab_tearout(), tab_weld(); fos, where, fy = crash()
    return [
        ("T.2.5.4a lap belt side-view angle 45-65 deg", 45 <= la <= 65, f"{la:.1f} deg (tab at x={m.N['lap'][0]:.0f} on the lower SIS)"),
        ("T.2.7.1 anti-sub angle <= 20 deg, mount in line or forward", 0 <= aa <= 20, f"{aa:.1f} deg from vertical"),
        ("T.2.6.1 shoulder belt angle -20..+10 deg", -20 <= sa <= 10, f"{sa:.1f} deg"),
        ("T.2.4.3a tab double tearout >= 15 kN (one belt per tab)", tear >= 15e3, f"{tear / 1e3:.1f} kN"),
        ("T.2.4.3b tab thickness >= 1.6 mm", TAB["t"] >= 1.6, f"{TAB['t']} mm"),
        ("T.2.4.4 tab weld (both sides) >= 15 kN", weld >= 15e3, f"{weld / 1e3:.1f} kN"),
        ("T.2.5.8 / T.2.6.4 / T.2.7.5 bolt sizes", BOLTS["lap"] >= 10 and BOLTS["shoulder"] >= 10 and BOLTS["anti-sub"] >= 8,
         ", ".join(f"{k} M{v:.0f}" for k, v in BOLTS.items())),
        (f"frame FoS >= 1.0 vs welded UTS under a {CRASH_G:.0f} g harness load", fos >= 1.0,
         f"{fos:.2f} ({where}); vs welded yield {fy:.2f} (local yielding in a crash is accepted)"),
    ]

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:60s} {d}")
    assert all(p for _, p, _ in res), "harness check failed"
