---
name: pr-review-resolution
description: |
  Fetches review comments from GitHub PR via gh API, categorizes them (style/docs/security/test/logic/design),
  auto-fixes deterministic issues (ruff, prettier), generates LLM patches for logic/design, pushes fixes to branch,
  updates PR with resolution comments, and notifies via Telegram. Includes historical analysis mode for learning.
version: 1.0.0
author: ndethi
license: MIT
tags: [pr, review, automation, github, copilot, telegram]
---

# PR Review Resolution Skill

## Overview
Automates the PR review → fix → push → verify cycle. Reduces manual iteration on review comments by:
- **Deterministic auto-fix** for style, docs, security (ruff, prettier, secret scanning)
- **LLM-assisted patches** for logic, design (with test validation)
- **Human-in-the-loop** gate for judgment calls
- **Telegram notifications** for review progress
- **Historical analysis** mode to learn patterns and improve auto-fix rules

## Interface
```json
{
  "mode": "resolve | analyze",
  "pr_number": 42,
  "repo": "owner/repo",
  "since": "2026-01-01",
  "hitl_gate": true,
  "output": "resolution_report.json | analysis_report.json"
}
```

### Modes
- **`resolve`**: Active PR review cycle — fetch, categorize, fix, push, notify
- **`analyze`**: Historical learning — read-only pattern analysis on merged PRs

## Evaluation
The skill passes when:
- Categorization accuracy ≥ 90% on fixture PR comments
- Auto-fixes (style/docs) apply cleanly and tests pass
- LLM-generated patches compile and tests pass
- Git operations (commit, push, PR update) succeed
- Telegram notification sent (when gateway configured)
- Unknown comment types → `deferred`, never fabricated