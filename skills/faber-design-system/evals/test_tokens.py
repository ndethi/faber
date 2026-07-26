#!/usr/bin/env python3
"""
Tests for faber-design-system skill - token generation.

Verifies that the skill correctly generates design system assets from fixtures.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestDesignSystemGeneration:
    """Test design token generation from fixtures."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "design_system.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()

    def run_generate(self, fixture: str = "rohaki", format: str = "all", output_dir: Path = None, fixtures_dir: str = None) -> subprocess.CompletedProcess:
        """Run the design_system.py generate command."""
        if output_dir is None:
            output_dir = self.output_dir

        if fixtures_dir is None:
            fixtures_dir = str(self.FIXTURE_DIR.parent)

        cmd = [
            "python", str(self.SCRIPT),
            "generate",
            "--fixture", fixture,
            "--output-dir", str(output_dir),
            "--format", format,
            "--fixtures-dir", fixtures_dir
        ]
        project_root = self.SKILL_DIR.parent.parent
        return subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    def test_generate_css(self):
        """Test generating only CSS."""
        result = self.run_generate(format="css")
        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        assert (self.output_dir / "design-tokens.css").exists()

    def test_generate_tailwind(self):
        """Test generating only Tailwind config."""
        result = self.run_generate(format="tailwind")
        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        assert (self.output_dir / "tailwind.config.js").exists()

    def test_generate_json(self):
        """Test generating only JSON."""
        result = self.run_generate(format="json")
        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        assert (self.output_dir / "design-tokens.json").exists()

    def test_generate_all_formats(self):
        """Test generating all formats at once."""
        result = self.run_generate(format="all")
        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        assert (self.output_dir / "design-tokens.css").exists()
        assert (self.output_dir / "tailwind.config.js").exists()
        assert (self.output_dir / "design-tokens.json").exists()

    def test_css_contains_expected_variables(self):
        """Test that CSS output contains expected custom properties."""
        self.run_generate(format="css")
        css_content = (self.output_dir / "design-tokens.css").read_text()

        # Check brand colors - note the path includes "brand" in the token name
        assert "--rohaki-color-brand-bamboo-500:" in css_content
        assert "--rohaki-color-brand-bamboo-700:" in css_content
        assert "--rohaki-color-brand-sage-500:" in css_content
        assert "--rohaki-color-brand-earth-500:" in css_content

        # Check semantic colors
        assert "--rohaki-color-semantic-primary-DEFAULT:" in css_content
        assert "--rohaki-color-semantic-secondary-DEFAULT:" in css_content
        assert "--rohaki-color-semantic-accent-DEFAULT:" in css_content

        # Check gradients
        assert "--rohaki-color-gradients-brand-primary:" in css_content
        assert "--rohaki-color-gradients-hero:" in css_content
        assert "--rohaki-color-gradients-stats:" in css_content

        # Check spacing
        assert "--rohaki-spacing-space-4:" in css_content
        assert "--rohaki-spacing-space-8:" in css_content

        # Check typography
        assert "--rohaki-typography-fontFamilies-sans:" in css_content
        assert "--rohaki-typography-fontFamilies-display:" in css_content

        # Check shadows
        assert "--rohaki-shadow-brand:" in css_content

        # Check animation
        assert "--rohaki-animation-duration-normal:" in css_content
        assert "--rohaki-animation-easing-easeOut:" in css_content

        # Check z-index
        assert "--rohaki-zIndex-modal:" in css_content

    def test_css_contains_component_utilities(self):
        """Test that CSS output contains component utility classes."""
        self.run_generate(format="css")
        css_content = (self.output_dir / "design-tokens.css").read_text()

        # Card utilities
        assert ".rohaki-card" in css_content
        assert ".rohaki-card:hover" in css_content
        assert ".rohaki-card-stats" in css_content
        assert ".rohaki-card-glass" in css_content

        # Button utilities
        assert ".rohaki-btn" in css_content
        assert ".rohaki-btn-primary" in css_content
        assert ".rohaki-btn-secondary" in css_content
        assert ".rohaki-btn-outline" in css_content
        assert ".rohaki-btn-ghost" in css_content
        assert ".rohaki-btn-stats" in css_content

        # Badge utilities
        assert ".rohaki-badge" in css_content
        assert ".rohaki-badge-default" in css_content
        assert ".rohaki-badge-success" in css_content

        # Grid utilities
        assert ".rohaki-grid-cards" in css_content
        assert ".rohaki-grid-stats" in css_content
        assert ".rohaki-grid-features" in css_content

        # Section utilities
        assert ".rohaki-section" in css_content
        assert ".rohaki-section-hero" in css_content
        assert ".rohaki-section-stats" in css_content

        # Typography utilities
        assert ".rohaki-heading" in css_content
        assert ".rohaki-h1" in css_content
        assert ".rohaki-h2" in css_content
        assert ".rohaki-body" in css_content
        assert ".rohaki-stat-value" in css_content
        assert ".rohaki-stat-label" in css_content

    def test_tailwind_config_structure(self):
        """Test that Tailwind config has correct structure."""
        self.run_generate(format="tailwind")
        tw_content = (self.output_dir / "tailwind.config.js").read_text()

        # Check imports
        assert "import defaultConfig" in tw_content
        assert "@faber/tailwind-config/default" in tw_content

        # Check theme.extend
        assert "theme:" in tw_content
        assert "extend:" in tw_content

        # Check colors - should have resolved values not template references
        assert "#22c55e" in tw_content  # bamboo-500 resolved
        assert "#15803d" in tw_content  # bamboo-700 resolved
        assert "#4ade80" in tw_content  # sage-500 resolved
        assert "#c98b4a" in tw_content  # earth-500 resolved

        # Check spacing
        assert "spacing:" in tw_content

        # Check typography
        assert "fontFamily:" in tw_content
        assert "fontSize:" in tw_content

        # Check shadows
        assert "boxShadow:" in tw_content

        # Check animation
        assert "transitionDuration:" in tw_content
        assert "transitionTimingFunction:" in tw_content

        # Check z-index
        assert "zIndex:" in tw_content

        # Check background images
        assert "backgroundImage:" in tw_content
        assert "linear-gradient" in tw_content  # gradients should be resolved

    def test_json_output_valid_w3c_format(self):
        """Test that JSON output is valid W3C Design Tokens format."""
        self.run_generate(format="json")
        json_path = self.output_dir / "design-tokens.json"
        tokens = json.loads(json_path.read_text())

        # Check required top-level fields
        assert "tokens" in tokens
        assert tokens.get("format") == "design-tokens" or "$schema" in tokens

        # Check color tokens structure
        assert "color" in tokens["tokens"]
        assert "brand" in tokens["tokens"]["color"]
        assert "bamboo" in tokens["tokens"]["color"]["brand"]
        assert "500" in tokens["tokens"]["color"]["brand"]["bamboo"]

        bamboo_500 = tokens["tokens"]["color"]["brand"]["bamboo"]["500"]
        assert "value" in bamboo_500
        assert "type" in bamboo_500
        assert bamboo_500["type"] == "color"

        # Check spacing tokens
        assert "spacing" in tokens["tokens"]
        assert "space" in tokens["tokens"]["spacing"]

        # Check typography tokens
        assert "typography" in tokens["tokens"]
        assert "fontFamilies" in tokens["tokens"]["typography"]
        assert "fontSizes" in tokens["tokens"]["typography"]

        # Check component patterns
        assert "components" in tokens
        assert "card" in tokens["components"]
        assert "button" in tokens["components"]

    def test_determinism(self):
        """Test that same input produces identical output."""
        # First run
        result1 = self.run_generate(format="all")
        assert result1.returncode == 0

        css1 = (self.output_dir / "design-tokens.css").read_bytes()
        tw1 = (self.output_dir / "tailwind.config.js").read_bytes()
        json1 = (self.output_dir / "design-tokens.json").read_bytes()

        # Clean and run again
        shutil.rmtree(self.output_dir)
        self.output_dir.mkdir()

        result2 = self.run_generate(format="all")
        assert result2.returncode == 0

        css2 = (self.output_dir / "design-tokens.css").read_bytes()
        tw2 = (self.output_dir / "tailwind.config.js").read_bytes()
        json2 = (self.output_dir / "design-tokens.json").read_bytes()

        # Byte-for-byte comparison
        assert css1 == css2, "CSS output not deterministic"
        assert tw1 == tw2, "Tailwind output not deterministic"
        assert json1 == json2, "JSON output not deterministic"

    def test_unknown_fixture_fails(self):
        """Test that unknown fixture fails gracefully."""
        result = self.run_generate(fixture="nonexistent")
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()


