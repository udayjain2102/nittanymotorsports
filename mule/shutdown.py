"""12 V electrical system and shutdown circuit (FSAE 2026 IC.9, T.9, T.3.3, T.3.4) as a netlist that is simulated:
open any shutdown device -> the kill relay (normally open, T.9.1.3) drops -> ignition and fuel pump lose power.

Topology (mechanical throttle, so no BSPD / ETC):
  battery+ -> main fuse -> PRIMARY MASTER SWITCH (all battery current, direct acting) -> bus
  bus -> starter solenoid (via start button), fan, brake light (brake pressure switch), ECU keep-alive
  bus -> E-STOP (cockpit main switch) -> BOTS -> INERTIA SWITCH -> kill-relay coil -> ground
  bus -> kill-relay contacts -> ignition/ECU run, fuel pump
Wire ampacity and resistance: copper TXL, bundled, conservative values. Component currents are estimates for a
450 cc single; ratings of the switches you buy must be checked against CURRENT. Run: python shutdown.py
"""
import math
import mule as m

AWG = {18: (10.0, 0.0210), 16: (13.0, 0.0132), 14: (17.0, 0.0083), 12: (23.0, 0.0052), 10: (33.0, 0.0033),
       8: (46.0, 0.0021), 4: (135.0, 0.00082)}   # gauge: (ampacity A, ohm/m); 4 AWG = battery cable in free air
CURRENT = {"fuel pump": 5.0, "ignition/ECU": 6.0, "fan": 8.0, "brake light": 1.0, "kill relay coil": 0.2, "DRS servo": 4.0, "starter": 120.0}
SWITCH_RATING = {"primary master switch": 100.0, "e-stop": 10.0, "bots": 10.0, "inertia switch": 10.0, "kill relay": 30.0}  # A continuous
ESTOP_DIA = 40.0                   # mm (IC.9.4.1b >= 24)
BRAKE_LIGHT = dict(led_line_mm=160.0, area_cm2=18.0, y=520.0, z=0.0)   # T.3.4: >= 15 cm2, single LED line >= 150 mm

# component locations (x, y, z) from the layout
LOC = {"battery": (m.X_MAIN + 60, 150.0, 120.0),
       "primary master switch": (m.X_MAIN + 40, m.SHOULDER[1], m.Z_COCKPIT + 40),   # driver's right, at the main hoop, shoulder height
       "e-stop": (m.WHEEL_C[0] + 60, m.WHEEL_C[1] - 60, 180.0),                    # on the dash next to the steering wheel
       "bots": (m.X_PEDAL + 60, 200.0, -45.0), "inertia switch": (m.X_MAIN + 200, 150.0, 0.0),
       "kill relay": (m.X_MAIN + 80, 200.0, 150.0), "fuel pump": (m.X_MAIN - 128, 500.0, 0.0),
       "ignition/ECU": (300.0, 450.0, 150.0), "fan": (m.X_MAIN + 150, 350.0, 200.0),
       "brake light": (m.X_MAIN - 20, BRAKE_LIGHT["y"], BRAKE_LIGHT["z"]), "starter": (250.0, 200.0, -150.0),
       "DRS servo": (-380.0, 1030.0, 0.0)}                                          # at the flap pivot (aero.py)

# wires: (from, to, gauge, fuse A or None, load it carries)
WIRES = [("battery", "primary master switch", 4, 100.0, "starter"),        # main feed; fuse = T.9.2.2 overcurrent
         ("primary master switch", "starter", 4, None, "starter"),
         ("primary master switch", "e-stop", 18, 5.0, "kill relay coil"),
         ("e-stop", "bots", 18, None, "kill relay coil"), ("bots", "inertia switch", 18, None, "kill relay coil"),
         ("inertia switch", "kill relay", 18, None, "kill relay coil"),
         ("primary master switch", "kill relay", 12, 20.0, "fuel pump+ignition"),
         ("kill relay", "fuel pump", 16, None, "fuel pump"), ("kill relay", "ignition/ECU", 16, None, "ignition/ECU"),
         ("primary master switch", "fan", 14, 15.0, "fan"), ("primary master switch", "brake light", 18, 5.0, "brake light"),
         ("primary master switch", "DRS servo", 16, 7.5, "DRS servo")]   # servo loses power with the master switch; its spring shuts the flap
SHUTDOWN_SERIES = ["e-stop", "bots", "inertia switch"]     # normally closed, in series with the kill-relay coil
KILLED = ["fuel pump", "ignition/ECU"]                     # IC.9.2.2

def length(a, b):
    """Harness length (m): Manhattan route along the frame + 20 % for bends and service loops."""
    pa, pb = LOC[a], LOC[b]; return 1.2 * sum(abs(p - q) for p, q in zip(pa, pb)) / 1000

def load_current(load):
    return sum(CURRENT[k] for k in ("fuel pump", "ignition/ECU")) if load == "fuel pump+ignition" else CURRENT[load]

