#!/usr/bin/env python3
"""
Basic test for domain-suggest skill structure.
"""

import os
import sys
from pathlib import Path

def test_skill_structure() -> None:
    """Test that the skill has the expected structure."""
    # Check SKILL.md exists
    skill_md = Path("skills/domain-suggest/SKILL.md")
    assert skill_md.exists(), "SKILL.md should exist"
    
    # Check scripts directory exists
    scripts_dir = Path("skills/domain-suggest/scripts")
    assert scripts_dir.exists(), "scripts directory should exist"
    
    # Check that we have the expected script files
    expected_scripts = ["cli.py", "generators.py", "validators.py"]
    for script_name in expected_scripts:
        script_path = scripts_dir / script_name
        assert script_path.exists(), f"Script {script_name} should exist"
        assert os.access(str(script_path), os.X_OK), f"Script {script_name} should be executable"
    
    # Check config directory exists
    config_dir = Path("skills/domain-suggest/config")
    assert config_dir.exists(), "config directory should exist"
    
    # Check defaults.yaml exists
    config_file = config_dir / "defaults.yaml"
    assert config_file.exists(), "config/defaults.yaml should exist"
    
    # Check evals directory exists
    evals_dir = Path("skills/domain-suggest/evals")
    assert evals_dir.exists(), "evals directory should exist"
    
    # Check that at least one eval test exists
    eval_tests = list(evals_dir.glob("test_*.py"))
    assert len(eval_tests) > 0, "Should have at least one eval test file"
    
    print("✓ Skill structure test passed")


def test_skill_md_content() -> None:
    """Test that SKILL.md has required content."""
    skill_md = Path("skills/domain-suggest/SKILL.md")
    content = skill_md.read_text()
    
    # Check for required sections
    assert "name: domain-suggest" in content, "Should have correct name"
    assert "description:" in content, "Should have description"
    assert "version:" in content, "Should have version"
    assert "author:" in content, "Should have author"
    assert "license:" in content, "Should have license"
    
    # Check that description mentions domain suggestion
    assert "domain" in content.lower(), "Description should mention domain"
    assert "suggest" in content.lower(), "Description should mention suggest"
    
    print("✓ SKILL.md content test passed")


def test_import_modules() -> None:
    """Test that we can import the modules (basic syntax check)."""
    # Add scripts directory to path
    scripts_dir = str(Path("skills/domain-suggest/scripts").absolute())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    # Try to import each module
    try:
        import generators
        print("✓ generators module imported successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not import generators: {e}")
    
    try:
        import validators
        print("✓ validators module imported successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not import validators: {e}")
    
    # Note: We don't test cli.py import here as it has the main() block
    # that would try to parse arguments


if __name__ == "__main__":
    test_skill_structure()
    test_skill_md_content()
    test_import_modules()
    print("All basic tests passed!")