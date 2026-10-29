"""Simulation Execution API Routes."""

import logging
from fastapi import APIRouter, HTTPException
from api.schemas import SimulationRunRequest
from experiments.runner import ExperimentRunner

router = APIRouter(prefix="/simulation", tags=["simulation"])
logger = logging.getLogger(__name__)
runner = ExperimentRunner()


@router.post("/run")
def trigger_simulation(req: SimulationRunRequest):
    """Executes a simulation scenario and returns summary KPIs."""
    try:
        attack = None if req.attack_scenario == "none" else req.attack_scenario
        res = runner.run_scenario(
            controller_type=req.controller,
            attack_scenario=attack,
            episode_length=req.episode_length,
            start_idx=req.start_idx
        )
        return {
            "status": "success",
            "summary": res["summary"],
            "trajectory_points": len(res["trajectory"])
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
