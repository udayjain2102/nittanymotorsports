# Design history

One folder per frame version: the whole `mule/` folder (scripts, CAD, shop data, quote, docs) exactly as it was,
frozen with `python mule/snapshot.py <name> <commit>`. Each folder's `SNAPSHOT.md` gives the commit and date, and the git
tag with the same name points at it. Nothing here is edited or deleted.

| Folder | Frame | Pieces | Torsion (FEA) | What changed |
|---|---|---|---|---|
| `frame_v1_50.1kg` | 50.1 kg | 81 | — | First complete rules-checked frame (tag `frame-v1-50kg`) |
| `frame_v2_46.4kg` | 46.4 kg | 78 | 2004 N·m/deg | Optimised tube sizes, robustness fix, AF4 roll-over correction (1 Oct 2026) |
| `frame_v3_44.3kg` | 44.3 kg | 73 | 1946 N·m/deg | C2: rear wishbone pickups on rail nodes, rear posts no longer bend (1 Oct 2026); current design |
