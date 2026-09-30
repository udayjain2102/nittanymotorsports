"""NM26 detailed CAD: one STEP per part + one assembly STEP.

Same geometry inputs as mule.py (nodes, links, rockers, brakes, powertrain, electrical) but each part is
modelled with its real features instead of a primitive: treaded tyres on spoked rims with lug nuts,
hubs with studs, drilled rotors with hats, calipers with pistons and bleed screws, A-arms with rod ends
and ball joints, plate rockers, coil-over shocks with helical springs, CV shafts with bellows boots,
toothed sprockets, a finned engine, pickup tabs on the frame, etc.

Run:  python cad_parts.py
  -> cad/parts/NM26-<sys>-<nnn>_<name>.step   one file per part, already in its assembly position (Z-up)
  -> cad/NM26_Assembly.step                   the full car as a nested assembly (system sub-assemblies)
  -> cad/parts.csv                            part number, name, sub-assembly, file

Fusion: File > Open the assembly STEP for the whole car (each part becomes a component). To rebuild the
assembly from the part files, Insert each part STEP and leave it at the origin: every part file is already
positioned, so no joints are needed to line them up.
"""
import csv, math, pathlib
import cadquery as cq
import mule as m
import uprights as U, rocker, brakes as BR, powertrain as PT, shutdown as SD
from mule import N, mir, tube, box, cyl_x, cyl_z, sub, norm, SIZES, TIRE_OD, TIRE_W, WHEELBASE, TRACK_F, TRACK_R

