"""steering.py: bump steer, Ackermann, rack travel, full-lock clearance."""
import math
import numpy as np
import steering as st


def test_all_steering_checks_pass():
    failed = [(n, d) for n, ok, d in st.checks() if not ok]
    assert not failed, failed


def test_kingpin_rotation_is_rigid():
    lbj, ubj, so, _ = st.points()
    q = st.steer_rot(so, lbj, ubj, math.radians(20))
    assert math.isclose(np.linalg.norm(q - lbj), np.linalg.norm(so - lbj), rel_tol=1e-12)
    assert np.allclose(st.steer_rot(so, lbj, ubj, 0.0), so)
