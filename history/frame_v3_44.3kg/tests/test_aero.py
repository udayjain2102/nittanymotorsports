"""aero.py: forces, axle split, DRS logic, geometry and mounts."""
import math
import aero as A


def test_all_aero_checks_pass():
    failed = [(n, d) for n, ok, d in A.checks() if not ok]
    assert not failed, failed


def test_forces_are_q_s_c():
    v = 20.0; q = 0.5 * A.RHO * v * v
    L_, D = A.forces(v, "closed")
    assert math.isclose(L_, q * A.area() * A.COEF["closed"]["cl"]) and math.isclose(D, q * A.area() * A.COEF["closed"]["cd"])


def test_axle_split_sums_to_downforce():
    f, r = A.axle_split(25.0)
    assert math.isclose(f + r, A.forces(25.0)[0], rel_tol=1e-9)


def test_drs_truth_table_fails_closed():
    assert A.drs_open(True, False)                      # button held, no brake: open
    assert not A.drs_open(True, True)                   # braking: closed
    assert not A.drs_open(False, False)                 # button released: closed
    assert not A.drs_open(True, False, powered=False)   # power lost: spring closes it


def test_flap_rotates_about_its_pivot():
    c, o = A.section("closed"), A.section("open")
    assert math.dist(c["pivot"], o["pivot"]) < 1e-9
    assert math.isclose(math.dist(o["fle"], o["fte"]), A.FLAP["chord"], rel_tol=1e-9)
