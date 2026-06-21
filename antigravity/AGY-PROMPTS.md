# Antigravity CLI — Build Prompts for Faber

> Literal prompts to paste into the interactive `agy` TUI, one per build step. Run **`SETUP.md` first** — it walks you from zero to a ready state. These prompts don't assume anything; they ask the agent to *re-verify* its grounding at the start of each step.
>
> **Why interactive, not `agy -p`:** in headless `-p` mode `agy` auto-approves every tool call (including file writes) and has no non-interactive plan-mode guarantee. For a gated build, drive it in the TUI where `/grill-me`, `/diff`, and the Artifact Review Panel (Ctrl+R) are your controls. A headless variant for read-only CI checks is at the end.

## Pre-flight before any step (do this once per session)
1. `cd ~/projects/faber && agy` — launch in the workspace.
2. In the TUI: `/context` — confirm `AGENTS.md` is in the loaded context. If not, **stop** and fix per `SETUP.md` §6 before continuing.
3. `/config` — confirm permission mode is `request-review`.
4. `/usage` — note current quota; `/model` — pick the model for this step (see each step below).

## The per-step ritual (repeat for every step)
1. Paste the step prompt as-is. It starts with a **verify** instruction so the agent re-reads the rules and the step file before doing anything.
2. The prompt says **PLAN FIRST / `/grill-me`** — let the agent produce a plan before it edits.
3. Review the plan against that step's `Procedure` + `Done-check`. Correct it in the prompt box.
4. Approve. As it works, inspect changes with `/diff` and open artifacts with **Ctrl+R**; approve pending actions with **Ctrl+K**.
5. At the step's **HITL GATE**, stop. Review the PR yourself and **merge** to advance.
6. Multi-skill steps (02, 03, 04): do **one skill at a time** — its own `/diff`, commit, and PR.
7. Glance at `/usage` between steps; switch back to Gemini for routine work to save quota.

---

## 00 — Init & foundations  ·  model: Gemini 3 Pro/Flash
```text
Before anything: confirm you can read AGENTS.md in the workspace root and list the files under _inbox/. If either is missing, STOP and tell me — do not try to continue.

Follow the rules in AGENTS.md. Execute _inbox/build-plan/build.00-init-foundations.md exactly.
PLAN FIRST: show me the repo tree and the exact list of files you will persist from _inbox/, and do NOT edit anything until I approve.
Then: (the repo is already git-init'd with a rollback commit and AGENTS.md is the bootstrap version) — create the directory skeleton; persist the canonical files from _inbox/ UNCHANGED (copy, never regenerate) into their final locations (e.g. _inbox/FRAMEWORK.md → ./FRAMEWORK.md, _inbox/prompts/* → ./prompts/, _inbox/build-plan/* → ./build-plan/, _inbox/fixtures/rohaki/* → ./fixtures/rohaki/); checksum them against _inbox/ to confirm equality; **replace the bootstrap AGENTS.md with the canonical one** the step generates; write CLAUDE.md whose body is just "@AGENTS.md", and README.md per the step; commit with the step's message.
Done-check: `diff -r` between _inbox/ and the persisted paths is empty; the skeleton dirs exist; the canonical AGENTS.md replaced the bootstrap one; `/context` still shows AGENTS.md loaded after the swap. Report the checksums to me.
```

## 01 — Core: orchestrator + telemetry + intent-collect  ·  model: Gemini for the orchestrator, switch to Claude (`/model`) for intent-collect
```text
Before anything: confirm AGENTS.md is loaded (`/context` shows it) and that build.00 has been merged (./FRAMEWORK.md, ./prompts/, ./build-plan/, ./fixtures/rohaki/ all exist at the workspace root). If not, STOP.

Follow AGENTS.md. Execute build-plan/build.01-core.md. Run /grill-me first and show me a plan for: (a) runs/telemetry.schema.json, (b) the orchestrator that reads a run plan and writes runs/<id>/telemetry.json, (c) the intent-collect skill built per prompts/skill.intent-collector.md. Do not edit until I approve.
Build in that order. Keep skills/intent-collect/SKILL.md under 500 lines; put the question set + emission logic in scripts/; include the eval.
Validate: orchestrator runs a no-op plan and writes valid telemetry; the intent-collect eval against fixtures/rohaki emits spec.md + trajectory.md + scope-baseline.md, and re-running yields the same structure (determinism).
HITL GATE: stop and show me scope-baseline.md for confirmation before anything downstream. Then create a branch, commit, and open a PR referencing skill.intent-collector@1.0.0.
```

