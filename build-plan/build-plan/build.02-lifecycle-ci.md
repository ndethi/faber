---
kind: build-step
id: build.02-lifecycle-ci
order: 2
title: Lifecycle skills + CI pipeline
harness: claude-code | antigravity
model: { recommended: claude-opus-4-x, swappable: true }
depends_on: [build.01-core]
persists:
  - skills/{scaffold,build,evaluate,deploy,publish}/{SKILL.md,scripts/,evals/}
  - .github/workflows/ci.yml
commit: "feat: lifecycle skills + gated CI"
hitl: "approve CI workflow + deploy targets before enabling production deploy"
acceptance:
  - each lifecycle skill has a valid SKILL.md + passing eval
  - CI runs build → acceptance checks → trajectory-guard hook → preview; prod deploy gated
---

# Build 02 — Lifecycle + CI

## Role
Pipeline builder. You implement scaffold→publish and wire CI so acceptance + trajectory are enforced.

## Procedure
1. **Build skills** `scaffold`, `build`, `evaluate`, `deploy`, `publish`. Stack default Astro; host default Cloudflare Pages (fallback GitHub Pages). Each: deterministic logic in `scripts/`, pushy `description`, an eval.
   - `evaluate` runs the spec's acceptance criteria (Lighthouse, a11y, link-check, meta, claim-substantiation, token-lint) as the test suite.
2. **CI** (`.github/workflows/ci.yml`): on PR → install → `build` → `evaluate` (acceptance) → `trajectory-guard` hook (placeholder until Build 03) → preview deploy. On merge to `main` → production deploy, **gated**.
3. **[HITL]** Present CI workflow + deploy targets/secrets for approval before enabling prod.
4. Commit; open PRs referencing the relevant registry ids (lifecycle skills are specified by `framework.bootstrap@1.0.0` §2 until they earn their own entries).

## Done-check
PR pipeline builds + runs acceptance on the Rohaki fixture; prod deploy requires human approval.
