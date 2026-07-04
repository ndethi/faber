#!/usr/bin/env python3
"""
Eval for the model-route skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Routes skills according to policy
4. Records eval results and updates policy
5. Checks graduation correctly
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/model-route/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "model-route" in content, "SKILL.md must mention model-route"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that model_route.py exists and is executable."""
    script = Path("skills/model-route/scripts/model_route.py")
    assert script.exists(), "model_route.py must exist"
    assert os.access(str(script), os.X_OK), "model_route.py must be executable"
    print("✓ model_route.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/model-route/scripts/model_route.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    print("✓ Script shows usage without required args")


def test_default_routing() -> None:
    """Test default routing for various skill IDs."""
    test_cases = [
        ("intent-collect", "local"),
        ("build", "local"),
        ("evaluate", "frontier"),
        ("scaffold", "local"),
        ("deploy", "local"),
        ("publish", "local"),
        ("observe", "local"),
        ("feedback", "frontier"),
        ("unknown-skill", "frontier"),  # default
    ]

    for skill_id, expected_route in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.json"

            result = subprocess.run(
                [
                    sys.executable,
                    "skills/model-route/scripts/model_route.py",
                    "--skill-id", skill_id,
                    "--policy-path", str(policy_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"Failed for {skill_id}: {result.stderr}"
            decision = json.loads(result.stdout.strip())
            assert decision["model"] == expected_route, f"{skill_id}: expected {expected_route}, got {decision['model']}"
            assert "endpoint" in decision
            assert "model_name" in decision
            assert "reason" in decision
            assert "estimated_cost_usd" in decision

    print("✓ Default routing test")


def test_context_override() -> None:
    """Test context-based routing override."""
    # Routine context should downgrade to local
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"

        result = subprocess.run(
            [
                sys.executable,
                "skills/model-route/scripts/model_route.py",
                "--skill-id", "evaluate",  # normally frontier
                "--context", "extract and parse JSON",  # routine task
                "--policy-path", str(policy_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        decision = json.loads(result.stdout.strip())
        # Context should downgrade to local
        assert decision["model"] == "local", f"Expected local, got {decision['model']}"
        assert "downgraded" in decision["reason"].lower() or "routine" in decision["reason"].lower()

    # Complex context should upgrade to frontier
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"

        result = subprocess.run(
            [
                sys.executable,
                "skills/model-route/scripts/model_route.py",
                "--skill-id", "build",  # normally local
                "--context", "design system architecture with complex reasoning",  # complex task
                "--policy-path", str(policy_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        decision = json.loads(result.stdout.strip())
        # Context should upgrade to frontier
        assert decision["model"] == "frontier", f"Expected frontier, got {decision['model']}"

    print("✓ Context override test")


def test_record_eval_and_graduation() -> None:
    """Test recording eval results and graduation check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"

        # Record 15 eval results where local matches frontier quality
        for i in range(15):
            result = subprocess.run(
                [
                    sys.executable,
                    "skills/model-route/scripts/model_route.py",
                    "--skill-id", "build",
                    "--policy-path", str(policy_path),
                    "--record-eval",
                    "--local-quality", "0.96",
                    "--frontier-quality", "0.98",
                    "--local-cost", "0.0",
                    "--frontier-cost", "0.01",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, f"Record eval {i} failed: {result.stderr}"

        # Check graduation - should graduate
        result = subprocess.run(
            [
                sys.executable,
                "skills/model-route/scripts/model_route.py",
                "--skill-id", "build",
                "--policy-path", str(policy_path),
                "--check-graduation",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Graduation check failed: {result.stderr}"
        grad = json.loads(result.stdout.strip())
        assert grad["should_graduate"] is True, f"Expected graduation, got: {grad}"
        assert grad["samples"] == 15
        assert grad["avg_quality_ratio"] >= 0.95
        assert grad["avg_cost_savings"] >= 0.5

    # Test insufficient samples
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"

        # Record only 5 evals
        for i in range(5):
            subprocess.run(
                [
                    sys.executable,
                    "skills/model-route/scripts/model_route.py",
                    "--skill-id", "deploy",
                    "--policy-path", str(policy_path),
                    "--record-eval",
                    "--local-quality", "0.90",
                    "--frontier-quality", "0.95",
                    "--local-cost", "0.0",
                    "--frontier-cost", "0.01",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

        result = subprocess.run(
            [
                sys.executable,
                "skills/model-route/scripts/model_route.py",
                "--skill-id", "deploy",
                "--policy-path", str(policy_path),
                "--check-graduation",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        grad = json.loads(result.stdout.strip())
        assert grad["should_graduate"] is False
        assert "Insufficient samples" in grad["reason"]

    print("✓ Record eval and graduation test")


def test_policy_persistence() -> None:
    """Test that policy is saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"

        # First run creates default policy
        result = subprocess.run(
            [
                sys.executable,
                "skills/model-route/scripts/model_route.py",
                "--skill-id", "intent-collect",
                "--policy-path", str(policy_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

        # Verify policy file exists and has correct structure
        assert policy_path.exists()
        policy = json.loads(policy_path.read_text())
        assert "skills" in policy
        assert "graduation_thresholds" in policy
        assert "eval_history" in policy

        # Second run should load existing policy
        result = subprocess.run(
            [
                sys.executable,
                "skills/model-route/scripts/model_route.py",
                "--skill-id", "build",
                "--policy-path", str(policy_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

    print("✓ Policy persistence test")


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_default_routing,
        test_context_override,
        test_record_eval_and_graduation,
        test_policy_persistence,
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