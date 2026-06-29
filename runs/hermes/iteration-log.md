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