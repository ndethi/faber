---
name: feedback
description: "Lifecycle skill #8: collects user feedback after each run and stores it as feedback.json. Reads observations.json and telemetry.json from run directory, optionally prompts for rating/notes, writes structured feedback payload."
version: 1.0.0
author: ndethi
license: MIT
tags: ["lifecycle", "feedback", "user-feedback", "post-deploy", "framework"]
metadata:
  hermes:
    tags: ["lifecycle", "feedback", "user-feedback", "post-deploy", "framework"]
    related_skills: ["intent-collect", "scaffold", "build", "evaluate", "deploy", "publish", "observe", "trajectory-guard"]
---

# Feedback Skill

Lifecycle skill #8 in the Faber framework (per FRAMEWORK.md §3). Collects user feedback after each run to close the post-deploy feedback loop (FRAMEWORK.md §6).

## Purpose

Reads the run artifacts and collects structured feedback:

- **Input**: Run directory containing `observations.json` and optionally `telemetry.json`
- **Process**: 
  1. Loads `observations.json` (if exists) for context
  2. Loads `telemetry.json` (if exists) for trajectory context
  3. Prompts for rating (1-5) and optional notes (interactive or CLI args)
  4. Writes `feedback.json` to run directory or specified output directory
- **Output**: `feedback.json` with rating, notes, and context

This feeds the **post-deploy feedback loop** (FRAMEWORK.md §6):
```
observe → triage → propose → HITL → build → verify
```
Client feedback becomes **extended-scope** ledger items (FRAMEWORK.md §9).

## Interface

### Inputs
- `--run-dir` (required): Path to run directory (contains observations.json, telemetry.json)
- `--output-dir` (optional, default: run-dir): Directory to write feedback.json
- `--hitl-gate` (flag): Require manual confirmation before writing
- `--dry-run` (flag): Show what would be written without writing
- `--rating` (optional, 1-5): Rating for non-interactive use
- `--notes` (optional): Feedback notes for non-interactive use

### Outputs

Machine-readable JSON summary on stdout:
```json
{
  "status": "success",
  "artifacts": ["feedback.json"],
  "rating": 4,
  "notes": "Good run",
  "hitl_gate_required": false,
  "hitl_gate_passed": true,
  "dry_run": false
}
```

Files created on disk:
```
<output-dir>/
└── feedback.json
```

## Feedback.json Structure

```json
{
  "run_id": "run_20260706_100000",
  "collected_at": "2026-07-06T10:00:00Z",
  "rating": 4,
  "notes": "Good run",
  "context": {
    "runs_analyzed": 3,
    "success_rate": 0.8,
    "total_tokens": 1500,
    "total_cost_usd": 0.75,
    "skills_invoked": ["intent-collect", "scaffold", "build", "evaluate"],
    "trajectory_status": "ordered"
  },
  "hitl_gate": false,
  "dry_run": false
}
```

## Determinism

Same inputs (run artifacts + rating + notes) → identical feedback.json structure. Verified by eval.

## HITL Gate

- `--hitl-gate` flag enables interactive confirmation before writing
- Default: no gate (automated pipelines)
- On cancellation: exits with code 1, status `hitl_gate_failed`

## Unknown Handling

Per FRAMEWORK.md §1: Unknowns appear as `TODO:` in feedback, never fabricated.