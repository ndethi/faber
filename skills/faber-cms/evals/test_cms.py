#!/usr/bin/env python3
"""
Eval tests for faber-cms skill - Iteration A.

Tests that the skill correctly generates:
- Cloudflare Worker project structure
- D1 schema & migrations
- TypeScript types and routes
- wrangler.toml with D1 binding
- Cloudflare Access middleware
- CI/CD workflow
"""

import json
import hashlib
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCMSGeneration:
    """Test CMS Worker generation (Iteration A)."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "generate_cms.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()

    def run_generate(self, output_dir: Path = None, **kwargs) -> subprocess.CompletedProcess:
        """Run the generate command."""
        if output_dir is None:
            output_dir = self.output_dir

        cmd = [
            "python", str(self.SCRIPT),
            "--project-name", kwargs.get("project_name", "test-cms"),
            "--output-dir", str(output_dir),
            "--production-domain", kwargs.get("production_domain", "cms.test.example.com"),
            "--staging-domain", kwargs.get("staging_domain", "dev-cms.test.example.com"),
            "--cf-access-emails", kwargs.get("cf_access_emails", "admin@test.com"),
            "--cf-access-groups", kwargs.get("cf_access_groups", ""),
            "--content-types", json.dumps(kwargs.get("content_types", [
                {
                    "name": "page",
                    "displayName": "Page",
                    "fields": [
                        {"name": "slug", "type": "string", "required": True, "unique": True},
                        {"name": "title", "type": "string", "required": True},
                        {"name": "content", "type": "markdown", "required": True},
                        {"name": "published", "type": "boolean", "default": False}
                    ]
                }
            ]))
        ]
        if "content_types_file" in kwargs:
            cmd.extend(["--content-types-file", kwargs["content_types_file"]])
        project_root = self.SKILL_DIR.parent.parent
        return subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    def test_generates_worker_structure(self):
        """Test that Worker project structure is created."""
        result = self.run_generate()
        assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"

        # Core Worker files
        assert (self.output_dir / "worker" / "src" / "index.ts").exists()
        assert (self.output_dir / "worker" / "src" / "types.ts").exists()
        assert (self.output_dir / "worker" / "package.json").exists()
        assert (self.output_dir / "worker" / "tsconfig.json").exists()
        assert (self.output_dir / "worker" / "wrangler.toml").exists()

        # D1 schema
        assert (self.output_dir / "worker" / "src" / "db" / "schema.sql").exists()
        assert (self.output_dir / "worker" / "src" / "db" / "migrations" / "0001_initial.sql").exists()

        # Middleware & routes
        assert (self.output_dir / "worker" / "src" / "middleware" / "cf-access.ts").exists()
        assert (self.output_dir / "worker" / "src" / "routes" / "content.ts").exists()
        assert (self.output_dir / "worker" / "src" / "routes" / "collections.ts").exists()
        assert (self.output_dir / "worker" / "src" / "routes" / "health.ts").exists()

        # CI/CD
        assert (self.output_dir / "worker" / ".github" / "workflows" / "deploy.yml").exists()

    def test_package_json_structure(self):
        """Test package.json has correct dependencies."""
        result = self.run_generate()
        assert result.returncode == 0

        pkg = json.loads((self.output_dir / "worker" / "package.json").read_text())

        assert pkg["name"] == "test-cms"
        assert pkg["private"] is True
        assert "hono" in pkg["dependencies"]
        assert "drizzle-orm" in pkg["dependencies"]
        assert "zod" in pkg["dependencies"]
        assert "wrangler" in pkg["devDependencies"]
        assert "typescript" in pkg["devDependencies"]
        assert "vitest" in pkg["devDependencies"]

    def test_wrangler_toml_has_d1_binding(self):
        """Test wrangler.toml has D1 database binding."""
        self.run_generate()
        content = (self.output_dir / "worker" / "wrangler.toml").read_text()

        assert '[[d1_databases]]' in content
        assert 'binding = "DB"' in content
        assert 'database_name = "test-cms-db"' in content
        assert '[[kv_namespaces]]' in content
        assert 'binding = "SESSIONS"' in content
        assert "CF_ACCESS_TEAM_DOMAIN" in content

    def test_typescript_types_generated(self):
        """Test types.ts has Zod schemas for content types."""
        self.run_generate()
        content = (self.output_dir / "worker" / "src" / "types.ts").read_text()

        assert "pageSchema" in content
        assert "z.object" in content
        assert "z.string()" in content
        assert "z.boolean()" in content
        assert "export type Page" in content

    def test_d1_schema_has_required_tables(self):
        """Test D1 schema includes content, collections, versions tables."""
        self.run_generate()
        schema = (self.output_dir / "worker" / "src" / "db" / "schema.sql").read_text()

        # Core tables
        assert "CREATE TABLE IF NOT EXISTS collections" in schema
        assert "CREATE TABLE IF NOT EXISTS content_versions" in schema
        assert "CREATE TABLE IF NOT EXISTS content_page" in schema

        # Indexes
        assert "CREATE INDEX IF NOT EXISTS idx_content_page_collection" in schema
        assert "CREATE INDEX IF NOT EXISTS idx_content_page_status" in schema
        assert "CREATE INDEX IF NOT EXISTS idx_content_page_slug" in schema

        # Unified view
        assert "CREATE VIEW IF NOT EXISTS content_items" in schema

    def test_migration_file_generated(self):
        """Test initial migration file is generated."""
        self.run_generate()
        migration = (self.output_dir / "worker" / "src" / "db" / "migrations" / "0001_initial.sql").read_text()

        assert "0001_initial_schema" in migration
        assert "CREATE TABLE IF NOT EXISTS collections" in migration
        assert "CREATE TABLE IF NOT EXISTS content_page" in migration

    def test_cf_access_middleware(self):
        """Test Cloudflare Access middleware is generated."""
        self.run_generate()
        middleware = (self.output_dir / "worker" / "src" / "middleware" / "cf-access.ts").read_text()

        assert "cfAccessMiddleware" in middleware
        assert "CF-Access-Jwt-Assertion" in middleware
        assert "verify" in middleware
        assert "jwksUrl" in middleware or "cdn-cgi/access/certs" in middleware

    def test_content_routes_crud(self):
        """Test content routes have CRUD endpoints."""
        self.run_generate()
        routes = (self.output_dir / "worker" / "src" / "routes" / "content.ts").read_text()

        # CRUD operations
        assert 'contentRoutes.get("/"' in routes  # List
        assert 'contentRoutes.get("/:id"' in routes  # Get one
        assert 'contentRoutes.post("/"' in routes  # Create
        assert 'contentRoutes.put("/:id"' in routes  # Update
        assert 'contentRoutes.delete("/:id"' in routes  # Delete

        # Validation
        assert "zValidator" in routes
        assert "createSchema" in routes
        assert "updateSchema" in routes

    def test_collections_routes(self):
        """Test collections management routes."""
        self.run_generate()
        routes = (self.output_dir / "worker" / "src" / "routes" / "collections.ts").read_text()

        assert 'collectionsRoutes.get("/"' in routes
        assert 'collectionsRoutes.get("/:name"' in routes
        assert 'collectionsRoutes.post("/"' in routes
        assert "createCollectionSchema" in routes

    def test_health_routes(self):
        """Test health check endpoint."""
        self.run_generate()
        routes = (self.output_dir / "worker" / "src" / "routes" / "health.ts").read_text()

        assert "healthRoutes" in routes
        assert "SELECT 1" in routes
        assert '"healthy"' in routes
        assert '"unhealthy"' in routes

    def test_main_index_imports(self):
        """Test main index.ts imports all routes and middleware."""
        self.run_generate()
        index = (self.output_dir / "worker" / "src" / "index.ts").read_text()

        assert "cfAccessMiddleware" in index
        assert "contentRoutes" in index
        assert "collectionsRoutes" in index
        assert "healthRoutes" in index
        assert "app.use" in index
        assert "app.route" in index

    def test_ci_workflow_has_staging_and_production(self):
        """Test CI/CD workflow has separate staging/production jobs."""
        self.run_generate()
        workflow = (self.output_dir / "worker" / ".github" / "workflows" / "deploy.yml").read_text()

        assert "deploy-staging:" in workflow
        assert "deploy-production:" in workflow
        assert "github.ref == 'refs/heads/dev'" in workflow
        assert "github.ref == 'refs/heads/main'" in workflow
        assert "cloudflare/pages-action@v1" in workflow

    def test_custom_domains_used(self):
        """Test custom domains are used in generated files."""
        result = self.run_generate(
            production_domain="cms.custom.com",
            staging_domain="staging.custom.com"
        )
        assert result.returncode == 0

        # Check wrangler.toml
        wrangler = (self.output_dir / "worker" / "wrangler.toml").read_text()
        assert "cms.custom.com" in wrangler
        assert "staging.custom.com" in wrangler

        # Check CI workflow
        workflow = (self.output_dir / "worker" / ".github" / "workflows" / "deploy.yml").read_text()
        assert "cms.custom.com" in workflow
        assert "staging.custom.com" in workflow

    def test_cf_access_config(self):
        """Test Cloudflare Access emails/groups are configured."""
        result = self.run_generate(
            cf_access_emails="admin@example.com,editor@example.com",
            cf_access_groups="content-editors,admins"
        )
        assert result.returncode == 0

        wrangler = (self.output_dir / "worker" / "wrangler.toml").read_text()
        assert "admin@example.com" in wrangler
        assert "editor@example.com" in wrangler
        assert "content-editors" in wrangler
        assert "admins" in wrangler

    def test_multiple_content_types(self):
        """Test generation with multiple content types."""
        result = self.run_generate(content_types=[
            {
                "name": "page",
                "displayName": "Page",
                "fields": [
                    {"name": "slug", "type": "string", "required": True, "unique": True},
                    {"name": "title", "type": "string", "required": True},
                    {"name": "content", "type": "markdown", "required": True},
                ]
            },
            {
                "name": "post",
                "displayName": "Blog Post",
                "fields": [
                    {"name": "slug", "type": "string", "required": True, "unique": True},
                    {"name": "title", "type": "string", "required": True},
                    {"name": "excerpt", "type": "string", "required": False},
                    {"name": "content", "type": "markdown", "required": True},
                    {"name": "tags", "type": "array", "items": {"type": "string"}},
                ]
            }
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Check types for both content types
        types = (self.output_dir / "worker" / "src" / "types.ts").read_text()
        assert "pageSchema" in types
        assert "postSchema" in types
        assert "type Page" in types
        assert "type Post" in types

        # Check schema has both tables
        schema = (self.output_dir / "worker" / "src" / "db" / "schema.sql").read_text()
        assert "CREATE TABLE IF NOT EXISTS content_page" in schema
        assert "CREATE TABLE IF NOT EXISTS content_post" in schema

        # Check content routes handle both
        routes = (self.output_dir / "worker" / "src" / "routes" / "content.ts").read_text()
        assert "{collection}" in routes

    def test_determinism(self):
        """Test same input produces identical output."""
        import hashlib

        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1) / "out"
            out2 = Path(d2) / "out"

            result1 = self.run_generate(output_dir=out1)
            assert result1.returncode == 0

            result2 = self.run_generate(output_dir=out2)
            assert result2.returncode == 0

            # Compare key files
            for fname in ["worker/src/index.ts", "worker/wrangler.toml", "worker/package.json",
                          "worker/src/db/schema.sql", "worker/src/routes/content.ts"]:
                hash1 = hashlib.sha256((out1 / fname).read_bytes()).hexdigest()
                hash2 = hashlib.sha256((out2 / fname).read_bytes()).hexdigest()
                assert hash1 == hash2, f"{fname} not deterministic: {hash1} != {hash2}"

    def test_content_types_file_input(self):
        """Test reading content types from file."""
        ct_data = [
            {
                "name": "product",
                "displayName": "Product",
                "fields": [
                    {"name": "sku", "type": "string", "required": True, "unique": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "price", "type": "number", "required": True},
                ]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(ct_data, f)
            ct_file = f.name

        try:
            result = self.run_generate(content_types_file=ct_file)
            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Check product type generated
            types = (self.output_dir / "worker" / "src" / "types.ts").read_text()
            assert "productSchema" in types
            assert "type Product" in types

            schema = (self.output_dir / "worker" / "src" / "db" / "schema.sql").read_text()
            assert "CREATE TABLE IF NOT EXISTS content_product" in schema
        finally:
            Path(ct_file).unlink()


class TestDeterminism:
    """Test deterministic output from CMS generator."""

    SKILL_DIR = Path(__file__).parent.parent
    SCRIPT = SKILL_DIR / "scripts" / "generate_cms.py"
    FIXTURE_DIR = SKILL_DIR.parent.parent / "fixtures" / "rohaki"

    def run_generate(self, output_dir: Path, **kwargs) -> subprocess.CompletedProcess:
        cmd = [
            "python", str(self.SCRIPT),
            "--project-name", kwargs.get("project_name", "test-cms"),
            "--output-dir", str(output_dir),
            "--production-domain", kwargs.get("production_domain", "test.example.com"),
            "--staging-domain", kwargs.get("staging_domain", "dev.test.example.com"),
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
            for fname in ["worker/src/index.ts", "worker/wrangler.toml", "worker/package.json",
                          "worker/src/db/schema.sql", "worker/src/routes/content.ts"]:
                hash1 = hashlib.sha256((out1 / fname).read_bytes()).hexdigest()
                hash2 = hashlib.sha256((out2 / fname).read_bytes()).hexdigest()
                assert hash1 == hash2, f"{fname} not deterministic: {hash1} != {hash2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])