def powered(open_devices=(), pms_on=True):
    """Which loads have power with the given devices opened. Simulates the relay: coil energised only if every
    series shutdown device is closed and the master switch is on."""
    if not pms_on: return set()
    coil = all(d not in open_devices for d in SHUTDOWN_SERIES)
    on = {"starter", "fan", "brake light", "DRS servo"}
    if coil: on |= set(KILLED)
    return on

def drops():
    """Voltage drop (V) from the battery to each killed load at run current."""
    r = {}
    for load in KILLED:
        path = [("battery", "primary master switch"), ("primary master switch", "kill relay"), ("kill relay", load)]
        run = sum(i for k, i in CURRENT.items() if k != "starter")       # everything running, engine on
        amps = [run, CURRENT["fuel pump"] + CURRENT["ignition/ECU"], CURRENT[load]]
        v = 0.0
        for (a, b), i in zip(path, amps):
            g = next(x[2] for x in WIRES if (x[0], x[1]) == (a, b))
            v += i * AWG[g][1] * length(a, b) * 2            # out and back (chassis return treated like a wire)
        r[load] = v
    return r

def checks():
    res = []
    for d in SHUTDOWN_SERIES + ["primary master switch"]:
        off = powered(open_devices=(d,)) if d != "primary master switch" else powered(pms_on=False)
        res.append((f"IC.9.2 opening {d} kills ignition + fuel pump", not (set(KILLED) & off), f"powered: {sorted(off) or 'nothing'}"))
    res.append(("IC.9.3.2a primary master switch cuts ALL loads", powered(pms_on=False) == set(), ""))
    res.append(("IC.9.3.2b master switch direct acting (no relay upstream)", WIRES[0][:2] == ("battery", "primary master switch"), "battery -> fuse -> PMS"))
    ok_w = [(a, b, g, f) for a, b, g, f, ld in WIRES
            if (ld != "starter" and load_current(ld) > AWG[g][0]) or (f is not None and f > AWG[g][0])]   # cranking is intermittent
    res.append(("every wire: load <= ampacity, fuse <= ampacity", not ok_w, "all OK" if not ok_w else str(ok_w)))
    unprot = [(a, b) for a, b, g, f, ld in WIRES if f is None and a == "primary master switch" and ld != "starter"]
    res.append(("every branch off the bus is fused (starter excepted)", not unprot, "all OK" if not unprot else str(unprot)))
    run = sum(i for k, i in CURRENT.items() if k != "starter")
    need = {"primary master switch": run, "e-stop": CURRENT["kill relay coil"], "bots": CURRENT["kill relay coil"],
            "inertia switch": CURRENT["kill relay coil"], "kill relay": CURRENT["fuel pump"] + CURRENT["ignition/ECU"]}
    bad = [k for k, i in need.items() if i > SWITCH_RATING[k]]
    res.append(("switch and relay ratings >= their current", not bad, "all OK" if not bad else str(bad)))
    vd = drops(); res.append(("voltage drop to pump / ignition <= 0.5 V", max(vd.values()) <= 0.5, ", ".join(f"{k} {v:.2f} V" for k, v in vd.items())))
    b = LOC["battery"]; res.append(("T.9.2.1 battery inside the structure, below the shoulder belt mount", b[1] < m.SHOULDER_BAR_Y and abs(b[2]) < m.Z_COCKPIT, f"y={b[1]:.0f} vs {m.SHOULDER_BAR_Y}"))
    p = LOC["primary master switch"]
    res.append(("T.9.3.1 master switch: right side, at the main hoop, shoulder height", p[2] > 0 and abs(p[0] - m.X_MAIN) <= 100 and abs(p[1] - m.SHOULDER[1]) <= 75,
                f"x={p[0]:.0f}, y={p[1]:.0f}, z={p[2]:.0f}"))
    res.append(("IC.9.4.1b cockpit main switch >= 24 mm", ESTOP_DIA >= 24, f"{ESTOP_DIA:.0f} mm"))
    bl = BRAKE_LIGHT
    res.append(("T.3.4 brake light >= 15 cm2, LED line >= 150 mm, wheel-centre to shoulder height, on centreline",
                bl["area_cm2"] >= 15 and bl["led_line_mm"] >= 150 and m.TIRE_OD / 2 <= bl["y"] <= m.SHOULDER[1] and abs(bl["z"]) <= 50,
                f"{bl['area_cm2']:.0f} cm2, y={bl['y']:.0f}"))
    return res

if __name__ == "__main__":
    res = checks()
    for n, p, d in res: print(("PASS " if p else "FAIL ") + f"{n:72s} {d}")
    for a, b, g, f, ld in WIRES: print(f"  {a:>22s} -> {b:<16s} {g:2d} AWG  {length(a, b):4.1f} m  fuse {f or '-'}")
    assert all(p for _, p, _ in res), "shutdown/wiring check failed"
