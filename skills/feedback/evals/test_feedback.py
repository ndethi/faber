#!/usr/bin/env python3
"""
Evaluations for the Feedback skill.

Tests that the feedback skill meets its acceptance criteria per SKILL.md.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_skill_md_exists():
    """Test that SKILL.md exists and has required fields."""
    skill_md = Path("skills/feedback/SKILL.md")
    assert skill_md.exists(), "SKILL.md does not exist"

    content = skill_md.read_text()
    assert "name: feedback" in content
    assert "description:" in content
    assert "version:" in content
    assert "author:" in content
    assert "license:" in content
    assert "tags:" in content


def test_script_exists_and_executable():
    """Test that collect_feedback.py exists and is executable."""
    script = Path("skills/feedback/scripts/collect_feedback.py")
    assert script.exists(), "collect_feedback.py does not exist"
    assert script.stat().st_mode & 0o111, "collect_feedback.py is not executable"


def test_script_help():
    """Test that script shows help without error."""
    result = subprocess.run(
        [sys.executable, "skills/feedback/scripts/collect_feedback.py", "--help"],
        capture_output=True,
        text=True,
        timeout=30
    )
    assert result.returncode == 0, f"Help failed: {result.stderr}"
    assert "--run-dir" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--hitl-gate" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--rating" in result.stdout
    assert "--notes" in result.stdout


def test_missing_run_dir():
    """Test that script fails gracefully when run directory is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_dir = Path(tmpdir) / "nonexistent"

        result = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(nonexistent_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode != 0, "Should fail when run directory missing"
        assert "does not exist" in result.stderr or "does not exist" in result.stdout


def test_collects_feedback_from_observations():
    """Test that feedback is collected from run directory with observations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "run_20260706_100000"
        run_dir.mkdir()

        # Create observations.json
        observations = {
            "generated_at": "2026-07-06T10:00:00Z",
            "time_window": "24h",
            "runs_analyzed": 3,
            "aggregates": {
                "total_count": 3,
                "success_count": 2,
                "failure_count": 1,
                "total_tokens": 500,
                "total_cost_usd": 1.25,
                "avg_duration_sec": 15.0,
                "median_duration_sec": 12.0,
                "success_rate": 0.66
            },
            "trends": {"tokens_per_hour": [100, 200, 200]},
            "recent_runs": []
        }
        (run_dir / "observations.json").write_text(json.dumps(observations))

        # Create telemetry.json
        telemetry = {
            "run_id": "run_20260706_100000",
            "skills": ["intent-collect", "scaffold", "build", "evaluate"],
            "trajectory_strictness": "ordered"
        }
        (run_dir / "telemetry.json").write_text(json.dumps(telemetry))

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(run_dir),
             "--output-dir", str(output_dir),
             "--rating", "5",
             "--notes", "Excellent run",
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Feedback collection failed: {result.stderr}"

        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert output["rating"] == 5
        assert output["notes"] == "Excellent run"
        assert output["dry_run"] is True

        # Verify feedback.json was NOT written (dry-run)
        assert not (output_dir / "feedback.json").exists()


def test_writes_feedback_file():
    """Test that feedback.json is written when not in dry-run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "run_20260706_100000"
        run_dir.mkdir()

        observations = {
            "generated_at": "2026-07-06T10:00000:00Z",
            "runs_analyzed": 1,
            "aggregates": {"success_rate": 1.0}
        }
        (run_dir / "observations.json").write_text(json.dumps(observations))

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(run_dir),
             "--output-dir", str(output_dir),
             "--rating", "4",
             "--notes", "Good"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Feedback write failed: {result.stderr}"

        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert output["rating"] == 4
        assert output["notes"] == "Good"
        assert output["dry_run"] is False

        # Verify feedback.json was written
        assert (output_dir / "feedback.json").exists()

        feedback = json.loads((output_dir / "feedback.json").read_text())
        assert feedback["run_id"] == "run_20260706_100000"
        assert feedback["rating"] == 4
        assert feedback["notes"] == "Good"
        assert feedback["context"]["runs_analyzed"] == 1
        assert "collected_at" in feedback


def test_default_rating_when_not_provided():
    """Test default rating (3) when not provided and not in HITL mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "run_20260706_100000"
        run_dir.mkdir()
        (run_dir / "observations.json").write_text(json.dumps({"runs_analyzed": 1}))

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(run_dir),
             "--output-dir", str(output_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0

        output = json.loads(result.stdout.strip())
        assert output["rating"] == 3  # Default neutral
        assert output["notes"] == ""


def test_handles_missing_observations():
    """Test graceful handling when observations.json is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "run_20260706_100000"
        run_dir.mkdir()
        # No observations.json

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(run_dir),
             "--output-dir", str(output_dir),
             "--rating", "3",
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0

        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert output["rating"] == 3
        # Context should have None values for missing observations
        # (The feedback context reading handles missing files gracefully)


def test_deterministic_output():
    """Test that identical inputs produce identical feedback structure."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        for tmpdir, label in [(tmpdir1, "1"), (tmpdir2, "2")]:
            run_dir = Path(tmpdir) / "run_20260706_100000"
            run_dir.mkdir()
            (run_dir / "observations.json").write_text(json.dumps({"runs_analyzed": 2, "aggregates": {"success_rate": 0.5}}))

        # Run first time
        result1 = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(Path(tmpdir1) / "run_20260706_100000"),
             "--output-dir", str(Path(tmpdir1) / "output"),
             "--rating", "4",
             "--notes", "Test",
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Run second time
        result2 = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(Path(tmpdir2) / "run_20260706_100000"),
             "--output-dir", str(Path(tmpdir2) / "output"),
             "--rating", "4",
             "--notes", "Test",
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result1.returncode == 0
        assert result2.returncode == 0

        output1 = json.loads(result1.stdout.strip())
        output2 = json.loads(result2.stdout.strip())

        # Remove variable fields for comparison
        for key in ["collected_at"]:
            output1.pop(key, None)
            output2.pop(key, None)

        # Core fields should be identical
        assert output1["status"] == output2["status"]
        assert output1["rating"] == output2["rating"]
        assert output1["notes"] == output2["notes"]
        assert output1["dry_run"] == output2["dry_run"]


def test_invalid_rating_rejected():
    """Test that invalid ratings are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "run_20260706_100000"
        run_dir.mkdir()
        (run_dir / "observations.json").write_text(json.dumps({}))

        result = subprocess.run(
            [sys.executable, "skills/feedback/scripts/collect_feedback.py",
             "--run-dir", str(run_dir),
             "--rating", "6"],  # Invalid: >5
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode != 0, "Should reject invalid rating"


if __name__ == "__main__":
    test_skill_md_exists()
    print("✓ test_skill_md_exists")

    test_script_exists_and_executable()
    print("✓ test_script_exists_and_executable")

    test_script_help()
    print("✓ test_script_help")

    test_missing_run_dir()
    print("✓ test_missing_run_dir")

    test_collects_feedback_from_observations()
    print("✓ test_collects_feedback_from_observations")

    test_writes_feedback_file()
    print("✓ test_writes_feedback_file")

    test_default_rating_when_not_provided()
    print("✓ test_default_rating_when_not_provided")

    test_handles_missing_observations()
    print("✓ test_handles_missing_observations")

    test_deterministic_output()
    print("✓ test_deterministic_output")

    test_invalid_rating_rejected()
    print("✓ test_invalid_rating_rejected")

    print("\nAll tests passed!")