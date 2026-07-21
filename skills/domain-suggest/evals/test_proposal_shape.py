#!/usr/bin/env python3
"""
Test that the output proposals have the correct shape and content.
"""

import json
import tempfile
from pathlib import Path
import subprocess
import sys

def test_output_has_correct_shape() -> None:
    """Test that output matches the expected schema exactly."""
    # Create test input
    test_brief = {
        "spec": "Web application for tracking renewable energy credits",
        "trajectory": "Prototype: Basic tracking -> MVP: Market dashboard -> Enterprise: API & reporting",
        "scope-baseline": "Track REC purchases, sales, and retirement with basic reporting"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write input files
        (tmpdir_path / "spec.md").write_text(test_brief["spec"])
        (tmpdir_path / "trajectory.md").write_text(test_brief["trajectory"])
        (tmpdir_path / "scope-baseline.md").write_text(test_brief["scope-baseline"])
        
        # Run the command
        result = subprocess.run([
            sys.executable,
            "skills/domain-suggest/scripts/cli.py",
            "--input-dir", str(tmpdir_path),
            "--output-dir", tmpdir,
            "--dry-run"
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            # If we can't parse JSON, we can't test the structure
            raise AssertionError(f"Output should be valid JSON, got: {result.stdout[:200]}...")
        
        # === Check top-level structure ===
        expected_top_level = {
            "status": str,
            "artifacts": list,
            "domain_candidates": list,
            "hitl_gate_required": bool,
            "hitl_gate_passed": bool
        }
        
        for key, expected_type in expected_top_level.items():
            assert key in output, f"Missing required key: {key}"
            assert isinstance(output[key], expected_type), \
                f"Key '{key}' should be {expected_type.__name__}, got {type(output[key])}"
        
        # === Check status value ===
        assert output["status"] in ["success", "error"], \
            f"Status should be 'success' or 'error', got: {output['status']}"
        
        # If status is error, we might not have candidates - but for valid input we expect success
        # For now, we'll just check the structure if it's success
        if output["status"] == "success":
            # === Check artifacts ===
            assert isinstance(output["artifacts"], list), "Artifacts should be a list"
            for i, artifact in enumerate(output["artifacts"]):
                assert isinstance(artifact, str), f"artifacts[{i}] should be string"
            
            # === Check domain_candidates ===
            candidates = output["domain_candidates"]
            assert isinstance(candidates, list), "domain_candidates should be a list"
            assert len(candidates) == 3, f"Should have exactly 3 candidates, got {len(candidates)}"
            
            for i, candidate in enumerate(candidates):
                assert isinstance(candidate, dict), f"candidate[{i}] should be a dict"
                
                # Check required fields
                required_fields = {
                    "domain": str,
                    "rationale": str,
                    "availability": str
                }
                
                for field, expected_type in required_fields.items():
                    assert field in candidate, f"candidate[{i}] missing required field: {field}"
                    assert isinstance(candidate[field], expected_type), \
                        f"candidate[{i}].{field} should be {expected_type.__name__}, got {type(candidate[field])}"
                
                # Validate domain format
                domain = candidate["domain"]
                assert isinstance(domain, str) and len(domain) > 0, \
                    f"candidate[{i}].domain should be non-empty string"
                
                # Basic domain format check (should contain at least one dot)
                assert "." in domain, f"candidate[{i}].domain should contain a dot: {domain}"
                # Should not start or end with dot
                assert not domain.startswith(".") and not domain.endswith("."), \
                    f"candidate[{i}].domain should not start or end with dot: {domain}"
                
                # Validate rationale
                rationale = candidate["rationale"]
                assert isinstance(rationale, str) and len(rationale.strip()) > 0, \
                    f"candidate[{i}].rationale should be non-empty string"
                
                # Validate availability
                avail = candidate["availability"]
                assert avail in ["available", "unavailable", "unknown"], \
                    f"candidate[{i}].availability should be 'available', 'unavailable', or 'unknown', got: {avail}"
        
        # === Check HITL fields ===
        assert isinstance(output["hitl_gate_required"], bool), \
            "hitl_gate_required should be boolean"
        assert isinstance(output["hitl_gate_passed"], bool), \
            "hitl_gate_passed should be boolean"
        
        print("✓ Output structure is correct")

def test_domain_candidates_are_different() -> None:
    """Test that the three domain candidates are actually different."""
    test_brief = {
        "spec": "Distributed ledger for carbon credit tracking",
        "trajectory": "Private network -> Consortium -> Public mainnet",
        "scope-baseline": "Track carbon credits on blockchain with IoT integration"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write input files
        (tmpdir_path / "spec.md").write_text(test_brief["spec"])
        (tmpdir_path / "trajectory.md").write_text(test_brief["trajectory"])
        (tmpdir_path / "scope-baseline.md").write_text(test_brief["scope-baseline"])
        
        # Run the command
        result = subprocess.run([
            sys.executable,
            "skills/domain-suggest/scripts/cli.py",
            "--input-dir", str(tmpdir_path),
            "--output-dir", tmpdir,
            "--dry-run"
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Parse JSON output
        output = json.loads(result.stdout.strip())
        assert output["status"] == "success", "Expected success for valid input"
        
        candidates = output["domain_candidates"]
        assert len(candidates) == 3, "Should have exactly 3 candidates"
        
        # Extract domains
        domains = [c["domain"].lower() for c in candidates]
        
        # Check that all domains are different
        assert len(set(domains)) == 3, \
            f"All three domains should be different, got: {domains}"
        
        # Optionally, check that they look like reasonable domain suggestions
        for domain in domains:
            # Should contain at least one letter
            assert any(c.isalpha() for c in domain), \
                f"Domain should contain at least one letter: {domain}"
            # Should not be too long
            assert len(domain) <= 30, f"Domain seems too long: {domain}"
        
        print("✓ All three domain candidates are distinct")

if __name__ == "__main__":
    test_output_has_correct_shape()
    test_domain_candidates_are_different()
    print("All proposal shape tests passed!")