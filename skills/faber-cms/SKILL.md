---
name: faber-cms
description: |
  Cloudflare Worker-based CMS with D1 database, Hono + Drizzle + Zod, and Cloudflare Access authentication.
  Includes admin dashboard (Astro) with content editor, media library, and settings.
version: 1.1.0
author: ndethi
license: MIT
tags: [cms, cloudflare, worker, d1, hono, drizzle, zod, admin, cf-access]
---

# Faber CMS Skill

## Overview

Generates and deploys a complete CMS backend (Cloudflare Worker) with:
- **D1 SQLite database** — schema + migrations per content type
- **Worker TypeScript** — Hono + Drizzle + Zod
- **Cloudflare Access** — JWT validation via CF Access JWKS
- **REST API** — content CRUD, collections management, media upload, health check
- **Admin Dashboard** — Astro static app with content editor, media library, settings
- **Config** — wrangler.toml (D1 + R2 + KV + CF Access), package.json, tsconfig.json
- **CI/CD** — lint-and-test → deploy-preview (PR) / deploy-staging (dev) / deploy-production (main)

## Architecture

### Worker Structure (`scripts/worker/`)

```
worker/
├── src/
│   ├── index.ts              # Main Hono app
│   ├── types.ts              # Env + Zod schemas
│   ├── middleware/
│   │   └── cf-access.ts      # CF Access JWT middleware
│   ├── routes/
│   │   ├── content.ts        # Content CRUD
│   │   ├── collections.ts    # Collections management
│   │   ├── media.ts          # R2 presigned upload + metadata
│   │   ├── settings.ts       # Site config, webhooks, API keys
│   │   └── health.ts         # Health check
│   └── db/
│       ├── schema.ts         # Drizzle schema
│       ├── migrations/       # SQL migrations
│       └── index.ts          # Drizzle client + D1 binding
├── package.json
├── tsconfig.json
├── wrangler.toml
└── .github/workflows/deploy.yml
```

### Database Schema (D1 via Drizzle)

| Table | Purpose |
|-------|---------|
| `content` | Polymorphic content entries across collections |
| `collections` | Collection registry with Zod schemas |
| `media` | R2-backed media assets |
| `users` | Synced from CF Access (admin/editor/viewer) |
| `audit_log` | Append-only audit trail |

### CF Access Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full CRUD, settings, user management, webhooks |
| `editor` | Content CRUD, media upload, preview |
| `viewer` | Read-only, preview |

## Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-1 | Worker compiles and typechecks | `npm run typecheck` passes |
| AC-2 | All unit tests pass | `npm test` (23 tests) |
| AC-3 | D1 schema generates correctly | `drizzle-kit generate` produces valid SQL |
| AC-4 | CF Access middleware validates JWT | Unit test with mock JWKS |
| AC-5 | Content CRUD works end-to-end | Integration test with Miniflare |
| AC-6 | Media upload generates presigned R2 URL | Unit test |
| AC-7 | Admin UI builds without errors | `npm run build` in admin/ |
| AC-8 | Deterministic generation | Byte-for-byte identical output on repeated runs |

## Usage

```bash
# Generate worker project
python scripts/generate_worker.py --output-dir ./worker --config config/defaults.yaml

# Generate admin UI
python scripts/generate_admin.py --output-dir ./admin --config config/defaults.yaml

# Deploy worker
cd worker && wrangler deploy --env production

# Deploy admin UI to Cloudflare Pages
cd admin && npm run build && wrangler pages deploy ./dist --project-name=fabre-cms-admin
```

## Configuration

`config/defaults.yaml` contains:
- Content type definitions (page, post, solution, impact_metric)
- Collection schemas (Zod)
- UI config (field widgets, validation, preview)
- CF Access settings
- D1/R2/KV bindings

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| hono | ^4.0.0 | Web framework |
| drizzle-orm | ^0.30.0 | ORM for D1 |
| zod | ^3.22.0 | Validation |
| @cloudflare/kv-asset-handler | ^0.3.0 | Static assets |
| @hono/zod-validator | ^0.2.0 | Zod + Hono integration |
| @cloudflare/workers-types | ^4.2024000.0 | TypeScript types |
| drizzle-kit | ^0.20.0 | Migration generation |
| vitest | ^1.4.0 | Testing |
| wrangler | ^3.30.0 | Cloudflare CLI |
| typescript | ^5.4.0 | TypeScript |
| eslint | ^8.56.0 | Linting |
| @typescript-eslint/* | ^7.0.0 | TS linting |

## Deploy Targets

| Branch | Target | URL Form |
|--------|--------|----------|
| `main` | Production | Custom domain (e.g., `cms.example.com`) |
| `dev` | Staging | `dev-cms.example.com` |
| `hermes/*` | Preview | `preview/<branch>.cms.example.com` |

## Related Skills

- `deploy` — Deploys worker to Cloudflare
- `publish` — Creates release, tags, version bump
- `observe` — Collects RUM/CWV post-deploy
- `feedback` — Client feedback → triage loop

## References

- `references/2026-07-26-faber-cms-worker-pattern.md` — Iteration A (Worker + D1 + Hono)
- `references/2026-08-02-faber-cms-admin-ui-pattern.md` — Iteration B (Admin UI + 5 new evals)