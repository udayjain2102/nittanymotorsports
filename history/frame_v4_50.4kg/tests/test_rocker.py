"""rocker.py: bellcrank geometry, shock stroke window, motion ratio, clearance, load split."""
import numpy as np
import mule as m
import rocker


def test_all_rocker_checks_pass():
    failed = [(n, d) for n, ok, d in rocker.checks() if not ok]
    assert not failed, failed


def test_shock_compresses_in_bump():
    for axle in ("front", "rear"):
        g = rocker.design(axle)
        assert rocker.shock_length(g, 20)[0] < rocker.shock_length(g, -20)[0]


def test_rocker_load_split_balances_force_and_moment():
    for axle in ("front", "rear"):
        r = rocker.analyse(axle); P, A, B = r["g"]["P"], r["A3"], r["B3"]
        F = np.array([100.0, -2000.0, 300.0])
        split, fs = rocker.reactions(axle, F)
        FB = -split[rocker.SHOCK_MOUNT[axle]]                     # shock force on the rocker
        Fp = -split[m.susp_links(axle)[-1][3]]                     # pivot reaction on the rocker (frame pushes back)
        assert np.allclose(F + FB + Fp, 0, atol=1e-6)
        n = np.cross(A - P, B - P); n /= np.linalg.norm(n)
        assert abs(np.dot(np.cross(A - P, F) + np.cross(B - P, FB), n)) < 1e-6
