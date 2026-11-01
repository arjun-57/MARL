# Threat Model and Cyber-Physical Security Architecture

## 1. Overview & Threat Landscape

Modern distributed electrical distribution networks rely increasingly on distributed intelligence (DER controllers, smart inverters, BESS management systems). This integration exposes critical infrastructure to sophisticated cyber-physical attack vectors.

This document formalizes the threat taxonomy, adversary capabilities, and defense mechanisms evaluated in Resilient-MAS.

---

## 2. Threat Vector Taxonomy

```text
+---------------------+---------------------------------------------------------+
| Attack Vector       | Operational Description                                 |
+---------------------+---------------------------------------------------------+
| False Data          | Adversary manipulates sensor telemetry or forecasts     |
| Injection (FDI)     | (e.g. inflating solar generation reporting to 3.5 MW on  |
|                     | a 1.5 MW inverter, or spoofing zero demand).            |
+---------------------+---------------------------------------------------------+
| Communication       | Communication channels experience artificial latency    |
| Latency             | of 1-3 control cycles (hours). Decision algorithms act   |
|                     | on outdated state, risking voltage collapse.            |
+---------------------+---------------------------------------------------------+
| Severe Packet Loss  | Stochastic packet drop rate of 30% to 50%, simulating   |
|                     | RF jamming, network congestion, or DDoS on gateways.    |
+---------------------+---------------------------------------------------------+
| Hardware Crash &    | Silent agent disconnect or sudden unannounced hardware   |
| Silent Dropout      | failure without failover signals.                        |
+---------------------+---------------------------------------------------------+
| Multi-Vector        | Simultaneous execution of FDI and network degradation.  |
| Combined Attack     |                                                         |
+---------------------+---------------------------------------------------------+
```

---

## 3. Four-Tier Defense Cascade

To prevent compromised telemetry from influencing grid dispatch, Resilient-MAS deploys a strict 4-tier filtering cascade before the coordinator aggregates proposals:

```text
Proposal Received
       │
       ▼
[ Tier 1: Physical Bounds Check ]
  - Is P_solar within [0, P_max_solar]?
  - Is P_bess within [-P_max_charge, P_max_discharge]?
  - Does BESS requested power violate hardware C-rate?
       │
       ├── Violation ──► Flag Physical Anomaly (Penalty = 0.5 - 1.0)
       ▼
[ Tier 2: Temporal Consistency Check ]
  - Is |P(t) - P(t-1)| / Delta_t <= Ramp_Rate_Max?
  - Does BESS SOC jump without corresponding energy transfer?
       │
       ├── Violation ──► Flag Temporal Anomaly (Penalty = 0.4 - 0.8)
       ▼
[ Tier 3: Cross-Agent & Astronomical Check ]
  - Does solar generation report > 0 at nighttime (Solar Zenith > 90 deg)?
  - Is reported irradiance inconsistent with nearby feeder sensors?
       │
       ├── Violation ──► Flag Cross-Agent Anomaly (Penalty = 0.9)
       ▼
[ Tier 4: Statistical Anomaly Detection ]
  - Rolling Z-Score: |x(t) - mu_rolling| / sigma_rolling > 3.0?
  - Residual EWMA deviation exceedance?
       │
       ├── Violation ──► Flag Statistical Anomaly (Penalty = 0.3 - 0.6)
       ▼
[ Trust Engine Scoring ]
  - Update agent trust score T_i via EWMA.
  - If T_i < 0.40: Quarantine agent, switch to autonomous local fail-safe.
```

---

## 4. Safety Interlock Layer (Hard Physical Guardrails)

The final defense barrier is the `SafetyAgent`. Even if an adversarial proposal bypasses the trust sentinel, the `SafetyAgent` executes a deterministic physical interlock:

1. **Voltage Regulation Bounds (ANSI C84.1)**:
   - If minimum bus voltage $V_{\min} < 0.95 \text{ p.u.}$, battery charging is immediately clamped to 0.0 MW, and EV fleet charging is throttled by 50% to prevent undervoltage tripping.
   - If $V_{\min} < 0.91 \text{ p.u.}$, emergency BESS discharge is forced to inject active power and support feeder voltage.

2. **Electrochemical Limits**:
   - Hard clamp on BESS SOC: Cannot charge when $\text{SOC} \ge 0.95$; cannot discharge when $\text{SOC} \le 0.10$.

---

## 5. Empirical Benchmark Comparison

Under a sustained False Data Injection (FDI) campaign against the Solar PV agent:

```text
+-----------------------+------------------+-------------------+----------------------+
| Controller Paradigm   | Cost (EUR)       | ANSI Violations   | Performance Loss (%) |
+-----------------------+------------------+-------------------+----------------------+
| Centralized Rule      | 10,992.57        | 24 hours          | +14.93%              |
| Independent MAS       | 9,899.61         | 0 hours           | +1.63%               |
| Coordinated MAS       | 9,973.44         | 0 hours           | +1.66%               |
| Resilient-MAS (Ours)  | 9,813.83         | 0 hours           | 0.00% (Resilient)    |
+-----------------------+------------------+-------------------+----------------------+
```

Key Finding:
The Centralized baseline experiences 24 hours of operational violations and a 14.93% cost surge because it blind-trusts corrupted telemetry. Resilient-MAS detects the physical rating violation at Step 1, isolates the agent with an updated trust score ($T < 0.40$), and maintains normal operations with 0.00% performance degradation.
