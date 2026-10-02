"""mule.py: geometry vs FSAE 2026 rules, tube sizes, model integrity."""
import mule as m


def test_all_rule_checks_pass():
    failed = [(n, d) for n, ok, d in m.checks() if not ok]
    assert not failed, failed


def test_tube_sizes_meet_F_3_4_1():
    for s, (I_min, A_min) in m.RULE_MIN.items():
        I, A = m.tube_props(s)
        assert I >= I_min and A >= A_min and m.SIZES[s][0] >= 25.0, s


def test_frame_is_symmetric():
    keys = {tuple(round(c, 1) for c in p) for a, b, _, _ in m.MEMBERS for p in (a, b)}
    for k in keys:
        assert (k[0], k[1], round(-k[2], 1)) in keys or abs(k[2]) < 0.1, k


def test_no_zero_length_or_duplicate_members():
    seen = set()
    for a, b, _, _ in m.MEMBERS:
        assert m.norm(m.sub(b, a)) > 1.0
        k = tuple(sorted((tuple(round(c, 1) for c in a), tuple(round(c, 1) for c in b))))
        assert k not in seen, k
        seen.add(k)


def test_belly_pan_sits_under_lowest_tubes():
    bb = m.belly_pan().BoundingBox()
    assert abs(bb.ymax - (m.Y_LOW - m.rad("Lower side impact"))) < 0.01 and bb.zlen >= 2 * m.Z_REAR and bb.xlen >= m.X_BH - m.X_REAR - 1
    assert bb.ymin > 50, "pan must not drag: V.1.4.1"
    assert m.belly_pan().isValid()


def test_suspension_links_are_symmetric_pairs():
    for axle in ("front", "rear"):
        links = m.susp_links(axle)
        assert len(links) == 6 and all(p[2] > 0 for _, p, _, _ in links)


def test_readme_colour_key_matches_the_model():
    import pathlib, mule
    readme = (pathlib.Path(__file__).resolve().parents[1] / "README.md").read_text()
    assert mule.colour_key_md() in readme, "README colour key is stale: run python report.py"
    assert all(len(rgb) == 3 and all(0 <= c <= 1 for c in rgb) for rgb, _, _ in mule.COLORS.values())


def test_every_cad_colour_group_has_a_part_code():
    assert set(m.PART_CODE) == set(m.COLORS)
