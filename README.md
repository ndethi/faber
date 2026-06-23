# Faber — Agentic Web Framework

> *Faber* (Latin: maker, craftsman, builder). A composable, model-swappable framework for producing client websites with AI agents under spec-driven, drift-resistant control. Read [`FRAMEWORK.md`](FRAMEWORK.md) for the full design; read on for orientation.

## What this is, in one paragraph

A library of **Agent Skills** that cover the website lifecycle — *intent → scaffold → build → evaluate → deploy → publish → observe → feedback* — orchestrated against a **canonical spec** (the single source of truth) and a **trajectory** (the expected process path), with executable acceptance criteria so drift becomes a failing test, not a silent slide. A meta-skill lets the system extend its own library under human-reviewed PRs. A thin Phase-1 portal lets non-technical clients see scope/cost/progress and approve gates, with **git as the backend** so the repo stays the single source of truth.

## Mental model (five lines)

1. **Noisy sources → clean context → canonical spec → conformant code.** Each layer depends only on the one below.
2. **The spec is the source of truth.** Code conforms to the spec; intent changes are deliberate spec PRs.
3. **Drift is a failing test.** Acceptance criteria run in CI; a process-level `trajectory-guard` compares actual vs expected paths.
4. **Agents propose, humans dispose.** Every gate is a PR review.
5. **Skills are model-swappable.** Routine steps can migrate to self-hosted local models (gpt-oss / Nemotron on DGX) once their evals clear threshold.

## Repo layout

```
FRAMEWORK.md            design source of truth (v0.2)
INTERFACE.md            interface decision (chat-first, git-as-backend, thin portal)
IDENTITY.md             naming (Faber)
RUNBOOK.md              harness-agnostic overview (Claude Code or Antigravity)
CHECKSUMS.txt           SHA-256 of every file in this bundle (byte-exact verification)

prompts/                versioned prompt registry — durable specs for each skill
  _registry.md            format + index
  framework.bootstrap.md  · skill.intent-collector.md
  skill.observe-feedback.md · meta.skill-author.md · app.client-portal.md

build-plan/             ordered, harness-executable build steps (00 → 06)
  README.md  build.00-init-foundations.md  build.01-core.md
  build.02-lifecycle-ci.md  build.03-observe-feedback.md
  build.04-meta-cost.md  build.05-client-portal.md
  build.06-rohaki-fixture.md

antigravity/            harness-specific guides (this bundle targets Antigravity CLI)
  SETUP.md              from-zero scaffolding (install → workspace → verify)
  AGY-PROMPTS.md        literal per-step prompts to paste into `agy`
  INBOX-MANIFEST.md     exact file inventory for _inbox/
```

## Two paths through this repo

You'll do path A **once** (when you set up Faber on your machine), then path B **per client website**.

### Path A — Bootstrap Faber (one-time, ~half a day with reviews)

The framework comes into existence when build steps 00→05 actually execute against this bundle. Until then, you have a specification, not a running framework.

1. Read [`antigravity/SETUP.md`](antigravity/SETUP.md) end to end. It takes you from a blank machine to a verified ready state: install `agy`, sign in, create the workspace with a git rollback anchor, unzip this bundle into `_inbox/`, write a bootstrap `AGENTS.md`, **verify `agy` loads it** (the assumption that's bitten everyone before), set permissions, pick your model.
2. Run [`antigravity/AGY-PROMPTS.md`](antigravity/AGY-PROMPTS.md) steps **00 through 05** in order. Each step produces a PR you review and merge. Stop after step 05 — that's when the framework is live and tested on its own surfaces (portal works end-to-end).
3. Step 06 is reserved for the first client (path B below).

You only do this once per machine / team setup.

### Path B — Build a client website (every time)

With Faber bootstrapped, producing a client site is now a series of governed agent runs against the lifecycle ring.

1. **New client branch / project.** From the bootstrapped Faber repo, create a branch (or fork) for the client. Drop their source materials (PDFs, brief, prior site copy) into `fixtures/<client>/` — this is the "sources" layer of the context pyramid.
2. **Intent collection** (`skill.intent-collect`). The agent runs structured elicitation over the client's materials and emits three artifacts deterministically:
   - `spec.md` — canonical, testable site spec with IDed acceptance criteria.
   - `trajectory.md` — expected lifecycle path + checkpoints + strictness (set from production context: prototype / normal / client-production).
   - `scope-baseline.md` — plain-language, client-shareable; seeds the scope ledger.
3. **Client confirms scope** via the portal (HITL gate). Approval lands as a git event; the build can proceed.
4. **Lifecycle execution.** The orchestrator composes the skills in order: `scaffold → build → evaluate → deploy(preview) → publish`. CI runs the acceptance criteria (Lighthouse, a11y, link-check, meta, claim-substantiation, token-lint). `trajectory-guard` compares actual vs expected and reports conformance. The dev gate is PR review; production deploy is gated.
5. **After publish, `observe` + `feedback` engage.** Runtime telemetry (RUM, errors, uptime, client feedback) is triaged into `bug | regression | new-request | spec-gap`. Each triaged item becomes a PR proposal (code fix, spec delta, new eval, or new skill via `skill-author`) — never auto-merged.
6. **Change requests = extended scope.** Any new client request flows through `intent-collect` again, appends an entry to the `scope-ledger` with cost + IP attribution, and re-enters the lifecycle. Baseline scope stays fixed; everything beyond it is visible and billable.

For each subsequent client, repeat from step 1. The framework — skills, orchestrator, dashboard, portal — is shared across clients; only `fixtures/<client>/`, `spec.md`, `trajectory.md`, and `scope-ledger.md` are client-specific.

## Where to go next

- **Setting up Faber for the first time?** → [`antigravity/SETUP.md`](antigravity/SETUP.md) §1.
- **Already set up; ready to run a build step?** → [`antigravity/AGY-PROMPTS.md`](antigravity/AGY-PROMPTS.md).
- **Need to understand a design choice?** → [`FRAMEWORK.md`](FRAMEWORK.md) for design, [`INTERFACE.md`](INTERFACE.md) for the chat-vs-UI call.
- **Adding a new client website?** → Path B above, starting with a new branch + populated `fixtures/<client>/`.

## Status

- **Design:** v0.2 (this bundle) — composable skill library, process-level drift control, governed self-extension, post-deploy feedback loop, thin client portal.
- **Implementation:** unimplemented. Build steps 00→06 produce the running framework; nothing in this bundle has executed yet. The bundle is the *specification* of Faber, not Faber itself.
- **First scaling target:** Rohaki Investments (step 06), brought in separately after step 05 proves the framework end-to-end on its own surfaces.

## Verification

Every file in this bundle is listed in [`CHECKSUMS.txt`](CHECKSUMS.txt). After unzipping:

```bash
cd agentic-web-framework && sha256sum -c CHECKSUMS.txt
# every line must end in "OK"
```

If any line says `FAILED`, your bundle is corrupt or has been edited — re-download before proceeding.
