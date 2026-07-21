---
name: domain-suggest
description: |
  Given a project brief (spec.md, trajectory.md, scope-baseline.md), probes RDAP/whois services to generate 3 production domain name candidates with rationale (memorability, availability, TLD fit). Outp
version: 1.0.0
author: ndethi
license: MIT
tags: ["domain", "suggest", "whois", "rdap", "naming", "framework"]
---

# Domain Suggest

## Overview
Auto-generated skill for capability: Given a project brief (spec.md, trajectory.md, scope-baseline.md), probes RDAP/whois services to generate 3 production domain name candidates with rationale (memorability, availability, TLD fit). Output must be deterministic for the same brief; human selects one. Implements FRAMEWORK.md §13 rule 4: domain-suggest skill.. Given a project brief (spec.md, trajectory.md, scope-baseline.md), probes RDAP/whois services to generate 3 production domain name candidates with rationale (memorability, availability, TLD fit). Outp

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
| scaffold | 7.5 | 15 | False | 0 |
| deploy | 7.0 | 14 | False | 0 |
| evaluate | 6.5 | 13 | False | 0 |
| publish | 6.0 | 12 | False | 0 |
| pm-github | 5.5 | 11 | False | 0 |

**Recommendation**: High similarity to existing skill(s) — consider extending instead of creating new.
