"""
Automated context diagnoser and rule-based threshold evaluator.

Identifies root causes of context explosion, token bloat, and advanced context degradation
(Context Poisoning, Context Distraction, Context Clash) to map prescriptive architectural solutions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContextDiagnoser:
    def __init__(self, run_folder: Path):
        self.run_folder = Path(run_folder)
        self.summary_file = self.run_folder / "eval_summary.json"
        self.diagnostic_report_file = self.run_folder / "context_diagnostics.json"

    def run_diagnostics(self) -> Dict[str, Any]:
        """Runs automated rule-based threshold analysis on eval_summary.json."""
        if not self.summary_file.exists():
            return {"error": f"Summary file not found at {self.summary_file}"}

        try:
            with open(self.summary_file, "r") as f:
                summary = json.load(f)
        except Exception as e:
            return {"error": f"Failed to parse summary file: {e}"}

        overall = summary.get("overall_summary", {})
        det = overall.get("deterministic_metrics", {})
        llm = overall.get("llm_based_metrics", {})

        def get_avg(source_dict: Dict[str, Any], key: str, default: float = 0.0) -> float:
            val = source_dict.get(key)
            if isinstance(val, dict):
                return float(val.get("average", default))
            elif isinstance(val, (int, float)):
                return float(val)
            return default

        # Fetch key metrics
        avg_total_tokens = get_avg(det, "token_usage.total_tokens")
        avg_prompt_tokens = get_avg(det, "token_usage.prompt_tokens")
        avg_latency = get_avg(det, "latency_metrics.average_turn_latency_seconds")
        cache_hit_rate = get_avg(det, "cache_efficiency.cache_hit_rate")
        tool_success = get_avg(det, "tool_success_rate.tool_success_rate", 1.0)
        
        # Attribution metrics if available
        hist_tokens = get_avg(det, "token_attribution.conversation_history_tokens")
        tool_res_tokens = get_avg(det, "token_attribution.tool_execution_results_tokens")

        # LLM Metrics
        cap_honesty = get_avg(llm, "capability_honesty", 5.0)
        traj_acc = get_avg(llm, "trajectory_accuracy", 5.0)
        fact_retention = get_avg(llm, "fact_retention_probe", 5.0)
        degrad_guard = get_avg(llm, "context_degradation_guard", 5.0)

        diagnostics = {
            "dimensions": {},
            "degradation_failure_modes": {},
            "recommended_pillars": []
        }

        # --- Rule-Based Dimension Classification ---
        # Dimension A: Tool Payload Explosion
        if tool_res_tokens > 8000 or (avg_prompt_tokens > 15000 and tool_success < 0.9):
            diagnostics["dimensions"]["Dimension A: Tool Payload Explosion"] = {
                "detected": True,
                "severity": "HIGH" if tool_res_tokens > 15000 else "MEDIUM",
                "evidence": f"Tool execution results consume average {tool_res_tokens} tokens per turn. Tool success is {tool_success:.2f}.",
                "pillar": "Pillar 1: Prune & Offload (Pydantic models & JSONPath truncation)"
            }
            diagnostics["recommended_pillars"].append("Pillar 1 (Prune)")

        # Dimension B: Conversation History Rot
        if hist_tokens > 6000 or (avg_prompt_tokens > 20000 and fact_retention < 3.5):
            diagnostics["dimensions"]["Dimension B: Conversation History Rot"] = {
                "detected": True,
                "severity": "HIGH" if fact_retention < 2.5 else "MEDIUM",
                "evidence": f"Conversation history exceeds thresholds ({hist_tokens} tokens). Fact retention probe dropped to {fact_retention:.2f}/5.0.",
                "pillar": "Pillar 2: Compress & Reduce (Rolling summarization buffer)"
            }
            diagnostics["recommended_pillars"].append("Pillar 2 (Compress)")

        # Dimension C: Sub-Agent State Bloat / Handoff Duplication
        if traj_acc < 3.5 and avg_prompt_tokens > 12000:
            diagnostics["dimensions"]["Dimension C: Sub-Agent State Bloat"] = {
                "detected": True,
                "severity": "MEDIUM",
                "evidence": f"Trajectory accuracy is sub-optimal ({traj_acc:.2f}) with high base token spend ({avg_prompt_tokens}).",
                "pillar": "Pillar 4: Isolate Contracts (Data Transfer Objects DTOs)"
            }
            diagnostics["recommended_pillars"].append("Pillar 4 (Isolate)")

        # Dimension D: Static Prompt Bloat
        if avg_prompt_tokens > 10000 and cache_hit_rate < 0.3:
            diagnostics["dimensions"]["Dimension D: Static Prompt Bloat"] = {
                "detected": True,
                "severity": "HIGH" if cache_hit_rate < 0.1 else "MEDIUM",
                "evidence": f"Large static prompt base ({avg_prompt_tokens} tokens) with extremely low KV-cache hit rate ({cache_hit_rate:.2%}).",
                "pillar": "Pillar 3 (Retrieve on Demand) & Pillar 5 (Cache Prefixes)"
            }
            diagnostics["recommended_pillars"].append("Pillar 5 (Cache)")
            diagnostics["recommended_pillars"].append("Pillar 3 (Retrieve)")

        # --- Advanced Context Degradation Failure Modes ---
        if degrad_guard < 4.0:
            if fact_retention < 3.0:
                diagnostics["degradation_failure_modes"]["Context Clash"] = {
                    "detected": True,
                    "evidence": f"Context degradation score is {degrad_guard:.2f} combined with low fact retention ({fact_retention:.2f}). Signals contradictory accumulation.",
                    "mitigation": "Pillar 6: Write & Persist (Durable external Key-Value store to reconcile state)"
                }
                diagnostics["recommended_pillars"].append("Pillar 6 (Write)")
            if cap_honesty < 3.5:
                diagnostics["degradation_failure_modes"]["Context Poisoning"] = {
                    "detected": True,
                    "evidence": f"Capability honesty dropped to {cap_honesty:.2f}. Agent is compounding hallucinated abilities or facts across turns.",
                    "mitigation": "Enforce strict tool validation and prompt ejection rules."
                }
            if avg_latency > 8.0 and traj_acc < 3.8:
                diagnostics["degradation_failure_modes"]["Context Distraction"] = {
                    "detected": True,
                    "evidence": f"Agent latency is high ({avg_latency:.2f}s) and trajectory accuracy is compromised ({traj_acc:.2f}). History bloat distracting attention head.",
                    "mitigation": "Enforce rigid per-component token budgeting."
                }

        diagnostics["recommended_pillars"] = list(set(diagnostics["recommended_pillars"]))

        # Save diagnostics
        try:
            with open(self.diagnostic_report_file, "w") as f:
                json.dump(diagnostics, f, indent=4)
        except Exception as e:
            print(f"Error saving diagnostic report: {e}")

        return diagnostics
