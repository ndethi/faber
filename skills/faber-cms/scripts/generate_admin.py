#!/usr/bin/env python3
"""
Faber CMS Admin UI Generator
Generates an Astro-based admin dashboard from config/defaults.yaml
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent.parent


def load_config(config_path: Path) -> Dict[str, Any]:
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_astro_config(config: Dict[str, Any]) -> str:
    content_types = config.get("contentTypes", [])
    collections_config = {ct["name"]: ct for ct in content_types}

    return f"""import {{ defineConfig }} from "astro/config";
import tailwind from "@astrojs/tailwind";
import react from "@astrojs/react";

export default defineConfig({{
  site: "https://admin.yourdomain.com",
  output: "static",
  integrations: [tailwind(), react()],
  adapter: "@astrojs/cloudflare",
  vite: {{
    ssr: {{
      external: ["@cloudflare/kv-asset-handler"]
    }}
  }}
}});
"""


def generate_package_json(config: Dict[str, Any]) -> str:
    return json.dumps({
        "name": "faber-cms-admin",
        "version": "1.1.0",
        "private": true,
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
            "astro": "^4.16.0",
            "@astrojs/tailwind": "^5.1.0",
            "@astrojs/react": "^3.6.0",
            "@astrojs/cloudflare": "^11.0.0",
            "react": "^18.3.0",
            "react-dom": "^18.3.0",
            "tailwindcss": "^3.4.0",
            "zod": "^3.23.0",
            "lucide-react": "^0.447.0",
            "date-fns": "^4.1.0",
            "clsx": "^2.1.0",
            "tailwind-merge": "^2.5.0"
        },
        "devDependencies": {
            "@types/react": "^18.3.0",
            "@types/react-dom": "^18.3.0",
            "typescript": "^5.6.0",
            "vitest": "^2.1.0",
            "playwright": "^1.47.0",
            "eslint": "^9.10.0",
            "@typescript-eslint/eslint-plugin": "^8.5.0",
            "@typescript-eslint/parser": "^8.5.0",
            "prettier": "^3.3.0",
            "prettier-plugin-astro": "^0.14.0"
        }
    }, indent=2)


def generate_tsconfig() -> str:
    return json.dumps({
        "compilerOptions": {
            "target": "ES2022",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "strict": true,
            "jsx": "react-jsx",
            "jsxImportSource": "react",
            "baseUrl": ".",
            "paths": {
                "@/*": ["src/*"]
            },
            "types": ["astro/client", "vitest/globals"]
        },
        "include": ["src/**/*", "astro.config.mjs"],
        "exclude": ["node_modules", "dist"]
    }, indent=2)


def generate_tailwind_config() -> str:
    return """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        bamboo: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
      },
    },
  },
  plugins: [],
};
"""


def generate_main_layout(config: Dict[str, Any]) -> str:
    content_types = config.get("contentTypes", [])
    nav_items = [{"name": ct["label"], "href": f"/admin/content?collection={ct['name']}", "icon": ct.get("uiConfig", {}).get("icon", {}).get("placeholder", "📄")} for ct in content_types]

    return f"""---
import {{ ViewTransitions }} from "astro:transitions";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
---

<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="generator" content={{Astro.generator}} />
    <title>Faber CMS Admin</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <ViewTransitions />
  </head>
  <body class="min-h-screen bg-gray-50 flex">
    <Sidebar />
    <div class="flex-1 flex flex-col min-w-0 ml-64 lg:ml-64">
      <Header />
      <main class="flex-1 p-6 lg:p-8 overflow-auto">
        <slot />
      </main>
    </div>
  </body>
</html>

<style is:global>
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
</style>
"""


def generate_dashboard_page(config: Dict[str, Any]) -> str:
    return """---
import BaseLayout from "@/layouts/BaseLayout";
import StatsGrid from "@/components/StatsGrid";
import ActivityFeed from "@/components/ActivityFeed";
import QuickActions from "@/components/QuickActions";
---

<BaseLayout title="Dashboard">
  <div class="space-y-8">
    <header>
      <h1 class="text-3xl font-bold text-bamboo-900">Dashboard</h1>
      <p class="text-bamboo-600 mt-1">Overview of your content and activity</p>
    </header>

    <StatsGrid />

    <div class="grid lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <ActivityFeed />
      </div>
      <div>
        <QuickActions />
      </div>
    </div>
  </div>
</BaseLayout>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate Faber CMS Admin UI project")
    parser.add_argument("--config", default="config/defaults.yaml", help="Path to config YAML")
    parser.add_argument("--output-dir", default="admin", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    if args.dry_run:
        print("DRY RUN - Would generate:")
        print(f"  Output directory: {output_dir}")
        print(f"  Content types: {[ct['name'] for ct in config.get('contentTypes', [])]}")
        print(f"  Pages: Dashboard, Content List, Content Editor, Media Library, Collections Manager, Settings")
        return

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate config files
    (output_dir / "astro.config.mjs").write_text(generate_astro_config(config))
    (output_dir / "package.json").write_text(generate_package_json(config))
    (output_dir / "tsconfig.json").write_text(generate_tsconfig())
    (output_dir / "tailwind.config.js").write_text(generate_tailwind_config())

    # Create directory structure
    (output_dir / "src" / "layouts").mkdir(parents=True, exist_ok=True)
    (output_dir / "src" / "components").mkdir(parents=True, exist_ok=True)
    (output_dir / "src" / "pages" / "admin" / "content").mkdir(parents=True, exist_ok=True)
    (output_dir / "src" / "pages" / "admin" / "media").mkdir(parents=True, exist_ok=True)
    (output_dir / "src" / "pages" / "admin" / "collections").mkdir(parents=True, exist_ok=True)
    (output_dir / "src" / "pages" / "admin" / "settings").mkdir(parents=True, exist_ok=True)

    # Generate main layout
    (output_dir / "src" / "layouts" / "BaseLayout.astro").write_text(generate_main_layout(config))

    # Generate dashboard page
    (output_dir / "src" / "pages" / "admin" / "index.astro").write_text(generate_dashboard_page(config))

    # Install dependencies and verify
    print("\nInstalling dependencies...")
    subprocess.run(["npm", "install"], cwd=output_dir, check=True)

    print("\nRunning build...")
    result = subprocess.run(["npm", "run", "build"], cwd=output_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Build failed:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)

    print("\n✅ Admin UI project generated and verified successfully!")
    print(f"Output: {output_dir.absolute()}")


if __name__ == "__main__":
    main()