# Architecture Specification: Resilient-MAS

## 1. System Overview

Resilient-MAS is an enterprise-grade Cyber-Physical Multi-Agent Energy Management System designed for radial electrical distribution networks subjected to cyber-physical threats, false data injection (FDI), communication latency, and packet loss.

The platform couples distributed multi-agent consensus with physics-based AC power flow simulation using pandapower on an IEEE 33-bus medium-voltage feeder.

---

## 2. Five-Tier System Architecture

```text
+-------------------------------------------------------------------------------+
|                             TIER 1: PHYSICAL LAYER                            |
|  IEEE 33-Bus Radial Feeder (12.66 kV)                                         |
|  - Substation Point of Common Coupling (PCC, Bus 0)                           |
|  - Distributed Energy Resources (DERs):                                       |
|      * Solar Photovoltaic Plant: 1.5 MW Peak (Bus 18)                         |
|      * Battery Energy Storage System (BESS): 2.0 MWh / 0.8 MW (Bus 14)        |
|      * Commercial EV Fleet Hub: 0.5 MW Peak (Bus 24)                          |
|      * 32 Distributed Active Loads scaled from real OPSD German demand profile|
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       TIER 2: DISTRIBUTED AGENT MESH                          |
|  Autonomous agents with localized state perception:                           |
|  - SolarAgent (Bus 18): Local irradiance monitoring and active curtailment     |
|  - BatteryAgent (Bus 14): State of Charge (SOC) tracking and arbitrage logic  |
|  - EVAgent (Bus 24): Fleet charging scheduling and peak-shaving dispatch      |
|  - DemandAgent: Feeder-wide load monitoring and demand-response flexibility   |
|  - MarketAgent (Bus 0): Ember European day-ahead wholesale price interface    |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                   TIER 3: ADVERSARIAL COMMUNICATION BUS                       |
|  Simulated message passing with configurable adversarial hooks:               |
|  - False Data Injection (FDI): Arbitrary injection and sensor spoofing        |
|  - Propagation Delay: 1-3 step communication latency                          |
|  - Packet Drop: Stochastic message discard (30% to 50% loss rates)            |
|  - Agent Crash: Hardware dropouts and unannounced silent failures             |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|               TIER 4: CYBER-PHYSICAL SECURITY & TRUST SENTINEL                |
|  4-Stage Validation Cascade prior to coordinator action aggregation:          |
|  - Stage 1: Physical Bounds Verification (Nameplate ratings, C-rates)         |
|  - Stage 2: Temporal Consistency Check (Ramp-rate limits dP/dt)               |
|  - Stage 3: Cross-Agent & Astronomical Check (Solar radiation vs. time of day)|
|  - Stage 4: Statistical Anomaly Detection (Rolling Z-score and EWMA)          |
|  - Dynamic Trust Scoring: T_i in [0, 1] with quarantine threshold at T < 0.40 |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                   TIER 5: COORDINATION & SAFETY INTERLOCKS                    |
|  - CoordinatorAgent: Trust-weighted aggregation of agent proposals            |
|  - SafetyAgent: Hard ANSI C84.1 voltage and BESS SOC boundary enforcement     |
|  - Pandapower Engine: Exact Newton-Raphson AC power flow solution             |
|  - Operations Copilot: RAG-grounded telemetry interpretation and reasoning   |
+-------------------------------------------------------------------------------+
```

---

## 3. Mathematical Formulations

### 3.1 AC Power Flow Equations (Newton-Raphson)

For each bus $i \in \{0, \dots, N-1\}$ in the $N$-bus network:

$$P_i = |V_i| \sum_{j=1}^N |V_j| \left( G_{ij} \cos(\theta_i - \theta_j) + B_{ij} \sin(\theta_i - \theta_j) \right)$$

$$Q_i = |V_i| \sum_{j=1}^N |V_j| \left( G_{ij} \sin(\theta_i - \theta_j) - B_{ij} \cos(\theta_i - \theta_j) \right)$$

