# Trajectory‑Guard Skill

> Enforces that each run’s telemetry matches the baseline `trajectory.md`.

## Overview
The **trajectory‑guard** skill is run as a CI job. It receives a run directory, loads `observations.json` and compares a chosen field (`summary`) against the canonical baseline defined in `trajectory.md`. If a drift is detected the script exits with a non‑zero status, causing the CI workflow to fail.

## Specification
- **Input**: path to a run directory (`<run_dir>`).
- **Process**:
  1. Read `<run_dir>/observations.json`.
  2. Read the repository‑level `trajectory.md`.
  3. Compare the `summary` field from the JSON to the trimmed contents of `trajectory.md`.
  4. Exit `0` if they match, otherwise exit `1`.
- **Output**: console log indicating success or drift.

## Implementation
Implemented in `skills/trajectory-guard/scripts/guard.py`.
