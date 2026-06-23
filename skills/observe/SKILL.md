# Observe Skill

## Description
Collects telemetry data from each run and stores it in `runs/<run_id>/observations.json`.

## Specification
- Reads `runs/*/telemetry.json`.
- Merges relevant fields (timestamp, cost, metrics) into a single JSON per run.
- Writes `observations.json` alongside telemetry.

## Usage
Run the script `scripts/observe.py` after a run completes.

## Evaluation
The skill passes when `observations.json` exists for every run directory and the JSON is valid.
