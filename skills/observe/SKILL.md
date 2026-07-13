---
name: observe
description: "Lifecycle skill #7: collects and aggregates telemetry data from framework runs into observations.json"
version: 1.0.0
author: ndethi
license: MIT
tags: ["lifecycle", "observe", "telemetry", "observations", "post-deploy", "framework"]
metadata:
  hermes:
    tags: ["lifecycle", "observe", "telemetry", "observations", "post-deploy", "framework"]
    related_skills: ["intent-collect", "scaffold", "build", "evaluate", "deploy", "publish", "feedback", "trajectory-guard"]
---

# Observe Skill

Lifecycle skill #7 in the Faber framework (per FRAMEWORK.md §3). Collects and aggregates telemetry data from run directories.

## Purpose

Reads telemetry data from each run and creates a consolidated observations file:

- **Input**: Run directories containing `telemetry.json`
- **Process**:
  1. Discovers all run directories under `runs/`
  2. Reads `telemetry.json` from each run
  3. Extracts and merges relevant fields (timestamp, cost, metrics, skills invoked)
  4. Writes `observations.json` alongside telemetry
- **Output**: `observations.json` per run directory

## Interface

### Inputs

- `--runs-dir` (required): Path to runs directory (contains run_*/ subdirectories)
- `--output-dir` (optional, default: runs-dir): Directory to write observations.json
- `--time-window` (optional): Filter runs by time window (e.g., "24h", "7d")
- `--dry-run` (flag): Show what would be processed without writing

### Outputs

Machine-readable JSON summary on stdout:
```json
{
  "status": "success",
  "artifacts": ["observations.json"],
  "runs_processed": 3,
  "time_window": "24h",
  "dry_run": false
}
```

Files created on disk:
```
<output-dir>/
└── run_<id>/
    └── observations.json
```

## Observations.json Structure

```json
{
  "run_id": "run_20260706_100000",
  "timestamp": "2026-07-06T10:00:00Z",
  "total_tokens": 1500,
  "total_cost_usd": 0.75,
  "skills_invoked": ["intent-collect", "scaffold", "build", "evaluate"],
  "trajectory_status": "ordered",
  "evaluation_score": 0.95
}
```

## Determinism

Same input runs + same time window → identical observations.json structure. Verified by eval.

## Unknown Handling

Per FRAMEWORK.md §1: Unknowns appear as `TODO:` in reports, never fabricated.

## Usage

```bash
# Process all runs
python skills/observe/scripts/observe.py --runs-dir ./runs

# Process last 24 hours
python skills/observe/scripts/observe.py --runs-dir ./runs --time-window 24h

# Dry run
python skills/observe/scripts/observe.py --runs-dir ./runs --dry-run
```

## Acceptance Criteria

1. **Discovers run directories** — Finds all `run_*/` under runs-dir
2. **Parses telemetry.json** — Extracts timestamp, cost, tokens, skills, trajectory status
3. **Writes observations.json** — Creates consolidated file per run
4. **Time window filtering** — `--time-window` filters runs by age
5. **Deterministic output** — Identical inputs produce identical observations
6. **Dry-run works** — `--dry-run` shows steps without writing
7. **Exit code reflects success** — 0 if all runs processed, 1 if any fail

## Dependencies

- `evaluate` (upstream): Runs must complete evaluation first
- `trajectory-guard` (cross-cutting): Trajectory status included in observations
- Run directories must have: `telemetry.json` with required fields