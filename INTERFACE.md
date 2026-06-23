# Interface Strategy

> **Decision:** Chat-first for the build loop; **git is the backend**; add a *thin* client-facing UI as a projection over the same git artifacts in Phase 1; defer a full builder UI until multi-client. Skills stay interface-agnostic, so each phase is additive — never a rewrite.

## Users
- **Dev / builder** (your team) — drives builds. Lives in the harness (Claude Code / Antigravity).
- **Client** (e.g. Rohaki) — supplies intent, approves, requests changes, wants to see scope + cost + progress.
- **End-users** of the produced site — out of scope for this decision.

## What chat is / isn't good for
| Great in chat | Poor in chat |
|---|---|
| Dev build loop, agentic edits | Non-technical client access |
| Intent elicitation | Persistent at-a-glance dashboard |
| One-off reasoning/repair | Approval queue with audit trail beyond PRs |
| | Showing client scope/cost over time |

## The core principle
**Skills are interface-agnostic** (file in → file out + telemetry). Whether a skill is invoked by a chat harness or a backend job runner, its contract is identical. Therefore every interface is a *projection* over the same git artifacts (`spec.md`, `trajectory.md`, `runs/*/telemetry.json`, `scope-ledger.md`). The repo is the database; UIs are views. This is what makes the phases additive.

## Phase 0 — git *is* the backend (now, zero UI infra)
- **Approval queue + audit trail** → GitHub **PRs**.
- **Server-side job runner** → GitHub **Actions**.
- **Dashboard (read view)** → a **generated static HTML** built from `runs/*/telemetry.json` (open the file; no server).
- **Billing / scope record** → `scope-ledger.md`.
- **Intent intake** → a structured chat conversation (`intent-collect`) that emits markdown.

This already delivers observability, HITL, and a cost ledger with no app to maintain.

## Phase 1 — thin client portal (when a client needs in)
A minimal backend that adds *only* what git/chat can't give a non-technical client:
- **Auth** (dev + client roles).
- **Read view**: scope baseline, run/trajectory status, cost, deploy previews.
- **Approve actions**: HITL gates (scope sign-off, feedback proposals) — which **write back as commits / PR events**.
- **Server-triggered runs** so the client never opens a terminal.
- **Secrets** (deploy tokens, model keys) + **webhooks** (CI, host, analytics).

Still git-as-SSOT: the portal never forks state; it reads the artifacts and writes approvals back. Spec'd in `prompts/app.client-portal.md`.

## Phase 2 — full builder UI (only if multi-client self-serve)
Clients self-author intent and watch builds live. Justified only once the client count makes the UI cheaper than bespoke dev time. Same artifacts underneath.

## Why backend at all (Phase 1 trigger list)
Build the thin backend when you need any of: client login, client-visible dashboard without git access, server-run agents (no client terminal), held secrets, CI/host/analytics webhooks, or a billable scope/cost record clients can see. Until then, Phase 0 covers it.

## Net
Don't choose chat *or* a builder. Choose **chat-first + git-as-backend now**, **thin projection later**, with skills kept interface-agnostic so you never rebuild.
