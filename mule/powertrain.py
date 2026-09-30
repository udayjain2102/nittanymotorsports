"""Powertrain: gearing, chain drive (length, adjustment, wrap, clearances), CV angles, engine mounts,
and the frame under a full-traction launch (chain loop + rear tyre force, inertia relief).

ENGINE values are a generic 450 cc single placeholder: replace them with the chosen engine's
service-manual numbers and measured mount/countershaft positions, then re-run pytest.
Axes as mule.py (X fwd, Y up, Z right). Chain on the LEFT side (motorcycle convention).
Run: python powertrain.py
"""
import math
import numpy as np
import mule as m
import loads as L
import fea

ENGINE = dict(redline=11500, peak_torque=50.0,             # rpm, N*m   (placeholder: verify)
              primary=2.6, gears=[2.0, 1.6, 1.33, 1.14, 1.0],  # primary reduction, gearbox ratios (placeholder)
              box=(150.0, m.X_MAIN - 50, 130.0, 470.0, -170.0, 170.0),   # envelope x0,x1,y0,y1,z0,z1 (placeholder)
              countershaft=(200.0, 250.0), mass=32.0)          # output shaft (X, Y) and mass
CHAIN = dict(pitch=15.875, width=17.0, break_kN=35.6)      # DID 520VO O-ring: 8000 lb average tensile (DID listing)
FRONT_T, REAR_T = 13, 50                                   # sprockets
CHAIN_Z = -180.0                                           # chain line (left): outboard of the engine case, inboard of the spool posts
ADJUST = 20.0                                              # eccentric spool carriers: +/- centre-distance adjustment, mm
SHIELD = dict(t=2.66, width_x=3.0)                         # T.5.2.7: 2.66 mm steel, >= 3x chain width
CV = dict(max_angle=22.0, plunge=20.0, z_in=m.N["sp_c"][2] + 10)   # tripod CV limits; inboard joint just outside the carrier

def pitch_r(n): return CHAIN["pitch"] / (2 * math.sin(math.pi / n))

def sprockets():
    cs = np.array([*ENGINE["countershaft"], CHAIN_Z]); ax = np.array([0.0, m.TIRE_OD / 2, CHAIN_Z])
    return cs, pitch_r(FRONT_T), ax, pitch_r(REAR_T)

def chain_links(C, n1, n2):
    """Chain length in pitches for centre distance C (mm), standard formula."""
    p = CHAIN["pitch"]; c = C / p
    return 2 * c + (n1 + n2) / 2 + ((n2 - n1) / (2 * math.pi)) ** 2 / c

def centre_for_links(Lp, n1, n2):
    lo, hi = 50.0, 2000.0
    for _ in range(80):
        mid = (lo + hi) / 2; (lo, hi) = (mid, hi) if chain_links(mid, n1, n2) < Lp else (lo, mid)
    return (lo + hi) / 2

def gearing():
    r = m.TIRE_R_LOADED / 1000; final = REAR_T / FRONT_T   # loaded rolling radius for speed
    top = ENGINE["redline"] / (ENGINE["primary"] * ENGINE["gears"][-1] * final) / 60 * 2 * math.pi * r * 3.6
    wheel_T1 = ENGINE["peak_torque"] * ENGINE["primary"] * ENGINE["gears"][0] * final
    return final, top, wheel_T1

def traction_torque():
    """Axle torque at the rear traction limit, 1 g accel transfer, both rear tyres (spool), N*m."""
    w = L.MASS * L.G; rear = w * (1 - L.FRONT_SPLIT) + w * 1.0 * L.CG_H / m.WHEELBASE
    return L.MU * rear * m.TIRE_OD / 2 / 1000

def seg_point_dist(p, a, b):
    ab = b - a; t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1); return np.linalg.norm(p - (a + t * ab))

