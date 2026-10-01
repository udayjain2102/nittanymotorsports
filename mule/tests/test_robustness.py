"""robustness.py: the design passes under realistic tolerances, and the check catches a design with no margin."""
import mule as m
import robustness as R


def test_all_robustness_checks_pass():
    failed = [(n, d) for n, ok, d in R.checks() if not ok]
    assert not failed, failed


def test_tolerances_catch_the_old_125_shoulder_bar():
    # the 2026-10-01 optimiser's 1.25" bar passed the nominal 20 g case (FoS 1.08) but not with real tube tolerances
    saved = list(m.MEMBERS)
    try:
        m.MEMBERS[:] = [(a, b, "H" if r == "Shoulder harness bar" else s, r) for a, b, s, r in saved]
        worst = min(d["20 g harness (vs welded UTS)"] for d, _ in R.frame_samples())
        assert worst < 1.0
    finally:
        m.MEMBERS[:] = saved


def test_random_draws_are_fixed_per_tube():
    a = R._rng(3, ("x", 1.0)).uniform(); b = R._rng(3, ("x", 1.0)).uniform(); c = R._rng(4, ("x", 1.0)).uniform()
    assert a == b and a != c
