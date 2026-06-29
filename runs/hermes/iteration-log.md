# Iteration Log — Faber Phase A*

*Append-only history of gap-closing iterations*

---

## Iteration 0 — 2026-06-29T00:52:00Z
**Action:** Initialized Phase A* state files
- Created `STATE.json` with phase=A*, iteration=0, composite=0.0
- Created `backlog.md` with 10 items from state report + HERMES-BRIEF §7
- Created this `iteration-log.md`
- **Branch:** dev (will create hermes/ topic branch for first work item)
- **Next:** Human review of backlog prioritization; begin Iteration 1

---
---
## Iteration 1 — 2026-06-29T01:18:00Z
**Action:** AGENTS.md swap to canonical (BG-001)
- Replaced bootstrap constitution with canonical version per FRAMEWORK.md
- Preserved human Commitizen + PR-policy additions
- Added branch model, HITL gates, telemetry, feedback loop, self-extension rules
- **Commit:** f0c4921 `feat: replace bootstrap AGENTS.md with canonical constitution`
- **Branch:** hermes/agents-canonical-swap
- **Diff:** +146/-46 lines
- **PR:** #7 https://github.com/ndethi/faber/pull/7
- **Next:** Await human review & merge (HITL gate)

---
## Iteration 2 — 2026-06-29T01:30:00Z
**Action:** skills/build/ correction (BG-002)
- **Spec reference:** HERMES-BRIEF §7 item 2; build-plan/build-plan/build.02-lifecycle-ci.md; FRAMEWORK.md §8 default (Astro + Cloudflare Pages)
- **Plan:**
  1. Update `skills/build/SKILL.md` to reference Astro + Cloudflare Pages as framework defaults (not npm/esbuild/webpack)
  2. Implement actual build scripts in `skills/build/scripts/` (Astro build wrapper with Cloudflare Pages output)
  3. Add `skills/build/evals/` with deterministic eval proving build produces expected artifacts
- **Expected diff:** ~50-80 lines across SKILL.md + new scripts/ + new evals/
- **Branch:** hermes/build-skill-correction
- **PR target:** dev (referencing skill.build@1.0.0 registry entry when created)
- **Constraint:** Per HERMES-BRIEF §1.8, no further skills until this one is eval-compliant
- **Result:** ✓ SKILL.md updated with Astro + Cloudflare Pages defaults; ✓ build.py implements Astro build wrapper with package.json check; ✓ test_build.py passes 6/6 tests (pytest + direct); ✓ BG-002 marked done
- **Diff:** ~120 lines added across SKILL.md, build.py, test_build.py
- **Next:** Iteration 3 — Orchestrator + telemetry (BG-003) and/or intent-collect skill (build.01-core)

---
## Iteration 4 — 2026-06-29T18:00:00Z (planned, parallel)
**Action:** BG-004 (intent-collect) + BG-011 (pr-review-resolution) — parallel via subagents
- **Spec references:** build.01-core (intent-collect); FRAMEWORK.md §1, §2, §7 (skill contract, cross-cutting, self-extension)
- **Subagent 1 (BG-004):** Build `intent-collect` skill per `skill.intent-collector@1.0.0` registry — emits spec.md, trajectory.md, scope-baseline.md; eval on fixtures/rohaki
- **Subagent 2 (BG-011):** Build `pr-review-resolution` skill:
  1. `fetch_comments.py` — gh API (no email)
  2. `categorize.py` — deterministic regex/heuristics (style, docs, security, test, logic, design)
  3. `resolve.py` — auto-fix (ruff/prettier), LLM patch for logic/design, defer unknown
  4. `apply_fixes.py` — git commit, push to hermes/<topic>
  5. `update_pr.py` — gh pr comment with fix SHA, resolve conversation
  6. `notify.py` — Telegram via Hermes gateway
  7. `analyze.py` — historical pattern analysis (read-only)
  8. Evals: mock fixtures, categorization accuracy, fix compilation, integration
