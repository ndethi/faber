---
kind: build-step
id: build.03-observe-feedback
order: 3
title: Observability + post-deploy feedback + drift guard + dashboard
harness: claude-code | antigravity
model: { recommended: claude-sonnet-4-x, swappable: true }
depends_on: [build.02-lifecycle-ci]
persists:
  - skills/{observe,feedback,trajectory-guard,dashboard}/{SKILL.md,scripts/,evals/}
  - dashboard output as generated static HTML (no backend)
commit: "feat: observe + feedback loop + trajectory-guard + static dashboard"
hitl: "any feedback-loop proposal requires dev approval before it re-enters build"
acceptance:
  - injected out-of-order step is caught by trajectory-guard with correct delta
  - exact strictness blocks; partial only flags
  - injected post-deploy error yields a triaged PR proposal (never auto-merge)
  - dashboard renders from telemetry alone (static HTML, no server)
---

# Build 03 — Observe & Feedback (closes the v0.1 gaps)

## Role
You build the second half of the ring and the drift checker, per `prompts/skill.observe-feedback.md`.

## Procedure
1. Build `observe`, `trajectory-guard`, `feedback`, `dashboard` per the registry entry (specs + ACs there).
2. **Replace the Build-02 trajectory-guard placeholder** in CI with the real check (diff actual vs `trajectory.md`; enforce strictness).
3. `dashboard` emits **generated static HTML** from `runs/*/telemetry.json` + ledger + audit outputs — open the file, no server (Phase 0 per `INTERFACE.md`).
4. Wire the post-deploy loop: `observe → triage → propose (PR) → [HITL] → build → verify`; schedule conformance + health audits.
5. Prove all ACs with synthetic runs (injected deviation; injected error). Commit; PR references `skill.observe-feedback@1.0.0`.

## Done-check
Drift is a failing/flagged signal; post-deploy errors become triaged PRs; the static dashboard renders with no backend.
