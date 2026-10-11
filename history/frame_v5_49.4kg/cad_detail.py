"""Detailed component models and rough routing for cad_parts.py.

Engine: a 450 cc air/oil-cooled single modelled feature by feature (cases, covers, finned cylinder, head, cam cover,
coil, throttle body, airbox, header, muffler, oil filter, starter, mounts). Components: real shapes for the parts that
were boxes (seat shell, head restraint, pedal box, fuel cell, firewall, dash, switches, relay, ECU, fan, battery...).
Routing: brake lines, throttle cable, fuel line and the 12 V harness as tubes along the frame, from the real
component positions (brakes.geometry, shutdown.LOC, uprights.geom), so the drawing shows where each run goes.

Axes as mule.py: X forward, Y up, Z right. mm. Nothing here is checked against a supplier's part; these are
representative shapes at the right size and place.
"""
import math
import cadquery as cq
import mule as m
import uprights as U, brakes as BR, powertrain as PT, shutdown as SD
from mule import N, box, cyl_x, cyl_z, sub, norm, tube, TIRE_OD

V = cq.Vector
def unit(v): n = norm(v); return tuple(x / n for x in v)
def add3(a, b, k=1.0): return tuple(x + k * y for x, y in zip(a, b))
def cyl(a, b, r):
    d = sub(b, a); return cq.Solid.makeCylinder(r, norm(d), V(*a), V(*unit(d)))
def sphere(p, r): return cq.Solid.makeSphere(r, V(*p))
def fuse(*shapes):
    s = shapes[0]
    for t in shapes[1:]: s = s.fuse(t)
    return s.clean()
def rbox(x0, x1, y0, y1, z0, z1, r):
    b = box(x0, x1, y0, y1, z0, z1)
    try: return cq.Workplane().add(b).edges().fillet(min(r, (x1 - x0) / 2.01, (y1 - y0) / 2.01, (z1 - z0) / 2.01)).val()
    except Exception: return b
def route(pts, r):
    """Round tube along a polyline, spheres at the corners (a rough routing, not a bend-radius-true run)."""
    parts = [cyl(a, b, r) for a, b in zip(pts, pts[1:])] + [sphere(p, r) for p in pts[1:-1]]
    return fuse(*parts)
def ring(x, y, z0, z1, ro, ri): return cyl_z(x, y, z0, z1, ro).cut(cyl_z(x, y, z0 - 1, z1 + 1, ri))

# ---------------- ENGINE ----------------
EX0, EX1, EY0, EY1, EZ0, EZ1 = PT.ENGINE["box"]
CX = (EX0 + EX1) / 2 + 30          # cylinder axis station
HEAD_TOP = EY1                     # cam cover top; the fuel cell floor is 10 mm above the envelope
THROTTLE_BODY = (245.0, 440.0, 0.0)          # rear of the head, faces the airbox (fuel cell sits over the head, so no intake up there)
INJECTOR = (245.0, 462.0, 0.0)
COIL = (EX1 - 20, 440.0, 0.0)                # stick coil in the head's front face (toward the firewall)
HEADER_PTS = [(EX1 - 70, 425.0, 30.0), (EX1 - 20, 400.0, 80.0), (EX1 - 10, 320.0, 150.0), (EX1 - 30, 290.0, 150.0),
              (-40.0, 340.0, 130.0)]        # down the right side of the head, back along the right of the case to the muffler
MUFFLER = ((-40.0, 360.0, 120.0), (-240.0, 360.0, 120.0), 42.0)   # right rear, above the spool, inboard of the toe link
STARTER = ((230.0, 190.0, -150.0), (330.0, 190.0, -150.0), 28.0)  # left, below the countershaft
OIL_FILTER = ((EX1, 200.0, 60.0), (EX1 + 22, 200.0, 60.0), 32.0)
AIRBOX = (EX0 - 20, EX0 + 65, 400.0, 520.0, -90.0, 90.0)

