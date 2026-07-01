#!/usr/bin/env python3
"""
Eval for the trajectory-guard skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Correctly diffs exact/ordered/partial modes
4. Handles gate violations
5. Emits proper exit codes (0=pass, 1=fail, 2=warning)
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def make_telemetry(
    expected: list,
    actual: list,
    strictness: str = "ordered",
    run_id: str = "test-run",
) -> dict:
    """Create a telemetry dict for testing."""
    return {
        "run_id": run_id,
        "timestamp": "2026-01-01T00:00:00Z",
        "expected_trajectory": expected,
        "trajectory_strictness": strictness,
        "skills": actual,
        "model": "test-model",
        "tokens": 0,
        "cost": 0.0,
        "deploy_status": "not_deployed",
    }


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/trajectory-guard/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "trajectory-guard" in content, "SKILL.md must mention trajectory-guard"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that trajectory_guard.py exists and is executable."""
    script = Path("skills/trajectory-guard/scripts/trajectory_guard.py")
    assert script.exists(), "trajectory_guard.py must exist"
    assert os.access(str(script), os.X_OK), "trajectory_guard.py must be executable"
    print("✓ trajectory_guard.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    print("✓ Script shows usage without required args")


def test_exact_mode_pass() -> None:
    """Test exact mode: identical expected and actual."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    actual = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="exact")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert output["match_percent"] == 100.0, "Should be 100% match"
        assert output["status"] == "pass", "Should pass"
        assert output["details"]["missing"] == [], "No missing"
        assert output["details"]["extra"] == [], "No extra"
        print("✓ Exact mode pass test")
    finally:
        Path(telemetry_path).unlink()


def test_exact_mode_fail_missing() -> None:
    """Test exact mode: missing expected step."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    actual = [{"skill_id": "intent-collect"}, {"skill_id": "build"}]  # missing scaffold
    telemetry = make_telemetry(expected, actual, strictness="exact")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, f"Expected exit code 1 (fail), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert "scaffold" in output["details"]["missing"], "Should report scaffold as missing"
        assert output["status"] == "fail", "Should fail"
        print("✓ Exact mode fail (missing) test")
    finally:
        Path(telemetry_path).unlink()


def test_exact_mode_fail_extra() -> None:
    """Test exact mode: extra unexpected step."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "build"}]
    actual = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="exact")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, f"Expected exit code 1 (fail), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert "scaffold" in output["details"]["extra"], "Should report scaffold as extra"
        assert output["status"] == "fail", "Should fail"
        print("✓ Exact mode fail (extra) test")
    finally:
        Path(telemetry_path).unlink()


def test_exact_mode_fail_out_of_order() -> None:
    """Test exact mode: steps out of order."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    actual = [{"skill_id": "scaffold"}, {"skill_id": "intent-collect"}, {"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="exact")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, f"Expected exit code 1 (fail), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert len(output["details"]["out_of_order"]) > 0, "Should detect out of order"
        assert output["status"] == "fail", "Should fail"
        print("✓ Exact mode fail (out of order) test")
    finally:
        Path(telemetry_path).unlink()


def test_ordered_mode_pass() -> None:
    """Test ordered mode: expected in order, extras allowed."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "build"}]
    actual = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="ordered")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Expected exit code 0 (pass), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert output["match_percent"] == 100.0, "Should be 100% match"
        assert output["status"] == "pass", "Should pass"
        assert "scaffold" in output["details"]["extra"], "scaffold should be extra"
        print("✓ Ordered mode pass (extras allowed) test")
    finally:
        Path(telemetry_path).unlink()


def test_ordered_mode_warning_missing() -> None:
    """Test ordered mode: missing expected step = warning."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    actual = [{"skill_id": "intent-collect"}, {"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="ordered")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 2, f"Expected exit code 2 (warning), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert "scaffold" in output["details"]["missing"], "Should report scaffold as missing"
        assert output["status"] == "warning", "Should be warning"
        print("✓ Ordered mode warning (missing) test")
    finally:
        Path(telemetry_path).unlink()