V = cq.Vector
def unit(v): n = norm(v); return tuple(x / n for x in v)
def add3(a, b, k=1.0): return tuple(x + k * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def cyl(a, b, r):  # solid cylinder from a to b
    d = sub(b, a); return cq.Solid.makeCylinder(r, norm(d), V(*a), V(*unit(d)))
def sphere(p, r): return cq.Solid.makeSphere(r, V(*p))
def fuse(*shapes):
    s = shapes[0]
    for t in shapes[1:]: s = s.fuse(t)
    return s.clean()
def fillet_all(shape, r):
    try: return cq.Workplane().add(shape).edges().fillet(r).val()
    except Exception: return shape          # ponytail: skip the fillet if OCC can't do it, geometry still right
def plane(origin, normal, xdir=None):
    n = unit(normal)
    if xdir is None:
        xdir = cross(n, (0, 1, 0)) if abs(n[1]) < 0.9 else cross(n, (1, 0, 0))
    return cq.Plane(origin=V(*origin), xDir=V(*unit(xdir)), normal=V(*n))
def mirror_z(shape): return shape.mirror("XY", (0, 0, 0))   # right side -> left side
def polar(shape, n, axis_pt, axis_dir):
    return [shape.rotate(V(*axis_pt), V(*add3(axis_pt, axis_dir)), 360 * i / n) for i in range(n)]

# ---------------- CORNER PARTS (right side, world coords) ----------------
RIM_R, RIM_W = 165.0, 170.0     # 13 in rim: bead seat radius, barrel width
LUG_PCD, LUGS = 100.0, 4

def tyre(x, zc):
    """Treaded tyre: revolved rounded profile, 3 circumferential grooves, 2 rows of transverse sipes."""
    y = TIRE_OD / 2; R = TIRE_OD / 2; w = TIRE_W / 2
    prof = [(RIM_R, -w + 5), (R - 28, -w), (R - 6, -w + 18), (R, -w + 32), (R, w - 32), (R - 6, w - 18), (R - 28, w), (RIM_R, w - 5)]
    t = cq.Workplane("XZ", origin=(0, 0, 0)).polyline([(r, z) for r, z in prof]).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    # XZ workplane: local x = world X, local y = world Z; revolve about local y = world Z (wheel axis)
    for z in (-42, 0, 42):
        t = t.cut(cyl_z(0, 0, z - 3, z + 3, R + 1).cut(cyl_z(0, 0, z - 3, z + 3, R - 7)))
    sipe = cq.Solid.makeBox(4, 20, 24, V(R - 6, -10, 0))
    for zoff, phase in ((-w + 30, 0.0), (w - 54, 6.0)):
        for s in polar(sipe.translate(V(0, 0, zoff)), 30, (0, 0, 0), (0, 0, 1)):
            t = t.cut(s.rotate(V(0, 0, 0), V(0, 0, 1), phase))
    return t.translate(V(x, y, zc))

def rim(x, zc, z_face):
    """Rim: barrel + drop centre, outboard spoked centre disc with lug holes and centre bore."""
    y = TIRE_OD / 2
    barrel = cyl_z(0, 0, -RIM_W / 2, RIM_W / 2, RIM_R).cut(cyl_z(0, 0, -RIM_W / 2, RIM_W / 2, RIM_R - 4))
    for z in (-RIM_W / 2, RIM_W / 2 - 4):   # bead flanges
        barrel = barrel.fuse(cyl_z(0, 0, z, z + 4, RIM_R + 8).cut(cyl_z(0, 0, z, z + 4, RIM_R - 4)))
    zd = z_face - zc
    disc = cyl_z(0, 0, zd - 8, zd, RIM_R - 3).cut(cyl_z(0, 0, zd - 8, zd, 32))
    for i in range(LUGS):
        a = 2 * math.pi * i / LUGS
        disc = disc.cut(cyl_z(LUG_PCD / 2 * math.cos(a), LUG_PCD / 2 * math.sin(a), zd - 9, zd + 1, 7))
    for i in range(5):   # windows between the spokes
        a = 2 * math.pi * (i + 0.5) / 5
        disc = disc.cut(cyl_z(100 * math.cos(a), 100 * math.sin(a), zd - 9, zd + 1, 34))
    return fuse(barrel, disc).translate(V(x, y, zc))

def lug_nuts(x, zc, z_face):
    y = TIRE_OD / 2; d = 1 if z_face > zc else -1
    nut = cq.Workplane(plane((0, 0, z_face), (0, 0, d))).polygon(6, 19).extrude(12).val()
    nuts = [nut.translate(V(LUG_PCD / 2 * math.cos(2 * math.pi * i / LUGS), LUG_PCD / 2 * math.sin(2 * math.pi * i / LUGS), 0)) for i in range(LUGS)]
    return fuse(*nuts).translate(V(x, y, 0))

def hub(g):
    hx, hy = g["x"], g["r"]; zlo = g["zi"] - U.BEARING["B"] / 2 - 8; face = g["face"]
    shaft = cyl_z(hx, hy, zlo, face, U.HUB["od"] / 2).cut(cyl_z(hx, hy, zlo, face, U.HUB["id"] / 2))
    flange = cyl_z(hx, hy, face - 8, face, 65)
    studs = [cyl_z(hx + LUG_PCD / 2 * math.cos(2 * math.pi * i / LUGS), hy + LUG_PCD / 2 * math.sin(2 * math.pi * i / LUGS), face - 8, face + 30, 6) for i in range(LUGS)]
    return fuse(shaft, flange, *studs)

def rotor(g):
    hx, hy, zr, face = g["x"], g["r"], g["rotor"], g["face"]; R = U.ROTOR_OD / 2
    ring = cyl_z(hx, hy, zr - 2, zr + 2, R).cut(cyl_z(hx, hy, zr - 2, zr + 2, R - 32))
    for i in range(24):
        a = 2 * math.pi * i / 24
        ring = ring.cut(cyl_z(hx + (R - 16) * math.cos(a), hy + (R - 16) * math.sin(a), zr - 3, zr + 3, 3))
    hat = cyl_z(hx, hy, zr - 2, face - 8, R - 30).cut(cyl_z(hx, hy, zr - 2, face - 8, R - 34))
    hat_top = cyl_z(hx, hy, face - 12, face - 8, R - 30).cut(cyl_z(hx, hy, face - 12, face - 8, 30))
    return fuse(ring, hat, hat_top)

def caliper(g):
    hx, hy, zr = g["x"], g["r"], g["rotor"]; R = U.ROTOR_OD / 2
    body = fillet_all(box(hx - 60, hx + 20, hy + R - 30, hy + R + U.CALIPER_H - 30, zr - 18, zr + 18), 5)
    body = body.cut(box(hx - 65, hx + 25, hy + R - 40, hy + R + 4, zr - 3.5, zr + 3.5))       # rotor slot
    for dx in (-38, -2):    # piston bosses, one each side
        for dz in (-18, 18):
            body = body.fuse(cyl_z(hx + dx, hy + R - 8, zr + dz - (4 if dz < 0 else 0), zr + dz + (4 if dz > 0 else 0), 13))
    bleed = cyl_z(hx - 50, hy + R + U.CALIPER_H - 30, zr + 18, zr + 30, 3.5)
    return fuse(body, bleed)

def upright(g, links):
    hx, hy = g["x"], g["r"]; hr = U.BEARING["D"] / 2 + U.UPRIGHT["wall"]
    zlo, zhi = g["zi"] - U.BEARING["B"] / 2 - 3, g["zo"] + U.BEARING["B"] / 2 + 3
    body = cyl_z(hx, hy, zlo, zhi, hr).cut(cyl_z(hx, hy, zlo - 1, zhi + 1, U.BEARING["D"] / 2))
    for _, p, _, _ in links:
        body = body.fuse(tube((hx, hy, p[2]), p, (U.UPRIGHT["w"], U.UPRIGHT["w"] / 2)))
        body = body.fuse(cyl_z(p[0], p[1], p[2] - 14, p[2] + 14, 13))   # ball-joint / rod-end boss
    return body

def rod_end(p, axis, r=9, L=22):
    a = unit(axis); return fuse(sphere(p, r), cyl(add3(p, a, -L / 2), add3(p, a, L / 2), r * 0.55))

def a_arm(links):
    """Two tubes to a common ball joint, with rod ends at the inboard pickups and a ball-joint housing outboard."""
    (n1, bj, q1, _), (n2, _, q2, _) = links
    hinge = unit(sub(q2, q1))
    tubes = [tube(q, bj, m.SUSP_TUBE) for q in (q1, q2)]
    return fuse(*tubes, rod_end(q1, hinge), rod_end(q2, hinge), sphere(bj, 14), cyl(add3(bj, (0, 1, 0), -18), add3(bj, (0, 1, 0), 18), 10))

def link_rod(p, q, size):
    return fuse(tube(p, q, size), sphere(p, 10), sphere(q, 10))

def pickup_tabs(q, other_q, out_pt):
    """Double-shear tabs on the frame at an inboard pickup: two 3 mm plates either side of the rod end."""
    h = unit(sub(other_q, q)); u = sub(out_pt, q); u = unit(sub(u, tuple(x * sum(a * b for a, b in zip(u, h)) for x in h)))
    tabs = []
    for s in (-1, 1):
        pl = plane(add3(add3(q, h, s * 13), u, 8), h, u)
        tabs.append(cq.Workplane(pl).center(0, 0).rect(34, 26).extrude(3).val())
    return fuse(*tabs)

def rocker_plate(P, A, B):
    n = unit(cross(sub(A, P), sub(B, P))); pl = plane(P, n, sub(A, P))
    to2 = lambda p: (sum(a * b for a, b in zip(sub(p, P), pl.xDir.toTuple())), sum(a * b for a, b in zip(sub(p, P), pl.yDir.toTuple())))
    plate = cq.Workplane(pl).polyline([(0, 0), to2(A), to2(B)]).close().offset2D(14).extrude(4, both=True).val()
    for p in (P, A, B):
        plate = plate.cut(cyl(add3(p, n, -6), add3(p, n, 6), 5))
    return fuse(plate, cyl(add3(P, n, -14), add3(P, n, 14), 10).cut(cyl(add3(P, n, -15), add3(P, n, 15), 5))), n

def shock(B, S, n):
    """Coil-over: eye at the rocker (B), damper body, reservoir, helical spring, shaft, eye at the frame (S)."""
    d = unit(sub(S, B)); L = norm(sub(S, B)); at = lambda k: add3(B, d, k)
    eye = lambda p: cyl(add3(p, n, -11), add3(p, n, 11), 11).cut(cyl(add3(p, n, -12), add3(p, n, 12), 5))
    body = cyl(at(14), at(L * 0.58), 17)
    res = cyl(add3(at(25), cross(d, n), 30), add3(at(L * 0.45), cross(d, n), 30), 12)
    res = res.fuse(cyl(add3(at(45), cross(d, n), 10), add3(at(45), cross(d, n), 30), 8))
    shaft = cyl(at(L * 0.58), at(L - 12), 6)
    seat_lo, seat_hi = cyl(at(L * 0.18), at(L * 0.18 + 5), 30), cyl(at(L - 20), at(L - 15), 30)
    h = cq.Wire.makeHelix(18, L - 20 - 5 - (L * 0.18 + 5), 25, center=V(*at(L * 0.18 + 5)), dir=V(*d))
    spring = cq.Workplane(cq.Plane(origin=h.startPoint(), normal=h.tangentAt(0))).circle(4).sweep(h, isFrenet=True).val()
    return fuse(eye(B), body, res, shaft, seat_lo, seat_hi, spring, eye(S), cyl(at(0), at(14), 9))

def bellows(x, y, z0, z1, r_in, r_out, folds):
    pts = [(r_in, z0)]
    for i in range(folds):
        za, zb = z0 + (i + 0.5) * (z1 - z0) / folds, z0 + (i + 1) * (z1 - z0) / folds
        pts += [(r_out, za), (r_in + 4, zb)]
    prof = pts + [(r_in - 4, z1), (r_in - 4, z0)]
    b = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    return b.translate(V(x, y, 0))

def cv_shaft(z_in, z_out):
    y = TIRE_OD / 2; s = 1 if z_out > z_in else -1
    shaft = cyl_z(0, y, min(z_in, z_out), max(z_in, z_out), 12)
    inner = cyl_z(0, y, min(z_in - s * 45, z_in + s * 10), max(z_in - s * 45, z_in + s * 10), 32)   # tripod housing
    outer = cyl_z(0, y, min(z_out - s * 40, z_out), max(z_out - s * 40, z_out), 33)               # outer CV joint
    b1 = bellows(0, y, z_in + s * 10, z_in + s * 75, 16, 30, 5) if s > 0 else bellows(0, y, z_in - 75, z_in - 10, 16, 30, 5)
    b2 = bellows(0, y, z_out - 105, z_out - 40, 16, 30, 5) if s > 0 else bellows(0, y, z_out + 40, z_out + 105, 16, 30, 5)
    return fuse(shaft, inner, outer, b1, b2)

# ---------------- OTHER SYSTEMS ----------------
def frame_tubes():
    return [(tube(a, b, s), s, role) for a, b, s, role in m.MEMBERS]

def frame_brackets():
    """Pickup tabs for every A-arm inboard pickup and rear toe-link, shock tabs, rocker pivot bushings."""
    out = []
    for ax in ("front", "rear"):
        links = m.susp_links(ax)
        for pair in (links[0:2], links[2:4]):
            (_, bj, q1, _), (_, _, q2, _) = pair
            out += [("pickup_tabs", pickup_tabs(q1, q2, bj)), ("pickup_tabs", pickup_tabs(q2, q1, bj))]
        if ax == "rear":   # toe-link inboard tab, hinge along X
            _, p, q, _ = links[4]
            out.append(("toe_link_tabs", pickup_tabs(q, add3(q, (1, 0, 0), 50), p)))
        r = rocker.analyse(ax); P, S, B = tuple(r["g"]["P"]), tuple(r["g"]["S"]), tuple(r["B3"])
        _, n = rocker_plate(P, tuple(r["A3"]), B)
        out.append(("shock_tabs", pickup_tabs(S, add3(S, n, 50), B)))
        out.append(("rocker_pivot_bushing", cyl(add3(P, n, -24), add3(P, n, 24), 8)))
    return [(nm, s) for nm, s in out] + [(nm, mirror_z(s)) for nm, s in out]

def sprocket(c, r_pitch, teeth, bore, lightening):
    z = PT.CHAIN_Z; R = r_pitch + 5
    d = cyl_z(c[0], c[1], z - 4, z + 4, R).cut(cyl_z(c[0], c[1], z - 5, z + 5, bore))
    t = cq.Solid.makeBox(7, 5.5, 10, V(c[0] + R - 5, c[1] - 2.75, z - 5))
    for tt in polar(t, teeth, (c[0], c[1], z), (0, 0, 1)):
        d = d.cut(tt)
    if lightening:
        for i in range(6):
            a = 2 * math.pi * i / 6
            d = d.cut(cyl_z(c[0] + 0.62 * R * math.cos(a), c[1] + 0.62 * R * math.sin(a), z - 5, z + 5, 0.16 * R))
    return d

def chain_run(a, b):
    d = unit(sub(b, a)); return cq.Workplane(plane(a, d)).rect(10, 17).extrude(norm(sub(b, a))).val()

def engine():
    x0, x1, y0, y1, z0, z1 = PT.ENGINE["box"]
    case = fillet_all(box(x0, x1, y0, y0 + 200, z0, z1), 15)
    cx = (x0 + x1) / 2 + 30
    cylinder = cq.Solid.makeCylinder(55, 95, V(cx, y0 + 200, 0), V(0, 1, 0))
    fins = [cq.Solid.makeCylinder(78, 3, V(cx, y0 + 205 + 9 * i, 0), V(0, 1, 0)) for i in range(10)]
    head = fillet_all(box(cx - 62, cx + 62, y0 + 295, y1, -60, 60), 8)
    cover = cyl_z(x0 + 70, y0 + 90, z0 - 12, z0, 60)     # clutch cover, left side (chain side)
    cover2 = cyl_z(x1 - 90, y0 + 100, z1, z1 + 12, 55)   # ignition cover, right side
    return fuse(case, cylinder, *fins, head, cover, cover2)

def spool(zs):
    y = TIRE_OD / 2
    s = cyl_z(0, y, -zs + 20, zs - 20, 25).cut(cyl_z(0, y, -zs + 19, zs - 19, 10))
    for z in (-zs + 40, zs - 60):
        s = s.fuse(cyl_z(0, y, z, z + 10, 60))            # bearing shoulders
    s = s.fuse(cyl_z(0, y, PT.CHAIN_Z + 6, PT.CHAIN_Z + 16, 70))   # sprocket carrier flange
    return s

def spool_carrier(zs, sg):
    y = TIRE_OD / 2; z0, z1 = sorted((sg * zs - 8, sg * zs + 8))
    c = fillet_all(box(-50, 50, y - 60, y + 60, z0, z1), 8).cut(cyl_z(0, y, z0 - 1, z1 + 1, 42.5))
    for dx, dy in ((-38, -48), (38, -48), (-38, 48), (38, 48)):
        c = c.cut(cyl_z(dx, y + dy, z0 - 1, z1 + 1, 4.5))
    return c

def steering_wheel():
    c = (m.WHEEL_C[0], m.WHEEL_C[1], 0.0); R = m.WHEEL_DIA / 2
    w = cq.Solid.makeTorus(R - 14, 14, V(*c), V(1, 0, 0))
    spokes = [cq.Solid.makeBox(8, R - 20, 24, V(c[0] - 4, c[1], c[2] - 12)).rotate(V(*c), V(c[0] + 1, c[1], c[2]), a) for a in (0, 120, 240)]
    hub_ = cyl_x(c[0] - 20, c[0] + 8, c[1], c[2], 32)
    return fuse(w, *spokes, hub_)

def steering_column():
    a, b = (m.WHEEL_C[0] - 20, m.WHEEL_C[1], 0.0), (m.RACK[0], m.RACK[1], 0.0)
    mid = add3(a, sub(b, a), 0.55)
    return fuse(tube(a, b, "C"), sphere(mid, 16), cyl(add3(a, (1, 0, 0), -5), add3(a, (1, 0, 0), 5), 22))

def steering_rack():
    x, y, hl = m.RACK
    housing = cyl_z(x, y, -hl + 30, hl - 30, m.RACK_R).cut(cyl_z(x, y, -hl + 29, hl - 29, 11))
    bar = cyl_z(x, y, -hl, hl, 10)
    lugs = [box(x - 12, x + 12, y - 45, y, z - 8, z + 8) for z in (-90, 90)]
    pinion = cyl(add3((x, y, 0), (0, 1, 0), 0), add3((x, y, 0), (-0.98, 0.17, 0), -45), 12)
    return fuse(housing, bar, *lugs, sphere((x, y, -hl), 11), sphere((x, y, hl), 11), pinion)

def seat_shell():
    hx = m.HIP[0]; y0 = m.SEAT_Y0
    base = box(hx - 80, m.X_PEDAL - 450, y0, y0 + 6, -200, 200)
    back = box(hx - 90, hx - 40, y0, m.SHOULDER[1] + 40, -200, 200)
    bolsters = [box(hx - 90, m.X_PEDAL - 450, y0, y0 + 120, s * 200 - (6 if s > 0 else 0), s * 200 + (6 if s < 0 else 0)) for s in (-1, 1)]
    wings = [box(hx - 90, hx - 40, y0 + 300, m.SHOULDER[1] + 40, s * 200 - (6 if s > 0 else 0), s * 200 + (6 if s < 0 else 0)) for s in (-1, 1)]
    return fillet_all(fuse(base, back, *bolsters, *wings), 4)

def pedal(nm, z):
    g = BR.geometry(); (xp, yp), (xa, ya) = g["piv"], g["pad"]
    arm = tube((xp, yp, z), (xa, ya, z), (BR.PEDAL["b"] * 2, BR.PEDAL["b"]))
    pad = fillet_all(box(xa - 8, xa, ya - 40, ya + 40, z - 35, z + 35), 3)
    return fuse(arm, pad, cyl_z(xp, yp, z - 18, z + 18, 12))

# ---------------- ASSEMBLY ----------------
class Build:
    def __init__(self):
        self.root = cq.Assembly(name="NM26_Mule"); self.count = {}; self.rows = []; self.subs = {}
    def sub(self, name):   # sub-assemblies are attached in finish(): Assembly.add copies its argument
        if name not in self.subs:
            self.subs[name] = cq.Assembly(name=name)
        return self.subs[name]
    def finish(self):
        for name in sorted(self.subs): self.root.add(self.subs[name])
        return self
    def add(self, shape, name, key, group):
        code = m.PART_CODE[key]; self.count[code] = self.count.get(code, 0) + 1
        pn = f"NM26-{code}-{self.count[code]:03d}"; full = f"{pn}_{name}"
        self.sub(group).add(shape, name=full, color=m.color(key))
        self.rows.append((pn, name, group, m.COLORS[key][1], full + ".step", shape))
        return shape

def build():
    b = Build()
    # frame weldment: every tube and bracket is a body in one sub-assembly
    for i, (t, s, role) in enumerate(frame_tubes()):
        b.add(t, f"tube_{s}_{role.split(' (')[0].replace(' ', '_').replace('/', '-')}", {"J": "frame_heavy", "H": "frame_heavy", "A": "frame_heavy", "B": "frame_b", "C": "frame_c"}[s], "01_frame_weldment")
    for nm, s in frame_brackets():
        b.add(s, nm, "frame_b", "01_frame_weldment")
    # corners
    for ax, x, tr in (("front", WHEELBASE, TRACK_F), ("rear", 0.0, TRACK_R)):
        g = U.geom(ax); links = m.susp_links(ax); zc = tr / 2
        r = rocker.analyse(ax); P, A, B, S = (tuple(r[k]) if k in ("A3", "B3") else tuple(r["g"][k]) for k in ("P", "A3", "B3", "S"))
        plate, n = rocker_plate(P, A, B)
        right = [
            ("tyre", tyre(x, zc), "wheel"), ("rim_13in", rim(x, zc, g["face"]), "corner"), ("lug_nuts", lug_nuts(x, zc, g["face"]), "corner"),
            ("hub", hub(g), "corner"), ("rotor_drilled", rotor(g), "corner"), ("caliper", caliper(g), "brake"),
            ("upright", upright(g, links), "corner"),
            ("lower_a_arm", a_arm(links[0:2]), "suspension"), ("upper_a_arm", a_arm(links[2:4]), "suspension"),
            (("tie_rod" if ax == "front" else "toe_link"), link_rod(links[4][1], links[4][2], m.SUSP_TUBE), "suspension"),
            ("pushrod", link_rod(links[5][1], links[5][2], m.PUSHROD_TUBE), "pushrod"),
            ("rocker_plate", plate, "rocker"), ("coilover_shock", shock(B, S, n), "shock"),
        ]
        for side, f in (("R", lambda s: s), ("L", mirror_z)):
            grp = f"02_corner_{ax}_{side}"
            for nm, s, key in right:
                b.add(f(s), f"{nm}_{ax}_{side}", key, grp)
    # cockpit
    b.add(seat_shell(), "seat_shell", "driver_cell", "03_cockpit")
    b.add(fillet_all(box(m.X_MAIN + 13, m.X_MAIN + 73, m.HEAD[1] - 140, m.HEAD[1] + 140, -80, 80), 10), "head_restraint", "driver_cell", "03_cockpit")
    g = BR.geometry(); (xb, yb) = g["bar"]
    b.add(box(m.PB_X[0] - 20, m.PB_X[1] + 10, g["y_base"] - 6, g["y_base"], -m.PB_Z - 20, m.PB_Z + 20), "pedal_box_base", "brake", "03_cockpit")
    for z, nm in ((BR.BRAKE_Z, "brake"), (BR.THROTTLE_Z, "throttle")):
        b.add(pedal(nm, z), f"{nm}_pedal", "brake", "03_cockpit")
    zb = BR.BRAKE_Z
    b.add(tube((xb, yb, zb - BR.BAR["e"] - 10), (xb, yb, zb + BR.BAR["e"] + 10), (BR.BAR["d"], BR.BAR["d"] / 2)), "balance_bar", "brake", "03_cockpit")
    for dz, ax in ((-BR.BAR["e"], "front"), (BR.BAR["e"], "rear")):
        mc = fuse(cyl_x(xb + BR.MC_ROD, g["mc_front"], yb, zb + dz, 16), cyl_x(xb + 5, xb + BR.MC_ROD, yb, zb + dz, 5),
                  cyl_x(xb + BR.MC_ROD + 45, xb + BR.MC_ROD + 55, yb + 16, zb + dz, 6))
        b.add(mc, f"master_cyl_{ax}_{BR.MC_BORE[ax] / 25.4:.3f}in", "brake", "03_cockpit")
        b.add(fuse(cyl_x(xb + BR.MC_ROD, xb + BR.MC_ROD + 40, yb + 70, zb + dz, 18), cyl_x(xb + BR.MC_ROD + 45, xb + BR.MC_ROD + 56, yb + 70, zb + dz, 12)),
              f"reservoir_{ax}", "brake", "03_cockpit")
    b.add(steering_wheel(), "steering_wheel", "steering", "03_cockpit")
    b.add(steering_column(), "steering_column", "steering", "03_cockpit")
    b.add(steering_rack(), "steering_rack", "steering", "03_cockpit")
    # powertrain
    b.add(engine(), "engine_450cc_single_placeholder", "powertrain", "04_powertrain")
    cs, r1, ax_, r2 = PT.sprockets()
    b.add(sprocket(cs, r1, PT.FRONT_T, 12, False), f"sprocket_front_{PT.FRONT_T}T", "powertrain", "04_powertrain")
    b.add(sprocket(ax_, r2, PT.REAR_T, 26, True), f"sprocket_rear_{PT.REAR_T}T", "powertrain", "04_powertrain")
    for sg in (1, -1):
        b.add(chain_run((cs[0], cs[1] + sg * r1, PT.CHAIN_Z), (ax_[0], ax_[1] + sg * r2, PT.CHAIN_Z)), f"chain_{'top' if sg > 0 else 'bottom'}", "powertrain", "04_powertrain")
    zs = N["sp_c"][2]
    b.add(spool(zs), "spool", "powertrain", "04_powertrain")
    for sg, side in ((1, "R"), (-1, "L")):
        b.add(spool_carrier(zs, sg), f"spool_carrier_{side}", "powertrain", "04_powertrain")
        cv = cv_shaft(PT.CV["z_in"], U.geom("rear")["zi"] - 10)
        b.add(cv if sg > 0 else mirror_z(cv), f"cv_halfshaft_{side}", "powertrain", "04_powertrain")
    fc = fuse(fillet_all(box(m.X_MAIN - 213, m.X_MAIN - 43, 480, 700, -140, 140), 8), cyl(( m.X_MAIN - 128, 700, 0), (m.X_MAIN - 128, 740, 0), 22))
    b.add(fc, "fuel_cell_6L", "fuel", "04_powertrain")
    # body / closeout
    b.add(box(m.IA[0] - 1.5, m.IA[0], m.Y_BH_BOT, m.Y_BH_TOP, -m.Z_BH, m.Z_BH), "anti_intrusion_plate", "closeout", "05_body")
    ia = box(*m.IA[:4], -m.IA[4], m.IA[4])
    try: ia = cq.Workplane().add(ia).faces(">X").chamfer(25).val()
    except Exception: pass
    b.add(ia, "impact_attenuator", "crash", "05_body")
    b.add(box(m.X_MAIN - 40, m.X_MAIN - 13, m.Y_LOW, 700, -m.Z_COCKPIT, m.Z_COCKPIT), "firewall", "closeout", "05_body")
    b.add(m.belly_pan(), "belly_pan_1.6mm", "closeout", "05_body")
    # electrical
    for nm, (w, h, d) in (("battery", (150, 90, 90)), ("primary master switch", (60, 60, 40)), ("e-stop", (40, 40, 40)),
                          ("inertia switch", (50, 50, 40)), ("kill relay", (40, 40, 30)), ("brake light", (20, 60, 160))):
        x, y, z = SD.LOC[nm]
        s = fillet_all(box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2), 3)
        if nm == "battery":
            s = fuse(s, cyl((x + 50, y + h / 2, z), (x + 50, y + h / 2 + 14, z), 7), cyl((x - 50, y + h / 2, z), (x - 50, y + h / 2 + 14, z), 7))
        if nm == "e-stop":
            s = fuse(s, cyl((x, y + h / 2, z), (x, y + h / 2 + 12, z), 6), cyl((x, y + h / 2 + 12, z), (x, y + h / 2 + 22, z), 18))
        b.add(s, nm.replace(" ", "_"), "electrical", "06_electrical")
    return b.finish()

