---
name: pm-github
description: |
  A framework-scoped Faber skill that owns all GitHub project-management operations across Faber and its client offshoots (Rohaki, k-dimensional, future clients). Scope of ownership: (a) versioning & re
version: 1.0.0
author: ndethi
license: MIT
tags: ["pm", "github", "issues", "projects", "governance", "cross-cutting"]
---

# Pm Github

## Overview
Auto-generated skill for capability: A framework-scoped Faber skill that owns all GitHub project-management operations across Faber and its client offshoots (Rohaki, k-dimensional, future clients). Scope of ownership: (a) versioning & releases -- semver bumps, tag creation, release notes, changelog append; (b) GitHub Projects v2 -- project creation, field schema (Status, Priority, Severity, Type, Target Release, Epic), views, automation; (c) issues -- triage, creation, deduplication, labelling, linking to PRs/commits/projects; (d) PR review-comment -> issue pipeline -- classify each actionable comment by severity (Critical|High|Medium|Low) and type (bug|enhancement|docs|refactor|security), dedup by sha256(source_repo + source_pr + source_comment_id), emit a proposal batch as a PR comment listing 'would create N issues; approve to materialize'; (e) milestones & roadmaps -- with docs/roadmap.md as SSOT, not a proprietary board; (f) governance -- label taxonomy, issue/PR templates. NON-NEGOTIABLE INVARIANT: every write operation is proposal-only by default (dry-run=True). Real GitHub writes require an explicit --apply flag OR a separately-gated workflow, never the default. This preserves AGENTS.md's 'agents propose, humans dispose' rule. Config resolution: skill-level defaults at skills/pm-github/config/defaults.yaml, repo-level overrides at .github/pm-config.yaml in the invoked repo, merged over defaults. If .github/pm-config.yaml is absent, work with defaults and propose the file as a PR. Constraints: gh CLI only (no GraphQL-only deps); testable locally without GitHub write permissions (fixtures + mocks); every write appends to runs/hermes/pm-log.jsonl; idempotent (dedup key). Non-goals: replacing human triage judgement (skill classifies deterministically and proposes; human confirms); portfolio management across unrelated repos (per-repo only); issue resolution (tracking/organization only); two-way Linear/Jira sync (separate skill pm-linear-sync, not now).. A framework-scoped Faber skill that owns all GitHub project-management operations across Faber and its client offshoots (Rohaki, k-dimensional, future clients). Scope of ownership: (a) versioning & re

## Interface
```json
{
  "capability": "string",
  "requirements": ["string"]
}
```

## Evaluation
The skill passes when:
  SKILL.md exists with required YAML frontmatter
  scripts/ directory with executable entry point
  evals/ directory with passing test
  Deterministic output for identical inputs
  Unknowns appear as TODO:, never fabricated
  Dedup search documented in SKILL.md

## Determinism & HITL
- **Determinism**: Same inputs → same output structure
- **HITL Gate**: Dev reviews/approves PR (client-scoped); promotion to framework-scoped requires second PR/gate
- **Unknown Handling**: Gaps surface as `TODO:`, never fabricated

## Dedup Search
This skill was created after searching existing skills:
| Skill | Score | Overlap | Name Match | Tag Overlap |
|-------|-------|---------|------------|-------------|
| pr-review | 16.4 | 32 | False | 2 |
| skill-author | 12.4 | 24 | False | 2 |
| intent-collect | 11.2 | 22 | False | 1 |
| build | 8.5 | 17 | False | 0 |
| trajectory-guard | 7.5 | 15 | False | 0 |

**Recommendation**: High similarity to existing skill(s) — consider extending instead of creating new.
