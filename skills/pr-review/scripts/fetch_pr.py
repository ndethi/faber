#!/usr/bin/env python3
"""
Fetch PR details and diff from GitHub.
Outputs structured JSON for the review pipeline.
"""
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class PRFile:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str


@dataclass
class PRContext:
    number: int
    title: str
    body: str
    head_sha: str
    base_ref: str
    files: List[PRFile]
    diff: str


def run_gh(args: List[str]) -> subprocess.CompletedProcess:
    """Run gh command and return result."""
    return subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
    )


def fetch_pr_metadata(pr_number: int, repo: str) -> dict:
    """Fetch PR metadata from GitHub."""
    result = run_gh([
        "pr", "view", str(pr_number),
        "--repo", repo,
        "--json", "title,body,headRefOid,baseRefName,files"
    ])
    if result.returncode != 0:
        raise RuntimeError(f"gh pr view failed: {result.stderr}")
    return json.loads(result.stdout)


def fetch_pr_diff(pr_number: int, repo: str) -> str:
    """Fetch full PR diff."""
    result = run_gh([
        "pr", "diff", str(pr_number),
        "--repo", repo,
    ])
    if result.returncode != 0:
        raise RuntimeError(f"gh pr diff failed: {result.stderr}")
    return result.stdout


def fetch_pr_checks(pr_number: int, repo: str) -> dict:
    """Fetch CI check status."""
    result = run_gh([
        "pr", "checks", str(pr_number),
        "--repo", repo,
        "--json", "name,state,conclusion,detailsUrl"
    ])
    if result.returncode != 0:
        return {"checks": []}
    return json.loads(result.stdout)


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "usage": "fetch_pr.py <pr_number> <repo> [--output <file>]"
        }, indent=2))
        sys.exit(1)

    pr_number = int(sys.argv[1])
    repo = sys.argv[2]
    output_file = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    # Fetch PR data
    print(f"Fetching PR #{pr_number} from {repo}...", file=sys.stderr)
    metadata = fetch_pr_metadata(pr_number, repo)
    diff = fetch_pr_diff(pr_number, repo)
    checks = fetch_pr_checks(pr_number, repo)

    # Parse files from metadata
    files = []
    for f in metadata.get("files", []):
        files.append(PRFile(
            filename=f["path"],
            status=f.get("status", "modified"),
            additions=f["additions"],
            deletions=f["deletions"],
            patch=f.get("patch", ""),
        ))

    context = PRContext(
        number=pr_number,
        title=metadata.get("title", ""),
        body=metadata.get("body", ""),
        head_sha=metadata.get("headRefOid", ""),
        base_ref=metadata.get("baseRefName", ""),
        files=files,
        diff=diff,
    )

    output = {
        "context": asdict(context),
        "checks": checks,
    }

    if output_file:
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()