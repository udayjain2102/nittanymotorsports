"""Fusion Generative Design setup for a frame study (curiosity: what load path does GD find?).

Writes fusion_gd/: NM26_GD_preserve.step (roll hoops + 40 mm balls at every point the frame must reach),
NM26_GD_obstacles.step (wheels with steer sweep, engine, driver, cockpit opening, rear axle), LOADS.md (5 load cases,
forces per preserve body, from the same code as the frame checks). GD grows a solid, not a tube frame: the result is a
picture of the load paths, not a buildable or rules-legal frame.
Axes: exported like NM26_Mule.step (Z-up STEP), which this Fusion shows as X forward from the rear axle, Y up, Z right.
Run: python fusion_gd.py
"""
import math, pathlib
import numpy as np
import cadquery as cq
import mule as m, loads as L, rocker, powertrain as P, harness as H

OUT = pathlib.Path(__file__).parent / "fusion_gd"
BALL = 20.0   # preserve ball radius

def pts():
    """{preserve name: (x, y, z)} - right side names end _R, mirrored _L."""
    p = {}
    for ax in ("front", "rear"):
        s = m.SUSP[ax]
        for n in s["inner_low"] + s["inner_up"]: p[f"{ax}_pickup_{n}"] = m.N[n]
        p[f"{ax}_rocker_pivot"] = m.N[s["pushrod"][1]]
        p[f"{ax}_shock_mount"] = tuple(rocker.design(ax)["S"])
    p["rear_toe_link"] = m.SUSP["rear"]["steer"][1]
    p["rack_mount"] = (m.RACK[0], m.RACK[1], m.RACK[2])
    for n in ("em_fb", "em_ft", "em_rb", "sb", "lap", "pb0m", "pb1m", "sp_c"): p[f"mount_{n}"] = m.N[n]
    out = {}
    for k, v in p.items():
        out[k + "_R"] = tuple(map(float, v)); out[k + "_L"] = tuple(map(float, m.mir(v)))
    out["mount_anti_sub"] = tuple(map(float, m.N["as_c"]))
    return out

def zup(a): return cq.Assembly(name=a.name + "_Zup").add(a, loc=cq.Location(cq.Vector(), cq.Vector(1, 0, 0), 90))
def cyl(a, b, r):
    a, b = np.array(a, float), np.array(b, float); d = b - a
    return cq.Solid.makeCylinder(r, float(np.linalg.norm(d)), cq.Vector(*a), cq.Vector(*d))
def box(x0, x1, y0, y1, z0, z1): return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))

def preserve():
    a = cq.Assembly(name="NM26_GD_preserve")
    for name, p in pts().items(): a.add(cq.Solid.makeSphere(BALL, cq.Vector(*p)), name=name)
    for i, (p, q, s, role) in enumerate(m.MEMBERS):
        if role in ("Main hoop", "Front hoop"):   # rule-required tubes stay tubes
            a.add(cyl(p, q, m.SIZES[s][0] / 2), name=f"hoop_{role.split()[0].lower()}_{i}")
    return a

def obstacles():
    a = cq.Assembly(name="NM26_GD_obstacles"); r = m.TIRE_OD / 2
    for x, tr, extra in ((m.WHEELBASE, m.TRACK_F, 60.0), (0.0, m.TRACK_R, 30.0)):   # front: steer sweep
        for s in (1, -1):
            zc = s * tr / 2; a.add(cyl((x, r, zc - 140), (x, r, zc + 140), r + extra), name=f"wheel_{'front' if x else 'rear'}_{'R' if s > 0 else 'L'}")
    x0, x1, y0, y1, z0, z1 = P.ENGINE["box"]; zi = m.EM_Z - BALL - 5   # mount balls sit on the engine case: stop the box short of them
    a.add(box(x0, x1, y0, y1, max(z0, -zi), min(z1, zi)), name="engine_envelope")
    zc = m.N["sp_c"][2]   # spool between the carriers, CV shafts outboard of them (carrier balls left free)
    a.add(cyl((0, r, -zc + BALL + 10), (0, r, zc - BALL - 10), 60.0), name="rear_spool")
    for s in (1, -1): a.add(cyl((0, r, s * (zc + BALL + 10)), (0, r, s * (m.TRACK_R / 2 - 150)), 45.0), name=f"rear_cv_shaft_{'R' if s > 0 else 'L'}")
    a.add(cyl((m.HIP[0], m.HIP[1], 0), (m.HEAD[0], m.HEAD[1], 0), 180.0), name="driver_torso")
    a.add(cq.Solid.makeSphere(150.0, cq.Vector(m.HEAD[0], m.HEAD[1], 0)), name="driver_head")
    a.add(box(m.HIP[0], m.X_PEDAL, 210, 560, -175, 175), name="driver_legs_T12")   # T.1.2 350 x 350, above the rack, pedal box and floor
    a.add(box(m.HEAD[0] - 100, m.X_FRONT - 50, m.Y_SIS, 1500, -200, 200), name="cockpit_opening_T11")   # stops short of the front hoop
    return a

