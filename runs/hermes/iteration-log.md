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