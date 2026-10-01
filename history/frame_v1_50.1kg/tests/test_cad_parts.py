"""cad/ outputs of cad_parts.py: one STEP per part, all listed in NM26_Assembly_parts.csv, unique part numbers, assembly present."""
import csv, pathlib
CAD = pathlib.Path(__file__).parent.parent / "cad"

def test_part_files_match_csv():
    rows = list(csv.DictReader(open(CAD / "NM26_Assembly_parts.csv")))
    assert len(rows) >= 250
    files = {p.name for p in (CAD / "parts").glob("*.step")}
    assert {r["file"] for r in rows} == files
    pns = [r["part_number"] for r in rows]
    assert len(set(pns)) == len(pns)
    assert all(r["file"].startswith(r["part_number"] + "_") for r in rows)
    names = [r["name"] for r in rows]
    assert len(set(names)) == len(names), "two parts share a name"
    assert all(r["contains"] and r["contains"] != r["name"].replace("_", " ") for r in rows), "a part has no description"

def test_assembly_step_has_every_part():
    text = (CAD / "NM26_Assembly.step").read_text(errors="ignore").replace("\n", "").replace(" ", "")   # STEP wraps long strings
    for r in csv.DictReader(open(CAD / "NM26_Assembly_parts.csv")):
        assert f"PRODUCT('{r['part_number']}_{r['name']}'" in text
    for sub in ("01_frame_weldment", "02_corner_front_R", "02_corner_rear_L", "03_cockpit", "04_powertrain", "05_body", "06_electrical", "07_aero"):
        assert f"PRODUCT('{sub}'" in text