ZUP = cq.Location(V(), V(1, 0, 0), 90)   # model Y-up -> STEP Z-up (Fusion default)

if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "cad"; (out / "parts").mkdir(parents=True, exist_ok=True)
    b = build()
    bad = [(pn, nm) for pn, nm, _, _, _, s in b.rows if not s.isValid() or s.Volume() <= 0]
    assert not bad, f"invalid solids: {bad}"
    import sys
    for pn, nm, grp, col, fn, s in b.rows:
        if "--assembly-only" in sys.argv: break
        cq.exporters.export(s.rotate(V(0, 0, 0), V(1, 0, 0), 90), str(out / "parts" / fn))
    cq.Assembly(name="NM26_Mule_Zup").add(b.root, loc=ZUP).save(str(out / "NM26_Assembly.step"))
    with open(out / "parts.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["part_number", "name", "sub_assembly", "colour", "file"])
        w.writerows(r[:5] for r in b.rows)
    shape = cq.Compound.makeCompound([r[5] for r in b.rows])
    for nm, d in [("iso", (1, 0.6, 1)), ("side", (0, 0, 1)), ("front", (1, 0, 0)), ("top", (0, 1, 0))]:
        cq.exporters.export(shape, str(out / f"view_{nm}.svg"), opt={"projectionDir": d, "showHidden": False, "width": 1400, "height": 800})
    print(f"wrote {len(b.rows)} part files in cad/parts, cad/NM26_Assembly.step, cad/parts.csv, cad/view_*.svg")
