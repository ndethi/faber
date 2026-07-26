#!/usr/bin/env python3
"""
Tests for faber-design-system skill - apply to project.

Verifies that apply_to_project correctly:
- Copies generated assets to project
- Updates astro.config.mjs imports
- Updates global.css imports
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestApplyToProject:
    """Test applying design system to an Astro project."""

    FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "rohaki"
    SKILL_DIR = Path(__file__).parent.parent.parent / "faber-design-system"
    SCRIPT = SKILL_DIR / "scripts" / "design_system.py"

    def run_apply(self, project_root: Path) -> subprocess.CompletedProcess:
        """Run the apply command."""
        cmd = [
            "python", str(self.SCRIPT),
            "apply",
            "--project-root", str(project_root),
            "--fixture", "rohaki",
            "--output-dir", "src/styles",
            "--fixtures-dir", "fixtures"
        ]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=self.SKILL_DIR.parent.parent.parent)

    def create_minimal_astro_project(self, project_root: Path):
        """Create a minimal Astro project structure."""
        # Create directory structure
        (project_root / "src" / "styles").mkdir(parents=True)
        (project_root / "src" / "pages").mkdir(parents=True)
        (project_root / "src" / "components").mkdir(parents=True)
        (project_root / "src" / "layouts").mkdir(parents=True)
        (project_root / "public").mkdir(parents=True)

        # Create minimal package.json
        (project_root / "package.json").write_text(json.dumps({
            "name": "test-project",
            "version": "0.1.0",
            "type": "module",
            "scripts": {"dev": "astro dev", "build": "astro build"},
            "dependencies": {"astro": "^4.0.0"},
            "devDependencies": {"typescript": "^5.0.0"}
        }, indent=2))

        # Create minimal astro.config.mjs
        (project_root / "astro.config.mjs").write_text("""import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://example.com",
  output: "static",
});
""")

        # Create minimal global.css
        (project_root / "src" / "styles" / "global.css").write_text("""/* Global styles */
:root {
  --color-primary: #0066cc;
}

body {
  margin: 0;
  font-family: system-ui, sans-serif;
}
""")

        # Create minimal index.astro
        (project_root / "src" / "pages" / "index.astro").write_text("""---
import BaseLayout from "../layouts/BaseLayout.astro";
---

<BaseLayout title="Test">
  <main>Hello World</main>
</BaseLayout>
""")

        # Create minimal BaseLayout
        (project_root / "src" / "layouts" / "BaseLayout.astro").write_text("""---
interface Props {
  title: string;
}
const { title } = Astro.props;
---

<!DOCTYPE html>
<html lang="en">
  <head>
    <title>{title}</title>
  </head>
  <body>
    <slot />
  </body>
</html>
""")

    def test_apply_creates_design_tokens(self):
        """Test that apply creates design tokens files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test-project"
            project.mkdir()
            self.create_minimal_astro_project(project)

            # Copy fixture to project
            import shutil
            shutil.copytree(self.FIXTURE_DIR, project / "fixtures" / "rohaki")

            result = self.run_apply(project)
            assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

            # Check design tokens files created
            assert (project / "src" / "styles" / "design-tokens.css").exists()
            assert (project / "src" / "styles" / "tailwind.config.js").exists()
            assert (project / "src" / "styles" / "design-tokens.json").exists()

    def test_apply_updates_astro_config(self):
        """Test that apply adds import to astro.config.mjs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test-project"
            project.mkdir()
            self.create_minimal_astro_project(project)

            import shutil
            shutil.copytree(self.FIXTURE_DIR, project / "fixtures" / "rohaki")

            result = self.run_apply(project)
            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Check astro.config.mjs updated
            astro_config = (project / "astro.config.mjs").read_text()
            assert "import './src/styles/design-tokens.css';" in astro_config

    def test_apply_updates_global_css(self):
        """Test that apply adds import to global.css."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test-project"
            project.mkdir()
            self.create_minimal_astro_project(project)

            import shutil
            shutil.copytree(self.FIXTURE_DIR, project / "fixtures" / "rohaki")

            result = self.run_apply(project)
            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Check global.css updated
            global_css = (project / "src" / "styles" / "global.css").read_text()
            assert "@import './design-tokens.css';" in global_css

    def test_apply_idempotent(self):
        """Test that running apply twice doesn't duplicate imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test-project"
            project.mkdir()
            self.create_minimal_astro_project(project)

            import shutil
            shutil.copytree(self.FIXTURE_DIR, project / "fixtures" / "rohaki")

            # Run apply first time
            result1 = self.run_apply(project)
            assert result1.returncode == 0

            # Run apply second time
            result2 = self.run_apply(project)
            assert result2.returncode == 0

            # Check no duplicate imports
            astro_config = (project / "astro.config.mjs").read_text()
            import_count = astro_config.count("import './src/styles/design-tokens.css';")
            assert import_count == 1, f"Duplicate imports found: {import_count}"

            global_css = (project / "src" / "styles" / "global.css").read_text()
            import_count = global_css.count("@import './design-tokens.css';")
            assert import_count == 1, f"Duplicate imports in global.css: {import_count}"

    def test_apply_with_existing_tailwind(self):
        """Test apply works with existing tailwind.config.js."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "test-project"
            project.mkdir()
            self.create_minimal_astro_project(project)

            import shutil
            shutil.copytree(self.FIXTURE_DIR, project / "fixtures" / "rohaki")

            # Create existing tailwind.config.js
            (project / "tailwind.config.js").write_text("""export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: { extend: {} },
  plugins: [],
};
""")

            result = self.run_apply(project)
            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Check design tokens still generated
            assert (project / "src" / "styles" / "design-tokens.css").exists()
            assert (project / "src" / "styles" / "tailwind.config.js").exists()

            # Check astro config updated
            astro_config = (project / "astro.config.mjs").read_text()
            assert "import './src/styles/design-tokens.css';" in astro_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])