def load_cases():
    """[(name, fixed preserve names, {preserve name: force N (x fwd, y up, z right)})]."""
    pp = pts(); key = {tuple(np.round(v, 3)): k for k, v in pp.items()}
    find = lambda p: key[tuple(np.round(np.asarray(p, float), 3))]
    front = [k for k in pp if k.startswith("front_pickup")]; rear = [k for k in pp if k.startswith("rear_pickup")]
    cases = []
    zsep = np.mean([abs(pp[k][2]) for k in front]) * 2; Fv = 1e6 / zsep / 4
    cases.append(("1 torsion 1000 N*m", rear, {k: (0, Fv if pp[k][2] > 0 else -Fv, 0) for k in front}))
    for ax, case, fixed in (("front", "3g bump", rear), ("rear", "corner+brake", front)):
        C, links = L.corner(ax); f = L.link_forces(C, links, L.cases(ax)[case]); F = {}
        for (n, p, q, node), v in zip(links, f):
            u = np.subtract(q, p); u = u / np.linalg.norm(u)
            if n == "pushrod":
                for nd, Fr in rocker.reactions(ax, -v * u)[0].items():
                    k = f"{ax}_rocker_pivot_R" if nd == m.SUSP[ax]["pushrod"][1] else f"{ax}_shock_mount_R"
                    F[k] = tuple(np.add(F.get(k, (0, 0, 0)), Fr))
            else:
                k = find(q); F[k] = tuple(np.add(F.get(k, (0, 0, 0)), -v * u))
        cases.append((f"{'2' if ax == 'front' else '3'} {ax} right wheel {case}", fixed, F))
    cases.append(("4 main hoop roll-over (AF4: 6 kN side, 5 kN aft, 9 kN down)", front + rear,
                  {"hoop_main (top cross)": (-5000.0, -9000.0, 6000.0)}))
    Fh = H.DRIVER_KG * H.CRASH_G * 9.81; F = {}
    for s, side in ((1, "R"), (-1, "L")):
        for nm, node, tgt, frac in (("mount_sb", (m.X_MAIN, m.SHOULDER_BAR_Y, s * m.BELT_Z), (m.SHOULDER[0], m.SHOULDER[1], s * m.BELT_Z), H.SPLIT["shoulder"] / 2),
                                    ("mount_lap", m.N["lap"] if s > 0 else m.mir(m.N["lap"]), (m.HIP[0], m.HIP[1], s * 180.0), H.SPLIT["lap"] / 2)):
            u = np.subtract(tgt, node); F[f"{nm}_{side}"] = tuple(Fh * frac * u / np.linalg.norm(u))
    u = np.subtract((H.BUCKLE[0], H.BUCKLE[1], 0), m.N["as_c"]); F["mount_anti_sub"] = tuple(Fh * H.SPLIT["anti-sub"] * u / np.linalg.norm(u))
    cases.append((f"5 harness {H.CRASH_G:.0f} g crash", front + rear, F))
    return cases

def write():
    OUT.mkdir(exist_ok=True)
    zup(preserve()).save(str(OUT / "NM26_GD_preserve.step")); zup(obstacles()).save(str(OUT / "NM26_GD_obstacles.step"))
    lines = ["# Fusion Generative Design: NM26 frame study (generated by `fusion_gd.py`)", "",
             "Curiosity study: Generative Design grows a solid, not a tube frame, so the result shows where the load paths",
             "want to go. It is not buildable or rules-legal as-is (FSAE F.3 needs tubes of set sizes).", "",
             "## Set-up", "1. Upload both STEP files to the same Fusion folder; insert `NM26_GD_obstacles` into `NM26_GD_preserve`.",
             "   Check the axes first: the main hoop top should sit at Y ≈ " + f"{m.H_MAIN:.0f}" + " mm (X forward from the rear axle, Y up, Z right).",
             "2. Generative Design workspace → **Preserve Geometry**: every body of `NM26_GD_preserve` (balls and hoop tubes).",
             "3. **Obstacle Geometry**: every body of `NM26_GD_obstacles`.",
             "4. Material: Steel AISI 4130 (or plain steel). Objective: minimise mass, safety factor 1.2. Manufacturing: Unrestricted.",
             "5. One load case per section below: **Structural Constraints → Fixed** on the listed balls, **Structural Loads → Force**",
             "   on each ball with the X/Y/Z components in newtons (X forward, Y up, Z right).", ""]
    for name, fixed, F in load_cases():
        lines += [f"## Load case {name}", f"Fixed: {', '.join(sorted(fixed))}", "", "| Preserve body | Fx (fwd) N | Fy (up) N | Fz (right) N |", "|---|---|---|---|"]
        lines += [f"| {k} | {v[0]:.0f} | {v[1]:.0f} | {v[2]:.0f} |" for k, v in sorted(F.items())] + [""]
    lines += ["Load case 4 goes on the main hoop's top tube face. Simplifications: driver and engine are boxes/cylinders;",
              "fixed supports stand in for the inertia relief the Python FEA uses, so stresses near the fixed balls read high."]
    (OUT / "LOADS.md").write_text("\n".join(lines) + "\n")
    return OUT

if __name__ == "__main__":
    lc = load_cases(); assert len(lc) == 5 and all(F for _, _, F in lc), "every load case needs forces"
    clash = [(p.name, o.name) for p in preserve().children for o in obstacles().children if p.obj.intersect(o.obj).Volume() > 1e-3]
    assert not clash, f"Fusion GD rejects preserve/obstacle overlaps: {clash}"
    assert all(k in pts() or k.startswith("hoop") for _, fx, F in lc for k in list(fx) + list(F)), "loads must sit on preserve bodies"
    print(f"wrote {write()}/: {len(pts())} preserve balls + hoops, 5 load cases")
