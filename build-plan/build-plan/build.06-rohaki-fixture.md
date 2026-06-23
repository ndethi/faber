---
kind: build-step
id: build.06-rohaki-fixture
order: 6
title: Prove it scales — Rohaki end-to-end
harness: claude-code | antigravity
model: { recommended: claude-opus-4-8, swappable: true }
depends_on: [build.05-client-portal]
persists:
  - fixtures/rohaki/runs/<id>/ (telemetry + acceptance results + trajectory conformance report)
commit: "test: rohaki end-to-end scaling run + conformance report"
hitl: "client confirms scope-baseline before the build proceeds"
acceptance:
  - end-to-end run over fixtures/rohaki passes the site acceptance criteria
  - trajectory conformance >= threshold under `ordered` strictness
  - the run is visible in the client portal (scope, cost, status)
---

# Build 06 — Rohaki scaling test (only after the framework is solid)

## Role
You exercise the *whole* framework — including the now-built portal — against a real client fixture. Rohaki is the test, not the subject.

## Procedure
1. Run `intent-collect` over `fixtures/rohaki/` → `spec.md` + `trajectory.md` + `scope-baseline.md`. **[HITL]** client confirms scope.
2. Execute the lifecycle: `scaffold → build → evaluate → deploy(preview) → publish → observe`, strictness `ordered`.
3. `trajectory-guard` compares actual vs expected; `dashboard`/portal surface the run, cost, and status.
4. Write `fixtures/rohaki/runs/<id>/` with telemetry, acceptance results, and the trajectory conformance report.
5. If acceptance + conformance both pass, set the exercised registry entries `status: active`. Commit.

## Done-check
Rohaki builds end-to-end; site acceptance passes; trajectory conformance clears threshold under `ordered`; the run is visible in the portal. Any drift surfaced as a failing/flagged check — by design. The framework is proven to scale to a real client.
