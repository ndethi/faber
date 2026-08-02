#!/usr/bin/env python3
"""
Faber CMS Admin UI Generator - Iteration B

Generates an embedded Astro admin UI for the CMS Worker.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

from generate_admin_routes import generate_admin_pages
from generate_admin_components import generate_admin_components
from generate_admin_api_client import generate_admin_api_client
from apply_design_system import apply_design_system
from setup_admin_project import setup_admin_project

app = typer.Typer(help="Faber CMS Admin UI Generator - Iteration B: Embedded Astro Admin UI")


def load_worker_config(file_path: str) -> Dict[str, Any]:
    """Load Worker configuration from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


@app.command()
def generate(
    project_name: str = typer.Option(..., "--project-name", help="Project name (e.g., rohaki-cms-admin)"),
    output_dir: str = typer.Option(..., "--output-dir", help="Output directory for generated admin project"),
    worker_url: str = typer.Option(..., "--worker-url", help="URL of the deployed CMS Worker API (e.g., https://cms.example.com)"),
    fixture: str = typer.Option("faber-brand", "--fixture", help="Design system fixture (default: faber-brand)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated without writing files"),
    content_types_file: Optional[str] = typer.Option(None, "--content-types-file", help="JSON file with content types (optional)"),
):
    """Generate the complete admin UI project."""

    config = {
        "project_name": project_name,
        "output_dir": output_dir,
        "worker_url": worker_url,
        "fixture": fixture,
    }

    if content_types_file:
        config["content_types_file"] = content_types_file

    if dry_run:
        typer.echo("=== DRY RUN: Would generate ===")
        typer.echo(json.dumps(config, indent=2))
        typer.echo("\nFiles that would be created:")
        files = [
            f"{output_dir}/src/pages/admin/index.astro",
            f"{output_dir}/src/pages/admin/content.astro",
            f"{output_dir}/src/pages/admin/content/[collection].astro",
            f"{output_dir}/src/pages/admin/content/[collection]/[id].astro",
            f"{output_dir}/src/pages/admin/settings.astro",
            f"{output_dir}/src/components/admin/Sidebar.astro",
            f"{output_dir}/src/components/admin/Header.astro",
            f"{output_dir}/src/components/admin/ContentTable.astro",
            f"{output_dir}/src/components/admin/ContentForm.astro",
            f"{output_dir}/src/components/admin/Modal.astro",
            f"{output_dir}/src/components/admin/Toast.astro",
            f"{output_dir}/src/components/admin/ConfirmDialog.astro",
            f"{output_dir}/src/lib/api-client.ts",
            f"{output_dir}/src/lib/types.ts",
            f"{output_dir}/src/styles/admin.css",
            f"{output_dir}/package.json",
            f"{output_dir}/astro.config.mjs",
            f"{output_dir}/wrangler.toml",
            f"{output_dir}/.github/workflows/deploy.yml",
        ]
        for f in files:
            typer.echo(f"  {f}")
        return

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Generating admin UI for {project_name}...")

    # 1. Setup admin project structure
    typer.echo("  → Setting up admin project structure...")
    setup_admin_project(config, out_path)

    # 2. Apply design system tokens
    typer.echo(f"  → Applying design system fixture: {fixture}...")
    apply_design_system(config, out_path)

    # 3. Generate admin pages
    typer.echo("  → Generating admin pages...")
    pages = generate_admin_pages(config)
    for name, content in pages.items():
        (out_path / "src" / "pages" / "admin" / f"{name}.astro").write_text(content)

    # 4. Generate admin components
    typer.echo("  → Generating admin components...")
    components = generate_admin_components(config)
    (out_path / "src" / "components" / "admin").mkdir(parents=True, exist_ok=True)
    for name, content in components.items():
        (out_path / "src" / "components" / "admin" / f"{name}.astro").write_text(content)

    # 5. Generate API client
    typer.echo("  → Generating API client...")
    api_client = generate_admin_api_client(config)
    (out_path / "src" / "lib").mkdir(parents=True, exist_ok=True)
    (out_path / "src" / "lib" / "api-client.ts").write_text(api_client["api-client.ts"])
    (out_path / "src" / "lib" / "types.ts").write_text(api_client["types.ts"])

    typer.echo(f"\n✓ Generated complete admin UI at {output_dir}")
    typer.echo(f"  Project: {project_name}")
    typer.echo(f"  Worker URL: {worker_url}")
    typer.echo(f"  Fixture: {fixture}")
    typer.echo(f"\nNext steps:")
    typer.echo(f"  cd {output_dir}")
    typer.echo(f"  npm install")
    typer.echo(f"  npm run dev")
    typer.echo(f"  # Configure WRANGLER_* env vars for deployment")
    typer.echo(f"  # Then deploy: npm run deploy:staging / npm run deploy:production")


if __name__ == "__main__":
    app()