"""cockpit.py: T.1.1 / T.1.2 templates pass; the geometric helpers behave."""
import numpy as np
import cockpit as C


def test_templates_pass():
    failed = [(n, d) for n, ok, d in C.checks() if not ok]
    assert not failed, failed


def test_polygon_clearance_sign():
    sq = np.array([(0, 0), (10, 0), (10, 10), (0, 10)], float)
    assert C._hits(sq, [((5, 5), 1)])[0] < 0            # circle inside -> overlap
    assert abs(C._hits(sq, [((15, 5), 2)])[0] - 3) < 1e-9   # 5 mm from the edge, radius 2 -> 3 mm gap


def test_t12_template_size():
    p = C.t12_poly(0.0)
    assert np.isclose(p[:, 0].max() - p[:, 0].min(), 350) and np.isclose(p[:, 1].max(), 350)
