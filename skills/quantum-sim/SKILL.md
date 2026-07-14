---
name: quantum-sim
description: |
  quantum entanglement simulation
version: 1.0.0
author: ndethi
license: MIT
tags: ["capability", "auto-generated"]
---

# Quantum Sim

## Overview
Auto-generated skill for capability: quantum entanglement simulation. quantum entanglement simulation

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
No existing skills found matching the query. Proceeding with new skill creation.