def engine_parts():
    """[(name, solid, contains)] - the engine as separate files (case, covers, cylinder, head, intake, exhaust...)."""
    cs = PT.ENGINE["countershaft"]
    out = []
    # crankcase: lower (crank) and upper (gearbox) halves with a parting line, sump underneath
    lower = rbox(EX0 + 20, EX1 - 20, EY0 + 10, 270, -120, 120, 22)
    sump = rbox(EX0 + 60, EX1 - 60, EY0, EY0 + 12, -90, 90, 6)
    for x in range(int(EX0) + 70, int(EX1) - 60, 40):     # sump cooling ribs
        sump = sump.fuse(box(x, x + 4, EY0 - 4, EY0 + 2, -80, 80))
    upper = rbox(EX0 + 30, EX1 - 10, 272, 330, -110, 110, 14)
    cs_boss = cyl_z(cs[0], cs[1], -172, -100, 24)
    out.append(("engine_crankcase", fuse(lower, sump, upper, cs_boss), "cast aluminium crankcase, lower (crank) and upper (gearbox) halves, sump with ribs, countershaft boss"))
    # covers: clutch (right) with ribs, stator/ignition (left), countershaft sprocket guard
    clutch = cyl_z(EX0 + 130, 235, 120, 146, 98)
    for r in (40, 62, 84):
        clutch = clutch.fuse(ring(EX0 + 130, 235, 146, 150, r + 3, r - 3))
    for i in range(6):
        a = 2 * math.pi * i / 6
        clutch = clutch.fuse(cyl_z(EX0 + 130 + 88 * math.cos(a), 235 + 88 * math.sin(a), 146, 152, 5))   # cover bolts
    out.append(("engine_clutch_cover", clutch, "right-side clutch cover, ribbed, 6 bolts"))
    stator = cyl_z(EX1 - 90, 230, -140, -120, 80).fuse(cyl_z(EX1 - 90, 230, -150, -140, 40))
    out.append(("engine_stator_cover", stator, "left-side stator / ignition cover with timing plug"))
    # cylinder with square fins, head, cam cover, plug + stick coil
    barrel = cq.Solid.makeCylinder(52, 72, V(CX, 330, 0), V(0, 1, 0))
    fins = [rbox(CX - 75, CX + 75, 336 + 9 * i, 339 + 9 * i, -75, 75, 22) for i in range(8)]
    out.append(("engine_cylinder", fuse(barrel, *fins), "finned cylinder barrel (air/oil cooled), 8 square fins"))
    head = rbox(CX - 70, CX + 62, 400, 448, -72, 72, 10)
    head_fins = [rbox(CX - 76, CX + 68, 404 + 11 * i, 407 + 11 * i, -78, 78, 12) for i in range(3)]
    cam = rbox(CX - 52, CX + 44, 448, HEAD_TOP, -56, 56, 8)
    filler = cyl((CX - 30, HEAD_TOP, 30), (CX - 30, HEAD_TOP + 6, 30), 18)   # oil filler cap (stays under the fuel cell floor)
    out.append(("engine_head_and_cam_cover", fuse(head, *head_fins, cam, filler), "cylinder head with fins, cam cover and oil filler cap"))
    coil = fuse(cyl(add3(COIL, (1, 0, 0), -10), add3(COIL, (1, 0, 0), 45), 12), cyl(add3(COIL, (1, 0, 0), 45), add3(COIL, (1, 0, 0), 60), 16))
    out.append(("engine_spark_plug_coil", coil, "stick coil on the spark plug, front face of the head (the coil lead runs to the ECU)"))
    # intake: rubber boot -> throttle body with injector -> airbox with filter snorkel
    tb = THROTTLE_BODY
    boot = cyl((CX - 70, 435, 0), (tb[0] + 22, 438, 0), 26)
    body = cyl((tb[0] + 22, tb[1], tb[2]), (tb[0] - 22, tb[1], tb[2]), 24)
    butterfly_shaft = cyl((tb[0], tb[1], -34), (tb[0], tb[1], 34), 4)
    tps = cyl((tb[0], tb[1], 34), (tb[0], tb[1], 44), 14)                   # throttle position sensor
    cable_drum = cyl((tb[0], tb[1], -34), (tb[0], tb[1], -40), 22)         # throttle cable drum (cable from the pedal)
    inj = cyl(INJECTOR, add3(INJECTOR, (0, 1, 0), 26), 7).fuse(cyl(add3(INJECTOR, (0, 1, 0), 26), add3(INJECTOR, (0, 1, 0), 34), 10))
    out.append(("engine_throttle_body_and_injector", fuse(boot, body, butterfly_shaft, tps, cable_drum, inj), "38 mm throttle body with cable drum, TPS and fuel injector, rubber boot to the head"))
    ab = AIRBOX
    airbox = rbox(*ab, 16).cut(rbox(ab[0] + 4, ab[1] - 4, ab[2] + 4, ab[3] - 4, ab[4] + 4, ab[5] + 4 - 8, 12))   # hollow shell (restrictor side wall)
    airbox = airbox.fuse(cyl((ab[1] - 6, 440, 0), (tb[0] - 22, 440, 0), 24))      # outlet to the throttle body
    snorkel = cyl((ab[0] + 30, ab[3] - 5, 0), (ab[0] + 30, ab[3] + 30, 0), 20)
    snorkel = snorkel.fuse(cyl((ab[0] + 30, ab[3] + 30, 0), (ab[0] + 30, ab[3] + 32, 0), 24).cut(cyl((ab[0] + 30, ab[3] + 28, 0), (ab[0] + 30, ab[3] + 40, 0), 16)))
    out.append(("engine_airbox_with_20mm_restrictor", fuse(airbox, snorkel), "airbox behind the head with the 20 mm restrictor snorkel (IC.2.3) and filter"))
    # exhaust: header down the right side, muffler at the right rear, tailpipe out the back
    header = route(HEADER_PTS, 19)
    flange = cyl(add3(HEADER_PTS[0], (1, 0, 0), -6), add3(HEADER_PTS[0], (1, 0, 0), 2), 34)
    out.append(("engine_exhaust_header", fuse(header, flange), "38 mm stainless header, head front face down the right side of the engine to the muffler"))
    (a, b, r) = MUFFLER
    muf = cyl(a, b, r).fuse(cyl(add3(a, (1, 0, 0), 8), add3(a, (1, 0, 0), -8), r + 3)).fuse(cyl(add3(b, (1, 0, 0), 8), add3(b, (1, 0, 0), -8), r + 3))
    muf = muf.fuse(cyl(b, add3(b, (1, 0, 0), -60), 15)).fuse(cyl(a, HEADER_PTS[-1], 19))
    for i in range(3):    # mounting straps
        x = a[0] - 40 - 60 * i; muf = muf.fuse(ring(x, a[1], a[2] - 2, a[2] + 2, r + 5, r + 1).rotate(V(x, a[1], a[2]), V(x + 1, a[1], a[2]), 0))
    out.append(("engine_muffler", muf, "muffler on the right rear (T.5.8 noise), tailpipe rearward, 3 band clamps"))
    # oil filter, starter motor
    of = cyl(*OIL_FILTER)
    out.append(("engine_oil_filter", of, "spin-on oil filter on the front face of the case"))
    (a, b, r) = STARTER
    st = cyl(a, b, r).fuse(cyl(add3(a, (0, 1, 0), 30), add3(b, (0, 1, 0), 30), 16))        # motor + solenoid on top
    st = st.fuse(cyl(add3(b, (0, 1, 0), 40), add3(b, (0, 1, 0), 54), 5))                    # battery cable stud
    out.append(("engine_starter_motor", st, "12 V starter motor with solenoid on top, left side below the countershaft (main cable from the master switch)"))
    # gear lever + rear brake-side nothing (rear brake is on the pedal); kick lever omitted
    lever = fuse(cyl((EX0 + 80, 300, -110), (EX0 + 80, 300, -175), 8), cyl((EX0 + 80, 300, -175), (EX0 + 200, 330, -175), 6), sphere((EX0 + 200, 330, -175), 10))
    out.append(("engine_gear_lever", lever, "gear shift shaft and lever, left side (hand-shift linkage to the cockpit to be added)"))
    # engine mounts to the frame nodes em_fb / em_ft / em_rb (both sides)
    for sg, side in ((1, "R"), (-1, "L")):
        z0, z1 = sorted((sg * 100, sg * 142))   # overlaps the case side so the brackets read as bolted to it
        fb, ft, rb = N["em_fb"], N["em_ft"], N["em_rb"]
        mounts = fuse(rbox(EX1 - 20, fb[0] - 12, fb[1] - 13, fb[1] + 13, z0, z1, 4),           # front-bottom, to the main hoop base cross
                      rbox(EX1 - 30, ft[0] - 12, 326, ft[1] + 13, z0, z1, 4),                    # front-top, up to the mid cross
                      rbox(rb[0] - 30, rb[0] + 30, rb[1] - 13, EY0 + 14, z0, z1, 4))             # rear-bottom, to the rear-ring bottom cross
        for p in (fb, ft, rb):
            mounts = mounts.cut(cyl((p[0], p[1], z0 - 1), (p[0], p[1], z1 + 1), 5))
        out.append((f"engine_mount_brackets_{side}", mounts, f"3 engine mount brackets, {'right' if sg > 0 else 'left'} side, bolted through the frame cross tubes at em_fb / em_ft / em_rb"))
    return out

