"""brakes.py: sizing, bias, pedal travel/BOTS, strength, frame at 2000 N."""
import math
import brakes as B
import loads as L
import mule as m


def test_all_brake_checks_pass():
    failed = [(n, d) for n, ok, d in B.checks() if not ok]
    assert not failed, failed


def test_axle_loads_sum_to_weight_and_transfer_forward():
    f, r = B.axle_loads(1.5)
    assert math.isclose(f + r, L.MASS * L.G)
    assert math.isclose(f - L.MASS * L.G * L.FRONT_SPLIT, L.MASS * L.G * 1.5 * L.CG_H / m.WHEELBASE)


def test_front_lock_pressure_hand_calc():
    mu = 1.0; Fz = B.axle_loads(mu)[0] / 2
    T = mu * Fz * m.TIRE_OD / 2                                  # N*mm per front wheel
    p = T / (2 * B.PAD_MU * math.pi / 4 * B.CALIPER["front"]["piston"] ** 2 * B.R_EFF)   # MPa
    assert math.isclose(B.lock_pressure(mu)["front"], 10 * p)


def test_lock_point_locks_both_axles_at_once():
    s, F = B.lock_point(1.5)
    assert math.isclose(B.lock_force(1.5, s), F, rel_tol=1e-9)
    assert B.lock_force(1.5, s + 0.05) > F and B.lock_force(1.5, s - 0.05) > F   # any other split needs more force


def test_pedal_travel_lever_rule():
    assert math.isclose(B.pedal_travel(1.0, 4.0, 99.0), B.RATIO * 4.0)
    assert math.isclose(B.pedal_travel(0.5, 4.0, 2.0), B.RATIO * 3.0)


def test_pressure_at_split_matches_bar_force():
    p = B.pressures(1000.0, 0.6)
    assert math.isclose(p["front"] / 10 * math.pi / 4 * B.MC_BORE["front"] ** 2, 1000 * B.RATIO * 0.6)
