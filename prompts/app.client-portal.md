---
id: app.client-portal
version: 0.1.0
status: draft
intent: A thin, client-facing UI that projects over the repo's git artifacts — read scope/runs/cost, approve HITL gates (writing back as commits/PR events), and trigger runs — without forking state from git.
model: { recommended: claude-sonnet-4-x; swappable: true }
inputs:
  - name: AUTH; required: true; note: dev + client roles
  - name: REPO; required: true; note: the client project repo (SSOT)
produces:
  - app/ (thin backend + UI) reading git artifacts, writing approvals back
depends_on: [framework.bootstrap@1.0.0, skill.observe-feedback@1.0.0, skill.scope-ledger@1.0.0]
trajectory_strictness: ordered
hitl_gates: [dev approves before exposing any write action to clients]
tags: [interface, phase-1, portal, projection, hitl]
---

# App: client-portal (Phase 1)

## Role
You build a thin client portal that is a **view over git**, never a second source of truth.

## Intent (expanded)
Give non-technical clients a way to see scope/cost/progress and approve gates, while every write lands back in git (commit or PR event). Defer all logic that belongs in skills — the portal only reads artifacts and relays approvals.

## Procedure (what the portal does at runtime)
1. **Read** from the repo only: `scope-baseline.md`, `spec.md`, `trajectory.md`, `runs/*/telemetry.json`, `scope-ledger.md`, deploy preview URLs.
2. **Render** for the client: scope, run/trajectory status, cost, extended-scope items, preview links.
3. **Approve** HITL gates (scope sign-off, feedback proposals) → translate the click into a **commit or PR review event** (the gate's source of truth stays git).
4. **Trigger** a run server-side (dispatch a CI/job-runner event); stream status from telemetry.
5. **Auth** dev vs client scopes; secrets held server-side only.

## Building it (your task — only if Phase 1 is chosen)
- Keep the backend minimal (read git + GitHub API; write via commits/PR/dispatch). No bespoke database that duplicates git state.
- Static-first read view; write actions gated behind auth. **[HITL gate before any client-exposed write]**
- Eval: assert an approval click produces the correct git event and that the portal renders correctly from telemetry alone (no hidden state).

## Acceptance criteria
- AC-1 Portal renders scope/runs/cost from git artifacts only (no separate DB of truth).
- AC-2 An approval click results in the corresponding commit/PR event; revoking in git reflects back in the UI.
- AC-3 A run can be triggered without the client touching a terminal.
- AC-4 Secrets never reach the client; role separation enforced.

## Trajectory
`read → render → (approve → git event) | (trigger → dispatch) ; auth throughout`. Strictness: `ordered`.

## Self-improvement hook
If clients repeatedly need a view the portal can't render from existing artifacts, propose the missing artifact in `spec`/telemetry (PR) first — don't add portal-local state.

## Execution command
> Only if Phase 1 is selected: build `app/` per this entry, proving AC-1…AC-4 (git remains SSOT). Open a PR referencing `app.client-portal@0.1.0`.
