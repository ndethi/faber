# Faber Gap-Closing Backlog

*Generated from state report 2026-06-28 and HERMES-BRIEF.md §7*

## High Priority

| ID | Source | Item | Priority | Status |
|----|--------|------|----------|--------|
| BG-001 | State Report + §7 | **AGENTS.md swap to canonical** — replace bootstrap constitution with canonical version, preserving human's Commitizen + PR-policy additions | HIGH | done (PR #7 merged) |
| BG-002 | State Report + §7 | **skills/build/ correction** — align SKILL.md to FRAMEWORK §8 (Astro + Cloudflare Pages default); add scripts/; add evals/ with passing test | HIGH | done (PR #8 merged) |
| BG-003 | State Report | **Orchestrator + telemetry** — orchestrator/ exists? runs/telemetry.schema.json has trajectory fields? | HIGH | done (PR #9 merged) |

## Medium Priority

| ID | Source | Item | Priority | Status |
|----|--------|------|----------|--------|
| BG-004 | State Report | **Missing lifecycle skills** — intent-collect, scaffold, evaluate, deploy, publish, observe, feedback need SKILL.md + scripts/ + evals/ | MEDIUM | **intent-collect done** (PR #11); others pending |
| BG-005 | State Report | **Cross-cutting skills** — trajectory-guard, dashboard, model-route, scope-ledger, skill-author need completion | MEDIUM | **5/5 done** (trajectory-guard #13, dashboard #14, model-route #15, scope-ledger #16, skill-author #18 merged) |
| BG-006 | State Report | **_inbox/ and build-plan/** — persisted from v0.2 bundle or amend build.00 acceptance | MEDIUM | open |
| BG-007 | State Report | **CI workflow** — per build-plan/build.02 once enough skills exist | MEDIUM | open |
| BG-008 | State Report | **Client portal** — per app.client-portal@0.1.0 once skills + CI stable | MEDIUM | open |
| BG-011 | User Request | **PR Review Resolution Skill** — fetch Copilot/GH review comments via gh API, systematically resolve each comment, push fixes, update PR | MEDIUM | **done** (PR #10 merged) |
| BG-012 | User Request | **PR Review Skill** — automated first-pass PR review against FRAMEWORK.md/AGENTS.md/HERMES-BRIEF.md, deterministic checks + LLM semantic review, posts GitHub review with inline comments | MEDIUM | **done** (PR #19 merged) |

## Low Priority / Tracking

| ID | Source | Item | Priority | Status |
|----|--------|------|----------|--------|
| BG-009 | FRAMEWORK §1 | **No skill without eval** — audit all existing skills for evals/ | LOW | open |
| BG-010 | HERMES-BRIEF §1.6 | **AGENTS.md vs FRAMEWORK.md alignment** — when they disagree on design, FRAMEWORK.md wins | LOW | open |

## Infrastructure / Process (Completed This Session)

| Item | Status |
|------|--------|
| **Review workflow: Copilot auto-request** | ✅ Enabled via GitHub UI (manual step) |
| **Review workflow: Adversarial review (NVIDIA Nemotron)** | ✅ Implemented in `.github/workflows/skill-review.yml` |
| **Review workflow: On-demand auto-fix (label `auto-resolve` or `/resolve-reviews`)** | ✅ Implemented in `.github/workflows/pr-review.yml` |
| **OpenRouter key for free models** | ⚠️ Added but account has no credits; using NVIDIA endpoint as fallback |
| **Test PR #17 merged** | ✅ Validated workflow pipeline |

## Notes

- Human prioritizes via Telegram/state report review
- One item per iteration (parallelism only via subagents for independent skills)
- Update status to "in_progress" when starting, "done" when PR merged
- New items added as discovered during iterations
- **Next up**: BG-006 _inbox/ & build-plan, BG-007 CI workflow, BG-009 eval audit