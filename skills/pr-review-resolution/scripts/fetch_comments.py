#!/usr/bin/env python3
"""
Fetch review comments from GitHub PR via gh API.
Outputs structured JSON for categorization step.
"""
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class ReviewComment:
    id: int
    body: str
    path: str
    line: Optional[int]
    side: str  # "RIGHT" (new) | "LEFT" (old)
    author: str
    created_at: str
    in_reply_to: Optional[int]
    commit_id: Optional[str]
    html_url: str
    pull_request_review_id: Optional[int]
    state: str  # "PENDING" | "COMMENTED" | "APPROVED" | "CHANGES_REQUESTED"


def fetch_pr_comments(pr_number: int, repo: str) -> List[ReviewComment]:
    """Fetch all review comments from a PR using gh API."""
    cmd = [
        "gh", "api",
        f"/repos/{repo}/pulls/{pr_number}/comments",
        "--paginate",
        "-q", "[.[] | {id: .id, body: .body, path: .path, line: .line, side: .side, author: .user.login, created_at: .created_at, in_reply_to: .in_reply_to_id, commit_id: .commit_id, html_url: .html_url, pull_request_review_id: .pull_request_review_id}]"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh api failed: {result.stderr}")

    comments = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        data = json.loads(line)
        comments.append(ReviewComment(
            id=data["id"],
            body=data["body"],
            path=data["path"],
            line=data["line"],
            side=data["side"],
            author=data["author"],
            created_at=data["created_at"],
            in_reply_to=data["in_reply_to"],
            commit_id=data["commit_id"],
            html_url=data["html_url"],
            pull_request_review_id=data["pull_request_review_id"],
            state="PENDING",  # Default; would need reviews API for full state
        ))
    return comments


def fetch_review_states(pr_number: int, repo: str) -> dict:
    """Fetch review states (APPROVED, CHANGES_REQUESTED, COMMENTED) for context."""
    cmd = [
        "gh", "api",
        f"/repos/{repo}/pulls/{pr_number}/reviews",
        "--paginate",
        "-q", "[.[] | {id: .id, state: .state, author: .user.login}]"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    reviews = {}
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            data = json.loads(line)
            reviews[data["id"]] = {"state": data["state"], "author": data["author"]}
    return reviews


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: fetch_comments.py <pr_number> <repo>"}))
        sys.exit(1)

    pr_number = int(sys.argv[1])
    repo = sys.argv[2]

    try:
        comments = fetch_pr_comments(pr_number, repo)
        reviews = fetch_review_states(pr_number, repo)

        # Enrich comments with review state if available
        for c in comments:
            if c.pull_request_review_id and c.pull_request_review_id in reviews:
                c.state = reviews[c.pull_request_review_id]["state"]

        output = {
            "pr_number": pr_number,
            "repo": repo,
            "comments": [asdict(c) for c in comments],
            "total": len(comments),
        }
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()