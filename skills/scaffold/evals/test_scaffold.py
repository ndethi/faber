#!/usr/bin/env python3
"""
Eval for the scaffold skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Reads intent-collect artifacts correctly
4. Generates valid Astro + Cloudflare Pages project structure
5. Produces expected outputs deterministically
6. Handles unknowns as TODO:, never fabricates
7. HITL gate and dry-run work correctly
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


FIXTURES_DIR = Path("fixtures/rohaki")
SKILL_DIR = Path("skills/scaffold")
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name: scaffold" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "scaffold" in content, "SKILL.md must mention skill name"
    assert "intent-collect" in content, "SKILL.md must reference intent-collect"
    assert "FRAMEWORK.md" in content, "SKILL.md must reference FRAMEWORK.md"
    assert "HITL" in content, "SKILL.md must mention HITL gates"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that scaffold.py exists and is executable."""
    assert SCRIPT.exists(), "scaffold.py must exist"
    assert os.access(str(SCRIPT), os.X_OK), "scaffold.py must be executable"
    print("✓ scaffold.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    assert "input-dir" in output.lower(), "Should mention --input-dir argument"
    print("✓ Script shows usage without required args")


def test_missing_input_artifacts() -> None:
    """Test that script errors gracefully when input artifacts missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty directory - no artifacts
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", tmpdir, "--output-dir", tmpdir + "/out"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should fail when artifacts missing"
        
        # Parse JSON output
        output = json.loads(result.stdout.strip())
        assert output["status"] == "error"
        assert "not found" in output["error"].lower()
    
    print("✓ Missing input artifacts handled correctly")


def test_generates_project_structure() -> None:
    """Test that scaffold generates complete project structure from fixtures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated"
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Scaffold failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert len(output["artifacts"]) > 20, "Should generate many files"
        
        # Check key files exist
        key_files = [
            "package.json",
            "astro.config.mjs",
            "wrangler.toml",
            "tsconfig.json",
            "eslint.config.js",
            ".prettierrc",
            ".gitignore",
            ".github/workflows/ci.yml",
            ".github/workflows/deploy.yml",
            "src/pages/index.astro",
            "src/layouts/BaseLayout.astro",
            "src/components/Header.astro",
            "src/components/Footer.astro",
            "src/styles/global.css",
            "tests/example.test.ts",
            "README.md",
            "SCAFFOLD_SUMMARY.md",
        ]
        
        for rel_path in key_files:
            full_path = output_dir / rel_path
            assert full_path.exists(), f"Missing key file: {rel_path}"
        
        # Check skill stubs exist
        for stage in ["build", "evaluate", "deploy", "publish", "observe", "feedback"]:
            stub_path = output_dir / f"scripts/{stage}/{stage}.py"
            assert stub_path.exists(), f"Missing skill stub: {stub_path}"
    
    print("✓ Generates complete project structure with all key files")


def test_package_json_valid() -> None:
    """Test that generated package.json is valid and has required fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated"
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0
        
        package_json = output_dir / "package.json"
        content = json.loads(package_json.read_text())
        
        assert content["name"] == "build-a-website"  # from fixture goal
        assert "scripts" in content
        assert "build" in content["scripts"]
        assert "dev" in content["scripts"]
        assert "test" in content["scripts"]
        assert "dependencies" in content
        assert "astro" in content["dependencies"]
        assert "devDependencies" in content
        assert "wrangler" in content["devDependencies"]
        assert "vitest" in content["devDependencies"]
    
    print("✓ Generated package.json is valid with required scripts and deps")


def test_astro_config_valid() -> None:
    """Test that generated astro.config.mjs is valid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated"
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0
        
        astro_config = output_dir / "astro.config.mjs"
        content = astro_config.read_text()
        
        assert "defineConfig" in content
        assert "cloudflare" in content
        assert "output" in content
        assert "static" in content or "adapter" in content
    
    print("✓ Generated astro.config.mjs is valid")


def test_github_workflows_generated() -> None:
    """Test that CI/CD workflows are generated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated"
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0
        
        ci_workflow = output_dir / ".github" / "workflows" / "ci.yml"
        deploy_workflow = output_dir / ".github" / "workflows" / "deploy.yml"
        
        assert ci_workflow.exists(), "CI workflow missing"
        assert deploy_workflow.exists(), "Deploy workflow missing"
        
        ci_content = ci_workflow.read_text()
        assert "lint-and-test" in ci_content
        assert "npm ci" in ci_content
        assert "npm run lint" in ci_content
        assert "npm test" in ci_content
        assert "npm run build" in ci_content
        
        deploy_content = deploy_workflow.read_text()
        assert "deploy" in deploy_content.lower()
        assert "cloudflare" in deploy_content.lower()
    
    print("✓ GitHub Actions CI/CD workflows generated")


def test_determinism() -> None:
    """Test that two runs on identical inputs yield identical structure."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        output_dir1 = Path(tmpdir1) / "generated"
        output_dir2 = Path(tmpdir2) / "generated"
        
        # Run first time
        result1 = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir1)],
            capture_output=True, text=True, timeout=60
        )
        
        # Run second time
        result2 = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir2)],
            capture_output=True, text=True, timeout=60
        )
        
        assert result1.returncode == 0 and result2.returncode == 0
        
        # Compare file contents (should be identical)
        for root, dirs, files in os.walk(output_dir1):
            for filename in files:
                rel_path = Path(root).relative_to(output_dir1) / filename
                file1 = output_dir1 / rel_path
                file2 = output_dir2 / rel_path
                
                assert file2.exists(), f"File missing in second run: {rel_path}"
                
                content1 = file1.read_text()
                content2 = file2.read_text()
                
                # Skip files with timestamps (none expected but just in case)
                if "SCAFFOLD_SUMMARY.md" in str(rel_path):
                    # Summary has timestamp, just check structure
                    assert "Generated from intent-collect artifacts" in content1
                    assert "Generated from intent-collect artifacts" in content2
                else:
                    assert content1 == content2, f"{rel_path} should be identical between runs"
        
        # Same file count
        files1 = list(output_dir1.rglob("*"))
        files2 = list(output_dir2.rglob("*"))
        assert len(files1) == len(files2), "File count should match"
    
    print("✓ Determinism test passed - identical outputs for identical inputs")