def clearances():
    """Min gap (mm) from the two sprockets (disc, pitch radius + 8) and both chain runs to frame tubes, pan, ground."""
    cs, r1, ax, r2 = sprockets(); worst = (1e9, "")
    samples = []
    for c, r in ((cs, r1 + 8), (ax, r2 + 8)):
        samples += [c + r * np.array([math.cos(t), math.sin(t), 0]) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    d = ax - cs; dist = np.linalg.norm(d); u = d / dist
    nrm = np.array([-u[1], u[0], 0])
    for sgn in (1, -1):   # top and bottom runs
        n_ = nrm * sgn   # run offset normal to the centre line (small-angle approximation of the tangent)
        p1, p2 = cs + r1 * n_, ax + r2 * n_
        samples += [p1 + k * (p2 - p1) for k in np.linspace(0, 1, 20)]
    for a_, b_, sz, role in m.MEMBERS:
        a_, b_ = np.array(a_, float), np.array(b_, float); rad = m.SIZES[sz][0] / 2 + CHAIN["width"] / 2
        for p in samples:
            gap = seg_point_dist(p, a_, b_) - rad
            if gap < worst[0]: worst = (gap, role)
    pan_top = m.Y_LOW - 12.7
    low = min(p[1] for p in samples)
    return worst, low, low - pan_top if abs(CHAIN_Z) < m.Z_REAR else None

def cv():
    """Half-shaft angle (deg) and plunge (mm) over +/-TRAVEL from the spool carrier to the rear hub."""
    import uprights as U, springs
    g = U.geom("rear"); z_out = g["zi"] - 10; y0 = m.TIRE_OD / 2
    L0 = z_out - CV["z_in"]
    ang = math.degrees(math.atan2(springs.TRAVEL, L0)); plunge = math.hypot(L0, springs.TRAVEL) - L0
    return ang, plunge, L0

CV_BOOT_R = 40.0   # mm, CV boot / joint radius, applied along the whole shaft (conservative)

def seg_seg(p1, q1, p2, q2, n=40):
    """Minimum distance (mm) between two segments, sampled."""
    best = 1e9
    for i in range(n + 1):
        a = p1 + (q1 - p1) * i / n
        best = min(best, seg_point_dist(a, p2, q2))
    return best

def toe_link_to_halfshaft():
    """Smallest gap (mm) between the rear toe link and the CV half-shaft (boot radius included) over the design
    travel: both outer ends move with the upright. Trinity's 2020 FSAE car had its rear tie rods hit the axle."""
    import suspension as S, springs
    import uprights as U
    g = S.geom("rear"); (_, p, q, _) = m.susp_links("rear")[4]; z_out = U.geom("rear")["zi"] - 10; worst = 1e9
    for t in (-springs.DROOP, -12.5, 0.0, 25.0, springs.TRAVEL):
        lo, hi = -0.8, 0.8
        for _ in range(60):
            mid = (lo + hi) / 2; f, _ = S.upright(g, mid)
            (lo, hi) = (mid, hi) if f(g["C"])[1] - g["C"][1] - t < 0 else (lo, mid)
        f, _ = S.upright(g, (lo + hi) / 2)
        mv = lambda pt: np.array([pt[0], *reversed(f((pt[2], pt[1])))])
        hub = mv((0.0, m.TIRE_OD / 2, z_out))
        gap = seg_seg(np.array(q, float), mv(p), np.array([0.0, m.TIRE_OD / 2, CV["z_in"]]), hub) - CV_BOOT_R - m.SUSP_TUBE[0] / 2
        worst = min(worst, gap)
    return worst

def mount_forces(F_chain_engine, p_chain):
    """Engine free body: chain force at its tangent point + weight x 2.5 g -> minimum-norm forces at the 6 mounts."""
    names = ["em_fb", "em_ft", "em_rb"]; pts = [np.array(m.N[n], float) for n in names] + [np.array(m.mir(m.N[n]), float) for n in names]
    box = ENGINE["box"]; cg = np.array([(box[0] + box[1]) / 2, (box[2] + box[3]) / 2, 0.0])
    Wt = np.array([0, -2.5 * ENGINE["mass"] * L.G, 0])
    A = np.zeros((6, 18)); b = np.zeros(6)
    for i, p in enumerate(pts):
        for k in range(3):
            e = np.zeros(3); e[k] = 1; A[:3, 3 * i + k] = e; A[3:, 3 * i + k] = np.cross(p - cg, e)
    b[:3] = -(F_chain_engine + Wt); b[3:] = -np.cross(p_chain - cg, F_chain_engine)
    f = np.linalg.pinv(A) @ b
    return [(names[i % 3] + ("'" if i >= 3 else ""), pts[i], f[3 * i:3 * i + 3]) for i in range(6)]

def launch_frame():
    """Frame FoS under a full-traction launch: chain loop (engine mounts + spool carriers) + right-rear tyre force."""
    fr = fea.Frame(m.MEMBERS); cs, r1, ax, r2 = sprockets()
    T = traction_torque(); Tc = T / (r2 / 1000)                 # chain tension, N
    top1, top2 = cs + np.array([0, r1, 0]), ax + np.array([0, r2, 0])   # tight (top) run
    u = (top2 - top1) / np.linalg.norm(top2 - top1)
    F_on_engine = Tc * u; F_on_spool = -Tc * u
    loads = {}
    for name, p, f in mount_forces(F_on_engine, top1):
        k = fr.find(p); loads[k] = loads.get(k, 0) - f         # mount pushes engine with f -> frame gets -f
    zl, zr = -m.N["sp_c"][2], m.N["sp_c"][2]; share_l = (zr - CHAIN_Z) / (zr - zl)
    for z, sh in ((zl, share_l), (zr, 1 - share_l)):
        k = fr.find((0.0, m.TIRE_OD / 2, z)); loads[k] = loads.get(k, 0) + sh * F_on_spool
    C, links = L.corner("rear"); w = L.MASS * L.G
    Fz = (w * (1 - L.FRONT_SPLIT) + w * L.CG_H / m.WHEELBASE)   # spool worst case: one tyre carries the axle
    f = L.link_forces(C, links, (T * 1000 / (m.TIRE_OD / 2), Fz, 0.0))
    for (n, p, q, node), v in zip(links, f):
        uu = np.subtract(q, p) / np.linalg.norm(np.subtract(q, p))
        if n == "pushrod":
            import rocker
            for nd, Fv in rocker.reactions("rear", -v * uu)[0].items():
                k = fr.find(m.N[nd]); loads[k] = loads.get(k, 0) + Fv
            continue
        k = fr.find(m.N[node]); loads[k] = loads.get(k, 0) - v * uu
    u_, st = fr.solve(*fea.inertia_relief(fr, loads))
    j = int(np.argmax(st))
    return fea.SY_WELD / st[j], fr.el[j][3], Tc

def checks():
    final, top, wheel_T1 = gearing(); cs, r1, ax, r2 = sprockets()
    C = np.linalg.norm(ax - cs); Lp = chain_links(C, FRONT_T, REAR_T); Lp_even = 2 * math.ceil(Lp / 2)
    C_even = centre_for_links(Lp_even, FRONT_T, REAR_T)
    wrap = 180 - 2 * math.degrees(math.asin((r2 - r1) / C))
    (gap, what), low, pan_gap = clearances(); ang, plunge, L0 = cv()
    fos, where, Tc = launch_frame()
    bx = ENGINE["box"]
    return [
        ("top speed at redline 100-130 km/h", 100 <= top <= 130, f"{top:.0f} km/h ({FRONT_T}/{REAR_T} = {final:.2f})"),
        ("1st gear can reach the traction limit", wheel_T1 >= traction_torque(), f"{wheel_T1:.0f} vs {traction_torque():.0f} N*m"),
        ("chain centre distance >= r1 + r2 + 25 mm", C >= r1 + r2 + 25, f"{C:.0f} mm (min {r1 + r2 + 25:.0f})"),
        ("wrap on the front sprocket >= 120 deg", wrap >= 120, f"{wrap:.0f} deg"),
        ("even-link chain fits inside the carrier adjustment", abs(C_even - C) <= ADJUST, f"{Lp_even} links -> centre {C_even:.0f} mm ({C_even - C:+.0f}, adjust +/-{ADJUST:.0f})"),
        ("chain tension safety >= 4 (traction-limited)", CHAIN["break_kN"] * 1e3 / Tc >= 4, f"{Tc / 1e3:.1f} kN vs {CHAIN['break_kN']:.0f} kN"),
        ("sprockets/chain clear frame tubes >= 10 mm", gap >= 10, f"{gap:.0f} mm ({what})"),
        ("sprockets/chain >= 50 mm above ground", low >= 50, f"{low:.0f} mm"),
        ("chain line outboard of the engine, inboard of the spool posts", bx[4] - 5 > CHAIN_Z > -m.N["sp_c"][2] + 20,
         f"z = {CHAIN_Z:.0f} (engine side {bx[4]:.0f}, posts {-m.N['sp_c'][2]:.0f})"),
        ("CV angle <= limit over +/-50 mm travel", ang <= CV["max_angle"], f"{ang:.1f} deg (shaft {L0:.0f} mm)"),
        ("CV plunge <= limit", plunge <= CV["plunge"], f"{plunge:.1f} mm"),
        ("rear toe link clears the CV half-shaft >= 10 mm over travel (boot included)", toe_link_to_halfshaft() >= 10, f"{toe_link_to_halfshaft():.0f} mm"),
        ("engine envelope clear of main hoop / firewall", bx[1] <= m.X_MAIN - 40, f"engine front {bx[1]:.0f}, firewall {m.X_MAIN - 40:.0f}"),
        ("frame FoS >= 1.2 under full-traction launch", fos >= 1.2, f"{fos:.2f} ({where})"),
    ]

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:52s} {d}")
    print(f"scatter shield (T.5.2.7): {SHIELD['t']} mm steel, >= {SHIELD['width_x'] * CHAIN['width']:.0f} mm wide, centred on the chain line")
    assert all(p for _, p, _ in res), "powertrain check failed"