def test_ordered_mode_warning_out_of_order() -> None:
    """Test ordered mode: out of order = warning."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}]
    actual = [{"skill_id": "scaffold"}, {"skill_id": "intent-collect"}, {"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="ordered")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 2, f"Expected exit code 2 (warning), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert len(output["details"]["out_of_order"]) > 0, "Should detect out of order"
        assert output["status"] == "warning", "Should be warning"
        print("✓ Ordered mode warning (out of order) test")
    finally:
        Path(telemetry_path).unlink()


def test_partial_mode_pass() -> None:
    """Test partial mode: checkpoints hit, order free."""
    expected = [
        {"skill_id": "intent-collect", "checkpoint": "HITL confirmation", "gate": True},
        {"skill_id": "build"},
    ]
    actual = [{"skill_id": "build"}, {"skill_id": "intent-collect"}]
    telemetry = make_telemetry(expected, actual, strictness="partial")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Expected exit code 0 (pass), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert output["match_percent"] == 100.0, "Should be 100% match"
        assert output["status"] == "pass", "Should pass"
        assert len(output["details"]["out_of_order"]) == 0, "No out-of-order in partial mode"
        print("✓ Partial mode pass (order free) test")
    finally:
        Path(telemetry_path).unlink()


def test_partial_mode_warning_missing_checkpoint() -> None:
    """Test partial mode: missing checkpoint = warning."""
    expected = [
        {"skill_id": "intent-collect", "checkpoint": "HITL confirmation", "gate": True},
        {"skill_id": "build"},
    ]
    actual = [{"skill_id": "build"}]  # missing intent-collect gate
    telemetry = make_telemetry(expected, actual, strictness="partial")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 2, f"Expected exit code 2 (warning), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert "intent-collect" in output["details"]["missing"], "Should report missing checkpoint"
        assert "intent-collect" in output["details"]["gate_violations"], "Should be gate violation"
        assert output["status"] == "warning", "Should be warning"
        print("✓ Partial mode warning (missing gate) test")
    finally:
        Path(telemetry_path).unlink()


def test_gate_violation_in_ordered_mode() -> None:
    """Test gate violation in ordered mode = warning (not fail)."""
    expected = [
        {"skill_id": "intent-collect", "gate": True},
        {"skill_id": "build"},
    ]
    actual = [{"skill_id": "build"}]
    telemetry = make_telemetry(expected, actual, strictness="ordered")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 2, f"Expected exit code 2 (warning), got {result.returncode}"
        output = json.loads(result.stdout.strip())
        assert "intent-collect" in output["details"]["gate_violations"], "Should be gate violation"
        print("✓ Gate violation in ordered mode test")
    finally:
        Path(telemetry_path).unlink()


def test_strictness_override() -> None:
    """Test --strictness CLI override."""
    expected = [{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}]
    actual = [{"skill_id": "intent-collect"}]  # missing scaffold
    telemetry = make_telemetry(expected, actual, strictness="partial")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(telemetry, f)
        telemetry_path = f.name

    try:
        # Override to exact mode - should fail
        result = subprocess.run(
            [sys.executable, "skills/trajectory-guard/scripts/trajectory_guard.py", "--telemetry-path", telemetry_path, "--strictness", "exact"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, "Should fail with exact override"
        output = json.loads(result.stdout.strip())
        assert output["strictness"] == "exact", "Report should show exact strictness"
        print("✓ Strictness override test")
    finally:
        Path(telemetry_path).unlink()


def test_output_file() -> None:
    """Test --output writes report to file."""
    expected = [{"skill_id": "intent-collect"}]
    actual = [{"skill_id": "intent-collect"}]
    telemetry = make_telemetry(expected, actual)

    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry_path = Path(tmpdir) / "telemetry.json"
        output_path = Path(tmpdir) / "report.json"
        telemetry_path.write_text(json.dumps(telemetry))

        result = subprocess.run(
            [
                sys.executable,
                "skills/trajectory-guard/scripts/trajectory_guard.py",
                "--telemetry-path", str(telemetry_path),
                "--output", str(output_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, "Should pass"
        assert output_path.exists(), "Output file should be created"
        report = json.loads(output_path.read_text())
        assert report["match_percent"] == 100.0
        print("✓ Output file test")


import os


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_exact_mode_pass,
        test_exact_mode_fail_missing,
        test_exact_mode_fail_extra,
        test_exact_mode_fail_out_of_order,
        test_ordered_mode_pass,
        test_ordered_mode_warning_missing,
        test_ordered_mode_warning_out_of_order,
        test_partial_mode_pass,
        test_partial_mode_warning_missing_checkpoint,
        test_gate_violation_in_ordered_mode,
        test_strictness_override,
        test_output_file,
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