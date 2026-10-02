"""Roll: roll gradient, static camber and camber to the ground in a corner, roll-centre movement in roll, jacking.

Roll stiffness per axle = ride rate (wheel rate in series with the tyre) x track^2 / 2 (no anti-roll bars).
In a left turn the right wheel is outside: it moves up by roll x track/2 relative to the chassis, the left moves down.
Roll centre in roll: in the chassis frame, the line from each contact patch through its own instant centre; where
the two lines cross is the roll centre (lateral shift and height). Jacking: each tyre's side force times the slope of
its patch-to-IC line pushes the body up (outside wheel) or down (inside); the difference lifts the car.
Targets marked "(ours)" are our design choices, not rules.
Run: python roll.py
"""
import math
import loads as L
import mule as m
import sideview as V
import springs
import suspension as S

STATIC_CAMBER = {"front": -2.5, "rear": -2.0}   # deg at ride height (shims at the upper ball joint); + = top outward.
                                                # Set so the loaded outside tyre sits near -1 deg to the ground at DESIGN_G
DESIGN_G = L.MU

def upright_at(g, t):
    """Upright transform with the wheel at travel t (mm, + bump) relative to the chassis."""
    lo, hi = -0.8, 0.8
    for _ in range(60):
        mid = (lo + hi) / 2; f, _ = S.upright(g, mid)
        (lo, hi) = (mid, hi) if f(g["C"])[1] - g["C"][1] - t < 0 else (lo, mid)
    return S.upright(g, (lo + hi) / 2)

def roll_gradient():
    """Body roll (deg per g) from the sprung mass above the roll axis and both axles' ride rates."""
    k = {a: V.ride_rate(a) * (m.TRACK_F if a == "front" else m.TRACK_R) ** 2 / 2 for a in ("front", "rear")}   # N*mm/rad
    ms = sum(2 * springs.size(a)["sprung"] for a in k)
    rc = {a: S.analyse(S.geom(a))["rc"] for a in k}
    h_axis = rc["rear"] + (rc["front"] - rc["rear"]) * L.FRONT_SPLIT          # roll-axis height under the CG
    return math.degrees(ms * L.G * (L.CG_H - h_axis) / (k["front"] + k["rear"])), k

def camber_in_corner(axle, g_lat=DESIGN_G):
    """(outside, inside) wheel camber to the ground, deg, at g_lat. Body roll tilts the outside wheel top outward."""
    phi = roll_gradient()[0] * g_lat; tr = m.TRACK_F if axle == "front" else m.TRACK_R
    z = math.radians(phi) * tr / 2; g = S.geom(axle)
    dc = lambda t: -math.degrees(upright_at(g, t)[1])
    return STATIC_CAMBER[axle] + dc(z) + phi, STATIC_CAMBER[axle] + dc(-z) - phi

def rc_in_roll(axle, g_lat=DESIGN_G):
    """Roll centre (lateral shift toward the outside wheel, height) in the chassis frame at g_lat, mm, and each side's
    patch-to-IC slope (outside, inside)."""
    phi = roll_gradient()[0] * g_lat; tr = m.TRACK_F if axle == "front" else m.TRACK_R
    z = math.radians(phi) * tr / 2; g = S.geom(axle); lines = []
    for t, side in ((z, 1), (-z, -1)):                   # outside (right, +z) bumps, inside (left) droops
        f, _ = upright_at(g, t)
        ic = S.line_x(g["Al"], f(g["Bl"]), g["Au"], f(g["Bu"])); C = f(g["C"])
        lines.append(((side * C[0], C[1]), (side * ic[0], ic[1])))
    (c1, i1), (c2, i2) = lines
    rc = S.line_x(c1, i1, c2, i2)
    slope = lambda c, i: abs((i[1] - c[1]) / (i[0] - c[0]))
    return rc, slope(c1, i1), slope(c2, i2)

def jacking(axle, g_lat=DESIGN_G):
    """Net upward force on the body (N) and the resulting lift (mm) at g_lat."""
    w = L.MASS * L.G; share = L.FRONT_SPLIT if axle == "front" else 1 - L.FRONT_SPLIT
    tr = m.TRACK_F if axle == "front" else m.TRACK_R
    dW = w * share * g_lat * L.CG_H / tr; Fo, Fi = w * share / 2 + dW, w * share / 2 - dW
    _, so, si = rc_in_roll(axle, g_lat)
    F = g_lat * (Fo * so - Fi * si)
    return F, F / (2 * V.ride_rate(axle))

def lltd():
    """Front share of the total lateral load transfer (Milliken): each axle carries its roll-stiffness share of the
    sprung roll moment about the roll axis, plus its own geometric part (axle load x RC height). No anti-roll bars."""
    _, k = roll_gradient(); kf = k["front"] / (k["front"] + k["rear"])
    rc = {a: S.analyse(S.geom(a))["rc"] for a in k}
    h_axis = rc["rear"] + (rc["front"] - rc["rear"]) * L.FRONT_SPLIT
    w = L.MASS * L.G
    dWf = w / m.TRACK_F * (kf * (L.CG_H - h_axis) + L.FRONT_SPLIT * rc["front"])
    dWr = w / m.TRACK_R * ((1 - kf) * (L.CG_H - h_axis) + (1 - L.FRONT_SPLIT) * rc["rear"])
    return dWf / (dWf + dWr), kf

def checks():
    grad, _ = roll_gradient(); ll, kf = lltd(); out = [
        (f"front lateral load transfer share within front weight {100 * L.FRONT_SPLIT:.0f} % +0..+12 points (ours: mild understeer)",
         L.FRONT_SPLIT <= ll <= L.FRONT_SPLIT + 0.12, f"LLTD {100 * ll:.1f} % front (roll stiffness {100 * kf:.0f} % front, no bars)"),("roll gradient 0.5-2.0 deg/g (ours)", 0.5 <= grad <= 2.0, f"{grad:.2f} deg/g, {grad * DESIGN_G:.1f} deg at {DESIGN_G} g")]
    for a in ("front", "rear"):
        o, i = camber_in_corner(a); (dz, h), _, _ = rc_in_roll(a); rc0 = S.analyse(S.geom(a))["rc"]
        F, lift = jacking(a); tr = m.TRACK_F if a == "front" else m.TRACK_R
        out += [
            (f"{a} static camber -3.5..0 deg", -3.5 <= STATIC_CAMBER[a] <= 0, f"{STATIC_CAMBER[a]:+.1f} deg"),
            (f"{a} outside-wheel camber to ground -2.0..-0.3 deg at {DESIGN_G} g (ours)", -2.0 <= o <= -0.3,
             f"outside {o:+.2f}, inside {i:+.2f} deg"),
            (f"{a} roll centre stays above ground in roll (jacking keeps its sign)", h > 0,
             f"height {h:.0f} mm (static {rc0:.0f}); lateral shift {dz:+.0f} mm = {dz / (grad * DESIGN_G):+.0f} mm/deg (low RCs move far sideways)"),
            (f"{a} jacking lift <= 5 mm at {DESIGN_G} g (ours)", abs(lift) <= 5, f"{F:.0f} N, lift {lift:.1f} mm"),
        ]
    return out

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:72s} {d}")
    assert all(p for _, p, _ in res), "roll check failed"
