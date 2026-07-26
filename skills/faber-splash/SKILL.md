---
name: faber-splash
description: Generates the Faber framework launch splash page (faber-www) — a static Astro site built with the faber-design-system skill, deployed by Faber CI/CD. Proves the framework ships itself: (a) what Faber is, (b) what shipped (rohaki-mvp + splash), (c) the loop — live PR/deploy timeline. CTA → Intent Wizard (/intent).
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - splash-page
  - marketing
  - astro
  - cloudflare-pages
  - framework
  - self-hosting
---

# Faber Splash Skill

## Purpose

The `faber-splash` skill generates the Faber framework's launch splash page — a marketing landing page at `faberframework.com` that demonstrates the framework can ship itself. This is the "anti-marketing" move: don't write the splash, let Faber write the splash. Show, then tell.

## When to Use

- Creating the Faber framework's public marketing site (`faber-www` repo)
- Demonstrating framework self-hosting capability
- Building a project that needs to showcase: what it is, what it shipped, the loop (PR→CI→Deploy)

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_name` | string | Yes | Project name (e.g., `faber-www`) |
| `output_dir` | string | Yes | Output directory for generated Astro project |
| `fixture` | string | No | Design system fixture (default: `faber-brand` — green gradients, card grids, stats) |
| `deploy_targets` | object | Yes | Production + staging deploy config per FRAMEWORK.md §13 |
| `intent_wizard_url` | string | No | URL for Intent Wizard CTA (default: `/intent`) |
| `rohaki_url` | string | No | Live Rohaki MVP URL for "what shipped" section |
| `github_repo` | string | No | GitHub repo for fetch deploy receipts (default: `ndethi/faber`) |

## Outputs

| Path | Description |
|------|-------------|
| `<output_dir>/package.json` | Astro + Cloudflare Pages deps |
| `<output_dir>/astro.config.mjs` | Astro config with Cloudflare adapter, design system import |
| `<output_dir>/wrangler.toml` | Cloudflare Pages config with production/staging targets |
| `<output_dir>/src/pages/index.astro` | Splash page with three scrolls + CTA |
| `<output_dir>/src/components/LoopDiagram.astro` | Live PR→CI→Deploy timeline |
| `<output_dir>/src/components/DeployReceipts.astro` | Deploy log panel with receipts |
| `<output_dir>/src/styles/design-tokens.css` | Design tokens from faber-design-system |
| `<output_dir>/.github/workflows/deploy.yml` | CI/CD: dev→staging, main→production |

## Interface (JSON)

```json
{
  "project_name": "faber-www",
  "output_dir": "./faber-www",
  "fixture": "faber-brand",
  "deploy_targets": {
    "production": { "domain": "faberframework.com", "branch": "main" },
    "staging": { "domain": "dev.faberframework.com", "branch": "dev" }
  },
  "intent_wizard_url": "/intent",
  "rohaki_url": "https://build-a-website-2ts.pages.dev",
  "github_repo": "ndethi/faber"
}
```

Returns:

```json
{
  "generated": [
    "faber-www/package.json",
    "faber-www/astro.config.mjs",
    "faber-www/wrangler.toml",
    "faber-www/src/pages/index.astro",
    "faber-www/src/components/LoopDiagram.astro",
    "faber-www/src/components/DeployReceipts.astro",
    "faber-www/.github/workflows/deploy.yml"
  ],
  "project_name": "faber-www",
  "fixture": "faber-brand",
  "staging_url": "https://dev.faberframework.com",
  "production_url": "https://faberframework.com"
}
```

## CLI Usage

```bash
# Generate splash page project
python -m skills.faber-splash.generate_splash \
  --project-name faber-www \
  --output-dir ./faber-www \
  --fixture faber-brand \
  --production-domain faberframework.com \
  --staging-domain dev.faberframework.com \
  --intent-wizard-url /intent \
  --rohaki-url https://build-a-website-2ts.pages.dev \
  --github-repo ndethi/faber
```

## Determinism Guarantee

Same inputs → byte-for-byte identical output. No LLM in generation path.

## Acceptance Criteria

1. Generates complete, runnable Astro project at `output_dir`
2. Splash page has three scroll sections:
   - **Scroll 1 (Hero):** What Faber is — phase-gated agent framework for shipping software
   - **Scroll 2 (Stats/Grid):** What shipped — Rohaki MVP (live link) + Splash itself
   - **Scroll 3 (Loop):** The loop — live PR→CI→Deploy timeline with real receipts
3. CTA button routes to Intent Wizard (`/intent` or provided URL)
4. Uses `faber-design-system` tokens (green gradients, card grids, stats sections, spring motion)
5. Deploys to production (`main` → faberframework.com) and staging (`dev` → dev.faberframework.com) per FRAMEWORK.md §13
6. CI/CD workflow passes lint, typecheck, build; deploys on push to `dev`/`main`
7. LoopDiagram component fetches live GitHub PR/commit data (or shows cached fallback)
8. DeployReceipts component shows Cloudflare Pages deploy logs/links as receipts

## References

- `skills/faber-design-system/` — design tokens, Tailwind config, component utilities
- `fixtures/rohaki/` — Rohaki brand tokens (bamboo/sage/earth palettes)
- `build-plan/build-plan/build.06-rohaki-fixture.md` — Rohaki as first customer
- FRAMEWORK.md §13 — Deploy targets & domain conventions
- FRAMEWORK.md §2 — Lifecycle & cross-cutting skills