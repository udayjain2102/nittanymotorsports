"""Freeze one version of the design: copy mule/ as it is at a git commit into ../history/<name>/ (never overwrites).

Run before any change that regenerates CAD, shop data or the quote package, so every build stage stays on file:
    python snapshot.py frame_v3_44.3kg            # the current commit
    python snapshot.py frame_v2_46.4kg 95d2f37    # an older commit or tag
Naming: <what>_v<N>_<key number>, e.g. frame_v2_46.4kg. ../history/<name>/SNAPSHOT.md records the commit and date.
"""
import io, pathlib, subprocess, sys, tarfile

HERE = pathlib.Path(__file__).parent

def snapshot(name, ref="HEAD"):
    out = HERE.parent / "history" / name
    if out.exists(): sys.exit(f"history/{name} already exists; snapshots are never overwritten")
    git = lambda *a: subprocess.run(["git", *a], cwd=HERE.parent, check=True, capture_output=True).stdout
    commit, date, subject = git("log", "-1", "--format=%H%n%ci%n%s", ref).decode().splitlines()
    with tarfile.open(fileobj=io.BytesIO(git("archive", ref, "mule"))) as tar:
        members = tar.getmembers()
        for m in members: m.name = m.name[len("mule/"):]
        members = [m for m in members if m.name]
        tar.extractall(out, members=members, filter="data")
    (out / "SNAPSHOT.md").write_text(f"# {name}\n\nThe `mule/` folder exactly as it was at commit `{commit[:7]}` "
                                     f"({date}): {subject}\n\nFrozen copy for the build record; do not edit. "
                                     f"Regenerating anything here does not change the current design in `mule/`.\n")
    print(f"wrote history/{name}/ ({len(members)} entries) from {commit[:7]}")

if __name__ == "__main__":
    snapshot(*sys.argv[1:3])
