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
- **Tube:** 4130 normalized, seamless (or 4130 DOM if that is what you stock). **Mill certificates please.** Several sizes sit within 1–3 % of the FSAE minimum section, so we will measure wall thickness on arrival; tube more than 5 % under nominal wall can't be used.
- **Process:** TIG, **ER70S-2 filler, no post-weld heat treatment.** Our roll-hoop strength calculation assumes exactly this (welds at 85 % of the filler minimums), so please tell us before changing filler or process.
- **Other steel:** if 1020 DOM would be much cheaper or easier for you, say so with a price, but quote 4130 first. The strength calculation would have to be redone for 1020 before we could accept it.
- **Tabs:** 1/8" (3.2 mm) plate, 34 × 26 mm blanks, welded in pairs (double shear); the CAD shows them as 3 mm. Hole sizes to suit the rod ends; we'll confirm.
- **Open ends:** every square-cut end in the cut sheet ("cap end") gets a welded cap or plug (FSAE F.5.3.3). Hoop legs and some posts run 15–20 mm past their joint so the tubes coped onto them land fully on tube.
- **Hoop corners:** the jig coordinates for the hoop corners are points on the bent tube; tubes meeting there weld to the bend.
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
