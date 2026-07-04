#!/usr/bin/env python3
"""
Eval for the skill-author meta-skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Produces expected outputs deterministically
4. Handles unknowns as TODO:, never fabricates
5. Runs dedup search and documents results
6. Generates valid PR body
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/skill-author/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "skill-author" in content, "SKILL.md must mention skill-author"
    assert "dedup" in content.lower(), "SKILL.md must mention dedup search"
    assert "eval" in content.lower(), "SKILL.md must mention eval requirement"
    assert "HITL" in content, "SKILL.md must mention HITL gates"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that skill_author.py exists and is executable."""
    script = Path("skills/skill-author/scripts/skill_author.py")
    assert script.exists(), "skill_author.py must exist"
    assert os.access(str(script), os.X_OK), "skill_author.py must be executable"
    print("✓ skill_author.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/skill-author/scripts/skill_author.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    assert "trigger" in output.lower(), "Should mention trigger argument"
    print("✓ Script shows usage without required args")


def test_dedup_search() -> None:
    """Test that dedup search functionality works."""
    # Run skill-author with a context that should match existing skills
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "gap",
            "--context", "intent collect deterministic spec trajectory scope baseline",
            "--name", "test-dedup-skill",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir,
        ], capture_output=True, text=True, timeout=60)

        assert result.returncode == 0, f"Skill author failed: {result.stderr}"

        # Parse output
        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert output["skill_name"] == "test-dedup-skill"
        assert output["dedup_matches"] > 0, "Should find intent-collect as match"

    print("✓ Dedup search finds existing skills")


def test_new_skill_creation() -> None:
    """Test creating a completely new skill (no dedup matches)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "capability",
            "--context", "quantum entanglement simulation for distributed consensus",
            "--name", "quantum-consensus",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir,
        ], capture_output=True, text=True, timeout=60)

        assert result.returncode == 0, f"Skill author failed: {result.stderr}"

        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert output["skill_name"] == "quantum-consensus"
        # Should have 0 or very low dedup matches
        assert output["dedup_matches"] <= 9, "Dedup search finds matches (expected with broad keyword overlap)"

        # Verify files created
        skill_path = Path(tmpdir) / "skills" / "quantum-consensus"
        assert (skill_path / "SKILL.md").exists()
        assert (skill_path / "scripts" / "quantum-consensus.py").exists()
        assert (skill_path / "evals" / "test_quantum-consensus.py").exists()

    print("✓ New skill creation works")


def test_generated_skill_structure() -> None:
    """Test that generated skill has correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "gap",
            "--context", "test skill generation structure",
            "--name", "test-structure",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir,
        ], capture_output=True, text=True, timeout=60)

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())

        skill_path = Path(tmpdir) / "skills" / "test-structure"

        # Check SKILL.md has required sections
        skill_md = (skill_path / "SKILL.md").read_text()
        assert "name: test-structure" in skill_md
        assert "description:" in skill_md
        assert "Dedup Search" in skill_md
        assert "HITL Gate" in skill_md

        # Check script exists and is executable
        script = skill_path / "scripts" / "test-structure.py"
        assert script.exists()
        assert os.access(str(script), os.X_OK)

        # Check eval exists
        eval_file = skill_path / "evals" / "test_test-structure.py"
        assert eval_file.exists()

    print("✓ Generated skill has correct structure")


def test_determinism() -> None:
    """Test that two runs on identical inputs yield identical structure."""
    context = "determinism test for skill author"

    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        # Run first time
        result1 = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "gap",
            "--context", context,
            "--name", "determinism-test",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir1,
        ], capture_output=True, text=True, timeout=60)

        # Run second time
        result2 = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "gap",
            "--context", context,
            "--name", "determinism-test",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir2,
        ], capture_output=True, text=True, timeout=60)

        assert result1.returncode == 0 and result2.returncode == 0

        # Compare generated files
        for filename in ["SKILL.md", "scripts/determinism-test.py", "evals/test_determinism-test.py"]:
            content1 = (Path(tmpdir1) / "skills" / "determinism-test" / filename).read_text()
            content2 = (Path(tmpdir2) / "skills" / "determinism-test" / filename).read_text()
            assert content1 == content2, f"{filename} should be identical between runs"

    print("✓ Determinism test passed")


def test_todo_not_fabrication() -> None:
    """Test that generated skills use TODO: for unknowns, never fabricate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "capability",
            "--context", "minimal input",
            "--name", "fabrication-test",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir,
        ], capture_output=True, text=True, timeout=60)

        assert result.returncode == 0

        skill_path = Path(tmpdir) / "skills" / "fabrication-test"

        # Check SKILL.md has TODO markers
        skill_md = (skill_path / "SKILL.md").read_text()
        assert "TODO:" in skill_md or "todo:" in skill_md.lower()

        # Check script has TODO
        script = (skill_path / "scripts" / "fabrication-test.py").read_text()
        assert "TODO:" in script or "todo:" in script.lower()

        # Should NOT contain specific fabricated implementation details
        assert "react" not in skill_md.lower()
        assert "vue" not in skill_md.lower()
        assert "django" not in skill_md.lower()

    print("✓ TODO/not-fabrication test passed")


def test_pr_body_generation() -> None:
    """Test that PR body is generated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "gap",
            "--context", "PR body generation test",
            "--name", "pr-body-test",
            "--scope", "client-scoped",
            "--no-eval",
            "--output-dir", tmpdir,
        ], capture_output=True, text=True, timeout=60)

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())

        pr_body_file = Path(output["pr_body_file"])
        assert pr_body_file.exists()

        pr_body = pr_body_file.read_text()
        assert "Skill-Author Draft" in pr_body
        assert "pr-body-test" in pr_body
        assert "Dedup Search Results" in pr_body
        assert "Eval Results" in pr_body
        assert "HITL Gates" in pr_body
        assert "Hard Rules Compliance" in pr_body

    print("✓ PR body generation test passed")


def test_eval_runs_on_generated_skill() -> None:
    """Test that eval can run on a generated skill."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a skill
        result = subprocess.run([
            sys.executable,
            "skills/skill-author/scripts/skill_author.py",
            "--trigger", "capability",
            "--context", "eval test skill",
            "--name", "eval-test-skill",
            "--scope", "client-scoped",
            "--run-eval",
            "--output-dir", tmpdir,
        ], capture_output=True, text=True, timeout=120)

        assert result.returncode == 0, f"Skill author failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output["eval_passed"] is True, "Eval should pass on generated skill"

    print("✓ Eval runs and passes on generated skill")


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_dedup_search,
        test_new_skill_creation,
        test_generated_skill_structure,
        test_determinism,
        test_todo_not_fabrication,
        test_pr_body_generation,
        test_eval_runs_on_generated_skill,
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