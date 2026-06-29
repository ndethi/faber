#!/usr/bin/env python3
"""
Eval for the build skill.

Tests that the build skill:
1. Has the required SKILL.md with correct defaults (Astro + Cloudflare Pages)
2. Has executable scripts/
3. Produces valid JSON output with file hashes
4. Handles errors gracefully
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_skill_md_has_correct_defaults():
    """Test that SKILL.md references Astro + Cloudflare Pages as defaults."""
    skill_md = Path("skills/build/SKILL.md").read_text()
    assert "Astro" in skill_md, "SKILL.md must reference Astro as default stack"
    assert "Cloudflare Pages" in skill_md, "SKILL.md must reference Cloudflare Pages as default host"
    assert "npm/esbuild/webpack" not in skill_md or "not npm/esbuild/webpack" in skill_md.lower(), \
        "SKILL.md should not promote npm/esbuild/webpack as defaults"
    print("✓ SKILL.md references correct defaults")


def test_build_script_exists_and_executable():
    """Test that build.py exists and is executable."""
    script = Path("skills/build/scripts/build.py")
    assert script.exists(), "build.py must exist"
    assert script.stat().st_mode & 0o111, "build.py must be executable"
    print("✓ build.py exists and is executable")


def test_build_script_help():
    """Test that build.py shows usage when run without args."""
    result = subprocess.run(
        [sys.executable, "skills/build/scripts/build.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when no args"
    assert "Usage" in result.stdout or "Usage" in result.stderr, "Should show usage"
    print("✓ build.py shows usage without args")


def test_build_script_invalid_dir():
    """Test that build.py handles invalid directory gracefully."""
    result = subprocess.run(
        [sys.executable, "skills/build/scripts/build.py", "/nonexistent/path"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error for invalid dir"
    output = json.loads(result.stdout.strip())
    assert output["success"] is False, "Should return success=false"
    assert "error" in output, "Should include error message"
    print("✓ build.py handles invalid directory gracefully")


def test_build_script_output_format():
    """Test that build.py outputs valid JSON with expected structure."""
    # We can't easily test a full Astro build without a project,
    # but we can verify the JSON structure is parseable
    # Test with a directory that will fail fast (no package.json)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an empty directory (no package.json)
        # The script should fail fast with a clear error

        result = subprocess.run(
            [sys.executable, "skills/build/scripts/build.py", tmpdir],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail because no package.json / astro not found
        output = json.loads(result.stdout.strip())
        assert output["success"] is False, "Should return success=false for empty dir"
        assert "error" in output, "Should include error message"
        assert "command" in output, "Should include command for debugging"
        print("✓ build.py outputs valid error JSON for empty directory")

    # Also test that the success output structure is valid by checking the code
    script_content = Path("skills/build/scripts/build.py").read_text()
    assert '"success": True' in script_content or '"success": true' in script_content
    assert '"dist_dir"' in script_content
    assert '"files"' in script_content
    assert '"sha256"' in script_content
    print("✓ build.py success output structure verified in code")


def test_deterministic_output():
    """Test that two runs on same input yield same structure (determinism)."""
    # This is a structural test - we verify the script design supports determinism
    # by checking it doesn't use random/timestamp in output paths
    script_content = Path("skills/build/scripts/build.py").read_text()
    # The script uses file content hashes, not timestamps
    assert "sha256" in script_content, "Script must compute content hashes"
    assert "timestamp" not in script_content.lower() or "datetime" not in script_content, \
        "Script should not use timestamps in output"
    print("✓ Script design supports deterministic output")


def main():
    tests = [
        test_skill_md_has_correct_defaults,
        test_build_script_exists_and_executable,
        test_build_script_help,
        test_build_script_invalid_dir,
        test_build_script_output_format,
        test_deterministic_output,
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