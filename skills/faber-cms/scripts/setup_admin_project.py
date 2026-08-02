#!/usr/bin/env python3
"""
Faber CMS Admin - Admin Project Setup

Sets up the Astro project structure for the admin UI.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


def setup_admin_project(config: Dict[str, Any], output_path: Path) -> None:
    """Set up the admin Astro project structure."""
    project_name = config["project_name"]

    # Create package.json
    package_json = {
        "name": project_name,
        "version": "0.1.0",
        "description": f"Admin UI for {project_name} CMS",
        "private": True,
        "scripts": {
            "dev": "astro dev",
            "start": "astro dev",
            "build": "astro build",
            "preview": "astro preview",
            "astro": "astro",
            "deploy:staging": "wrangler pages deploy ./dist --branch=staging --env=staging",
            "deploy:production": "wrangler pages deploy ./dist --branch=main --env=production",
            "deploy": "npm run deploy:production",
            "typecheck": "tsc --noEmit"
        },
        "dependencies": {
            "astro": "^3.0.0"
        },
        "devDependencies": {
            "typescript": "^5.0.0",
            "@types/node": "^20.0.0",
            "wrangler": "^3.0.0"
        }
    }

    (output_path / "package.json").write_text(json.dumps(package_json, indent=2))

    # Create astro.config.mjs
    astro_config = """import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://admin.example.com', // Update with your domain
  base: '/',
  trailingSlash: 'never',
  build: {
    format: 'file'
  },
  vite: {
    plugins: []
  }
});
"""
    (output_path / "astro.config.mjs").write_text(astro_config)

    # Create tsconfig.json
    tsconfig = {
        "extends": "astro/tsconfigs/strict",
        "compilerOptions": {
            "baseUrl": ".",
            "paths": {
                "@/*": ["./src/*"]
            }
        },
        "include": ["src/**/*.ts", "src/**/*.astro", "src/**/*.js"],
        "exclude": ["node_modules/**", "dist/**"]
    }
    (output_path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    # Create basic directory structure
    (output_path / "src" / "components" / "admin").mkdir(parents=True, exist_ok=True)
    (output_path / "src" / "components" / "ui").mkdir(parents=True, exist_ok=True)
    (output_path / "src" / "layouts").mkdir(parents=True, exist_ok=True)
    (output_path / "src" / "lib").mkdir(parents=True, exist_ok=True)
    (output_path / "src" / "pages" / "admin").mkdir(parents=True, exist_ok=True)
    (output_path / "src" / "styles").mkdir(parents=True, exist_ok=True)
    (output_path / "public").mkdir(parents=True, exist_ok=True)

    # Create basic layout
    layout = """---
// BaseLayout.astro - Admin Layout
--->
<slot />
"""
    (output_path / "src" / "layouts" / "BaseLayout.astro").write_text(layout)

    # Create basic CSS
    css = """/* admin.css - Admin Styles */
:root {
  /* These will be overridden by design system tokens */
  --faber-primary: #10b981;
  --faber-primary-dark: #059669;
  --faber-background: #ffffff;
  --faber-surface: #f9fafb;
  --faber-surface-hover: #f3f4f6;
  --faber-border: #e5e7eb;
  --faber-text: #111827;
  --faber-text-muted: #6b7280;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  font-size: 16px;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
  background-color: var(--faber-background);
  color: var(--faber-text);
  line-height: 1.6;
}

a {
  color: var(--faber-primary);
  text-decoration: underline;
}

a:hover {
  text-decoration: underline;
}

/* Utility classes */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-left { text-align: left; }

.hidden { display: none; }

.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.justify-center { justify-content: center; }
.space-x-2 > * + * { margin-left: 0.5rem; }
.space-y-2 > * + * { margin-top: 0.5rem; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }

.p-1 { padding: 0.25rem; }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.p-8 { padding: 2rem; }

.py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }

.px-1 { padding-left: 0.25rem; padding-right: 0.25rem; }
.px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
.px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }

