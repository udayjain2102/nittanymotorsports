"""mass.py: budget sums, CG maths, and that load-case assumptions cover it."""
import math
import mass as M


def test_all_mass_checks_pass():
    failed = [(n, d) for n, ok, d in M.checks() if not ok]
    assert not failed, failed


def test_summary_is_mass_weighted():
    it = M.items(); s = M.summary(); kg = sum(i[1] for i in it)
    assert math.isclose(s["kg"], kg)
    assert math.isclose(s["cg_h"], sum(i[1] * i[2][1] for i in it) / kg)


def test_frame_mass_matches_member_sum():
    kg, _ = M.frame()
    total = sum(M.m.tube_props(s)[1] * math.dist(a, b) * M.m.STEEL_DENSITY for a, b, s, _ in M.m.MEMBERS)
    assert math.isclose(kg, total)