# ---------------- COMPONENTS THAT WERE BOXES ----------------
def seat_shell():
    """Curved shell, 4 mm: back = 100 deg cylinder sector wrapped round the driver, extruded along the seat-back line;
    base = shallow cylinder trough along X; hip bolsters; shoulder-belt slots."""
    hx, y0 = m.HIP[0], m.SEAT_Y0
    x_front = m.X_PEDAL - 450
    a, b = (hx - 65, y0 + 60, 0.0), (m.SHOULDER[0] - 65, m.SHOULDER[1] + 40, 0.0)
    d = unit(sub(b, a)); L = norm(sub(b, a))
    def sector(radius, t, half_deg, n=24):   # 2D annulus sector, open toward -x (rearward), in the plane's local coords
        ang = [math.radians(-half_deg + 2 * half_deg * i / n) for i in range(n + 1)]
        outer = [(radius * math.cos(q) - radius, radius * math.sin(q)) for q in ang]
        inner = [((radius - t) * math.cos(q) - radius, (radius - t) * math.sin(q)) for q in reversed(ang)]
        return outer + inner
    pl = cq.Plane(origin=V(*a), xDir=V(-d[1], d[0], 0), normal=V(*d))        # local x = rearward, so the sector edges wrap forward (perpendicular to the back), local y = Z
    back = cq.Workplane(pl).polyline(sector(300.0, 4.0, 42.0)).close().extrude(L).val()
    pl2 = cq.Plane(origin=V(hx - 40, y0 + 4, 0), xDir=V(0, -1, 0), normal=V(1, 0, 0))   # base trough: local x = down, so the edges curve up
    base = cq.Workplane(pl2).polyline(sector(400.0, 4.0, 31.0)).close().extrude(x_front - (hx - 40)).val()
    wings = [rbox(hx - 110, hx - 20, y0 + 80, y0 + 380, s * 200 - 8, s * 200 + 8, 6) for s in (-1, 1)]
    holes = fuse(*[cyl((hx - 120, m.SHOULDER[1] - 20, s * m.BELT_Z), (hx + 40, m.SHOULDER[1] - 20, s * m.BELT_Z), 25) for s in (-1, 1)])
    return fuse(back, base, *wings).cut(holes)

