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

## Iteration 3 — 2026-06-29T17:00:00Z
**Action:** Orchestrator + telemetry (BG-003)
- **Spec reference:** build-plan/build-plan/build.01-core.md; FRAMEWORK.md §4-5; HERMES-BRIEF §7
- **Plan:**
  1. Extend `runs/telemetry.schema.json` with trajectory fields (expected vs actual trajectory, strictness)
  2. Implement `orchestrator/orchestrator.py`: reads run plan (ordered skill list + strictness), invokes skills sequentially, writes `runs/<id>/telemetry.json` against schema
  3. Add no-op run plan to prove orchestrator works
  4. Add eval for orchestrator (run no-op plan → validate telemetry output)
- **Expected diff:** ~150-200 lines across schema + orchestrator + run plan + eval
- **Branch:** hermes/orchestrator-telemetry
- **PR target:** dev (referencing skill.orchestrator@1.0.0 when registry entry created)
- **Constraint:** Per build.01-core acceptance: orchestrator runs no-op plan and writes valid telemetry
- **Result:** ✓ telemetry.schema.json extended with expected_trajectory + trajectory_strictness; ✓ orchestrator/orchestrator.py implements plan execution + telemetry writing; ✓ runs/noop-plan.json no-op plan; ✓ orchestrator/evals/test_orchestrator.py passes 7/7 tests; ✓ BG-003 marked done
- **Diff:** ~200 lines added across schema, orchestrator.py, noop-plan.json, test_orchestrator.py, noop skill
- **Next:** Iteration 4 — intent-collect skill (build.01-core) or remaining HIGH priority items

---