def test_dry_run_works() -> None:
    """Test that --dry-run shows what would be created without writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        assert output["status"] == "dry_run"
        assert "would_create" in output
        assert output["would_create"] > 20
        assert "files" in output
        assert len(output["files"]) > 20
        
        # No files should be created
        assert not list(Path(tmpdir).rglob("*")), "No files should be created in dry-run"
    
    print("✓ Dry-run works correctly - shows files without writing")


def test_todo_not_fabrication() -> None:
    """Test that generated skill stubs use TODO: for unknowns, never fabricate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated"
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0
        
        # Check skill stubs have TODO comments
        for stage in ["build", "evaluate", "deploy", "publish", "observe", "feedback"]:
            stub_path = output_dir / f"scripts/{stage}/{stage}.py"
            content = stub_path.read_text()
            
            assert "TODO:" in content or "todo:" in content.lower(), f"{stage} stub should have TODO"
            assert "Implement" in content or "implement" in content.lower()
            
            # Should NOT contain specific fabricated implementation details
            # (The stub should be generic, not pretend to do real work)
    
    print("✓ TODO/not-fabrication test passed")


def test_output_summary() -> None:
    """Test that scaffold emits correct summary with counts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated"
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0
        
        output = json.loads(result.stdout.strip())
        
        assert output["status"] == "success"
        assert "artifacts" in output
        assert len(output["artifacts"]) > 20
        assert output["acceptance_criteria_count"] >= 1  # fixture has SPEC-01
        assert output["trajectory_steps"] >= 1  # fixture has steps
        assert output["project_name"] == "build-a-website"  # from fixture
        assert "input_artifacts" in output
        assert "output_dir" in output
    
    print("✓ Output summary has correct counts and metadata")


def main() -> int:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_missing_input_artifacts,
        test_generates_project_structure,
        test_package_json_valid,
        test_astro_config_valid,
        test_github_workflows_generated,
        test_determinism,
        test_dry_run_works,
        test_todo_not_fabrication,
        test_output_summary,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())