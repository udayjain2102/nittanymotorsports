"""NM26 FSAE-lite mule: parametric tube frame + packaging, with rule checks.

Axes (same as NM26_FSAE_Concept.step): X forward (rear axle at 0), Y up (ground at 0),
Z lateral (+Z = driver's right). Units: mm.

Run:  python mule.py            -> asserts rules, writes cad/simple/NM26_Mule.step, views/simple_*.svg, fab/tube_order_list.csv
Tune the PARAMETERS block; everything else is derived from it.
"""
import math, csv, pathlib
import cadquery as cq

# ---------------- PARAMETERS ----------------
WHEELBASE   = 1750
TRACK_F     = 1220
TRACK_R     = 1220   # widened from 1180 so the tilt test (60 deg) keeps ~1 deg margin with the rear wing
TIRE_OD     = 521      # 20.5x7.0-13
TIRE_W      = 180
TIRE_R_LOADED = TIRE_OD / 2 - 6   # rolling radius at static load (~700 N / 120 N/mm): speed and gearing

Y_LOW       = 73       # lower side-impact centerline -> bottom at 60 mm (V.1.4.2: <=90, should <=75)
Y_SIS       = 367      # upper side-impact centerline -> top edge 320 above lower bottom (F.6.4.4: 290-345)
Z_COCKPIT   = 292      # half-width of side-impact structure (tube centerline); T.1.1 template (550 wide) needs >= 288 (cockpit.py)

X_MAIN      = 520      # main hoop station (leaves ~500 mm for engine + chain ahead of rear axle)
H_MAIN      = 1280     # main hoop top (centerline)
Z_MAIN_TOP  = 140
H_FRONT     = 850      # front hoop top (centerline)
Z_FRONT_TOP = 180
X_REAR      = -300     # rear bulkhead station
Y_REAR_TOP  = 328     # C2: upper rear pickups on rr_top/r_top, mean height 340 (suspension.py)
Z_REAR      = 200
X_RING      = WHEELBASE - 120  # front suspension ring (A-arm rear pickups)
X_RR        = 200      # rear suspension ring (A-arm front pickups)

Z_BH        = 180      # front bulkhead half-width (centerline)
Y_BH_BOT    = 100
Y_BH_TOP    = 410

SEAT_BACK_DEG = 20     # from vertical; <=30 => "upright" (T.2.1.d)
HIP_Y       = 205      # 95th template hip-circle centre height
PEDAL_BOX_LEN = 165    # pedal face -> front of master cylinders (brakes.py checks the real stack-up)
WHEEL_DIA   = 270      # steering wheel
SHOULDER_BAR_Y = 620
BELT_Z = 100              # shoulder belt tabs at +/-BELT_Z on the shoulder bar (T.2.6.2 spacing 175-235)
SEAT_Y0 = 90
LAP_ANGLE = 55.0         # lap belt side-view angle target (T.2.5.4: 45-65 deg upright)

# Tube sizes (OD, wall) - F.3.4.1
SIZES = {"J": (38.1, 2.41), "H": (31.75, 2.41), "A": (25.4, 2.41), "B": (25.4, 1.65), "C": (25.4, 1.24)}   # H = hoops 1.25x.095 (exceeds size A), 1.0x.095, 1.0x.065, 1.0x.049
RULE_MIN = {"J": (11320, 173), "H": (11320, 173), "A": (11320, 173), "B": (8509, 114), "C": (6695, 91)}     # I mm^4, area mm^2
STEEL_DENSITY = 7.85e-6  # kg/mm^3

# ---------------- DRIVER TEMPLATE (F.5.6.5/6) ----------------
th = math.radians(SEAT_BACK_DEG)
up = (-math.sin(th), math.cos(th))                     # along seat back, leaning rearward
# head restraint sits just ahead of the main hoop; head circle <=25 mm from it
HEAD_X = X_MAIN + SIZES["J"][0] / 2 + 53.65 + 150     # J main hoop face + 53.65 mm restraint plate and padding + head radius
                                                       # (same head position as before; the old "12.7 + 60" took the hoop as 1 in)
HIP = (HEAD_X - up[0] * 770, HIP_Y)                    # 490 + 280 along the back line
SHOULDER = (HIP[0] + up[0] * 490, HIP[1] + up[1] * 490)
HEAD = (SHOULDER[0] + up[0] * 280, SHOULDER[1] + up[1] * 280)
X_PEDAL = HIP[0] + 915                                  # rearmost pedal face, pedals fully forward
X_FRONT = round(HIP[0] + 315)                           # front hoop just ahead of the hands
WHEEL_C = (HIP[0] + 220, 585)                           # steering wheel centre (X, Y)
X_BH = math.ceil((X_PEDAL + PEDAL_BOX_LEN + 25 + 12.7 + 1.5) / 10) * 10  # F.8.6.3 25 mm to AIP
# steering rack low under the shins; the T.1.2 template (350 tall) passes over it, between the front ring verticals
# (the ring has no top cross tube for that reason; cockpit.py checks it)
RACK_R = 20
RACK = (WHEELBASE - 80, 180, 190)                      # centre X, Y, half-length to the tie-rod pivots

X_LAP = HIP[0] - (HIP[1] - Y_LOW) / math.tan(math.radians(LAP_ANGLE))   # lap tabs on the lower SIS tube, under the hip
X_AS = HIP[0] + 120                                                     # anti-sub mount: under the groin (harness.py checks)

# ---------------- FRAME NODES (right side; mirrored) ----------------
N = {
    "bh_bot": (X_BH, Y_BH_BOT, Z_BH), "bh_top": (X_BH, Y_BH_TOP, Z_BH),
    "ring_bot": (X_RING, 90, 220), "ring_top": (X_RING, 395, 220),
    "fh_bot": (X_FRONT, Y_LOW, Z_COCKPIT), "fh_sis": (X_FRONT, Y_SIS, Z_COCKPIT),
    "fh_sh": None, "fh_top": (X_FRONT, H_FRONT, Z_FRONT_TOP),
    "mh_bot": (X_MAIN, Y_LOW, Z_COCKPIT), "mh_sis": (X_MAIN, Y_SIS, Z_COCKPIT),
    "mh_bar": (X_MAIN, SHOULDER_BAR_Y, Z_COCKPIT), "mh_sh": None,
    "mh_top": (X_MAIN, H_MAIN, Z_MAIN_TOP),
    "r_bot": (X_REAR, 110, Z_REAR), "r_top": (X_REAR, Y_REAR_TOP, Z_REAR),
}
def _on(a, b, x):  # point on straight member a-b at station x (keeps rails straight)
    t = (x - N[a][0]) / (N[b][0] - N[a][0]); return tuple(p + t * (q - p) for p, q in zip(N[a], N[b]))
