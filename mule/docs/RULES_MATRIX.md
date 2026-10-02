# NM26 rules matrix: every frame-relevant FSAE 2026 rule and how it is met

Generated 2026-10-01 from the FSAE 2026 rulebook (v1.0), corrected after the 1 Oct audit (statuses now match real checks), sections V.1, F (tube frame), T.1 and T.2. The rule text is
not reproduced (SAE copyright): look the number up in the rulebook. **Every rule is a hard requirement; none is
traded for weight**, and any new frame layout must pass all of them. Status:

- **Automated:** checked by code on every `python report.py` and every GitHub push.
- **Build / inspection:** a fabrication, part-choice or paperwork item to tick off during the build (BUILD_PLAN §3, SES).
- **N/A:** does not apply to this design; the reason is given.

**Totals:** 84 automated, 94 build/inspection items, 45 not applicable, 15 definitions.

| Rule | Topic | Status | Where / note |
|---|---|---|---|
| V.1.1 |  | Automated | frame_rules.py |
| V.1.2 |  | Automated | rule number cited in a check (see REPORT.md) |
| V.1.3.1 | Vehicle Track | Automated | mass.py tilt test (IN.11.2) |
| V.1.3.2 | Vehicle Track | Automated | rule number cited in a check (see REPORT.md) |
| V.1.4.1 |  | Build / inspection |  |
| V.1.4.2 |  | Automated | rule number cited in a check (see REPORT.md) |
| V.1.4.3 |  | Build / inspection |  |
| F.1.1 |  | Definition |  |
| F.1.2 |  | Definition |  |
| F.1.3 |  | Definition |  |
| F.1.4 |  | Definition |  |
| F.1.5 |  | Definition |  |
| F.1.6 |  | Definition |  |
| F.1.7 |  | Definition |  |
| F.1.8 |  | Definition |  |
| F.1.9 |  | Definition |  |
| F.1.10 |  | Definition |  |
| F.1.11 |  | Definition |  |
| F.1.12 |  | Definition |  |
| F.1.14 |  | Definition |  |
| F.1.15 |  | Definition |  |
| F.1.16 |  | Definition |  |
| F.1.17 |  | Automated | frame_rules.py (side-view truss test) |
| F.2.1 | Structural Equivalency Spreadsheet - SES | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.1.1 | Structural Equivalency Spreadsheet - SES | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.1.2 | Structural Equivalency Spreadsheet - SES | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.2 | Structural Documentation | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.2.1 | Structural Documentation | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.3 | Equivalence | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.3.1 | Equivalence | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.3.2 | Equivalence | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.3.3 | Equivalence | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.4 |  | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.2.5 |  | N/A | SES paperwork, submitted with the SES (not geometry) |
| F.3.1 |  | Build / inspection |  |
| F.3.2.1 |  | Automated | frame_rules.py (size per tube job) |
| F.3.3.1 | Non Structural Tubing | Build / inspection |  |
| F.3.3.2 | Non Structural Tubing | Build / inspection |  |
| F.3.4.1 | Steel Tubing and Material | Automated | mule.py |
| F.3.4.3 | Steel Tubing and Material | Build / inspection |  |
| F.3.5 | Aluminum Tubing | N/A | aluminium tubing not used |
| F.3.5.1 | Aluminum Tubing | N/A | aluminium tubing not used |
| F.3.5.2 | Aluminum Tubing | N/A | aluminium tubing not used |
| F.3.5.3 | Aluminum Tubing | N/A | aluminium tubing not used |
| F.5.1.1 | Primary Structure | Build / inspection |  |
| F.5.1.2 | Primary Structure | Build / inspection |  |
| F.5.2.1 | Bent Tubes or Multiple Tubes | Automated | frame_rules.py (bend CLR >= 3 x OD, from fab.CLR_BY_SIZE) |
| F.5.2.2 | Bent Tubes or Multiple Tubes | Build / inspection |  |
| F.5.2.3 | Bent Tubes or Multiple Tubes | Automated | frame_rules.py |
| F.5.2.4 | Bent Tubes or Multiple Tubes | Build / inspection |  |
| F.5.3.1 | Holes and Openings in Regulated Tubing | Build / inspection |  |
| F.5.3.2 | Holes and Openings in Regulated Tubing | Build / inspection |  |
| F.5.3.3 | Holes and Openings in Regulated Tubing | Build / inspection | weld a cap or plug on every open end; fab.py tube_cut_sheet marks them ("cap end"). Corrected 1 Oct 2026: was listed as automated with no check |
| F.5.4.1 |  | Build / inspection |  |
| F.5.4.2 |  | Build / inspection |  |
| F.5.4.3 |  | Build / inspection |  |
| F.5.5 | Bonding in Regulated Structure | N/A | no bonded structure |
| F.5.5.1 | Bonding in Regulated Structure | N/A | no bonded structure |
| F.5.5.2 | Bonding in Regulated Structure | N/A | no bonded structure |
| F.5.5.3 | Bonding in Regulated Structure | N/A | no bonded structure |
| F.5.6.1 | Roll Hoops | Automated | frame_rules.py |
| F.5.6.2 | Roll Hoops | Automated | frame_rules.py |
| F.5.6.3 | Roll Hoops | Automated | frame_rules.py |
| F.5.6.4 | Roll Hoops | Automated | rule number cited in a check (see REPORT.md) |
| F.5.6.6 | Roll Hoops | Automated | rule number cited in a check (see REPORT.md) |
| F.5.7 | Front Hoop | Automated | rule number cited in a check (see REPORT.md) |
| F.5.7.1 | Front Hoop | Automated | frame_rules.py (size) |
| F.5.7.2 | Front Hoop | Build / inspection |  |
| F.5.7.3 | Front Hoop | Automated | frame_rules.py |
| F.5.7.4 | Front Hoop | Automated | rule number cited in a check (see REPORT.md) |
| F.5.7.5 | Front Hoop | Automated | rule number cited in a check (see REPORT.md) |
| F.5.7.6 | Front Hoop | Automated | frame_rules.py |
| F.5.7.7 | Front Hoop | N/A | front hoop is steel |
| F.5.8 | Main Hoop | Automated | rule number cited in a check (see REPORT.md) |
| F.5.8.1 | Main Hoop | Automated | frame_rules.py |
| F.5.8.2 | Main Hoop | Automated | frame_rules.py |
| F.5.8.3 | Main Hoop | Automated | frame_rules.py |
| F.5.8.4 | Main Hoop | Automated | rule number cited in a check (see REPORT.md) |
| F.5.9 | Main Hoop Braces | Automated | rule number cited in a check (see REPORT.md) |
| F.5.9.1 | Main Hoop Braces | Automated | frame_rules.py (size) |
| F.5.9.2 | Main Hoop Braces | Automated | frame_rules.py |
| F.5.9.3 | Main Hoop Braces | Automated | frame_rules.py |
| F.5.9.4 | Main Hoop Braces | Automated | rule number cited in a check (see REPORT.md) |
| F.5.9.5 | Main Hoop Braces | Automated | rule number cited in a check (see REPORT.md) |
| F.5.9.6 | Main Hoop Braces | Automated | frame_rules.py |
| F.5.10 |  | N/A | no head-restraint protection member used |
| F.5.10.1 |  | N/A | no head-restraint protection member used |
| F.5.10.2 |  | N/A | no head-restraint protection member used |
| F.5.11.1 | External Items | Build / inspection |  |
| F.5.11.2 | External Items | Build / inspection |  |
| F.5.11.3 | External Items | Build / inspection |  |
| F.5.11.4 | External Items | Automated | frame_rules.py |
| F.5.11.5 | External Items | Build / inspection |  |
| F.5.12 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.1 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.2 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.3 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.4 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.5 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.6 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.12.7 | Mechanically Attached Roll Hoop Bracing | N/A | roll hoop bracing welded, not bolted |
| F.5.13.1 | Other Bracing Requirements | N/A | braces welded to steel members |
| F.5.13.2 | Other Bracing Requirements | Build / inspection |  |
| F.5.14 |  | Automated | frame_rules.py |
| F.5.15 |  | Build / inspection |  |
| F.5.16 |  | Build / inspection |  |
| F.6.1 |  | Automated | frame_rules.py (size) |
| F.6.2.1 | Front Bulkhead Support | Automated | frame_rules.py (size) |
| F.6.2.2 | Front Bulkhead Support | Build / inspection | bulkhead integration at the weld; fea.py frontal() carries the 95 kN IA peak through it. Corrected 1 Oct 2026: was listed as automated |
| F.6.2.3 | Front Bulkhead Support | Automated | frame_rules.py |
| F.6.2.4 | Front Bulkhead Support | Build / inspection |  |
| F.6.2.5 | Front Bulkhead Support | Build / inspection |  |
| F.6.3 | Front Hoop Bracing | Automated | rule number cited in a check (see REPORT.md) |
| F.6.3.1 | Front Hoop Bracing | Automated | frame_rules.py (size) |
| F.6.3.2 | Front Hoop Bracing | Automated | frame_rules.py |
| F.6.3.3 | Front Hoop Bracing | Automated | frame_rules.py |
| F.6.3.4 | Front Hoop Bracing | Automated | rule number cited in a check (see REPORT.md) |
| F.6.3.5 | Front Hoop Bracing | Automated | frame_rules.py |
| F.6.3.6 | Front Hoop Bracing | Automated | frame_rules.py |
| F.6.4 | Side Impact Structure | Automated | rule number cited in a check (see REPORT.md) |
| F.6.4.1 | Side Impact Structure | Automated | frame_rules.py (size) |
| F.6.4.2 | Side Impact Structure | Build / inspection |  |
| F.6.4.3 | Side Impact Structure | Automated | frame_rules.py |
| F.6.4.5 | Side Impact Structure | Automated | frame_rules.py |
| F.6.4.6 | Side Impact Structure | Automated | frame_rules.py |
| F.6.5 | Shoulder Harness Mounting | Automated | rule number cited in a check (see REPORT.md) |
| F.6.5.1 | Shoulder Harness Mounting | Automated | frame_rules.py |
| F.6.5.2 | Shoulder Harness Mounting | N/A | shoulder bar is straight (frame_rules.py checks it) |
| F.6.5.3 | Shoulder Harness Mounting | Automated | frame_rules.py |
| F.6.6 | Main Hoop Bracing Supports | Automated | rule number cited in a check (see REPORT.md) |
| F.6.6.1 | Main Hoop Bracing Supports | Automated | frame_rules.py (size) |
| F.6.6.2 | Main Hoop Bracing Supports | Automated | frame_rules.py |
| F.6.6.3 | Main Hoop Bracing Supports | Build / inspection |  |
| F.8.1.1 | Requirements | Build / inspection |  |
| F.8.1.2 | Requirements | Build / inspection |  |
| F.8.2.1 | Anti Intrusion Plate - AIP | Build / inspection |  |
| F.8.2.2 | Anti Intrusion Plate - AIP | Build / inspection |  |
| F.8.2.3 | Anti Intrusion Plate - AIP | Build / inspection |  |
| F.8.3 | Composite Anti Intrusion Plate | N/A | steel anti-intrusion plate |
| F.8.3.1 | Composite Anti Intrusion Plate | N/A | steel anti-intrusion plate |
| F.8.3.2 | Composite Anti Intrusion Plate | N/A | steel anti-intrusion plate |
| F.8.4.1 | Impact Attenuator - IA | Build / inspection |  |
| F.8.4.2 | Impact Attenuator - IA | Automated | rule number cited in a check (see REPORT.md) |
| F.8.4.3 | Impact Attenuator - IA | Automated | rule number cited in a check (see REPORT.md) |
| F.8.5.1 | Impact Attenuator Attachment | Build / inspection |  |
| F.8.5.2 | Impact Attenuator Attachment | Build / inspection |  |
| F.8.5.3 | Impact Attenuator Attachment | Build / inspection |  |
| F.8.5.4 | Impact Attenuator Attachment | Build / inspection |  |
| F.8.5.5 | Impact Attenuator Attachment | Build / inspection |  |
| F.8.5.6 | Impact Attenuator Attachment | Automated | rule number cited in a check (see REPORT.md) |
| F.8.5.7 | Impact Attenuator Attachment | Build / inspection |  |
| F.8.6.1 |  | Build / inspection |  |
| F.8.6.2 |  | Build / inspection |  |
| F.8.6.3 |  | Automated | rule number cited in a check (see REPORT.md) |
| F.8.7.1 | Front Impact Verification | Build / inspection |  |
| F.8.7.2 | Front Impact Verification | Automated (load path) + Build | fea.py frontal(): the 95 kN standard-foam IA peak through the front structure, FoS >= 1.0 vs welded UTS (ours); the IA itself is a bought standard part |
| F.8.7.3 | Front Impact Verification | Build / inspection |  |
| F.8.7.4 | Front Impact Verification | Build / inspection |  |
| F.8.7.5 | Front Impact Verification | Build / inspection |  |
| F.8.8.1 | Impact Attenuator Data - IAD | Build / inspection |  |
| F.8.8.3 | Impact Attenuator Data - IAD | Build / inspection |  |
| F.8.8.4 | Impact Attenuator Data - IAD | N/A | standard attenuator |
| F.8.8.5 | Impact Attenuator Data - IAD | Build / inspection |  |
| F.8.8.6 | Impact Attenuator Data - IAD | N/A | standard attenuator |
| F.8.8.7 | Impact Attenuator Data - IAD | N/A | standard attenuator |
| F.8.8.8 | Impact Attenuator Data - IAD | N/A | standard attenuator |
| F.9.1.1 | Location | Build / inspection |  |
| F.9.1.2 | Location | Build / inspection |  |
| F.9.2 |  | Build / inspection |  |
| T.1.1 | Cockpit Opening | Automated | cockpit.py (T.1.1 template) |
| T.1.1.1 | Cockpit Opening | Automated | cockpit.py (T.1.1 template) |
| T.1.1.2 | Cockpit Opening | Automated | cockpit.py (T.1.1 template) |
| T.1.1.3 | Cockpit Opening | Automated | cockpit.py (T.1.1 template) |
| T.1.1.4 | Cockpit Opening | Automated | cockpit.py (T.1.1 template) |
| T.1.2.1 |  | Automated | cockpit.py (T.1.2 template) |
| T.1.2.2 |  | Automated | cockpit.py (T.1.2 template) |
| T.1.2.3 |  | Automated | cockpit.py (T.1.2 template) |
| T.1.3.1 | Driver Protection | Automated | frame_rules.py |
| T.1.3.2 | Driver Protection | Automated | frame_rules.py: estimated 95th-male legs inside the structure in side and front view (added 1 Oct 2026; was missing); confirm on the buck |
| T.1.3.3 | Driver Protection | Build / inspection |  |
| T.1.3.4 | Driver Protection | Build / inspection |  |
| T.1.4.1 | Vehicle Controls | Build / inspection |  |
| T.1.4.2 | Vehicle Controls | Build / inspection |  |
| T.1.4.3 | Vehicle Controls | Build / inspection |  |
| T.1.4.4 | Vehicle Controls | Automated | rule number cited in a check (see REPORT.md) |
| T.1.5.1 | Driver’s Seat | Automated | rule number cited in a check (see REPORT.md) |
| T.1.6.1 | Thermal Protection | Build / inspection |  |
| T.1.6.2 | Thermal Protection | Build / inspection |  |
| T.1.7 | Floor Closeout | Automated | rule number cited in a check (see REPORT.md) |
| T.1.7.1 | Floor Closeout | Build / inspection |  |
| T.1.7.2 | Floor Closeout | Build / inspection |  |
| T.1.7.3 | Floor Closeout | Build / inspection |  |
| T.1.7.4 | Floor Closeout | Build / inspection |  |
| T.1.8.1 | Firewall | Build / inspection |  |
| T.1.8.2 | Firewall | Build / inspection |  |
| T.1.8.3 | Firewall | Build / inspection |  |
| T.1.8.4 | Firewall | N/A | EV only |
| T.1.8.5 | Firewall | N/A | EV only |
| T.1.8.6 | Firewall | Build / inspection |  |
| T.2.1 |  | Automated | rule number cited in a check (see REPORT.md) |
| T.2.2.1 | Harness Specification | Build / inspection |  |
| T.2.2.2 | Harness Specification | Build / inspection |  |
| T.2.2.3 | Harness Specification | Build / inspection |  |
| T.2.2.4 | Harness Specification | Build / inspection |  |
| T.2.2.5 | Harness Specification | Build / inspection |  |
| T.2.2.6 | Harness Specification | Build / inspection |  |
| T.2.3.1 | Harness Requirements | N/A | upright driving position (20°), not reclined |
| T.2.3.2 | Harness Requirements | Build / inspection |  |
| T.2.4 |  | Build / inspection |  |
| T.2.4.1 |  | Build / inspection |  |
| T.2.4.2 |  | Automated | frame_rules.py F.3.2.1 (harness supports in the "harness" category, size B) |
| T.2.4.3 |  | Automated | rule number cited in a check (see REPORT.md) |
| T.2.4.4 |  | Automated | rule number cited in a check (see REPORT.md) |
| T.2.4.5 |  | Build / inspection |  |
| T.2.4.6 |  | Build / inspection |  |
| T.2.5.1 |  | Build / inspection |  |
| T.2.5.2 |  | Build / inspection |  |
| T.2.5.3 |  | Build / inspection |  |
| T.2.5.4 |  | Automated (a) + Build (b) | a: harness.py lap-belt angle; b ("should", 0-75 mm forward of the seat junction): check on the buck |
| T.2.5.5 |  | N/A | upright driving position |
| T.2.5.6 |  | Build / inspection |  |
| T.2.5.7 |  | Build / inspection |  |
| T.2.5.8 |  | Automated | rule number cited in a check (see REPORT.md) |
| T.2.6.1 | Shoulder Harness | Automated | rule number cited in a check (see REPORT.md) |
| T.2.6.2 | Shoulder Harness | Automated | rule number cited in a check (see REPORT.md) |
| T.2.6.3 | Shoulder Harness | Build / inspection |  |
| T.2.7.1 | Anti-Submarine Belt Mounting | Automated | rule number cited in a check (see REPORT.md) |
| T.2.7.2 | Anti-Submarine Belt Mounting | N/A | 5-point harness |
| T.2.7.4 | Anti-Submarine Belt Mounting | Build / inspection |  |
| T.2.7.5 | Anti-Submarine Belt Mounting | Automated | rule number cited in a check (see REPORT.md) |
| T.2.8.1 | Head Restraint | Build / inspection |  |
| T.2.8.2 | Head Restraint | Build / inspection |  |
| T.2.8.3 | Head Restraint | Build / inspection |  |
| T.2.8.4 | Head Restraint | Build / inspection |  |
| T.2.8.5 | Head Restraint | Build / inspection |  |
| T.2.8.6 | Head Restraint | Build / inspection |  |
| T.2.8.7 | Head Restraint | Build / inspection |  |
| T.2.9 |  | Build / inspection |  |
