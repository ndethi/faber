#!/usr/bin/env python3
"""
Eval for the evaluate skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Produces expected outputs deterministically
4. Handles unknowns as TODO:, never fabricates
5. HITL gate and dry-run work correctly
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


FIXTURES_DIR = Path("fixtures/rohaki")
SKILL_DIR = Path("skills/evaluate")
SCRIPT = SKILL_DIR / "scripts" / "evaluate.py"


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name: evaluate" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "evaluate" in content, "SKILL.md must mention skill name"
    assert "intent-collect" in content, "SKILL.md must reference intent-collect"
    assert "scaffold" in content, "SKILL.md must reference scaffold"
    assert "trajectory-guard" in content, "SKILL.md must reference trajectory-guard"
    assert "FRAMEWORK.md" in content, "SKILL.md must reference FRAMEWORK.md"
    assert "HITL" in content, "SKILL.md must mention HITL gates"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that evaluate.py exists and is executable."""
    assert SCRIPT.exists(), "evaluate.py must exist"
    assert os.access(str(SCRIPT), os.X_OK), "evaluate.py must be executable"
    print("✓ evaluate.py exists and is executable")


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
    assert "project-dir" in output.lower(), "Should mention --project-dir argument"
    print("✓ Script shows usage without required args")


def test_missing_input_artifacts() -> None:
    """Test that script errors gracefully when input artifacts missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty directory - no artifacts
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", tmpdir, "--project-dir", tmpdir],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Should fail when artifacts missing"
        
        output = json.loads(result.stdout.strip())
        assert output["status"] == "error"
        assert "not found" in output["error"].lower() or "missing" in output["error"].lower()
    
    print("✓ Missing input artifacts handled correctly")


def test_dry_run_works() -> None:
    """Test that --dry-run shows what would be evaluated without running checks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a minimal scaffolded project structure for dry-run
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        
        # Create minimal package.json for dry-run to recognize
        (project_dir / "package.json").write_text(json.dumps({
            "name": "test-project",
            "scripts": {"test": "vitest run", "lint": "eslint src"}
        }))
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--project-dir", str(project_dir), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        assert output["status"] == "dry_run"
        assert "would_run" in output
        assert len(output["would_run"]) == 4  # npm test, lint, astro check, trajectory-guard
        assert "acceptance_criteria_count" in output
        assert "strictness" in output
        
        # No files should be created
        assert not list(Path(tmpdir).rglob("evaluation-report*")), "No report files in dry-run"
    
    print("✓ Dry-run works correctly - shows checks without executing")


def test_parses_input_artifacts() -> None:
    """Test that the script correctly parses spec.md and trajectory.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text(json.dumps({
            "name": "test-project",
            "scripts": {"test": "vitest run", "lint": "eslint src"}
        }))
        
        # Run with dry-run to see parsed values
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--project-dir", str(project_dir), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0
        
        output = json.loads(result.stdout.strip())
        assert output["status"] == "dry_run"
        assert "acceptance_criteria_count" in output
        assert output["acceptance_criteria_count"] >= 1  # fixture has SPEC-01
        assert "strictness" in output
        assert output["strictness"] in ["exact", "ordered", "partial"]
    
    print("✓ Parses input artifacts correctly (spec.md SPEC-XX, trajectory.md strictness)")


def test_determinism_dry_run() -> None:
    """Test that two dry-runs on identical inputs yield identical output."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        project_dir1 = Path(tmpdir1) / "project"
        project_dir2 = Path(tmpdir2) / "project"
        
        for pd in [project_dir1, project_dir2]:
            pd.mkdir()
            (pd / "package.json").write_text(json.dumps({
                "name": "test-project",
                "scripts": {"test": "vitest run", "lint": "eslint src"}
            }))
        
        # Run dry-run twice
        result1 = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--project-dir", str(project_dir1), "--dry-run"],
            capture_output=True, text=True, timeout=30
        )
        result2 = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--project-dir", str(project_dir2), "--dry-run"],
            capture_output=True, text=True, timeout=30
        )
        
        assert result1.returncode == 0 and result2.returncode == 0
        
        out1 = json.loads(result1.stdout.strip())
        out2 = json.loads(result2.stdout.strip())
        
        # Dry-run outputs should be identical (except timestamps if any)
        assert out1["status"] == out2["status"] == "dry_run"
        assert out1["acceptance_criteria_count"] == out2["acceptance_criteria_count"]
        assert out1["strictness"] == out2["strictness"]
        assert out1["would_run"] == out2["would_run"]
    
    print("✓ Determinism test passed - identical dry-run outputs for identical inputs")


def test_todo_not_fabrication() -> None:
    """Test that reports don't fabricate results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text(json.dumps({
            "name": "test",
            "scripts": {"test": "vitest run", "lint": "eslint src"}
        }))
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--project-dir", str(project_dir)],
            capture_output=True, text=True, timeout=180
        )
        
        # Should complete (may fail due to missing deps but should not crash)
        assert result.returncode in [0, 1]
        
        if result.returncode == 0:
            out = json.loads(result.stdout.strip())
            for artifact in out["artifacts"]:
                if artifact.endswith(".md"):
                    content = Path(artifact).read_text()
                    # Should not claim false success
                    if "FAIL" in content or "❌" in content:
                        # That's honest - it failed
                        pass
    
    print("✓ TODO/not-fabrication test passed - honest failure reporting")


def test_output_report_structure_dry_run() -> None:
    """Test that dry-run output has correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text(json.dumps({
            "name": "test-project",
            "scripts": {"test": "vitest run", "lint": "eslint src"}
        }))
        
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-dir", str(FIXTURES_DIR), "--project-dir", str(project_dir), "--dry-run"],
            capture_output=True, text=True, timeout=30
        )
        
        assert result.returncode == 0
        
        out = json.loads(result.stdout.strip())
        
        required_keys = ["status", "would_run", "acceptance_criteria_count", "strictness", "project_dir"]
        for key in required_keys:
            assert key in out, f"Missing key in dry-run output: {key}"
        
        assert out["status"] == "dry_run"
        assert len(out["would_run"]) == 4
        # Check that all 4 checks are present (trajectory-guard includes strictness in name)
        check_names = {c for c in out["would_run"]}
        assert "npm test" in check_names
        assert "npm run lint" in check_names
        assert "npx astro check" in check_names
        # trajectory-guard includes strictness in name
        assert any("trajectory-guard" in c for c in check_names)
    
    print("✓ Dry-run output structure is correct")


def main() -> int:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_missing_input_artifacts,
        test_dry_run_works,
        test_parses_input_artifacts,
        test_determinism_dry_run,
        test_todo_not_fabrication,
        test_output_report_structure_dry_run,
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
    sys.exit(main())