## 02 — Lifecycle skills + CI  ·  model: Gemini 3 Pro
```text
Before anything: confirm AGENTS.md is loaded and that skills/intent-collect/ exists from build.01. If not, STOP.

Follow AGENTS.md. Execute build-plan/build.02-lifecycle-ci.md. This builds several skills — do them ONE AT A TIME, each with its own /diff review, commit, and PR.
/grill-me for the whole step first, then proceed skill by skill: scaffold → build → evaluate → deploy → publish. Stack default Astro; host Cloudflare Pages (fallback GitHub Pages). The evaluate skill runs the spec acceptance suite: Lighthouse, a11y, link-check, meta, claim-substantiation, token-lint.
Then write .github/workflows/ci.yml: on PR → install → build → evaluate → trajectory-guard placeholder → preview deploy; on merge to main → production deploy, GATED.
HITL GATE: show me the CI workflow and the deploy targets/secrets plan, and STOP before enabling production deploy.
```

## 03 — Observe + feedback + trajectory-guard + dashboard  ·  model: Claude for trajectory-guard/feedback, Gemini for dashboard
```text
Before anything: confirm AGENTS.md is loaded and that the lifecycle skills + CI from build.02 exist (skills/{scaffold,build,evaluate,deploy,publish}/, .github/workflows/ci.yml). If not, STOP.

Follow AGENTS.md. Execute build-plan/build.03-observe-feedback.md per prompts/skill.observe-feedback.md. Build one at a time: observe → trajectory-guard → feedback → dashboard.
Replace the Build-02 trajectory-guard CI placeholder with the real check (diff actual trajectory vs trajectory.md; enforce strictness). The dashboard must emit a GENERATED STATIC HTML report from runs/*/telemetry.json — no server.
Prove with synthetic runs: inject an out-of-order step → trajectory-guard flags it with the correct delta; `exact` strictness blocks, `partial` only flags; inject a post-deploy error → feedback produces a TRIAGED PR PROPOSAL (never an auto-merge).
HITL GATE: any feedback-loop proposal stops for my approval before it re-enters build. Show me artifacts with Ctrl+R. Commit; PR references skill.observe-feedback@1.0.0.
```

## 04 — Meta + cost: skill-author + model-route + scope-ledger  ·  model: Claude for skill-author
```text
Before anything: confirm AGENTS.md is loaded and that skills/{observe,feedback,trajectory-guard,dashboard}/ exist from build.03. If not, STOP.

Follow AGENTS.md. Execute build-plan/build.04-meta-cost.md. Build skill-author, model-route, scope-ledger — one at a time.
skill-author (per prompts/meta.skill-author.md): validate trigger → DEDUP-SEARCH existing skills → draft SKILL.md + scripts + an eval → run the eval → classify client/framework → OPEN A PR. It must NEVER auto-merge; promotion client→framework is a SEPARATE PR. Prove: a duplicate trigger yields an improvement PR (no new skill); a novel trigger yields a PR with SKILL.md + passing eval; no path merges automatically.
model-route: route local vs frontier per step; graduate a step to local only when its eval clears threshold. Target local runtime = self-hosted gpt-oss / NVIDIA Nemotron on NVIDIA DGX / DGX Spark via an OpenAI-compatible endpoint (vLLM / NIM). Log routing + cost deltas to telemetry.
scope-ledger: seed from scope-baseline.md; append extended-scope items with agent-cost estimate + dev IP attribution.
HITL GATE: every skill-author PR and every promotion stops for my approval.
```