# F.5.2.3 (audit 1 Oct 2026): the upper FBH support bh_top -> ring_top -> fh_sis is one straight tube line, so ring_top
# sits ON it (was (X_RING, 395, 220): an 8.5 deg kink with no same-size in-plane support, the ring-top cross is barred by T.1.2)
N["ring_top"] = tuple(round(c, 1) for c in _on("bh_top", "fh_sis", X_RING))
N["rr_bot"], N["rr_top"] = _on("mh_bot", "r_bot", X_RR), _on("mh_sis", "r_top", X_RR)
Y_RLOW = 150.0   # rear lower rail height = rear lower pickup height (C2: pickups on rail nodes); rail kinks up at rr_bot
N["rr_bot"] = (X_RR, Y_RLOW, N["rr_bot"][2]); N["r_bot"] = (X_REAR, Y_RLOW, Z_REAR)
N["lap"], N["as"] = _on("mh_bot", "fh_bot", X_LAP), _on("mh_bot", "fh_bot", X_AS)   # harness nodes on the lower SIS
N["as_c"] = (X_AS, Y_LOW, 0.0)                                            # anti-sub tab, centre of the floor cross
N["lap_up"] = _on("fh_bot", "mh_sis", X_LAP)                             # lap-tab brace top, on the SIS diagonal
N["sb"] = (X_MAIN, SHOULDER_BAR_Y, BELT_Z)                                # shoulder belt tab on the shoulder bar
def _at_y(a, b, y):  # point on member a-b at height y
    t = (y - N[a][1]) / (N[b][1] - N[a][1]); return tuple(p + t * (q - p) for p, q in zip(N[a], N[b]))
# hoop "shoulder" nodes lie ON the straight upper legs, so each hoop is knee bend + two top corners
# (two bends 25 mm apart can't be bent on a 4" CLR die - fab.py checks the straights between bends)
N["mh_sh"] = _at_y("mh_bar", "mh_top", H_MAIN - 110)
N["fh_sh"] = _at_y("fh_sis", "fh_top", H_FRONT - 95)   # just below the top bend (tangent ~86 mm)
# upper A-arm inboard pickups: nodes part-way up the suspension-ring / bulkhead verticals
# rear pickups sit ON the main-hoop-brace support rail nodes (rr_bot/r_bot, rr_top/r_top): no rear posts in bending (C2)
PICKUP_Y = {"front": (140, 340)}  # (lower, upper) inboard pickup heights, from suspension.py grid search
for ax, (lo_, hi_) in PICKUP_Y.items():
    for pre in ("ring", "bh"):
        N[pre + "_lsus"], N[pre + "_sus"] = _at_y(pre + "_bot", pre + "_top", lo_), _at_y(pre + "_bot", pre + "_top", hi_)

# engine mounts (inboard, on cross tubes split at these nodes) and spool-carrier posts at the rear axle station
EM_Z = 130.0   # engine mounts on the cross tubes (100 with the 292 cockpit: launch FoS 1.06; 160: 1.13)
N["em_fb"] = (X_MAIN, Y_LOW, EM_Z)                          # engine bottom-front, on the main hoop base cross
N["em_ft"] = (X_MAIN, Y_SIS, EM_Z)                          # engine top-front, on the main hoop mid cross
N["em_rb"] = (X_RR, N["rr_bot"][1], EM_Z)                   # engine bottom-rear, on the rear-ring bottom cross
N["sp_bot"], N["sp_top"] = _on("rr_bot", "r_bot", 0.0), _on("rr_top", "r_top", 0.0)
N["sp_mid"] = N["sp_bot"]                                  # (C2) rear lower rail now crosses the post at its foot
N["sp_c"] = (0.0, TIRE_OD / 2, N["sp_mid"][2])              # spool bearing carrier, at axle height
# pedal box: base plate bolts to two floor cross tubes (rear under the pedal pivot, front under the master cylinders)
PB_X, PB_Z = (X_PEDAL + 25, X_PEDAL + 160), 70.0            # cross stations; bolt points at +/-PB_Z (brakes.py)
for i, x in enumerate(PB_X):
    N[f"pb{i}"] = _on("ring_bot", "bh_bot", x); N[f"pb{i}m"] = (x, N[f"pb{i}"][1], PB_Z)

# Double wishbone per axle: inboard pickups (frame nodes), ball-joint heights, ball-joint inset from
# wheel centre plane, and extra inboard lean of the upper ball joint (gives KPI).
SUSP = {
    "front": dict(inner_low=("ring_lsus", "bh_lsus"), inner_up=("ring_sus", "bh_sus"), lbj_y=143, ubj_y=380, inset=62, ubj_lean=40, caster_dx=19.0,
                  # steering arm behind the axle -> rack low under the shins (steering.py); pushrod -> rocker at ring top
                  steer=((-85, 190, 30), RACK, "ring_lsus"), pushrod=((0, 165, 45), "ring_top")),
    "rear":  dict(inner_low=("rr_bot", "r_bot"),     inner_up=("rr_top", "r_top"),    lbj_y=146, ubj_y=370, inset=65, ubj_lean=15,
                  # toe link aimed at the arms' instant centre (rear bump steer ~0) and pushrod->rocker at the braced rear bulkhead
                  steer=((-80, 323, 20), (X_REAR + 150, 300, 223), "r_top"), pushrod=((0, 165, 45), "r_top")),
}
SUSP_TUBE = (15.875, 0.89)   # A-arms, tie rods: 5/8" x 0.035" 4130 (loads.py checks buckling)
PUSHROD_TUBE = (19.05, 1.24)  # pushrods: 3/4" x 0.049" (5/8" rear buckled at FoS 1.9)