## Iteration 4 — 2026-06-30T06:09:00Z
**Action:** PR Review Resolution Skill (BG-011)
- **Source:** User request — systematically resolve Copilot/GH review comments
- **Skill name:** `pr-review-resolution` (lifecycle-adjacent, cross-cutting)
- **Spec reference:** FRAMEWORK.md §1 (skill contract), §2 (cross-cutting skills), HERMES-BRIEF §1.4 (no autonomous skill creation)
- **Plan:**
  1. **Draft SKILL.md** at `skills/pr-review-resolution/SKILL.md` with:
     - Description: "Fetches review comments from GitHub PR (via gh API), categorizes by type, generates fixes, pushes to branch, updates PR"
     - Inputs: PR number, repo, hitl_gate flag
     - Outputs: Resolution report (comment_id → fix status)
     - Interface: JSON in/out for orchestrator compatibility
  2. **Implement scripts/**:
     - `fetch_comments.py` — gh pr view --comments
     - `categorize.py` — classify comments (style, docs, security, test, logic, design)
     - `resolve.py` — for each comment: generate fix (auto/llm/deferred), run tests, commit
     - `apply_fixes.py` — apply fixes with HITL gate
     - `notify.py` — send Telegram notifications
     - `pr_review_resolution.py` — main entry point
  3. **Add evals/**:
     - Test with mock PR comments (fixture)
     - Verify categorization accuracy
     - Verify fix compiles + tests pass
     - Verify git operations (commit, push, PR update)
  4. **Registry entry** already exists at `skills/pr-review-resolution/SKILL.md`
  5. **PR** merged to dev
- **Dependencies:** `gh` CLI auth
- **Constraints:** 
  - Per AGENTS.md §2.7: no autonomous skill creation → manual PR (skill-author not yet built)
  - Per FRAMEWORK.md §1: must have evals
  - HITL gate: human reviews generated fixes before push (configurable via --hitl-gate)
- **Expected diff:** ~300-400 lines across SKILL.md, 5 scripts, evals
- **Branch:** hermes/pr-review-resolution → merged to dev
- **Priority:** MEDIUM (BG-004 intent-collect is next)
- **Related:** Enables automated PR iteration loop; integrates with orchestrator + trajectory-guard
- **Result:** ✓ All 21 Copilot comments resolved on PR #10; ✓ PR #9 (orchestrator) and PR #10 merged; ✓ evals pass; ✓ BG-011 marked done
- **Diff:** ~1620 lines added (skills/pr-review-resolution/*), ~14 lines deleted (scope creep from BG-003)
- **Next:** Iteration 5 — intent-collect skill (BG-004)

---

## Iteration 5 — 2026-06-30T06:45:00Z
**Action:** Build intent-collect skill (BG-004)
- **Source:** State Report + FRAMEWORK.md §3 (lifecycle ring)
- **Skill name:** `intent-collect` (lifecycle skill #1)
- **Spec reference:** FRAMEWORK.md §3; build-plan/build-plan/build.01-core.md; prompts/skill.intent-collector.md
- **Plan:**
  1. **Create `skills/intent-collect/{SKILL.md, scripts/, evals/}`** per FRAMEWORK skill contract
  2. **Draft SKILL.md** at `skills/intent-collect/SKILL.md` with:
     - Description: "Turn fuzzy client conversation into a deterministic, testable spec plus an expected trajectory and a client-shareable scope baseline — the only sanctioned way to create or change intent."
     - Inputs: CLIENT_CONTEXT, PRODUCTION_CONTEXT
     - Outputs: spec.md, trajectory.md, scope-baseline.md
     - Interface: JSON in/out for orchestrator compatibility
  3. **Implement scripts/**:
     - `intent_collect.py` — structured elicitation: extract → elicit → spec → trajectory → scope-baseline → HITL
     - Fixed question set: goals, audiences+JTBD, non-goals, IA, content model, constraints, success metrics
     - Emit spec.md with IDed acceptance criteria (SPEC-NN)
     - Derive trajectory.md — ordered DAG of lifecycle skill steps + checkpoints + gates
     - Emit scope-baseline.md — plain-language, client-shareable; seeds scope-ledger
  4. **Add evals/**:
     - Test with fixture brief (use existing output/ as fixture or create fixtures/rohaki/)
     - Assert the three artifacts are produced with required sections
     - Verify at least N IDed acceptance criteria in spec.md
     - Verify re-running yields identical artifact structure (determinism check)
     - Verify unknowns appear as `TODO:`, never fabricated
  5. **Registry entry** in `prompts/prompts/skill.intent-collector.md` (already exists)
  6. **PR** targeting `dev` referencing `skill.intent-collector@1.0.0`
- **Dependencies:** orchestrator already built (BG-003)
- **Constraints:** 
  - Per AGENTS.md §2.7: no autonomous skill creation → manual PR (skill-author not yet built)
  - Per FRAMEWORK.md §1: must have evals
  - HITL gate: scope-baseline.md requires client confirmation before build (per build.01-core)
- **Expected diff:** ~200-300 lines across SKILL.md, scripts/, evals/
- **Branch:** hermes/intent-collect
- **Priority:** MEDIUM (BG-004)
- **Related:** Enables deterministic front door; feeds trajectory-guard; seeds scope-ledger
- **Result:** ✓ SKILL.md created with pushy description; ✓ intent_collect.py implements structured elicitation; ✓ evals/test_intent_collect.py passes 7/7 tests; ✓ BG-004 marked done
- **Diff:** ~250 lines added across SKILL.md, scripts/, evals/
- **Next:** After BG-004, consider BG-005 (cross-cutting) or BG-012 (pr-review skill separate PR)

---

## Iteration 6 — 2026-07-04T00:00:00Z
**Action:** Cross-cutting skills batch (BG-005)
- **Source:** State Report — trajectory-guard, dashboard, model-route, scope-ledger, skill-author
- **Skills delivered:**
  - `trajectory-guard` (PR #13) — process-level drift control via expected vs actual trajectory diff
  - `dashboard` (PR #14) — management dashboard from telemetry data
  - `model-route` (PR #15) — model routing with local-vs-frontier graduation gates
  - `scope-ledger` (PR #16) — baseline vs extended scope tracking with cost attribution
  - `skill-author` (PR #18) — meta-skill for governed self-extension (SKILL.md + scripts/ + evals/ generation)
- **Result:** ✓ All 5 skills merged; ✓ all evals pass; ✓ BG-005 marked 5/5 done
- **Next:** Iteration 7 — PR Review Skill (BG-012)

---

## Iteration 7 — 2026-07-04T10:00:00Z
**Action:** PR Review Skill (BG-012) — automated first-pass PR reviews
- **Source:** User request — automated PR review to reduce human reviewer burden
- **Skill name:** `pr-review` (cross-cutting, runs on every PR targeting dev)
- **Spec reference:** FRAMEWORK.md §1 (skill contract), §2 (cross-cutting skills), AGENTS.md §2.3 (PR discipline), §11 (PR Review Process)
- **Plan:**
  1. **Draft SKILL.md** at `skills/pr-review/SKILL.md` with:
     - Description: "Automated PR reviewer: fetches PR diff, runs deterministic checks (lint, tests, schema, trajectory, branch model, commit style, security), performs semantic review against FRAMEWORK.md/AGENTS.md/HERMES-BRIEF.md, posts structured GitHub review with inline comments"
     - Inputs: PR_NUMBER, REPO, SPEC_FILES, HITL_GATE, CHECK_TRAJECTORY
     - Outputs: review_report.json (verdict, issues, deterministic_checks)
  2. **Implement scripts/**:
     - `fetch_pr.py` — gh API for PR metadata, diff, CI checks
     - `review.py` — deterministic checks + LLM semantic review (adversarial model)
     - `post_review.py` — submit GitHub review with inline comments
  3. **Add evals/**: test with fixture PR diffs, assert categorization accuracy ≥ 0.9
  4. **Run plan** in `runs/pr-review-plan.json` for orchestrator integration
- **Dependencies:** orchestrator (BG-003), trajectory-guard, gh CLI auth, skill-review.yml workflow
- **Constraints:**
  - Per AGENTS.md §2.7: no autonomous skill creation → manual PR
  - Per FRAMEWORK.md §1: must have evals
  - HITL gate: human reviews/approves PR after automated review
- **Result:** ✓ skills/pr-review/ created with SKILL.md, fetch_pr.py, review.py, post_review.py, test_pr_review.py; ✓ evals pass; ✓ PR #19 open for review
- **Next:** BG-006 _inbox/ & build-plan, BG-007 CI workflow, BG-009 eval audit

---

## Iteration 8 — 2026-07-04T16:00:00Z
**Action:** PM-GitHub Skill (BG-005 extended) — GitHub project management automation
- **Source:** User request — global PM sub-agent/skill for versioning, tags, releases, GitHub Projects, Issues across Faber and offshoot repos (Rohaki, k-dimensional, future)
- **Skill name:** `pm-github` (cross-cutting, framework-scoped)
- **Spec reference:** FRAMEWORK.md §1 (skill contract), §2 (cross-cutting skills), §12 (PM as a skill), AGENTS.md §2.11 (PM ops route through skills/pm-github/)
- **Plan:**
  1. **Draft SKILL.md** at `skills/pm-github/SKILL.md` with:
     - Description: "GitHub project management operations: versioning/releases, issue/PR triage, GitHub Projects v2, labels/milestones, proposal-based workflow with human approval gates"
     - Inputs: REPO, COMMAND (propose-issues, apply-proposals, bootstrap-project, version-bump, create-release), CONFIG_FILE
     - Outputs: proposal artifacts (JSON + Markdown), applied changes report
  2. **Implement modular scripts/**:
     - `cli.py` — Typer CLI with subcommands (propose-issues, apply-proposals, bootstrap-project, version-bump, create-release, classify, dedup)
     - `github_client.py` — gh API wrapper (issues, PRs, projects, labels, milestones, releases)
     - `classify.py` — deterministic severity/type rubric (no LLM): Critical/High/Medium/Low + bug/enhancement/docs/refactor/security/needs-triage
     - `dedup.py` — SHA256 dedup keys from source PR + comment ID for idempotency
     - `proposals.py` — ProposalBatch + ProposedIssue dataclasses, write/load/generate_markdown, index.jsonl
     - `bootstrap_project.py` — create GitHub Project v2 with fields (Status, Priority, Severity, Type, Target Release, Epic), views, automation rules
  3. **Config**: `config/defaults.yaml` + repo override `.github/pm-config.yaml`
  4. **GitHub Action**: `.github/workflows/pm-sync.yml` — propose-only on PR review comments (never auto-apply)
  5. **Framework wiring**:
     - AGENTS.md §2.11: PM ops route through skills/pm-github/
     - FRAMEWORK.md §2: added pm-github to Cross-cutting skills
     - FRAMEWORK.md §12: "Project management as a skill"
     - docs/pm-github.md: human HOW-TO
     - framework/lessons.md: scaffold extension pattern lesson
  6. **Add evals/**: 31 tests covering classify, dedup, dry-run enforcement, proposal shape, CLI integration
- **Dependencies:** skill-author (for dogfooding generation), gh CLI auth, jsonschema
- **Constraints:**
  - Per AGENTS.md §2.7: no autonomous skill creation → manual PR (generated via skill-author, reviewed by human)
  - Per FRAMEWORK.md §1: must have evals (31/31 passing)
  - HITL gate: `--apply` flag required for writes, default is dry-run proposal only
  - Proposal-only workflow: GitHub Action posts proposal artifacts as PR comments, human reviews + approves before apply
- **Result:** ✓ skills/pm-github/ created with 6 scripts, config, evals (31 tests), docs, framework wiring; ✓ all evals pass; ✓ PR #20 merged
- **Diff:** ~4,800 lines added across skill, workflows, docs, framework files
- **Next:** BG-006 _inbox/ & build-plan, BG-007 CI workflow, BG-009 eval audit, BG-004 remaining lifecycle skills (scaffold, evaluate, deploy, publish, observe, feedback)

---

---

## Iteration: BG-019 — Deploy targets & domain conventions (2026-07-19)

- **Spec ref**: User directive 2026-07-19: production domain faberframework.com, dev/staging on custom Cloudflare Pages branch alias. Encoded into FRAMEWORK.md as §13.
- **Plan**:
  1. Add FRAMEWORK.md §13 "Deploy targets & domain conventions" — production = canonical URL (project's own domain, e.g. faberframework.com), staging = Cloudflare Pages branch alias for `dev` (e.g. dev.<project>.pages.dev or custom dev subdomain).
  2. Add matching AGENTS.md §2.12 "Deploy target discipline" — every Faber-managed project declares both domains; `deploy` skill gates on `main`→prod, `dev`→staging.
  3. Add `framework/lessons.md` lesson: "Staging branch ≠ preview deploy — `dev` has its own deploy target, distinct from ephemeral PR previews."
- **Expected diff**: framework docs only — ~120 lines added across FRAMEWORK.md, AGENTS.md, framework/lessons.md. No skill code; no eval (docs-only iteration per §5 §2.5 plan-before-edit).
- **HITL**: PR to dev, human merge.



---
## Iteration 9 — 2026-07-20T06:43:50ZZ

**Action:** Add domain-suggest skill (BG-020)

- **Spec reference:** FRAMEWORK.md §13 "Deploy targets & domain conventions" rule 4: The `domain-suggest` skill is the sanctioned way to pick a production domain. Given a project brief, it probes RDAP/whois and returns 3 candidates with rationale (memorability, availability, TLD fit). Output is deterministic for the same brief; the human picks.

- **Plan:**
  1. **Run skill-author** to generate scaffold at `skills/domain-suggest/` with:
     - name: domain-suggest
     - description: "Given a project brief, probes RDAP/whois and returns 3 production domain candidates with rationale (memorability, availability, TLD fit). Output deterministic for same brief; human picks."
     - author: ndethi
     - license: MIT
     - tags: ["domain", "suggest", "whois", "rdap", "naming", "framework"]
  2. **Extend scaffold** (same branch, same PR):
     - Modular scripts: `cli.py` (Typer entrypoint), `generators.py` (RDAP/whois probing logic), `validators.py` (input validation, output sanity)
     - Config: `config/defaults.yaml` (RDAP endpoints, timeout, TLD preferences, scoring weights)
     - Assets: none initially
     - Framework wiring:
       - Update `AGENTS.md` §2.12 "Deploy target discipline" to reference `domain-suggest` skill for generating domain candidates
       - Ensure `FRAMEWORK.md` §13 is already present (from BG-019)
       - Add `docs/domain-suggest.md` human HOW-TO guide
       - Add lesson to `framework/lessons.md`: "Domain suggestions must be deterministic, verifiable, and actionable — never fabricate availability; show TODO: for unknown TLDs or ambiguous WHOIS responses."
  3. **Write evals suite**:
     - `test_generators.py` — test RDAP/whois parsing, caching, error handling
     - `test_validators.py` — test brief validation, candidate scoring, dedup
     - `test_dry_run_never_writes.py` — assert no network calls, no file writes when `--dry-run`
     - `test_proposal_shape.py` — assert output JSON schema matches expectation
     - Fixtures: sample briefs, mocked RDAP responses
  4. **Verify all evals pass**: `python -m pytest skills/domain-suggest/evals/ -v`
  5. **Update STATE.json**: iteration++, last_commit_sha, updated timestamp
  6. **Update backlog.md**: set BG-020 status to done
  7. **Update iteration-log.md**: result summary
  8. **Commit, push, create PR to dev**

- **Expected diff:** ~200-300 lines across SKILL.md, scripts/, config/, evals/, docs/, framework/

- **Branch:** hermes/domain-suggest-skill (already checked out)

- **PR target:** dev (referencing skill.domain-suggest@1.0.0 registry entry when created)

- **Constraint:** Per FRAMEWORK.md §1 and HERMES-BRIEF §1.8: no further skills until this one is eval-compliant.

- **HITL gate:** PR requires adversarial review (different model/agent), human review, and CI gates (evals, trajectory-guard conformance).

- **Next:** After BG-020 merge, BG-006 _inbox/ & build-plan, BG-007 CI workflow.

---

## Iteration 10 — 2026-07-26T08:30:00Z

**Action:** Design System Foundation — `faber-design-system` skill (BG-021)

- **Source:** Phase 2 feature request — "Design system foundation first (#2 partially — tokens + Tailwind + motion primitives). Without this, everything after it inherits the current 'pretty basic' baseline."
- **Skill name:** `faber-design-system` (framework-scoped, lifecycle-adjacent)
- **Spec reference:** FRAMEWORK.md §1 (skill contract), §2 (cross-cutting skills); fixtures/rohaki/design-tokens.* (Rohaki fixture created in previous session); skills/scaffold/scripts/scaffold.py (current generic defaults)
- **Plan:**
  1. **Create `skills/faber-design-system/{SKILL.md, scripts/, evals/, assets/}`** per FRAMEWORK skill contract
  2. **Draft SKILL.md** at `skills/faber-design-system/SKILL.md` with:
     - Description: "Generates project-specific design system assets (Tailwind config, CSS custom properties, component utility classes) from a Faber fixture's design tokens. Extends scaffold's generic defaults with fixture-specific theming (e.g., Rohaki's green gradients, card grids, stats sections)."
     - Inputs: FIXTURE_NAME (e.g., "rohaki"), OUTPUT_DIR, TEMPLATE_OVERRIDES
     - Outputs: tailwind.config.js, src/styles/design-tokens.css, src/components/ (utility classes), design-tokens.json (W3C format)
     - Interface: JSON in/out for orchestrator compatibility
  3. **Implement scripts/**:
     - `generate_tokens.py` — reads fixture design-tokens.json, emits CSS custom properties + Tailwind config + W3C JSON
     - `generate_components.py` — emits component utility classes (card, button, badge, grid, section, typography) as CSS + Tailwind @layer utilities
     - `design_system.py` — main entry point (Typer CLI): --fixture, --output-dir, --format (css|tailwind|json|all)
     - `apply_to_project.py` — copies generated assets to an Astro project, updates astro.config.mjs imports
  4. **Assets/templates/**:
     - `tailwind.config.template.js` — framework base + fixture extension pattern
     - `design-tokens.css.template` — CSS custom properties template
     - `components.css.template` — component utility classes template
  5. **Add evals/**:
     - `test_tokens.py` — given rohaki fixture, emits correct CSS vars + Tailwind config + JSON
     - `test_components.py` — asserts component utilities match fixture spec (card grids, stats grids, gradients)
     - `test_determinism.py` — same input → byte-for-byte identical output
     - `test_apply.py` — applies to temp Astro project, verifies imports resolve
  6. **Registry entry** in `prompts/_registry.md` (new skill entry)
  7. **PR** targeting `dev` referencing `skill.faber-design-system@1.0.0`
- **Dependencies:** Fixture exists at `fixtures/rohaki/design-tokens.json` (created in previous session)
- **Constraints:**
  - Per AGENTS.md §2.7: no autonomous skill creation → manual PR (skill-author not yet used for framework skills)
  - Per FRAMEWORK.md §1: must have evals
  - HITL gate: human reviews generated artifacts before merge
  - **Key distinction:** This skill does NOT replace scaffold defaults. It EXTENDS them. Projects opt-in via `--fixture rohaki`. Scaffold remains generic.
- **Expected diff:** ~400-500 lines across SKILL.md, scripts/, evals/, assets/
- **Branch:** hermes/faber-design-system (this branch)
- **Priority:** HIGH (BG-021)
- **Related:** Enables BG-022 (splash page), BG-024 (intent wizard), Rohaki MVP theming
- **Result:** ✓ SKILL.md created with pushy description; ✓ design_system.py implements generate/apply commands; ✓ tokens_to_tailwind extracts all color tokens including semantic + gradients; ✓ resolve_token_references handles embedded {path} in strings; ✓ generate_component_css emits card/button/badge/grid/section/typography utilities; ✓ 27 evals pass (test_tokens.py 17, test_apply.py 5, test_determinism.py 5); ✓ CLI generates CSS custom properties + Tailwind config + W3C JSON; ✓ apply command updates astro.config.mjs + global.css; ✓ Deterministic byte-for-byte output verified
- **Diff:** ~2,800 lines added across SKILL.md, scripts/design_system.py, evals/*.py, assets/templates/tailwind.config.j2
- **Next:** BG-022 Faber Launch Splash (faber-splash skill)
