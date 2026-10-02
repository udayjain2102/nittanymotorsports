# Clean-sheet frame: design spec

Goal: a frame of roughly 34–39 kg (46.2 kg when this was written; the C2 frame was 44.3 kg, and 50.4 kg after the 2 Oct audit gates) that keeps every FSAE 2026 rule and every margin. The user chose
the most open option (2026-10-01): wheelbase, seat angle, rear length and engine position may all change.

## Hard gates (never traded)
A concept counts only if `python report.py` passes **everything**:
- every FSAE frame rule (`frame_rules.py`, `RULES_MATRIX.md`) and every other rule check;
- every strength case at nominal FoS ≥ 1.2 (harness ≥ 1.0 vs welded UTS, wing ≥ 1.5);
- the reality-gap gates in `robustness.py`: every case FoS ≥ 1.0 in all 16 tolerance samples, worst torsion ≥ 2× roll
  stiffness, tilt ≥ 60° with mass errors;
- suspension, steering, cockpit, harness, brake and powertrain checks (re-tuned where pickups move).

## Concepts
| | A. Lightest | B. Balanced (build first) | C. Simplest build |
|---|---|---|---|
| Target frame | ~34 kg | ~36 kg | ~39 kg |
| Pieces | ~75 | ~50–60 | ~60, 2–3 tube sizes |
| Key moves | B, plus unregulated tubes below 1″ where durability allows, shortest cockpit | Pickups on triangulated nodes (front box ahead of the leg template's end, so it can be closed); rear pickups on the main-hoop-brace support triangles; no bending posts | Same topology as B with mostly 1.0″ × 0.065″ tube and square-tube box tops as weld datums |
| Seat back | 13° | 13–15° | 20° (as now) |
| Rear end | short, spool carrier on the engine (needs the measured CRF450R) | as A | spool carrier on frame plates |

## How B is built (one change at a time, each verified by `report.py`)
1. **Front box:** move the front suspension station forward of the T.1.2 template's end (pedal face − 100 mm), slide the
   wishbone pickups along their own axes to it (front-view kinematics unchanged), close it with a top cross, and carry
   the rack on a low cross. Re-design rockers/shock mounts there.
2. **Rear:** rear pickups onto the main-hoop-brace support nodes; drop the separate rear ring posts in bending.
3. **Cockpit:** seat back toward 13–15° to shorten the cockpit; re-check helmet lines, harness angles, templates.
4. **Re-size** with the optimiser (all gates), then piece-count reduction (merge straight runs, bend where a node exists).
5. Compare with today's frame on mass, pieces, margins; the winner replaces `main` and the quote package.

Work happens on git branch `clean-sheet-B` (A and C branch from it). `main` and the shop quote stayed at the 46.2 kg frame
until C2 was chosen and merged (1 Oct 2026, 44.3 kg). Engine mounts stay on the placeholder envelope until a CRF450R is measured.
