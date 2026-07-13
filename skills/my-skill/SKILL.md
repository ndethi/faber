---
name: my-skill
description: |
  my capability gap
version: 1.0.0
author: ndethi
license: MIT
tags: ["gap", "auto-generated"]
---

# My Skill

## Overview
Auto-generated skill for gap: my capability gap. my capability gap

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
| skill-author | 1.0 | 2 | False | 0 |
| test-dedup | 0.2 | 0 | False | 1 |
| quantum-sim | 0.2 | 0 | False | 1 |

**Recommendation**: High similarity to existing skill(s) — consider extending instead of creating new.
