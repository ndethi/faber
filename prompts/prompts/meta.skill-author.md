---
id: meta.skill-author
version: 1.0.0
status: draft
intent: Let the system extend its own library — authoring new client-scoped or framework-scoped skills — only ever via a human-approved PR, with a second gate for promotion.
model: { recommended: claude-opus-4-x; swappable: true }
inputs:
  - name: TRIGGER; required: true; note: a recurring lessons/feedback pattern or a named capability gap
  - name: SCOPE; required: false; note: client | framework (default client; framework requires promotion gate)
produces:
  - skills/skill-author/ (the meta-skill)
  - at runtime: a PR proposing a new skill (SKILL.md + scripts + eval + rationale)
depends_on: [framework.bootstrap@1.0.0, skill.observe-feedback@1.0.0]
trajectory_strictness: exact
hitl_gates: [dev approves the new-skill PR, dev approves client→framework promotion]
tags: [meta, self-extension, skills, hitl, governance]
---

# Meta-skill: skill-author

## Role
You build `skill-author`: the governed mechanism by which the system proposes new skills. It never merges anything; it opens PRs for a human to decide.

## Intent (expanded)
Capture recurring work as reusable skills without letting the library sprawl or drift in quality. *Agent proposes, dev disposes.*

## Procedure (what the skill does at runtime)
1. **Validate trigger** — accept only a recurring `lessons.md`/feedback pattern or a named capability gap (≥2 occurrences, or an explicit dev request).
2. **Dedup search** — search existing `skills/` and the registry. If an existing skill covers it, propose an *improvement PR* to that skill instead. **(Hard rule: search before create.)**
3. **Draft** a `SKILL.md` (skill-creator conventions: pushy trigger-oriented description, body < 500 lines, determinism in `scripts/`) + an **eval**. **(Hard rule: no skill without an eval.)**
4. **Run the eval**; attach results.
5. **Classify scope** — `client` (lives in the client repo) vs `framework` (shared library).
6. **Open a PR** with: rationale (the trigger + frequency), the skill, eval results, and the scope classification. **[HITL gate]**
7. **Promotion** — moving a `client` skill to `framework` is a **separate PR** with its own approval. **[HITL gate]**

## Building the skill (your task now)
- Implement steps 1–7 with deterministic dedup + packaging in `scripts/`; the model handles drafting + rationale.
- Wire it to `feedback` (a `spec-gap`/`new-request` of kind "needs-capability" can invoke `skill-author`).
- Eval for the meta-skill itself: given a trigger that duplicates an existing skill → asserts it proposes an *improvement*, not a new skill; given a novel trigger → asserts a PR with `SKILL.md` + eval + rationale is opened and **nothing is merged**.

## Deliverables
`skills/skill-author/{SKILL.md, scripts/, evals/}`.

## Acceptance criteria
- AC-1 Duplicate trigger → improvement PR to the existing skill (no new skill created).
- AC-2 Novel trigger → PR containing `SKILL.md` + `scripts/` + passing eval + rationale.
- AC-3 Nothing is ever auto-merged; both gates require human approval.
- AC-4 `client`-scoped skills land in the client repo; `framework` promotion is a distinct second PR.
- AC-5 A proposed skill without an eval is rejected by the skill's own checks.

## Trajectory
`validate-trigger → dedup-search → draft(+eval) → run-eval → classify → PR →[HITL] → (promotion PR →[HITL])`. Strictness: `exact`.

## Self-improvement hook
This skill governs self-improvement; changes to *its own* gates or rules require a `FRAMEWORK.md` §7 edit (PR) first — it may not relax its own guardrails autonomously.

## Execution command
> Build `skill-author` per this entry. Prove AC-1…AC-5, including that no path auto-merges. Open a PR referencing `meta.skill-author@1.0.0`.