def susp_links(axle):
    """Right-side links: (name, upright point, chassis point, frame node taking the reaction)."""
    s = SUSP[axle]; x = WHEELBASE if axle == "front" else 0.0
    wz = (TRACK_F if axle == "front" else TRACK_R) / 2; zb = wz - s["inset"]
    lbj, ubj = (x, s["lbj_y"], zb), (x - s.get("caster_dx", 0.0), s["ubj_y"], zb - s["ubj_lean"])
    (so, si, sn), (ko, kn) = s["steer"], s["pushrod"]
    return ([(f"lower {n}", lbj, N[n], n) for n in s["inner_low"]] +
            [(f"upper {n}", ubj, N[n], n) for n in s["inner_up"]] +
            [("steer", (x + so[0], so[1], zb - so[2]), si, sn), ("pushrod", (x + ko[0], ko[1], zb - ko[2]), N[kn], kn)])
def mir(p): return (p[0], p[1], -p[2])
def node(name):  # "name" right side, "name'" left side
    return mir(N[name[:-1]]) if name.endswith("'") else N[name]

# (a, b, size, role). Each side member is mirrored automatically; "X:" = cross member (right->left).
SIDE = [
    # front hoop (size A) - modelled as straight segments between bend nodes (real part: bent, R>=76)
    ("fh_bot", "fh_sis", "H", "Front hoop"), ("fh_sis", "fh_sh", "H", "Front hoop"), ("fh_sh", "fh_top", "H", "Front hoop"),
    # main hoop (size A, single piece)
    ("mh_bot", "mh_sis", "J", "Main hoop"), ("mh_sis", "mh_bar", "J", "Main hoop"),
    ("mh_bar", "mh_sh", "J", "Main hoop"), ("mh_sh", "mh_top", "J", "Main hoop"),
    # side impact (B)
    ("fh_sis", "mh_sis", "H", "Upper side impact"),
    ("fh_bot", "as", "H", "Lower side impact"), ("as", "lap", "H", "Lower side impact"), ("lap", "mh_bot", "H", "Lower side impact"),
    ("as", "as_c", "B", "Anti-sub floor cross"), ("as_c", "mh_bot", "C", "Cockpit floor V (anti-sub)"), ("as_c", "fh_bot", "C", "Cockpit floor V (anti-sub)"),
    ("mh_bar", "sb", "J", "Shoulder harness bar"),
    ("fh_bot", "lap_up", "B", "Diagonal side impact"), ("lap_up", "mh_sis", "B", "Diagonal side impact"),   # A, not B: the 20 g harness case under tube tolerances (robustness.py)
    ("lap", "lap_up", "B", "Lap belt tab brace"),
    # front hoop brace (B) to bulkhead
    ("fh_top", "bh_top", "B", "Front hoop brace"),
    # front bulkhead (B) + supports (C)
    ("bh_bot", "bh_lsus", "B", "Front bulkhead"), ("bh_lsus", "bh_sus", "B", "Front bulkhead"), ("bh_sus", "bh_top", "B", "Front bulkhead"),
    ("bh_top", "ring_top", "H", "FBH support upper"), ("ring_top", "fh_sis", "H", "FBH support upper"),
    ("fh_top", "ring_top", "C", "Front hoop lower brace"),
    ("bh_bot", "pb1", "A", "FBH support lower (pedal box)"), ("pb1", "pb0", "A", "FBH support lower (pedal box)"), ("pb0", "ring_bot", "A", "FBH support lower (pedal box)"),
    ("ring_bot", "fh_bot", "A", "FBH support lower"),
    ("pb0", "pb0m", "B", "Pedal box cross (rear)"), ("pb1", "pb1m", "A", "Pedal box cross (front)"),
    ("ring_bot", "fh_sis", "C", "FBH support diagonal"),   # topo-experiment: front-bay diagonal bh_top->ring_bot removed (beam-model removal study, all gates pass)
    ("ring_bot", "ring_lsus", "J", "Front susp ring"), ("ring_lsus", "ring_sus", "J", "Front susp ring"), ("ring_sus", "ring_top", "J", "Front susp ring"),   # J: no ring top cross (T.1.2), posts bend
    # main hoop braces (B) rearward + supports (C)
    ("mh_top", "r_top", "A", "Main hoop brace"),
    ("mh_sis", "rr_top", "A", "MH brace support upper"), ("rr_top", "sp_top", "A", "MH brace support upper"), ("sp_top", "r_top", "A", "MH brace support upper"),
    ("mh_bot", "rr_bot", "A", "MH brace support lower"), ("rr_bot", "sp_bot", "C", "MH brace support lower"), ("sp_bot", "r_bot", "C", "MH brace support lower"),
    ("rr_bot", "rr_top", "C", "Rear susp ring"),
    ("r_bot", "r_top", "C", "Rear bulkhead"),
    ("mh_bot", "rr_top", "C", "Rear side diagonal"),
    ("mh_bar", "rr_top", "C", "Main hoop bend support (F.5.6.3)"),   # side-view tube at the hoop bend below the braces   # C2: rr_top-r_bot half removed (19 deg cope; spool braces + side bay diagonal triangulate the rear)
    ("sp_bot", "sp_c", "C", "Spool carrier post"),   # topo-experiment: upper post sp_c->sp_top removed (removal study)
    ("sp_c", "rr_top", "B", "Spool carrier brace (chain pull)"), ("sp_c", "rr_bot", "B", "Spool carrier brace (chain pull)"),
    ("r_top", "sp_bot", "C", "Rear side bay diagonal (bulkhead pickups)"),
    ("mh_bot", "em_fb", "H", "Main hoop base cross + front engine mounts"), ("rr_bot", "em_rb", "H", "Rear-ring bottom cross + rear engine mounts"),
    ("mh_sis", "em_ft", "H", "Main hoop mid cross / firewall + top engine mounts"),
]
CROSS = [
    ("bh_bot", "B", "Front bulkhead"), ("bh_top", "B", "Front bulkhead"),
    ("ring_bot", "A", "Lower FBH support cross (F.5.2.3)"),   # = lower FBH support size: its F.5.2.3 support at the ring_bot kink. No ring_top cross: T.1.2
    ("fh_top", "H", "Front hoop"),   # no front hoop base cross: removed in the 2026-10-01 optimisation (not rule-required, lightly loaded)
    ("em_fb", "H", "Main hoop base cross + front engine mounts"), ("mh_top", "J", "Main hoop"),
    ("sb", "J", "Shoulder harness bar"),   # 20 g harness load on a 584 mm span; sized by frame_opt.py with the tolerance check
    ("em_rb", "H", "Rear-ring bottom cross + rear engine mounts"),  # no top cross here: it would pass through the engine
    ("r_bot", "C", "Rear bulkhead"), ("r_top", "C", "Rear bulkhead"),
    ("ring_lsus", "C", "Front pickup cross (rocker/shock loads, rack)"),
    ("pb0m", "B", "Pedal box cross (rear)"), ("pb1m", "A", "Pedal box cross (front)"),
]
DIAG = [  # single diagonals (right node -> left node)
    ("mh_bot", "r_bot'", "C", "Engine bay floor diagonal"),
    ("r_bot", "r_top'", "C", "Rear bulkhead diagonal"),
    ("mh_top", "r_top'", "C", "MH brace-plane diagonal (lateral)"),
    ("fh_top", "ring_top'", "C", "FH brace-plane diagonal (lateral)"),
    ("em_ft", "em_ft'", "H", "Main hoop mid cross / firewall + top engine mounts"),
]
MEMBERS = []
for a, b, s, r in SIDE:
    MEMBERS += [(node(a), node(b), s, r), (mir(node(a)), mir(node(b)), s, r)]
