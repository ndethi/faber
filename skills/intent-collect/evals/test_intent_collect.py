#!/usr/bin/env python3
"""
Eval for the intent-collect skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Produces spec.md, trajectory.md, scope-baseline.md deterministically
4. Handles unknowns as TODO:, never fabricates
5. Correctly maps production_context to trajectory strictness
"""
import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/intent-collect/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"
    
    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "intent-collect" in content, "SKILL.md must mention intent-collect"
    assert "spec.md" in content, "SKILL.md must mention spec.md output"
    assert "trajectory.md" in content, "SKILL.md must mention trajectory.md output"
    assert "scope-baseline.md" in content, "SKILL.md must mention scope-baseline.md output"
    print("✓ SKILL.md exists with required fields")

def test_script_exists_and_executable() -> None:
    """Test that intent_collect.py exists and is executable."""
    script = Path("skills/intent-collect/scripts/intent_collect.py")
    assert script.exists(), "intent_collect.py must exist"
    assert os.access(str(script), os.X_OK), "intent_collect.py must be executable"
    print("✓ intent_collect.py exists and is executable")

def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/intent-collect/scripts/intent_collect.py"],
        capture_output=True,
        text=True,
    )
    # Should fail because required args missing
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    print("✓ Script shows usage without required args")

def test_output_structure_rohaki_fixture() -> None:
    """Test that running on Rohaki fixture produces expected output structure."""
    # Use the existing fixtures/rohaki directory as input context
    fixture_dir = Path("fixtures/rohaki")
    assert fixture_dir.exists(), "Fixture directory must exist"
    
    # Read the spec.md from fixture as our client_context
    client_context = (fixture_dir / "spec.md").read_text()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/intent-collect/scripts/intent_collect.py",
            "--client-context", client_context,
            "--production-context", "normal",
            "--output-dir", tmpdir
        ], capture_output=True, text=True, timeout=30)
        
        # Should succeed
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            # If not JSON, maybe it's the old format - let's check if files were created
            output = {}
            
        # Check that output files exist
        assert (Path(tmpdir) / "spec.md").exists(), "spec.md must be created"
        assert (Path(tmpdir) / "trajectory.md").exists(), "trajectory.md must be created"
        assert (Path(tmpdir) / "scope-baseline.md").exists(), "scope-baseline.md must be created"
        
        # Check spec.md has acceptance criteria
        spec_content = (Path(tmpdir) / "spec.md").read_text()
        assert "Acceptance Criteria" in spec_content, "spec.md must have Acceptance Criteria section"
        assert "SPEC-" in spec_content, "spec.md must have IDed acceptance criteria"
        
        # Check trajectory.md has strictness
        traj_content = (Path(tmpdir) / "trajectory.md").read_text()
        assert "strictness:" in traj_content, "trajectory.md must show strictness"
        assert "ordered" in traj_content.lower(), "trajectory.md should have ordered strictness for normal context"
        
        # Check scope-baseline.md
        scope_content = (Path(tmpdir) / "scope-baseline.md").read_text()
        assert "Scope Baseline" in scope_content, "scope-baseline.md must have header"
        assert "TODO: Review with client." in scope_content, "scope-baseline.md must have TODO for HITL"
        
    print("✓ Output structure test passed on Rohaki fixture")

def test_determinism() -> None:
    """Test that two runs on identical inputs yield identical structure."""
    client_context = "Goal: Build a blog. Audience: Writers. Constraints: Must be SEO friendly."
    
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        # Run first time
        result1 = subprocess.run([
            sys.executable,
            "skills/intent-collect/scripts/intent_collect.py",
            "--client-context", client_context,
            "--production-context", "prototype",
            "--output-dir", tmpdir1
        ], capture_output=True, text=True, timeout=30)
        
        # Run second time
        result2 = subprocess.run([
            sys.executable,
            "skills/intent-collect/scripts/intent_collect.py",
            "--client-context", client_context,
            "--production-context", "prototype",
            "--output-dir", tmpdir2
        ], capture_output=True, text=True, timeout=30)
        
        assert result1.returncode == 0 and result2.returncode == 0, "Both runs should succeed"
        
        # Compare file contents (should be identical)
        for filename in ["spec.md", "trajectory.md", "scope-baseline.md"]:
            content1 = (Path(tmpdir1) / filename).read_text()
            content2 = (Path(tmpdir2) / filename).read_text()
            assert content1 == content2, f"{filename} should be identical between runs"
            
    print("✓ Determinism test passed")

def test_todo_not_fabrication() -> None:
    """Test that unknowns appear as TODO:, never fabricated details."""
    client_context = "Goal: Build something. Audience: Someone."
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/intent-collect/scripts/intent_collect.py",
            "--client-context", client_context,
            "--production-context", "normal",
            "--output-dir", tmpdir
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0, "Should succeed"
        
        scope_content = (Path(tmpdir) / "scope-baseline.md").read_text()
        # Should have TODO for review
        assert "TODO: Review with client." in scope_content, "Should have TODO for HITL"
        
        # Should NOT contain specific fabricated details like specific tech choices
        # unless they were in the input (which they weren't)
        assert "react" not in scope_content.lower(), "Should not invent React"
        assert "vue" not in scope_content.lower(), "Should not invent Vue"
        assert "wordpress" not in scope_content.lower(), "Should not invent WordPress"
        
    print("✓ TODO/not-fabrication test passed")

def test_production_context_mapping() -> None:
    """Test that production_context correctly maps to trajectory strictness."""
    client_context = "Goal: Build an app. Audience: Users."
    test_cases = [
        ("prototype", "partial"),
        ("normal", "ordered"),
        ("client-production", "exact")
    ]
    
    for prod_context, expected_strictness in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                sys.executable,
                "skills/intent-collect/scripts/intent_collect.py",
                "--client-context", client_context,
                "--production-context", prod_context,
                "--output-dir", tmpdir
            ], capture_output=True, text=True, timeout=30)
            
            assert result.returncode == 0, f"Failed for {prod_context}"
            
            traj_content = (Path(tmpdir) / "trajectory.md").read_text()
            assert f"strictness: {expected_strictness}" in traj_content, \
                f"Expected strictness {expected_strictness} for {prod_context}"
                
    print("✓ Production context mapping test passed")

def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_output_structure_rohaki_fixture,
        test_determinism,
        test_todo_not_fabrication,
        test_production_context_mapping,
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