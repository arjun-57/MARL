# Forward Deployed Engineering Runbook

## 1. Scope & Operations

This document outlines the standard operating procedures for deploying, maintaining, and observing Resilient-MAS in forward deployed enterprise and operational technology (OT) environments.

---

## 2. Prerequisites & Environment

### Hardware Requirements
- **CPU**: 4+ cores (x86_64 or ARM64)
- **RAM**: 8 GB minimum (16 GB recommended for multi-year high-frequency batch simulations)
- **Storage**: 2 GB free disk space

### Software Requirements
- Python 3.10+ or Python 3.11+
- Docker Engine 24.0+ and Docker Compose v2 (for containerized deployments)
- Modern web browser (Chrome, Firefox, Edge, Safari) for interactive operations console

---

## 3. Deployment Modes

### Mode A: Containerized Deployment (Recommended for Forward Deployments)

```bash
# 1. Clone repository
git clone https://github.com/arjun-57/MARL.git
cd MARL

# 2. Configure environment
cp .env.example .env
# Edit .env with your specific API keys or leave mock for offline operation

# 3. Launch service stack
docker compose up --build -d

# 4. Verify service health
curl -f http://localhost:8000/health
```

The service exposes:
- **Operations Console**: `http://localhost:8000/`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Mode B: Bare-Metal / Virtual Environment Deployment

```bash
# 1. Create and activate dedicated virtual environment
python3.11 -m venv .venv
source .venv/bin/activate    # On Windows: .\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Build dataset artifacts (if rebuilding from raw sources)
python -m data.build_dataset

# 4. Run test suite
pytest -v

# 5. Start application server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## 4. Operational Monitoring & Health Checks

### Liveness & Readiness Endpoint
```http
GET /health
```
Expected Response:
```json
{
  "status": "healthy",
  "system": "Resilient-MAS IEEE 33-Bus"
}
```

### Telemetry & Agent Status
```http
GET /api/agents/status?run_id=resilient_false_data
```
Returns live trust scores, quarantine states, and inverter power setpoints for all feeder agents.

### Trajectory Streaming
```http
GET /api/metrics/trajectory?run_id=resilient_false_data&max_points=168
```
Streams time-series records (voltage minima/maxima, active power, BESS SOC, market prices) for dashboard rendering.

---

## 5. Air-Gapped and Offline Operations

Resilient-MAS is designed to function in strictly air-gapped substation environments without public internet access:
- Set `LLM_PROVIDER=mock` in `.env` to enable the deterministic offline Copilot provider.
- All RAG knowledge bases (`rag/documents/*.md`) and TF-IDF vector models execute locally in-memory.
- Pandapower AC power flow equations execute locally with pure NumPy and SciPy solvers.