def head_restraint():
    hy = m.HEAD[1]; x0 = m.X_MAIN + 13
    pad = rbox(x0, x0 + 50, hy - 130, hy + 130, -85, 85, 22)             # padding (>= 38 mm foam)
    plate = box(x0 + 50, x0 + 54, hy - 110, hy + 110, -70, 70)
    arms = [cyl((x0 + 52, hy - 60, z), (m.X_MAIN, hy - 60, z), 6) for z in (-50, 50)]     # to the main hoop
    return fuse(pad, plate, *arms)

def pedal_box():
    g = BR.geometry(); (xp, yp) = g["piv"]; yb = g["y_base"]
    base = rbox(m.PB_X[0] - 20, m.PB_X[1] + 10, yb - 6, yb, -m.PB_Z - 20, m.PB_Z + 20, 3)
    for x in (m.PB_X[0], m.PB_X[1]):     # bolt holes over the two floor cross tubes
        for z in (-m.PB_Z, m.PB_Z):
            base = base.cut(cyl((x, yb - 7, z), (x, yb + 1, z), 4.5))
    cheeks = [rbox(xp - 30, xp + 30, yb, yp + 25, z - 3, z + 3, 8) for z in (BR.BRAKE_Z - 24, BR.BRAKE_Z + 24, BR.THROTTLE_Z - 24, BR.THROTTLE_Z + 24)]
    pivot = cyl((xp, yp, BR.BRAKE_Z - 30), (xp, yp, BR.THROTTLE_Z + 30), 6)
    heel = box(xp - 60, xp - 40, yb, yb + 30, -m.PB_Z - 20, m.PB_Z + 20)
    return fuse(base, *cheeks, pivot, heel)

