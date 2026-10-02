"""harness.py: T.2 belt geometry, tab strength, crash load on the frame."""
import math
import harness as H


def test_all_harness_checks_pass():
    failed = [(n, d) for n, ok, d in H.checks() if not ok]
    assert not failed, failed


def test_tab_tearout_hand_calc():
    t = H.TAB
    assert math.isclose(H.tab_tearout(), 2 * t["t"] * (t["e"] - t["hole"] / 2) * 0.6 * t["Su"])


def test_lap_tab_placed_at_the_target_angle():
    assert math.isclose(H.lap_angle(), H.m.LAP_ANGLE, abs_tol=1e-6)
