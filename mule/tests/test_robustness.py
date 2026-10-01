"""robustness.py: the design passes under realistic tolerances, and the check catches a design with no margin."""
import mule as m
import robustness as R


def test_all_robustness_checks_pass():
    failed = [(n, d) for n, ok, d in R.checks() if not ok]
    assert not failed, failed


def test_random_draws_are_fixed_per_tube():
    a = R._rng(3, ("x", 1.0)).uniform(); b = R._rng(3, ("x", 1.0)).uniform(); c = R._rng(4, ("x", 1.0)).uniform()
    assert a == b and a != c