def fuel_cell():
    x0, x1 = m.X_MAIN - 213, m.X_MAIN - 43; xc = (x0 + x1) / 2
    tank = rbox(x0, x1, 480, 700, -140, 140, 14)
    neck = cyl((xc, 700, 0), (xc, 740, 0), 22).fuse(cyl((xc, 740, 0), (xc, 752, 0), 30))     # filler neck + cap
    breather = cyl((xc + 60, 700, 60), (xc + 60, 725, 60), 5)
    p = SD.LOC["fuel pump"]
    pump = cyl((p[0], 480, 0), (p[0], 545, 0), 20).fuse(cyl((p[0], 478, 0), (p[0], 480, 0), 34))   # in-tank pump on its flange
    outlet = cyl((p[0], 480, -30), (p[0], 468, -30), 5)                                          # fuel outlet fitting
    return fuse(tank, neck, breather, pump, outlet)

def firewall():
    x0, x1 = m.X_MAIN - 40, m.X_MAIN - 13
    sheet = box(x0 + 10, x0 + 12, m.Y_LOW, 700, -m.Z_COCKPIT, m.Z_COCKPIT)
    flanges = [box(x0 - 8, x0 + 12, 698, 700, -m.Z_COCKPIT, m.Z_COCKPIT), box(x0 - 8, x0 + 12, m.Y_LOW, m.Y_LOW + 2, -m.Z_COCKPIT, m.Z_COCKPIT),
               box(x0 - 8, x0 + 12, m.Y_LOW, 700, m.Z_COCKPIT - 2, m.Z_COCKPIT), box(x0 - 8, x0 + 12, m.Y_LOW, 700, -m.Z_COCKPIT, -m.Z_COCKPIT + 2)]
    fw = fuse(sheet, *flanges)
    for z in (-100, 100):     # grommets for the harness / throttle cable / fuel line
        fw = fw.cut(cyl((x0, 420, z), (x0 + 20, 420, z), 14))
    return fw

def dash_panel():
    x = m.X_FRONT - 35; e = SD.LOC["e-stop"]
    panel = rbox(x, x + 3, 470, 560, -160, 160, 6).cut(cyl((x - 1, e[1], e[2]), (x + 4, e[1], e[2]), 22))
    start = cyl((x, 515, -120), (x + 12, 515, -120), 9).fuse(cyl((x + 12, 515, -120), (x + 16, 515, -120), 12))   # start button
    drs = cyl((x, 515, -70), (x + 12, 515, -70), 7).fuse(cyl((x + 12, 515, -70), (x + 16, 515, -70), 10))          # DRS button (momentary)
    return fuse(panel, start, drs)

def master_switch():
    x, y, z = SD.LOC["primary master switch"]
    body = cyl_z(x, y, z - 20, z + 20, 30)
    plate = rbox(x - 45, x + 45, y - 45, y + 45, z - 22, z - 20, 6)
    handle = fuse(cyl_z(x, y, z + 20, z + 34, 12), rbox(x - 32, x + 32, y - 6, y + 6, z + 34, z + 46, 3))   # red key handle
    studs = [cyl((x + dx, y - 30, z), (x + dx, y - 48, z), 6) for dx in (-15, 15)]
    return fuse(body, plate, handle, *studs)

def e_stop():
    x, y, z = SD.LOC["e-stop"]; d = (-1, 0, 0)     # mounted in the dash, button facing the driver (rearward)
    body = cyl(add3((x, y, z), d, -30), (x, y, z), 20)
    collar = cyl((x, y, z), add3((x, y, z), d, 6), 24)
    button = cyl(add3((x, y, z), d, 6), add3((x, y, z), d, 22), SD.ESTOP_DIA / 2)
    return fuse(body, collar, button)

def inertia_switch():
    x, y, z = SD.LOC["inertia switch"]
    body = rbox(x - 25, x + 25, y - 20, y + 20, z - 20, z + 20, 4)
    reset = cyl((x, y + 20, z), (x, y + 34, z), 9)
    return fuse(body, reset, box(x - 30, x + 30, y - 22, y - 20, z - 25, z + 25))

def kill_relay():
    x, y, z = SD.LOC["kill relay"]
    body = rbox(x - 15, x + 15, y - 12, y + 18, z - 15, z + 15, 2)
    blades = [box(x + dx - 1, x + dx + 1, y - 20, y - 12, z + dz - 3, z + dz + 3) for dx, dz in ((-8, -8), (8, -8), (-8, 8), (8, 8), (0, 0))]
    return fuse(body, *blades)

def brake_light():
    x, y, z = SD.LOC["brake light"]; L = SD.BRAKE_LIGHT["led_line_mm"]
    housing = rbox(x - 8, x + 8, y - 20, y + 20, z - L / 2 - 8, z + L / 2 + 8, 4)
    lens = box(x - 12, x - 8, y - 8, y + 8, z - L / 2, z + L / 2)      # LED line facing rearward
    tab = box(x, x + 30, y - 4, y + 4, z - 10, z + 10)
    return fuse(housing, lens, tab)

