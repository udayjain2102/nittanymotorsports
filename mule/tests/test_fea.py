"""fea.py: beam element correctness + frame load cases."""
import fea


def test_cantilever_and_inertia_relief():
    fea.selfcheck()   # beam vs PL^3/3EI, and inertia relief balances applied loads to zero


def test_hoop_cases_and_torsion():
    r = fea.run(verbose=False)
    assert r["fos"]["Main hoop"] > 1.2 and r["fos"]["Front hoop"] > 1.2, r["fos"]
    assert r["torsion"] > 1400, r["torsion"]
    assert max(r["defl"].values()) <= 25, r["defl"]          # AF4.1/AF4.2 deflection limit
