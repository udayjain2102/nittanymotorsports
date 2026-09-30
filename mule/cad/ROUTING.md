# NM26 routing: brake lines, throttle cable, fuel line, 12 V harness

Rough runs along the frame, from the real component positions (`brakes.geometry`, `shutdown.LOC`, `uprights.geom`). Axes X forward, Y up, Z right (driver's right), mm. The same runs are the `08_routing` parts in `NM26_Assembly.step`.

| Run | What | Waypoints (x, y, z) |
|---|---|---|
| `brake_line_front_MC_to_tee` | 3/16 in hard brake line, front master cylinder to the front tee under the bulkhead | (2085, 174, -70) -> (2115, 174, -70) -> (2090, 174, -70) -> (2090, 120, 0) |
| `brake_line_front_R` | front right brake line: hard line along the lower bulkhead support, braided flexible hose over the wishbone to the caliper | (2090, 120, 0) -> (2090, 120, 160) -> (1630, 110, 200) -> (1630, 200, 300) -> (1710, 368, 633) |
| `brake_line_front_L` | front left brake line: hard line along the lower bulkhead support, braided flexible hose over the wishbone to the caliper | (2090, 120, 0) -> (2090, 120, -160) -> (1630, 110, -200) -> (1630, 200, -300) -> (1710, 368, -633) |
| `brake_line_rear_MC_to_tee` | 3/16 in hard brake line, rear master cylinder along the left lower side-impact rail to the rear tee at the spool posts (brake-light pressure switch at the MC end) | (2085, 174, -20) -> (2115, 174, -20) -> (2115, 110, -20) -> (1630, 110, -204) -> (1321, 89, -276) -> (1126, 89, -276) -> (914, 89, -276) -> (520, 89, -276) -> (200, 103, -240) -> (0, 112, -218) -> (0, 136, 0) |
| `brake_line_rear_R` | rear right brake line: up the spool carrier post, flexible hose along the upper wishbone to the caliper | (0, 136, 0) -> (0, 136, 214) -> (0, 210, 214) -> (-60, 330, 330) -> (-40, 368, 633) |
| `brake_line_rear_L` | rear left brake line: up the spool carrier post, flexible hose along the upper wishbone to the caliper | (0, 136, 0) -> (0, 136, -214) -> (0, 210, -214) -> (-60, 330, -330) -> (-40, 368, -633) |
| `throttle_cable` | mechanical throttle cable (IC.3.3), pedal to the throttle-body drum, along the right lower rail and through the right firewall grommet | (1911, 277, 65) -> (1861, 130, 65) -> (1630, 110, 204) -> (1321, 89, 276) -> (540, 89, 276) -> (490, 420, 100) -> (460, 440, 60) -> (275, 460, -46) -> (245, 462, -38) |
| `fuel_line` | 8 mm fuel hose, in-tank pump outlet to the injector (fuel cell sits above the engine; return-less) | (392, 468, -30) -> (372, 455, -40) -> (285, 496, -30) -> (245, 496, 0) |
| `wire_battery_to_primary_master_switch` | 4 AWG wire, battery to primary master switch, routed along the frame (shutdown.py netlist) | (580, 150, 120) -> (580, 210, 120) -> (530, 210, 306) -> (530, 665, 306) -> (560, 665, 332) |
| `wire_primary_master_switch_to_e-stop` | 18 AWG wire, primary master switch to e-stop, routed along the frame (shutdown.py netlist) | (560, 665, 332) -> (530, 381, 306) -> (530, 381, 278) -> (1321, 381, 278) -> (1301, 480, 200) -> (1286, 525, 180) |
| `wire_e-stop_to_bots` | 18 AWG wire, e-stop to bots, routed along the frame (shutdown.py netlist) | (1286, 525, 180) -> (1301, 480, -200) -> (1321, 110, -276) -> (1630, 110, -220) -> (1981, 110, -45) -> (1981, 200, -45) |
| `wire_bots_to_inertia_switch` | 18 AWG wire, bots to inertia switch, routed along the frame (shutdown.py netlist) | (1981, 200, -45) -> (1981, 95, 0) -> (720, 95, 0) -> (720, 150, 0) |
| `wire_inertia_switch_to_kill_relay` | 18 AWG wire, inertia switch to kill relay, routed along the frame (shutdown.py netlist) | (720, 150, 0) -> (680, 95, 60) -> (600, 95, 150) -> (600, 200, 150) |
| `wire_primary_master_switch_to_kill_relay` | 12 AWG wire, primary master switch to kill relay, routed along the frame (shutdown.py netlist) | (560, 665, 332) -> (530, 400, 306) -> (560, 300, 200) -> (600, 200, 150) |
| `wire_kill_relay_to_fuel_pump` | 16 AWG wire, kill relay to fuel pump, routed along the frame (shutdown.py netlist) | (600, 200, 150) -> (500, 200, 100) -> (460, 420, 100) -> (420, 470, 40) -> (392, 478, 20) |
| `wire_kill_relay_to_ignition-ECU` | 16 AWG wire, kill relay to ignition/ECU, routed along the frame (shutdown.py netlist) | (600, 200, 150) -> (500, 200, 100) -> (460, 420, 100) -> (420, 450, 150) -> (300, 450, 150) |
| `wire_ignition-ECU_to_coil` | signal / ground wire, ignition/ECU to coil, routed along the frame (shutdown.py netlist) | (300, 450, 150) -> (360, 450, 120) -> (505, 440, 40) -> (505, 440, 0) |
| `wire_primary_master_switch_to_starter` | 4 AWG wire, primary master switch to starter, routed along the frame (shutdown.py netlist) | (560, 665, 332) -> (530, 300, 306) -> (530, 150, 0) -> (530, 150, -150) -> (330, 240, -150) |
| `wire_primary_master_switch_to_fan` | 14 AWG wire, primary master switch to fan, routed along the frame (shutdown.py netlist) | (560, 665, 332) -> (530, 400, 306) -> (670, 350, 200) |
| `wire_primary_master_switch_to_brake_light` | 18 AWG wire, primary master switch to brake light, routed along the frame (shutdown.py netlist) | (560, 665, 332) -> (530, 381, 306) -> (530, 520, 150) -> (500, 520, 0) |
| `wire_primary_master_switch_to_DRS_servo` | 16 AWG wire, primary master switch to DRS servo, routed along the frame (shutdown.py netlist) | (560, 665, 332) -> (530, 1000, 306) -> (530, 1260, 140) -> (-300, 370, 184) -> (-340, 970, 30) -> (-380, 1030, 0) |
| `wire_dash_DRS_button_to_ignition-ECU` | signal / ground wire, dash DRS button to ignition/ECU, routed along the frame (shutdown.py netlist) | (1301, 515, -70) -> (1301, 480, -200) -> (1321, 381, -278) -> (530, 381, -278) -> (460, 420, -100) -> (300, 450, -150) -> (300, 450, 150) |
| `wire_battery_to_chassis_ground` | signal / ground wire, battery to chassis ground, routed along the frame (shutdown.py netlist) | (580, 150, 120) -> (580, 90, 120) -> (520, 87, 130) |
