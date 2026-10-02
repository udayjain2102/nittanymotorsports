"""roll.py and compliance.py: limiting cases and the checks."""
import math
import compliance as C
import roll as R
import suspension as S


def test_all_roll_and_compliance_checks_pass():
    failed = [(n, d) for n, ok, d in R.checks() + C.checks() if not ok]
    assert not failed, failed


def test_no_lateral_g_gives_static_values():
    for a in ("front", "rear"):
        o, i = R.camber_in_corner(a, 0.0)
        assert math.isclose(o, R.STATIC_CAMBER[a], abs_tol=1e-6) and math.isclose(i, R.STATIC_CAMBER[a], abs_tol=1e-6)
        (dz, h), _, _ = R.rc_in_roll(a, 0.0)
        assert abs(dz) < 1e-6 and math.isclose(h, S.analyse(S.geom(a))["rc"], abs_tol=1e-6)
        assert abs(R.jacking(a, 0.0)[0]) < 1e-6


def test_rigid_links_and_frame_give_zero_compliance(monkeypatch):
    monkeypatch.setattr(C, "E", 1e30)
    monkeypatch.setattr(C.fea.Frame, "solve", lambda self, loads, fixed: (C.np.zeros(6 * len(self.P)), None))
    r = C.corner("front")
    assert abs(r["toe"]) < 1e-9 and abs(r["camber"]) < 1e-9