def battery():
    x, y, z = SD.LOC["battery"]; w, h, d = 150, 90, 90
    case = rbox(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2, 4)
    terms = [cyl((x + s * 50, y + h / 2, z), (x + s * 50, y + h / 2 + 14, z), 7) for s in (-1, 1)]
    strap = box(x - 10, x + 10, y - h / 2 - 6, y + h / 2 + 3, z - d / 2 - 6, z + d / 2 + 6).cut(box(x - 11, x + 11, y - h / 2 - 1, y + h / 2, z - d / 2 - 1, z + d / 2 + 1))
    tray = box(x - w / 2 - 6, x + w / 2 + 6, y - h / 2 - 6, y - h / 2, z - d / 2 - 6, z + d / 2 + 6)
    return fuse(case, *terms, strap, tray)

def bots():
    x, y, z = SD.LOC["bots"]
    body = rbox(x - 14, x + 14, y - 10, y + 10, z - 8, z + 8, 2)
    lever = box(x - 14, x + 26, y + 10, y + 12, z - 4, z + 4).fuse(sphere((x + 26, y + 11, z), 4))
    return fuse(body, lever)

def ecu():
    x, y, z = SD.LOC["ignition/ECU"]
    body = rbox(x - 60, x + 60, y - 15, y + 15, z - 40, z + 40, 4)
    conn = rbox(x - 45, x + 45, y - 15, y + 5, z + 40, z + 56, 2)
    return fuse(body, conn)

def fan():
    x, y, z = SD.LOC["fan"]; r = 80
    shroud = ring(x, y, z - 15, z + 15, r + 8, r)
    hub = cyl_z(x, y, z - 10, z + 10, 22)
    blades = [box(x + 20, x + r - 4, y - 12, y + 12, z - 2, z + 2).rotate(V(x, y, z), V(x, y, z + 1), 360 * i / 5).rotate(
        V(x, y, z), V(x + math.cos(2 * math.pi * i / 5), y + math.sin(2 * math.pi * i / 5), z), 30) for i in range(5)]
    motor = cyl_z(x, y, z + 10, z + 40, 25)
    return fuse(shroud, hub, *blades, motor)

def drs_servo(pivot):
    x, y = pivot[0], pivot[1] - 48
    body = rbox(x - 30, x + 30, y - 20, y + 20, -30, 30, 4)
    shaft = cyl((x, y, 30), (x, y, 44), 5)
    arm = box(x - 4, x + 4, y, pivot[1] - 6, 40, 44).fuse(sphere((x, pivot[1] - 6, 42), 5))
    lugs = [box(x - 36, x + 36, y - 24, y - 20, z - 5, z + 5) for z in (-22, 22)]
    return fuse(body, shaft, arm, *lugs)

# ---------------- ROUTING ----------------
def _frame_path(*names):
    return [N[n] if not n.endswith("'") else m.mir(N[n[:-1]]) for n in names]
def _off(p, dy=0.0, dz=0.0, dx=0.0): return (p[0] + dx, p[1] + dy, p[2] + dz)

def caliper_inlet(ax, sg):
    g = U.geom(ax); return (g["x"] - 40, g["r"] + U.ROTOR_OD / 2 + 8, sg * (g["rotor"] + 18))

