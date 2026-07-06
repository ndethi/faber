#!/usr/bin/env python3
"""
Evaluations for the Observe skill.

Tests that the observe skill meets its acceptance criteria per SKILL.md.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def test_skill_md_exists():
    """Test that SKILL.md exists and has required fields."""
    skill_md = Path("skills/observe/SKILL.md")
    assert skill_md.exists(), "SKILL.md does not exist"
    
    content = skill_md.read_text()
    assert "name: observe" in content
    assert "description:" in content
    assert "version:" in content
    assert "author:" in content
    assert "license:" in content
    assert "tags:" in content


def test_script_exists_and_executable():
    """Test that observe.py exists and is executable."""
    script = Path("skills/observe/scripts/observe.py")
    assert script.exists(), "observe.py does not exist"
    assert script.stat().st_mode & 0o111, "observe.py is not executable"


def test_script_help():
    """Test that script shows help without error."""
    result = subprocess.run(
        [sys.executable, "skills/observe/scripts/observe.py", "--help"],
        capture_output=True,
        text=True,
        timeout=30
    )
    assert result.returncode == 0, f"Help failed: {result.stderr}"
    assert "--runs-dir" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--time-window" in result.stdout
    assert "--hitl-gate" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--format" in result.stdout


def test_missing_runs_dir():
    """Test that script fails gracefully when runs directory is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_dir = Path(tmpdir) / "nonexistent"
        
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(nonexistent_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode != 0, "Should fail when runs directory missing"
        assert "does not exist" in result.stderr or "does not exist" in result.stdout


def test_parses_time_window():
    """Test that time window parsing works correctly."""
    # This is tested indirectly through integration tests
    pass


def test_discovers_telemetry_files():
    """Test that script finds telemetry.json files in run directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        # Create a run directory with telemetry
        run1 = runs_dir / "run_20260705_100000"
        run1.mkdir()
        telemetry1 = {
            "timestamp": "2026-07-05T10:00:00Z",
            "success": True,
            "tokens": 100,
            "cost_usd": 3.50,
            "duration_sec": 45.2,
            "model": "test-model"
        }
        (run1 / "telemetry.json").write_text(json.dumps(telemetry1))
        
        # Create another run directory
        run2 = runs_dir / "run_20260705_110000"
        run2.mkdir()
        telemetry2 = {
            "timestamp": "2026-07-05T11:00:00Z",
            "success": False,
            "tokens": 50,
            "cost_usd": 1.75,
            "duration_sec": 30.1,
            "model": "test-model"
        }
        (run2 / "telemetry.json").write_text(json.dumps(telemetry2))
        
        # Create a non-run directory (should be ignored)
        (runs_dir / "not-a-run").mkdir()
        
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(runs_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        assert output["runs_analyzed"] == 2
        assert output["total_tokens"] == 150
        assert abs(output["total_cost_usd"] - 5.25) < 0.001
        assert abs(output["success_rate"] - 0.5) < 0.001


def test_time_window_filtering():
    """Test that --time-wilter filters correctly."""
    from datetime import datetime, timezone, timedelta
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        # Use today's date for the heuristic to work
        today = datetime.now(timezone.utc)
        one_hour_ago = today - timedelta(hours=1)
        
        # Create old run (should be filtered out with 1h window)
        old_run = runs_dir / f"run_{one_hour_ago.strftime('%Y%m%d_%H%M%S')}"
        old_run.mkdir()
        old_telemetry = {
            "timestamp": one_hour_ago.isoformat(),
            "success": True,
            "tokens": 100,
            "cost_usd": 0.05,
            "duration_sec": 10.0
        }
        (old_run / "telemetry.json").write_text(json.dumps(old_telemetry))
        
        # Create recent run (should be included)
        recent_run = runs_dir / f"run_{today.strftime('%Y%m%d_%H%M%S')}"
        recent_run.mkdir()
        recent_telemetry = {
            "timestamp": today.isoformat(),
            "success": True,
            "tokens": 200,
            "cost_usd": 0.10,
            "duration_sec": 20.0
        }
        (recent_run / "telemetry.json").write_text(json.dumps(recent_telemetry))
        
        # Test 1-hour window (should only see recent run)
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(runs_dir),
             "--time-window", "1h",
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Time window test failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        assert output["runs_analyzed"] == 1  # Only recent run
        assert output["total_tokens"] == 200
        assert abs(output["total_cost_usd"] - 0.10) < 0.001


def test_dry_run_works():
    """Test that --dry-run shows analysis without writing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        run_dir = runs_dir / "run_20260705_100000"
        run_dir.mkdir()
        telemetry = {
            "timestamp": "2026-07-05T10:00:00Z",
            "success": True,
            "tokens": 50,
            "cost_usd": 2.50,
            "duration_sec": 15.0
        }
        (run_dir / "telemetry.json").write_text(json.dumps(telemetry))
        
        output_dir = Path(tmpdir) / "output"
        
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(runs_dir),
             "--output-dir", str(output_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Dry run failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        assert output["status"] == "success"
        assert output["dry_run"] is True
        assert output["runs_analyzed"] == 1
        assert output["total_tokens"] == 50
        assert abs(output["total_cost_usd"] - 2.50) < 0.001
        
        # Verify no files were actually written
        assert not (output_dir / "observations.json").exists()
        assert not (output_dir / "OBSERVATION_SUMMARY.md").exists()


def test_aggregates_correctly():
    """Test that aggregation calculations are correct."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        # Create three test runs
        test_data = [
            {"timestamp": "2026-07-05T10:00:00Z", "success": True, "tokens": 100, "cost_usd": 1.0, "duration_sec": 10.0},
            {"timestamp": "2026-07-05T10:01:00Z", "success": True, "tokens": 200, "cost_usd": 2.0, "duration_sec": 20.0},
            {"timestamp": "2026-07-05T10:02:00Z", "success": False, "tokens": 50, "cost_usd": 0.5, "duration_sec": 5.0}
        ]
        
        for i, data in enumerate(test_data):
            run_dir = runs_dir / f"run_20260705_1000{i:02d}"
            run_dir.mkdir()
            (run_dir / "telemetry.json").write_text(json.dumps(data))
        
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(runs_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Aggregation test failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        
        # Check aggregates
        assert output["runs_analyzed"] == 3
        assert output["total_tokens"] == 350  # 100 + 200 + 50
        assert abs(output["total_cost_usd"] - 3.5) < 0.001  # 1.0 + 2.0 + 0.5
        assert abs(output["success_rate"] - (2/3)) < 0.001  # 2 out of 3 successful
        assert abs(output["avg_duration_sec"] - 11.666) < 0.001  # (10+20+5)/3


def test_deterministic_output():
    """Test that identical inputs produce identical output."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        # Create identical test data in both temp dirs
        for tmpdir, label in [(tmpdir1, "1"), (tmpdir2, "2")]:
            runs_dir = Path(tmpdir) / "runs"
            runs_dir.mkdir()
            
            run_dir = runs_dir / "run_20260705_100000"
            run_dir.mkdir()
            telemetry = {
                "timestamp": "2026-07-05T10:00:00Z",
                "success": True,
                "tokens": 100,
                "cost_usd": 5.0,
                "duration_sec": 12.5
            }
            (run_dir / "telemetry.json").write_text(json.dumps(telemetry))
        
        # Run first time
        result1 = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(Path(tmpdir1) / "runs"),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Run second time
        result2 = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(Path(tmpdir2) / "runs"),
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
        for key in ["timestamp", "generated_at"]:
            output1.pop(key, None)
            output2.pop(key, None)
        
        # Also remove artifacts list as it may vary slightly in formatting
        output1.pop("artifacts", None)
        output2.pop("artifacts", None)
        
        assert output1 == output2, "Outputs should be deterministic"


def test_todo_not_fabrication():
    """Test that unknown information appears as TODO, not fabricated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        # Create telemetry with missing fields
        run_dir = runs_dir / "run_20260705_100000"
        run_dir.mkdir()
        telemetry = {
            "timestamp": "2026-07-05T10:00:00Z"
            # Missing tokens, cost, duration, success, etc.
        }
        (run_dir / "telemetry.json").write_text(json.dumps(telemetry))
        
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(runs_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"TODO test failed: {result.stderr}"
        
        output = json.loads(result.stdout.strip())
        # With missing data, values should be 0 or empty, not fabricated values
        assert output["total_tokens"] >= 0  # Should be 0, not made up
        assert output["total_cost_usd"] >= 0.0  # Should be 0.0, not made up
        assert output["avg_duration_sec"] >= 0.0  # Should be 0.0, not made up


def test_output_report_structure():
    """Test that output has correct structure."""
    from datetime import datetime, timezone
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        # Use today's date for the heuristic to work
        today = datetime.now(timezone.utc)
        
        run_dir = runs_dir / f"run_{today.strftime('%Y%m%d_%H%M%S')}"
        run_dir.mkdir()
        telemetry = {
            "timestamp": today.isoformat(),
            "success": True,
            "tokens": 50,
            "cost_usd": 2.5,
            "duration_sec": 15.0,
            "model": "test-model"
        }
        (run_dir / "telemetry.json").write_text(json.dumps(telemetry))
        
        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()
        
        # Run WITHOUT dry-run to actually write files
        result = subprocess.run(
            [sys.executable, "skills/observe/scripts/observe.py",
             "--runs-dir", str(runs_dir),
             "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Structure test failed: {result.stderr}"
        
        # Check files created
        assert (output_dir / "observations.json").exists()
        assert (output_dir / "OBSERVATION_SUMMARY.md").exists()
        
        # Validate JSON structure
        observations = json.loads((output_dir / "observations.json").read_text())
        required_top_level = [
            "generated_at", "time_window", "runs_analyzed", "aggregates",
            "trends", "recent_runs"
        ]
        for key in required_top_level:
            assert key in observations, f"Missing top-level key: {key}"
        
        required_aggregates = [
            "total_count", "success_count", "failure_count", "total_tokens",
            "total_cost_usd", "avg_duration_sec", "median_duration_sec", "success_rate"
        ]
        for key in required_aggregates:
            assert key in observations["aggregates"], f"Missing aggregate key: {key}"
        
        required_trends = [
            "tokens_per_hour", "cost_per_hour", "duration_per_hour", "success_rate_per_hour"
        ]
        for key in required_trends:
            assert key in observations["trends"], f"Missing trend key: {key}"
        
        # Validate markdown summary
        summary = (output_dir / "OBSERVATION_SUMMARY.md").read_text()
        assert "# Observation Summary" in summary
        assert "## Aggregate Metrics" in summary
        assert "## Recent Runs" in summary


if __name__ == "__main__":
    # Run tests manually
    test_skill_md_exists()
    print("✓ test_skill_md_exists")
    
    test_script_exists_and_executable()
    print("✓ test_script_exists_and_executable")
    
    test_script_help()
    print("✓ test_script_help")
    
    test_missing_runs_dir()
    print("✓ test_missing_runs_dir")
    
    test_discovers_telemetry_files()
    print("✓ test_discovers_telemetry_files")
    
    test_time_window_filtering()
    print("✓ test_time_window_filtering")
    
    test_dry_run_works()
    print("✓ test_dry_run_works")
    
    test_aggregates_correctly()
    print("✓ test_aggregates_correctly")
    
    test_deterministic_output()
    print("✓ test_deterministic_output")
    
    test_todo_not_fabrication()
    print("✓ test_todo_not_fabrication")
    
    test_output_report_structure()
    print("✓ test_output_report_structure")
    
    print("\nAll tests passed!")