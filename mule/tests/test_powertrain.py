"""powertrain.py: gearing, chain drive, CV, engine mounts, frame under launch."""
import math
import numpy as np
import powertrain as P


def test_all_powertrain_checks_pass():
    failed = [(n, d) for n, ok, d in P.checks() if not ok]
    assert not failed, failed


def test_chain_length_formula_equal_sprockets():
    # equal sprockets: length = 2C/p + N exactly
    assert math.isclose(P.chain_links(500.0, 20, 20), 2 * 500 / P.CHAIN["pitch"] + 20)


def test_centre_for_links_inverts_chain_links():
    c = P.centre_for_links(60, P.FRONT_T, P.REAR_T)
    assert math.isclose(P.chain_links(c, P.FRONT_T, P.REAR_T), 60, rel_tol=1e-6)


def test_engine_mounts_balance_the_chain_force():
    F = np.array([-3000.0, 800.0, 0.0]); p = np.array([200.0, 283.0, -180.0])
    mounts = P.mount_forces(F, p)
    box = P.ENGINE["box"]; cg = np.array([(box[0] + box[1]) / 2, (box[2] + box[3]) / 2, 0.0])
    W = np.array([0, -2.5 * P.ENGINE["mass"] * P.L.G, 0])
    assert np.allclose(sum(f for _, _, f in mounts) + F + W, 0, atol=1e-6)
    M = sum(np.cross(q - cg, f) for _, q, f in mounts) + np.cross(p - cg, F)
    assert np.allclose(M, 0, atol=1e-3)
