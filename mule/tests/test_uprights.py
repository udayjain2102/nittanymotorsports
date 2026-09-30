"""uprights.py: bearing statics, life, hub shaft, arms, studs, packaging."""
import math
import numpy as np
import uprights as U


def test_all_upright_checks_pass():
    failed = [(n, d) for n, ok, d in U.checks() if not ok]
    assert not failed, failed


def test_bearing_split_overhung_lever_rule():
    g = U.geom("front"); F = np.array([0.0, 1000.0, 0.0])
    ro, ri, a = U.bearing_loads(g, F)
    zc = g["W"][2]   # load line at the wheel centre plane
    assert zc > g["zo"]                                    # overhung: wheel centre outboard of both bearings
    assert math.isclose(ro - ri, 1000.0, rel_tol=1e-9)   # so the inboard bearing load reverses
    assert math.isclose(ro * (g["zo"] - g["zi"]), 1000.0 * (zc - g["zi"]), rel_tol=1e-9)
    assert a < 1e-9


def test_lateral_load_goes_axial_and_adds_moment():
    g = U.geom("rear")
    _, _, a = U.bearing_loads(g, np.array([0.0, 0.0, -1500.0]))
    assert math.isclose(a, 1500.0, rel_tol=1e-9)


def test_stud_slip_torque_formula():
    s = U.STUDS
    expect = s["n"] * s["preload"] * s["Sp"] * s["As"] * s["mu"] * s["pcd"] / 2 / 1000
    assert math.isclose(U.stud_slip_torque(), expect)
