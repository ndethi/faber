---
name: dashboard
description: "Generates management dashboard (dashboard/index.html) from telemetry: runs list, trajectory diffs, cost/model-routing, eval scores, deploy health, HITL queue, scope ledger."
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - cross-cutting
  - observability
  - dashboard
  - telemetry
  - visualization
---

# Dashboard Skill

**Cross-cutting skill** — generates the management dashboard from run telemetry (FRAMEWORK.md §5).

## Purpose

Creates a visual dashboard (`dashboard/index.html`) that surfaces all consequences the agent and dev should care about: run status, trajectory conformance, cost, eval scores, deploy health, and the HITL queue.

## Inputs

- `runs_dir` (string, required): Path to `runs/` directory containing run telemetry
- `output_dir` (string, optional): Output directory for `index.html` (default: `dashboard/`)

## Outputs

- **`dashboard/index.html`** — Single-file HTML dashboard with:
  - Runs table (run_id, timestamp, status, trajectory match%, model, tokens, cost, deploy_status)
  - Per-run trajectory diff (expected vs actual, missing/extra/out-of-order, gate violations)
  - Cost summary (total, per-run, per-skill if available)
  - Model routing decisions (local vs frontier per step)
  - Eval scores per run
  - Deploy health (RUM/CWV placeholders)
  - HITL queue (pending PRs, pending spec changes)
  - Scope ledger (baseline vs extended scope, cost, IP attribution)
- **Machine-readable summary** (JSON to stdout):
  - `runs_processed`: integer
  - `dashboard_path`: string
  - `summary`: {total_runs, total_cost, avg_trajectory_match, etc.}

## Interface

```bash
python skills/dashboard/scripts/dashboard.py \
  --runs-dir runs/ \
  [--output-dir dashboard/]
```

Returns JSON summary on stdout.

## Evaluation

- `evals/test_dashboard.py`: Tests dashboard generation with fixture telemetry
- Verifies HTML output contains required sections, correct data rendering

## Dependencies

- Python 3.10+
- Standard library only (json, sys, pathlib, argparse, glob, html)
- No external dependencies — generates self-contained HTML with embedded CSS/JS