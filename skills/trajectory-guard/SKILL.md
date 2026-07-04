---
name: trajectory-guard
description: "Diffs actual vs expected trajectory; emits conformance report with match %, missing/extra/out-of-order steps, gate compliance."
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - cross-cutting
  - observability
  - drift-control
  - telemetry
---

# Trajectory Guard Skill

**Cross-cutting skill** — wraps every run to enforce process-level drift control (FRAMEWORK.md §4).

## Purpose

Validates that the actual execution trajectory matches the expected trajectory derived by `intent-collect`. Emits a conformance report used by the dashboard and orchestrator.

## Inputs

- `telemetry_path` (string, required): Path to `runs/<run_id>/telemetry.json`
- `strictness` (string, optional): Override strictness mode (`exact` | `ordered` | `partial`). Defaults to telemetry's `trajectory_strictness`.

## Outputs

- **Conformance report** (JSON to stdout, also written to `trajectory-guard-report.json` in same dir):
  - `run_id`: string
  - `strictness`: `exact` | `ordered` | `partial`
  - `match_percent`: float (0-100)
  - `status`: `pass` | `fail` | `warning`
  - `details`:
    - `expected_steps`: array of step objects
    - `actual_steps`: array of step objects
    - `missing`: array of expected step IDs not in actual
    - `extra`: array of actual step IDs not in expected
    - `out_of_order`: array of step IDs that appear in different order
    - `gate_violations`: array of HITL gate steps that were skipped/failed
- **Exit code**: 0 = pass, 1 = fail (for `exact` mode violations), 2 = warning (for `ordered`/`partial` deviations)

## Strictness Modes (FRAMEWORK.md §4)

| Mode | Behavior |
|------|----------|
| `exact` | Actual must equal expected exactly. Any deviation = fail (exit 1). |
| `ordered` | Expected steps must appear in order; extras allowed. Deviations = warning (exit 2). |
| `partial` | Expected checkpoints must be hit; order free. Missing checkpoints = warning (exit 2). |

## Interface

```bash
python skills/trajectory-guard/scripts/trajectory_guard.py \
  --telemetry-path runs/<run_id>/telemetry.json \
  [--strictness exact|ordered|partial]
```

Returns JSON conformance report on stdout.

## Evaluation

- `evals/test_trajectory_guard.py`: Tests exact/ordered/partial modes with fixture telemetry files
- Verifies correct match% calculation, missing/extra/out-of-order detection, gate violation detection

## Dependencies

- Python 3.10+
- Standard library only (json, sys, pathlib, argparse, difflib)