"""TEST_PLAN.md quotes predicted numbers; fail if the design code no longer produces them."""
import math
import pathlib
import brakes as B
import fea
import loads as L
import mule as m
import powertrain as P
import springs as S

PLAN = (pathlib.Path(__file__).resolve().parents[1] / "docs" / "TEST_PLAN.md").read_text()


def quoted(s):
    assert s in PLAN, f"TEST_PLAN.md is stale: expected '{s}'"


def test_brake_numbers():
    s = B.design_split()
    quoted(f"{B.lock_force(L.MU, s):.0f} N pedal on 1.5-grip")
    quoted(f"{B.lock_force(1.0, s):.0f} N on a 1.0-grip")
    p = B.pressures(500, s); quoted(f"| 500 N | {p['front']:.1f} bar | {p['rear']:.1f} bar |")
    p = B.pressures(2000, s); quoted(f"{p['front']:.0f} bar front, {p['rear']:.0f} bar rear")
    quoted(f"trips at {B.BOTS_TRAVEL:.0f} mm")


def test_frame_numbers():
    quoted(f"{fea.run(verbose=False)['torsion']:.0f} N·m/deg (`fea.py`)")
    mass = sum(fea.props(sz)[0] * math.dist(a, b) for a, b, sz, _ in m.MEMBERS) * m.STEEL_DENSITY
    quoted(f"{mass:.1f} kg of tube")


def test_tilt_margin():
    for tr in (m.TRACK_R, m.TRACK_F):
        quoted(f"{math.degrees(math.atan(tr / 2 / L.CG_H)):.1f}°")
    quoted(f"CG must be ≤ {m.TRACK_R / 2 / math.tan(math.radians(60)):.0f} mm")


def test_gearing_and_ride():
    E = P.ENGINE; r = m.TIRE_R_LOADED / 1000; fin = P.REAR_T / P.FRONT_T
    v = [5000 / (E["primary"] * g * fin) / 60 * 2 * math.pi * r * 3.6 for g in E["gears"]]
    quoted("| " + " | ".join(f"{x:.1f}" for x in v) + " |")
    quoted(f"{S.RIDE_HZ['front']} Hz front / {S.RIDE_HZ['rear']} Hz rear")


def test_event_predictions():
    import lapsim
    quoted(f"prediction is {lapsim.accel()[0]:.2f} s (`lapsim.py`")
    quoted(f"`lapsim.py`: {lapsim.skidpad()[0]:.2f} s at μ {lapsim.GRIP} without the wing")
    assert f"| {lapsim.skidpad(1.5, aero_on=False)[0]:.2f} |" in PLAN


def test_mass_numbers():
    import mass
    s = mass.summary()
    quoted(f"{s['kg']:.0f} kg with the driver")
    quoted(f"CG {s['cg_h']:.0f} mm")
    quoted(f"rolls at {s['tilt']:.1f}°")
