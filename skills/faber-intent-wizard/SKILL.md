---
name: faber-intent-wizard
description: |
  Generates a public `/intent` Astro route that collects project intent via a multi-step wizard,
  reuses intent-collect's structured elicitation logic to emit spec.md/trajectory.md/scope-baseline.md,
  stores submissions in D1 `intents` table, sends Telegram notifications, and generates backlog draft items.
  Deployed as part of the Faber splash site (faber-www) or standalone.
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - intent
  - wizard
  - astro
  - d1
  - telegram
  - framework
---

# Faber Intent Wizard Skill

## Purpose

The `faber-intent-wizard` skill generates a complete public intent collection wizard deployed as an Astro site with a Cloudflare Worker backend. It implements the deterministic front door of the Faber lifecycle for public use:

- **Multi-step `/intent` wizard** — Progressive disclosure form (goal → audience → non-goals → IA → content model → constraints → metrics)
- **Reuses `intent-collect` logic** — Extracts facts, elicits gaps, generates spec.md/trajectory.md/scope-baseline.md using the same deterministic functions
- **D1 persistence** — Stores submissions in `intents` table with full artifact history
- **Telegram notifications** — Sends formatted notification on each submission with scope-baseline preview
- **Backlog draft generation** — Creates GitHub issue-ready backlog items from submitted intent
- **Design system integration** — Uses `faber-design-system` tokens for consistent theming

This is the public-facing counterpart to the internal `intent-collect` skill, enabling anyone to submit project ideas that flow directly into the Faber pipeline.

## When to Use