class TestApplyCommand:
    """Test the apply command for integrating into Astro projects."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "design_system.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    def create_test_project(self, tmp_path: Path) -> Path:
        """Create a minimal Astro project structure."""
        project = tmp_path / "test-project"
        project.mkdir()

        # Standard Astro directories
        (project / "src" / "styles").mkdir(parents=True)
        (project / "src" / "pages").mkdir(parents=True)
        (project / "src" / "components").mkdir(parents=True)
        (project / "public").mkdir()

        # Minimal astro.config.mjs
        (project / "astro.config.mjs").write_text("""import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://example.com",
});
""")

        # Minimal global.css
        (project / "src" / "styles" / "global.css").write_text("/* Global styles */\n")

        # Fixtures directory with rohaki fixture
        fixtures_dir = project / "fixtures"
        fixtures_dir.mkdir()
        shutil.copytree(self.FIXTURE_DIR, fixtures_dir / "rohaki")

        return project

    def test_apply_to_astro_project(self, tmp_path):
        """Test applying design system to an Astro project."""
        project = self.create_test_project(tmp_path)

        cmd = [
            "python", str(self.SCRIPT),
            "apply",
            "--project-root", str(project),
            "--fixture", "rohaki",
            "--output-dir", "src/styles",
            "--fixtures-dir", "fixtures"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.SKILL_DIR.parent.parent)

        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        # Verify design tokens were generated
        assert (project / "src" / "styles" / "design-tokens.css").exists()
        assert (project / "src" / "styles" / "tailwind.config.js").exists()
        assert (project / "src" / "styles" / "design-tokens.json").exists()

        # Verify astro.config.mjs was updated
        astro_content = (project / "astro.config.mjs").read_text()
        assert "import './src/styles/design-tokens.css';" in astro_content

        # Verify global.css was updated
        global_content = (project / "src" / "styles" / "global.css").read_text()
        assert "@import './design-tokens.css';" in global_content


class TestComponentUtilities:
    """Test that component utilities are correctly generated."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "design_system.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()

    def run_generate(self, format: str = "css"):
        fixtures_dir = str(self.FIXTURE_DIR.parent)
        cmd = [
            "python", str(self.SCRIPT),
            "generate",
            "--fixture", "rohaki",
            "--output-dir", str(self.output_dir),
            "--format", format,
            "--fixtures-dir", fixtures_dir
        ]
        project_root = self.SKILL_DIR.parent.parent
        return subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    def test_card_utilities(self):
        """Test card component utilities."""
        result = self.run_generate(format="css")
        assert result.returncode == 0

        content = (self.output_dir / "design-tokens.css").read_text()

        # Base card
        assert ".rohaki-card {" in content
        assert "background: var(--rohaki-color-background-DEFAULT" in content
        assert "border: 1px solid var(--rohaki-color-border-DEFAULT" in content
        assert "border-radius: var(--rohaki-borderRadius-xl" in content
        assert "box-shadow: var(--rohaki-shadow-md" in content

        # Hover state
        assert ".rohaki-card:hover {" in content
        assert "transform: translateY(-4px)" in content
        assert "box-shadow: var(--rohaki-shadow-brand-lg" in content

        # Variants
        assert ".rohaki-card-elevated" in content
        assert ".rohaki-card-stats" in content
        assert ".rohaki-card-glass" in content

    def test_button_utilities(self):
        """Test button component utilities."""
        result = self.run_generate(format="css")
        assert result.returncode == 0

        content = (self.output_dir / "design-tokens.css").read_text()

        # Base button
        assert ".rohaki-btn {" in content
        assert "font-weight: var(--rohaki-font-semibold" in content
        assert "border-radius: var(--rohaki-borderRadius-lg" in content
        assert "display: inline-flex" in content

        # Sizes
        assert ".rohaki-btn-sm" in content
        assert ".rohaki-btn-md" in content
        assert ".rohaki-btn-lg" in content
        assert ".rohaki-btn-xl" in content

        # Variants
        assert ".rohaki-btn-primary" in content
        assert "background: var(--rohaki-gradient-brand-primary" in content
        assert ".rohaki-btn-secondary" in content
        assert ".rohaki-btn-outline" in content
        assert ".rohaki-btn-ghost" in content
        assert ".rohaki-btn-stats" in content

        # Primary hover/active
        assert ".rohaki-btn-primary:hover" in content
        assert ".rohaki-btn-primary:active" in content

    def test_badge_utilities(self):
        """Test badge component utilities."""
        result = self.run_generate(format="css")
        assert result.returncode == 0

        content = (self.output_dir / "design-tokens.css").read_text()

        assert ".rohaki-badge {" in content
        assert ".rohaki-badge-default" in content
        assert ".rohaki-badge-success" in content
        assert ".rohaki-badge-earth" in content
        assert ".rohaki-badge-stats" in content

    def test_grid_utilities(self):
        """Test grid utilities."""
        result = self.run_generate(format="css")
        assert result.returncode == 0

        content = (self.output_dir / "design-tokens.css").read_text()

        assert ".rohaki-grid-cards {" in content
        assert ".rohaki-grid-stats {" in content
        assert ".rohaki-grid-features {" in content

    def test_section_utilities(self):
        """Test section utilities."""
        result = self.run_generate(format="css")
        assert result.returncode == 0

        content = (self.output_dir / "design-tokens.css").read_text()

        assert ".rohaki-section {" in content
        assert ".rohaki-section-hero {" in content
        assert ".rohaki-section-stats {" in content
        assert ".rohaki-section-card-grid" in content
        assert ".rohaki-section-feature" in content
        assert ".rohaki-section-cta" in content

    def test_typography_utilities(self):
        """Test typography utilities."""
        result = self.run_generate(format="css")
        assert result.returncode == 0

        content = (self.output_dir / "design-tokens.css").read_text()

        assert ".rohaki-heading {" in content
        assert ".rohaki-h1" in content
        assert ".rohaki-h2" in content
        assert ".rohaki-body" in content
        assert ".rohaki-stat-value" in content
        assert ".rohaki-stat-label" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])