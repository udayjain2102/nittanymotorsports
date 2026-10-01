"""sideview.py: caster/trail, anti geometry, pitch, RC migration, bump steer at lock, steering ratio."""
import math
import mule as m
import sideview as V


def test_all_sideview_checks_pass():
    failed = [(n, d) for n, ok, d in V.checks() if not ok]
    assert not failed, failed


def test_caster_trail_hand_calc():
    s = m.SUSP["front"]; h = s["ubj_y"] - s["lbj_y"]
    cas, trail = V.caster_trail()
    assert math.isclose(cas, math.degrees(math.atan2(s["caster_dx"], h)), rel_tol=1e-9)
    assert math.isclose(trail, s["lbj_y"] * s["caster_dx"] / h, rel_tol=1e-9)   # axis meets ground ahead of the patch


def test_parallel_horizontal_pivots_give_zero_anti():
    # both front wishbone pivot axes are level in side view (same pickup heights) -> no side-view IC, 0 % anti-dive
    ic, slope = V.sv_ic("front")
    assert ic is None and abs(slope) < 1e-9 and abs(V.anti("front")) < 1e-9


def test_ride_rate_is_series_springs():
    kw = V.springs.size("front")["wheel"]
    assert math.isclose(1 / V.ride_rate("front"), 1 / kw + 1 / V.springs.TIRE_K)


def test_steering_effort_hand_calc():
    Fy = V.L.MU * V.L.MASS * V.L.G * V.L.FRONT_SPLIT
    T = Fy * (V.caster_trail()[1] + V.PNEU_TRAIL) / 1000 / V.steering_ratio()[0]
    assert math.isclose(V.steering_effort()[0], T, rel_tol=1e-9)
    assert math.isclose(V.steering_effort()[1], T / (m.WHEEL_DIA / 2000), rel_tol=1e-9)
