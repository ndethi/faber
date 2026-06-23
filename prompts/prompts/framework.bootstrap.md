---
id: framework.bootstrap
version: 1.0.0
status: draft
intent: Stand up the agentic-web-framework repo as a composable skill library with an orchestrator, drift control, and a wired prompt registry — portable to any client, with Rohaki as the test fixture.
model: { recommended: claude-opus-4-x, swappable: true }
inputs:
  - name: TARGET_DIR; required: true; note: empty git repo to scaffold into
  - name: STACK; required: false; note: default Astro
  - name: HOST; required: false; note: default Cloudflare Pages (fallback GitHub Pages)
  - name: STRICTNESS; required: false; note: default ordered
produces:
  - repo scaffold (skills/ orchestrator/ prompts/ fixtures/ .github/)
  - AGENTS.md + CLAUDE.md pointer
  - skill stubs across the lifecycle ring
  - CI workflow running acceptance + trajectory checks
depends_on: []
trajectory_strictness: ordered
hitl_gates: [approve repo plan before scaffolding, approve CI workflow before enabling deploy]
tags: [framework, bootstrap, skills, orchestrator]
---

# Framework Bootstrap

## Role
You are a framework engineer. You build a portable, model-swappable agentic system for producing websites, as a library of Agent Skills governed by a spec-and-trajectory contract. You read `FRAMEWORK.md` (v0.2) as your design source of truth and `prompts/_registry.md` as your format.

## Intent (expanded)
Convert the v0.2 design into a working repo skeleton: a skill library across the lifecycle ring, an orchestrator that composes them per a run plan, cross-cutting drift/observability/cost skills, and a wired registry. The result must run end-to-end against the Rohaki fixture without being coupled to it.

## Preconditions
- `FRAMEWORK.md` and `prompts/_registry.md` present.
- Empty git repo at `TARGET_DIR`.

## Inputs
`TARGET_DIR`, `STACK` (default Astro), `HOST` (default Cloudflare Pages), `STRICTNESS` (default `ordered`).

## Procedure (expected trajectory)
1. **Plan** the repo tree and skill list from `FRAMEWORK.md` §2 and §12. Present the plan. **[HITL gate]**
2. **Scaffold** directories:
   ```
   skills/{intent-collect,scaffold,build,evaluate,deploy,publish,observe,feedback,
           trajectory-guard,model-route,scope-ledger,dashboard,skill-author}/
   orchestrator/   prompts/   fixtures/rohaki/   .github/workflows/
   AGENTS.md  CLAUDE.md  FRAMEWORK.md  README.md
   ```
3. **Stub each skill** with a valid `SKILL.md` (frontmatter `name`+`description`; body: purpose, inputs, outputs, procedure, eval pointer) and an empty `evals/` — full bodies come from their own registry entries.
4. **Author the orchestrator**: reads a run plan (ordered skill list + strictness) and invokes skills in sequence, writing per-run telemetry (skills run, actual trajectory, tokens/cost, model, eval scores) to `runs/<id>/telemetry.json`.
5. **Write `AGENTS.md`** (constitution): read-order = spec → trajectory → FRAMEWORK → lessons; rules = spec is SSOT, one registry `id@version` per PR, no skill without an eval, dedup-search before authoring, prove acceptance + trajectory conformance before "done".
6. **Wire CI** (`.github/workflows/ci.yml`): build → acceptance checks → `trajectory-guard` conformance → preview deploy. Gate prod deploy. **[HITL gate]**
7. **Seed the fixture**: copy distilled Rohaki context into `fixtures/rohaki/` for the scaling test (§11).
8. **Commit** with conventional messages; open a PR referencing `framework.bootstrap@1.0.0`.

## Deliverables
The repo tree above, committed, CI present (deploy gated), fixture seeded.

## Acceptance criteria
- AC-1 Every skill dir has a valid `SKILL.md` (frontmatter parses; description is trigger-oriented).
- AC-2 Orchestrator runs a no-op plan end-to-end and writes `telemetry.json`.
- AC-3 `AGENTS.md` encodes spec-SSOT, one-id-per-PR, eval-required, dedup-before-author.
- AC-4 CI builds and runs `trajectory-guard` (even if trivially) on PRs; prod deploy is gated.
- AC-5 `fixtures/rohaki/` present and isolated from `skills/`.

## Trajectory
`plan →[HITL]→ scaffold → stub → orchestrator → AGENTS.md → CI →[HITL]→ fixture → commit/PR`. Strictness: `ordered`.

## Self-improvement hook
If a needed lifecycle stage is missing from §2, do not silently add it — propose a `FRAMEWORK.md` edit (PR) first, then a new registry entry.

## Execution command
> Read `FRAMEWORK.md` and `prompts/_registry.md`. Execute this entry's Procedure against `TARGET_DIR`, pausing at each `[HITL gate]`. Produce the scaffold, wire CI (deploy gated), seed the Rohaki fixture, and open a PR referencing `framework.bootstrap@1.0.0`.