for a, s, r in CROSS:
    MEMBERS.append((node(a), mir(node(a)), s, r))
for a, b, s, r in DIAG:
    MEMBERS.append((node(a), node(b), s, r))

def rad(role):
    """Outside radius (mm) of the tube a role is built from (audit: checks assumed 1 in tube everywhere)."""
    return SIZES[next(s for _, _, s, r in MEMBERS if r == role)][0] / 2

# ---------------- GEOMETRY HELPERS ----------------
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def norm(v): return math.sqrt(sum(x * x for x in v))
def ang(u, v): return math.degrees(math.acos(sum(a * b for a, b in zip(u, v)) / (norm(u) * norm(v))))
def seg_dist(p, a, b):  # 2D point-to-line distance (infinite line a-b)
    (x0, y0), (x1, y1), (x2, y2) = p, a, b
    return abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / math.hypot(x2 - x1, y2 - y1)
def tube_props(s):
    od, t = SIZES[s]; idd = od - 2 * t
    return math.pi / 64 * (od**4 - idd**4), math.pi / 4 * (od**2 - idd**2)

def tube(a, b, s):
    od, t = SIZES[s] if isinstance(s, str) else s; v = sub(b, a); L = norm(v)
    d = cq.Vector(*v).normalized()
    outer = cq.Solid.makeCylinder(od / 2, L, cq.Vector(*a), d)
    return outer.cut(cq.Solid.makeCylinder(od / 2 - t, L, cq.Vector(*a), d))
def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
def cyl_x(x0, x1, y, z, r):
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))
def cyl_z(x, y, z0, z1, r):
    return cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))

