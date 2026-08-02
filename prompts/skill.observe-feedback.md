---
id: skill.observe-feedback
version: 1.0.0
status: draft
intent: Close the two gaps in v0.1 — observability and the post-deploy feedback loop — and give the dev a management dashboard plus process-level drift detection.
model: { recommended: claude-sonnet-4-x; swappable: true }
inputs:
  - name: ANALYTICS; required: false; note: privacy-respecting tool (Plausible/Umami/Cloudflare Web Analytics)
  - name: ERROR_TRACKING; required: false; note: e.g. Sentry-compatible endpoint
produces:
  - skills/observe/, skills/feedback/, skills/trajectory-guard/, skills/dashboard/
depends_on: [framework.bootstrap@1.0.0]
trajectory_strictness: ordered
hitl_gates: [dev approves any feedback-loop proposal before it re-enters build]
tags: [skill, observability, feedback, drift, dashboard]
---

# Skills: observe · feedback · trajectory-guard · dashboard

## Role
You build the observability + feedback half of the ring, plus the process-drift checker and the dev dashboard.

## Intent (expanded)
Make every consequence visible (to agent and dev), turn post-deploy signals into governed change, and detect trajectory drift as a first-class signal.

## Procedure (what these skills do at runtime)
**observe** — collect per-run telemetry (skills run, actual trajectory, tokens/cost, model, eval scores, deploy status) and post-deploy signals (RUM/Core Web Vitals, analytics, errors, uptime, link-monitor). Write structured, agent-readable logs.

**trajectory-guard** — diff actual trajectory vs `trajectory.md`; emit a conformance report (match %, missing/extra/out-of-order, gate compliance). On violation: block (`exact`) or flag, and emit a *candidate-improvement* record if the deviation looks beneficial.

**feedback** — run the loop: `triage (bug|regression|new-request|spec-gap) → propose (PR: code fix | spec delta | new eval | new skill) → [HITL] → build → verify`. Route `new-request` items to `scope-ledger` as extended scope. Schedule periodic post-deploy conformance + health audits.

**dashboard** — internal builder tool surfacing: runs + expected-vs-actual trajectory diff; cost per run/skill; model-routing decisions; eval pass/fail; deploy health; post-deploy RUM; HITL queue; scope ledger.

## Building the skills (your task now)
- One `SKILL.md` per skill, pushy descriptions, deterministic collection/diff logic in `scripts/`.
- `dashboard` reads only from `runs/*/telemetry.json` + ledger + audit outputs (no bespoke data path).
- Evals: feed a synthetic run with a known deviation → assert `trajectory-guard` catches it; feed a synthetic error signal → assert `feedback` produces a triaged PR proposal (not an auto-merge).

## Deliverables
`skills/{observe,feedback,trajectory-guard,dashboard}/{SKILL.md,scripts/,evals/}`.

## Acceptance criteria
- AC-1 A run with an injected out-of-order step is flagged by `trajectory-guard` with the correct delta.
- AC-2 `exact` strictness blocks; `partial` only flags — verified by eval.
- AC-3 An injected post-deploy error yields a **triaged PR proposal**, never an auto-merge (HITL preserved).
- AC-4 `dashboard` renders runs, trajectory diff, cost, HITL queue, and scope ledger from telemetry alone.
- AC-5 A scheduled audit compares live routes to `spec.md` and reports deltas.

## Trajectory
`observe → trajectory-guard → feedback(triage→propose→[HITL]→build→verify); dashboard reads throughout`. Strictness: `ordered`.

## Self-improvement hook
Recurring triage categories that don't fit `bug|regression|new-request|spec-gap` → propose a taxonomy change (PR) to `feedback`.

## Execution command
> Build `observe`, `trajectory-guard`, `feedback`, and `dashboard` per this entry. Prove AC-1…AC-5 with synthetic runs. Open a PR referencing `skill.observe-feedback@1.0.0`.
