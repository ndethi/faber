---
kind: build-step
id: build.01-core
order: 1
title: Orchestrator, telemetry, and the intent front door
harness: claude-code | antigravity
model: { recommended: claude-opus-4-x, swappable: true }
depends_on: [build.00-init-foundations]
persists:
  - orchestrator/ (run-plan reader + skill invoker + telemetry writer)
  - runs/telemetry.schema.json
  - skills/intent-collect/{SKILL.md, scripts/, evals/}
commit: "feat: orchestrator + telemetry + intent-collect"
hitl: "client confirms scope-baseline before any build proceeds"
acceptance:
  - orchestrator runs a no-op plan and writes runs/<id>/telemetry.json
  - intent-collect passes its eval on fixtures/rohaki (spec.md + trajectory.md + scope-baseline.md)
---

# Build 01 — Core engine + intent

## Role
Engine builder. You make the orchestrator and the deterministic front door.

## Procedure
1. **Telemetry schema** (`runs/telemetry.schema.json`): run id, ordered skills invoked (actual trajectory), tokens + cost, model used, eval scores, deploy status, timestamps.
2. **Orchestrator** (`orchestrator/`): reads a run plan (ordered skill list + strictness), invokes skills in sequence, writes `runs/<id>/telemetry.json` against the schema. Prove with a no-op plan.
3. **Build `intent-collect`** per `prompts/skill.intent-collector.md` (its registry entry is the spec). Implement the fixed question set + emission logic in `scripts/`; keep `SKILL.md` body < 500 lines; add the eval.
4. Run the intent-collect eval against `fixtures/rohaki/`; confirm it emits `spec.md`, `trajectory.md`, `scope-baseline.md` deterministically.
5. **[HITL]** Present `scope-baseline.md` for client confirmation before downstream steps.
6. Commit; open a PR referencing `skill.intent-collector@1.0.0`.

## Done-check
Orchestrator writes valid telemetry; intent-collect eval green on the fixture; scope baseline awaiting human approval.