- **Dependencies:** orchestrator (local, from BG-003), gh auth, Hermes gateway
- **HITL:** Configurable gate before push (default true)
- **Branch:** hermes/pr-review-resolution (this branch)
- **PR target:** dev (skill.pr-review-resolution@1.0.0)
- **Constraint:** Per AGENTS.md §2.7 — no autonomous skill creation; manual PR with eval
- **Result:** ✓ telemetry.schema.json extended with expected_trajectory + trajectory_strictness; ✓ orchestrator/orchestrator.py implements plan execution + telemetry writing; ✓ runs/noop-plan.json no-op plan; ✓ orchestrator/evals/test_orchestrator.py passes 7/7 tests; ✓ BG-003 marked done
- **Diff:** ~200 lines added across schema, orchestrator.py, noop-plan.json, test_orchestrator.py, noop skill
- **Next:** Iteration 4 — intent-collect skill (build.01-core) or remaining HIGH priority items

---
## Iteration 4 (Planned) — PR Review Resolution Skill (BG-011)
**Action:** New skill: PR Review Resolution
- **Source:** User request — systematically resolve Copilot/GH review comments from email
- **Skill name:** `pr-review-resolution` (lifecycle-adjacent, cross-cutting)
- **Spec reference:** FRAMEWORK.md §1 (skill contract), §2 (cross-cutting skills), HERMES-BRIEF §1.4 (no autonomous skill creation)
- **Plan:**
  1. **Draft SKILL.md** at `skills/pr-review-resolution/SKILL.md` with:
     - Description: "Fetches review comments from GitHub PR (via gh API or email parsing), categorizes by type (nit, bug, design, test), generates fixes, pushes to branch, updates PR"
     - Inputs: PR number, repo, comment source (gh API / email / webhook)
     - Outputs: Resolution report (comment_id → fix_commit_sha / deferred / wontfix)
     - Interface: JSON in/out for orchestrator compatibility
  2. **Implement scripts/**:
     - `fetch_comments.py` — gh pr view --comments / parse email via himalaya/IMAP
     - `categorize.py` — classify comments (style, logic, test, docs, security)
     - `resolve.py` — for each comment: generate fix (AST edit / LLM), run tests, commit
     - `push_update.py` — push to hermes/<topic> branch, update PR description
  3. **Add evals/**:
     - Test with mock PR comments (fixture)
     - Verify categorization accuracy
     - Verify fix compiles + tests pass
     - Verify git operations (commit, push, PR update)
  4. **Registry entry** in `prompts/prompts/skill.pr-review-resolution.md`
  5. **PR** targeting `dev` referencing `skill.pr-review-resolution@1.0.0`
- **Dependencies:** Requires `gh` CLI auth, `himalaya` for email (optional), git write access
- **Constraints:** 
  - Per AGENTS.md §2.7: no autonomous skill creation → manual PR (skill-author not yet built)
  - Per FRAMEWORK.md §1: must have evals
  - HITL gate: human reviews generated fixes before push (configurable)
- **Expected diff:** ~300000-400 lines across SKILL.md, 4-5 scripts, evals, registry entry
- **Branch:** hermes/pr-review-resolution
- **Priority:** MEDIUM (after BG-004 intent-collect, or parallel if subagent)
- **Related:** Enables automated PR iteration loop; integrates with orchestrator + trajectory-guard
- **Result:** ✓ telemetry.schema.json extended with expected_trajectory + trajectory_strictness fields; ✓ orchestrator/orchestrator.py implemented with skill invocation + telemetry writing; ✓ runs/noop-plan.json created as no-op proof; ✓ orchestrator/evals/test_orchestrator.py passes 7/7 tests (pytest); ✓ orchestrator runs no-op plan and writes valid telemetry with trajectory fields; ✓ telemetry validates against schema
- **Diff:** ~250 lines added across schema, orchestrator, noop-plan, eval
- **Next:** Iteration 4 — intent-collect skill (build.01-core) and/or trajectory-guard skill