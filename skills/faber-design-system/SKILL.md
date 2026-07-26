---
name: faber-design-system
description: Generates project-specific design system assets (Tailwind config, CSS custom properties, component utility classes) from a Faber fixture's design tokens. Extends scaffold's generic defaults with fixture-specific theming (e.g., Rohaki's green gradients, card grids, stats sections).
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - design-system
  - tailwind
  - css
  - fixture
  - cross-cutting
---

# Faber Design System Skill

## Purpose

The `faber-design-system` skill generates a complete, production-ready design system for a Faber-managed project by extending the framework's generic scaffold defaults with a **fixture's** design tokens.

**Key distinction:** This skill does NOT replace the scaffold's generic defaults. It EXTENDS them. Projects opt-in via `--fixture <name>`. The scaffold skill (`skills/scaffold/`) remains the source of framework-wide defaults (blue primary, system UI fonts, basic spacing).

## When to Use

- Scaffolding a new project that should adopt a specific brand (e.g., Rohaki's bamboo/sage/earth palette)
- Re-theming an existing project to a different fixture
- Generating design tokens for design tool handoff (Figma, Style Dictionary)

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fixture` | string | Yes | Name of the Faber fixture (e.g., `rohaki`). Must exist at `fixtures/<fixture>/design-tokens.json` |
| `output_dir` | string | Yes | Directory to write generated assets (relative to project root) |
| `format` | string | No | Output format: `css`, `tailwind`, `json`, `all` (default: `all`) |
| `project_root` | string | No | Project root for `apply` subcommand (default: cwd) |
| `overrides` | object | No | Token overrides to apply on top of fixture |

## Outputs

| Path | Description |
|------|-------------|
| `<output_dir>/tailwind.config.js` | Tailwind config extending framework base with fixture tokens |
| `<output_dir>/design-tokens.css` | CSS custom properties + component utility classes |
| `<output_dir>/design-tokens.json` | W3C Design Tokens format (for Style Dictionary, Figma Tokens Studio) |
| `<output_dir>/components.css` | Component utility classes (cards, buttons, grids, sections, typography) |

## Interface (JSON)

```json
{
  "fixture": "rohaki",
  "output_dir": "src/styles",
  "format": "all",
  "overrides": {}
}
```

Returns:

```json
{
  "generated": [
    "src/styles/tailwind.config.js",
    "src/styles/design-tokens.css",
    "src/styles/design-tokens.json",
    "src/styles/components.css"
  ],
  "fixture": "rohaki",
  "format": "all"
}
```

## CLI Usage

```bash
# Generate all formats to project's src/styles/
python -m skills.faber-design-system.design_system --fixture rohaki --output-dir src/styles

# Generate only Tailwind config
python -m skills.faber-design-system.design_system --fixture rohaki --output-dir src/styles --format tailwind

# Apply to existing Astro project (copies files, updates imports)
python -m skills.faber-design-system.apply_to_project --project-root . --fixture rohaki
```

## Determinism Guarantee

Same fixture + same overrides + same version → **byte-for-byte identical output**. No LLM in the generation path.

## Acceptance Criteria

1. Given `fixtures/rohaki/design-tokens.json`, emits valid Tailwind config that extends framework defaults
2. Emits CSS custom properties matching fixture spec (colors, spacing, typography, shadows, gradients, animations, breakpoints, z-index)
3. Emits component utility classes: `.rohaki-card`, `.rohaki-btn-*`, `.rohaki-badge-*`, `.rohaki-grid-*`, `.rohaki-section-*`, `.rohaki-heading`, `.rohaki-h1`–`.rohaki-h6`, `.rohaki-body`, `.rohaki-stat-*`
3. Emits W3C Design Tokens JSON valid against schema
4. Deterministic: two runs with same input produce identical output
5. `apply_to_project` copies files to correct locations and updates `astro.config.mjs` to import the design tokens CSS

## References

- `fixtures/rohaki/design-tokens.json` — Rohaki fixture tokens (W3C format)
- `fixtures/rohaki/tailwind.config.js` — Rohaki Tailwind config (reference)
- `fixtures/rohaki/design-tokens.css` — Rohaki CSS custom properties (reference)
- `skills/scaffold/scripts/scaffold.py` — Framework generic defaults (what this extends)
- W3C Design Tokens Format: https://design-tokens.github.io/community-group/format/