## 05 — Client portal (Phase 1, BEFORE Rohaki)  ·  model: Gemini, verify with `/browser`
```text
Before anything: confirm AGENTS.md is loaded and that skills/{skill-author,model-route,scope-ledger}/ exist from build.04. If not, STOP.

Follow AGENTS.md. Execute build-plan/build.05-client-portal.md per prompts/app.client-portal.md.
Build app/ as a THIN VIEW OVER GIT: render scope/runs/cost from git artifacts only (no separate DB of truth). Add auth (dev + client roles); approval clicks translate into commit/PR events; a run can be triggered as a CI/job-runner dispatch; secrets stay server-side only.
Use /browser to verify: log in, render scope/cost/status from telemetry, click an approval and confirm it produces the matching git event, trigger a run without touching a terminal. Bring back screenshots as artifacts.
HITL GATE: STOP before exposing any client-facing write action — I approve, then you enable. Commit; PR references app.client-portal@0.1.0.
Do not proceed to build.06 until the portal works end-to-end — proving the framework before Rohaki is the point of this ordering.
```

## 06 — Rohaki end-to-end scaling test  ·  model: Claude Opus for intent, Gemini for build, `/browser` for the site
> **Precondition (you do this before invoking the prompt):** populate `fixtures/rohaki/` with the client context — the distilled markdown from the *first* conversation (`company-profile.md`, `esg-mrv-environmental.md`, `claims.md`, `website-spec.md`, `design-system-brief.md`). If the original Rohaki repo also has an `AGENTS.md`, copy it in as `fixtures/rohaki/AGENTS.fixture.md` so it can't shadow the workspace one. Verify with `ls fixtures/rohaki/`.

```text
Before anything: confirm AGENTS.md is loaded, the client portal from build.05 is working (an approval click writes back as a git event, runs are dispatchable), and that fixtures/rohaki/ contains the client context files I supplied (incl. AGENTS.fixture.md if applicable — that's the future site's constitution, NOT this workspace's). If anything is missing, STOP and tell me what.

Follow AGENTS.md. Execute build-plan/build.06-rohaki-fixture.md. This exercises the WHOLE framework against fixtures/rohaki — Rohaki is the test, not the subject.
Run intent-collect over fixtures/rohaki → spec.md + trajectory.md + scope-baseline.md. HITL GATE: I confirm scope first.
Then run the lifecycle under `ordered` strictness: scaffold → build → evaluate → deploy(preview) → publish → observe. trajectory-guard compares actual vs expected; the portal/dashboard must show the run, cost, and status. Use /browser to verify the built Rohaki site and confirm the anti-greenwashing claim-check passes (every environmental claim has a record per context/esg-mrv-environmental.md).
Write fixtures/rohaki/runs/<id>/ with telemetry + acceptance results + the trajectory conformance report. If acceptance AND conformance pass under `ordered`, set the exercised registry entries to status: active. Commit.
```

---

## Headless variant (read-only CI checks only)
Use `agy -p` **only** for reporting steps that must not write (e.g. running `evaluate` or a `trajectory-guard` conformance report in CI). Because `-p` auto-approves writes, restrict the prompt to reporting, sandbox it, attach a pseudo-TTY so output isn't silently dropped on a non-TTY, and add a timeout:
```bash
script -qec 'agy -p "Run the evaluate skill against the current build and print PASS/FAIL per acceptance id. Do NOT modify any files." --sandbox --print-timeout 10m' /dev/null < /dev/null
```
Keep **all** write/commit/PR steps interactive with the human gates above. (Even `--sandbox` has had write-bypass reports — don't rely on it as your only guardrail.)

## Gotchas
- **`-p` auto-approves tools** (incl. `write_file`); no non-interactive plan mode yet → keep writes interactive.
- **Quota is shared and invisible to the agent** → watch `/usage`, run `/grill-me` before big steps, cap parallel subagents at 3–5.
- **No `--output-format json`** in the current `--help` → parse plain text; JSON is unstable.
- **Fast-moving tool** → run `agy --help` and `agy changelog` before relying on any flag.
- **Multi-skill steps (02, 03, 04)** span several turns → one skill per `/diff` + commit + PR; don't let it batch them blindly (that's how trajectory drift sneaks in).
