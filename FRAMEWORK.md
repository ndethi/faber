# Agentic Web Framework — v0.2

**Skill library + process-level drift control + governed self-extension**

> Builds on **v0.1** (context pyramid · spec-as-single-source-of-truth · acceptance-criteria-as-CI-tests · the four pillars). v0.2 keeps all of that and turns the linear playbook into a **composable library of skills** with: a deterministic intent front-door, process-level (not just outcome-level) drift control, full-loop observability, a closed post-deploy feedback loop, and a meta-skill that lets the system extend itself under human review.
>
> This repo is the framework-as-product. The Rohaki website is its **test fixture**, not its subject (see §11).

---

## 1. Skills as the unit of work

Each lifecycle stage is packaged as an Agent Skill: a `SKILL.md` (YAML frontmatter: `name`, `description`; markdown body) plus optional `scripts/` (deterministic code), `references/` (load-on-demand docs), `assets/` (templates). Why this is the right abstraction here:

- **Model-swappable** — determinism lives in scripts; the model is the executor. Swapping Claude ↔ local ↔ frontier changes *who drives*, not *what is built*. This is the precondition for the cost layer (§8).
- **Composable** — an orchestrator sequences skills into a run.
- **Progressively disclosed** — only the triggered skill's body loads; resources load as needed.
- **Independently evaluable** — every skill ships an eval (hard rule).
- **Portable** — a skill is a folder; lift it into any project.

## 2. The lifecycle ring

```
        ┌──────────────────── feedback ←──────── observe ←──── publish
        ↓                                                        ↑
   intent-collect → scaffold → build → evaluate → deploy ───────┘
        ↑                                                
   (spec + trajectory)                              cross-cutting skills:
                                                    trajectory-guard · model-route
                                                    scope-ledger · dashboard
                                                    meta: skill-author
```
| Category | Skills |
|----------|--------|
| Lifecycle | `intent-collect` · `scaffold` · `build` · `evaluate` · `deploy` · `publish` · `observe` · `feedback` |
| Cross-cutting | `trajectory-guard` · `model-route` · `scope-ledger` · `dashboard` · `pm-github` |
| Meta | `skill-author` |

An **orchestrator** composes lifecycle skills per a run plan; cross-cutting skills wrap every run.

## 3. Intent collector — the deterministic front door

`intent-collect` runs structured elicitation and emits, deterministically (same inputs → same structure):

- **`spec.md`** — canonical, testable, with IDed acceptance criteria (the v0.1 SSOT).
- **`trajectory.md`** — the expected path (§4).
- **`scope-baseline.md`** — the agreed scope, **client-shareable**, and the seed of the scope ledger (§9).

It is the only sanctioned way to create or change intent. Output is a clean client-facing view plus the machine artifacts.

## 3.5 Intent Collection Interfaces — deterministic front door, multiple surfaces

The `intent-collect` skill MUST emit identical machine artifacts (`spec.md`, `trajectory.md`, `scope-baseline.md`) regardless of input surface. This is the determinism guarantee.

### Supported Input Surfaces

| Surface | Description | Determinism |
|---------|-------------|-------------|
| **CLI (structured prompts)** | Terminal-based elicitation via `intent_collect.py --interactive` | ✅ Same inputs → same outputs |
| **Web Form (static HTML)** | Client-facing questionnaire at `/intent` endpoint, posts JSON to orchestrator | ✅ Form schema versioned; same JSON → same artifacts |
| **API (JSON-RPC)** | `intent_collect` RPC method on orchestrator gateway; accepts structured JSON | ✅ Direct machine-to-machine; no LLM in path |
| **Telegram/Discord Bot** | Conversational elicitation via gateway; structured prompts with buttons | ✅ Gateway normalizes to JSON; same JSON → same artifacts |
| **Import (Markdown/YAML)** | `intent_collect.py --import spec.md` — upgrades legacy specs | ✅ Upgrade rules deterministic |

### Interface Contract

All surfaces normalize to a **canonical JSON input**:

```json
{
  "context": "Client conversation or project brief (free text)",
  "production_context": "prototype | normal | client-production",
  "constraints": ["brand-guidelines", "budget", "timeline"],
  "non_goals": ["mobile-app", "backend-api"],
  "stakeholders": [{"role": "marketing-lead", "name": "Jane"}],
  "artifacts": {
    "existing_spec": "path/to/spec.md",
    "existing_trajectory": "path/to/trajectory.md"
  }
}
```

