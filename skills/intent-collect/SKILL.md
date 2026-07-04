---
name: intent-collect
description: |
  Turn fuzzy client conversation into a deterministic, testable spec plus an 
  expected trajectory and a client-shareable scope baseline — the only sanctioned 
  way to create or change intent. Produces spec.md, trajectory.md, scope-baseline.md.
version: 1.0.0
author: ndethi
license: MIT
tags: [intent, spec, trajectory, scope, lifecycle]
---

# Intent-Collect Skill

## Overview
The deterministic front door of the Faber lifecycle. Transforms ambiguous client 
context into three canonical artifacts:
- **spec.md** - Source of truth with IDed acceptance criteria (SPEC-NN)
- **trajectory.md** - Expected path: ordered DAG of lifecycle steps + checkpoints + gates
- **scope-baseline.md** - Plain-language, client-shareable; seeds the scope ledger

Same inputs → same artifact structure (deterministic). Enables process-level 
drift control via trajectory-guard and client alignment via scope baseline.

## Interface
```json
{
  "client_context": "string",    // conversation, brief, distilled context
  "production_context": "string" // prototype | normal | client-production
}
```
Outputs written to current directory:
- `spec.md`
- `trajectory.md` 
- `scope-baseline.md`

## Evaluation
The skill passes when:
- All three output files exist with required sections
- spec.md contains ≥1 IDed acceptance criterion per functional area
- trajectory.md strictness matches production_context mapping
- Two runs on identical inputs yield identical file structure (determinism)
- Unknowns appear as `TODO:`, never fabricated details

## Determinism & HITL
- **Determinism**: File structure and section headers are deterministic given same inputs
- **HITL Gate**: scope-baseline.md requires client confirmation before build proceeds (per build.01-core)
- **Unknown Handling**: Gaps in client_context surface as `TODO:` items, never invented