# ---------------- RULE CHECKS ----------------
def checks():
    R = []
    def ok(name, cond, detail): R.append((name, bool(cond), detail))
    bot_low = Y_LOW - rad("Lower side impact")
    ok("V.1.2 wheelbase >=1525", WHEELBASE >= 1525, f"{WHEELBASE}")
    ok("V.1.3.2 small/large track >=75%", min(TRACK_F, TRACK_R) / max(TRACK_F, TRACK_R) >= .75,
       f"{min(TRACK_F, TRACK_R) / max(TRACK_F, TRACK_R):.2f}")
    ok("V.1.4.2 lower SIS to ground <=90 (should <=75)", bot_low <= 90, f"{bot_low:.1f}")
    top_edge = Y_SIS + rad("Upper side impact") - bot_low
    ok("F.6.4.4 upper SIS top edge 290-345 above lower SIS bottom", 290 <= top_edge <= 345, f"{top_edge:.1f}")
    for s in SIZES:
        I, A = tube_props(s)
        ok(f"F.3.4.1 size {s} I>={RULE_MIN[s][0]}, A>={RULE_MIN[s][1]}",
           I >= RULE_MIN[s][0] and A >= RULE_MIN[s][1] and SIZES[s][0] >= 25, f"I={I:.0f} A={A:.0f}")
    ok("F.5.8.4 main hoop inside width at base >=380", 2 * Z_COCKPIT - 25.4 >= 380, f"{2 * Z_COCKPIT - 25.4:.0f}")
    drop = H_MAIN + rad("Main hoop") - N["mh_top"][1]
    ok("F.5.9.4 MH brace attach <=160 below top", drop <= 160, f"{drop:.1f}")
    brace = sub(N["r_top"], N["mh_top"]); hoop = sub(N["mh_bot"], N["mh_top"])
    ok("F.5.9.5 MH/brace included angle >=30", ang(brace, (hoop[0], hoop[1], 0)) >= 30,
       f"{ang(brace, (hoop[0], hoop[1], 0)):.1f} deg")
    fdrop = H_FRONT + rad("Front hoop") - N["fh_top"][1]
    ok("F.6.3.4 FH brace attach <=50 below top", fdrop <= 50, f"{fdrop:.1f}")
    wtop = WHEEL_C[1] + WHEEL_DIA / 2
    ok("F.5.7.4 FH top >= steering wheel top", H_FRONT + rad("Front hoop") >= wtop, f"{H_FRONT + rad('Front hoop'):.0f} vs {wtop:.0f}")
    gap = (X_FRONT - rad("Front hoop")) - (WHEEL_C[0] + 15)
    ok("F.5.7.5 FH <=250 forward of steering wheel", 0 <= gap <= 250, f"{gap:.0f}")
    ok("T.1.4.4 controls below FH top", wtop < H_FRONT + rad("Front hoop"), "steering wheel")
    mt, ft = (X_MAIN, H_MAIN + rad("Main hoop")), (X_FRONT, H_FRONT + rad("Front hoop"))
    clr = seg_dist(HEAD, mt, ft) - 150
    ok("F.5.6.4a helmet >=50 from MH-FH line", clr >= 50, f"{clr:.0f}")
    ok("F.5.6.4b helmet >=50 from MH-brace line", seg_dist(HEAD, mt, (X_REAR, Y_REAR_TOP)) - 150 >= 50,
       f"{seg_dist(HEAD, mt, (X_REAR, Y_REAR_TOP)) - 150:.0f}")
    ok("T.2.1.d upright seat (<=30 deg)", SEAT_BACK_DEG <= 30, f"{SEAT_BACK_DEG}")
    ok("F.5.6.6 hip->pedal >=915", round(X_PEDAL - HIP[0], 3) >= 915, f"{X_PEDAL - HIP[0]:.0f}")
    ob_w, ob_h = 2 * Z_BH + 25.4, Y_BH_TOP - Y_BH_BOT + 25.4
    ok("F.8.4.3 bulkhead <=400x350 (no X-brace needed)", ob_w <= 400 and ob_h <= 350, f"{ob_w:.0f}x{ob_h:.0f}")
    ok("F.8.6.3 pedal box 25 mm clear of AIP", X_BH - rad("Front bulkhead") - (X_PEDAL + PEDAL_BOX_LEN) >= 25,
       f"{X_BH - rad('Front bulkhead') - (X_PEDAL + PEDAL_BOX_LEN):.0f}")
    ia_bot = IA[2] - bot_low
    ok("F.8.5.6a IA bottom leading edge <=175 above lower SIS bottom", ia_bot <= 175, f"{ia_bot:.0f}")
    ok("F.8.4.2 IA >=200 long, >=200 wide, >=100 high", round(IA[1] - IA[0]) >= 200 and 2 * IA[4] >= 200 and IA[3] - IA[2] >= 100, "")
    dy, dx = SHOULDER_BAR_Y - SHOULDER[1], SHOULDER[0] - X_MAIN
    sa = math.degrees(math.atan2(dy, dx))
    ok("T.2.6.1 shoulder belt angle -20..+10", -20 <= sa <= 10, f"{sa:.1f} deg")
    ok("T.2.6.2 shoulder belt spacing 175-235", 175 <= 2 * BELT_Z <= 235, f"{2 * BELT_Z}")
    ok("T.1.5.1a seat not below top of lowest tube", SEAT_Y0 >= Y_LOW + rad("Lower side impact"), f"{SEAT_Y0} vs {Y_LOW + rad('Lower side impact'):.1f}")
    inner_f = TRACK_F / 2 - TIRE_W / 2
    ok("frame clear of front tires (steer room >=80)", inner_f - (Z_BH + rad("Front bulkhead")) >= 80, f"{inner_f - Z_BH - rad('Front bulkhead'):.0f}")
    return R

IA = (X_BH + 12.7 + 1.5, X_BH + 12.7 + 1.5 + 200, 120, 320, 100)  # x0,x1,y0,y1,half-width (standard foam envelope)

# ---------------- COLOUR KEY (3D model) ----------------
# one colour per system; report.py writes the README "Colour key" from this table, views.py draws views/colour_key.png
COLORS = {
    "frame_heavy":  ((0.80, 0.05, 0.05), "Red", "Frame, heavy wall (x0.095in): roll hoops, front ring posts, hoop braces, shoulder bar, engine-mount crosses"),
    "frame_b":      ((1.00, 0.55, 0.00), "Orange", "Frame, 1.0 x 0.065in: side impact, bulkheads, braces, pedal-box and harness crosses"),
    "frame_c":      ((0.55, 0.55, 0.55), "Grey", "Frame, 1.0 x 0.049in: supports, floor V, lighter crosses"),
    "suspension":   ((0.10, 0.35, 0.95), "Blue", "Suspension links: A-arms and tie rods"),
    "pushrod":      ((0.00, 0.80, 0.90), "Cyan", "Pushrods"),
    "rocker":       ((0.15, 0.15, 0.55), "Navy", "Rockers (bellcranks)"),
    "shock":        ((0.55, 0.75, 1.00), "Light blue", "Coil-over shocks"),
    "wheel":        ((0.08, 0.08, 0.08), "Black", "Tyres"),
    "corner":       ((0.80, 0.80, 0.82), "Light grey", "Uprights, hubs and rotors"),
    "brake":        ((0.55, 0.15, 0.75), "Purple", "Brakes and pedals: calipers, pedal box, pedals, balance bar, master cylinders, reservoirs"),
    "steering":     ((0.00, 0.50, 0.45), "Teal", "Steering: wheel, column, rack"),
    "powertrain":   ((0.30, 0.30, 0.32), "Dark grey", "Powertrain: engine (placeholder), sprockets, chain, spool, carriers, CV half-shafts"),
    "fuel":         ((0.60, 0.35, 0.10), "Brown", "Fuel cell"),
    "driver_cell":  ((0.20, 0.65, 0.25), "Green", "Driver: seat base, seat back, head restraint"),
    "closeout":     ((0.88, 0.88, 0.80), "Cream", "Sheet metal: belly pan, firewall, anti-intrusion plate"),
    "crash":        ((1.00, 0.85, 0.10), "Yellow", "Impact attenuator (foam)"),
    "electrical":   ((0.95, 0.10, 0.60), "Pink", "Electrical: battery, master switch, E-stop, kill relay, inertia switch, brake light"),
    "aero":         ((0.95, 0.95, 0.97), "White", "Aero: rear wing main plane, DRS flap, endplates, wing struts and braces, DRS servo"),
    "hydraulic":    ((0.90, 0.72, 0.10), "Gold", "Routing: brake lines (hard line and flexible hose) and the throttle cable"),
    "wiring":       ((0.85, 0.00, 0.85), "Magenta", "Routing: 12 V harness wires (battery, master switch, shutdown loop, ignition, fuel pump, starter, fan, brake light, DRS)"),
}
# Part-number system code per colour group: NM26-<code>-<nnn>. Numbers are given in build order, so a part keeps
# its number while the model's structure is unchanged; freeze them (NM26_Mule_parts.csv) before ordering or drawing parts.
PART_CODE = {"frame_heavy": "FRM", "frame_b": "FRM", "frame_c": "FRM", "suspension": "SUS", "pushrod": "SUS",
             "rocker": "SUS", "shock": "SUS", "wheel": "WHL", "corner": "UPR", "brake": "BRK", "steering": "STR",
             "powertrain": "PWT", "fuel": "FUL", "driver_cell": "CKP", "closeout": "BDY", "crash": "BDY", "electrical": "ELE", "aero": "AER",
             "hydraulic": "RTG", "wiring": "RTG"}

