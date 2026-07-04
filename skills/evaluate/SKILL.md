---
name: evaluate
description: "Lifecycle skill #3: runs acceptance tests, linting, type-checking, and trajectory-guard against a scaffolded project. Reads spec.md (SPEC-XX criteria), trajectory.md (strictness), and scope-baseline.md. Executes deterministic checks: npm test (Vitest), npm run lint (ESLint), npx astro check (TypeScript), trajectory-guard. Outputs evaluation report with pass/fail per criterion and trajectory conformance. Quality gate before deploy."
version: 1.0.0
author: ndethi
license: MIT
tags: ["lifecycle", "evaluate", "quality-gate", "testing", "linting", "type-checking", "trajectory-guard", "framework"]
metadata:
  hermes:
    tags: ["lifecycle", "evaluate", "quality-gate", "testing", "linting", "type-checking", "trajectory-guard", "framework"]
    related_skills: ["intent-collect", "scaffold", "build", "deploy", "publish", "observe", "feedback", "trajectory-guard"]
---

# Evaluate Skill

Lifecycle skill #3 in the Faber framework (per FRAMEWORK.md §3). Runs deterministic quality checks on a scaffolded project before deploy.

## Purpose

Reads the three intent-collect outputs plus the scaffolded project:
- `spec.md` — Source of truth with IDed acceptance criteria (SPEC-XX)
- `trajectory.md` — Expected path with strictness (exact/ordered/partial)
- `scope-baseline.md` — Client-shareable scope baseline
- Project directory — Scaffolded Astro + Cloudflare Pages project

Executes quality checks and outputs evaluation report. **Quality gate** before `deploy` skill.

## Interface

### Inputs
- `--input-dir` (required): Directory containing `spec.md`, `trajectory.md`, `scope-baseline.md`
- `--project-dir` (required): Directory of the scaffolded project to evaluate
- `--output-dir` (optional, default: `.`): Directory to write evaluation report
- `--hitl-gate` (flag): Require manual confirmation before running checks
- `--dry-run` (flag): Show what would be evaluated without running checks

### Outputs
Machine-readable JSON summary on stdout:
```json
{
  "status": "success",
  "artifacts": ["evaluation-report.json", "EVALUATION_SUMMARY.md"],
  "overall_success": true,
  "checks_run": 4,
  "checks_passed": 4,
  "acceptance_criteria_evaluated": 4,
  "strictness": "ordered",
  "hitl_gate_required": false,
  "hitl_gate_passed": true
}
```

Files created on disk:
```
<output-dir>/
├── evaluation-report.json
└── EVALUATION_SUMMARY.md
```

## Checks Performed

| Check | Command | Purpose |
|-------|---------|---------|
| **Unit/Integration Tests** | `npm test` | Vitest test suite execution |
| **Linting** | `npm run lint` | ESLint code quality |
| **Type Checking** | `npx astro check` | TypeScript + Astro type validation |
| **Trajectory Conformance** | `trajectory-guard` | Process-level drift control (per trajectory.md strictness) |

## Strictness Levels (from trajectory.md)

| Level | Behavior |
|-------|----------|
| `exact` | Actual trajectory must match expected exactly (client production) |
| `ordered` | Expected steps in order; extras allowed (normal work) |
| `partial` | Expected checkpoints hit; order free (prototype) |

## Determinism

Same input artifacts + same project → identical evaluation report. Verified by eval.

## HITL Gate

- `--hitl-gate` flag enables interactive confirmation before running checks
- Default: no gate (automated pipelines)
- On failure: exits with code 1, status `hitl_gate_failed`

## Unknown Handling

Per FRAMEWORK.md §1: Unknowns appear as `TODO:` in reports, never fabricated.

## Usage

```bash
# Evaluate a scaffolded project
python skills/evaluate/scripts/evaluate.py \
  --input-dir ./intent-output \
  --project-dir ./my-project \
  --output-dir ./eval-output

# Dry run (preview without running)
python skills/evaluate/scripts/evaluate.py \
  --input-dir ./intent-output \
  --project-dir ./my-project \
  --dry-run

# With HITL gate (interactive)
python skills/evaluate/scripts/evaluate.py \
  --input-dir ./intent-output \
  --project-dir ./my-project \
  --hitl-gate
```

## Acceptance Criteria

1. **All four checks executed** — npm test, npm run lint, npx astro check, trajectory-guard
2. **Parses SPEC-XX from spec.md** — extracts acceptance criteria count
3. **Parses strictness from trajectory.md** — exact/ordered/partial
4. **Runs trajectory-guard with correct strictness** — passes telemetry file
5. **Outputs evaluation-report.json + EVALUATION_SUMMARY.md** — machine + human readable
6. **Deterministic output** — identical inputs produce identical reports
7. **HITL gate works** — `--hitl-gate` prompts for confirmation
8. **Dry-run works** — `--dry-run` shows checks without executing
9. **Exit code reflects overall success** — 0 if all pass, 1 if any fail

## Dependencies

- `scaffold` (upstream): must run first to produce project directory
- `trajectory-guard` (cross-cutting): invoked for process-level drift control
- Project must have: `package.json` with test/lint scripts, `astro.config.mjs`

## Related

- FRAMEWORK.md §3: Lifecycle ring definition
- FRAMEWORK.md §4: Trajectory determinant
- trajectory-guard: drift detection