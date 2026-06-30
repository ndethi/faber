#!/usr/bin/env python3
"""
Update GitHub PR with resolution comments.
Posts fix commit SHAs as replies, resolves conversations.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List


def run_cmd(cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def post_comment(pr_number: int, repo: str, body: str, in_reply_to: int = None) -> bool:
    """Post a comment on a PR."""
    args = ["gh", "api", f"/repos/{repo}/issues/{pr_number}/comments", "-f", f"body={body}"]
    if in_reply_to:
        args.extend(["-f", f"in_reply_to={in_reply_to}"])
    result = run_cmd(args)
    return result.returncode == 0


def resolve_conversation(pr_number: int, repo: str, comment_id: int) -> bool:
    """Mark a review comment conversation as resolved."""
    # Get the review ID for this comment
    result = run_cmd([
        "gh", "api", f"/repos/{repo}/pulls/{pr_number}/comments/{comment_id}"
    ])
    if result.returncode != 0:
        return False

    comment = json.loads(result.stdout)
    review_id = comment.get("pull_request_review_id")
    if not review_id:
        return False

    # Resolve the review conversation
    result = run_cmd([
        "gh", "api", "--method", "PATCH",
        f"/repos/{repo}/pulls/{pr_number}/reviews/{review_id}",
        "-f", "event=COMMENT"
    ])
    return result.returncode == 0


def generate_resolution_body(comment: Dict[str, Any], result: Dict[str, Any]) -> str:
    """Generate comment body for resolution."""
    cid = comment.get("id", "?")
    category = result.get("category", "unknown")
    fix_type = result.get("fix_type", "unknown")
    status = result.get("status", "unknown")
    commit_sha = result.get("commit_sha")
    error = result.get("error")

    if status == "applied":
        body = f"✅ **Resolved** (auto-fix applied)\n"
        body += f"- Category: `{category}`\n"
        body += f"- Fix type: `{fix_type}`\n"
        if commit_sha:
            body += f"- Commit: `{commit_sha[:8]}`\n"
        body += f"\n*Resolved by pr-review-resolution skill*"
    elif status == "deferred":
        body = f"⏳ **Deferred** — requires human review\n"
        body += f"- Category: `{category}`\n"
        body += f"- Reason: {error or 'No auto-fix available'}\n"
        body += f"\n*Please review and resolve manually*"
    else:
        body = f"❌ **Failed** to resolve\n"
        body += f"- Category: `{category}`\n"
        body += f"- Error: {error or 'Unknown error'}\n"

    return body


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: update_pr.py <resolved.json> <pr_number> <repo>"}))
        sys.exit(1)

    input_file = sys.argv[1]
    pr_number = int(sys.argv[2])
    repo = sys.argv[3]

    try:
        with open(input_file) as f:
            data = json.load(f)

        results = data.get("results", [])
        comments = data.get("comments", [])

        # Map comments by ID
        comment_map = {c["id"]: c for c in comments}

        applied_count = 0
        resolved_count = 0

        for result in results:
            cid = result.get("comment_id")
            comment = comment_map.get(cid, {})
            status = result.get("status")
            category = result.get("category")

            # Generate and post resolution comment
            body = generate_resolution_body(comment, result)
            in_reply_to = cid if comment.get("in_reply_to") is None else None

            if post_comment(pr_number, repo, body, in_reply_to):
                if status == "applied":
                    applied_count += 1
                    # Try to resolve conversation
                    if resolve_conversation(pr_number, repo, cid):
                        resolved_count += 1
                elif status == "deferred":
                    # Still post comment but don't resolve
                    pass

        output = {
            "success": True,
            "pr_number": pr_number,
            "repo": repo,
            "comments_posted": len(results),
            "auto_resolved": applied_count,
            "conversations_resolved": resolved_count,
        }
        print(json.dumps(output, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()