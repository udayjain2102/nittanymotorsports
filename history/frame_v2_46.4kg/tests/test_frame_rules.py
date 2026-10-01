"""frame_rules.py: every check passes on the design, and each key check fails when its rule is broken."""
import numpy as np
import pytest
import mule as m
import frame_rules as F


@pytest.fixture
def members():
    saved = list(m.MEMBERS)
    yield m.MEMBERS
    m.MEMBERS[:] = saved


def failing(prefix):
    return [n for n, ok, _ in F.checks() if not ok and n.startswith(prefix)]


def test_all_frame_rule_checks_pass():
    failed = [(n, d) for n, ok, d in F.checks() if not ok]
    assert not failed, failed


def test_missing_side_impact_diagonal_breaks_triangulation(members):
    members[:] = [mb for mb in members if mb[3] != "Diagonal side impact"]
    assert failing("F.1.17")


def test_undersized_main_hoop_fails_tube_size(members):
    members[:] = [(a, b, "B" if r == "Main hoop" else s, r) for a, b, s, r in members]
    assert failing("F.3.2.1")


def test_bent_main_hoop_brace_fails(members):
    out = []
    for a, b, s, r in members:
        if r == "Main hoop brace":
            mid = tuple((np.array(a) + np.array(b)) / 2 + np.array([0, 60, 0]))   # kink the brace 60 mm
            out += [(a, mid, s, r), (mid, b, s, r)]
        else:
            out.append((a, b, s, r))
    members[:] = out
    assert failing("F.5.9 two")


def test_mount_on_main_hoop_brace_span_fails(monkeypatch):
    a, b = next((np.array(a), np.array(b)) for a, b, s, r in m.MEMBERS if r == "Main hoop brace")
    pts = F.mount_points(); pts["test mount mid-brace"] = (a + b) / 2
    monkeypatch.setattr(F, "mount_points", lambda: pts)
    assert failing("F.5.11.4")


def test_tube_in_front_tyre_zone_fails(members):
    x = m.WHEELBASE; z = m.TRACK_F / 2
    members.append(((x, 300.0, 100.0), (x, 300.0, z), "C", "test tube into the tyre"))
    assert failing("V.1.1")
