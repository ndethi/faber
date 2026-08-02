---
name: faber-cms
description: Generates a Cloudflare Worker-based CMS with D1 SQLite database for content management. Provides RESTful API (GET/POST/PUT/DELETE) for content CRUD, Cloudflare Access authentication gate, and an embedded Astro admin UI. Content rendered from D1 instead of static files.
version: 1.1.0
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

**Both iterations complete:**
- **Iteration A** (PR #70): Worker + D1 + REST API + CF Access gate
- **Iteration B** (this PR): Embedded Astro admin UI for content management

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

### Iteration B (Admin UI - Complete)

| Path | Description |
|------|-------------|
| `<output_dir>/admin/src/pages/admin/*.astro` | Admin pages (Dashboard, ContentList, ContentEditor, Settings) |
| `<output_dir>/admin/src/components/admin/*.astro` | Reusable admin components (Sidebar, Header, ContentTable, ContentForm, Modal, Toast) |
| `<output_dir>/admin/src/lib/api-client.ts` | TypeScript client for Worker API |
| `<output_dir>/admin/src/lib/types.ts` | TypeScript types for API responses |
| `<output_dir>/admin/src/styles/admin.css` | Admin-specific styles using design tokens |
| `<output_dir>/admin/astro.config.mjs` | Astro configuration |
| `<output_dir>/admin/package.json` | Admin UI dependencies and scripts |
| `<output_dir>/admin/wrangler.toml` | Cloudflare Pages configuration |
| `<output_dir>/admin/tsconfig.json` | TypeScript config |
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
        { "name": "meta_description", "type": "string", "required": false },
        { "name": "published", "type": "boolean", "default": false },
        { "name": "published_at", "type": "datetime", "required": false }
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
    "rohaki-cms/worker/package.json",
    "rohaki-cms-admin/admin/src/pages/admin/index.astro",
    "rohaki-cms-admin/admin/src/pages/admin/content.astro",
    "rohaki-cms-admin/admin/src/pages/admin/content/[collection].astro",
    "rohaki-cms-admin/admin/src/pages/admin/content/[collection]/[id].astro",
    "rohaki-cms-admin/admin/src/pages/admin/settings.astro",
    "rohaki-cms-admin/admin/src/components/admin/Sidebar.astro",
    "rohaki-cms-admin/admin/src/components/admin/Header.astro",
    "rohaki-cms-admin/admin/src/components/admin/ContentTable.astro",
    "rohaki-cms-admin/admin/src/components/admin/ContentForm.astro",
    "rohaki-cms-admin/admin/src/components/admin/Modal.astro",
    "rohaki-cms-admin/admin/src/components/admin/Toast.astro",
    "rohaki-cms-admin/admin/src/lib/api-client.ts",
    "rohaki-cms-admin/admin/src/lib/types.ts",
    "rohaki-cms-admin/admin/src/styles/admin.css",
    "rohaki-cms-admin/admin/astro.config.mjs",
    "rohaki-cms-admin/admin/package.json",
    "rohaki-cms-admin/admin/wrangler.toml",
    "rohaki-cms-admin/admin/tsconfig.json"
  ],
  "project_name": "rohaki-cms",
  "worker_project_name": "rohaki-cms",
  "admin_project_name": "rohaki-cms-admin",
  "d1_database_name": "rohaki-cms-db",
  "staging_url": "https://dev-cms.rohaki.example.com",
  "production_url": "https://cms.rohaki.example.com",
  "admin_staging": "https://dev-cms-admin.rohaki.example.com",
  "admin_production_url": "https://cms-admin.rohaki.example.com"
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

# Iteration B: Generate Admin UI (requires worker URL from Iteration A)
python -m skills.faber-cms.scripts.generate_admin_ui \
  --project-name rohaki-cms-admin \
  --output-dir ./rohaki-cms-admin \
  --worker-url https://rohaki-cms-worker.example.com \
  --fixture rohaki-brand
```

## Determinism Guarantee

Same inputs → byte-for-byte identical output. No LLM in generation path.

## Acceptance Criteria

### Iteration A (Worker + D1 + API) - Complete
1. Generates complete Cloudflare Worker project at `output_dir`
2. Worker has REST API: `GET/POST /api/content`, `GET/PUT/DELETE /api/content/:id`
3. D1 schema includes `content`, `collections`, `versions` tables with proper indexes
4. Cloudflare Access middleware validates requests before API handlers
5. `wrangler.toml` declares D1 binding, KV namespace for sessions, CF Access config
6. TypeScript compiles without errors (`npm run typecheck` passes)
7. Deploys to staging (`dev` branch) and production (`main` branch) per FRAMEWORK.md §13

### Iteration B (Admin UI) - Complete
1. Generates complete Astro admin UI project at `output_dir`
2. Admin UI includes Dashboard, Content List, Content Editor, and Settings pages
3. Admin UI uses Faber design system tokens for consistent theming
4. TypeScript API client provides type-safe access to Worker API
5. Admin UI deploys to Cloudflare Pages (separate deployment from Worker)
6. Admin UI validates input and handles loading/error states
7. Deterministic generation: same inputs produce byte-for-byte identical output

## References

- `skills/faber-design-system/` — Design tokens used by admin UI
- `skills/faber-splash/` — Admin UI patterns, CF Access integration
- Cloudflare Workers + D1 docs: https://developers.cloudflare.com/d1/
- Cloudflare Access: https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/
- Hono framework: https://hono.dev/ (recommended for Worker routing)
- Astro framework: https://astro.build/ (used for admin UI)

## Two-Iteration Plan - Both Complete

| Iteration | Scope | PR | Status |
|-----------|-------|-----|--------|
| **A** | Worker + D1 + REST API + CF Access | PR #70 | ✅ Complete |
| **B** | Embedded Astro Admin UI | This PR | ✅ Complete |

**Rationale:** The CMS is now fully functional with both a secure Worker API and an intuitive admin UI. The Worker can be used independently as a headless CMS, while the admin UI provides a visual content management interface.