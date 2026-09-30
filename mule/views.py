"""Three-view PNG of the mule frame from mule.py (tube centrelines, wheels, driver template)."""
import pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import mule as m

COL = {"J": "#4b0000", "H": "#8b0000", "A": "#d62728", "B": "#ff7f0e", "C": "#7f7f7f"}
fig, ax = plt.subplots(1, 3, figsize=(20, 6.5), gridspec_kw={"width_ratios": [2.6, 2.6, 1.2]})
side, top, front = ax
for a, b, s, _ in m.MEMBERS:
    side.plot([a[0], b[0]], [a[1], b[1]], color=COL[s], lw=2)
    top.plot([a[0], b[0]], [a[2], b[2]], color=COL[s], lw=2)
    front.plot([a[2], b[2]], [a[1], b[1]], color=COL[s], lw=2)
r = m.TIRE_OD / 2
for x, tr in [(m.WHEELBASE, m.TRACK_F), (0, m.TRACK_R)]:
    side.add_patch(Circle((x, r), r, fill=False, color="k"))
    for z in (tr / 2, -tr / 2):
        top.add_patch(Rectangle((x - r, z - m.TIRE_W / 2), 2 * r, m.TIRE_W, fill=False, color="k"))
        front.add_patch(Rectangle((z - m.TIRE_W / 2, 0), m.TIRE_W, m.TIRE_OD, fill=False, color="k", ls=":" if x == 0 else "-"))
side.plot([m.X_MAIN, m.X_FRONT], [m.H_MAIN + 12.7, m.H_FRONT + 12.7], "c--", lw=1)
side.add_patch(Circle(m.WHEEL_C, m.WHEEL_DIA / 2, fill=False, color="k", lw=1))
def rect(axis, x0, x1, y0, y1, c, label):
    axis.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True, alpha=.25, color=c))
    axis.text((x0 + x1) / 2, (y0 + y1) / 2, label, ha="center", va="center", fontsize=8)
import powertrain as PT
bx = PT.ENGINE["box"]; rect(side, bx[0], bx[1], bx[2], bx[3], "k", "engine (placeholder)")
cs, r1, ax_, r2 = PT.sprockets()
for c, rr in ((cs, r1), (ax_, r2)): side.add_patch(Circle((c[0], c[1]), rr, fill=False, color="0.2", ls="--"))
for sg in (1, -1): side.plot([cs[0], ax_[0]], [cs[1] + sg * r1, ax_[1] + sg * r2], color="0.2", lw=1)
rect(side, m.X_MAIN - 213, m.X_MAIN - 43, 480, 700, "r", "fuel")
import brakes as BR
g = BR.geometry()
side.plot([g["piv"][0], g["pad"][0]], [g["piv"][1], g["pad"][1]], color="purple", lw=3, label="brake pedal + MCs")
side.plot([g["bar"][0], g["mc_front"]], [g["bar"][1]] * 2, color="purple", lw=5)
rect(side, m.IA[0], m.IA[1], m.IA[2], m.IA[3], "gold", "IA")
rect(side, m.X_REAR, m.X_BH, m.Y_LOW - 12.7 - m.PAN_T, m.Y_LOW - 12.7, "gray", "")
side.axhline(0, color="k", lw=.8)
for axis, t in [(side, "Side (X fwd, Y up)"), (top, "Top (X fwd, Z right)"), (front, "Front (Z, Y)")]:
    axis.set_aspect("equal"); axis.set_title(t); axis.grid(alpha=.3)
side.plot([], [], color=COL["J"], label="1.5x0.095 (front ring posts)"); side.plot([], [], color=COL["H"], label="1.25x0.095 (roll hoops)"); side.plot([], [], color=COL["A"], label="Size A 1.0x0.095 (MH braces, shoulder bar)")
side.plot([], [], color=COL["B"], label="Size B 1.0x0.065 (SIS, bulkhead, braces)")
side.plot([], [], color=COL["C"], label="Size C 1.0x0.049 (supports, cross)")
side.plot([], [], "c--", label="helmet line (F.5.6.4)")
side.legend(loc="upper right", fontsize=8)
fig.suptitle("NM26 FSAE-lite mule - frame layout (mm)")
fig.tight_layout()
fig.savefig(__file__.replace("views.py", "views/mule_3view.png"), dpi=110)

# ---- corner front views: wheel, rim barrel, upright housing, bearings, rotor, hub face, links ----
import uprights as U
fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
for ax, axle in zip(axs, ("front", "rear")):
    g = U.geom(axle); wz = g["W"][2]; r = g["r"]
    ax.add_patch(Rectangle((wz - m.TIRE_W / 2, 0), m.TIRE_W, m.TIRE_OD, fill=False, color="k"))
    ax.add_patch(Rectangle((wz - 90, r - U.RIM_BARREL_R), 180, 2 * U.RIM_BARREL_R, fill=False, ls="--", color="0.5"))
    hr = U.BEARING["D"] / 2 + U.UPRIGHT["wall"]
    ax.add_patch(Rectangle((g["zi"] - U.BEARING["B"] / 2 - 3, r - hr), g["zo"] - g["zi"] + U.BEARING["B"] + 6, 2 * hr, color="0.75"))
    for z in (g["zi"], g["zo"]):
        ax.add_patch(Rectangle((z - U.BEARING["B"] / 2, r - U.BEARING["D"] / 2), U.BEARING["B"], U.BEARING["D"], fill=False, color="b"))
    ax.plot([g["rotor"]] * 2, [r - U.ROTOR_OD / 2, r + U.ROTOR_OD / 2], color="tab:red", lw=3, label="rotor")
    ax.plot([g["face"]] * 2, [r - 65, r + 65], color="k", lw=2, label="hub face")
    for n, p, q, _ in m.susp_links(axle):
        ax.plot([p[2], q[2]], [p[1], q[1]], color="tab:orange" if n == "pushrod" else "tab:blue", lw=1.5)
        ax.plot([p[2], p[2]], [r, p[1]], color="0.4", lw=4, alpha=.5); ax.plot(p[2], p[1], "ko", ms=4)
    ax.set_xlim(wz - 260, wz + 150); ax.set_ylim(-10, 560); ax.set_aspect("equal"); ax.grid(alpha=.3)
    ax.set_title(f"{axle} corner, front view (outboard ->)"); ax.set_xlabel("Z (mm)"); ax.legend(fontsize=7, loc="upper left")
fig.tight_layout(); fig.savefig(__file__.replace("views.py", "views/corners.png"), dpi=110)

# colour key for the 3D model (same table as mule.COLORS)
fig2, axk = plt.subplots(figsize=(9, 0.42 * len(m.COLORS)))
for i, (rgb, name, what) in enumerate(m.COLORS.values()):
    y = len(m.COLORS) - i
    axk.add_patch(plt.Rectangle((0, y - 0.4), 0.6, 0.8, color=rgb, ec="k", lw=0.5))
    axk.text(0.8, y, f"{name}: {what}", va="center", fontsize=8)
axk.set_xlim(0, 12); axk.set_ylim(0.3, len(m.COLORS) + 0.7); axk.axis("off"); axk.set_title("NM26 mule 3D model: colour key")
fig2.tight_layout(); fig2.savefig(pathlib.Path(__file__).parent / "views" / "colour_key.png", dpi=130)
