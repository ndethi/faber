#!/usr/bin/env python3
"""
Eval tests for faber-splash skill.

Tests that the skill correctly generates a complete Faber splash page project.
"""

import json
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestSplashGeneration:
    """Test splash page project generation."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "generate_splash.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()
        self.fixtures_dir = self.FIXTURE_DIR.parent

    def run_generate(self, output_dir: Path = None, **kwargs) -> subprocess.CompletedProcess:
        """Run the generate command."""
        if output_dir is None:
            output_dir = self.output_dir

        cmd = [
            "python", str(self.SCRIPT),
            "--project-name", kwargs.get("project_name", "test-splash"),
            "--output-dir", str(output_dir),
            "--fixture", kwargs.get("fixture", "faber-brand"),
            "--production-domain", kwargs.get("production_domain", "test.example.com"),
            "--staging-domain", kwargs.get("staging_domain", "dev.test.example.com"),
            "--intent-wizard-url", kwargs.get("intent_wizard_url", "/intent"),
            "--rohaki-url", kwargs.get("rohaki_url", "https://rohaki.example.com"),
            "--github-repo", kwargs.get("github_repo", "test/repo"),
            "--fixtures-dir", str(self.fixtures_dir)
        ]
        project_root = self.SKILL_DIR.parent.parent
        return subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    def test_generate_creates_astro_structure(self):
        """Test that generate creates complete Astro project structure."""
        result = self.run_generate()
        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        # Check key files exist
        assert (self.output_dir / "package.json").exists()
        assert (self.output_dir / "astro.config.mjs").exists()
        assert (self.output_dir / "wrangler.toml").exists()
        assert (self.output_dir / "tsconfig.json").exists()
        assert (self.output_dir / "eslint.config.js").exists()
        assert (self.output_dir / ".prettierrc").exists()
        assert (self.output_dir / ".gitignore").exists()

        # Check source structure
        assert (self.output_dir / "src" / "pages" / "index.astro").exists()
        assert (self.output_dir / "src" / "layouts" / "BaseLayout.astro").exists()
        assert (self.output_dir / "src" / "components" / "LoopDiagram.astro").exists()
        assert (self.output_dir / "src" / "components" / "DeployReceipts.astro").exists()
        assert (self.output_dir / "src" / "styles" / "global.css").exists()
        assert (self.output_dir / "src" / "styles" / "design-tokens.css").exists()

        # Check CI/CD
        assert (self.output_dir / ".github" / "workflows" / "deploy.yml").exists()

    def test_package_json_structure(self):
        """Test package.json has correct structure."""
        result = self.run_generate()
        assert result.returncode == 0

        pkg = json.loads((self.output_dir / "package.json").read_text())
        assert pkg["name"] == "test-splash"
        assert pkg["version"] == "0.1.0"
        assert pkg["private"] is True
        assert pkg["type"] == "module"
        assert "dev" in pkg["scripts"]
        assert "build" in pkg["scripts"]
        assert "preview" in pkg["scripts"]
        assert "lint" in pkg["scripts"]
        assert "format" in pkg["scripts"]
        assert "test" in pkg["scripts"]
        assert "astro" in pkg["dependencies"]
        assert "@astrojs/check" in pkg["devDependencies"]
        assert "@cloudflare/astro-integration" in pkg["devDependencies"]
        assert "eslint" in pkg["devDependencies"]
        assert "prettier" in pkg["devDependencies"]
        assert "prettier-plugin-astro" in pkg["devDependencies"]
        assert "typescript" in pkg["devDependencies"]
        assert "vitest" in pkg["devDependencies"]
        assert "wrangler" in pkg["devDependencies"]

    def test_astro_config_structure(self):
        """Test astro.config.mjs has Cloudflare adapter."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / "astro.config.mjs").read_text()
        assert "import { defineConfig }" in content
        assert "import cloudflare" in content
        assert "integrations: [cloudflare()]" in content
        assert "output: \"static\"" in content
        assert "adapter: cloudflare" in content
        assert "test.example.com" in content

    def test_wrangler_toml_structure(self):
        """Test wrangler.toml has production + staging targets."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / "wrangler.toml").read_text()
        assert 'name = "test-splash"' in content
        assert 'compatibility_date = "2024-01-01"' in content
        assert 'pages_build_output_dir = "./dist"' in content
        assert "test.example.com" in content
        assert "dev.test.example.com" in content

    def test_index_astro_has_three_scrolls(self):
        """Test index.astro has three scroll sections + CTA."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / "src" / "pages" / "index.astro").read_text()
        # Scroll 1: What Faber Is
        assert "What Faber Is" in content
        assert "id=\"what-is-faber\"" in content
        assert "Spec as Single Source of Truth" in content
        assert "Process-Level Drift Control" in content
        assert "Closed Feedback Loop" in content
        assert "Governed Self-Extension" in content
        assert "rohaki-grid-features" in content

        # Scroll 2: What Shipped
        assert "What Shipped" in content
        assert "id=\"what-shipped\"" in content
        assert "Rohaki ESG Bamboo Supply Chain" in content
        assert "Faber Launch Splash" in content
        assert "rohaki-grid-cards" in content

        # Scroll 3: The Loop
        assert "The Loop" in content
        assert "id=\"the-loop\"" in content
        assert "LoopDiagram" in content
        assert "DeployReceipts" in content

        # CTA Section
        assert "id=\"cta\"" in content or "cta" in content.lower()
        assert "Start a Project" in content
        assert "intent" in content.lower()

    def test_base_layout_imports_design_tokens(self):
        """Test BaseLayout.astro imports design tokens."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / "src" / "layouts" / "BaseLayout.astro").read_text()
        assert "@import './styles/design-tokens.css';" in content
        assert "scroll-behavior: smooth" in content

    def test_loop_diagram_component(self):
        """Test LoopDiagram.astro component exists and has required structure."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / "src" / "components" / "LoopDiagram.astro").read_text()
        assert "PR → CI → Deploy Loop" in content
        assert "loop-stages" in content
        assert "loop-stage" in content
        assert "loop-timeline" in content
        assert "fetchRecentPRs" in content
        assert "github.com/repos" in content

    def test_deploy_receipts_component(self):
        """Test DeployReceipts.astro component exists and has required structure."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / "src" / "components" / "DeployReceipts.astro").read_text()
        assert "Deploy Receipts" in content
        assert "receipts-list" in content
        assert "Cloudflare Pages" in content
        assert "receipt-item" in content
        assert "receipt-status" in content
        assert "status-success" in content
        assert "status-failed" in content

    def test_ci_workflow_has_three_jobs(self):
        """Test deploy.yml has lint-and-test, deploy-staging, deploy-production jobs."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / ".github" / "workflows" / "deploy.yml").read_text()
        assert "lint-and-test:" in content
        assert "deploy-staging:" in content
        assert "deploy-production:" in content
        assert "cloudflare/pages-action@v1" in content
        assert "CLOUDFLARE_API_TOKEN" in content
        assert "CLOUDFLARE_ACCOUNT_ID" in content

    def test_gitignore_covers_essentials(self):
        """Test .gitignore covers node_modules, dist, .env, etc."""
        result = self.run_generate()
        assert result.returncode == 0

        content = (self.output_dir / ".gitignore").read_text()
        assert "node_modules/" in content
        assert "dist/" in content
        assert ".env" in content
        assert ".vscode/" in content
        assert ".DS_Store" in content

    def test_design_tokens_invoke(self):
        """Test that design system is invoked (placeholder check)."""
        result = self.run_generate()
        assert result.returncode == 0

        # design-tokens.css exists (either generated or placeholder)
        assert (self.output_dir / "src" / "styles" / "design-tokens.css").exists()

    def test_custom_domains(self):
        """Test custom production/staging domains are used."""
        result = self.run_generate(
            production_domain="custom.example.com",
            staging_domain="staging.custom.example.com"
        )
        assert result.returncode == 0

        # Check astro config
        astro_config = (self.output_dir / "astro.config.mjs").read_text()
        assert "custom.example.com" in astro_config

        # Check CI workflow
        workflow = (self.output_dir / ".github" / "workflows" / "deploy.yml").read_text()
        assert "custom.example.com" in workflow
        assert "staging.custom.example.com" in workflow


