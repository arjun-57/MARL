"""Read-only operational and research tools callable by the LLM Copilot."""

import json
from pathlib import Path
from typing import Dict, Any, List

class CopilotTools:
    """Provides structured telemetry inspection tools for the LLM Copilot."""

    def __init__(self, results_dir: str = "results", doc_dir: str = "rag/documents"):
        self.results_dir = Path(results_dir)
        self.doc_dir = Path(doc_dir)

    def get_current_state(self, run_id: str = "resilient_false_data") -> Dict[str, Any]:
        """Returns the latest grid telemetry, bus voltages, and load levels."""
        traj_file = self.results_dir / f"traj_{run_id}.csv"
        if not traj_file.exists():
            return {"error": f"No trajectory found for {run_id}"}
        import pandas as pd
        df = pd.read_csv(traj_file)
        latest = df.iloc[-1].to_dict()
        return {"run_id": run_id, "latest_state": latest}

    def get_agent_status(self, run_id: str = "resilient_false_data") -> Dict[str, Any]:
        """Returns active trust scores and quarantine status for all agents."""
        traj_file = self.results_dir / f"traj_{run_id}.csv"
        if not traj_file.exists():
            return {"solar_agent": 1.0, "battery_agent": 1.0, "demand_agent": 1.0, "market_agent": 1.0}
        import pandas as pd
        df = pd.read_csv(traj_file)
        latest = df.iloc[-1]
        trust_str = str(latest.get("trust_scores", "{}"))
        return {"run_id": run_id, "step": int(latest["step"]), "trust_status": trust_str}

    def get_attack_log(self, run_id: str = "resilient_false_data") -> Dict[str, Any]:
        """Returns summary of attacks and security anomalies detected during the run."""
        summary_file = self.results_dir / f"summary_{run_id}.json"
        if summary_file.exists():
            with open(summary_file, "r") as f:
                data = json.load(f)
            return {"scenario": data.get("attack_scenario"), "controller": data.get("controller")}
        return {"status": "No incidents logged"}

    def get_energy_metrics(self, run_id: str = "resilient_false_data") -> Dict[str, Any]:
        """Returns economic costs, losses, import/export, and voltage violation hours."""
        summary_file = self.results_dir / f"summary_{run_id}.json"
        if summary_file.exists():
            with open(summary_file, "r") as f:
                return json.load(f)
        return {"error": f"No summary file for {run_id}"}

    def get_benchmark_comparison(self, attack_scenario: str = "false_data") -> Dict[str, Any]:
        """Returns comparative performance degradation table across Centralized, Independent, and Resilient MAS."""
        bench_file = self.results_dir / f"benchmark_matrix_{attack_scenario}.csv"
        if bench_file.exists():
            import pandas as pd
            df = pd.read_csv(bench_file)
            return {"scenario": attack_scenario, "table": df.to_dict(orient="records")}
        return {"error": "Benchmark matrix not yet generated"}
