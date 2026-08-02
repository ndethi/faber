---
kind: build-step
id: build.00-init-foundations
order: 0
title: Initialize repo and persist canonical foundations
harness: claude-code | antigravity
model: { recommended: claude-sonnet-4-x, swappable: true }
depends_on: []
persists:
  - .gitignore (if missing), README.md, FRAMEWORK.md, INTERFACE.md, IDENTITY.md, RUNBOOK.md (if present in _inbox), AGENTS.md (canonical, replacing bootstrap), CLAUDE.md
  - prompts/ (registry + all entries)
  - build-plan/ (all step files)
  - skills/ (empty stubs), orchestrator/, runs/, fixtures/, .github/workflows/
commit: "chore: scaffold faber + persist canonical foundations"
hitl: false
acceptance:
  - canonical docs match _inbox byte-for-byte (no regeneration)
  - dir skeleton present; repo committed
  - the canonical AGENTS.md has replaced the bootstrap one and is still loaded by agy (`/context` confirms)
  - fixtures/ exists but is empty (client fixtures are populated separately at step 06)
---

# Build 00 — Init & Foundations

## Role
Repo initializer. You persist existing canonical artifacts exactly; you do not rewrite them.

## Procedure
1. Verify the **bootstrap state**: workspace is git-initialized, has a rollback commit, `_inbox/` is populated, and a bootstrap `AGENTS.md` is at the workspace root. If any of these is missing, STOP and report.
2. Create the skeleton:
   ```
   skills/{intent-collect,scaffold,build,evaluate,deploy,publish,observe,feedback,
           trajectory-guard,model-route,scope-ledger,dashboard,skill-author}/
   orchestrator/  prompts/  runs/  fixtures/  build-plan/  .github/workflows/
   ```
   `fixtures/` is created empty; client fixtures (e.g. Rohaki) are added separately at step 06.
3. **Persist from `_inbox/` unchanged**: copy `FRAMEWORK.md`, `INTERFACE.md`, `IDENTITY.md`, `RUNBOOK.md` (if present), all `prompts/*.md`, and all `build-plan/*.md`. Copy, do not regenerate.
4. Write the **canonical `AGENTS.md`** (constitution): read-order = `spec → trajectory → FRAMEWORK → INTERFACE → lessons`; rules = spec is SSOT, one registry `id@version` per PR, no skill without an eval, dedup-search before authoring, prove acceptance + trajectory conformance before "done", git is the source of truth for all state. **Overwrite the bootstrap `AGENTS.md`** with this. Add `CLAUDE.md` pointing to `AGENTS.md`.
5. Write `README.md` (orientation: the lifecycle ring, repo-as-database, how to run the build plan).
6. Verify canonical files equal `_inbox/` (checksum). Commit.

## Done-check
`git log` shows the new commit; `diff -r _inbox <repo paths>` is empty for persisted files; skeleton dirs exist; `fixtures/` exists and is empty; the canonical `AGENTS.md` has replaced the bootstrap one and `agy` still shows it loaded in `/context`.
