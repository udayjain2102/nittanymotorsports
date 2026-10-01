"""loads.py: link statics, buckling, frame under wheel loads."""
import numpy as np
import loads as L


def test_321_support_statics():
    L.selfcheck()


def test_upright_equilibrium_every_case():
    for axle in ("front", "rear"):
        C, links = L.corner(axle)
        for F in L.cases(axle).values():
            f = L.link_forces(C, links, F)
            force = np.asarray(F, float) + sum(v * (np.subtract(q, p) / np.linalg.norm(np.subtract(q, p)))
                                                for v, (_, p, q, _) in zip(f, links))
            assert np.allclose(force, 0, atol=1e-6)


def test_links_dont_buckle_and_frame_holds():
    worst_link, which, worst_frame = L.run(verbose=False)
    assert worst_link > 2, which
    if worst_frame <= 1.0:   # print every case: a rounding-sensitive rocker choice once failed this only on some CI CPUs
        import io, contextlib, platform
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            L.run(verbose=True)
        raise AssertionError(f"frame FoS {worst_frame:.3f} on {platform.processor() or platform.machine()}\n{buf.getvalue()}")
