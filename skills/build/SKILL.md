---
name: build
description: |
  Compiles source files using the framework default stack (Astro + Cloudflare Pages) and produces the final artifact for a Faber component. The skill is deterministic, runs locally with the same configuration each time, and outputs a summary of generated files.
version: 1.0.0
author: ndethi
---

# Build Skill

## Overview
- Runs the framework default build toolchain (**Astro** with **Cloudflare Pages** output) for the target component.
- Emits a deterministic artifact directory (e.g., `dist/`).
- Returns a JSON payload listing the files created and their SHA‑256 hashes.

## Interface
```json
{
  "component": "string",      // name of the component to build
  "options": {                // optional flags
    "watch": false,
    "minify": true,
    "stack": "astro",         // framework default
    "host": "cloudflare-pages" // framework default
  }
}
```

## Evaluation
The skill passes when:
- The expected `dist/` directory exists.
- All files listed in the output JSON are present and match the reported hashes.
- The build process exits with code 0.