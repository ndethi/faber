---
id: skill.intent-collector
version: 1.0.0
status: draft
intent: Turn fuzzy client conversation into a deterministic, testable spec plus an expected trajectory and a client-shareable scope baseline — the only sanctioned way to create or change intent.
model: { recommended: claude-opus-4-x, swappable: true }
inputs:
  - name: CLIENT_CONTEXT; required: true; note: conversation, brief, and/or distilled context files
  - name: PRODUCTION_CONTEXT; required: true; note: prototype | normal | client-production (sets default strictness)
produces:
  - skills/intent-collect/SKILL.md (+ scripts, eval)
  - emits at runtime: spec.md, trajectory.md, scope-baseline.md
depends_on: [framework.bootstrap@1.0.0]
trajectory_strictness: exact
hitl_gates: [client confirms scope-baseline before build begins]
tags: [skill, intent, spec, trajectory, scope]
---

# Skill: intent-collect

## Role
You build the `intent-collect` skill: a structured elicitation procedure that deterministically converts inputs into the canonical intent artifacts.

## Intent (expanded)
Be the front door of the lifecycle. Same inputs → same artifact *structure* (deterministic), with testable acceptance criteria and an expected trajectory. Make scope explicit and shareable so later requests are visibly "extended scope."

## Preconditions
Framework scaffold present (`framework.bootstrap`). A place to write `spec.md`, `trajectory.md`, `scope-baseline.md`.

## Inputs
`CLIENT_CONTEXT`, `PRODUCTION_CONTEXT`.

## Procedure (what the skill, once built, does at runtime)
1. **Extract** known facts from `CLIENT_CONTEXT` first (don't re-ask what's answered).
2. **Elicit** gaps via a fixed question set: goals, audiences + jobs-to-be-done, non-goals, IA, content model, constraints, success metrics. Surface unknowns as `TODO:` rather than inventing.
3. **Emit `spec.md`** — canonical SSOT with IDed acceptance criteria (`SPEC-NN`).
4. **Derive `trajectory.md`** — ordered DAG of lifecycle skill steps + checkpoints + gates; set strictness from `PRODUCTION_CONTEXT` (prototype→partial, normal→ordered, client-production→exact).
5. **Emit `scope-baseline.md`** — plain-language, client-shareable; seeds `scope-ledger`.
6. **Confirm** the scope baseline with the client. **[HITL gate]**

## Building the skill (your task now)
- Write `SKILL.md` with a pushy, trigger-oriented `description` ("Use whenever a new site, rebuild, or scope change is requested…").
- Put the question set + emission logic in `scripts/` (deterministic structure); keep the body < 500 lines.
- Add an **eval**: given a fixture brief (use `fixtures/rohaki/`), assert the three artifacts are produced with required sections and at least N IDed acceptance criteria, and that re-running yields the same structure (determinism check).

## Deliverables
`skills/intent-collect/{SKILL.md, scripts/, evals/}`.

## Acceptance criteria
- AC-1 Running on the Rohaki fixture produces `spec.md`, `trajectory.md`, `scope-baseline.md`.
- AC-2 `spec.md` has ≥1 IDed acceptance criterion per route; non-goals present.
- AC-3 `trajectory.md` strictness matches `PRODUCTION_CONTEXT` mapping.
- AC-4 Determinism: two runs on identical inputs yield identical artifact structure.
- AC-5 Unknowns appear as `TODO:`, never fabricated.

## Trajectory
`extract → elicit → spec → trajectory → scope-baseline →[HITL]→ confirm`. Strictness: `exact`.

## Self-improvement hook
If the fixed question set repeatedly misses a needed field, propose a question-set change as a PR to this skill (versioned), not an ad-hoc edit.

## Execution command
> Build the `intent-collect` skill per this entry. Validate it by running against `fixtures/rohaki/` and confirming AC-1…AC-5. Open a PR referencing `skill.intent-collector@1.0.0`.