def routes():
    """[(name, colour key, radius, points, contains)] - every run in the car, rough path along the frame."""
    g = BR.geometry(); (xb, yb) = g["bar"]; zb = BR.BRAKE_Z
    mc_f, mc_r = (g["mc_front"], yb, zb - BR.BAR["e"]), (g["mc_front"], yb, zb + BR.BAR["e"])
    ring_bot, bh_bot = N["ring_bot"], N["bh_bot"]
    R = []
    # brake, front circuit: MC -> tee under the bulkhead -> along the lower FBH supports -> flexible hose to each caliper
    tee_f = (bh_bot[0] - 40, bh_bot[1] + 20, 0.0)
    R.append(("brake_line_front_MC_to_tee", "hydraulic", 2.4, [mc_f, _off(mc_f, dx=30), (tee_f[0], mc_f[1], mc_f[2]), tee_f],
              "3/16 in hard brake line, front master cylinder to the front tee under the bulkhead"))
    for sg, side in ((1, "R"), (-1, "L")):
        pts = [tee_f, (bh_bot[0] - 40, bh_bot[1] + 20, sg * (bh_bot[2] - 20)), (ring_bot[0], ring_bot[1] + 20, sg * (ring_bot[2] - 20)),
               (ring_bot[0], 200, sg * 300), caliper_inlet("front", sg)]
        R.append((f"brake_line_front_{side}", "hydraulic", 2.4, pts, f"front {'right' if sg > 0 else 'left'} brake line: hard line along the lower bulkhead support, braided flexible hose over the wishbone to the caliper"))
    # brake, rear circuit: MC -> floor -> along the left lower side-impact rail -> rear tee -> up the spool posts -> calipers
    fh_bot_l, mh_bot_l, rr_bot_l, sp_bot_l = m.mir(N["fh_bot"]), m.mir(N["mh_bot"]), m.mir(N["rr_bot"]), m.mir(N["sp_bot"])
    lap_l, as_l = m.mir(N["lap"]), m.mir(N["as"])
    rail = lambda p: (p[0], p[1] + 16, p[2] + 16)      # sits on top-inside of the lower rail
    rear_tee = (sp_bot_l[0], sp_bot_l[1] + 40, 0.0)
    pts = [mc_r, _off(mc_r, dx=30), (mc_r[0] + 30, 110, mc_r[2]), (m.mir(ring_bot)[0], 110, m.mir(ring_bot)[2] + 16), rail(fh_bot_l), rail(as_l), rail(lap_l), rail(mh_bot_l), rail(rr_bot_l), rail(sp_bot_l), rear_tee]
    R.append(("brake_line_rear_MC_to_tee", "hydraulic", 2.4, pts, "3/16 in hard brake line, rear master cylinder along the left lower side-impact rail to the rear tee at the spool posts (brake-light pressure switch at the MC end)"))
    for sg, side in ((1, "R"), (-1, "L")):
        sp = N["sp_mid"]
        pts = [rear_tee, (sp[0], rear_tee[1], sg * (sp[2] - 20)), (sp[0], sp[1] + 60, sg * (sp[2] - 20)), (sp[0] - 60, 330, sg * 330), caliper_inlet("rear", sg)]
        R.append((f"brake_line_rear_{side}", "hydraulic", 2.4, pts, f"rear {'right' if sg > 0 else 'left'} brake line: up the spool carrier post, flexible hose along the upper wishbone to the caliper"))
    # throttle cable: pedal -> along the right lower rail -> through the firewall grommet -> throttle body drum
    (xa, ya) = g["pad"]; tz = BR.THROTTLE_Z
    fh_bot, mh_bot = N["fh_bot"], N["mh_bot"]
    pts = [(xa - 10, ya - 30, tz), (xa - 60, 130, tz), (ring_bot[0], 110, ring_bot[2] - 16), (fh_bot[0], fh_bot[1] + 16, fh_bot[2] - 16), (mh_bot[0] + 20, mh_bot[1] + 16, mh_bot[2] - 16),
           (m.X_MAIN - 30, 420, 100), (m.X_MAIN - 60, 440, 60), (THROTTLE_BODY[0] + 30, THROTTLE_BODY[1] + 20, -46), (THROTTLE_BODY[0], THROTTLE_BODY[1] + 22, -38)]
    R.append(("throttle_cable", "hydraulic", 3.5, pts, "mechanical throttle cable (IC.3.3), pedal to the throttle-body drum, along the right lower rail and through the right firewall grommet"))
    # fuel line: in-tank pump outlet -> down the back of the firewall -> injector
    p = SD.LOC["fuel pump"]
    pts = [(p[0], 468, -30), (p[0] - 20, 455, -40), (INJECTOR[0] + 40, INJECTOR[1] + 34, -30), add3(INJECTOR, (0, 1, 0), 34)]
    R.append(("fuel_line", "fuel", 4.0, pts, "8 mm fuel hose, in-tank pump outlet to the injector (fuel cell sits above the engine; return-less)"))
    # 12 V harness: from shutdown.WIRES, routed along the frame
    L = SD.LOC
    mh_r = lambda y: (m.X_MAIN + 10, y, m.Z_COCKPIT + 14)             # up the inside of the main hoop right leg
    sis_r = lambda x: (x, m.Y_SIS + 14, m.Z_COCKPIT - 14)             # along the upper side-impact tube, right
    H = {
        ("battery", "primary master switch"): [L["battery"], (L["battery"][0], L["battery"][1] + 60, L["battery"][2]), mh_r(L["battery"][1] + 60), mh_r(L["primary master switch"][1]), L["primary master switch"]],
        ("primary master switch", "e-stop"): [L["primary master switch"], mh_r(m.Y_SIS + 14), sis_r(m.X_MAIN + 10), sis_r(m.X_FRONT), (m.X_FRONT - 20, 480, 200), L["e-stop"]],
        ("e-stop", "bots"): [L["e-stop"], (m.X_FRONT - 20, 480, -200), (m.X_FRONT, 110, -m.Z_COCKPIT + 16), (m.X_RING, 110, -220), (L["bots"][0], 110, L["bots"][2]), L["bots"]],
        ("bots", "inertia switch"): [L["bots"], (L["bots"][0], 95, 0.0), (L["inertia switch"][0], 95, 0.0), L["inertia switch"]],
        ("inertia switch", "kill relay"): [L["inertia switch"], (L["inertia switch"][0] - 40, 95, 60), (L["kill relay"][0], 95, L["kill relay"][2]), L["kill relay"]],
        ("primary master switch", "kill relay"): [L["primary master switch"], mh_r(400), (m.X_MAIN + 40, 300, 200), L["kill relay"]],
        ("kill relay", "fuel pump"): [L["kill relay"], (m.X_MAIN - 20, 200, 100), (m.X_MAIN - 60, 420, 100), (m.X_MAIN - 100, 470, 40), (L["fuel pump"][0], 478, 20)],
        ("kill relay", "ignition/ECU"): [L["kill relay"], (m.X_MAIN - 20, 200, 100), (m.X_MAIN - 60, 420, 100), (m.X_MAIN - 100, 450, 150), L["ignition/ECU"]],
        ("ignition/ECU", "coil"): [L["ignition/ECU"], (L["ignition/ECU"][0] + 60, 450, 120), (COIL[0] + 55, COIL[1], 40), add3(COIL, (1, 0, 0), 55)],
        ("primary master switch", "starter"): [L["primary master switch"], mh_r(300), (m.X_MAIN + 10, 150, 0.0), (m.X_MAIN + 10, 150, -150), (STARTER[1][0], STARTER[1][1] + 50, STARTER[1][2])],
        ("primary master switch", "fan"): [L["primary master switch"], mh_r(400), L["fan"]],
        ("primary master switch", "brake light"): [L["primary master switch"], mh_r(m.Y_SIS + 14), (m.X_MAIN + 10, L["brake light"][1], 150), L["brake light"]],
        ("primary master switch", "DRS servo"): [L["primary master switch"], mh_r(1000), (m.X_MAIN + 10, m.H_MAIN - 20, m.Z_MAIN_TOP), (N["r_top"][0], N["r_top"][1] + 20, N["r_top"][2] - 16), (L["DRS servo"][0] + 40, L["DRS servo"][1] - 60, 30), L["DRS servo"]],
        ("dash DRS button", "ignition/ECU"): [(m.X_FRONT - 20, 515, -70), (m.X_FRONT - 20, 480, -200), sis_r(m.X_FRONT)[:2] + (-(m.Z_COCKPIT - 14),), (m.X_MAIN + 10, m.Y_SIS + 14, -(m.Z_COCKPIT - 14)), (m.X_MAIN - 60, 420, -100), L["ignition/ECU"][:2] + (-L["ignition/ECU"][2],), L["ignition/ECU"]],
        ("battery", "chassis ground"): [L["battery"], (L["battery"][0], L["battery"][1] - 60, L["battery"][2]), (N["em_fb"][0], N["em_fb"][1] + 14, N["em_fb"][2])],
    }
    import aero
    if not aero.FITTED:   # no wing on the base mule: no DRS servo wire or button lead
        H = {k: v for k, v in H.items() if "DRS" not in k[0] and "DRS" not in k[1]}
    gauge = {tuple(w[:2]): w[2] for w in SD.WIRES}
    for (a, b), pts in H.items():
        gauge_awg = gauge.get((a, b), 18); r = {4: 6.0, 12: 3.5, 14: 3.0, 16: 2.6}.get(gauge_awg, 2.2)
        what = f"{gauge_awg} AWG" if (a, b) in gauge else "signal / ground"
        R.append((f"wire_{a}_to_{b}".replace(" ", "_").replace("/", "-"), "wiring", r, pts,
                  f"{what} wire, {a} to {b}, routed along the frame (shutdown.py netlist)"))
    return R
