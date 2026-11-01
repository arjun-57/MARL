# Resilient Multi-Agent Energy Management System (Resilient-MAS)

[![Python 3.10 | 3.11](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Pandapower AC-PF](https://img.shields.io/badge/Grid%20Engine-Pandapower%20AC--PF-informational.svg)](https://www.pandapower.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI%20%7C%20Uvicorn-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![Docker Container](https://img.shields.io/badge/Deployment-Docker%20%7C%20Compose-2496ED.svg)](https://www.docker.com/)
[![CI Pipeline](https://img.shields.io/badge/CI-GitHub%20Actions-blueviolet.svg)](https://github.com/arjun-57/MARL/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

An enterprise-grade, cyber-physical multi-agent energy management system for medium-voltage radial distribution networks subjected to False Data Injection (FDI), communication latency, stochastic packet dropouts, and physical equipment disruptions.

The system couples **pandapower AC Power Flow** on the **IEEE 33-Bus radial feeder** with real-world **Ember European Day-Ahead Wholesale Electricity Prices** and **Open Power System Data (OPSD) German Demand and Solar Generation Time Series (50,400 hourly steps)**.

---

## 1. Executive Summary & Problem Formulation

Modern power distribution feeders face severe operational hazards when high penetrations of Distributed Energy Resources (DERs)—such as grid-scale photovoltaics, battery storage, and commercial electric vehicle hubs—are coordinated over insecure or delayed communication channels.

A malicious attacker or faulty telemetry sensor injecting corrupted data can deceive classical centralized controllers into improper dispatch, inducing severe ANSI C84.1 voltage violations, thermal line overloadings, and substantial economic penalties.

### Research & Engineering Objectives
1. **Physical Constraint Enforcement:** Guarantee ANSI C84.1 Range A voltage regulation ($0.90 \le |V_i| \le 1.10\text{ p.u.}$) and inverter nameplate limits under all operating conditions.
2. **Adversarial Resilience:** Detect and isolate False Data Injection (FDI), packet loss (up to 50%), and transmission latencies in real time.
3. **Decentralized Coordination:** Implement a multi-agent consensus protocol with dynamic trust scoring ($T_i \in [0, 1]$) and automatic quarantine ($T_i < 0.40$).
4. **Separation of Concerns:** Maintain an ultra-fast deterministic physics/safety loop while deploying an asynchronous LLM/RAG Copilot for auditable operational intelligence.

---

## 2. Quantified Empirical Benchmarks

The system was evaluated across 4 comparative control paradigms under adverse operational conditions. All metrics were generated from deterministic 168-hour simulation runs using real OPSD load and Ember price signals.

### Benchmark Matrix: False Data Injection (FDI Attack on Solar PV)

| Controller Architecture | Operational Cost (EUR) | ANSI C84.1 Voltage Violations | Net Reward | Performance Degradation |
| :--- | :--- | :--- | :--- | :--- |
| **Centralized Rule Controller** | 10,992.57 EUR | **24 hours** | -11,308.42 | **+14.93%** |
| **Independent MAS (Greedy)** | 9,899.61 EUR | 0 hours | -9,727.54 | +1.63% |
| **Coordinated MAS (Unsecured)**| 9,973.44 EUR | 0 hours | -9,801.37 | +1.66% |
| **Resilient-MAS (Proposed)** | **9,813.83 EUR** | **0 hours** | **-9,641.76** | **0.00% (Resilient)** |

### Performance Findings:
- Under FDI attack, the **Centralized Controller** suffered a **14.93% cost surge** and **24 consecutive hours of severe voltage violations** due to blind trust in spoofed sensor inputs.
- **Resilient-MAS** detected the physical inverter rating violation at control step 1, decayed the agent trust score below the quarantine threshold ($T < 0.40$), and autonomously maintained nominal operations with **0.00% performance degradation** and **zero voltage violations**.

---

## 3. End-to-End System Architecture

```text
+-------------------------------------------------------------------------------+
|                            LAYER 1: DATA INGESTION                            |
|  - Ember European Wholesale Day-Ahead Prices (Hourly UTC DatetimeIndex)       |
|  - OPSD German Demand & Solar Generation Time Series (50,400 hours)           |
|  - DataValidator: Range verification, null imputation, timestamp alignment    |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                      LAYER 2: DISTRIBUTED AGENT MESH                          |
|  Autonomous specialized agents computing localized dispatch proposals:        |
|  - SolarAgent (Bus 18): PV production monitoring & active curtailment         |
|  - BatteryAgent (Bus 14): 2.0 MWh / 0.8 MW BESS state-of-charge management   |
|  - EVAgent (Bus 24): 0.5 MW commercial charging hub scheduling                |
|  - DemandAgent: Feeder-wide load aggregation and demand-response flexibility  |
|  - MarketAgent (Bus 0): Day-ahead electricity arbitrage interface             |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                LAYER 3: ADVERSARIAL COMMUNICATION BUS                         |
|  Simulated message passing with active adversarial injection hooks:           |
|  - False Data Injection (FDI): Sensor spoofing and inverter telemetry bias    |
|  - Communication Delay: 1 to 3 step propagation lag                           |
|  - Packet Loss: 30% to 50% stochastic message dropouts                        |
|  - Agent Crash: Unannounced node hardware failure                             |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|             LAYER 4: CYBER-PHYSICAL SECURITY & TRUST SENTINEL                 |
|  4-Stage Validation Cascade prior to coordinator aggregation:                 |
|  - Stage 1: Physical Bounds Verification (Nameplate ratings, C-rates)         |
|  - Stage 2: Temporal Consistency Check (Ramp-rate limits dP/dt)               |
|  - Stage 3: Cross-Agent & Astronomical Check (Zenith angle solar verification)|
|  - Stage 4: Statistical Anomaly Detection (Rolling Z-score and EWMA)          |
|  - Dynamic Trust Scoring: T_i in [0, 1] with quarantine at T_i < 0.40         |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|              LAYER 5: COORDINATION, SAFETY & POWER FLOW ENGINE                |
|  - CoordinatorAgent: Trust-weighted proposal reconciliation                   |
|  - SafetyAgent: Hard ANSI C84.1 voltage and SOC physical interlocks           |
|  - Pandapower Engine: Full AC Newton-Raphson power flow on IEEE 33-Bus        |
|  - Observability Stack: Real-time telemetry, REST API, and RAG Copilot        |
+-------------------------------------------------------------------------------+
```

---

## 4. Mathematical & Physical Formulations

### 4.1 AC Power Flow Equations (Newton-Raphson)
For each bus $i \in \{0, \dots, 32\}$ in the network:

$$P_i = |V_i| \sum_{j=0}^{32} |V_j| \left( G_{ij} \cos(\theta_i - \theta_j) + B_{ij} \sin(\theta_i - \theta_j) \right)$$

$$Q_i = |V_i| \sum_{j=0}^{32} |V_j| \left( G_{ij} \sin(\theta_i - \theta_j) - B_{ij} \cos(\theta_i - \theta_j) \right)$$

### 4.2 ANSI C84.1 Voltage Regulation Envelope
$$V_{\min} \le |V_i| \le V_{\max}, \quad \forall i \in \{0, \dots, 32\}$$
Where $V_{\min} = 0.90 \text{ p.u.}$ and $V_{\max} = 1.10 \text{ p.u.}$

### 4.3 Dynamic Trust Scoring (EWMA Recurrence)
For each agent $i$ receiving an anomaly penalty $\pi_i(t) \in [0, 1]$:

$$T_i(t+1) = \alpha \cdot T_i(t) + (1 - \alpha) \cdot (1 - \pi_i(t))$$

Where $\alpha = 0.85$. If $T_i(t) < 0.40$, agent $i$ is immediately quarantined and isolated from the dispatch aggregate.

### 4.4 BESS Physical State Transition
$$\text{SOC}(t+1) = \text{SOC}(t) + \frac{P_{\text{bess}}(t) \cdot \eta \cdot \Delta t}{C_{\text{nominal}}}$$

Subject to hard operational boundaries: $\text{SOC} \in [0.10, 0.95]$ and $P_{\text{bess}} \in [-0.8, +0.8] \text{ MW}$.

---

## 5. Feeder Topology Specification (IEEE 33-Bus)

| Asset Name | Bus Index | Base / Nameplate Capacity | Operational Role |
| :--- | :--- | :--- | :--- |
| **Grid Substation (PCC)** | Bus 0 | 12.66 kV Reference (Slack Bus) | Energy import/export with Ember wholesale market |
| **Battery Storage (BESS)** | Bus 14 | 2.0 MWh Capacity, 0.8 MW Power | Peak-shaving, voltage stabilization, arbitrage |
| **Solar PV Plant** | Bus 18 | 1.5 MW Peak Capacity | Renewable generation and reactive voltage support |
| **EV Fleet Charging Hub** | Bus 24 | 0.5 MW Peak Capacity | Managed commercial charging and load curtailment |
| **Distributed Loads** | Buses 1-32 | 3.715 MW active, 2.300 MVAr reactive | Scaled dynamically via OPSD German demand profile |

---

## 6. Repository Structure

```text
MARL/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI test suite & power-flow validation
├── agents/                      # Distributed multi-agent implementations
│   ├── base_agent.py            # Base abstract agent lifecycle & message hooks
│   ├── battery_agent.py         # BESS arbitrage and SOC maintenance logic
│   ├── coordinator_agent.py     # Trust-weighted consensus aggregator
│   ├── demand_agent.py          # Feeder load aggregator and demand response
│   ├── ev_agent.py              # Commercial EV fleet dispatch controller
│   ├── market_agent.py          # Day-ahead wholesale market price interface
│   ├── safety_agent.py          # Deterministic ANSI C84.1 & SOC hard safety clamp
│   ├── solar_agent.py           # Solar PV inverter controller & curtailment
│   └── trust_agent.py           # Agent trust evaluator wrapper
├── api/                         # FastAPI backend service
│   ├── main.py                  # Application entry point, middleware & routing
│   ├── schemas.py               # Pydantic request and response schemas
│   └── routes/                  # Modular endpoint routers
│       ├── agents.py            # Agent trust scores and telemetry status
│       ├── copilot.py           # Operations Copilot RAG chat interface
│       ├── metrics.py           # Trajectory streams and benchmark tables
│       └── simulation.py        # Scenario execution trigger endpoints
├── assets/                      # Physical component models
│   ├── battery.py               # Electrochemical BESS model with degradation
│   ├── ev.py                    # Commercial EV fleet dynamics
│   ├── grid_connection.py       # Substation interconnect impedance & ratings
│   └── solar.py                 # Photovoltaic inverter physical characteristics
├── attacks/                     # Adversarial cyber-physical attack vectors
│   ├── base_attack.py           # Base attack abstraction
│   ├── communication_delay.py   # Latency, packet loss, crash, & combined attacks
│   ├── demand_spike.py          # Physical load surge & solar dropout attacks
│   └── false_data.py            # False Data Injection (FDI) sensor spoofing
├── communication/               # Asynchronous communication bus
│   ├── latency.py               # Propagation delay emulation
│   ├── message.py               # Standardized AgentMessage protocol dataclass
│   ├── message_bus.py           # Simulated message bus with interception hooks
│   └── network_monitor.py       # Bandwidth and message loss monitoring
├── config/                      # Declarative YAML configuration specifications
│   ├── agents.yaml              # Agent parameters and bus mappings
│   ├── attacks.yaml             # Attack vector parameters and injection steps
│   ├── battery.yaml             # BESS physical constants and degradation factors
│   ├── experiments.yaml         # Benchmark scenario runner definitions
│   └── system.yaml              # Global grid and solver settings
├── coordination/                # Control paradigm implementations
│   ├── centralized_controller.py# Classical centralized rule benchmark
│   ├── independent_controller.py# Uncoordinated greedy multi-agent benchmark
│   └── multi_agent_controller.py# Coordinated & Resilient-MAS controllers
├── dashboard/                   # High-performance operations console
│   ├── app.js                   # Chart.js telemetry charts & copilot client
│   ├── index.css                # Enterprise dark-theme design tokens
│   └── index.html               # Real-time grid monitoring dashboard
├── data/                        # Data processing & ETL pipeline
│   ├── build_dataset.py         # End-to-end dataset builder script
│   ├── loaders/                 # Real-world data ingestion loaders
│   │   ├── ember_loader.py      # Ember European wholesale price loader
│   │   ├── opsd_loader.py       # OPSD German demand & solar loader
│   │   └── validator.py         # Timestamp alignment and range validation
│   └── processed/               # Aligned production datasets (tracked)
│       ├── aligned_energy_data.csv
│       ├── germany_load.csv
│       ├── germany_price.csv
│       └── germany_solar.csv
├── docs/                        # Formal engineering & operational documentation
│   ├── ARCHITECTURE.md          # 5-Tier architecture & mathematical derivations
│   ├── DEPLOYMENT.md            # Forward deployed operations runbook
│   ├── FDE_PROFILE_README.md    # Tailored FDE GitHub profile showcase specification
│   └── THREAT_MODEL.md          # Cyber-physical threat model & defense cascade
├── environment/                 # Simulation environment & gym state transitions
│   ├── energy_env.py            # Primary cyber-physical simulation environment
│   ├── profile_mapper.py        # Real-time feeder load and solar profile mapper
│   ├── reward.py                # Multi-objective economic & reliability reward
│   ├── state.py                 # Network state representation vector
│   └── transition.py            # Environmental transition operators
├── evaluation/                  # Metrics aggregation & resilience scoring
│   └── resilience_metrics.py    # Performance degradation & KPI computation
├── experiments/                 # Automated experimental evaluation runner
│   └── runner.py                # 4-Controller x 6-Scenario benchmark orchestrator
├── grid/                        # Pandapower AC power flow integration
│   ├── bus_manager.py           # Bus load and generation setpoint manager
│   ├── constraints.py           # ANSI C84.1 voltage & thermal constraint checker
│   ├── ieee33.py                # IEEE 33-bus standard network constructor
│   ├── line_manager.py          # Branch impedance and thermal loading manager
│   ├── network_builder.py       # DER-augmented feeder network builder
│   └── power_flow.py            # Newton-Raphson AC power flow engine
├── llm/                         # Copilot integration layer
│   ├── base.py                  # Abstract LLM provider interface
│   ├── factory.py               # Provider factory (Gemini, OpenAI, Mock)
│   ├── gemini_provider.py       # Google GenAI provider implementation
│   ├── openai_provider.py       # OpenAI provider implementation
│   ├── prompts.py               # Operator copilot domain system prompts
│   └── tools.py                 # Telemetry inspection & diagnostic tool calls
├── logs/                        # Runtime execution logs (tracked with .gitkeep)
├── rag/                         # Domain-specific retrieval augmented generation
│   ├── documents/               # Curated operational standards & rulebooks
│   │   ├── attack_definitions.md
│   │   ├── battery_rules.md
│   │   ├── ieee33_system.md
│   │   └── safety_rules.md
│   ├── rag_agent.py             # Context synthesis & live telemetry fusion
│   └── retriever.py             # In-memory TF-IDF vector document retriever
├── results/                     # Baseline benchmark matrices & trajectories (tracked)
├── security/                    # Cyber-physical security sentinel cascade
│   ├── anomaly_detector.py      # Statistical EWMA and rolling Z-score detector
│   ├── consistency_checker.py   # Cross-agent & astronomical solar verifier
│   ├── incident_manager.py      # Security incident logging and dispatch
│   ├── physical_checker.py      # Tier 1 physical rating boundary checker
│   ├── temporal_checker.py      # Tier 2 ramp-rate and delta consistency checker
│   └── trust_score.py           # Dynamic EWMA trust engine & quarantine governor
├── tests/                       # Automated Pytest test suite
│   ├── test_agents.py           # Multi-agent proposal and trust decay tests
│   ├── test_battery.py          # Battery electrochemical physical dynamics tests
│   ├── test_data.py             # Data loader integrity and validation tests
│   └── test_grid.py             # IEEE 33-bus AC power flow convergence tests
├── .env.example                 # Environment configuration template
├── .gitignore                   # Production git ignore specification
├── Dockerfile                   # Multi-stage container build definition
├── docker-compose.yml           # Production service composition manifest
├── LICENSE                      # Apache License 2.0
├── pyproject.toml               # PEP 517/621 build and package configuration
├── pytest.ini                   # Pytest test discovery settings
└── requirements.txt             # Pinned production dependencies
```

---

## 7. REST API Reference

The FastAPI backend exposes endpoints for simulation control, telemetry monitoring, and operations copilot interactions:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness and readiness probe for container orchestrators |
| `GET` | `/api/agents/status` | Current trust scores, quarantine states, and dispatch setpoints |
| `GET` | `/api/metrics/summary` | Aggregate KPIs (cost, voltage violations, performance degradation) |
| `GET` | `/api/metrics/trajectory` | Time-series telemetry points for charting (voltages, power, SOC) |
| `GET` | `/api/metrics/benchmark-matrix`| Comparative degradation matrix across all 4 control paradigms |
| `POST` | `/api/simulation/run` | Triggers a fresh simulation run with custom controller and attack parameters |
| `POST` | `/api/copilot/query` | Submits operator questions to the RAG-grounded LLM Copilot |

Interactive Swagger / OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## 8. Quickstart & Deployment Runbook

### Option A: One-Command Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/arjun-57/MARL.git
cd MARL

# Build and start containerized stack
docker compose up --build -d

# Check service health
curl -f http://localhost:8000/health
```
Access the interactive dashboard at `http://localhost:8000`.

---

### Option B: Local Python Virtual Environment

```powershell
# 1. Create and activate a Python 3.11 virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Execute the full test suite
pytest -v

# 4. (Optional) Run the automated benchmark matrix
python -m experiments.runner

# 5. Launch the application server
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 9. Verification & Automated Testing

The platform includes a dedicated test suite verifying power-system convergence, electrochemical battery transitions, data loader integrity, and multi-agent trust decay:

```powershell
pytest -v
```

Expected test execution output:
```text
tests/test_agents.py::test_agent_proposals_and_bus PASSED
tests/test_agents.py::test_safety_agent_overrides PASSED
tests/test_agents.py::test_security_physical_check_fdi PASSED
tests/test_agents.py::test_trust_score_decay_and_quarantine PASSED
tests/test_battery.py::test_battery_charge_discharge PASSED
tests/test_battery.py::test_battery_limits PASSED
tests/test_data.py::test_ember_loader PASSED
tests/test_data.py::test_opsd_loader PASSED
tests/test_data.py::test_data_validator PASSED
tests/test_grid.py::test_ieee33_network_power_flow PASSED

============================== 10 passed in 13.68s ==============================
```

---

## 10. Operations Copilot & Domain RAG

The platform features an integrated **Operations Copilot** powered by Retrieval-Augmented Generation (RAG):
- The LLM is **completely decoupled from the millisecond control loop**, ensuring that physical grid stability is never dependent on model latency or hallucinations.
- Uses local TF-IDF semantic vector indexing over IEEE 33-bus documentation, ANSI standards, battery electrochemical rules, and attack definitions (`rag/documents/*.md`).
- Fuses live telemetry (current bus voltages, active power setpoints, agent trust scores) into prompt context.
- Supports **Google Gemini (`google-genai`)**, **OpenAI (`openai`)**, and a **Deterministic Offline Provider (`mock`)** for air-gapped substation environments.

---

## 11. Forward Deployed Engineering Standards

This repository adheres to production engineering standards required for Forward Deployed Software Engineer (FDE) and Technical Solutions roles:
- **Zero Emojis & Clean Technical Style:** Documentation strictly formatted for enterprise engineering review.
- **Reproducible Empirical Baselines:** All benchmark matrices and trajectory outputs committed and verifiable.
- **Defensive Engineering:** Hardware interlocks and deterministic safety overrides precede software recommendations.
- **Containerized Orchestration:** Production multi-stage Dockerfile and Docker Compose manifests included.
- **Automated CI/CD:** GitHub Actions workflows executing test validation and power-flow convergence checks.

---

## 12. License & Attribution

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.

Developed and maintained by **Arjun R** ([@arjun-57](https://github.com/arjun-57)). For technical inquiries or enterprise deployment questions, contact `arjunr3773@gmail.com`.
