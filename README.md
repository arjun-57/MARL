# Resilient Multi-Agent Energy Management System (Resilient-MAS)

A research-grade Cyber-Physical Multi-Agent Energy Management System for radial power distribution systems subjected to False Data Injection (FDI), Communication Latencies, Packet Loss, and Physical Disruptions.

Built with **pandapower AC Power Flow**, **IEEE 33-Bus Feeder**, real-world **Ember European Day-Ahead Wholesale Electricity Prices**, and **Open Power System Data (OPSD) German Demand and Solar Generation Time Series**.

---

## Research Question
> *Can a coordinated multi-agent energy management system maintain economic efficiency, power-system reliability, and safe operation when communication failures, agent dropouts, and false-data injection attacks occur?*

---

## System Architecture

```text
┌────────────────────────────────────────────────────────┐
│                   REAL-WORLD DATASETS                  │
│  Ember (Germany.csv) ──► Market Wholesale Prices       │
│  OPSD (time_series_60min) ──► German Load & Solar PV   │
│  pandapower case33bw() ──► 12.66 kV IEEE 33-Bus Grid   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         DATA PIPELINE & FEEDER PROFILE MAPPER          │
│  • Time Alignment (UTC DatetimeIndex, 50,400 hours)    │
│  • Feeder Load Scaling: L_{bus,i,t} = L_{base} * L_t/L_ref
│  • Feeder Solar Scaling: PV(t) = P_{capacity} * SolarProfile(t)
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            SPECIALIZED MULTI-AGENT LAYER               │
│  • Solar Agent (Bus 18): PV monitoring & curtailment   │
│  • Demand Agent (Global): Feeder load & demand response│
│  • Battery Agent (Bus 14): 2.0 MWh BESS & SOC governor │
│  • EV Agent (Bus 24): Fleet charging hub (0.5 MW)      │
│  • Market Agent (PCC Bus 0): Buy / Sell / Hold arbitrage│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│      COMMUNICATION BUS & ADVERSARIAL ATTACK HOOKS      │
│  • FDI Injection (tampered telemetry & forecasts)      │
│  • Communication Delay (1-3 hours propagation latency) │
│  • Packet Loss (30-50% message discard rate)           │
│  • Agent Failure (hardware dropouts / silent crash)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│      CYBER-PHYSICAL SECURITY & TRUST SENTINEL          │
│  Check 1: Physical Bounds (Inverter & Converter ratings)│
│  Check 2: Temporal Consistency (Ramp rate limits)      │
│  Check 3: Cross-Agent & Astronomical Clock Checks      │
│  Check 4: Rolling Z-Score & EWMA Statistical Detector  │
│  Dynamic Trust Scores: T_i in [0, 1]                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         COORDINATOR & SAFETY ENFORCEMENT               │
│  • Coordinator: Trust-weighted conflict reconciliation │
│  • Safety Agent: Hard ANSI C84.1 voltage (0.90-1.10 pu)│
│    and BESS SOC (0.10-0.95) emergency override         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               PANDAPOWER AC POWER FLOW                 │
│  • Newton-Raphson AC power flow equations              │
│  • Real-time bus voltages, line thermal loadings,      │
│    substation import/export, and active line losses    │
└────────────────────────────────────────────────────────┘
```

---

## Comparative Research Benchmarks

The framework evaluates 4 control paradigms under adverse conditions:
1. **Centralized Rule Controller**: Classical centralized benchmark without multi-agent decomposition or cyber protection.
2. **Independent MAS**: Decentralized agents acting selfishly without coordination or trust verification.
3. **Coordinated MAS**: Cooperative coordinator aggregating proposals without cyber trust checks.
4. **Resilient MAS (Proposed)**: Full 4-tier cyber-physical verification, real-time trust scoring, and safety governors.

### Resilience Metric:
$$\text{Performance Degradation} = \frac{\text{Performance}_{\text{normal}} - \text{Performance}_{\text{attack}}}{|\text{Performance}_{\text{normal}}|}$$

---

## Grid Operations Copilot and Domain RAG

The LLM is **not inside the millisecond control loop**. Instead, it acts as an **Operations & Research Copilot** using domain RAG:
- Answers: *"Why did the system discharge the battery at 18:00?"*
- Answers: *"Why was Solar Agent marked untrusted and discounted?"*
- Cites exact IEEE 33-bus limits, ANSI standards, and attack logs.
- Supports **Google Gemini (`google-genai`)**, **OpenAI (`openai`)**, and a **Deterministic Offline Provider**.

---

## Quickstart Guide

### 1. Prerequisites & Environment Setup
```powershell
# Create Python 3.11 virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (pandapower, scikit-learn, fastapi, numba, etc.)
pip install -r requirements.txt
```

### 2. Build Processed Datasets
```powershell
python -m data.build_dataset
```

### 3. Run Test Suite
```powershell
pytest -v
```

### 4. Execute Benchmark Experiment Matrix
```powershell
python -m experiments.runner
```

### 5. Launch Interactive Dashboard & API
```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your web browser.
