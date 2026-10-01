"""lapsim.py: hand calculations for the limiting cases."""
import math
import lapsim as S
import loads as L
import mule as m


def test_all_lapsim_checks_pass():
    failed = [(n, d) for n, ok, d in S.checks() if not ok]
    assert not failed, failed


def test_skidpad_is_steady_state_circle():
    t, v = S.skidpad(1.0, aero_on=False)
    assert math.isclose(t, 2 * math.pi * math.sqrt(S.SKID_R / L.G), rel_tol=1e-9)


def test_traction_limited_accel_matches_constant_acceleration(monkeypatch):
    monkeypatch.setattr(S, "torque", lambda rpm: 1e6)       # engine never limits
    monkeypatch.setattr(S, "CRR", 0.0); monkeypatch.setattr(S, "SHIFT_S", 0.0)
    a = S.GRIP * L.G * (1 - L.FRONT_SPLIT) / (1 - S.GRIP * L.CG_H / m.WHEELBASE)   # rear-drive traction limit
    t, _ = S.accel(cda=0.0)
    assert math.isclose(t, math.sqrt(2 * 75 / a), rel_tol=0.02)


def test_autocross_on_one_long_circle_is_steady_cornering(monkeypatch):
    R, L_ = 20.0, 2000.0
    monkeypatch.setattr(S, "course", lambda: [(L_, R)])
    t, _ = S.autocross()
    assert math.isclose(t, L_ / math.sqrt(S.GRIP * L.G * R), rel_tol=0.02)   # start from rest costs < 2 %