`intent-collect` runs **purely deterministic logic** (no LLM) to emit:
- `spec.md` — with `SPEC-XX:` acceptance criteria IDs
- `trajectory.md` — with `strictness: exact|ordered|partial`
- `scope-baseline.md` — client-shareable, seeds `scope-ledger`

### Determinism Guarantee

```bash
# Same input JSON → identical three output files (byte-for-byte)
python skills/intent-collect/scripts/intent_collect.py --input input.json --output-dir out1
python skills/intent-collect/scripts/intent_collect.py --input input.json --output-dir out2
diff -r out1 out2  # must be empty
```

### Web Form Spec (assets/intent-form.html)

- Single-page, no framework, posts to `/api/intent/collect` (orchestrator gateway)
- Form fields map 1:1 to canonical JSON schema
- Versioned: `intent-form@v1.html` → `intent-form@v2.html` on schema change
- Client can bookmark and share; no auth required for read-only preview

### Telegram Bot Flow

```
/intent_new → structured prompts with inline keyboards
  → context (free text)
  → production_context (button: prototype/normal/client-production)
  → constraints (multi-select)
  → non_goals (multi-select)
  → stakeholders (repeatable)
  → confirm → posts to orchestrator → returns spec.md + trajectory.md + scope-baseline.md as files
```

### HITL Gate on Intent Change

Any change to `spec.md`/`trajectory.md`/`scope-baseline.md` after initial emit:
1. Creates a PR with diff (via `skill-author` or `pm-github`)
2. Requires human approval (HITL gate)
3. On merge, re-triggers downstream skills per `trajectory-guard` strictness

---

## 4. Trajectory determinant — process-level drift control

v0.1 tested *outcomes*. v0.2 adds a test of *process*.

- **Expected trajectory** = an ordered DAG of skill steps + checkpoints + gates, derived by `intent-collect` from the spec **and the production context**.
- **`trajectory-guard`** diffs the *actual* trajectory (from run telemetry, §5) against expected and emits a conformance report: match %, missing / extra / out-of-order steps, gate compliance.
- **Strictness dial (set per production context):**
  - `exact` — actual must equal expected (client production build).
  - `ordered` — expected steps in order; extras allowed (normal work).
  - `partial` — expected checkpoints hit; order free (prototype).
- **Deviation handling:** a violation either blocks (in `exact`) or flags. Critically, a deviation can also be a **candidate improvement** → routed to the feedback loop as a proposed `spec.md`/`trajectory.md` change (PR, HITL). Drift detection feeds self-improvement instead of only punishing.

Process-eval (`trajectory-guard`) + outcome-eval (acceptance criteria) together = the full drift defense.

## 5. Observability — *gap #1, closed*

**Per-run telemetry** (structured, machine-readable, and readable by the agent for self-correction): skills invoked, actual trajectory, tokens + cost, model used (local/frontier), eval scores, build/deploy status, post-deploy health.

**Management dashboard** (`dashboard` skill / internal builder tool) for the dev:
- Runs list + status; **expected-vs-actual trajectory diff** per run.
- Cost per run and per skill; model-routing decisions.
- Eval pass/fail; deploy health; **post-deploy RUM / Core Web Vitals**.
- **HITL queue** (pending skill-author PRs, pending spec changes).
- **Scope ledger** (§9): baseline vs extended scope, cost, IP attribution.

Principle (from v0.1, sharpened): *every consequence the agent should care about must be made visible — to the agent and to the dev.*

## 6. Post-deploy feedback loop — *gap #2, closed*

v0.1 stopped loosely at "measure". v0.2 defines the loop after publish:

```
observe (RUM/CWV · analytics · errors · uptime · link-monitor · client feedback)
   → triage   (classify: bug | regression | new-request | spec-gap)
   → propose  (PR: code fix | spec delta | new eval | new skill)
   → HITL     (dev approves)
   → build    (re-enter lifecycle)
   → verify   (acceptance + trajectory conformance)
```

- **Scheduled post-deploy audits:** conformance (live site vs `spec.md` §IA/§acceptance) + health.
- **Client feedback** is captured structurally → becomes **extended-scope** items in the scope ledger (§9), never lost in chat.

## 7. Meta-skill — governed self-extension (`skill-author`)

The system grows its own library, under human control.

