# Context Optimization Platform Context

> This file provides context for AI assistants. For setup instructions, see [REFERENCE.md](REFERENCE.md).

---

## Overview

This is the **Context Optimization & Evaluation Platform** for enterprise agent architectures.

**Objective:** Equip development and QA teams to transition from prompt engineering to context engineering, using a production-grade evaluation framework to measure and validate agent performance and cost improvements.

**Key Concepts:**
- Context Engineering: Systematic management of the model's context window across six pillars (Prune, Compress, Retrieve, Isolate, Cache, Write)
- Evaluation Framework: 3-step process (Run Interactions → Evaluate → Analyze)
- Hill Climb Methodology: Iterative optimization from M0 (baseline) to M5 (fully optimized)

---

## Repository Structure

```
context_optimisation_strategy_sample/
├── README.md                  # Executive overview & architecture guide
├── REFERENCE.md               # Deep dive (CLI, financial metrics, customization)
├── customer-service/          # Agent A: Multi-turn, reliability focus
├── retail-ai-location-strategy/  # Agent B: Pipeline, scale focus
└── evaluation/                # Shared evaluation CLI (agent-eval)
```

---

## What Evaluators Are Doing

1. **Running baseline evaluations** on the `main` branch
2. **Checking out optimization iterations** (Prune, Compaction, Memory Store, Prefix Cache)
3. **Re-running evaluations** to compare before/after metrics
4. **Understanding trade-offs** between quality, cost, and latency

---

## Common Tasks You Should Help With

### Running Evaluations
```bash
# Full pipeline
cd customer-service
rm -rf customer_service/.adk/eval_history/*
uv run agent-eval run --agent-dir customer_service --scenarios-file eval/scenarios/suite/tool_heavy_workflow.json --session-input-file eval/scenarios/session_input.json --runs 5

cd ../evaluation
RUN_DIR=$(uv run agent-eval convert --agent-dir ../customer-service/customer_service --output-dir ../customer-service/eval/results | awk -F': ' '/^Run folder:/ {print $2}')
uv run agent-eval evaluate --interaction-file $RUN_DIR/raw/processed_interaction_sim.jsonl --metrics-files ../customer-service/eval/metrics/metric_definitions.json --results-dir $RUN_DIR
uv run agent-eval analyze --results-dir $RUN_DIR --agent-dir ../customer-service --location global
```

### Creating Custom Metrics
Metrics go in `eval/metrics/metric_definitions.json`. Help evaluators write custom LLM-as-Judge metrics with clear scoring criteria.

### Understanding Results
- `eval_summary.json` → Aggregated metrics
- `gemini_analysis.md` → Root cause analysis
- `OPTIMIZATION_LOG.md` → Multi-iteration variance tracking (mean ± stdev)

---

## Critical Reminders

1. **Always use Vertex AI**, not API keys (evaluation won't work otherwise)
2. **Clear eval_history** before each run: `rm -rf agent/.adk/eval_history/*`
3. **Run `uv sync`** after updating dependencies
4. **Use `--location global`** for Gemini 3 / 2.5 models in analyze command
