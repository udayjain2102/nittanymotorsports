"""fab.py: cope geometry, bend programs, cut sheet integrity."""
import math
import numpy as np
import fab
import mule as m


def test_perpendicular_cope_long_point():
    lp, sp = fab.cope_depths((0, 0, 1), 12.7, (1, 0, 0), 15.875)
    assert math.isclose(lp, math.sqrt(15.875**2 - 12.7**2), rel_tol=1e-3)
    assert math.isclose(sp, 15.875, rel_tol=1e-3)


def test_90_degree_bend_program():
    rows, last, dev, mn = fab.bend_program([(0, 0, 0), (500, 0, 0), (500, 500, 0)], 100.0)
    assert len(rows) == 1 and math.isclose(rows[0][2], 90.0)
    assert math.isclose(rows[0][0], 400.0) and math.isclose(last, 400.0)
    assert math.isclose(dev, 800.0 + math.pi * 50.0)


def test_pieces_cover_every_member_once():
    pcs = fab.pieces()
    piece_len = sum(np.linalg.norm(np.subtract(p["pts"][i + 1], p["pts"][i])) for p in pcs for i in range(len(p["pts"]) - 1))
    member_len = sum(m.norm(m.sub(b, a)) for a, b, _, _ in m.MEMBERS)
    assert math.isclose(piece_len, member_len, rel_tol=1e-9)


def test_hoops_bendable_with_legal_radius():
    for p in fab.pieces():
        if p["bent"]:
            clr = fab.CLR_BY_SIZE[p["size"]]
            assert clr >= 3 * m.SIZES[p["size"]][0], "F.5.2.1"
            assert fab.bend_program(p["pts"], clr)[3] >= 50, f"{p['role']}: < 50 mm straight between bends"


def test_every_tube_end_has_a_joint_and_never_copes_onto_a_smaller_tube():
    pcs = fab.pieces()
    for p, _, ends in fab.cope_ends(pcs):
        if p["bent"]:
            continue
        for e in ends:
            assert e is not None, p["id"]
            if e["recv"] is not None:
                assert m.SIZES[e["recv"]["size"]][0] >= m.SIZES[p["size"]][0] - 0.05
                assert e["long"] is not None and e["angle"] >= 20, (p["id"], e["angle"])


def test_outputs_written(tmp_path):
    fab.write(tmp_path)
    for f in ("tube_cut_sheet.csv", "hoop_bend_program.csv", "jig_node_coordinates.csv", "jig_plan.png"):
        assert (tmp_path / f).stat().st_size > 0
