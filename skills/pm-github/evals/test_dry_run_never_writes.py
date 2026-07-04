#!/usr/bin/env python3
"""
Test that dry-run mode never performs actual GitHub writes.

This test mocks the gh CLI and verifies that no write subcommands
are invoked when dry_run=True.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from github_client import GitHubClient, GHResult


class MockSubprocess:
    """Mock subprocess.run to track gh CLI calls."""
    def __init__(self):
        self.calls = []
        self.results = {}

    def add_result(self, args_pattern: list, result: GHResult):
        """Add a mock result for matching args."""
        key = tuple(args_pattern)
        self.results[key] = result

    def run(self, args, *a, **kw):
        self.calls.append(args)
        # Find matching result
        for pattern, result in self.results.items():
            if list(pattern) == args[:len(pattern)]:
                return MagicMock(
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
        # Default success for read operations
        return MagicMock(returncode=0, stdout="{}", stderr="")


def test_dry_run_create_issue_never_calls_gh() -> None:
    """Test that create_issue in dry-run doesn't call gh."""
    mock = MockSubprocess()
    client = GitHubClient(repo="owner/repo", dry_run=True)

    with patch("subprocess.run", mock.run):
        result = client.create_issue("Test Issue", "Body", labels=["bug"])

    # Verify result is dry-run
    assert result.success
    assert result.data["dry_run"] is True
    assert "Would create issue" in result.stdout

    # Verify NO gh calls were made for write operations
    write_calls = [c for c in mock.calls if _is_write_call(c)]
    assert len(write_calls) == 0, f"Dry-run should not make write calls: {write_calls}"

    print("✅ Dry-run create_issue doesn't call gh")


def test_dry_run_edit_issue_never_calls_gh() -> None:
    """Test that edit_issue in dry-run doesn't call gh."""
    mock = MockSubprocess()
    client = GitHubClient(repo="owner/repo", dry_run=True)

    with patch("subprocess.run", mock.run):
        result = client.edit_issue(1, title="New Title", add_labels=["bug"])

    assert result.success
    assert result.data["dry_run"] is True
    assert "Would edit issue" in result.stdout

    write_calls = [c for c in mock.calls if _is_write_call(c)]
    assert len(write_calls) == 0, f"Dry-run should not make write calls: {write_calls}"

    print("✅ Dry-run edit_issue doesn't call gh")


def test_dry_run_create_label_never_calls_gh() -> None:
    """Test that create_label in dry-run doesn't call gh."""
    mock = MockSubprocess()
    client = GitHubClient(repo="owner/repo", dry_run=True)

    with patch("subprocess.run", mock.run):
        result = client.create_label("new-label", "ff0000", "Description")

    assert result.success
    assert result.data["dry_run"] is True

    write_calls = [c for c in mock.calls if _is_write_call(c)]
    assert len(write_calls) == 0, f"Dry-run should not make write calls: {write_calls}"

    print("✅ Dry-run create_label doesn't call gh")


def test_dry_run_project_operations_never_calls_gh() -> None:
    """Test that project operations in dry-run don't call gh."""
    mock = MockSubprocess()
    client = GitHubClient(repo="owner/repo", dry_run=True)

    with patch("subprocess.run", mock.run):
        project_result = client.create_project("Test Project", "owner")
        field_result = client.create_project_field("proj1", "Status", "SINGLE_SELECT", ["A", "B"])
        view_result = client.create_project_view("proj1", "My View", "TABLE")
        item_result = client.add_item_to_project("proj1", "123")

    for result in [project_result, field_result, view_result, item_result]:
        assert result.success
        assert result.data["dry_run"] is True

    write_calls = [c for c in mock.calls if _is_write_call(c)]
    assert len(write_calls) == 0, f"Dry-run should not make write calls: {write_calls}"

    print("✅ Dry-run project operations don't call gh")


def test_live_mode_calls_gh_for_writes() -> None:
    """Test that live mode (dry_run=False) DOES call gh for writes."""
    mock = MockSubprocess()
    # Add mock results for write operations
    mock.add_result(["gh", "-R", "owner/repo", "issue", "create"], GHResult(True, "https://github.com/owner/repo/issues/1", "", 0))
    mock.add_result(["gh", "-R", "owner/repo", "label", "create"], GHResult(True, "", "", 0))

    client = GitHubClient(repo="owner/repo", dry_run=False)

    with patch("subprocess.run", mock.run):
        client.create_issue("Test", "Body")
        client.create_label("test-label", "ff0000")

    write_calls = [c for c in mock.calls if _is_write_call(c)]
    assert len(write_calls) >= 2, f"Live mode should make write calls: {write_calls}"

    print("✅ Live mode calls gh for writes")


def test_read_operations_work_in_dry_run() -> None:
    """Test that read operations still work in dry-run mode."""
    mock = MockSubprocess()
    mock.add_result(["gh", "-R", "owner/repo", "issue", "list"], GHResult(True, '[{"number": 1}]', "", 0, [{"number": 1}]))
    mock.add_result(["gh", "-R", "owner/repo", "label", "list"], GHResult(True, '[{"name": "bug"}]', "", 0, [{"name": "bug"}]))

    client = GitHubClient(repo="owner/repo", dry_run=True)

    with patch("subprocess.run", mock.run):
        issues = client.list_issues()
        labels = client.list_labels()

    assert issues.success
    assert labels.success
    assert issues.data is not None
    assert labels.data is not None

    print("✅ Read operations work in dry-run mode")


def test_audit_log_only_in_live_mode() -> None:
    """Test that audit log entries are only flushed for live operations."""
    mock = MockSubprocess()
    client = GitHubClient(repo="owner/repo", dry_run=True)

    with patch("subprocess.run", mock.run):
        client.create_issue("Test", "Body")

    # In dry-run, log entries are created but marked dry_run=True
    assert len(client._log_entries) == 1
    assert client._log_entries[0]["dry_run"] is True

    # In live mode, they'd be marked dry_run=False
    client2 = GitHubClient(repo="owner/repo", dry_run=False)
    mock.add_result(["gh", "-R", "owner/repo", "issue", "create"], GHResult(True, "url", "", 0))

    with patch("subprocess.run", mock.run):
        client2.create_issue("Test", "Body")

    assert len(client2._log_entries) == 1
    assert client2._log_entries[0]["dry_run"] is False

    print("✅ Audit log correctly tracks dry-run vs live")


def _is_write_call(args: list) -> bool:
    """Check if a gh command is a write operation."""
    if not args or args[0] != "gh":
        return False

    # Check for write subcommands
    write_indicators = [
        "issue create", "issue edit", "issue close", "issue reopen",
        "label create", "label edit", "label delete",
        "project create", "project field-create", "project view-create", "project item-add",
        "release create",
        "pr create", "pr edit", "pr merge", "pr close",
    ]

    cmd_str = " ".join(args)
    return any(indicator in cmd_str for indicator in write_indicators)


def main() -> int:
    tests = [
        test_dry_run_create_issue_never_calls_gh,
        test_dry_run_edit_issue_never_calls_gh,
        test_dry_run_create_label_never_calls_gh,
        test_dry_run_project_operations_never_calls_gh,
        test_live_mode_calls_gh_for_writes,
        test_read_operations_work_in_dry_run,
        test_audit_log_only_in_live_mode,
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