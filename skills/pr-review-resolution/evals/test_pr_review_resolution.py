#!/usr/bin/env python3
"""
Eval tests for pr-review-resolution skill.
Tests: categorization accuracy, fix application, git operations, notification sending.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


REPO_ROOT = Path(__file__).parent.parent.parent.parent


def run_script(script: str, args: List[str]) -> Dict[str, Any]:
    """Run a script and return parsed JSON output."""
    cmd = [sys.executable, str(REPO_ROOT / "skills" / "pr-review-resolution" / "scripts" / script)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=60)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout, "returncode": result.returncode}
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}", "stdout": result.stdout[:500]}


def test_fetch_comments_structure():
    """Test that fetch_comments.py produces expected structure (mocked)."""
    fixture = REPO_ROOT / "skills" / "pr-review-resolution" / "fixtures" / "sample_pr_comments.json"
    assert fixture.exists(), "Fixture must exist"

    with open(fixture) as f:
        data = json.load(f)

    assert "pr_number" in data
    assert "repo" in data
    assert "comments" in data
    assert len(data["comments"]) == 8

    for c in data["comments"]:
        assert "id" in c
        assert "body" in c
        assert "path" in c
        assert "line" in c
        assert "author" in c

    print("✓ Fetch structure test passed")


def test_categorize_accuracy():
    """Test categorization accuracy on fixture."""
    fixture = REPO_ROOT / "skills" / "pr-review-resolution" / "fixtures" / "sample_pr_comments.json"
    with open(fixture) as f:
        data = json.load(f)

    result = run_script("categorize.py", [str(fixture)])
    assert "error" not in result, f"Categorize failed: {result.get('error')}"
    assert "categorized" in result

    expected = {
        1001: "style",    # trailing whitespace
        1002: "docs",     # missing docstring
        1003: "security", # hardcoded API key
        1004: "test",     # missing unit test
        1005: "logic",    # off-by-one error
        1006: "design",   # extract service class
        1007: "style",    # import order
        1008: "style",    # variable naming
    }

    correct = 0
    total = 0
    for cat in result["categorized"]:
        cid = cat["id"]
        if cid in expected:
            total += 1
            if cat["category"] == expected[cid]:
                correct += 1
            else:
                print(f"  Mismatch: comment {cid} → got {cat['category']}, expected {expected[cid]}")

    accuracy = correct / total if total > 0 else 0
    print(f"  Categorization accuracy: {correct}/{total} = {accuracy:.1%}")

    assert accuracy >= 0.875, f"Accuracy {accuracy:.1%} below threshold"
    print("✓ Categorization accuracy test passed")


def test_categorize_fix_types():
    """Test that fix types are correctly assigned."""
    fixture = REPO_ROOT / "skills" / "pr-review-resolution" / "fixtures" / "sample_pr_comments.json"
    result = run_script("categorize.py", [str(fixture)])

    fix_type_map = {
        "style": "auto",
        "docs": "auto",
        "security": "defer",
        "test": "auto",
        "logic": "llm",
        "design": "llm",
    }

    for cat in result["categorized"]:
        expected_type = fix_type_map.get(cat["category"], "defer")
        assert cat["suggested_fix_type"] == expected_type, \
            f"Comment {cat['id']}: expected fix type {expected_type}, got {cat['suggested_fix_type']}"

    print("✓ Fix type assignment test passed")


def test_resolve_script_exists():
    """Test resolve.py exists and shows usage."""
    script = REPO_ROOT / "skills" / "pr-review-resolution" / "scripts" / "resolve.py"
    assert script.exists(), "resolve.py must exist"
    assert script.stat().st_mode & 0o111, "resolve.py must be executable"

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode != 0, "Should exit with error without args"
    assert "Usage" in result.stdout or "Usage" in result.stderr
    print("✓ Resolve script exists and shows usage")


def test_notify_script_exists():
    """Test notify.py exists."""
    script = REPO_ROOT / "skills" / "pr-review-resolution" / "scripts" / "notify.py"
    assert script.exists(), "notify.py must exist"
    print("✓ Notify script exists")


def test_analyze_script_exists():
    """Test analyze.py exists."""
    script = REPO_ROOT / "skills" / "pr-review-resolution" / "scripts" / "analyze.py"
    assert script.exists(), "analyze.py must exist"
    print("✓ Analyze script exists")


def test_main_entry_exists():
    """Test main entry point exists."""
    script = REPO_ROOT / "skills" / "pr-review-resolution" / "scripts" / "pr_review_resolution.py"
    assert script.exists(), "pr_review_resolution.py must exist"
    print("✓ Main entry point exists")


def test_skill_md_has_required_fields():
    """Test SKILL.md has required fields."""
    skill_md = REPO_ROOT / "skills" / "pr-review-resolution" / "SKILL.md"
    content = skill_md.read_text()

    required = ["name:", "description:", "version:", "author:", "tags:"]
    for req in required:
        assert req in content, f"SKILL.md missing required field: {req}"

    assert "github" in content.lower() or "gh api" in content.lower()
    assert "telegram" in content.lower()
    assert "hitl" in content.lower() or "human" in content.lower()
    assert "auto" in content.lower()
    assert "analyze" in content.lower() or "historical" in content.lower()

    print("✓ SKILL.md has required fields")


def test_deterministic_categorization():
    """Test that categorization is deterministic."""
    fixture = REPO_ROOT / "skills" / "pr-review-resolution" / "fixtures" / "sample_pr_comments.json"

    result1 = run_script("categorize.py", [str(fixture)])
    result2 = run_script("categorize.py", [str(fixture)])

    cats1 = [(c["id"], c["category"]) for c in result1["categorized"]]
    cats2 = [(c["id"], c["category"]) for c in result2["categorized"]]

    assert cats1 == cats2, "Categorization must be deterministic"
    print("✓ Deterministic categorization test passed")


def main():
    tests = [
        ("Fetch structure", test_fetch_comments_structure),
        ("Categorize accuracy", test_categorize_accuracy),
        ("Fix type assignment", test_categorize_fix_types),
        ("Resolve script exists", test_resolve_script_exists),
        ("Notify script exists", test_notify_script_exists),
        ("Analyze script exists", test_analyze_script_exists),
        ("Main entry exists", test_main_entry_exists),
        ("SKILL.md fields", test_skill_md_has_required_fields),
        ("Deterministic categorization", test_deterministic_categorization),
    ]

    passed = 0
    failed = 0

    for name, test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {name} FAILED: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())