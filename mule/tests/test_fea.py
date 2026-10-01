"""fea.py: beam element correctness + frame load cases."""
import fea


def test_cantilever_and_inertia_relief():
    fea.selfcheck()   # beam vs PL^3/3EI, and inertia relief balances applied loads to zero


def test_hoop_cases_and_torsion():
    r = fea.run(verbose=False)
    assert r["fos"]["Main hoop"] >= 1.0 and r["fos"]["Front hoop"] >= 1.0, r["fos"]   # vs welded 4130 yield (fea.SY_ROLL)
    assert r["torsion"] > 1400, r["torsion"]
    assert max(r["defl"].values()) <= 25, r["defl"]          # AF4.1/AF4.2 deflection limit


def test_inertia_relief_stress_independent_of_support_node():
    # a singular support set once gave CPU-dependent frame stresses in CI (loads FoS 0.83 vs 1.26)
    import numpy as np, mule as m
    fr = fea.Frame(m.MEMBERS)
    ld, sup = fea.inertia_relief(fr, {fr.find(m.N["sp_c"]): np.array([2000.0, 3000.0, -1500.0])})
    _, st1 = fr.solve(ld, sup)
    _, st2 = fr.solve(ld, {len(fr.P) - 1: range(6)})
    assert np.allclose(st1, st2, rtol=1e-6, atol=1e-6)
