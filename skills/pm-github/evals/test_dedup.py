#!/usr/bin/env python3
"""
Test deduplication idempotency for pm-github skill.

Tests that dedup keys are stable across re-runs and that
existing issues are correctly detected.
"""

import json
import hashlib
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from dedup import (
    generate_dedup_key,
    generate_issue_dedup_key,
    format_issue_with_dedup,
    extract_dedup_keys_from_issues,
)


def test_dedup_key_deterministic() -> None:
    """Test that dedup key generation is deterministic."""
    repo = "owner/repo"
    pr = 42
    comment_id = "123456789"

    key1 = generate_dedup_key(repo, pr, comment_id)
    key2 = generate_dedup_key(repo, pr, comment_id)
    key3 = generate_dedup_key(repo, pr, comment_id)

    assert key1 == key2 == key3, "Dedup key must be identical across calls"
    assert len(key1) == 16, "Dedup key should be 16 hex chars"
    assert all(c in "0123456789abcdef" for c in key1), "Dedup key must be hex"

    print("✅ Dedup key generation is deterministic")


def test_dedup_key_uniqueness() -> None:
    """Test that different inputs produce different keys."""
    keys = set()

    # Same repo, different PRs
    for pr in range(1, 10):
        key = generate_dedup_key("owner/repo", pr, "comment1")
        assert key not in keys, f"Duplicate key for PR {pr}"
        keys.add(key)

    # Same PR, different comments
    for i in range(1, 10):
        key = generate_dedup_key("owner/repo", 100, f"comment{i}")  # Use PR 100 to avoid collision with above
        assert key not in keys, f"Duplicate key for comment {i}"
        keys.add(key)

    # Different repos
    for repo in ["org/repo1", "org/repo2", "user/repo"]:
        key = generate_dedup_key(repo, 1, "comment1")
        assert key not in keys, f"Duplicate key for repo {repo}"
        keys.add(key)

    print("✅ Dedup keys are unique across different inputs")


def test_issue_dedup_key_content_based() -> None:
    """Test that issue dedup key is based on content (title, body, labels)."""
    title = "Fix critical bug"
    body = "This fixes the bug in production"
    labels = ["bug", "critical"]

    key1 = generate_issue_dedup_key(title, body, labels)
    key2 = generate_issue_dedup_key(title, body, labels)

    assert key1 == key2, "Same content should produce same key"

    # Different title -> different key
    key3 = generate_issue_dedup_key("Different title", body, labels)
    assert key3 != key1, "Different title should produce different key"

    # Different body -> different key
    key4 = generate_issue_dedup_key(title, "Different body", labels)
    assert key4 != key1, "Different body should produce different key"

    # Different labels -> different key
    key5 = generate_issue_dedup_key(title, body, ["enhancement"])
    assert key5 != key1, "Different labels should produce different key"

    # Label order shouldn't matter (sorted in function)
    key6 = generate_issue_dedup_key(title, body, ["critical", "bug"])
    assert key6 == key1, "Label order shouldn't matter"

    print("✅ Issue dedup key is content-based and order-independent")


def test_format_issue_with_dedup() -> None:
    """Test formatting issue body with embedded dedup key."""
    title = "Test Issue"
    body = "This is the issue body"
    dedup_key = "abc123def4567890"
    metadata = {"source": "pr-comment", "pr": 123}

    formatted = format_issue_with_dedup(title, body, dedup_key, metadata)

    assert dedup_key in formatted, "Dedup key should be in formatted body"
    assert "dedup-key" in formatted, "Should contain dedup-key label"
    assert "source" in formatted, "Metadata should be included"
    assert "pr" in formatted, "Metadata should include pr"

    # Should be parseable back
    import re
    matches = re.findall(r'dedup-key:([a-f0-9]{16})', formatted)
    assert len(matches) == 1, "Should have exactly one dedup key"
    assert matches[0] == dedup_key, "Dedup key should match"

    print("✅ Issue formatting with dedup key works correctly")


def test_extract_dedup_keys() -> None:
    """Test extracting dedup keys from issue bodies."""
    issues = [
        {"body": "Some text\n---\n**dedup-key:** `abc123def4567890`"},
        {"body": "Another issue\n---\n**dedup-key:** `fedcba9876543210`"},
        {"body": "No dedup key here"},
        {"body": "Multiple keys\n---\n**dedup-key:** `1111111111111111`\n**dedup-key:** `2222222222222222`"},
    ]

    keys = extract_dedup_keys_from_issues(issues)

    assert "abc123def4567890" in keys
    assert "fedcba9876543210" in keys
    assert "1111111111111111" in keys
    assert "2222222222222222" in keys
    assert len(keys) == 4, f"Should find 4 keys, found {len(keys)}: {keys}"

    print("✅ Dedup key extraction works correctly")


def test_cross_run_idempotency() -> None:
    """Test that running classification multiple times produces same dedup keys."""
    from classify import classify_comments

    comments = [
        {"id": "1001", "body": "Critical bug in production", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
        {"id": "1002", "body": "Nit: fix whitespace", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
    ]

    # Simulate multiple runs
    runs = 5
    all_keys = {}

    for run in range(runs):
        classified = classify_comments(comments, "owner/repo", 123)
        for c in classified:
            cid = c.source_comment_id
            if cid not in all_keys:
                all_keys[cid] = set()
            all_keys[cid].add(c.dedup_key)

    # Each comment should have exactly one unique key across all runs
    for cid, keys in all_keys.items():
        assert len(keys) == 1, f"Comment {cid} has multiple dedup keys across runs: {keys}"

    print("✅ Cross-run dedup key idempotency verified")


def main() -> int:
    tests = [
        test_dedup_key_deterministic,
        test_dedup_key_uniqueness,
        test_issue_dedup_key_content_based,
        test_format_issue_with_dedup,
        test_extract_dedup_keys,
        test_cross_run_idempotency,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())