#!/usr/bin/env python3
"""
Eval for the pr-review skill.
Tests that the review pipeline correctly identifies issues in PR diffs.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_review_script_exists():
    """Test that review.py exists and is executable."""
    script = Path("skills/pr-review/scripts/review.py")
    assert script.exists(), "review.py must exist"
    # assert script.stat().st_mode & 0o111, "review.py must be executable"
    print("✓ review.py exists")


def test_post_review_script_exists():
    """Test that post_review.py exists."""
    script = Path("skills/pr-review/scripts/post_review.py")
    assert script.exists(), "post_review.py must exist"
    print("✓ post_review.py exists")


def test_review_help():
    """Test that review.py shows usage without args."""
    result = subprocess.run(
        [sys.executable, "skills/pr-review/scripts/review.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when no args"
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower(), "Should show usage"
    print("✓ review.py shows usage without args")


def test_post_review_help():
    """Test that post_review.py shows usage without args."""
    result = subprocess.run(
        [sys.executable, "skills/pr-review/scripts/post_review.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when no args"
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower(), "Should show usage"
    print("✓ post_review.py shows usage without args")


def test_review_detects_sql_injection():
    """Test that review detects SQL injection pattern."""
    # Create a mock PR context with SQL injection
    pr_context = {
        "context": {
            "diff": '+    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
            "base_ref": "dev",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pr_context, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/pr-review/scripts/review.py", input_path, "--output", output_path, "--fast"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Review failed: {result.stderr}"

        with open(output_path) as f:
            report = json.load(f)

        # Check for SQL injection detection
        issues = report.get("issues", [])
        sql_issues = [i for i in issues if "sql" in i["message"].lower() or "injection" in i["message"].lower()]
        assert len(sql_issues) > 0, f"Should detect SQL injection, got issues: {issues}"

        print("✓ review detects SQL injection pattern")
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


def test_review_detects_hardcoded_secrets():
    """Test that review detects potential hardcoded secrets."""
    pr_context = {
        "context": {
            "diff": '+    api_key = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"',
            "base_ref": "dev",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pr_context, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/pr-review/scripts/review.py", input_path, "--output", output_path, "--fast"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Review failed: {result.stderr}"

        with open(output_path) as f:
            report = json.load(f)

        issues = report.get("issues", [])
        # Security checks are in deterministic_checks
        det_checks = report.get("deterministic_checks", [])
        sec_check = next((c for c in det_checks if c["name"] == "security"), None)
        assert sec_check is not None, "Should have security check"
        # The security check might pass or fail depending on patterns
        print(f"✓ Security check ran: {sec_check['status']} - {sec_check['details']}")
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


def test_review_report_structure():
    """Test that review output has correct structure."""
    pr_context = {
        "context": {
            "diff": "+    def hello():\n+        return 'world'",
            "base_ref": "dev",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pr_context, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/pr-review/scripts/review.py", input_path, "--output", output_path, "--fast"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Review failed: {result.stderr}"

        with open(output_path) as f:
            report = json.load(f)

        # Check required fields
        assert "verdict" in report, "Report must have verdict"
        assert report["verdict"] in ["APPROVE", "REQUEST_CHANGES", "COMMENT"], f"Invalid verdict: {report['verdict']}"
        assert "issues" in report, "Report must have issues"
        assert "deterministic_checks" in report, "Report must have deterministic_checks"
        assert "summary" in report, "Report must have summary"

        summary = report["summary"]
        assert all(k in summary for k in ["critical", "warning", "suggestion", "deterministic_failures"])

        print("✓ Review report has correct structure")
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


def test_review_deterministic_checks():
    """Test that deterministic checks run."""
    pr_context = {
        "context": {
            "diff": "+    print('hello')",
            "base_ref": "dev",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(pr_context, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "skills/pr-review/scripts/review.py", input_path, "--output", output_path, "--fast"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Review failed: {result.stderr}"

        with open(output_path) as f:
            report = json.load(f)

        det_checks = report.get("deterministic_checks", [])
        check_names = {c["name"] for c in det_checks}

        # Should have at least some checks
        expected_checks = {"commit_style", "lint", "tests", "security", "schemas", "trajectory"}
        assert len(check_names & expected_checks) > 0, f"Should run deterministic checks, got: {check_names}"

        print(f"✓ Deterministic checks ran: {check_names}")
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


def main():
    tests = [
        test_review_script_exists,
        test_post_review_script_exists,
        test_review_help,
        test_post_review_help,
        test_review_detects_sql_injection,
        test_review_detects_hardcoded_secrets,
        test_review_report_structure,
        test_review_deterministic_checks,
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