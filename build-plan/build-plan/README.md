# Build Plan

An ordered series of **prompt artifacts** (frontmatter metadata + body) that a harness (Claude Code / Antigravity) executes to persist this framework to a git repo and build the skill library. Run them in order; each ends in a commit (and, where marked, a PR + HITL gate).

## Precondition: `_inbox/`
Place the already-generated canonical artifacts into `_inbox/` so the build **persists them as-is (no regeneration → no drift)**:

```
_inbox/
  FRAMEWORK.md
  INTERFACE.md
  prompts/_registry.md
  prompts/framework.bootstrap.md
  prompts/skill.intent-collector.md
  prompts/skill.observe-feedback.md
  prompts/meta.skill-author.md
  prompts/app.client-portal.md
  fixtures/rohaki/   (the distilled Rohaki context: company-profile.md,
                     esg-mrv-environmental.md, claims.md, website-spec.md,
                     design-system-brief.md, AGENTS.md)
```

## Two kinds of prompt artifact (don't confuse them)
- **Registry entries** (`prompts/*.md`) = durable **specs** — *what* to build, acceptance criteria, trajectory. Source of truth for each skill.
- **Build steps** (`build-plan/*.md`) = operational **persistence prompts** — *order*, files persisted, commits, HITL gates. They reference the registry entries rather than duplicating them (DRY).

## How to run
1. Open the repo in the harness; ensure `_inbox/` is populated.
2. Feed `build.00` first; let it complete its commit.
3. Proceed in order. Pause at every `hitl:` gate for human approval (PR review).
4. Skill steps build `skills/<name>/` **per its registry entry**, run the skill's eval, and open a PR referencing `<id>@<version>`.

## Order
| step | builds | HITL |
|---|---|---|
| `build.00-init-foundations` | repo skeleton + persist canonical docs from `_inbox/` | — |
| `build.01-core` | orchestrator + telemetry + `intent-collect` | scope baseline |
| `build.02-lifecycle-ci` | scaffold/build/evaluate/deploy/publish + CI | CI + deploy |
| `build.03-observe-feedback` | observe/feedback/trajectory-guard/dashboard | feedback→build |
| `build.04-meta-cost` | skill-author + model-route + scope-ledger | skill PRs + promotion |
| `build.05-client-portal` | thin Phase-1 client portal (view over git) | portal write-exposure |
| `build.06-rohaki-fixture` | Rohaki end-to-end scaling test | scope baseline |

**Sequencing decision:** the portal is built *before* Rohaki — harden the framework on its own surfaces first, then test it on a real client. When `build.06` reports site acceptance **and** trajectory conformance under `ordered`, the framework is proven to scale.
