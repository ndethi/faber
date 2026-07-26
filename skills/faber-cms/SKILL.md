---
name: faber-cms
description: Generates a Cloudflare Worker-based CMS with D1 SQLite database for content management. Provides RESTful API (GET/POST) for content CRUD, Cloudflare Access authentication gate, and an embedded Astro admin UI. Content rendered from D1 instead of static files.
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - cms
  - cloudflare-workers
  - d1
  - sqlite
  - content-management
  - admin-ui
  - framework
---

# Faber CMS Skill

## Purpose

The `faber-cms` skill generates a complete Content Management System built on Cloudflare's edge platform:

- **Cloudflare Worker** (TypeScript) — RESTful API for content CRUD
- **D1 Database** (SQLite) — Persistent content storage with migrations
- **Cloudflare Access** — Zero-trust authentication gate for admin API
- **Embedded Astro Admin UI** — Content management interface using faber-design-system tokens

This is **Iteration A** of a two-iteration plan:
- **Iteration A** (this PR): Worker + D1 + REST API + CF Access gate
- **Iteration B** (next PR): Embedded Astro admin UI for content management

## When to Use

- Adding a CMS to a Faber-managed Astro site (e.g., Rohaki MVP blog/pages)
- Replacing static content files with database-driven content
- Needing authenticated content editing with audit trail
- Multi-environment content (staging/production) with D1

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_name` | string | Yes | Project name (e.g., `rohaki-cms`) |
| `output_dir` | string | Yes | Output directory for generated Worker project |
| `content_types` | array | Yes | Content type definitions (see schema below) |
| `deploy_targets` | object | Yes | Production + staging deploy config per FRAMEWORK.md §13 |
| `cf_access_policy` | object | No | Cloudflare Access configuration (default: email allowlist) |
| `fixture` | string | No | Design system fixture (default: `faber-brand`) |

### Content Type Schema

```json
{
  "name": "page",
  "displayName": "Page",
  "fields": [
    { "name": "slug", "type": "string", "required": true, "unique": true },
    { "name": "title", "type": "string", "required": true },
    { "name": "content", "type": "markdown", "required": true },
    { "name": "meta_description", "type": "string", "required": false },
    { "name": "published", "type": "boolean", "default": false },
    { "name": "published_at", "type": "datetime", "required": false }
  ]
}
```

## Outputs

### Iteration A (Worker + D1 + API)

| Path | Description |
|------|-------------|
| `<output_dir>/worker/src/index.ts` | Cloudflare Worker entry point with REST API |
| `<output_dir>/worker/src/db/schema.sql` | D1 schema with content, collections, versions tables |
| `<output_dir>/worker/src/db/migrations/0001_initial.sql` | Initial migration |
| `<output_dir>/worker/src/middleware/cf-access.ts` | Cloudflare Access middleware |
| `<output_dir>/worker/src/routes/content.ts` | Content CRUD routes (GET/POST/PUT/DELETE) |
| `<output_dir>/worker/src/routes/collections.ts` | Collection management routes |
| `<output_dir>/worker/wrangler.toml` | Worker config with D1 binding, KV, CF Access |
| `<output_dir>/worker/package.json` | Worker dependencies (hono, drizzle-orm, etc.) |
| `<output_dir>/worker/tsconfig.json` | TypeScript config |

### Iteration B (Admin UI - next PR)

| Path | Description |
|------|-------------|
| `<output_dir>/admin/src/pages/admin/*.astro` | Admin pages (Dashboard, ContentList, ContentEditor) |
| `<output_dir>/admin/src/components/admin/*.astro` | Reusable admin components |
| `<output_dir>/admin/src/styles/admin.css` | Admin-specific styles using design tokens |

## Interface (JSON)

```json
{
  "project_name": "rohaki-cms",
  "output_dir": "./rohaki-cms",
  "content_types": [
    {
      "name": "page",
      "displayName": "Page",
      "fields": [
        { "name": "slug", "type": "string", "required": true, "unique": true },
        { "name": "title", "type": "string", "required": true },
        { "name": "content", "type": "markdown", "required": true },
        { "name": "published", "type": "boolean", "default": false }
      ]
    },
    {
      "name": "post",
      "displayName": "Blog Post",
      "fields": [
        { "name": "slug", "type": "string", "required": true, "unique": true },
        { "name": "title", "type": "string", "required": true },
        { "name": "excerpt", "type": "string", "required": false },
        { "name": "content", "type": "markdown", "required": true },
        { "name": "tags", "type": "array", "items": { "type": "string" } },
        { "name": "published", "type": "boolean", "default": false }
      ]
    }
  ],
  "deploy_targets": {
    "production": { "domain": "cms.rohaki.example.com", "branch": "main" },
    "staging": { "domain": "dev-cms.rohaki.example.com", "branch": "dev" }
  },
  "cf_access_policy": {
    "emails": ["admin@example.com"],
    "groups": ["content-editors"]
  }
}
```

Returns:

```json
{
  "generated": [
    "rohaki-cms/worker/src/index.ts",
    "rohaki-cms/worker/src/db/schema.sql",
    "rohaki-cms/worker/wrangler.toml",
    "rohaki-cms/worker/package.json"
  ],
  "project_name": "rohaki-cms",
  "d1_database_name": "rohaki-cms-db",
  "staging_url": "https://dev-cms.rohaki.example.com",
  "production_url": "https://cms.rohaki.example.com"
}
```

## CLI Usage

```bash
# Iteration A: Generate Worker + D1 + API
python -m skills.faber-cms.scripts.generate_cms \
  --project-name rohaki-cms \
  --output-dir ./rohaki-cms \
  --content-types '{"name":"page","fields":[{"name":"slug","type":"string","required":true},{"name":"title","type":"string","required":true},{"name":"content","type":"markdown","required":true}]}' \
  --production-domain cms.rohaki.example.com \
  --staging-domain dev-cms.rohaki.example.com \
  --cf-access-emails admin@example.com

# With content types from file
python -m skills.faber-cms.scripts.generate_cms \
  --project-name rohaki-cms \
  --output-dir ./rohaki-cms \
  --content-types-file ./content-types.json \
  --production-domain cms.rohaki.example.com
```

## Determinism Guarantee

Same inputs → byte-for-byte identical output. No LLM in generation path.

## Acceptance Criteria (Iteration A)

1. Generates complete Cloudflare Worker project at `output_dir`
2. Worker has REST API: `GET/POST /api/content`, `GET/PUT/DELETE /api/content/:id`
3. D1 schema includes `content`, `collections`, `versions` tables with proper indexes
4. Cloudflare Access middleware validates requests before API handlers
5. `wrangler.toml` declares D1 binding, KV namespace for sessions, CF Access config
6. TypeScript compiles without errors (`npm run typecheck` passes)
7. Deploys to staging (`dev` branch) and production (`main` branch) per FRAMEWORK.md §13

## References

- `skills/faber-design-system/` — Design tokens for admin UI (Iteration B)
- `skills/faber-splash/` — Admin UI patterns, CF Access integration
- Cloudflare Workers + D1 docs: https://developers.cloudflare.com/d1/
- Cloudflare Access: https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/
- Hono framework: https://hono.dev/ (recommended for Worker routing)

## Two-Iteration Plan

| Iteration | Scope | PR | HITL |
|-----------|-------|-----|------|
| **A** | Worker + D1 + REST API + CF Access | This PR | Human reviews API + Worker |
| **B** | Embedded Astro Admin UI | Next PR | Human reviews admin UI |

**Rationale:** Splitting allows validating the Worker/API foundation before investing in the admin UI. The Worker is independently deployable and testable.