# IEEE 33-Bus Radial Distribution System Specification

## Overview
The IEEE 33-bus system (Baran and Wu, 1989) is a standard medium-voltage 12.66 kV radial distribution test network.
Total active baseline load: 3.715 MW.
Total reactive baseline load: 2.300 MVAr.

## Distributed Energy Resource (DER) Placements
1. **Solar PV Generator**: Installed at Bus 18 (feeder end). Rated capacity: 1.5 MW peak. Controllable inverter supporting active power curtailment and reactive power support.
2. **Battery Energy Storage System (BESS)**: Installed at Bus 14 (strategic midpoint). Energy capacity: 2.0 MWh. Inverter rating: 0.8 MW bidirectional (charging/discharging).
3. **Electric Vehicle (EV) Fast Charging Hub**: Installed at Bus 24. 10 x 50 kW charging bays (total station peak 0.5 MW).
4. **Point of Common Coupling (PCC)**: Bus 0 (Substation transformer slack bus). Connects the local distribution microgrid to the high-voltage transmission bulk grid.

## Operational Limits (ANSI C84.1 / EN 50160)
- Nominal voltage band: 0.95 p.u. to 1.05 p.u.
- Emergency critical voltage threshold: 0.90 p.u. (undervoltage blackout risk) to 1.10 p.u. (overvoltage equipment damage).
- Maximum line thermal loading: 100% of nominal rating.
