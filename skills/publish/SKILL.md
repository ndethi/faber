---
name: publish
description: "Lifecycle skill #6: publishes deployed artifacts and updates release channels. Reads deployment report, creates/releases GitHub Release (if configured), updates changelog, and publishes to package registries (npm, PyPI) per project config. Outputs publication summary with links and version."
version: 1.0.0
author: ndethi
license: MIT
tags: ["lifecycle", "publish", "release", "github-release", "npm", "changelog", "framework"]
metadata:
  hermes:
    tags: ["lifecycle", "publish", "release", "github-release", "npm", "changelog", "framework"]
    related_skills: ["intent-collect", "scaffold", "build", "evaluate", "deploy", "observe", "feedback", "trajectory-guard", "pm-github"]
---

# Publish Skill

Lifecycle skill #6 in the Faber framework (per FRAMEWORK.md §3). Publishes deployed artifacts and creates/releases GitHub Release.

## Purpose

Reads the deployment report and project configuration, then publishes the release:

- **GitHub Release**: Creates or updates a GitHub Release with release notes from evaluation/deployment
- **Package Registries**: Publishes to npm/PyPI if configured in package.json/pyproject.toml
- **Changelog**: Updates CHANGELOG.md with the new release entry
- **Version bump**: Updates version in package.json/pyproject.toml

## Interface

### Inputs

- `--project-dir` (required): Directory of the scaffolded project
- `--input-dir` (required): Directory containing `deployment-report.json`, `evaluation-report.json`, and intent artifacts
- `--output-dir` (optional, default: `.`): Directory to write publication report
- `--hitl-gate` (flag): Require manual confirmation before publishing
- `--dry-run` (flag): Show what would be published without executing
- `--version` (optional): Override version (default: read from package.json/pyproject.toml)
- `--tag` (optional): Git tag to create (default: `v{version}`)

### Outputs

Machine-readable JSON summary on stdout:
```json
{
  "status": "success",
  "artifacts": ["publication-report.json", "PUBLICATION_SUMMARY.md"],
  "version": "1.0.0",
  "tag": "v1.0.0",
  "github_release_url": "https://github.com/owner/repo/releases/tag/v1.0.0",
  "npm_published": true,
  "changelog_updated": true,
  "hitl_gate_required": false,
  "hitl_gate_passed": true
}
```

Files created on disk:
```
<output-dir>/
├── publication-report.json
└── PUBLICATION_SUMMARY.md
```

## Publication Process

1. **Validate prerequisites** — Check deployment-report.json exists and `status: success`
2. **Read version** — Parse version from package.json (npm) or pyproject.toml (PyPI)
3. **Generate release notes** — Combine evaluation summary, deployment info, and conventional commits
4. **Create GitHub Release** — Use `gh release create` with generated notes
5. **Publish to registries** — `npm publish` and/or `pip publish` if configured
6. **Update changelog** — Prepend release entry to CHANGELOG.md
7. **Write report** — Generate publication-report.json and PUBLICATION_SUMMARY.md

## Determinism

Same input artifacts + same project → identical publication report structure. Verified by eval.

## HITL Gate

- `--hitl-gate` flag enables interactive confirmation before publishing
- Default: no gate (automated pipelines)
- On failure: exits with code 1, status `hitl_gate_failed`

## Unknown Handling

Per FRAMEWORK.md §1: Unknowns appear as `TODO:` in reports, never fabricated.

## Usage

```bash
# Publish a deployed project
python skills/publish/scripts/publish.py \
  --project-dir ./my-project \
  --input-dir ./deploy-output \
  --output-dir ./publish-output

# Dry run (preview without publishing)
python skills/publish/scripts/publish.py \
  --project-dir ./my-project \
  --input-dir ./deploy-output \
  --dry-run

# With HITL gate (interactive)
python skills/publish/scripts/publish.py \
  --project-dir ./my-project \
  --input-dir ./deploy-output \
  --hitl-gate
```

## Acceptance Criteria

1. **Validates deployment report** — Exits with error if `deployment-report.json` missing or `status != success`
2. **Parses version from package.json/pyproject.toml** — Extracts semantic version
3. **Generates release notes** — Combines evaluation summary, deployment URL, conventional commits
4. **Creates GitHub Release** — Uses `gh release create` with tag and notes
5. **Publishes to npm/PyPI** — If `publishConfig` or `[tool.poetry]` present
6. **Updates CHANGELOG.md** — Prepends release entry with date, version, notes
7. **Outputs publication-report.json + PUBLICATION_SUMMARY.md** — Machine + human readable
8. **Deterministic output** — Identical inputs produce identical reports
9. **HITL gate works** — `--hitl-gate` prompts for confirmation
10. **Dry-run works** — `--dry-run` shows steps without executing
11. **Exit code reflects success** — 0 if all steps pass, 1 if any fail

## Dependencies

- `deploy` (upstream): Must run first and succeed
- `pm-github` (cross-cutting): For GitHub Release creation
- Project must have: `package.json` (npm) or `pyproject.toml` (PyPI), `CHANGELOG.md` (optional, will be created)
- GitHub CLI (`gh`) authenticated for release creation
- npm/PyPI credentials configured for registry publishing

## Related

- FRAMEWORK.md §3: Lifecycle ring definition
- FRAMEWORK.md §8: Default framework/deploy conventions
- deploy: Quality gate + deployment prerequisite
- pm-github: Release automation
- trajectory-guard: Drift detection