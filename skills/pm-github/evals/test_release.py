#!/usr/bin/env python3
"""
Test for release version calculation and notes generation.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cli import calculate_version_bump, compute_next_tag, generate_release_notes


def test_calculate_version_bump_major():
    """Test major bump for breaking changes."""
    prs = [
        {"title": "feat!: breaking change to API", "labels": []},
        {"title": "fix: minor bug", "labels": []},
    ]
    assert calculate_version_bump(prs) == "major"
    print("✅ test_calculate_version_bump_major passed")


def test_calculate_version_bump_minor():
    """Test minor bump for features."""
    prs = [
        {"title": "feat: add new feature", "labels": []},
        {"title": "fix: minor bug", "labels": []},
    ]
    assert calculate_version_bump(prs) == "minor"
    print("✅ test_calculate_version_bump_minor passed")


def test_calculate_version_bump_patch():
    """Test patch bump for fixes only."""
    prs = [
        {"title": "fix: minor bug", "labels": []},
        {"title": "chore: update deps", "labels": []},
    ]
    assert calculate_version_bump(prs) == "patch"
    print("✅ test_calculate_version_bump_patch passed")


def test_calculate_version_bump_explicit():
    """Test explicit bump override."""
    prs = [{"title": "fix: bug", "labels": []}]
    assert calculate_version_bump(prs, "major") == "major"
    assert calculate_version_bump(prs, "minor") == "minor"
    assert calculate_version_bump(prs, "patch") == "patch"
    print("✅ test_calculate_version_bump_explicit passed")


def test_compute_next_tag():
    """Test next tag computation."""
    assert compute_next_tag(None, "patch") == "v0.1.0"
    assert compute_next_tag("v0.1.0", "patch") == "v0.1.1"
    assert compute_next_tag("v0.1.0", "minor") == "v0.2.0"
    assert compute_next_tag("v0.1.0", "major") == "v1.0.0"
    assert compute_next_tag("v1.2.3", "patch") == "v1.2.4"
    assert compute_next_tag("v1.2.3", "minor") == "v1.3.0"
    assert compute_next_tag("v1.2.3", "major") == "v2.0.0"
    print("✅ test_compute_next_tag passed")


def test_generate_release_notes():
    """Test release notes generation."""
    prs = [
        {"title": "feat: add new feature", "labels": [{"name": "enhancement"}], "number": 1},
        {"title": "fix: resolve bug", "labels": [{"name": "bug"}], "number": 2},
        {"title": "docs: update readme", "labels": [{"name": "docs"}], "number": 3},
        {"title": "chore: update deps", "labels": [], "number": 4},
        {"title": "feat!: breaking API change", "labels": [], "number": 5},
    ]
    notes = generate_release_notes(prs, "major")
    
    assert "## Changes" in notes
    assert "*Version bump: major*" in notes
    assert "### ⚠️ Breaking Changes" in notes
    assert "feat!: breaking API change" in notes
    assert "### ✨ Features" in notes
    assert "feat: add new feature" in notes
    assert "### 🐛 Bug Fixes" in notes
    assert "fix: resolve bug" in notes
    assert "### 📝 Documentation" in notes
    assert "docs: update readme" in notes
    assert "### 🔧 Other" in notes
    assert "chore: update deps" in notes
    
    print("✅ test_generate_release_notes passed")


def test_generate_release_notes_empty():
    """Test release notes with no PRs."""
    notes = generate_release_notes([], "patch")
    assert "## Changes" in notes
    assert "*Version bump: patch*" in notes
    print("✅ test_generate_release_notes_empty passed")


def main():
    tests = [
        test_calculate_version_bump_major,
        test_calculate_version_bump_minor,
        test_calculate_version_bump_patch,
        test_calculate_version_bump_explicit,
        test_compute_next_tag,
        test_generate_release_notes,
        test_generate_release_notes_empty,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())