- Adding a public "Start a Project" wizard to a Faber-managed site (e.g., faber-www splash page CTA)
- Collecting client project briefs with structured elicitation
- Building a project intake pipeline that feeds into Faber's lifecycle
- Integrating Telegram notifications for real-time project awareness

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_name` | string | Yes | Project name (e.g., `faber-intent-wizard`) |
| `output_dir` | string | Yes | Output directory for generated Astro project |
| `deploy_targets` | object | Yes | Production + staging deploy config per FRAMEWORK.md §13 |
| `telegram_bot_token` | string | No | Telegram bot token for notifications (reads from env if omitted) |
| `telegram_chat_id` | string | No | Telegram chat ID for notifications (reads from env if omitted) |
| `fixture` | string | No | Design system fixture (default: `faber-brand`) |
| `intent_collect_fixture` | string | No | Intent-collect fixture for pre-filled context (optional) |

### Deploy Targets Schema

```json
{
  "production": { "domain": "intent.faberframework.com", "branch": "main" },
  "staging": { "domain": "dev-intent.faberframework.com", "branch": "dev" }
}
```

## Outputs

| Path | Description |
|------|-------------|
| `<output_dir>/src/pages/intent.astro` | Multi-step wizard form with progressive disclosure |
| `<output_dir>/src/pages/intent/success.astro` | Confirmation page with scope-baseline preview |
| `<output_dir>/src/pages/api/intent.ts` | API endpoint: POST /api/intent (stores to D1, emits artifacts, notifies Telegram) |
| `<output_dir>/src/pages/api/telegram.ts` | Telegram webhook handler |
| `<output_dir>/src/db/schema.sql` | D1 schema with `intents` table + indexes |
| `<output_dir>/src/db/migrations/0001_initial.sql` | Initial migration |
| `<output_dir>/wrangler.toml` | Worker config with D1 binding, KV for sessions, Telegram env vars |
| `<output_dir>/package.json` | Project dependencies (astro, hono, drizzle-orm, zod, etc.) |
| `<output_dir>/astro.config.mjs` | Astro config with Cloudflare adapter |
| `<output_dir>/.github/workflows/deploy.yml` | CI/CD: lint-and-test → deploy-preview (PR) / deploy-staging (dev) / deploy-production (main) |
| `<output_dir>/src/components/wizard/*.astro` | Wizard step components (StepGoal, StepAudience, StepNonGoals, StepIA, StepContentModel, StepConstraints, StepMetrics, StepReview) |
| `<output_dir>/src/components/ui/*.astro` | Reusable UI components (Button, Input, Textarea, Select, ProgressStepper, Card) |

## Interface (JSON)

```json
{
  "project_name": "faber-intent-wizard",
  "output_dir": "./faber-intent-wizard",
  "deploy_targets": {
    "production": { "domain": "intent.faberframework.com", "branch": "main" },
    "staging": { "domain": "dev-intent.faberframework.com", "branch": "dev" }
  },
  "telegram_bot_token": "env:TELEGRAM_BOT_TOKEN",
  "telegram_chat_id": "env:TELEGRAM_CHAT_ID",
  "fixture": "faber-brand"
}
```

Returns:

```json
{
  "generated": [
    "faber-intent-wizard/src/pages/intent.astro",
    "faber-intent-wizard/src/pages/api/intent.ts",
    "faber-intent-wizard/src/db/schema.sql",
    "faber-intent-wizard/wrangler.toml",
    "faber-intent-wizard/package.json"
  ],
  "project_name": "faber-intent-wizard",
  "d1_database_name": "faber-intent-wizard-db",
  "staging_url": "https://dev-intent.faberframework.com",
  "production_url": "https://intent.faberframework.com"
}
```

## CLI Usage

```bash
# Generate complete intent wizard project
python -m skills.faber-intent-wizard.scripts.generate_wizard \
  --project-name faber-intent-wizard \
  --output-dir ./faber-intent-wizard \
  --production-domain intent.faberframework.com \
  --staging-domain dev-intent.faberframework.com \
  --fixture faber-brand \
  --telegram-bot-token "$TELEGRAM_BOT_TOKEN" \
  --telegram-chat-id "$TELEGRAM_CHAT_ID"

# With deploy targets from file
python -m skills.faber-intent-wizard.scripts.generate_wizard \
  --project-name faber-intent-wizard \
  --output-dir ./faber-intent-wizard \
  --deploy-targets-file ./deploy-targets.json \
  --fixture faber-brand
```

## Determinism Guarantee

Same inputs → byte-for-byte identical output. No LLM in generation path.

## Acceptance Criteria

1. Generates complete Astro project at `output_dir` with `/intent` route
2. Multi-step wizard form: 7 steps (goal, audience, non-goals, IA, content model, constraints, metrics) + review
3. Reuses `intent-collect` logic: `extract_facts`, `elicit_gaps`, `generate_spec`, `generate_trajectory`, `generate_scope_baseline` (imported, not reimplemented)
4. D1 schema includes `intents` table with all required columns + indexes
5. API endpoint POST `/api/intent` stores to D1, emits three artifacts, sends Telegram notification
6. Telegram webhook handler validates and processes incoming updates
7. Backlog draft generator produces GitHub issue-ready markdown from submitted intent
8. `wrangler.toml` declares D1 binding, KV namespace, Telegram env vars
9. CI/CD workflow: lint-and-test → deploy-preview (PR) / deploy-staging (dev) / deploy-production (main)
10. TypeScript compiles without errors (`npm run typecheck` passes)
11. Deploys to staging (`dev` branch) and production (`main` branch) per FRAMEWORK.md §13
12. Design system tokens applied via `faber-design-system` fixture

## References

- `skills/intent-collect/` — Spec-emission logic (extract_facts, elicit_gaps, generate_spec, generate_trajectory, generate_scope_baseline)
- `skills/faber-cms/` — D1 schema patterns, Cloudflare Worker structure, CF Access patterns
- `skills/faber-design-system/` — Design tokens for theming (green gradients, card grids, stats sections)
- `skills/faber-splash/` — Deploy target patterns, CI/CD workflow structure
- Cloudflare Workers + D1 docs: https://developers.cloudflare.com/d1/
- Cloudflare Pages + Astro: https://docs.astro.build/en/guides/deploy/cloudflare/
- Telegram Bot API: https://core.telegram.org/bots/api
- FRAMEWORK.md §13 — Intent Collection Interfaces design
- AGENTS.md §2.12 — Deploy target discipline

## Deploy Target Discipline (per FRAMEWORK.md §13)

This skill generates a project that declares both production and staging deploy targets:

- **`main` → production** canonical domain (e.g., `intent.faberframework.com`)
- **`dev` → staging** (e.g., `dev-intent.faberframework.com`)
- Ephemeral PR previews are review surfaces only (`continue-on-error: true`)
- Merging `dev → main` is a HITL gate: PR must reference staging URL, reviewer must visit before approving