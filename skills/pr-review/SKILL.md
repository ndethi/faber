---
name: pr-review
description: "Automated PR review against Faber spec, best practices, and trajectory"
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [pr, review, automation, github, quality]
metadata:
  hermes:
    tags: [pr, review, automation, github, quality]
    related_skills: [github-code-review, github-pr-workflow, trajectory-guard]
---

# Skill: pr-review

## Role
You are an automated PR reviewer for the Faber framework. You review pull requests against:
1. **FRAMEWORK.md** — architecture, invariants, skill contracts
2. **AGENTS.md** — process constitution, branch model, PR discipline, HITL gates
3. **HERMES-BRIEF.md** — operating contract, Phase A* equilibrium conditions
4. **BRANCH-MODEL.md** — branch naming, PR targeting rules
5. **Best practices** — security, correctness, code quality, testing, performance
6. **Trajectory conformance** — expected vs actual skill sequence (via trajectory-guard)

## Intent
Automate the first-pass code review so human reviewers only need to handle judgment calls. The skill:
- Fetches PR diff and context
- Runs deterministic checks (linters, schema validation, trajectory-guard)
- Applies LLM review for semantic issues (architecture, design, security)
- Posts structured review with inline comments
- Supports iterative resolution via pr-review-resolution skill

## Preconditions
- `gh` CLI authenticated with repo write access
- Target repo follows Faber conventions (FRAMEWORK.md, AGENTS.md, etc.)
- PR targets `dev` branch (per BRANCH-MODEL.md)

## Inputs
- `PR_NUMBER` (required): GitHub PR number to review
- `REPO` (required): owner/repo format
- `SPEC_FILES` (optional): list of spec files to check against (default: FRAMEWORK.md, AGENTS.md, HERMES-BRIEF.md, BRANCH-MODEL.md)
- `HITL_GATE` (optional, default: true): whether human must approve before merge
- `CHECK_TRAJECTORY` (optional, default: true): run trajectory-guard if available

## Procedure

### 1. Fetch PR Context
```bash
gh pr view <PR_NUMBER> --repo <REPO> --json title,body,files,headRefOid,baseRefName
gh pr diff <PR_NUMBER> --repo <REPO>
gh pr checks <PR_NUMBER> --repo <REPO>
```

### 2. Run Deterministic Checks
- **Lint**: `ruff check .`, `prettier --check .` (or repo's linter)
- **Tests**: `python -m pytest` (or repo's test suite)
- **Schema validation**: validate telemetry, run plans, skill manifests
- **Trajectory guard**: if PR adds/modifies run plans, compare expected vs actual trajectory
- **Branch model**: verify branch name follows `hermes/<topic>` pattern, targets `dev`
- **Commit style**: verify Conventional Commits format
- **Security**: scan for secrets, hardcoded credentials

### 3. LLM Semantic Review
For each changed file, evaluate against:
- **FRAMEWORK.md §1**: Skill contract (SKILL.md, scripts/, evals/, references/)
- **FRAMEWORK.md §2**: Lifecycle & cross-cutting skills
- **FRAMEWORK.md §4**: Telemetry & observability
- **FRAMEWORK.md §5**: Definitions of Done
- **AGENTS.md §2**: Git discipline, PR discipline, commit style, HITL gates
- **AGENTS.md §3**: Skill contract requirements
- **HERMES-BRIEF.md**: Phase A* equilibrium, branch model
- **Security**: input validation, auth checks, no secrets
- **Correctness**: edge cases, error handling, null checks
- **Code Quality**: naming, DRY, single responsibility
- **Testing**: new code paths tested, happy path + error cases

### 4. Post Structured Review
Submit formal review with inline comments using the format:

```markdown
## PR Review Summary

**Verdict: [Approve | Request Changes | Comment]** (X issues, Y suggestions)

### 🔴 Critical
- **path/file.py:line** — Issue description
  Suggestion: Fix recommendation

### ⚠️ Warnings
- **path/file.py:line** — Issue description
  Suggestion: Fix recommendation

### 💡 Suggestions
- **path/file.py:line** — Improvement suggestion

### ✅ Looks Good
- Positive observations
```

### 5. Emit Report
Output `review_report.json`:
```json
{
  "pr_number": 123,
  "repo": "owner/repo",
  "verdict": "REQUEST_CHANGES",
  "issues": [
    {"level": "critical", "file": "path/file.py", "line": 42, "message": "...", "suggestion": "..."},
    ...
  ],
  "deterministic_checks": {
    "lint": "pass",
    "tests": "pass",
    "trajectory": "pass",
    "branch_model": "pass",
    "commit_style": "pass",
    "security": "pass"
  },
  "timestamp": "2026-06-30T...",
  "reviewer": "pr-review-skill@1.0.0"
}
```

## Building the Skill
- Write `SKILL.md` with pushy description ("Use whenever a PR is opened targeting dev branch…")
- Put fetch/review/post logic in `scripts/` (deterministic where possible)
- Keep body < 500 lines
- Add **eval**: given fixture PR diffs, assert categorization accuracy ≥ 0.9, review format valid, inline comments actionable

## Deliverables
`skills/pr-review/{SKILL.md, scripts/, evals/}`

## Acceptance Criteria
- AC-1: Fetches PR diff and metadata from gh API
- AC-2: Runs deterministic checks (lint, tests, schema, trajectory) and reports pass/fail
- AC-3: LLM review categorizes issues as Critical/Warning/Suggestion with ≥ 90% accuracy on fixtures
- AC-4: Posts formal GitHub review with inline comments
- AC-5: Emits review_report.json for downstream consumption
- AC-6: Respects HITL gate (default true)
- AC-7: Unknown patterns → deferred, never fabricated

## Trajectory
`fetch → deterministic_checks → llm_review → post_review → emit_report`. Strictness: `ordered`.

## Execution Command
> Review PR #<number> in <owner/repo> against Faber spec and best practices. Post structured review with inline comments. Emit review_report.json.