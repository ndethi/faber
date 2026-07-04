#!/usr/bin/env python3
"""
Deduplication logic for pm-github skill.

Provides deterministic dedup keys and existence checks via gh issue search.
"""

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class DedupResult:
    """Result of a deduplication check."""
    key: str
    exists: bool
    existing_issue_number: Optional[int] = None
    existing_issue_title: Optional[str] = None


def generate_dedup_key(source_repo: str, source_pr: int, source_comment_id: str) -> str:
    """
    Generate a deterministic SHA256 dedup key for a review comment.

    Args:
        source_repo: Repository in 'owner/name' format
        source_pr: PR number
        source_comment_id: Comment ID from GitHub API

    Returns:
        Hex digest of SHA256 hash (16 chars)
    """
    raw = f"{source_repo}:{source_pr}:{source_comment_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_issue_dedup_key(title: str, body: str, labels: List[str]) -> str:
    """
    Generate a dedup key for a proposed issue based on its content.

    Args:
        title: Issue title
        body: Issue body
        labels: List of labels

    Returns:
        Hex digest of SHA256 hash (16 chars)
    """
    # Normalize content for consistent hashing
    normalized = f"{title.strip()}\n{body.strip()}\n{','.join(sorted(labels))}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def check_dedup_key_exists(gh_client, dedup_key: str, repo: Optional[str] = None) -> DedupResult:
    """
    Check if an issue with the given dedup key already exists.

    Searches for issues with the dedup key in the body.

    Args:
        gh_client: GitHubClient instance
        dedup_key: The dedup key to search for
        repo: Repository override (uses client's repo if not provided)

    Returns:
        DedupResult with existence info
    """
    search_query = f'in:body "dedup-key:{dedup_key}"'
    args = ["issue", "list", "--state", "all", "--search", search_query, "--limit", "1", "--json", "number,title,body"]
    if repo:
        args = ["-R", repo] + args

    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            if issues:
                issue = issues[0]
                return DedupResult(
                    key=dedup_key,
                    exists=True,
                    existing_issue_number=issue.get("number"),
                    existing_issue_title=issue.get("title")
                )
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    return DedupResult(key=dedup_key, exists=False)


def check_multiple_dedup_keys(gh_client, dedup_keys: List[str], repo: Optional[str] = None) -> Dict[str, DedupResult]:
    """
    Check multiple dedup keys efficiently.

    Note: Currently sequential. Could be optimized with a single search query.
    """
    results = {}
    for key in dedup_keys:
        results[key] = check_dedup_key_exists(gh_client, key, repo)
    return results


def extract_dedup_keys_from_issues(issues: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract all dedup keys from a list of issues.

    Args:
        issues: List of issue dicts with 'body' field

    Returns:
        Set of dedup keys found
    """
    keys = set()
    # Match both formats:
    # - dedup-key:abc123... (plain text)
    # - **dedup-key:** `abc123...` (markdown bold with backticks)
    pattern1 = re.compile(r'dedup[- ]?key:?\s*([a-f0-9]{16})', re.I)
    pattern2 = re.compile(r'\*\*dedup[- ]?key:\*\*\s*[`"]([a-f0-9]{16})[`"]', re.I)
    for issue in issues:
        body = issue.get("body", "")
        keys.update(pattern1.findall(body))
        keys.update(pattern2.findall(body))
    return keys


def format_issue_with_dedup(title: str, body: str, dedup_key: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Format an issue body with the dedup key embedded.

    Args:
        title: Issue title
        body: Issue body content
        dedup_key: The dedup key
        metadata: Optional metadata to include

    Returns:
        Formatted issue body with dedup key
    """
    lines = [body.strip()] if body.strip() else []
    lines.append("")  # Blank line
    lines.append("---")
    lines.append(f"dedup-key:{dedup_key}")

    if metadata:
        lines.append("")
        lines.append("Metadata:")
        for k, v in metadata.items():
            lines.append(f"- {k}: {v}")

    return "\n".join(lines)


def main() -> None:
    """CLI for testing deduplication."""
    import argparse

    parser = argparse.ArgumentParser(description="Deduplication utilities for pm-github")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-key
    gen_parser = subparsers.add_parser("generate-key", help="Generate dedup key")
    gen_parser.add_argument("--repo", required=True, help="Source repository (owner/name)")
    gen_parser.add_argument("--pr", type=int, required=True, help="Source PR number")
    gen_parser.add_argument("--comment-id", required=True, help="Source comment ID")

    # check-key
    check_parser = subparsers.add_parser("check-key", help="Check if dedup key exists")
    check_parser.add_argument("--key", required=True, help="Dedup key to check")
    check_parser.add_argument("--repo", help="Repository (owner/name)")

    # extract-keys
    extract_parser = subparsers.add_parser("extract-keys", help="Extract dedup keys from issues JSON")
    extract_parser.add_argument("--input", required=True, help="JSON file with issues array")

    args = parser.parse_args()

    if args.command == "generate-key":
        key = generate_dedup_key(args.repo, args.pr, args.comment_id)
        print(key)

    elif args.command == "check-key":
        # This would need a GitHubClient instance - simplified for CLI
        print(f"Checking key: {args.key} (requires gh CLI)")
        # Actual check would use GitHubClient

    elif args.command == "extract-keys":
        with open(args.input) as f:
            issues = json.load(f)
        if isinstance(issues, dict):
            issues = issues.get("issues", [])
        keys = extract_dedup_keys_from_issues(issues)
        for key in sorted(keys):
            print(key)


if __name__ == "__main__":
    main()