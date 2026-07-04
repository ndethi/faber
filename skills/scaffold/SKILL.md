---
name: scaffold
description: "Lifecycle skill #2: creates project structure from intent-collect artifacts (spec.md, trajectory.md, scope-baseline.md). Generates Astro + Cloudflare Pages project with config, CI/CD, boilerplate, and skill stubs per FRAMEWORK.md conventions."
version: 1.0.0
author: ndethi
license: MIT
tags: ["lifecycle", "scaffold", "project-generation", "astro", "cloudflare-pages", "framework"]
metadata:
  hermes:
    tags: ["lifecycle", "scaffold", "project-generation", "astro", "cloudflare-pages", "framework"]
    related_skills: ["intent-collect", "build", "evaluate", "deploy", "publish", "observe", "feedback", "trajectory-guard"]
---

# Scaffold Skill

Lifecycle skill #2 in the Faber framework (per FRAMEWORK.md §3). Creates deterministic project structure from intent-collect artifacts.

## Purpose

Reads the three intent-collect outputs:
- `spec.md` — Source of truth with IDed acceptance criteria (SPEC-XX)
- `trajectory.md` — Expected path (ordered DAG of lifecycle steps + checkpoints)
- `scope-baseline.md` — Client-shareable scope baseline

Generates a complete, runnable project structure following FRAMEWORK.md §8 defaults:
- **Framework**: Astro (static site / SSR)
- **Deploy Target**: Cloudflare Pages
- **Package Manager**: npm
- **Language**: TypeScript

## Interface

### Inputs
- `--input-dir` (required): Directory containing `spec.md`, `trajectory.md`, `scope-baseline.md`
- `--output-dir` (optional, default: `.`): Directory to write project structure
- `--hitl-gate` (flag): Require manual confirmation before writing files
- `--dry-run` (flag): Show what would be created without writing

### Outputs
Machine-readable JSON summary on stdout:
```json
{
  "status": "success",
  "artifacts": ["package.json", "astro.config.mjs", "src/pages/index.astro", ...],
  "hitl_gate_required": false,
  "hitl_gate_passed": true,
  "input_artifacts": {...},
  "output_dir": "...",
  "acceptance_criteria_count": 4,
  "trajectory_steps": 9,
  "project_name": "my-project"
}
```

Files created on disk:
```
<output-dir>/
├── package.json
├── astro.config.mjs
├── wrangler.toml
├── tsconfig.json
├── eslint.config.js
├── .prettierrc
├── .gitignore
├── .github/workflows/ci.yml
├── .github/workflows/deploy.yml
├── src/
│   ├── pages/index.astro
│   ├── layouts/BaseLayout.astro
│   ├── components/Header.astro
│   ├── components/Footer.astro
│   └── styles/global.css
├── public/
├── tests/example.test.ts
├── scripts/
│   ├── build/build.py
│   ├── evaluate/evaluate.py
│   ├── deploy/deploy.py
│   ├── publish/publish.py
│   ├── observe/observe.py
│   └── feedback/feedback.py
├── SCAFFOLD_SUMMARY.md
└── README.md
```

## Determinism

Same input artifacts → identical output structure and file contents. Verified by eval.

## HITL Gate

- `--hitl-gate` flag enables interactive confirmation before writing
- Default: no gate (automated pipelines)
- On failure: exits with code 1, status `hitl_gate_failed`

## Unknown Handling

Per FRAMEWORK.md §1: Unknowns appear as `TODO:` in generated skill stubs, never fabricated.

## Usage

```bash
# Generate from intent artifacts
python skills/scaffold/scripts/scaffold.py \
  --input-dir ./intent-output \
  --output-dir ./my-project

# Dry run (preview without writing)
python skills/scaffold/scripts/scaffold.py \
  --input-dir ./intent-output \
  --dry-run

# With HITL gate (interactive)
python skills/scaffold/scripts/scaffold.py \
  --input-dir ./intent-output \
  --hitl-gate
```

## Acceptance Criteria

1. **All three input files required** — exits with error if any missing
2. **Parses SPEC-XX from spec.md** — extracts acceptance criteria count
3. **Parses trajectory steps** — extracts ordered lifecycle steps + checkpoints
4. **Generates valid Astro + Cloudflare Pages project** — `npm install && npm run build` succeeds
5. **Creates skill stubs for all lifecycle stages** — build, evaluate, deploy, publish, observe, feedback
6. **Deterministic output** — identical inputs produce identical file trees
7. **HITL gate works** — `--hitl-gate` prompts for confirmation
8. **Dry-run works** — `--dry-run` shows files without writing

## Dependencies

- `intent-collect` (upstream): must run first to produce input artifacts
- `trajectory-guard` (downstream): validates actual trajectory matches expected
- FRAMEWORK.md §8 defaults: Astro + Cloudflare Pages

## Related

- FRAMEWORK.md §3: Lifecycle ring definition
- FRAMEWORK.md §8: Default framework/deploy conventions
- trajectory-guard: drift detection