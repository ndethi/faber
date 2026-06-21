---
kind: build-step
id: build.05-client-portal
order: 5
title: Stand up the thin client portal (Phase 1)
harness: claude-code | antigravity
model: { recommended: claude-sonnet-4-6, swappable: true }
depends_on: [build.04-meta-cost]
persists:
  - app/ (thin backend + UI projecting over git artifacts) per app.client-portal@0.1.0
commit: "feat: phase-1 client portal (view over git; approvals write back)"
hitl: "approve before exposing any client-facing write action"
acceptance:
  - portal renders scope/runs/cost from git artifacts only (no separate DB of truth)
  - an approval click produces the corresponding commit/PR event; git remains SSOT
  - a run can be triggered without the client touching a terminal; secrets stay server-side
---

# Build 05 — Client portal (decision: build now, before Rohaki)

## Role
You build the Phase-1 client surface per `prompts/app.client-portal.md`. It is a **view over git**, never a second source of truth. Standing it up now hardens the framework before the Rohaki test.

## Procedure
1. Build `app/` per `app.client-portal@0.1.0`: read-only render of `scope-baseline.md`, `spec.md`, `trajectory.md`, `runs/*/telemetry.json`, `scope-ledger.md`, preview URLs.
2. Add **auth** (dev + client roles); hold secrets server-side only.
3. Wire **approve** actions → translate clicks into commit / PR-review events (the gate's truth stays in git).
4. Wire **trigger-run** → dispatch a CI/job-runner event; stream status from telemetry.
5. **[HITL]** Review before exposing any client-facing write; then enable.
6. Prove AC-1…AC-3 (incl. that revoking in git reflects back in the UI). Commit; PR references `app.client-portal@0.1.0`.

## Done-check
A non-technical user can log in, see scope/cost/progress, approve a gate (which lands as a git event), and trigger a run — with git still the single source of truth. Framework is now portal-complete and ready to be tested on a real client.
