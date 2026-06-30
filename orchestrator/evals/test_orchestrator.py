#!/usr/bin/env python3
"""
Eval for the orchestrator.

Tests that the orchestrator:
1. Loads run plans correctly
2. Invokes skills in sequence
3. Writes valid telemetry against schema
4. Includes trajectory fields (expected_trajectory, trajectory_strictness)
5. Handles errors gracefully
6. Produces deterministic output for same inputs
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_orchestrator_exists():
    """Test that orchestrator.py exists and is executable."""
    orchestrator = Path("orchestrator/orchestrator.py")
    assert orchestrator.exists(), "orchestrator.py must exist"
    assert orchestrator.stat().st_mode & 0o111, "orchestrator.py must be executable"
    print("✓ orchestrator.py exists and is executable")


def test_orchestrator_help():
    """Test that orchestrator shows usage without args."""
    result = subprocess.run(
        [sys.executable, "orchestrator/orchestrator.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when no args"
    assert "Usage" in result.stdout or "Usage" in result.stderr, "Should show usage"
    print("✓ orchestrator.py shows usage without args")


def test_orchestrator_invalid_plan():
    """Test that orchestrator handles invalid plan gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"invalid": "plan"}')
        plan_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "orchestrator/orchestrator.py", plan_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0, "Should fail for invalid plan"
        output = json.loads(result.stdout.strip())
        assert output.get("success", True) is False or "error" in output, "Should return error"
        print("✓ orchestrator handles invalid plan gracefully")
    finally:
        Path(plan_path).unlink(missing_ok=True)


def test_orchestrator_runs_noop_plan():
    """Test that orchestrator successfully runs the no-op plan."""
    result = subprocess.run(
        [sys.executable, "orchestrator/orchestrator.py", "runs/noop-plan.json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"Orchestrator failed: {result.stderr}"

    output = json.loads(result.stdout.strip())
    assert "run_id" in output, "Output must include run_id"
    assert "telemetry_path" in output, "Output must include telemetry_path"

    # Verify telemetry file exists and is valid
    telemetry_path = Path(output["telemetry_path"])
    assert telemetry_path.exists(), f"Telemetry file not found: {telemetry_path}"

    with open(telemetry_path) as f:
        telemetry = json.load(f)

    # Required fields per schema
    required = ["run_id", "timestamp", "skills", "model", "tokens", "cost", "deploy_status"]
    for field in required:
        assert field in telemetry, f"Telemetry missing required field: {field}"

    # Trajectory fields (new per build.01-core)
    assert "expected_trajectory" in telemetry, "Telemetry must have expected_trajectory"
    assert "trajectory_strictness" in telemetry, "Telemetry must have trajectory_strictness"
    assert telemetry["trajectory_strictness"] in ["exact", "ordered", "partial"]

    print("✓ orchestrator runs no-op plan and writes valid telemetry with trajectory fields")


def test_telemetry_validates_against_schema():
    """Test that generated telemetry validates against schema."""
    # Run no-op plan
    result = subprocess.run(
        [sys.executable, "orchestrator/orchestrator.py", "runs/noop-plan.json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout.strip())
    telemetry_path = Path(output["telemetry_path"])

    with open(telemetry_path) as f:
        telemetry = json.load(f)

    # Load schema
    with open("runs/telemetry.schema.json") as f:
        schema = json.load(f)

    # Basic schema validation (check required fields, types)
    required = schema.get("required", [])
    for field in required:
        assert field in telemetry, f"Missing required field: {field}"

    # Check skills array structure
    assert isinstance(telemetry["skills"], list), "skills must be array"
    for skill in telemetry["skills"]:
        assert "skill_id" in skill
        assert "status" in skill
        assert skill["status"] in ["success", "failure", "skipped"]
        assert "duration_ms" in skill
        assert isinstance(skill["duration_ms"], int)

    # Check trajectory fields
    assert isinstance(telemetry["expected_trajectory"], list)
    assert telemetry["trajectory_strictness"] in ["exact", "ordered", "partial"]

    # Check tokens structure
    assert isinstance(telemetry["tokens"], dict)
    assert all(k in telemetry["tokens"] for k in ["prompt", "completion", "total"])

    print("✓ Telemetry validates against schema structure")


def test_orchestrator_deterministic():
    """Test that two runs with same plan produce same structure (deterministic)."""
    # Use temp output dirs to avoid overwriting
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        # Copy noop-plan.json to temp dirs with unique run_ids
        with open("runs/noop-plan.json") as f:
            plan = json.load(f)
        
        plan1 = plan.copy()
        plan1["run_id"] = "noop-test-deterministic-1"
        plan_path1 = Path(tmpdir1) / "noop-plan-1.json"
        plan_path1.write_text(json.dumps(plan1))
        
        plan2 = plan.copy()
        plan2["run_id"] = "noop-test-deterministic-2"
        plan_path2 = Path(tmpdir2) / "noop-plan-2.json"
        plan_path2.write_text(json.dumps(plan2))

        # Run twice with different output dirs
        result1 = subprocess.run(
            [sys.executable, "orchestrator/orchestrator.py", str(plan_path1)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path.cwd(),
        )
        result2 = subprocess.run(
            [sys.executable, "orchestrator/orchestrator.py", str(plan_path2)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path.cwd(),
        )

        assert result1.returncode == 0
        assert result2.returncode == 0

        out1 = json.loads(result1.stdout.strip())
        out2 = json.loads(result2.stdout.strip())

        # Telemetry files should have same structure
        with open(out1["telemetry_path"]) as f:
            t1 = json.load(f)
        with open(out2["telemetry_path"]) as f:
            t2 = json.load(f)

        # Same structure (run_id will differ, but skills array structure same)
        assert len(t1["skills"]) == len(t2["skills"]), "Same number of skills"
        for s1, s2 in zip(t1["skills"], t2["skills"]):
            assert s1["skill_id"] == s2["skill_id"]
            assert s1["status"] == s2["status"]

        assert t1["expected_trajectory"] == t2["expected_trajectory"]
        assert t1["trajectory_strictness"] == t2["trajectory_strictness"]
        assert t1["model"] == t2["model"]

        print("✓ Orchestrator produces deterministic structure for same input")


def test_schema_has_trajectory_fields():
    """Test that telemetry.schema.json includes trajectory fields."""
    with open("runs/telemetry.schema.json") as f:
        schema = json.load(f)

    props = schema.get("properties", {})
    assert "expected_trajectory" in props, "Schema must have expected_trajectory"
    assert "trajectory_strictness" in props, "Schema must have trajectory_strictness"

    # Check expected_trajectory structure
    et = props["expected_trajectory"]
    assert et["type"] == "array"
    assert "items" in et
    item_props = et["items"]["properties"]
    assert "skill_id" in item_props
    assert "checkpoint" in item_props
    assert "gate" in item_props
    assert "strictness" in item_props

    # Check trajectory_strictness enum
    ts = props["trajectory_strictness"]
    assert ts["enum"] == ["exact", "ordered", "partial"]

    print("✓ Schema includes trajectory fields with correct structure")


def main():
    tests = [
        test_orchestrator_exists,
        test_orchestrator_help,
        test_orchestrator_invalid_plan,
        test_orchestrator_runs_noop_plan,
        test_telemetry_validates_against_schema,
        test_orchestrator_deterministic,
        test_schema_has_trajectory_fields,
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
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())