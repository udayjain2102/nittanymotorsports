# Design history

What changed between each version, tube by tube, and which Fusion file shows which frame: [`mule/docs/VERSIONS.md`](../mule/docs/VERSIONS.md).

One folder per frame version: the whole `mule/` folder (scripts, CAD, shop data, quote, docs) exactly as it was,
frozen with `python mule/snapshot.py <name> <commit>`. Each folder's `SNAPSHOT.md` gives the commit and date, and the git
tag with the same name points at it. Nothing here is edited or deleted.

| Folder | Frame | Pieces | Torsion (FEA) | What changed |
|---|---|---|---|---|
| `frame_v1_50.1kg` | 50.1 kg | 81 | — | First complete rules-checked frame (tag `frame-v1-50kg`) |
| `frame_v2_46.4kg` | 46.4 kg | 78 | 2004 N·m/deg | Optimised tube sizes, robustness fix, AF4 roll-over correction (1 Oct 2026) |
| `frame_v3_44.3kg` | 44.3 kg | 73 | 1946 N·m/deg | C2: rear wishbone pickups on rail nodes, rear posts no longer bend (1 Oct 2026) |
| `frame_v4_50.4kg` | 50.4 kg | 73 | 2422 N·m/deg | Audit fixes (2 Oct 2026): F.5.2.3/F.5.6.3 geometry, frontal 95 kN, buckling, 100 kg harness driver, fresh tolerance samples; wing not fitted |
| `frame_v5_49.4kg` | 49.4 kg | 71 | 2399 N·m/deg | Topology study (10 Oct 2026): FBH front-bay diagonal and upper spool post removed; four new frame checks; current design |
