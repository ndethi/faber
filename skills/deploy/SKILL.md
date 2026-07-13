---
name: deploy
description: "Lifecycle skill #5: deploys a successfully evaluated project to the target platform (Cloudflare Pages per FRAMEWORK.md §8). Reads deployment config from scaffolded project, validates trajectory-guard passed, executes deployment via wrangler/pages CLI, and outputs deployment summary with URL and status."
version: 1.0.0
author: ndethi
license: MIT
tags: ["lifecycle", "deploy", "cloudflare-pages", "wrangler", "deployment", "framework"]
metadata:
  hermes:
    tags: ["lifecycle", "deploy", "cloudflare-pages", "wrangler", "deployment", "framework"]
    related_skills: ["intent-collect", "scaffold", "build", "evaluate", "publish", "observe", "feedback", "trajectory-guard"]
---

# Deploy Skill

Lifecycle skill #5 in the Faber framework (per FRAMEWORK.md §3). Deploys an evaluated project to the target platform.

## Purpose

Reads the scaffolded project and evaluation results, then deploys to the configured platform:

- **Deploy Target**: Cloudflare Pages (per FRAMEWORK.md §8 defaults)
- **Tool**: Wrangler CLI (`npx wrangler pages deploy`)
- **Prerequisite**: `evaluate` skill must pass (quality gate)

## Interface

### Inputs

- `--project-dir` (required): Directory of the scaffolded project to deploy
- `--input-dir` (required): Directory containing `spec.md`, `trajectory.md`, `scope-baseline.md`, and `evaluation-report.json`
- `--output-dir` (optional, default: `.`): Directory to write deployment report
- `--hitl-gate` (flag): Require manual confirmation before deploying
- `--dry-run` (flag): Show what would be deployed without executing
- `--env` (optional, default: `production`): Deployment environment (preview/production)

### Outputs

Machine-readable JSON summary on stdout:
```json
{
  "status": "success",
  "artifacts": ["deployment-report.json", "DEPLOYMENT_SUMMARY.md"],
  "deployment_url": "https://my-project.pages.dev",
  "deployment_id": "abc123",
  "environment": "production",
  "hitl_gate_required": false,
  "hitl_gate_passed": true
}
```

Files created on disk:
```
<output-dir>/
├── deployment-report.json
└── DEPLOYMENT_SUMMARY.md
```

## Deployment Process

1. **Validate prerequisites** — Check evaluation-report.json exists and `overall_success: true`
2. **Read project config** — Parse `wrangler.toml` and `package.json` for deployment config
3. **Run build** — Execute `npm run build` to generate `dist/` directory
4. **Deploy** — Run `npx wrangler pages deploy dist/` with appropriate flags
5. **Capture result** — Extract deployment URL and ID from wrangler output
6. **Write report** — Generate deployment-report.json and DEPLOYMENT_SUMMARY.md

## Determinism

Same input artifacts + same project → identical deployment report structure. Verified by eval.

## HITL Gate

- `--hitl-gate` flag enables interactive confirmation before deploying
- Default: no gate (automated pipelines)
- On failure: exits with code 1, status `hitl_gate_failed`

## Unknown Handling

Per FRAMEWORK.md §1: Unknowns appear as `TODO:` in reports, never fabricated.

## Usage

```bash
# Deploy an evaluated project
python skills/deploy/scripts/deploy.py \
  --project-dir ./my-project \
  --input-dir ./eval-output \
  --output-dir ./deploy-output

# Dry run (preview without deploying)
python skills/deploy/scripts/deploy.py \
  --project-dir ./my-project \
  --input-dir ./eval-output \
  --dry-run

# With HITL gate (interactive)
python skills/deploy/scripts/deploy.py \
  --project-dir ./my-project \
  --input-dir ./eval-output \
  --hitl-gate
```

## Acceptance Criteria

1. **Validates evaluation report** — Exits with error if `evaluation-report.json` missing or `overall_success: false`
2. **Parses wrangler.toml** — Extracts project name and pages config
3. **Runs build before deploy** — Executes `npm run build` to generate `dist/`
4. **Executes wrangler pages deploy** — Deploys `dist/` to Cloudflare Pages
5. **Outputs deployment-report.json + DEPLOYMENT_SUMMARY.md** — Machine + human readable
6. **Deterministic output** — Identical inputs produce identical reports
7. **HITL gate works** — `--hitl-gate` prompts for confirmation
8. **Dry-run works** — `--dry-run` shows steps without executing
9. **Exit code reflects success** — 0 if deploy succeeds, 1 if any step fails

## Dependencies

- `evaluate` (upstream): Must run first and pass (quality gate)
- `trajectory-guard` (cross-cutting): Validated via evaluation report
- Project must have: `package.json` with build script, `wrangler.toml`, `dist/` after build
- Wrangler CLI available (`npx wrangler`)

## Related

- FRAMEWORK.md §3: Lifecycle ring definition
- FRAMEWORK.md §8: Default framework/deploy conventions
- evaluate: Quality gate before deploy
- trajectory-guard: Drift detection