def color(key): return cq.Color(*COLORS[key][0])   # entries: (rgb, colour name, what it is)

# ---------------- BUILD ----------------
PAN_T = 1.6   # belly pan / floor closeout (T.1.7): 1.6 mm 5052 aluminium, flat, under the lowest tubes
def belly_pan():
    """Flat sheet under the whole frame, following the lower-rail outline in plan, with the two
    25 mm drain holes T.5.5.4 asks for (behind the driver, ahead of the fuel/engine)."""
    y1 = Y_LOW - rad("Lower side impact")   # touches the underside of the lowest (side-impact) tubes
    outline = [N[k] for k in ("r_bot", "rr_bot", "mh_bot", "fh_bot", "ring_bot", "bh_bot")]
    pts = [(p[0], p[2] + rad("Lower side impact")) for p in outline] + [(p[0], -p[2] - rad("Lower side impact")) for p in reversed(outline)]
    pan = (cq.Workplane("XZ", origin=(0, y1, 0)).polyline([(x, -z) for x, z in pts]).close()
           .extrude(PAN_T).val())      # XZ workplane normal is -Y, so extrude goes down from y1
    for z in (-100, 100):
        pan = pan.cut(cq.Solid.makeCylinder(12.5, 10, cq.Vector(X_MAIN - 60, y1 + 2, z), cq.Vector(0, -1, 0)))
    return pan

