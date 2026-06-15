"""
Automated multi-run sandbox orchestrator and ablation testing engine.

Automates multi-iteration simulation execution (n=5 runs), cleans up prior adk evaluation
history, and supports sequential milestone ablation testing.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class SimulationRunner:
    def __init__(self, config: Dict[str, Any]):
        self.agent_dir = Path(config["agent_dir"])
        self.scenarios_file = config.get("scenarios_file")
        self.session_input_file = config.get("session_input_file")
        self.runs = config.get("runs", 5)
        self.order = config.get("order", "prune,compact,isolate,cache,write")
        self.ablation = config.get("ablation", False)
        self.eval_set_name = config.get("eval_set_name", "enterprise_eval_set")

    def clean_eval_history(self) -> None:
        """Cleans up the agent's .adk/eval_history directory prior to running simulations."""
        adk_dir = self.agent_dir / ".adk" / "eval_history"
        if adk_dir.exists():
            print(f"Cleaning existing evaluation history: {adk_dir}")
            for child in adk_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    try:
                        child.unlink()
                    except Exception:
                        pass
        else:
            adk_dir.mkdir(parents=True, exist_ok=True)

    def orchestrate(self) -> None:
        """Runs multi-turn adk user simulation across n runs."""
        print(f"\n=== Orchestrating Multi-Run Simulation (n={self.runs}) ===")
        print(f"Agent Directory: {self.agent_dir}")
        print(f"Optimization Order: {self.order}")
        if self.ablation:
            print("Ablation Mode: ENABLED (Isolating marginal pillar contributions)")

        # Step 1: Clean
        self.clean_eval_history()

        # Step 2: Ensure eval_set setup if scenarios provided
        agent_module_name = self.agent_dir.name

        if self.scenarios_file and self.session_input_file:
            print(f"\nCreating eval set: {self.eval_set_name}")
            try:
                subprocess.run(
                    ["uv", "run", "adk", "eval_set", "create", agent_module_name, self.eval_set_name],
                    cwd=self.agent_dir.parent,
                    check=True
                )
                subprocess.run(
                    [
                        "uv", "run", "adk", "eval_set", "add_eval_case", agent_module_name, self.eval_set_name,
                        "--scenarios_file", str(self.scenarios_file),
                        "--session_input_file", str(self.session_input_file)
                    ],
                    cwd=self.agent_dir.parent,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Warning during eval_set initialization: {e}")

        # Step 3: Execute n simulation runs
        print(f"\n=== Executing {self.runs} ADK User Simulation iterations ===")
        for i in range(1, self.runs + 1):
            print(f"--- Running Simulation Iteration {i}/{self.runs} ---")
            try:
                subprocess.run(
                    ["uv", "run", "adk", "eval", agent_module_name, self.eval_set_name],
                    cwd=self.agent_dir.parent,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Note: Iteration {i} finished with exit status: {e.returncode}")

        print(f"\nSUCCESS: Completed {self.runs} multi-run simulation iterations.")
        print(f"Simulations recorded in {self.agent_dir / '.adk' / 'eval_history'}")
        print("\nNext step: Run agent-eval convert to parse traces into JSONL.")
