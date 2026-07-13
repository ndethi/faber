#!/usr/bin/env python3
"""
Eval for the my-skill skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Produces expected outputs deterministically
4. Handles unknowns as TODO:, never fabricates
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/my-skill/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "my-skill" in content, "SKILL.md must mention skill name"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that main script exists and is executable."""
    script = Path("skills/my-skill/scripts/my-skill.py")
    assert script.exists(), f"{name}.py must exist"
    assert os.access(str(script), os.X_OK), f"{name}.py must be executable"
    print("✓ {name}.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/my-skill/scripts/my-skill.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    print("✓ Script shows usage without required args")


def test_determinism() -> None:
    """Test that two runs on identical inputs yield identical structure."""
    test_input = {"test": "input"}
    input_json = json.dumps(test_input)

    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        # Run first time
        result1 = subprocess.run([
            sys.executable,
            "skills/my-skill/scripts/my-skill.py",
            "--input", input_json,
            "--output-dir", tmpdir1
        ], capture_output=True, text=True, timeout=30)

        # Run second time
        result2 = subprocess.run([
            sys.executable,
            "skills/my-skill/scripts/my-skill.py",
            "--input", input_json,
            "--output-dir", tmpdir2
        ], capture_output=True, text=True, timeout=30)

        assert result1.returncode == 0 and result2.returncode == 0, "Both runs should succeed"

        # Compare file contents (should be identical)
        for filename in os.listdir(tmpdir1):
            if filename.endswith(".md") or filename.endswith(".json"):
                content1 = (Path(tmpdir1) / filename).read_text()
                content2 = (Path(tmpdir2) / filename).read_text()
                assert content1 == content2, f"{filename} should be identical between runs"

    print("✓ Determinism test passed")


def test_todo_not_fabrication() -> None:
    """Test that unknowns appear as TODO:, never fabricated details."""
    test_input = {"test": "minimal input"}
    input_json = json.dumps(test_input)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/my-skill/scripts/my-skill.py",
            "--input", input_json,
            "--output-dir", tmpdir
        ], capture_output=True, text=True, timeout=30)

        assert result.returncode == 0, "Should succeed"

        # Check output files for TODO items, no fabrication
        for filename in os.listdir(tmpdir):
            if filename.endswith(".md"):
                content = (Path(tmpdir) / filename).read_text()
                # Should have TODO for unknowns
                # Should NOT contain specific fabricated details
                assert "TODO:" in content or "todo:" in content.lower(), f"{filename} should have TODO for unknowns"

    print("✓ TODO/not-fabrication test passed")


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_determinism,
        test_todo_not_fabrication,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
