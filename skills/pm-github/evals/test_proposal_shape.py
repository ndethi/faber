#!/usr/bin/env python3
"""
Test proposal artifact shape and schema compliance.

Tests that proposal batches generate correctly structured JSON
and Markdown artifacts matching the documented schema.
"""

import json
import jsonschema
import sys
from pathlib import Path
from datetime import datetime, timezone

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from proposals import (
    ProposedIssue,
    ProposalBatch,
    create_proposal_batch_from_classified,
    write_proposal_batch,
    load_proposal_batch,
    generate_proposal_markdown,
    create_batch_id,
)


# JSON Schema for ProposalBatch
PROPOSAL_BATCH_SCHEMA = {
    "type": "object",
    "required": [
        "batch_id",
        "created_at",
        "source_repo",
        "source_pr",
        "proposed_issues",
        "total_count",
        "actionable_count",
        "filtered_count"
    ],
    "properties": {
        "batch_id": {"type": "string", "pattern": "^pm-\\d{8}-\\d{6}-[a-f0-9]{8}$"},
        "created_at": {"type": "string", "format": "date-time"},
        "source_repo": {"type": "string", "pattern": "^.+/.+$"},
        "source_pr": {"type": "integer", "minimum": 1},
        "proposed_issues": {
            "type": "array",
            "items": {"$ref": "#/definitions/proposed_issue"}
        },
        "total_count": {"type": "integer", "minimum": 0},
        "actionable_count": {"type": "integer", "minimum": 0},
        "filtered_count": {"type": "integer", "minimum": 0}
    },
    "definitions": {
        "proposed_issue": {
            "type": "object",
            "required": [
                "title",
                "body",
                "labels",
                "severity",
                "issue_type",
                "source_comment_id",
                "source_repo",
                "source_pr",
                "dedup_key",
                "confidence"
            ],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "body": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
                "severity": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                "issue_type": {"type": "string", "enum": ["bug", "enhancement", "docs", "refactor", "security", "needs-triage"]},
                "source_comment_id": {"type": "string"},
                "source_repo": {"type": "string", "pattern": "^.+/.+$"},
                "source_pr": {"type": "integer", "minimum": 1},
                "dedup_key": {"type": "string", "pattern": "^[a-f0-9]{16}$"},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "metadata": {"type": "object"}
            }
        }
    }
}


def test_batch_id_format() -> None:
    """Test that batch IDs follow the expected format."""
    for _ in range(10):
        batch_id = create_batch_id()
        # Format: pm-YYYYMMDD-HHMMSS-xxxxxxxx
        assert batch_id.startswith("pm-"), f"Batch ID should start with 'pm-': {batch_id}"
        parts = batch_id.split("-")
        assert len(parts) == 4, f"Batch ID should have 4 parts: {batch_id}"
        # Date part: YYYYMMDD
        assert len(parts[1]) == 8, f"Date part should be 8 digits: {parts[1]}"
        assert parts[1].isdigit(), f"Date part should be numeric: {parts[1]}"
        # Time part: HHMMSS
        assert len(parts[2]) == 6, f"Time part should be 6 digits: {parts[2]}"
        assert parts[2].isdigit(), f"Time part should be numeric: {parts[2]}"
        # UUID part: 8 hex chars
        assert len(parts[3]) == 8, f"UUID part should be 8 chars: {parts[3]}"
        assert all(c in "0123456789abcdef" for c in parts[3]), f"UUID part should be hex: {parts[3]}"

    print("✅ Batch ID format is correct")


def test_proposal_batch_schema_validation() -> None:
    """Test that ProposalBatch serializes to valid JSON per schema."""
    classified = [
        {
            "source_comment_id": "1001",
            "body": "Critical bug in production",
            "is_actionable": True,
            "severity": "Critical",
            "type": "bug",
            "confidence": 0.9,
            "dedup_key": "abc123def4567890",
            "matched_patterns": ["critical", "bug"],
        },
        {
            "source_comment_id": "1002",
            "body": "Consider adding pagination",
            "is_actionable": True,
            "severity": "Medium",
            "type": "enhancement",
            "confidence": 0.7,
            "dedup_key": "fedcba9876543210",
            "matched_patterns": ["enhancement"],
        },
    ]

    batch = create_proposal_batch_from_classified(classified, "owner/repo", 123)

    # Convert to dict for schema validation
    batch_dict = {
        "batch_id": batch.batch_id,
        "created_at": batch.created_at,
        "source_repo": batch.source_repo,
        "source_pr": batch.source_pr,
        "proposed_issues": [
            {
                "title": pi.title,
                "body": pi.body,
                "labels": pi.labels,
                "severity": pi.severity,
                "issue_type": pi.issue_type,
                "source_comment_id": pi.source_comment_id,
                "source_repo": pi.source_repo,
                "source_pr": pi.source_pr,
                "dedup_key": pi.dedup_key,
                "confidence": pi.confidence,
                "metadata": pi.metadata,
            }
            for pi in batch.proposed_issues
        ],
        "total_count": batch.total_count,
        "actionable_count": batch.actionable_count,
        "filtered_count": batch.filtered_count,
    }

    # Validate against schema
    jsonschema.validate(instance=batch_dict, schema=PROPOSAL_BATCH_SCHEMA)

    print("✅ ProposalBatch validates against JSON schema")


