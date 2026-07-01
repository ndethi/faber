#!/usr/bin/env python3
"""
Eval for the dashboard skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Generates valid HTML dashboard from telemetry
4. Includes all required sections
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def make_telemetry(
    run_id: str,
    skills: list,
    expected: list = None,
    model: str = "test-model",
    cost: float = 0.0,
    tokens: int = 1000,
    deploy_status: str = "not_deployed",
) -> dict:
    """Create a telemetry dict for testing."""
    return {
        "run_id": run_id,
        "timestamp": "2026-01-01T00:00:00Z",
        "expected_trajectory": expected or [],
        "trajectory_strictness": "ordered",
        "skills": skills,
        "model": model,
        "tokens": {"prompt": 500, "completion": 500, "total": tokens},
        "cost": cost,
        "deploy_status": deploy_status,
        "eval_scores": {"spec_conformance": 0.9, "design_coherence": 0.85},
    }


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/dashboard/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "dashboard" in content, "SKILL.md must mention dashboard"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that dashboard.py exists and is executable."""
    script = Path("skills/dashboard/scripts/dashboard.py")
    assert script.exists(), "dashboard.py must exist"
    assert os.access(str(script), os.X_OK), "dashboard.py must be executable"
    print("✓ dashboard.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/dashboard/scripts/dashboard.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    print("✓ Script shows usage without required args")


def test_generate_dashboard() -> None:
    """Test dashboard generation with fixture telemetry."""
    runs = [
        make_telemetry(
            "run-1",
            [{"skill_id": "intent-collect", "status": "success", "duration_ms": 1000},
             {"skill_id": "scaffold", "status": "success", "duration_ms": 2000},
             {"skill_id": "build", "status": "success", "duration_ms": 3000}],
            expected=[{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}],
            cost=0.05,
            tokens=5000,
        ),
        make_telemetry(
            "run-2",
            [{"skill_id": "intent-collect", "status": "success", "duration_ms": 1000},
             {"skill_id": "build", "status": "failure", "duration_ms": 100}],
            expected=[{"skill_id": "intent-collect"}, {"skill_id": "scaffold"}, {"skill_id": "build"}],
            cost=0.02,
            tokens=2000,
            deploy_status="failed",
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()

        for i, run in enumerate(runs):
            run_dir = runs_dir / f"run-{i+1}"
            run_dir.mkdir()
            (run_dir / "telemetry.json").write_text(json.dumps(run))

        output_dir = Path(tmpdir) / "dashboard"

        result = subprocess.run(
            [
                sys.executable,
                "skills/dashboard/scripts/dashboard.py",
                "--runs-dir", str(runs_dir),
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        output = json.loads(result.stdout.strip())

        assert output["runs_processed"] == 2, "Should process 2 runs"
        assert "dashboard_path" in output, "Should have dashboard path"
        assert output["summary"]["total_runs"] == 2
        assert output["summary"]["total_cost"] == 0.07

        # Check HTML file exists and has content
        html_path = Path(output["dashboard_path"])
        assert html_path.exists(), "HTML file should be created"
        html_content = html_path.read_text()
        assert "<!DOCTYPE html>" in html_content, "Should be valid HTML"
        assert "Faber Dashboard" in html_content, "Should have title"
        assert "Runs" in html_content, "Should have Runs section"
        assert "Trajectory Conformance" in html_content, "Should have trajectory section"
        assert "Cost Summary" in html_content, "Should have cost section"
        assert "Model Routing" in html_content, "Should have model routing section"
        assert "Eval Scores" in html_content, "Should have eval scores section"
        assert "HITL Queue" in html_content, "Should have HITL queue section"
        assert "Scope Ledger" in html_content, "Should have scope ledger section"
        assert "run-1" in html_content or "run-2" in html_content, "Should include run IDs"

        print("✓ Dashboard generation test")


def test_empty_runs_dir() -> None:
    """Test dashboard generation with empty runs directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        output_dir = Path(tmpdir) / "dashboard"

        result = subprocess.run(
            [
                sys.executable,
                "skills/dashboard/scripts/dashboard.py",
                "--runs-dir", str(runs_dir),
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        output = json.loads(result.stdout.strip())

        assert output["runs_processed"] == 0, "Should process 0 runs"
        assert output["summary"]["total_runs"] == 0

        html_path = Path(output["dashboard_path"])
        assert html_path.exists(), "HTML file should be created"
        html_content = html_path.read_text()
        assert "No runs found" in html_content, "Should show empty state"

        print("✓ Empty runs directory test")


def test_missing_runs_dir() -> None:
    """Test error handling for missing runs directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "nonexistent"
        output_dir = Path(tmpdir) / "dashboard"

        result = subprocess.run(
            [
                sys.executable,
                "skills/dashboard/scripts/dashboard.py",
                "--runs-dir", str(runs_dir),
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 1, "Should exit with error"
        output = json.loads(result.stdout.strip())
        assert "error" in output, "Should return error"

        print("✓ Missing runs directory test")


def test_output_file_structure() -> None:
    """Test that generated HTML has proper structure."""
    runs = [
        make_telemetry(
            "test-run",
            [{"skill_id": "intent-collect", "status": "success", "duration_ms": 1000}],
            expected=[{"skill_id": "intent-collect"}],
            cost=0.01,
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        (runs_dir / "test-run" / "telemetry.json").parent.mkdir(parents=True)
        (runs_dir / "test-run" / "telemetry.json").write_text(json.dumps(runs[0]))

        output_dir = Path(tmpdir) / "dashboard"

        result = subprocess.run(
            [
                sys.executable,
                "skills/dashboard/scripts/dashboard.py",
                "--runs-dir", str(runs_dir),
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())

        html_path = Path(output["dashboard_path"])
        html = html_path.read_text()

        # Check for key structural elements
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "<style>" in html
        assert "runs-table" in html
        assert "trajectory-detail" in html
        assert "cost-summary" in html
        assert "model-routing" in html
        assert "eval-scores" in html
        assert "hitl-queue" in html
        assert "scope-ledger" in html

        print("✓ HTML structure test")


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_generate_dashboard,
        test_empty_runs_dir,
        test_missing_runs_dir,
        test_output_file_structure,
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