Where:
- $V_i = |V_i| e^{j \theta_i}$ is the complex bus voltage.
- $Y_{ij} = G_{ij} + j B_{ij}$ is the network nodal admittance matrix.
- $P_i, Q_i$ are net active and reactive power injections at bus $i$.

### 3.2 Physical Constraint Bounds (ANSI C84.1)

All network buses must operate within the strict ANSI C84.1 Range A voltage envelope:

$$V_{\min} \le |V_i| \le V_{\max}, \quad \forall i \in \{0, \dots, 32\}$$

Where:
- $V_{\min} = 0.90 \text{ p.u.}$ (Severe undervoltage threshold)
- $V_{\max} = 1.10 \text{ p.u.}$ (Severe overvoltage threshold)
- Nominal operational band: $[0.95, 1.05] \text{ p.u.}$

Branch thermal loading constraint:

$$S_{l} \le S_{l,\max}, \quad \forall l \in \text{Lines}$$

### 3.3 Dynamic Trust Engine Formulation

Each agent $i$ maintains a time-varying trust score $T_i(t) \in [0.0, 1.0]$, initialized at $T_i(0) = 1.0$.

When an agent transmits telemetry or an action proposal, it is evaluated across the 4-tier security cascade, producing an aggregated violation penalty $\pi_i(t) \in [0, 1]$.

The trust score updates according to an Exponentially Weighted Moving Average (EWMA):

$$T_i(t+1) = \alpha \cdot T_i(t) + (1 - \alpha) \cdot (1 - \pi_i(t))$$

Where:
- $\alpha = 0.85$ is the memory retention factor.
- If $T_i(t) < \theta_{\text{quarantine}} = 0.40$, agent $i$ is immediately quarantined. Its proposals are discarded and substituted with autonomous fail-safe local defaults.

### 3.4 BESS Degradation & Physical Transition

The battery state of charge (SOC) evolves according to:

$$\text{SOC}(t+1) = \text{SOC}(t) + \frac{P_{\text{bess}}(t) \cdot \eta \cdot \Delta t}{C_{\text{nominal}}}$$

Where:
- $\eta = 0.92$ (Charging efficiency), $\eta = \frac{1}{0.92}$ (Discharging efficiency).
- Operating envelope: $\text{SOC} \in [0.10, 0.95]$.
- Active power rating: $P_{\text{bess}} \in [-0.8, +0.8] \text{ MW}$.

Cumulative electrochemical degradation is modeled as:

$$\Delta \text{Degradation} = k_{\text{deg}} \cdot \frac{|P_{\text{bess}}(t)| \cdot \Delta t}{2 \cdot C_{\text{nominal}}}$$

---

## 4. Operational Sequence Flow

```text
Step 1: Ingestion & Environment Step
        Time series inputs (OPSD load profile, solar profile, Ember day-ahead price)
        are sampled for hour t.

Step 2: Agent Proposal Generation
        SolarAgent, BatteryAgent, EVAgent, and DemandAgent compute optimal local
        dispatch proposals based on local state and market signals.

Step 3: Adversarial Bus Transmission
        Proposals pass through the communication bus where attacks (FDI, delay,
        packet drop) may corrupt or intercept payloads.

Step 4: Sentinel Verification & Trust Update
        Security sentinels execute physical, temporal, astronomical, and statistical
        verification checks. Trust scores update via EWMA; compromised agents are quarantined.

Step 5: Trust-Weighted Coordination & Safety Clamping
        Coordinator aggregates proposals weighted by trust scores. SafetyAgent
        verifies that net dispatch preserves ANSI C84.1 voltage bounds and SOC limits.

Step 6: AC Power Flow Execution
        Pandapower solves full Newton-Raphson power flow equations. Voltages, line loadings,
        substation imports, and losses are recorded.

Step 7: Observability & RAG Context Ingestion
        Telemetry is pushed to dashboard websockets/REST endpoints.
        Incident logs are indexed for the Operations Copilot.
```

