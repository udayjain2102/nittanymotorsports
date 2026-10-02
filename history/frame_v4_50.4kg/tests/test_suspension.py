"""suspension.py: 4-bar kinematics and hardpoint targets."""
import math
import suspension as S


def test_parallel_equal_arms_have_no_camber_gain():
    S.selfcheck()


def test_all_suspension_checks_pass():
    failed = [(n, d) for n, ok, d in S.checks() if not ok]
    assert not failed, failed


def test_upright_moves_rigidly():
    g = S.geom("front")
    f, _ = S.upright(g, 0.1)
    for a, b in (("Bl", "Bu"), ("Bl", "C"), ("Bu", "C")):
        assert math.isclose(math.dist(f(g[a]), f(g[b])), math.dist(g[a], g[b]), rel_tol=1e-9)
