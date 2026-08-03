import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
SKILL_DIR = Path(__file__).parent.parent


def run_generate(output_dir: Path, config_path: Path, script: str) -> subprocess.CompletedProcess:
    """Run the generate script and return result."""
    return subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / script), "--config", str(config_path), "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def get_file_hash(filepath: Path) -> str:
    """Get SHA256 hash of file contents."""
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


class TestWorkerGeneration:
    """Tests for worker project generation."""

    def test_generate_worker_creates_expected_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0, f"Generation failed: {result.stderr}"

            # Check expected files exist
            expected_files = [
                "package.json",
                "tsconfig.json",
                "wrangler.toml",
                "schema.sql",
                "collections.json",
                "src/index.ts",
                "src/types.ts",
                "src/db/schema.ts",
                "src/db/index.ts",
                "src/db/zod-schemas.ts",
                "src/middleware/cf-access.ts",
                "src/routes/health.ts",
                "src/routes/collections.ts",
                "src/routes/content.ts",
                "src/routes/media.ts",
                "src/routes/settings.ts",
                "src/utils/crypto.ts",
                "src/utils/preview.ts",
                "migrations/0001_initial.sql",
            ]

            for f in expected_files:
                assert (output_dir / f).exists(), f"Missing file: {f}"

    def test_generate_worker_deterministic(self):
        """Two generations with same config produce byte-identical output."""
        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            output1 = Path(tmpdir1) / "worker"
            output2 = Path(tmpdir2) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result1 = run_generate(output1, config_path, "generate_worker.py")
            assert result1.returncode == 0

            result2 = run_generate(output2, config_path, "generate_worker.py")
            assert result2.returncode == 0

            # Compare key files
            key_files = [
                "package.json",
                "tsconfig.json",
                "wrangler.toml",
                "schema.sql",
                "collections.json",
                "src/index.ts",
                "src/types.ts",
                "src/db/schema.ts",
                "src/middleware/cf-access.ts",
            ]

            for f in key_files:
                hash1 = get_file_hash(output1 / f)
                hash2 = get_file_hash(output2 / f)
                assert hash1 == hash2, f"{f} not deterministic: {hash1} != {hash2}"

    def test_worker_typecheck_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            # Run typecheck
            typecheck_result = subprocess.run(
                ["npm", "run", "typecheck"],
                cwd=output_dir,
                capture_output=True,
                text=True,
            )
            assert typecheck_result.returncode == 0, f"Typecheck failed: {typecheck_result.stderr}"

    def test_worker_tests_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            # Run tests
            test_result = subprocess.run(
                ["npm", "test"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert test_result.returncode == 0, f"Tests failed: {test_result.stderr}"


class TestAdminGeneration:
    """Tests for admin UI project generation."""

    def test_generate_admin_creates_expected_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "admin"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_admin.py")
            assert result.returncode == 0, f"Generation failed: {result.stderr}"

            expected_files = [
                "astro.config.mjs",
                "package.json",
                "tsconfig.json",
                "tailwind.config.js",
                "src/layouts/BaseLayout.astro",
                "src/pages/admin/index.astro",
            ]

            for f in expected_files:
                assert (output_dir / f).exists(), f"Missing file: {f}"

    def test_generate_admin_deterministic(self):
        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            output1 = Path(tmpdir1) / "admin"
            output2 = Path(tmpdir2) / "admin"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result1 = run_generate(output1, config_path, "generate_admin.py")
            assert result1.returncode == 0

            result2 = run_generate(output2, config_path, "generate_admin.py")
            assert result2.returncode == 0

            key_files = [
                "astro.config.mjs",
                "package.json",
                "tsconfig.json",
                "tailwind.config.js",
                "src/layouts/BaseLayout.astro",
                "src/pages/admin/index.astro",
            ]

            for f in key_files:
                hash1 = get_file_hash(output1 / f)
                hash2 = get_file_hash(output2 / f)
                assert hash1 == hash2, f"{f} not deterministic: {hash1} != {hash2}"

    def test_admin_build_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "admin"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_admin.py")
            assert result.returncode == 0

            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert build_result.returncode == 0, f"Build failed: {build_result.stderr}"


class TestD1Schema:
    """Tests for D1 schema generation."""

    def test_schema_includes_all_content_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            schema_sql = (output_dir / "schema.sql").read_text()
            content_types = ["page", "post", "solution", "impact_metric"]

            for ct in content_types:
                assert f"content_{ct}" in schema_sql, f"Missing content_{ct} table in schema"

    def test_schema_has_required_indexes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            schema_sql = (output_dir / "schema.sql").read_text()
            assert "idx_content_page_collection" in schema_sql
            assert "idx_content_page_status" in schema_sql
            assert "uq_content_page_collection_slug" in schema_sql


class TestZodSchemas:
    """Tests for Zod schema generation."""

    def test_zod_schemas_generated_for_all_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            zod_file = output_dir / "src" / "db" / "zod-schemas.ts"
            content = zod_file.read_text()

            assert "pageSchema" in content
            assert "postSchema" in content
            assert "solutionSchema" in content
            assert "impact_metricSchema" in content

    def test_zod_schemas_have_correct_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            zod_file = output_dir / "src" / "db" / "zod-schemas.ts"
            content = zod_file.read_text()

            # Check page schema fields
            assert "title" in content
            assert "description" in content
            assert "heroImage" in content
            assert "ctaText" in content
            assert "ctaLink" in content
            assert "order" in content


class TestCollectionsConfig:
    """Tests for collections.json generation."""

    def test_collections_json_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "worker"
            config_path = SKILL_DIR / "config" / "defaults.yaml"

            result = run_generate(output_dir, config_path, "generate_worker.py")
            assert result.returncode == 0

            collections = json.loads((output_dir / "collections.json").read_text())

            assert "page" in collections
            assert "post" in collections
            assert "solution" in collections
            assert "impact_metric" in collections

            for name, config in collections.items():
                assert "name" in config
                assert "label" in config
                assert "schema" in config
                assert "uiConfig" in config


class TestConfigValidation:
    """Tests for config validation."""

    def test_defaults_yaml_valid(self):
        config_path = SKILL_DIR / "config" / "defaults.yaml"
        assert config_path.exists()

        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "contentTypes" in config
        assert len(config["contentTypes"]) == 4
        assert "cfAccess" in config
        assert "preview" in config
        assert "github" in config
        assert "media" in config
        assert "worker" in config


class TestSkillContract:
    """Tests for skill contract compliance."""

    def test_skill_md_exists(self):
        skill_md = SKILL_DIR / "SKILL.md"
        assert skill_md.exists()

        content = skill_md.read_text()
        assert "name: faber-cms" in content
        assert "version: 1.1.0" in content
        assert "scripts:" in content
        assert "evals:" in content

    def test_scripts_executable(self):
        scripts_dir = SKILL_DIR / "scripts"
        generate_worker = scripts_dir / "generate_worker.py"
        generate_admin = scripts_dir / "generate_admin.py"

        assert generate_worker.exists()
        assert generate_admin.exists()

        # Check they're executable
        assert os.access(generate_worker, os.X_OK)
        assert os.access(generate_admin, os.X_OK)

    def test_evals_directory_exists(self):
        evals_dir = SKILL_DIR / "evals"
        assert evals_dir.exists()
        assert evals_dir.is_dir()

    def test_config_directory_exists(self):
        config_dir = SKILL_DIR / "config"
        assert config_dir.exists()
        assert (config_dir / "defaults.yaml").exists()