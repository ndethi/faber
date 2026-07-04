---
name: skill-author
description: |
  Governed self-extension meta-skill for the Faber framework. Implements the
  skill creation lifecycle per FRAMEWORK.md §7: dedup search → draft SKILL.md +
  scripts/ + eval → run eval → open PR with rationale + eval results.
  Classification: client-scoped vs framework-scoped. HITL gates: dev reviews PR;
  promotion to framework-scoped requires second PR/gate.
  Hard rules: no skill without eval; no skill without dedup search.
version: 1.0.0
author: ndethi
license: MIT
tags: [meta, skill-author, self-extension, governance, dedup]
---

# Skill-Author Meta-Skill

## Overview
The canonical way to create new skills in the Faber framework. Enforces the
governance loop from FRAMEWORK.md §7:

1. **Trigger** — recurring pattern in `lessons.md`/feedback or capability gap
2. **Dedup** — search existing skills first (no sprawl)
3. **Draft** — SKILL.md + `scripts/` + `evals/` (skill contract)
4. **Eval** — run eval, must pass
5. **PR** — open with rationale + eval results
6. **HITL** — dev reviews/approves; promotion = second PR/gate

## Interface
```json
{
  "trigger": "gap|pattern|capability",
  "context": "string describing the gap/pattern/capability",
  "name": "optional kebab-case skill name",
  "scope": "client-scoped|framework-scoped",
  "author": "string",
  "license": "string",
  "tags": ["comma", "separated", "tags"],
  "auto_pr": false,
  "run_eval": true
}
```
Outputs:
- `skills/<name>/SKILL.md`
- `skills/<name>/scripts/<name>.py`
- `skills/<name>/evals/test_<name>.py`
- `PR_BODY_<name>.md` — ready for `gh pr create`

## Evaluation
The skill passes when:
- Dedup search runs and documents results
- SKILL.md has all required fields (name, description, version, author, license, tags)
- Script exists, is executable, shows usage on missing args
- Eval file exists and tests: SKILL.md, script existence, script help, output structure, determinism
- Eval passes on fresh run
- PR body generated with dedup results + eval status

## Determinism & HITL
- **Determinism**: Same inputs → same skill structure
- **HITL Gate 1**: This PR requires dev review + merge
- **HITL Gate 2**: Promotion to framework-scoped = second PR + dev review
- **Hard Rules**: No skill without eval; no skill without dedup search

## Determinism
Same trigger + context → same skill name + structure + dedup results.

## Unknown Handling
Gaps in skill design surface as `TODO:` in generated artifacts, never fabricated.