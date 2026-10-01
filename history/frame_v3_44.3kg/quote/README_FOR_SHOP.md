# NM26 frame: request for quote

Nittany Motorsports NM26 test car ("mule"), a Formula SAE-style tube frame. Please quote building the welded frame.

## What's in this folder
| File | Contents |
|---|---|
| `NM26_Frame_Weldment.step` | The frame as built: every tube and tab as a separate named part, in final position. Units mm, Z up, X forward from the rear axle centreline, origin at ground level on the car centreline. |
| `material_list.csv` | Raw material: tube by size (piece count, total cut length, longest piece, 20 ft sticks), tab plate, bushing bar. **Stick counts are minimums; please add 15–25 % for notching scrap and mistakes.** |
| `tube_cut_sheet.csv` | Every straight piece: size, cut length (long point to long point), the tube each end copes onto, cope angle, notch phase. |
| `hoop_bend_program.csv` | Feed / rotation / bend (Y-B-C) programs for the two roll hoops (main 1.5" × 0.095", front 1.25" × 0.095", CLR as listed). |
| `jig_node_coordinates.csv`, `jig_plan.png` | Coordinates of every joint above a flat table, for the fixture. |

## Specification
- **Tube:** 4130 normalized, seamless or DOM. **Please also quote 1020 DOM** in the same sizes. The FSAE rules credit both steels with the same strength, so the choice comes down to cost and weldability.
- **Process:** TIG preferred. Filler and procedure at the shop's recommendation for the steel chosen.
- **Tabs:** 1/8" (3.2 mm) plate, 34 × 26 mm blanks, welded in pairs (double shear). Hole sizes to suit the rod ends; we'll confirm.
- **Tolerance:** suspension pickup tabs ±1 mm to the coordinates; other joints ±2 mm.

## Please quote separately
1. Material (each steel).
2. Cutting and notching.
3. Hoop bending (or say if we should get the two hoops bent elsewhere).
4. Jig / fixture.
5. Welding and tab installation.
6. Lead time.

## Not final yet
This quote is preliminary. Before we order:
- the engine-mount tabs will be added once the engine (Honda CRF450R) is measured;
- harness, seat, pedal-box and firewall tabs will be added;
- the layout may change slightly after a full-size driver mock-up.

The frame mass is about 44 kg of tube plus about 4 kg of tabs and weld.
