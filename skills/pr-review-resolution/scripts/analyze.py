#!/usr/bin/env python3
"""
Historical PR review analysis — read-only mode.
Analyzes past merged PRs to learn patterns and improve auto-fix rules.
"""
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def fetch_merged_prs(repo: str, since: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch merged PRs since date."""
    cmd = [
        "gh", "api",
        f"/repos/{repo}/pulls",
        "--paginate",
        "-q", f"[.[] | select(.merged_at >= \"{since}\" and .merged_at != null) | {{number: .number, title: .title, merged_at: .merged_at, author: .user.login}}]",
    ]
    result = run_cmd(cmd)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def fetch_pr_reviews(pr_number: int, repo: str) -> List[Dict[str, Any]]:
    """Fetch all review comments for a PR."""
    cmd = [
        "gh", "api",
        f"/repos/{repo}/pulls/{pr_number}/comments",
        "--paginate",
        "-q", "[.[] | {id: .id, body: .body, path: .path, line: .line, author: .user.login, created_at: .created_at}]",
    ]
    result = run_cmd(cmd)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def categorize_comment(body: str) -> str:
    """Deterministic categorization using keywords."""
    body_lower = body.lower()

    # Security first (high priority)
    if any(kw in body_lower for kw in ["secret", "password", "token", "api key", "credential", "vuln", "cve", "exploit"]):
        return "security"

    # Style/formatting
    if any(kw in body_lower for kw in [
        "format", "lint", "style", "prettier", "ruff", "black", "trailing", "whitespace",
        "indent", "spacing", "semicolon", "quote", "brace", "import order", "unused import"
    ]):
        return "style"

    # Documentation
    if any(kw in body_lower for kw in [
        "docstring", "comment", "readme", "documentation", "doc ", "type hint", "annotation",
        "describe", "explain", "clarify", "typo"
    ]):
        return "docs"

    # Tests
    if any(kw in body_lower for kw in [
        "test", "pytest", "unittest", "coverage", "assert", "mock", "fixture",
        "edge case", "test case", "add test", "missing test"
    ]):
        return "test"

    # Logic/algorithm
    if any(kw in body_lower for kw in [
        "logic", "algorithm", "condition", "loop", "recursion", "complexity",
        "off by one", "infinite", "null", "none", "exception", "error handling",
        "race condition", "concurrency", "thread", "async", "await"
    ]):
        return "logic"

    # Design/architecture
    if any(kw in body_lower for kw in [
        "design", "architecture", "pattern", "interface", "api", "contract",
        "coupling", "cohesion", "single responsibility", "dependency", "abstraction",
        "refactor", "extract", "rename", "move", "split", "merge"
    ]):
        return "design"

    return "other"


def analyze_pr(pr_number: int, repo: str) -> Dict[str, Any]:
    """Analyze a single PR's review comments."""
    comments = fetch_pr_reviews(pr_number, repo)
    categories = Counter()
    comment_details = []

    for c in comments:
        cat = categorize_comment(c["body"])
        categories[cat] += 1
        comment_details.append({
            "comment_id": c["id"],
            "category": cat,
            "path": c.get("path"),
            "line": c.get("line"),
            "author": c["author"],
            "preview": c["body"][:100],
        })

    return {
        "pr_number": pr_number,
        "total_comments": len(comments),
        "categories": dict(categories),
        "details": comment_details,
    }


def analyze_repo(repo: str, since: str, limit: int = 50) -> Dict[str, Any]:
    """Analyze multiple merged PRs."""
    prs = fetch_merged_prs(repo, since, limit)

    all_categories = Counter()
    pr_analyses = []
    total_comments = 0

    for pr in prs[:limit]:
        analysis = analyze_pr(pr["number"], repo)
        pr_analyses.append({**pr, **analysis})
        all_categories.update(analysis["categories"])
        total_comments += analysis["total_comments"]

    # Generate proposals for new auto-fix rules
    proposals = []
    for cat, count in all_categories.most_common():
        if cat in ("style", "docs") and count >= 5:
            proposals.append({
                "type": "auto-fix-rule",
                "category": cat,
                "frequency": count,
                "suggestion": f"Add deterministic auto-fix for {cat} comments (frequency: {count})",
            })

    return {
        "repo": repo,
        "since": since,
        "prs_analyzed": len(prs),
        "total_comments": total_comments,
        "category_distribution": dict(all_categories),
        "pr_analyses": pr_analyses,
        "proposals": proposals,
    }


def main():
    if len(sys.argv) < 4:
        print(json.dumps({
            "error": "Usage: analyze.py <repo> <since_YYYY-MM-DD> <output.json> [limit]"
        }))
        sys.exit(1)

    repo = sys.argv[1]
    since = sys.argv[2]
    output_file = sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    try:
        result = analyze_repo(repo, since, limit)

        with open(output_file, "w") as f:
            json.dump(result, indent=2)

        print(json.dumps({
            "prs_analyzed": result["prs_analyzed"],
            "total_comments": result["total_comments"],
            "categories": result["category_distribution"],
            "proposals": result["proposals"],
            "output": output_file,
        }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()