def test_write_proposal_batch_creates_files() -> None:
    """Test that write_proposal_batch creates correct files."""
    import tempfile

    classified = [
        {
            "source_comment_id": "1001",
            "body": "Test issue body",
            "is_actionable": True,
            "severity": "High",
            "type": "bug",
            "confidence": 0.8,
            "dedup_key": "abc123def4567890",
            "matched_patterns": [],
        }
    ]

    batch = create_proposal_batch_from_classified(classified, "owner/repo", 123)

    with tempfile.TemporaryDirectory() as tmpdir:
        written = write_proposal_batch(batch, Path(tmpdir))

        # Check files exist
        assert "json" in written
        assert "markdown" in written
        assert written["json"].exists()
        assert written["markdown"].exists()

        # Check JSON content
        json_content = json.loads(written["json"].read_text())
        assert json_content["batch_id"] == batch.batch_id
        assert len(json_content["proposed_issues"]) == 1
        assert json_content["proposed_issues"][0]["dedup_key"] == "abc123def4567890"

        # Check Markdown content
        md_content = written["markdown"].read_text()
        assert batch.batch_id in md_content
        assert "Test issue body" in md_content
        assert "High" in md_content
        assert "bug" in md_content
        assert "Would create" in md_content
        assert "apply" in md_content.lower()

    print("✅ write_proposal_batch creates correct JSON and Markdown files")


def test_load_proposal_batch_roundtrip() -> None:
    """Test that loading a proposal batch preserves all data."""
    import tempfile

    classified = [
        {
            "source_comment_id": "1001",
            "body": "Roundtrip test",
            "is_actionable": True,
            "severity": "Medium",
            "type": "enhancement",
            "confidence": 0.75,
            "dedup_key": "abc123def4567890",
            "matched_patterns": ["enhancement"],
        }
    ]

    batch = create_proposal_batch_from_classified(classified, "owner/repo", 123)

    with tempfile.TemporaryDirectory() as tmpdir:
        written = write_proposal_batch(batch, Path(tmpdir))
        loaded = load_proposal_batch(written["json"])

        assert loaded.batch_id == batch.batch_id
        assert loaded.source_repo == batch.source_repo
        assert loaded.source_pr == batch.source_pr
        assert len(loaded.proposed_issues) == len(batch.proposed_issues)

        for orig, loaded_issue in zip(batch.proposed_issues, loaded.proposed_issues):
            assert orig.title == loaded_issue.title
            assert orig.body == loaded_issue.body
            assert orig.labels == loaded_issue.labels
            assert orig.severity == loaded_issue.severity
            assert orig.issue_type == loaded_issue.issue_type
            assert orig.dedup_key == loaded_issue.dedup_key
            assert orig.confidence == loaded_issue.confidence

    print("✅ Proposal batch roundtrip (write -> load) preserves data")


def test_markdown_contains_required_sections() -> None:
    """Test that generated markdown has all required sections for PR comment."""
    classified = [
        {
            "source_comment_id": "1001",
            "body": "Test body",
            "is_actionable": True,
            "severity": "Critical",
            "type": "security",
            "confidence": 0.95,
            "dedup_key": "abc123def4567890",
            "matched_patterns": [],
        }
    ]

    batch = create_proposal_batch_from_classified(classified, "owner/repo", 123)
    markdown = generate_proposal_markdown(batch)

    # Required sections
    assert "PM-GitHub Proposal Batch" in markdown
    assert batch.batch_id in markdown
    assert "owner/repo#PR123" in markdown or "owner/repo" in markdown
    assert "Proposed Issues" in markdown
    assert "Test body" in markdown
    assert "Critical" in markdown
    assert "security" in markdown
    assert "abc123def4567890" in markdown
    assert "Actions" in markdown
    assert "apply" in markdown.lower()
    assert "This is a proposal only" in markdown
    assert "pm-github" in markdown.lower()

    print("✅ Markdown contains all required sections for PR comment")


def test_empty_proposal_batch() -> None:
    """Test handling of empty proposal batch (no actionable comments)."""
    classified = [
        {
            "source_comment_id": "1001",
            "body": "LGTM!",
            "is_actionable": False,
            "severity": "Low",
            "type": "non-actionable",
            "confidence": 1.0,
            "dedup_key": "abc123def4567890",
            "matched_patterns": [],
        }
    ]

    batch = create_proposal_batch_from_classified(classified, "owner/repo", 123, min_confidence=0.5)

    assert batch.actionable_count == 0
    assert batch.total_count == 1
    assert batch.filtered_count == 1
    assert len(batch.proposed_issues) == 0

    # Should still generate valid markdown
    markdown = generate_proposal_markdown(batch)
    assert "0" in markdown or "zero" in markdown.lower()

    print("✅ Empty proposal batch handled correctly")


def test_proposal_batch_index_jsonl() -> None:
    """Test that index.jsonl is updated with batch metadata."""
    import tempfile

    classified = [
        {
            "source_comment_id": "1001",
            "body": "Test",
            "is_actionable": True,
            "severity": "Medium",
            "type": "bug",
            "confidence": 0.7,
            "dedup_key": "abc123def4567890",
            "matched_patterns": [],
        }
    ]

    batch = create_proposal_batch_from_classified(classified, "owner/repo", 123)

    with tempfile.TemporaryDirectory() as tmpdir:
        write_proposal_batch(batch, Path(tmpdir))

        index_path = Path(tmpdir) / "pm-proposals" / "index.jsonl"
        assert index_path.exists()

        lines = index_path.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["batch_id"] == batch.batch_id
        assert entry["source_repo"] == "owner/repo"
        assert entry["source_pr"] == 123
        assert entry["actionable_count"] == 1

    print("✅ Index JSONL updated correctly")


def main() -> int:
    tests = [
        test_batch_id_format,
        test_proposal_batch_schema_validation,
        test_write_proposal_batch_creates_files,
        test_load_proposal_batch_roundtrip,
        test_markdown_contains_required_sections,
        test_empty_proposal_batch,
        test_proposal_batch_index_jsonl,
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