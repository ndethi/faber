#!/usr/bin/env python3
"""
Post review comments to GitHub PR.
"""
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class ReviewIssue:
    level: str
    file: str
    line: int
    message: str
    suggestion: str


def post_github_review(pr_number: int, repo: str, verdict: str, issues: List[ReviewIssue], body: str):
    """Submit a formal GitHub review with inline comments."""
    # Build review body
    review_body = body

    # Build inline comments
    comments = []
    for issue in issues:
        if issue.file == "unknown" or issue.line == 0:
            continue  # Skip issues without location

        prefix = {"critical": "🔴 **Critical**", "warning": "⚠️ **Warning**", "suggestion": "💡 **Suggestion**"}[issue.level]
        comment_body = f"{prefix}: {issue.message}\n\n> Suggestion: {issue.suggestion}"

        comments.append({
            "path": issue.file,
            "line": issue.line,
            "body": comment_body,
            "side": "RIGHT",
        })

    # Submit review via gh API
    head_sha = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "headRefOid", "--jq", ".headRefOid"],
        capture_output=True, text=True
    ).stdout.strip()

    review_data = {
        "commit_id": head_sha,
        "body": review_body,
        "event": verdict.replace("_", "-").upper(),  # APPROVE, REQUEST_CHANGES, COMMENT
        "comments": comments,
    }

    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr_number}/reviews", "--method", "POST", "--input", "-"],
        input=json.dumps(review_data),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Failed to post review: {result.stderr}", file=sys.stderr)
        return False

    print("Review posted successfully", file=sys.stderr)
    return True


def post_summary_comment(pr_number: int, repo: str, body: str):
    """Post a summary comment on the PR."""
    result = subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--repo", repo, "--body", body],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Failed to post comment: {result.stderr}", file=sys.stderr)
        return False
    return True


def main():
    if len(sys.argv) < 4:
        print(json.dumps({
            "usage": "post_review.py <pr_number> <repo> <review_report.json> [--hitl-gate]"
        }, indent=2))
        sys.exit(1)

    pr_number = int(sys.argv[1])
    repo = sys.argv[2]
    report_file = sys.argv[3]
    hitl_gate = "--hitl-gate" in sys.argv

    with open(report_file) as f:
        report = json.load(f)

    verdict = report["verdict"]
    issues = [ReviewIssue(**i) for i in report["issues"]]
    det_checks = report["deterministic_checks"]
    summary = report["summary"]

    # Build review body
    body_lines = [
        "## PR Review Summary",
        "",
        f"**Verdict: {verdict.replace('_', ' ').title()}** "
        f"({summary['critical']} critical, {summary['warning']} warnings, "
        f"{summary['suggestion']} suggestions, {summary['deterministic_failures']} deterministic failures)",
        "",
    ]

    # Deterministic checks summary
    body_lines.append("### Deterministic Checks")
    for check in det_checks:
        status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️"}[check["status"]]
        body_lines.append(f"- {status_emoji} **{check['name']}**: {check['details']}")
    body_lines.append("")

    # Issues by level
    for level in ["critical", "warning", "suggestion"]:
        level_issues = [i for i in issues if i.level == level]
        if not level_issues:
            continue

        emoji = {"critical": "🔴", "warning": "⚠️", "suggestion": "💡"}[level]
        body_lines.append(f"### {emoji} {level.title()}s")
        for issue in level_issues:
            loc = f"{issue.file}:{issue.line}" if issue.file != "unknown" else "general"
            body_lines.append(f"- **{loc}** — {issue.message}")
            body_lines.append(f"  > Suggestion: {issue.suggestion}")
        body_lines.append("")

    if hitl_gate:
        body_lines.append("---")
        body_lines.append("*HITL gate enabled: human review required before merge.*")

    review_body = "\n".join(body_lines)

    # Post review
    success = post_github_review(pr_number, repo, verdict, issues, review_body)

    # Also post summary comment for visibility
    post_summary_comment(pr_number, repo, review_body)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()