#!/usr/bin/env python3
"""
Scaffold Skill - Lifecycle skill #2: creates project structure from intent-collect artifacts.

Reads intent outputs (spec.md, trajectory.md, scope-baseline.md), generates:
- Directory structure per FRAMEWORK.md conventions
- Config files (package.json, astro.config.mjs, wrangler.toml, etc.)
- CI workflows (.github/workflows/)
- Boilerplate code (Astro + Cloudflare Pages defaults per FRAMEWORK.md §8)
- Skill stubs for remaining lifecycle stages

Inputs: --input-dir (containing spec.md, trajectory.md, scope-baseline.md)
Outputs: Project structure in --output-dir
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# FRAMEWORK.md §8 defaults
DEFAULT_FRAMEWORK = "astro"
DEFAULT_DEPLOY_TARGET = "cloudflare-pages"
DEFAULT_PACKAGE_MANAGER = "npm"

# Lifecycle stages in order (per FRAMEWORK.md §2)
LIFECYCLE_STAGES = [
    "intent-collect",
    "scaffold",
    "build",
    "evaluate",
    "deploy",
    "publish",
    "observe",
    "feedback"
]

# Stage to directory mapping
STAGE_DIRS = {
    "intent-collect": [],
    "scaffold": [],
    "build": ["scripts/build"],
    "evaluate": ["scripts/evaluate"],
    "deploy": ["scripts/deploy"],
    "publish": ["scripts/publish"],
    "observe": ["scripts/observe"],
    "feedback": ["scripts/feedback"],
}

# Common project directories
BASE_DIRS = [
    "src",
    "src/pages",
    "src/components",
    "src/layouts",
    "src/styles",
    "public",
    "tests",
    "scripts",
    ".github/workflows",
    "docs",
]


def parse_spec(spec_path: Path) -> Dict[str, Any]:
    """Parse spec.md and extract acceptance criteria."""
    content = spec_path.read_text()
    
    spec = {
        "acceptance_criteria": [],
        "goal": "",
        "audience": "",
        "non_goals": "",
        "constraints": "",
    }
    
    # Extract SPEC-XX items
    spec_pattern = r"SPEC-(\d+):\s*(.+)"
    for match in re.finditer(spec_pattern, content):
        spec_id = int(match.group(1))
        spec_text = match.group(2).strip()
        spec["acceptance_criteria"].append({
            "id": f"SPEC-{spec_id:02d}",
            "text": spec_text
        })
    
    # Extract context fields
    for field in ["goal", "audience", "non_goals", "constraints"]:
        pattern = rf"- {field.capitalize()}:\s*(.+)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            spec[field] = match.group(1).strip()
    
    return spec


def parse_trajectory(trajectory_path: Path) -> Dict[str, Any]:
    """Parse trajectory.md and extract ordered steps."""
    content = trajectory_path.read_text()
    
    trajectory = {
        "strictness": "ordered",
        "steps": [],
        "checkpoints": []
    }
    
    # Extract strictness
    strictness_match = re.search(r"strictness:\s*(\w+)", content, re.IGNORECASE)
    if strictness_match:
        trajectory["strictness"] = strictness_match.group(1)
    
    # Extract numbered steps
    step_pattern = r"^\d+\.\s*(.+)$"
    for line in content.splitlines():
        match = re.match(step_pattern, line.strip())
        if match:
            step = match.group(1).strip()
            if any(cp in step.lower() for cp in ["hitl", "gate", "review", "confirmation"]):
                trajectory["checkpoints"].append(step)
            else:
                trajectory["steps"].append(step)
    
    return trajectory


def parse_scope_baseline(scope_path: Path) -> Dict[str, Any]:
    """Parse scope-baseline.md for project metadata."""
    content = scope_path.read_text()
    
    scope = {
        "project_name": "project",
        "description": "",
    }
    
    # Try to extract project name from goal
    goal_match = re.search(r"- Goal:\s*(.+)", content)
    if goal_match:
        goal = goal_match.group(1).strip()
        # Convert to kebab-case project name
        scope["project_name"] = re.sub(r"[^a-z0-9]+", "-", goal.lower()).strip("-")
        scope["description"] = goal
    
    return scope


def generate_package_json(spec: Dict, scope: Dict) -> str:
    """Generate package.json for Astro + Cloudflare Pages."""
    project_name = scope.get("project_name", "project")
    
    return json.dumps({
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "astro dev",
            "build": "astro build",
            "preview": "astro preview",
            "lint": "eslint src --ext .ts,.tsx,.astro",
            "format": "prettier --write \"src/**/*.{ts,tsx,astro,css,md}\"",
            "test": "vitest run",
            "test:watch": "vitest"
        },
        "dependencies": {
            "astro": "^4.16.0"
        },
        "devDependencies": {
            "@astrojs/check": "^0.9.0",
            "@cloudflare/astro-integration": "^1.0.0",
            "eslint": "^9.0.0",
            "prettier": "^3.2.0",
            "prettier-plugin-astro": "^0.13.0",
            "typescript": "^5.4.0",
            "vitest": "^1.4.0",
            "wrangler": "^3.30.0"
        },
        "engines": {
            "node": ">=18.14.1"
        }
    }, indent=2)


def generate_astro_config(spec: Dict, scope: Dict) -> str:
    """Generate astro.config.mjs with Cloudflare Pages adapter."""
    return '''import { defineConfig } from "astro/config";
import cloudflare from "@cloudflare/astro-integration";

export default defineConfig({
  site: "https://example.com",
  integrations: [cloudflare()],
  output: "static",
  adapter: cloudflare({
    platformProxy: {
      enabled: true
    }
  }),
  vite: {
    ssr: {
      external: ["@cloudflare/kv-asset-handler"]
    }
  }
});'''


def generate_wrangler_toml(spec: Dict, scope: Dict) -> str:
    """Generate wrangler.toml for Cloudflare Pages."""
    project_name = scope.get("project_name", "project")
    
    return f'''name = "{project_name}"
compatibility_date = "2024-01-01"
pages_build_output_dir = "./dist"

[vars]
ENVIRONMENT = "production"

[[kv_namespaces]]
binding = "SITE_KV"
id = "<your-kv-namespace-id>"
preview_id = "<your-preview-kv-namespace-id>"
'''


def generate_tsconfig() -> str:
    """Generate tsconfig.json for Astro."""
    return json.dumps({
        "extends": "astro/tsconfigs/strict",
        "compilerOptions": {
            "strictNullChecks": True,
            "baseUrl": ".",
            "paths": {
                "@/*": ["src/*"]
            }
        },
        "include": ["src/**/*", "astro.config.mjs", "wrangler.toml"],
        "exclude": ["node_modules", "dist"]
    }, indent=2)


def generate_eslint_config() -> str:
    """Generate eslint.config.js."""
    return '''export default [
  {
    files: ["**/*.{js,ts,astro}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        browser: true,
        node: true
      }
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off"
    }
  }
];'''


def generate_prettier_config() -> str:
    """Generate .prettierrc."""
    return json.dumps({
        "plugins": ["prettier-plugin-astro"],
        "overrides": [
            {
                "files": "*.astro",
                "options": {
                    "parser": "astro"
                }
            }
        ],
        "singleQuote": True,
        "tabWidth": 2,
        "trailingComma": "es5"
    }, indent=2)


def generate_gitignore() -> str:
    """Generate .gitignore."""
    return '''# Dependencies
node_modules/

# Build outputs
dist/
.build/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Testing
coverage/

# Cloudflare
wrangler.toml.local
.dev.vars
'''


def generate_github_workflow_ci(spec: Dict, scope: Dict) -> str:
    """Generate CI workflow for GitHub Actions."""
    project_name = scope.get("project_name", "project")
    
    return f'''name: CI

on:
  push:
    branches: [dev, main]
  pull_request:
    branches: [dev, main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint
      
      - name: Run type check
        run: npx astro check
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build

  deploy-preview:
    needs: lint-and-test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
      
      - name: Deploy to Cloudflare Pages Preview
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: {project_name}-preview
          directory: ./dist
          branch: preview/${{ github.head_ref }}
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}
'''


def generate_github_workflow_deploy(spec: Dict, scope: Dict) -> str:
    """Generate deploy workflow for main branch."""
    project_name = scope.get("project_name", "project")
    
    return f'''name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
      
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: {project_name}
          directory: ./dist
          branch: main
'''


def generate_astro_boilerplate() -> Dict[str, str]:
    """Generate basic Astro boilerplate files."""
    return {
        "src/pages/index.astro": '''---
import BaseLayout from "@/layouts/BaseLayout.astro";
---

<BaseLayout title="Welcome">
  <main class="container">
    <h1>Welcome to Your Project</h1>
    <p>Built with Astro + Cloudflare Pages</p>
  </main>
</BaseLayout>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    text-align: center;
  }
</style>''',
        
        "src/layouts/BaseLayout.astro": '''---
interface Props {
  title: string;
}

const { title } = Astro.props;
---

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="generator" content={Astro.generator} />
    <title>{title}</title>
  </head>
  <body>
    <slot />
  </body>
</html>''',
        
        "src/styles/global.css": '''/* Global styles */
:root {
  --font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --color-primary: #0066cc;
  --color-background: #ffffff;
  --color-text: #1a1a1a;
}

* {
  box-sizing: border-box;
}

html {
  font-family: var(--font-family);
  line-height: 1.6;
  color: var(--color-text);
  background-color: var(--color-background);
}

body {
  margin: 0;
  min-height: 100vh;
}

a {
  color: var(--color-primary);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}''',
        
        "src/components/Header.astro": '''---
interface Props {
  title: string;
}

const { title } = Astro.props;
---

<header class="site-header">
  <h1>{title}</h1>
</header>

<style>
  .site-header {
    padding: 1rem 2rem;
    border-bottom: 1px solid #e0e0e0;
  }
</style>''',
        
        "src/components/Footer.astro": '''---
---

<footer class="site-footer">
  <p>&copy; {new Date().getFullYear()} Project. Built with Astro.</p>
</footer>

<style>
  .site-footer {
    padding: 1rem 2rem;
    text-align: center;
    border-top: 1px solid #e0e0e0;
    color: #666;
    font-size: 0.875rem;
  }
</style>''',
        
        "tests/example.test.ts": '''import { describe, it, expect } from "vitest";

describe("Project setup", () => {
  it("should have basic test infrastructure", () => {
    expect(true).toBe(true);
  });
});''',
        
        "README.md": '''# Project

Generated by Faber scaffold skill from intent-collect artifacts.

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Deploy

Configure Cloudflare Pages with:
- Build command: `npm run build`
- Output directory: `dist`

## Structure

- `src/` - Astro source files
- `public/` - Static assets
- `tests/` - Vitest tests
- `scripts/` - Build/deploy scripts
- `.github/workflows/` - CI/CD pipelines
''',
    }


def generate_skill_stubs(trajectory: Dict) -> Dict[str, str]:
    """Generate placeholder skill scripts for remaining lifecycle stages."""
    stubs = {}
    
    for stage in LIFECYCLE_STAGES:
        if stage in ["intent-collect", "scaffold"]:
            continue  # Already exist
        
        # Determine which trajectory steps map to this stage
        stage_steps = [s for s in trajectory["steps"] if stage in s.lower()]
        
        stubs[f"scripts/{stage}/{stage}.py"] = f'''#!/usr/bin/env python3
"""
{stage.capitalize()} Skill - Lifecycle stage: {stage}

