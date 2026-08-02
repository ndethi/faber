#!/usr/bin/env python3
"""
No-op Skill Eval
"""

import json
import subprocess
import sys
from pathlib import Path


def test_noop_skill_exists():
    """Test that noop skill exists with required files."""
    skill_dir = Path("skills/noop")
    assert skill_dir.exists(), "skills/noop directory missing"
    assert (skill_dir / "scripts" / "noop.py").exists(), "noop.py script missing"
    print("✓ Noop skill structure exists")


def test_noop_script_executable():
    """Test that noop script is executable and runs successfully."""
    result = subprocess.run(
        [sys.executable, "skills/noop/scripts/noop.py"],
        capture_output=True,
        text=True,
        cwd="."
    )
    assert result.returncode == 0, f"Noop script failed: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["success"] is True, "Noop should return success=True"
    assert "message" in output, "Noop output should have message"
    assert "run_id" in output, "Noop output should have run_id"
    print("✓ Noop script executes successfully")


def test_noop_deterministic():
    """Test that noop produces deterministic output."""
    result1 = subprocess.run(
        [sys.executable, "skills/noop/scripts/noop.py"],
        capture_output=True,
        text=True,
        cwd="."
    )
    result2 = subprocess.run(
        [sys.executable, "skills/noop/scripts/noop.py"],
        capture_output=True,
        text=True,
        cwd="."
    )
    
    # Both should succeed
    assert result1.returncode == 0
    assert result2.returncode == 0
    
    # Output should be identical (except run_id might differ, but structure same)
    out1 = json.loads(result1.stdout)
    out2 = json.loads(result2.stdout)
    
    # Check structure is same
    assert set(out1.keys()) == set(out2.keys()), "Output keys should match"
    assert out1["success"] == out2["success"] == True
    assert out1["message"] == out2["message"]
    print("✓ Noop output is deterministic")


if __name__ == "__main__":
    test_noop_skill_exists()
    test_noop_script_executable()
    test_noop_deterministic()
    print("\n✓ All noop evals passed")