def build():
    asm = cq.Assembly(name="NM26_Mule"); count = {}; asm.parts = []
    def add(shape, name, key):   # every CAD name starts with its part number NM26-<system>-<nnn> (see PART_CODE)
        code = PART_CODE[key]; count[code] = count.get(code, 0) + 1; pn = f"NM26-{code}-{count[code]:03d}"
        asm.add(shape, name=f"{pn}_{name}", color=color(key)); asm.parts.append((pn, name, COLORS[key][1]))
    colors = {"J": "frame_heavy", "H": "frame_heavy", "A": "frame_heavy", "B": "frame_b", "C": "frame_c"}
    for s in SIZES:
        tubes = [tube(a, b, s) for a, b, sz, _ in MEMBERS if sz == s]
        add(cq.Compound.makeCompound(tubes), name=f"frame_size_{s}", key=(colors[s]))
    # wheels
    for x, tr, n in [(WHEELBASE, TRACK_F, "front"), (0, TRACK_R, "rear")]:
        for sgn, side in [(1, "R"), (-1, "L")]:
            zc = sgn * tr / 2
            t = cyl_z(x, TIRE_OD / 2, zc - TIRE_W / 2, zc + TIRE_W / 2, TIRE_OD / 2)
            t = t.cut(cyl_z(x, TIRE_OD / 2, zc - TIRE_W / 2, zc + TIRE_W / 2, 165))
            add(t, name=f"tire_{n}_{side}", key=("wheel"))
            links = susp_links(n)
            if sgn < 0: links = [(nm, mir(p), mir(q), k) for nm, p, q, k in links]
            import uprights as U   # local: uprights -> loads -> this module
            ug = U.geom(n); hx, hy = ug["x"], ug["r"]; zf = lambda z: sgn * z
            hr = U.BEARING["D"] / 2 + U.UPRIGHT["wall"]
            zlo, zhi = ug["zi"] - U.BEARING["B"] / 2 - 3, ug["zo"] + U.BEARING["B"] / 2 + 3
            body = cyl_z(hx, hy, min(zf(zlo), zf(zhi)), max(zf(zlo), zf(zhi)), hr)
            for _, p_, _, _ in links:   # upright arms: housing -> each hardpoint on the upright
                body = body.fuse(tube((hx, hy, p_[2]), p_, (U.UPRIGHT["w"], U.UPRIGHT["w"] / 2)))
            add(body, name=f"upright_{n}_{side}", key=("corner"))
            hub = cyl_z(hx, hy, min(zf(zlo - 5), zf(ug["face"])), max(zf(zlo - 5), zf(ug["face"])), U.HUB["od"] / 2)
            flange_z = sorted((zf(ug["face"] - 8), zf(ug["face"])))
            hub = hub.fuse(cyl_z(hx, hy, flange_z[0], flange_z[1], 65))
            add(hub, name=f"hub_{n}_{side}", key=("corner"))
            rz = sorted((zf(ug["rotor"] - 2), zf(ug["rotor"] + 2)))
            add(cyl_z(hx, hy, rz[0], rz[1], U.ROTOR_OD / 2).cut(cyl_z(hx, hy, rz[0], rz[1], 55)),
                    name=f"rotor_{n}_{side}", key=("corner"))
            cz = sorted((zf(ug["rotor"] - 18), zf(ug["rotor"] + 18)))
            add(box(hx - 60, hx + 20, hy + U.ROTOR_OD / 2 - 30, hy + U.ROTOR_OD / 2 + U.CALIPER_H - 30, cz[0], cz[1]),
                    name=f"caliper_{n}_{side}", key=("brake"))
            for nm, p, q, _ in links:
                col = "pushrod" if nm == "pushrod" else "suspension"
                add(tube(p, q, PUSHROD_TUBE if nm == "pushrod" else SUSP_TUBE),
                        name=f"{nm.replace(' ', '_')}_{n}_{side}", key=(col))
    import rocker   # local: rocker imports this module
    for n in ("front", "rear"):
        r = rocker.analyse(n); P, A, B, S = r["g"]["P"], r["A3"], r["B3"], r["g"]["S"]
        for sgn, side in [(1, "R"), (-1, "L")]:
            f = (lambda p: tuple(p)) if sgn > 0 else (lambda p: mir(tuple(p)))
            for a_, b_, nm in [(P, A, "arm_pushrod"), (P, B, "arm_shock"), (A, B, "arm_tie")]:
                add(tube(f(a_), f(b_), (12.0, 6.0)), name=f"rocker_{n}_{side}_{nm}", key=("rocker"))
            add(tube(f(B), f(S), (50.0, 25.0)), name=f"shock_{n}_{side}", key=("shock"))
    # packaging
    hx = HIP[0]
    add(box(hx - 80, X_PEDAL - 450, SEAT_Y0, SEAT_Y0 + 6, -200, 200), name="seat_base", key=("driver_cell"))
    add(box(hx - 90, hx - 40, SEAT_Y0, SHOULDER[1] + 40, -200, 200), name="seat_back", key=("driver_cell"))
    add(box(X_MAIN + 13, X_MAIN + 13 + 60, HEAD[1] - 140, HEAD[1] + 140, -80, 80), name="head_restraint",
            key=("driver_cell"))
    import brakes as BR   # local: brakes -> loads -> this module
    g = BR.geometry(); (xp, yp), (xb, yb), (xa, ya) = g["piv"], g["bar"], g["pad"]
    add(box(PB_X[0] - 20, PB_X[1] + 10, g["y_base"] - 6, g["y_base"], -PB_Z - 20, PB_Z + 20), name="pedal_box_base", key=("brake"))
    for z, nm in ((BR.BRAKE_Z, "brake"), (BR.THROTTLE_Z, "throttle")):
        add(tube((xp, yp, z), (xa, ya, z), (BR.PEDAL["b"] * 2, BR.PEDAL["b"])), name=f"{nm}_pedal", key=("brake"))
        add(box(xa - 8, xa, ya - 40, ya + 40, z - 35, z + 35), name=f"{nm}_pedal_pad", key=("brake"))
    zb = BR.BRAKE_Z
    add(tube((xb, yb, zb - BR.BAR["e"] - 10), (xb, yb, zb + BR.BAR["e"] + 10), (BR.BAR["d"], BR.BAR["d"] / 2)), name="balance_bar", key=("brake"))
    for dz, ax in ((-BR.BAR["e"], "front"), (BR.BAR["e"], "rear")):
        add(cyl_x(xb + BR.MC_ROD, g["mc_front"], yb, zb + dz, 16), name=f"master_cyl_{ax}_{BR.MC_BORE[ax] / 25.4:.3f}in", key=("brake"))
        add(cyl_x(xb + BR.MC_ROD, xb + BR.MC_ROD + 40, yb + 70, zb + dz, 18), name=f"reservoir_{ax}", key=("brake"))
    add(box(IA[0] - 1.5, IA[0], Y_BH_BOT, Y_BH_TOP, -Z_BH, Z_BH), name="anti_intrusion_plate", key=("closeout"))
    add(box(IA[0], IA[1], IA[2], IA[3], -IA[4], IA[4]), name="impact_attenuator", key=("crash"))
    w = cq.Solid.makeTorus(WHEEL_DIA / 2 - 12, 12, cq.Vector(*WHEEL_C, 0), cq.Vector(1, 0, 0))
    add(w, name="steering_wheel", key=("steering"))
    add(tube((WHEEL_C[0], WHEEL_C[1], 0), (RACK[0], RACK[1], 0), "C"), name="steering_column", key=("steering"))
    add(cyl_z(RACK[0], RACK[1], -RACK[2], RACK[2], RACK_R), name="steering_rack", key=("steering"))
    import powertrain as PT   # local: powertrain -> loads -> this module
    add(box(*PT.ENGINE["box"]), name="engine_450cc_single_placeholder", key=("powertrain"))
    cs, r1, ax_, r2 = PT.sprockets(); zc = PT.CHAIN_Z
    add(cyl_z(cs[0], cs[1], zc - 4, zc + 4, r1 + 6), name=f"sprocket_front_{PT.FRONT_T}T", key=("powertrain"))
    add(cyl_z(ax_[0], ax_[1], zc - 4, zc + 4, r2 + 6), name=f"sprocket_rear_{PT.REAR_T}T", key=("powertrain"))
    for sg in (1, -1):   # chain runs
        add(tube((cs[0], cs[1] + sg * r1, zc), (ax_[0], ax_[1] + sg * r2, zc), (10.0, 5.0)), name=f"chain_{'top' if sg > 0 else 'bottom'}", key=("powertrain"))
    zs = N["sp_c"][2]
    add(tube((0.0, TIRE_OD / 2, -zs), (0.0, TIRE_OD / 2, zs), (50.0, 10.0)), name="spool", key=("powertrain"))
    import uprights as U
    for sg, side in ((1, "R"), (-1, "L")):
        add(box(-45, 45, TIRE_OD / 2 - 55, TIRE_OD / 2 + 55, sg * zs - 6, sg * zs + 6), name=f"spool_carrier_{side}", key=("powertrain"))
        add(tube((0.0, TIRE_OD / 2, sg * PT.CV["z_in"]), (0.0, TIRE_OD / 2, sg * (U.geom("rear")["zi"] - 10)), (25.0, 12.5)),
                name=f"cv_halfshaft_{side}", key=("powertrain"))
    add(box(X_MAIN - 40, X_MAIN - 13, Y_LOW, 700, -Z_COCKPIT, Z_COCKPIT), name="firewall", key=("closeout"))
    add(box(X_MAIN - 13 - 200, X_MAIN - 13 - 30, 480, 700, -140, 140), name="fuel_cell_6L", key=("fuel"))
    add(belly_pan(), name="belly_pan_1.6mm", key=("closeout"))
    import shutdown as SD   # local: electrical layout
    for nm, (w, h, d) in (("battery", (150, 90, 90)), ("primary master switch", (60, 60, 40)), ("e-stop", (40, 40, 40)),
                          ("inertia switch", (50, 50, 40)), ("kill relay", (40, 40, 30)), ("brake light", (20, 60, 160))):
        x, y, z = SD.LOC[nm]
        add(box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2), name=nm.replace(" ", "_"), key=("electrical"))
    import aero as AE   # local: aero imports mule
    if not AE.FITTED:   # wing not fitted on the base mule: the CAD shows the car as built
        return asm
    for st, label in (("closed", "DRS_flap_closed"),):
        sec = AE.section(st)
        for el, (le, chord, ang) in (("main_plane", (sec["le"], AE.MAIN["chord"], AE.MAIN["angle"])),
                                     (label, (sec["fle"], AE.FLAP["chord"], AE.FLAP[st]))):
            add(airfoil(le, chord, ang, AE.SPAN), name=f"rear_wing_{el}", key=("aero"))
    xs = [p_[0] for st in ("closed", "open") for p_ in AE.section(st).values()]
    ys = [p_[1] for st in ("closed", "open") for p_ in AE.section(st).values()]
    for sg, side in ((1, "R"), (-1, "L")):
        z0 = sg * AE.SPAN / 2
        add(box(min(xs) - 5, max(xs) + 5, min(ys) - 60, max(ys) + 15, min(z0, z0 + sg * AE.ENDPLATE_T), max(z0, z0 + sg * AE.ENDPLATE_T)),
            name=f"rear_wing_endplate_{side}", key=("aero"))
    for a_, b_, sz, role in AE.strut_members():
        add(tube(a_, b_, sz), name=role.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_"), key=("aero"))
    pv = AE.section("closed")["pivot"]
    add(box(pv[0] - 30, pv[0] + 30, pv[1] - 70, pv[1] - 25, -30, 30), name="DRS_servo_15Nm", key=("aero"))
    return asm

def airfoil(le, chord, angle_deg, span, camber=0.06, pos=0.4, thick=0.12, n=30):
    """Inverted NACA 4-digit style section (camber toward the ground) extruded across the car; LE at le (x, y),
    chord running rearward and up at angle_deg."""
    xs = [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    def yc(x): return camber / pos**2 * (2 * pos * x - x * x) if x < pos else camber / (1 - pos)**2 * (1 - 2 * pos + 2 * pos * x - x * x)
    def yt(x): return 5 * thick * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x**3 - 0.1036 * x**4)
    upper = [(x, -yc(x) + yt(x)) for x in xs]; lower = [(x, -yc(x) - yt(x)) for x in reversed(xs)]
    a = math.radians(angle_deg); d = (-math.cos(a), math.sin(a)); nrm = (math.sin(a), math.cos(a))
    pts = [(le[0] + chord * (u * d[0] + v * nrm[0]), le[1] + chord * (u * d[1] + v * nrm[1])) for u, v in upper + lower[1:-1]]
    return cq.Workplane("XY").polyline(pts).close().extrude(span).translate((0, 0, -span / 2)).val()

def cutlist():
    rows = {}
    for a, b, s, role in MEMBERS:
        L = norm(sub(b, a)); k = (s, role)
        rows.setdefault(k, [0, 0.0]); rows[k][0] += 1; rows[k][1] += L
    return rows

def colour_key_md():
    """Markdown table of the 3D-model colours (pasted into README "Colour key")."""
    rows = ["| Colour | What it is |", "|---|---|"]
    for _, name, what in COLORS.values():
        rows.append(f"| {name} | {what} |")
    return "\n".join(rows)

if __name__ == "__main__":
    out = pathlib.Path(__file__).parent
    res = checks()
    for name, passed, d in res:
        print(("PASS " if passed else "FAIL ") + f"{name:60s} {d}")
    print(f"hip={tuple(round(v) for v in HIP)} shoulder={tuple(round(v) for v in SHOULDER)} "
          f"head={tuple(round(v) for v in HEAD)} pedal_x={X_PEDAL:.0f} bulkhead_x={X_BH}")
    rows = cutlist(); total_mass = 0
    with open(out / "fab" / "tube_order_list.csv", "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["size", "OD_mm", "wall_mm", "role", "pieces", "total_length_mm", "mass_kg"])
        for (s, role), (n, L) in sorted(rows.items()):
            od, t = SIZES[s]; m = tube_props(s)[1] * L * STEEL_DENSITY; total_mass += m
            wr.writerow([s, od, t, role, n, round(L), round(m, 2)])
    for s in SIZES:
        L = sum(v[1] for k, v in rows.items() if k[0] == s)
        print(f"size {s}: {L / 1000:.1f} m of tube")
    print(f"frame tube mass ~{total_mass:.1f} kg, {len(MEMBERS)} members")
    asm = build()
    # export Z-up (Fusion/SolidWorks default): rotate +90 deg about X so model Y (up) -> Z
    zup = cq.Assembly(name="NM26_Mule_Zup").add(asm, loc=cq.Location(cq.Vector(), cq.Vector(1, 0, 0), 90))
    (out / "cad" / "simple").mkdir(parents=True, exist_ok=True); zup.save(str(out / "cad" / "simple" / "NM26_Mule.step"))
    with open(out / "cad" / "simple" / "NM26_Mule_parts.csv", "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["part_number", "name", "colour"]); wr.writerows(asm.parts)
    shape = asm.toCompound()
    (out / "views").mkdir(exist_ok=True)
    for nm, d in [("side", (0, 0, 1)), ("front", (1, 0, 0)), ("top", (0, 1, 0)), ("iso", (1, 0.6, 1))]:
        cq.exporters.export(shape, str(out / "views" / f"simple_{nm}.svg"),
                            opt={"projectionDir": d, "showHidden": False, "width": 1200, "height": 700})
    assert all(p for _, p, _ in res), "rule check failed"
    print("wrote cad/simple/NM26_Mule.step, cad/simple/NM26_Mule_parts.csv, views/simple_*.svg, fab/tube_order_list.csv")
