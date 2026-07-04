#!/usr/bin/env python3
"""
Test classification stability for PR review comments.

Tests that the classify module produces deterministic, stable
(severity, type) classifications for known fixture comments.
"""

import json
import sys
from pathlib import Path

# Add scripts to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from classify import (
    classify_comments,
    ClassifiedComment,
    Severity,
    IssueType
)


# Expected classifications for our fixtures
# (comment_id -> expected {severity, type, actionable})
EXPECTED_CLASSIFICATIONS = {
    1001: {"severity": "Critical", "type": "bug", "actionable": True},      # prod outage
    1002: {"severity": "Critical", "type": "security", "actionable": True}, # SQL injection
    1003: {"severity": "Critical", "type": "security", "actionable": True}, # auth bypass
    1004: {"severity": "High", "type": "bug", "actionable": True},          # checkout broken
    1005: {"severity": "High", "type": "bug", "actionable": True},          # perf regression
    1006: {"severity": "High", "type": "bug", "actionable": True},          # a11y violation
    1007: {"severity": "Medium", "type": "enhancement", "actionable": True}, # pagination
    1008: {"severity": "Medium", "type": "refactor", "actionable": True},   # split function
    1009: {"severity": "Low", "type": "needs-triage", "actionable": True},  # nit whitespace
    1010: {"severity": "Low", "type": "needs-triage", "actionable": True},  # nit quotes
    1011: {"severity": "Low", "type": "non-actionable", "actionable": False}, # LGTM
    1012: {"severity": "Low", "type": "non-actionable", "actionable": False}, # ship it
    1013: {"severity": "Low", "type": "non-actionable", "actionable": False}, # question
    1014: {"severity": "Low", "type": "non-actionable", "actionable": False}, # question
    1015: {"severity": "Medium", "type": "enhancement", "actionable": True}, # suggest test
    1016: {"severity": "Medium", "type": "needs-triage", "actionable": True}, # vague
    1017: {"severity": "High", "type": "enhancement", "actionable": True},   # webhooks
    1018: {"severity": "High", "type": "enhancement", "actionable": True},   # caching
    1019: {"severity": "Low", "type": "needs-triage", "actionable": True},   # unused import
    1020: {"severity": "Medium", "type": "bug", "actionable": True},         # error handling
}


def load_fixture_comments() -> list:
    """Load PR comment fixtures from JSON."""
    fixture_path = Path(__file__).parent / "fixtures" / "pr_comments.json"
    with fixture_path.open() as f:
        return json.load(f)


def test_classification_stability() -> None:
    """Test that classification produces stable, expected results."""
    comments = load_fixture_comments()
    source_repo = "test/repo"
    source_pr = 123

    classified = classify_comments(comments, source_repo, source_pr)

    assert len(classified) == len(comments), "Should classify all comments"

    errors = []
    for classified_comment in classified:
        comment_id = int(classified_comment.source_comment_id)
        expected = EXPECTED_CLASSIFICATIONS.get(comment_id)

        if not expected:
            errors.append(f"Comment {comment_id}: No expected classification defined")
            continue

        # Check actionable
        if classified_comment.is_actionable != expected["actionable"]:
            errors.append(
                f"Comment {comment_id}: actionable={classified_comment.is_actionable}, "
                f"expected={expected['actionable']}"
            )

        if not expected["actionable"]:
            # Non-actionable comments should have Low/non-actionable
            continue

        # Check severity
        if classified_comment.severity != expected["severity"]:
            errors.append(
                f"Comment {comment_id}: severity={classified_comment.severity}, "
                f"expected={expected['severity']} (body: {classified_comment.body[:60]}...)"
            )

        # Check type
        if classified_comment.issue_type != expected["type"]:
            errors.append(
                f"Comment {comment_id}: type={classified_comment.issue_type}, "
                f"expected={expected['type']} (body: {classified_comment.body[:60]}...)"
            )

    if errors:
        for error in errors:
            print(f"❌ {error}")
        raise AssertionError(f"{len(errors)} classification mismatches")

    print(f"✅ All {len(classified)} comments classified as expected")


def test_determinism() -> None:
    """Test that two runs on identical inputs yield identical classifications."""
    comments = load_fixture_comments()
    source_repo = "test/repo"
    source_pr = 123

    run1 = classify_comments(comments, source_repo, source_pr)
    run2 = classify_comments(comments, source_repo, source_pr)

    assert len(run1) == len(run2)

    for c1, c2 in zip(run1, run2):
        # Compare all fields except confidence (may vary slightly due to match counting)
        assert c1.source_comment_id == c2.source_comment_id
        assert c1.body == c2.body
        assert c1.is_actionable == c2.is_actionable
        assert c1.severity == c2.severity
        assert c1.issue_type == c2.issue_type
        assert c1.matched_patterns == c2.matched_patterns
        assert c1.dedup_key == c2.dedup_key

    print("✅ Determinism test passed - identical inputs produce identical output")


def test_dedup_key_consistency() -> None:
    """Test that dedup keys are consistent for same inputs."""
    comments = load_fixture_comments()
    source_repo = "test/repo"
    source_pr = 123

    run1 = classify_comments(comments, source_repo, source_pr)
    run2 = classify_comments(comments, source_repo, source_pr)

    keys1 = {c.source_comment_id: c.dedup_key for c in run1}
    keys2 = {c.source_comment_id: c.dedup_key for c in run2}

    assert keys1 == keys2, "Dedup keys must be identical across runs"

    # All keys should be unique
    assert len(set(keys1.values())) == len(keys1), "All dedup keys must be unique"

    print("✅ Dedup key consistency test passed")


def test_non_actionable_defaults() -> None:
    """Test that non-actionable comments get Low severity and non-actionable type."""
    comments = [
        {"id": 999, "body": "LGTM!", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
        {"id": 998, "body": "Approved", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
        {"id": 997, "body": "Thanks!", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
    ]

    classified = classify_comments(comments, "test/repo", 1)

    for c in classified:
        assert not c.is_actionable, f"Should be non-actionable: {c.body}"
        assert c.severity == "Low", f"Non-actionable should be Low severity: {c.severity}"
        assert c.issue_type == "non-actionable", f"Non-actionable should be non-actionable type: {c.issue_type}"

    print("✅ Non-actionable defaults test passed")


def test_ambiguous_fallbacks() -> None:
    """Test that ambiguous comments fall back to Medium/needs-triage."""
    comments = [
        {"id": 996, "body": "Something feels off here", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
        {"id": 995, "body": "Not sure about this", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
        {"id": 994, "body": "This is weird", "user": {"login": "test"}, "created_at": "2024-01-01T00:00:00Z"},
    ]

    classified = classify_comments(comments, "test/repo", 1)

    for c in classified:
        assert c.is_actionable, f"Should be actionable: {c.body}"
        assert c.severity == "Medium", f"Ambiguous should default to Medium: {c.severity} (body: {c.body})"
        assert c.issue_type == "needs-triage", f"Ambiguous should default to needs-triage: {c.issue_type} (body: {c.body})"

    print("✅ Ambiguous fallback test passed")


def test_confidence_bounds() -> None:
    """Test that confidence scores are within valid range."""
    comments = load_fixture_comments()
    classified = classify_comments(comments, "test/repo", 123)

    for c in classified:
        assert 0.0 <= c.confidence <= 1.0, f"Confidence out of bounds: {c.confidence}"

    print("✅ Confidence bounds test passed")


def main() -> int:
    tests = [
        test_classification_stability,
        test_determinism,
        test_dedup_key_consistency,
        test_non_actionable_defaults,
        test_ambiguous_fallbacks,
        test_confidence_bounds,
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