- **Trigger:** a recurring pattern in `lessons.md`/feedback, or a capability gap surfaced by a run.
- **Procedure:** **search existing skills first (dedup)** → draft `SKILL.md` + `scripts/` + an **eval** (skill-creator conventions) → run the eval → **open a PR** with rationale + eval results.
- **Classification:** `client-scoped` (lives in the client repo) vs `framework-scoped` (proposed for the shared library).
- **Gates (HITL):** (1) dev reviews/approves the PR; (2) promoting `client-scoped → framework-scoped` is a **second** PR/gate.
- **Hard rules:** no skill without an eval; no skill without a dedup search. *Agent proposes, dev disposes.*

## 8. Model routing + local models — the cost layer

- Skill contracts are **model-agnostic**; the model does minimal reasoning around deterministic scripts.
- **`model-route`** picks local (cheap, routine) vs frontier (hard reasoning) per step.
- **Continuous comparison:** run local and frontier on a sample per skill, compare quality vs cost; update the routing policy. A step **graduates** frontier→local only when its eval clears threshold — this *persists the agent-led feature set* the local models can reliably own.
- **Target local runtime:** self-hosted open-weight models — OpenAI **gpt-oss** (e.g. 120B) or NVIDIA **Nemotron** — on local **NVIDIA DGX / DGX Spark**, served behind an **OpenAI-compatible endpoint** (e.g. vLLM or NVIDIA NIM). Both harnesses can point at it: Claude Code via `ANTHROPIC_BASE_URL` to a gateway; Antigravity via its open-weights / Model Garden option.
- All routing decisions + cost deltas surface in the dashboard.

## 9. Commercial layer — scope, cost, IP (`scope-ledger`)

- The intent spec is the **baseline scope** (client-shareable).
- Every new request → an **extended-scope** ledger item with: estimated agent cost (tokens / $ / model) and **dev IP attribution** (what the dev/agent authored).
- Surfaced in the dashboard for billing and IP tracking; ties directly to the feedback loop (client feedback → extended scope).

## 10. Tensions the design must resolve (not wish away)

| Tension | Resolution |
|---|---|
| Determinism vs agent autonomy | strictness dial per context + deviations-as-candidate-improvements (HITL) |
| Skill sprawl | dedup search + eval-required + PR gate + promotion gate |
| Local cost vs quality | continuous local-vs-frontier evals gate graduation |
| Self-extension vs control | every new skill enters only via human-approved PR |

## 11. Rohaki as test fixture

Use the already-distilled Rohaki context as the **scaling test**, not the goal: run `intent-collect` over it, generate `trajectory.md`, execute the lifecycle, and measure both **acceptance** and **trajectory conformance**. If the framework can drive Rohaki end-to-end under `ordered`/`exact` strictness, it scales. Keep Rohaki artifacts in a `fixtures/` dir, isolated from framework code.

## 12. Project management as a skill

`pm-github` is a cross-cutting Faber skill that owns all GitHub project-management operations. Unlike traditional project boards (Jira, Linear, GitHub Projects UI), pm-github encodes PM governance as **deterministic, versioned, auditable code**:

- **Portable**: the skill is a folder (`skills/pm-github/`) that lifts into any repo — no vendor lock-in.
- **PR-gated**: every write (issue, label, project field, release) is a *proposal* by default (`dry-run=True`). Real writes require explicit `--apply` or a gated workflow. This enforces "agents propose, humans dispose" (AGENTS.md §2.6).
- **No template staleness**: label taxonomy, field schemas, and view definitions live in `.github/pm-config.yaml` (per-repo) merging over `skills/pm-github/config/defaults.yaml` (skill-level). When the skill evolves, `sync-labels` and `bootstrap-project` bring repos current in one command.
- **Deterministic classification**: PR review comments → issues uses a keyword rubric (no LLM), so the same comment always yields the same (severity, type). Ambiguous comments fall back to `Medium`/`needs-triage` — never guessed.
- **Idempotent & auditable**: every operation carries a SHA256 dedup key (`source_repo:pr:comment_id`). Re-running never duplicates. All writes append to `runs/hermes/pm-log.jsonl` with timestamp, actor, and dry-run flag.
- **Roadmap as code**: milestones and roadmaps source from `docs/roadmap.md` (SSOT), not a proprietary board. The skill reads/writes this file, keeping human and machine views in sync.

This design makes PM operations **composable** (orchestrator can invoke `pm-github` alongside `build`, `evaluate`, etc.), **observable** (telemetry captures every proposal and application), and **self-documenting** (the skill *is* the process spec).
