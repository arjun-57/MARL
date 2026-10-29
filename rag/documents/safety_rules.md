# Grid Safety Rules, Constraints, and Emergency Action Matrix

## Constraint Enforcement Hierarchy
The Safety Agent operates as a strict, non-bypassable governor between the multi-agent coordinator and the physical IEEE 33-bus system.

### Decision Actions:
- **ACCEPT**: Control proposals satisfy all physical and electrical constraints without modification.
- **MODIFY**: Control proposals exceed operational limits (e.g. BESS requested 1.2 MW > 0.8 MW max) and are clamped to safe values.
- **REJECT**: Unsafe actions that violate hard physical limits (e.g., attempting to discharge battery when SOC is at or below 10%).
- **EMERGENCY**: Grid is under critical physical stress (voltage < 0.92 p.u. or line loading > 100%). Overrides normal economic dispatch:
  1. Forbids BESS charging.
  2. Throttles EV charging fleet by 50%.
  3. Commands maximum localized active power support.
  4. Curtains solar PV if voltage exceeds 1.08 p.u.