class TestSplashDeterminism:
    """Test deterministic output from splash generator."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "generate_splash.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    def run_generate(self, output_dir: Path, **kwargs) -> subprocess.CompletedProcess:
        cmd = [
            "python", str(self.SCRIPT),
            "--project-name", kwargs.get("project_name", "test-splash"),
            "--output-dir", str(output_dir),
            "--fixture", kwargs.get("fixture", "faber-brand"),
            "--production-domain", kwargs.get("production_domain", "test.example.com"),
            "--staging-domain", kwargs.get("staging_domain", "dev.test.example.com"),
            "--fixtures-dir", str(self.FIXTURE_DIR.parent)
        ]
        project_root = self.SKILL_DIR.parent.parent
        return subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    def test_css_deterministic(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1) / "out"
            out2 = Path(d2) / "out"

            result1 = self.run_generate(out1)
            assert result1.returncode == 0

            result2 = self.run_generate(out2)
            assert result2.returncode == 0

            # Compare key files
            for fname in ["package.json", "astro.config.mjs", "wrangler.toml", "src/pages/index.astro"]:
                hash1 = hashlib.sha256((out1 / fname).read_bytes()).hexdigest()
                hash2 = hashlib.sha256((out2 / fname).read_bytes()).hexdigest()
                assert hash1 == hash2, f"{fname} not deterministic: {hash1} != {hash2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])