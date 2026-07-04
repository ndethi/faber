# AGENTS.md — Faber Framework Constitution (Canonical)

You are building the **Faber** agentic web framework into this repo. This constitution governs all work — human, agent, or hybrid.

---

## 1. Design Authority

- **FRAMEWORK.md** is the design source of truth (architecture, invariants, skill contracts).
- **AGENTS.md** is the process constitution (rules, gates, definitions of done).
- When they disagree on *design*, FRAMEWORK.md wins. Open a PR fixing AGENTS.md first; do not silently follow the weaker one.

---

## 2. Operating Rules

### 2.1 Git is the source of truth
No state lives outside the repo. All artifacts (specs, trajectories, telemetry, evals, skills, portal data) are committed files.

### 2.2 Branch model (per BRANCH-MODEL.md)
- `main` — production. **Never push here.** Promotion = human-merged `dev → main` PR.
- `dev` — integration. **Never commit directly.** All changes flow via PRs from `hermes/<topic>` branches.
- `hermes/<topic>` — your working branches. One logical change per branch, one PR per branch, base **always `dev`**.
- `hermes/brief` — holds `long-running/HERMES-BRIEF.md`; updated only via PR.

### 2.3 PR discipline
- Every PR targets `dev`. Human reviews and merges.
- PR title mirrors the commit subject; references the registry `id@version` when applicable.
- Use `gh pr create --base dev` (configured in this repo).

### 2.4 Commit style (Commitizen)
All significant commits follow Conventional Commits:
```
feat:   new capability
fix:    bug fix
chore:  maintenance, tooling, docs
refactor: code change without behavior change
test:   test additions or fixes
```
Enforced via pre-commit hook (`cz check`) and CI validation.

### 2.5 Plan before edit
For any non-trivial change: write a 3–5 line plan into `runs/hermes/iteration-log.md` *before* editing. State the spec reference (FRAMEWORK §X / skill name / SPEC-ID), expected diff size.

### 2.6 HITL gates (human-in-the-loop)
Specified per skill/build step in FRAMEWORK.md and registry entries. A gate means: **PR opened → human reviews → human merges**. No auto-merge past a gate.

### 2.7 No autonomous skill creation
Hermes's profile-level skill extraction is disabled. All skills authored via Faber's `skill-author` meta-skill (once it exists) or manual PR. Every skill requires an eval.

### 2.8 Executable acceptance > LLM judge
Lighthouse, axe, link-check, claim-substantiation, token-lint, trajectory-guard conformance — deterministic checks are the gate. The judge only evaluates what deterministic checks cannot.

### 2.9 No fabrication
Unknown facts, sources, or capabilities = `TODO:` in the artifact + Telegram surface. Never invent.

### 2.10 Respect `/stop`
On `/stop` (TUI or Telegram gateway): halt cleanly, post one-line status to Telegram, exit loop.

### 2.11 PM & GitHub operations route through `skills/pm-github/`
Do not open issues, create tags, edit project fields, or bulk-label via ad-hoc scripts. Every PM write is a proposal until human-approved. `.github/pm-config.yaml` overrides skill defaults per repo.

---

## 3. Skill Contract (per FRAMEWORK.md §1)

Every skill at `skills/<name>/` contains:
- `SKILL.md` — YAML frontmatter (`name`, `description`, `version`, `author`, `license`, `tags`) + markdown body
- `scripts/` — deterministic code (Python/Node) that does the actual work; model only orchestrates
- `evals/` — **hard requirement**: automated test proving the skill meets its acceptance criteria
- `references/` — load-on-demand docs (optional)
- `assets/` — templates (optional)

**No skill ships without a passing eval.** (FRAMEWORK.md §1, hard rule)

---

## 4. Lifecycle & Cross-Cutting Skills (FRAMEWORK.md §2)

| Category | Skills |
|----------|--------|
| Lifecycle | `intent-collect`, `scaffold`, `build`, `evaluate`, `deploy`, `publish`, `observe`, `feedback` |
| Cross-cutting | `trajectory-guard`, `model-route`, `scope-ledger`, `dashboard` |
| Meta | `skill-author` |

An **orchestrator** (`orchestrator/`) sequences lifecycle skills per a run plan; cross-cutting skills wrap every run.

---

## 5. Definitions of Done

