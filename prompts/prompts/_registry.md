# Prompt Registry

Versioned, testable prompt artifacts that **persist intent**. Each entry is a self-contained spec an agent (Claude Code / Antigravity, any model) can execute to produce a defined deliverable. The format extends the project's existing role-template style (Role · Task · Outputs · Quality · Execution) with registry metadata, an explicit **trajectory**, and **HITL gates**.

## Why a registry (not loose prompts)
- **Versioned** — intent changes are diffable history, not lost edits.
- **Testable** — every entry carries acceptance criteria + an expected trajectory.
- **Composable** — entries declare `depends_on`; the orchestrator chains them.
- **Model-swappable** — `model` is a recommendation, not a requirement.
- **Governed** — `hitl_gates` mark where a human must approve.

## Entry format

````markdown
---
id: <namespace.name>            # e.g. skill.intent-collector
version: <semver>               # 1.0.0
status: draft | active | deprecated
intent: <one sentence>          # the durable why
model: { recommended: <id>, swappable: true }
inputs:                         # variables / placeholders
  - name: <VAR>; required: true|false; note: <desc>
produces:                       # concrete deliverables (paths/artifacts)
  - <path-or-artifact>
depends_on: [<id@version>, ...]
trajectory_strictness: exact | ordered | partial
hitl_gates: [<where a human approves>, ...]
tags: [...]
---

# <Title>

## Role
<persona the executing agent adopts>

## Intent (expanded)
<what durable goal this serves and why>

## Preconditions
<what must exist before running>

## Inputs
<the variables above, expanded>

## Procedure  (= the expected trajectory; steps are checkpoints)
1. ...
2. ...

## Deliverables
<exactly what is produced, where>

## Acceptance criteria  (testable; become evals/CI)
- AC-1 ...

## Trajectory  (expected ordered path + gates; checked by trajectory-guard)
- step order, checkpoints, and which steps are HITL gates

## Self-improvement hook
<what to append to lessons.md / propose as a spec or skill PR if surprised>

## Execution command
<the literal instruction to begin>
````

## Index

|| id | intent | produces | depends_on ||
|---|---|---|---|---|---|
|| `framework.bootstrap` | Stand up the framework repo + skill library + orchestrator | repo scaffold, registry wired, `AGENTS.md` | — ||
|| `skill.intent-collector` | Turn client conversation into deterministic spec + trajectory + scope baseline | `intent-collect/` skill | `framework.bootstrap` ||
|| `skill.observe-feedback` | Close observability + post-deploy feedback gaps | `observe/`, `feedback/`, `trajectory-guard/`, `dashboard/` skills | `framework.bootstrap` ||
|| `meta.skill-author` | Let the system author new skills via PR under HITL | `skill-author/` skill | `framework.bootstrap`, `skill.observe-feedback` ||
|| `skill.faber-cms@1.1.0` | Generate CMS with Worker API (D1) + Embedded Admin UI | CMS Worker project + Admin UI project | `framework.bootstrap` ||

## Conventions
- One registry entry = one deliverable = (ideally) one PR.
- A PR's description references the `id@version` it satisfies.
- Bump `version` (semver) on any intent change; never silently rewrite.
- `status: active` only after the entry's acceptance criteria pass at least once.