Generated by scaffold skill from trajectory.
TODO: Implement actual logic per FRAMEWORK.md conventions.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def main() -> None:
    parser = argparse.ArgumentParser(description="{stage.capitalize()} skill")
    parser.add_argument("--input-dir", required=True, help="Input directory with artifacts")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--hitl-gate", action="store_true", help="Enable HITL gate")
    
    args = parser.parse_args()
    
    # TODO: Implement {stage} logic
    # Input artifacts: spec.md, trajectory.md, scope-baseline.md + previous stage outputs
    
    result = {{
        "status": "success",
        "stage": "{stage}",
        "artifacts": [],
        "hitl_gate_required": args.hitl_gate,
        "hitl_gate_passed": True,
        "note": "TODO: Implement {stage} skill logic"
    }}
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
'''
    
    return stubs


def read_intent_artifacts(input_dir: Path) -> Tuple[Dict, Dict, Dict]:
    """Read and parse the three intent-collect artifacts."""
    spec_path = input_dir / "spec.md"
    trajectory_path = input_dir / "trajectory.md"
    scope_path = input_dir / "scope-baseline.md"
    
    if not spec_path.exists():
        raise FileNotFoundError(f"spec.md not found in {input_dir}")
    if not trajectory_path.exists():
        raise FileNotFoundError(f"trajectory.md not found in {input_dir}")
    if not scope_path.exists():
        raise FileNotFoundError(f"scope-baseline.md not found in {input_dir}")
    
    spec = parse_spec(spec_path)
    trajectory = parse_trajectory(trajectory_path)
    scope = parse_scope_baseline(scope_path)
    
    return spec, trajectory, scope


def write_files(file_map: Dict[str, str], output_dir: Path) -> List[str]:
    """Write all files to output directory."""
    written = []
    
    for rel_path, content in file_map.items():
        full_path = output_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        written.append(rel_path)
    
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold: create project structure from intent-collect artifacts"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing spec.md, trajectory.md, scope-baseline.md"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write project structure (default: current)"
    )
    parser.add_argument(
        "--hitl-gate",
        action="store_true",
        help="Enable HITL gate (requires manual confirmation before writing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing"
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Read and parse intent artifacts
    try:
        spec, trajectory, scope = read_intent_artifacts(input_dir)
    except FileNotFoundError as e:
        print(json.dumps({
            "status": "error",
            "error": str(e),
            "artifacts": []
        }, indent=2))
        sys.exit(1)
    
    # Build file map
    file_map = {}
    
    # Base directories
    for dir_path in BASE_DIRS:
        file_map[f"{dir_path}/.gitkeep"] = ""
    
    # Config files
    file_map["package.json"] = generate_package_json(spec, scope)
    file_map["astro.config.mjs"] = generate_astro_config(spec, scope)
    file_map["wrangler.toml"] = generate_wrangler_toml(spec, scope)
    file_map["tsconfig.json"] = generate_tsconfig()
    file_map["eslint.config.js"] = generate_eslint_config()
    file_map[".prettierrc"] = generate_prettier_config()
    file_map[".gitignore"] = generate_gitignore()
    
    # CI/CD workflows
    file_map[".github/workflows/ci.yml"] = generate_github_workflow_ci(spec, scope)
    file_map[".github/workflows/deploy.yml"] = generate_github_workflow_deploy(spec, scope)
    
    # Astro boilerplate
    for rel_path, content in generate_astro_boilerplate().items():
        file_map[rel_path] = content
    
    # Skill stubs for remaining lifecycle stages
    for rel_path, content in generate_skill_stubs(trajectory).items():
        file_map[rel_path] = content
    
    # Summary document
    summary = f"""# Scaffold Output Summary

Generated from intent-collect artifacts at: {datetime.now(timezone.utc).isoformat()}

## Input Artifacts
- spec.md: {len(spec['acceptance_criteria'])} acceptance criteria
- trajectory.md: {len(trajectory['steps'])} steps, strictness={trajectory['strictness']}
- scope-baseline.md: project="{scope['project_name']}"

## Generated Files
{chr(10).join(f"- {f}" for f in sorted(file_map.keys()))}

## Framework Defaults (per FRAMEWORK.md §8)
- Framework: Astro
- Deploy Target: Cloudflare Pages
- Package Manager: npm

## Next Steps
1. Review generated structure
2. Run `npm install` in output directory
3. Run `npm run dev` to preview
4. Implement remaining lifecycle skills (build, evaluate, deploy, publish, observe, feedback)
"""
    file_map["SCAFFOLD_SUMMARY.md"] = summary
    
    # HITL gate
    hitl_gate_passed = True
    if args.hitl_gate and not args.dry_run:
        print("\n=== HITL GATE: Scaffold Review Required ===")
        print(f"Would create {len(file_map)} files in {output_dir}")
        print("Key files:")
        for f in sorted(file_map.keys())[:20]:
            print(f"  - {f}")
        if len(file_map) > 20:
            print(f"  ... and {len(file_map) - 20} more")
        print("\nProceed? [y/N]: ", end="", flush=True)
        try:
            response = input().strip().lower()
            if response not in ('y', 'yes'):
                hitl_gate_passed = False
                print("HITL gate not passed. Exiting without writing files.")
        except (EOFError, KeyboardInterrupt):
            hitl_gate_passed = False
            print("\nHITL gate interrupted. Exiting without writing files.")
    
    if args.dry_run:
        print(json.dumps({
            "status": "dry_run",
            "would_create": len(file_map),
            "files": sorted(file_map.keys()),
            "hitl_gate_required": args.hitl_gate,
            "hitl_gate_passed": hitl_gate_passed
        }, indent=2))
        return
    
    if not hitl_gate_passed:
        print(json.dumps({
            "status": "hitl_gate_failed",
            "artifacts": [],
            "hitl_gate_required": True,
            "hitl_gate_passed": False
        }, indent=2))
        sys.exit(1)
    
    # Write files
    written = write_files(file_map, output_dir)
    
    # Emit machine-readable summary
    result = {
        "status": "success",
        "artifacts": written,
        "hitl_gate_required": args.hitl_gate,
        "hitl_gate_passed": True,
        "input_artifacts": {
            "spec": str(input_dir / "spec.md"),
            "trajectory": str(input_dir / "trajectory.md"),
            "scope_baseline": str(input_dir / "scope-baseline.md")
        },
        "output_dir": str(output_dir),
        "acceptance_criteria_count": len(spec["acceptance_criteria"]),
        "trajectory_steps": len(trajectory["steps"]),
        "project_name": scope.get("project_name", "project")
    }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()