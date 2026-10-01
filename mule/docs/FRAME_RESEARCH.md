# Frame redesign research: how lighter FSAE steel frames are built

Compiled 2026-10-01 from web sources (FSAE.com forum archives, team design reports and theses, DesignJudges) and checked
against the 2026 FSAE rulebook. Forum figures are self-reported; treat them as indications, not data.

## The gap
| Frame | Mass | Tube length | kg per m | Source |
|---|---|---|---|---|
| NM26 now | 46.2 kg | ~44 m | ~1.05 | `mule.py` |
| NM26 before 1 Oct | 50.1 kg | 44.8 m | 1.12 | tag `frame-v1-50kg` |
| Univ. of Delaware 2017 (4130) | ~31.8 kg | ~41 m | ~0.78 | [UDel report](https://udel.edu/~pgeneva/downloads/fsae/2017_FSAE_chassis.pdf) |
| Wollongong (4130) | 28–34 kg | — | — | [FSAE forum](http://www.fsae.com/forums/archive/index.php/t-11777.html) |
| UTAS (4130, 450 single) | ~30 kg | — | — | same thread |

Length is similar; **the difference is tube size**. Almost everything on light frames is 1.0" OD at 0.049" (0.74 kg/m).
Our tubes are heavier because loads bend them: suspension pickups sit mid-span on posts.

## Ideas, and how they apply to NM26
1. **Suspension pickups on nodes.** Wishbone axes should pass through frame nodes so loads run along tubes
   ([Rouelle, FSAE forum](http://www.fsae.com/forums/archive/index.php/t-11559.html)). A pickup can slide along its own
   wishbone axis (no kinematic change) until it lands on a node, or get a short diagonal to one
   ([DesignJudges](https://www.designjudges.com/articles/engineering-a-lighter-chassis-part-1)). *NM26: our front and
   rear "suspension ring" posts carry pickups mid-span; this is the main redesign.*
2. **Close the front ring.** T.1.2.2: the leg template only travels to 100 mm behind the rearmost pedal face (verified in
   the 2026 rules). A top cross is legal ahead of that. UWA, with the same problem, surrounded the open node with members
   instead ([Waterman 2011](https://robotics.ee.uwa.edu.au/theses/2011-REV-SAE-SpaceFrame-Waterman.pdf)). *NM26: pedal
   face ≈ x 1921, so a cross is legal ahead of ~1821; the ring is at 1630.*
3. **No separate rear box.** Hang the rear pickups and spool carriers on the main-hoop-brace-support triangles and a short
   rear bulkhead ([FSAE forum](https://www.fsae.com/forums/archive/index.php/t-1646.html)). Brace supports must stay
   triangulated tube (F.6.6).
4. **Rule-minimum hoops and shoulder bar** (1.0" × 0.095", Size A) once the load paths are fixed. 2026 allows the main hoop
   braces to cope to a bent shoulder bar, braced at the bends (F.6.5.2) ([DesignJudges 2026 changes](https://www.designjudges.com/articles/guide-to-2026-frame-rule-changes)).
   Put harness tabs at nodes; harness loads exceed suspension loads.
5. **Everything non-regulated at 1.0" × 0.049"** (or 0.035"), mass budget ~0.75 kg/m; target torsion ~2000 N·m/deg hub to hub.

## Steel
Rules credit any steel with the same strength (F.3.4.2), so 4130 earns no smaller tubes. Teams pick it for thin-wall
availability and modest cost (~$350 of tube); 1020 DOM works for the regulated sizes. Weld 4130 with ER70S-2
([FSAE forum](http://www.fsae.com/forums/archive/index.php/t-5164.html)).

## Fabrication
Laser-cut tube kits ran $1,000–3,000 per frame; still use a fixture plate, not tabs alone
([FSAE forum](https://www.fsae.com/forums/archive/index.php/t-5646.html)). Bent tubes need a support at the point of
maximum deviation of the same size (F.5.2.3), so bends rarely save mass outside the hoops and shoulder bar.

## Don'ts (2026 rules and lessons)
- No engine or suspension mounts on the main hoop or its braces above other nodes (F.5.11.4).
- Welded inserts must be thicker and smaller in diameter than the tube (F.3.4.3).
- A roll-hoop bend below the braces must be triangulated at a node (F.5.6.3).
- Cracks start at the heat-affected zone of welded mounts on thin tube; one team fixed it by stress relieving
  ([FSAE forum](http://www.fsae.com/forums/archive/index.php/t-12192.html)).
- FEA torsion numbers are optimistic; measure hub to hub.

## From the three reference reports (re-read 2026-10-01)
- **Trinity University 2020 final design report** (built and drove its car): the welds of *component mounts* on the
  frame (suspension mounts) looked fatigue-prone, not the frame joints themselves. The steering rack mounts had to be
  moved after the build because the steering wheel ended up above the front hoop (F.5.7.4). *For the redesign: put tabs
  at nodes, and check the wheel height against the front hoop in the layout, not after welding.*
- **JCU 2020 rear suspension paper:** mild steel is easier to weld; 4130 gets no smaller tubes under the rules and
  weakens when welded; small quantities may need shipping. Same conclusion as the steel note above.
- **NAU 2025 suspension report:** pickup points are a joint decision of the frame and suspension teams; its roll
  stiffness method (K = 2·k·MR²·t²/2 per axle) applied to NM26 gives ~476 N·m/deg total (242 front, 234 rear,
  `roll.py`). The frame (1969 N·m/deg FEA now) is ~4× that. Real frames measure ~⅔ of FEA, so the target is **≥ 1500 FEA and
  ≥ 1000 measured** (2× roll stiffness), see `SIM_TO_REAL.md`.

## Checked and rejected
- "The 20 g harness case is self-imposed and too harsh": ours is 80 kg × 20 g = 15.7 kN total, below the 30 kN the rules
  require across the two shoulder belts for monocoques (F.7.9.1). It stays.

## Deep pass: documented geometry for a clean-sheet frame (2026-10-01)
No public source gives a fully dimensioned single-cylinder steel frame (main-hoop-to-axle distance, rear overhang,
node count). The numbers below are what exists; anything marked *derived* comes from rules and these benchmarks.

| Car | Engine | Frame | Wheelbase / track | Stiffness | Source |
|---|---|---|---|---|---|
| Berkeley B16 | KTM 350 single | 31.8 kg | 1549 / 1143 mm | — | [fsae.studentorg.berkeley.edu/b16](https://fsae.studentorg.berkeley.edu/b16/) |
| Berkeley B14/B15 | 250 single | 33.6 kg | 1524 mm | — | [b14](https://fsae.studentorg.berkeley.edu/b14/) |
| Berkeley B22/B23 | KTM 450 | — | 1575 mm | — | front shocks **direct-acting, no rockers** ([b22](https://fsae.studentorg.berkeley.edu/b22/)) |
| Univ. of Delaware 2017 | — | 31.3 kg **measured**, ~38.7 m tube, $723 steel | 1550–1600 target | FEA 2390–2607, measured 2958 N·m/deg | [UDel report](https://udel.edu/~pgeneva/downloads/fsae/2017_FSAE_chassis.pdf) |
| UTAS | BMW 450 single | ~30 kg (mostly mild steel) | — | — | [FSAE forum](https://www.fsae.com/forums/archive/index.php/t-11669.html) |
| Rouelle, rule of thumb | — | "25–30 kg" | — | "about 1500 N·m/deg" | same thread |

**Ideas worth carrying into concepts:**
- **Spool carrier bolted to the engine case** (two plates with eccentric bearing carriers, ~1.4 kg), so the rear frame
  carries suspension loads only ([Oregon State / GFR report](https://ir.library.oregonstate.edu/downloads/dv13zw278);
  swingarm-pivot differential mounts in [FSAE forum t-8141](https://www.fsae.com/forums/archive/index.php/t-8141.html)).
  *Unverified:* that the CRF450R swingarm pivot passes through the engine case; check when an engine is measured.
- **Main hoop brace foot = upper rear pickup node** (rear box and brace support share nodes).
- **Direct-acting front shocks** (Berkeley B22/B23) remove the front rockers and their mid-tube loads.
- **Bulkhead ≤ 400 × 350 mm** with the standard foam attenuator needs no bulkhead diagonal (F.8.4.3).
- **Unregulated tubes** at 0.625 × 0.049" and 1.0 × 0.035" (UDel); 2026 also lets main hoop braces cope onto a bent
  shoulder bar.
- **Stiffness:** Deakin (SAE 2000-01-3554): frame = 1× roll stiffness passes ~80 % of the load transfer, 2× ~90 %.
  NM26 roll stiffness ~476 N·m/deg, so ≥ ~1000 N·m/deg real (≈1500 FEA) is enough. **Spend stiffness to save mass,
  don't add it.**
- **Cockpit length** (*derived, checked against `mule.py`*): main hoop to bulkhead is 1610 mm; a 13° seat back instead
  of 20° moves the hip ~85 mm rearward and the hip-to-pedal rule is a straight-line distance (~10 mm), so ~100 mm can come out.
- **Fabrication:** a jigged, laser-notched frame took one team ~16 h to weld (forum, self-reported); jigs under $100.

**2027 previews to design for now:** crossed-X braces banned, lateral tubes through regulated tubes banned, welded
inserts welded at both ends, harness mounts on floor tubes.
