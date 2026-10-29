# Battery Energy Storage System (BESS) Operating Guidelines & Degradation

## Electrochemical Specifications
- Usable Storage Capacity: 2.0 MWh Lithium Iron Phosphate (LFP) chemistry.
- Inverter Max Bidirectional Power: 0.8 MW.
- Round-Trip Efficiency: 90.25% (95% charging efficiency, 95% discharging efficiency).
- Operational SOC Limits: Minimum 10% (0.10) to Maximum 95% (0.95). Target cycling range: 20% to 90%.

## State Transition Equation
\[ SOC_{t+1} = SOC_t + \frac{\eta_c P_c \Delta t}{E_{max}} - \frac{P_d \Delta t}{\eta_d E_{max}} \]

## Economic Dispatch Rules
1. **Voltage Support Priority**: If local bus voltage falls below 0.94 p.u., BESS discharges active power to support feeder voltage regardless of spot market price.
2. **Solar Self-Consumption**: When solar generation exceeds 0.8 MW and SOC < 0.90, BESS absorbs surplus local generation to prevent reverse power flow and overvoltage.
3. **Price Arbitrage**:
   - Charge when wholesale price < 30-35 EUR/MWh.
   - Discharge when wholesale price > 70-75 EUR/MWh.
   - Degradation cost penalty: 25.0 EUR/MWh cycled.
