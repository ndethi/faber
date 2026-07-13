---
name: test-dedup
description: |
  intent collect deterministic spec trajectory scope
version: 1.0.0
author: ndethi
license: MIT
tags: ["gap", "auto-generated"]
---

# Test Dedup

## Overview
Auto-generated skill for gap: intent collect deterministic spec trajectory scope. intent collect deterministic spec trajectory scope

## Interface
```json
{
  "input": "string",
  "context": "string"
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
| intent-collect | 2.8 | 4 | False | 4 |
| dashboard | 1.5 | 3 | False | 0 |
| scope-ledger | 0.5 | 1 | False | 0 |
| trajectory-guard | 0.5 | 1 | False | 0 |
| pr-review-resolution | 0.5 | 1 | False | 0 |

**Recommendation**: High similarity to existing skill(s) — consider extending instead of creating new.
