---
kind: build-step
id: build.04-meta-cost
order: 4
title: Self-extension (skill-author) + model routing + scope ledger
harness: claude-code | antigravity
model: { recommended: claude-opus-4-x, swappable: true }
depends_on: [build.03-observe-feedback]
persists:
  - skills/skill-author/{SKILL.md,scripts/,evals/}
  - skills/model-route/{SKILL.md,scripts/,evals/}
  - skills/scope-ledger/{SKILL.md,scripts/,evals/}
commit: "feat: skill-author (PR/HITL) + model-route + scope-ledger"
hitl: "every new skill PR + every client→framework promotion requires dev approval"
acceptance:
  - duplicate trigger → improvement PR (no new skill); novel trigger → PR with SKILL.md + eval; nothing auto-merges
  - model-route graduates a step frontier→local only when its eval clears threshold
  - scope-ledger records extended-scope items with cost + IP attribution
---

# Build 04 — Meta + Cost

## Role
You add governed self-extension and the cost/commercial layer.

## Procedure
1. **`skill-author`** per `prompts/meta.skill-author.md`: validate trigger → **dedup search** → draft `SKILL.md`+`scripts/`+eval → run eval → classify (client/framework) → **open PR [HITL]**; promotion client→framework is a **second PR [HITL]**. Hard rules: no skill without an eval; search before create; nothing auto-merges.
2. **`model-route`**: route local vs frontier per step; run continuous local-vs-frontier comparison on samples; **graduate** a step to local only when its eval clears threshold; log decisions + cost deltas to telemetry/dashboard. **Target local runtime:** self-hosted **gpt-oss** / NVIDIA **Nemotron** on **NVIDIA DGX / DGX Spark**, served via an OpenAI-compatible endpoint (vLLM / NIM).
3. **`scope-ledger`**: seed from `scope-baseline.md`; append extended-scope items (new client requests) with estimated agent cost (tokens/$/model) + dev IP attribution; surface in dashboard.
4. Prove all ACs (including that no path auto-merges). Commit; PRs reference the respective registry ids.

## Done-check
The system can propose skills it cannot merge alone; cheap steps migrate to local under eval control; scope/cost/IP are recorded per client.
