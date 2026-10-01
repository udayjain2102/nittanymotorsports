"""Frame quote package for the shop: frame-weldment STEP + material list + shop data, in quote/.

The shop quotes building the frame in house from a material list and a CAD file. This collects both, plus the cut
sheet, hoop bend programs and jig data, from the same model as everything else. Re-run after any frame change.
Run: python quote_package.py   (needs cad/parts from cad_parts.py)
"""
import csv, math, pathlib, shutil
import cadquery as cq
import mule as m, fab

HERE = pathlib.Path(__file__).parent; OUT = HERE / "quote"
STICK, KERF, GRIP = 6096.0, 3.0, 50.0       # 20 ft random-length stock, saw kerf, bender grip each end of a hoop (mm)
TAB = dict(t_in=0.125, w=34.0, h=26.0)     # pickup/shock tab plate (cad_parts.pickup_tabs: 3 mm, 34 x 26 mm)

def piece_lengths():
    """{size: [cut length mm, ...]} for every physical piece; hoops use developed length + grip."""
    out = {}
    for p, Lc, (a, b) in fab.cope_ends(fab.pieces()):
        if p["bent"]:
            L = fab.bend_program(p["pts"], fab.CLR_BY_SIZE[p["size"]])[2] + 2 * GRIP
        else:
            L = Lc - (a["long"] if a else 0) - (b["long"] if b else 0)
        out.setdefault(p["size"], []).append(L)
    return out

def sticks(lengths):
    """First-fit decreasing into STICK-long stock with KERF per cut. ponytail: FFD, not optimal; fine for a quote."""
    bins = []
    for L in sorted(lengths, reverse=True):
        for i, used in enumerate(bins):
            if used + L + KERF <= STICK: bins[i] += L + KERF; break
        else: bins.append(L + KERF)
    return len(bins)

def material_rows():
    rows = []
    for sz, Ls in sorted(piece_lengths().items(), key=lambda kv: -m.SIZES[kv[0]][0]):
        od, t = m.SIZES[sz]
        rows.append(["4130 round tube (normalized)", f'{od / 25.4:.3f}" OD x {t / 25.4:.3f}" wall', len(Ls),
                     f"{sum(Ls) / 1000:.2f}", f"{max(Ls):.0f}", sticks(Ls), f"{sticks(Ls) * STICK / 304.8:.0f} ft"])
    tabs = [r for r in csv.DictReader(open(HERE / "cad" / "NM26_Assembly_parts.csv"))
            if r["sub_assembly"] == "01_frame_weldment" and not r["name"].startswith("tube_")]
    n_plates = 2 * sum("bushing" not in r["name"] for r in tabs); n_bush = sum("bushing" in r["name"] for r in tabs)
    rows.append(["4130 sheet", f'{TAB["t_in"]:.3f}" ({TAB["t_in"] * 25.4:.1f} mm)', n_plates,
                 f"{n_plates * TAB['w'] * TAB['h'] / 1e6:.3f} m2 net", f"{TAB['w']:.0f} x {TAB['h']:.0f} mm blanks", "-", '12" x 12" sheet'])
    rows.append(["Steel bar/tube for rocker pivot bushings", '5/8" OD, bore to suit the rocker bolt', n_bush,
                 f"{n_bush * 48 / 1000:.2f}", "48", "-", '1 ft'])
    return rows

def frame_step(path):
    asm = cq.Assembly(name="NM26_Frame_Weldment")
    # only the parts cad_parts.py listed this run: cad/parts/ also keeps files from older frame versions
    files = sorted(HERE / "cad" / "parts" / r["file"] for r in csv.DictReader(open(HERE / "cad" / "NM26_Assembly_parts.csv"))
                   if r["sub_assembly"] == "01_frame_weldment")
    for f in files:
        asm.add(cq.importers.importStep(str(f)), name=f.stem)
    asm.save(str(path))
    return len(files)

def main():
    OUT.mkdir(exist_ok=True)
    n = frame_step(OUT / "NM26_Frame_Weldment.step")
    rows = material_rows()
    with open(OUT / "material_list.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["material", "size", "pieces", "total cut length m", "longest piece mm", "20 ft sticks", "order"])
        w.writerows(rows)
    for src in ("tube_cut_sheet.csv", "hoop_bend_program.csv", "jig_node_coordinates.csv", "jig_plan.png"):
        shutil.copy(HERE / "fab" / src, OUT / src)
    print(f"wrote quote/: NM26_Frame_Weldment.step ({n} parts), material_list.csv ({len(rows)} lines), shop data")
    return rows, n

if __name__ == "__main__":
    rows, n = main()
    assert n == sum(1 for r in csv.DictReader(open(HERE / "cad" / "NM26_Assembly_parts.csv")) if r["sub_assembly"] == "01_frame_weldment")
    tube_pieces = sum(r[2] for r in rows if r[0].startswith("4130 round"))
    assert tube_pieces == len(fab.pieces()), (tube_pieces, len(fab.pieces()))   # every piece is on the list once
    for r in rows: print(" | ".join(map(str, r)))
