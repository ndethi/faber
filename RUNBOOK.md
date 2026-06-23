# Runbook — Building Faber with Claude Code / Antigravity

How to run the `build-plan/` prompt series in a harness, step by step. The mental model: **both tools are agent runtimes over the same git repo. `AGENTS.md` makes them behave the same; you (the dev) are the HITL gate; PRs are the approval queue.** Pick one harness to start — Claude Code is the cleaner fit for this git-/PR-driven build; reach for Antigravity when you want its browser-verification loop on the actual site UI later.

---

## 0. Prerequisites (both tools)

1. **Isolated, clean repo.** Create an empty repo (ideally in a container or VM, since agents get broad access). Make one commit so you always have a rollback point.
2. **Populate `_inbox/`** with the canonical artifacts (see `build-plan/README.md`): `FRAMEWORK.md`, `INTERFACE.md`, `IDENTITY.md`, `prompts/*.md`, and `fixtures/rohaki/*`.
3. **GitHub repo** connected — PRs are your HITL gates; Actions is your job runner; Pages/Cloudflare Pages is the host (token added at the deploy step, not before).
4. **Decide the constitution lives in `AGENTS.md`** (cross-tool standard). Claude Code reads `CLAUDE.md`, so make `CLAUDE.md` a one-line import: `@AGENTS.md`. Antigravity imports the same file as a workspace rule. One source of truth, both harnesses.

---

## Path A — Claude Code (recommended to start)

### A1. Install & open
```bash
npm install -g @anthropic-ai/claude-code
cd faber/            # your repo
claude               # start an interactive session in the repo
```

### A2. Set up the constitution
```text
/init                # generates a starter CLAUDE.md
```
Then replace CLAUDE.md's body with a single import so the constitution stays in AGENTS.md:
```text
@AGENTS.md
```
Set approval rules so the agent can't write unreviewed:
```text
/permissions         # require approval for writes; allow read/build freely
```

### A3. Turn each build step into a slash command (optional but clean)
The `build-plan/*.md` files are already prompt artifacts. Drop them in so you can invoke them by name:
```bash
mkdir -p .claude/commands
cp build-plan/build.0*.md .claude/commands/
```
Now `/build.00-init-foundations`, `/build.01-core`, … run each step's body as a command. (Alternatively, just paste a step's body into the prompt.)

### A4. Run the steps in order, planning first
For each step `00 → 06`:
1. **Plan mode first.** Press `Shift+Tab` until the status line shows *plan mode* (or start the session with `claude --permission-mode plan`). Use `--model opusplan` so Opus plans and Sonnet executes.
2. Invoke the step (`/build.00-init-foundations` or paste its body). Claude returns a **plan** — read it against the step's `Procedure` and `Done-check`.
3. Approve to execute. Claude writes files, runs checks, commits, and (for skill steps) opens a **PR** referencing the registry `id@version`.
4. **HITL gate:** review the PR diff yourself. Where the step's `hitl:` field is set, this is mandatory. Merge to advance.
5. Repeat for the next step. Respect `depends_on` — run sequentially, not in parallel; the order is the drift defense.

### A5. Reasoning-heavy vs routine
Use Opus (`--model opusplan`, effort `high`) for `intent-collect`, `trajectory-guard`, `skill-author`. Sonnet is fine for `observe`/`dashboard`/`portal`. Later, `model-route` automates this — and points routine steps at your local gpt-oss / Nemotron endpoint via `ANTHROPIC_BASE_URL` to a gateway.

### A6. Headless (for CI later)
`evaluate` and `trajectory-guard` run unattended in CI via print mode:
```bash
claude -p "run the evaluate skill against the current build" --output-format json --allowedTools "Bash,Read"
```

---

## Path B — Antigravity

### B1. Install & open
Download the preview from `antigravity.google`, install, sign in with a Google account. Open your `faber/` repo folder. Confirm `git status` is clean with a rollback commit.

### B2. Mode, terminal policy, model
- Choose **Agent-assisted** development mode (you stay in control; agent handles safe automations).
- Terminal Policy: start with *Agent Decides* (it asks before risky commands).
- Model: **Gemini 3 Pro** (free in preview) for scaffolding/routine steps; switch to **Claude** (add your Anthropic API key in settings) for reasoning-heavy steps — one-click switch mid-task. The hosted **GPT-OSS-120B** open-weights option is the same family you'll later self-host, so it's a useful rehearsal of the cost layer.
- Import `AGENTS.md` as a workspace rule so the constitution applies.

### B3. Run the steps in order via Manager view
For each step `00 → 06`:
1. Open **Manager view**. Write the goal in plain language, pointing at the file: e.g. *"Execute `build-plan/build.00-init-foundations.md` exactly; pause at any HITL gate."*
2. The agent produces a **Plan Artifact** (Task List + Implementation Plan). Review it against the step's `Procedure`/`Done-check`; leave comments on the artifact (Google-Docs style) — the agent reads them on the next run.
3. Dispatch. Review the **Artifacts** it returns (task list complete, walkthrough, any screenshots/browser recording) the way you'd review a junior engineer's PR.
4. Let it commit and open a **PR**; **you merge** (the HITL gate).
5. Advance to the next step. You *can* run agents in parallel, but keep build steps sequential to honour `depends_on`; use parallelism only for independent skills inside a step.

### B4. Watch for drift early
If the Task List starts wandering from the step's `Procedure`, correct it there — tighten the goal, split the dispatch, or switch that task to a stronger reasoning model (Claude Opus). This is the manual version of what `trajectory-guard` later enforces automatically.

---

## The HITL map (where you must approve)

| build step | gate |
|---|---|
| 00 init-foundations | — (verify canonical files match `_inbox/`) |
| 01 core | confirm `scope-baseline.md` before downstream |
| 02 lifecycle-ci | approve CI workflow + deploy targets/secrets before prod |
| 03 observe-feedback | any feedback proposal before it re-enters build |
| 04 meta-cost | every new-skill PR + every client→framework promotion |
| 05 client-portal | before exposing any client-facing write action |
| 06 rohaki-fixture | client confirms scope before the build runs |

Every gate is a PR review in both tools. "Approve" = merge.

---

## Suggested first session

```text
# Claude Code
cd faber/ && claude
/init                                  # then set CLAUDE.md to: @AGENTS.md
/permissions                           # require approval for writes
# Shift+Tab to plan mode, --model opusplan
/build.00-init-foundations             # review plan → approve → it commits
# review, then continue:
/build.01-core                         # → PR for skill.intent-collector@1.0.0 → you merge
```

Stop after `build.05` and confirm the portal works end-to-end (a non-technical user can log in, see scope/cost, approve a gate, trigger a run) **before** running `build.06` on Rohaki — that's the whole point of building the portal first.

> Tooling note: Antigravity and Claude Code are both public-preview-fast — model names, flags, and limits shift. Check each tool's own docs if a command here has moved.
