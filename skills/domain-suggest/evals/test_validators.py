#!/usr/bin/env python3
"""
Tests for the domain-suggest validators module.
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = str(Path("skills/domain-suggest/scripts").absolute())
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

def test_import() -> None:
    """Test that validators module can be imported."""
    try:
        import validators
        print("✓ validators module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import validators: {e}")
        raise

def test_validate_brief_input() -> None:
    """Test the validate_brief_input function."""
    try:
        from validators import validate_brief_input
        
        # Test valid brief
        valid_brief = {
            "spec": "Track bamboo sustainability metrics",
            "trajectory": "Prototype -> Beta -> Launch",
            "scope-baseline": "Basic tracking of bamboo plots with carbon measurements"
        }
        
        is_valid, errors = validate_brief_input(valid_brief)
        assert is_valid, f"Valid brief should pass validation. Errors: {errors}"
        print("✓ Valid brief passes validation")
        
        # Test invalid brief (empty)
        invalid_brief = {
            "spec": "",
            "trajectory": "",
            "scope-baseline": ""
        }
        
        is_valid, errors = validate_brief_input(invalid_brief)
        assert not is_valid, "Empty brief should fail validation"
        assert len(errors) > 0, "Should have error messages"
        print("✓ Empty brief fails validation as expected")
        
        # Test brief with only one field filled
        partial_brief = {
            "spec": "Only spec provided",
            "trajectory": "",
            "scope-baseline": ""
        }
        
        is_valid, errors = validate_brief_input(partial_brief)
        assert is_valid, "Brief with one filled field should pass"
        print("✓ Partial valid brief passes validation")
        
    except Exception as e:
        print(f"✗ Error in validate_brief_input test: {e}")
        # Don't fail - implementation might differ
        raise

def test_validate_output_structure() -> None:
    """Test the validate_output_structure function."""
    try:
        from validators import validate_output_structure
        
        # Test valid output
        valid_output = {
            "status": "success",
            "artifacts": ["domain-recommendations.md"],
            "domain_candidates": [
                {
                    "domain": "bambooeco.com",
                    "rationale": "Available, short, memorable, .com TLD",
                    "availability": "available"
                },
                {
                    "domain": "bambooscan.org",
                    "rationale": "Contains relevant keyword, .org suitable for eco-focus",
                    "availability": "unavailable"
                },
                {
                    "domain": "ecobamboo.dev",
                    "rationale": "Availability unknown - requires manual verification",
                    "availability": "unknown"
                }
            ],
            "hitl_gate_required": False,
            "hitl_gate_passed": True
        }
        
        is_valid, errors = validate_output_structure(valid_output)
        assert is_valid, f"Valid output should pass. Errors: {errors}"
        print("✓ Valid output structure passes validation")
        
        # Test invalid output (wrong number of candidates)
        invalid_output = valid_output.copy()
        invalid_output["domain_candidates"] = [
            {
                "domain": "test.com",
                "rationale": "Test domain",
                "availability": "available"
            }
            # Only one candidate instead of three
        ]
        
        is_valid, errors = validate_output_structure(invalid_output)
        assert not is_valid, "Output with wrong number of candidates should fail"
        print("✓ Invalid output (wrong candidate count) fails validation")
        
    except Exception as e:
        print(f"✗ Error in validate_output_structure test: {e}")
        # Don't fail - implementation might differ
        raise

if __name__ == "__main__":
    test_import()
    test_validate_brief_input()
    test_validate_output_structure()
    print("Validator tests completed")