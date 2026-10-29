"""Metrics, Benchmarks, and Attacks API Routes."""

from fastapi import APIRouter
from pathlib import Path
import json
import pandas as pd

router = APIRouter(prefix="/metrics", tags=["metrics"])
results_dir = Path("results")


@router.get("/summary")
def get_run_summary(run_id: str = "resilient_false_data"):
    """Returns JSON summary of experiment KPIs."""
    summary_path = results_dir / f"summary_{run_id}.json"
    if summary_path.exists():
        with open(summary_path, "r") as f:
            return json.load(f)
    return {"error": f"Run {run_id} not found"}


@router.get("/trajectory")
def get_trajectory(run_id: str = "resilient_false_data", max_points: int = 168):
    """Returns time-series trajectory points for charting."""
    traj_path = results_dir / f"traj_{run_id}.csv"
    if traj_path.exists():
        df = pd.read_csv(traj_path).head(max_points)
        return df.to_dict(orient="records")
    return []


@router.get("/benchmark-matrix")
def get_benchmark_matrix(attack_scenario: str = "false_data"):
    """Returns comparative degradation table across controllers."""
    bench_file = results_dir / f"benchmark_matrix_{attack_scenario}.csv"
    if bench_file.exists():
        df = pd.read_csv(bench_file)
        return df.to_dict(orient="records")
    return []