.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mt-6 { margin-top: 1.5rem; }
.mt-8 { margin-top: 2rem; }

.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mb-8 { margin-bottom: 2rem; }

.rounded { border-radius: 0.25rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }

.border { border-width: 1px; }
.border-t { border-top-width: 1px; }
.border-b { border-bottom-width: 1px; }

.bg-faber-background { background-color: var(--faber-background); }
.bg-faber-surface { background-color: var(--faber-surface); }
.bg-faber-surface-hover { background-color: var(--faber-surface-hover); }
.bg-faber-primary { background-color: var(--faber-primary); }
.bg-faber-primary-dark { background-color: var(--faber-primary-dark); }

.text-faber-text { color: var(--faber-text); }
.text-faber-text-muted { color: var(--faber-text-muted); }
.text-faber-primary { color: var(--faber-primary); }
.text-faber-primary-dark { color: var(--faber-primary-dark); }

.text-sm { font-size: 0.875rem; }
.text-base { font-size: 1rem; }
.text-lg { font-size: 1.125rem; }
.text-xl { font-size: 1.25rem; }
.text-2xl { font-size: 1.5rem; }
.text-3xl { font-size: 1.875rem; }

.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

.hover\\:bg-faber-surface-hover:hover { background-color: var(--faber-surface-hover); }
.hover\\:bg-faber-primary-dark:hover { background-color: var(--faber-primary-dark); }
.hover\\:underline:hover { text-decoration: underline; }

.transition-colors { transition-property: background-color, border-color, color, fill, stroke; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }

/* Form styles */
input,
select,
textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--faber-border);
  border-radius: 0.25rem;
  background-color: var(--faber-background);
  color: var(--faber-text);
  font-family: inherit;
  font-size: 0.875rem;
}

input:focus,
select:focus,
textarea:focus {
  outline: 2px solid var(--faber-primary);
  outline-offset: 2px;
  border-color: transparent;
}

input::placeholder,
textarea::placeholder {
  color: var(--faber-text-muted);
  opacity: 0.7;
}

/* Button styles */
button {
  cursor: pointer;
  font-family: inherit;
  border: none;
  border-radius: 0.25rem;
  font-weight: 500;
  transition: all 0.15s ease-in-out;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Table styles */
table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--faber-border);
}

th {
  font-weight: 600;
  background-color: var(--faber-surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

tr:hover {
  background-color: var(--faber-surface-hover);
}

/* Responsive */
@media (max-width: 640px) {
  .hidden\\:sm\\:block { display: none; }
}
"""
    (output_path / "src" / "styles" / "admin.css").write_text(css)

    # Create .gitignore
    gitignore = """# Dependencies
node_modules/
.pnpm-debug.log*

# Built files
dist/
 .astro/

# Environment
.env
.env.*

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# OS
.DS_Store
Thumbs.db

# Wrangler
wrangler.state.json
.wrangler/
"""
    (output_path / ".gitignore").write_text(gitignore)

    # Create README
    readme = f"""# {project_name} - CMS Admin UI

Admin interface for managing content in the Faber CMS.

## Development

```bash
npm install
npm run dev
```

## Deployment

### Staging
```bash
npm run deploy:staging
```

### Production
```bash
npm run deploy:production
```

## Configuration

This admin UI connects to a Faber CMS Worker at:
{worker_url}

Update the worker URL in wrangler.toml if needed.
"""
    (output_path / "README.md").write_text(readme)

    # Create basic wrangler.toml for Pages
    wrangler = f"""name = "{project_name}"
main = "./dist/index.html"
compatibility_date = "2024-01-01"

[env.staging]
name = "{project_name}-staging"
compatibility_date = "2024-01-01"

[env.production]
name = "{project_name}"
compatibility_date = "2024-01-01"

[vars]
WORKER_URL = "{worker_url}"
"""
    (output_path / "wrangler.toml").write_text(wrangler)

    print(f"✓ Admin project structure created at {output_path}")


if __name__ == "__main__":
    print("Use via generate_admin_ui.py")