### Skill-level
- `SKILL.md` + `scripts/` + `evals/` present
- Eval passes (`python -m pytest skills/<name>/evals/`)
- Registry entry in `_registry.md` with `status: active`

### Build-step level (per build-plan)
- All skills in step complete per above
- Acceptance criteria in build-plan satisfied
- HITL gate cleared (human merged PR)

### Phase A* Equilibrium (per HERMES-BRIEF.md §2)
All 9 conditions hold simultaneously — see brief for full list.

---

## 6. Telemetry & Observability

- **Telemetry schema**: `runs/telemetry.schema.json` — run id, ordered skills invoked (actual trajectory), tokens+cost, model used, eval scores, deploy status, timestamps.
- **Trajectory conformance**: `trajectory-guard` diffs expected (`trajectory.md`) vs actual (telemetry); emits report with `exact`/`ordered`/`partial` strictness.
- **Dashboard**: `dashboard` skill generates `dashboard/index.html` from telemetry; CI uploads as artifact.

---

## 7. Post-Deploy Feedback Loop (FRAMEWORK.md §6)

```
observe (RUM/CWV · analytics · errors · uptime · link-monitor · client feedback)
  → triage   (classify: bug | regression | new-request | spec-gap)
  → propose  (PR: code fix | spec delta | new eval | new skill)
  → HITL     (dev approves)
  → build    (re-enter lifecycle)
  → verify   (acceptance + trajectory conformance)
```

Client feedback → extended-scope ledger items (never lost in chat).

---

## 8. Self-Extension (FRAMEWORK.md §7)

`skill-author` meta-skill governs new skills:
1. Trigger: recurring pattern in `lessons.md`/feedback or capability gap
2. Dedup search → draft `SKILL.md` + `scripts/` + **eval**
3. Run eval → open PR with rationale + results
4. HITL gate (dev reviews)
5. Promotion `client-scoped → framework-scoped` = second PR/gate

**Hard rules:** no skill without eval; no skill without dedup search. Agent proposes, dev disposes.

---

## 9. Cost & Commercial Layer (FRAMEWORK.md §8–9)

- `model-route` picks local vs frontier per step; continuous local-vs-frontier evals gate graduation.
- `scope-ledger`: baseline scope (from intent) + extended-scope items with estimated agent cost + dev IP attribution.
- Dashboard surfaces cost per run/skill, routing decisions, scope ledger.

---

## 10. Reference Files (read at session start)

```
@AGENTS.md
@README.md
@FRAMEWORK.md
@long-running/HERMES-BRIEF.md
@long-running/BRANCH-MODEL.md
@runs/hermes/STATE.json
@runs/hermes/backlog.md
```

---

## 11. PR Review Process (MANDATORY)

### 11.1 Review Requirements
**NO PR MERGES WITHOUT REVIEW.** Every PR must pass through:

1. **Adversarial Review** — A different model/agent than the author reviews the code
   - Use `pr-review-resolution` skill with `--adversarial` flag
   - Or Copilot/GitHub reviewer (different from writing model)
   
2. **Human Review** — Dev reviews and explicitly approves
   - HITL gate per §2.6
   - Dev merges manually (no auto-merge)

3. **CI Gates** — All automated checks pass
   - Evals pass (`python -m pytest skills/<name>/evals/`)
   - Trajectory-guard conformance
   - Lint/type checks

### 11.2 Review Workflow
```bash
# On PR open → auto-triggered by .github/workflows/skill-review.yml
# 1. Adversarial review posts comments
# 2. Author fixes comments (or defers with rationale)
# 3. Re-review until clean
# 4. Human review + merge
```

### 11.3 Adversarial Review Rules
- **Different model** than writer (e.g., writer=nemotron, reviewer=claude/opus/gpt-4)
- **Critique mode** — look for: logic errors, security issues, spec violations, missing edge cases, fabrication
- **No rubber-stamp** — must find at least 1 issue or explicitly approve with reasoning
- **Categories**: `bug`, `security`, `design`, `spec-violation`, `missing-test`, `fabrication`, `nit`

### 11.4 Merge Checklist (Dev must verify)
- [ ] Adversarial review completed (comments addressed or deferred with rationale)
- [ ] Human review completed (you read the diff)
- [ ] All evals pass locally
- [ ] Trajectory-guard passes
- [ ] CI green
- [ ] You manually click "Merge" (no auto-merge)

---

*Canonical version.Git is the source of truth (per §2.1). All process changes go through PRs.*