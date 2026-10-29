"""Agents & Security Telemetry API Routes."""

from fastapi import APIRouter
from pathlib import Path
import json
import pandas as pd

router = APIRouter(prefix="/agents", tags=["agents"])
results_dir = Path("results")


@router.get("/status")
def get_agents_status(run_id: str = "resilient_false_data"):
    """Returns trust scores and latest operational status of all agents."""
    traj_path = results_dir / f"traj_{run_id}.csv"
    if not traj_path.exists():
        # Fallback default
        return {
            "agents": {
                "solar_agent": {"role": "Photovoltaic generation & inverter", "bus": 18, "trust": 1.0, "status": "nominal"},
                "battery_agent": {"role": "BESS storage & voltage support", "bus": 14, "trust": 1.0, "status": "nominal"},
                "demand_agent": {"role": "Feeder demand response & flexibility", "bus": "all", "trust": 1.0, "status": "nominal"},
                "ev_agent": {"role": "Fleet charging dispatch", "bus": 24, "trust": 1.0, "status": "nominal"},
                "market_agent": {"role": "Day-ahead electricity arbitrage", "bus": 0, "trust": 1.0, "status": "nominal"},
                "coordinator_agent": {"role": "Trust-weighted action reconciliation", "status": "active"},
                "safety_agent": {"role": "Hard ANSI/EN constraint governor", "status": "active"}
            }
        }

    df = pd.read_csv(traj_path)
    latest = df.iloc[-1]
    import ast
    try:
        trust_dict = ast.literal_eval(str(latest.get("trust_scores", "{}")))
    except Exception:
        trust_dict = {"solar_agent": 1.0, "battery_agent": 1.0, "demand_agent": 1.0, "ev_agent": 1.0, "market_agent": 1.0}

    return {
        "run_id": run_id,
        "step": int(latest["step"]),
        "timestamp": str(latest["timestamp"]),
        "agents": {
            "solar_agent": {
                "role": "Solar PV (1.5 MW)",
                "bus": 18,
                "trust": trust_dict.get("solar_agent", 1.0),
                "status": "quarantined" if trust_dict.get("solar_agent", 1.0) < 0.4 else "nominal"
            },
            "battery_agent": {
                "role": "BESS Storage (2.0 MWh / 0.8 MW)",
                "bus": 14,
                "trust": trust_dict.get("battery_agent", 1.0),
                "status": "quarantined" if trust_dict.get("battery_agent", 1.0) < 0.4 else "nominal",
                "soc": float(latest["soc"])
            },
            "demand_agent": {
                "role": "Feeder Demand Response",
                "bus": "all",
                "trust": trust_dict.get("demand_agent", 1.0),
                "status": "nominal"
            },
            "ev_agent": {
                "role": "EV Fleet Hub (0.5 MW)",
                "bus": 24,
                "trust": trust_dict.get("ev_agent", 1.0),
                "status": "nominal"
            },
            "market_agent": {
                "role": "Ember Market Day-Ahead",
                "bus": 0,
                "trust": trust_dict.get("market_agent", 1.0),
                "status": "nominal"
            }
        }
    }
