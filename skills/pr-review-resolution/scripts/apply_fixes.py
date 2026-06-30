#!/usr/bin/env python3
"""
Apply and push fixes to the PR branch.
Handles git operations: commit, push, branch management.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


def run_cmd(cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def get_current_branch(repo_root: Path) -> str:
    result = run_cmd(["git", "branch", "--show-current"], repo_root)
    return result.stdout.strip()


def ensure_on_pr_branch(repo_root: Path, pr_number: int, repo: str) -> str:
    """Ensure we're on the correct branch for the PR."""
    # Try to find existing hermes branch for this PR
    branch_name = f"hermes/pr-{pr_number}-fixes"

    # Check if branch exists locally
    result = run_cmd(["git", "branch", "--list", branch_name], repo_root)
    if result.stdout.strip():
        run_cmd(["git", "checkout", branch_name], repo_root)
        return branch_name

    # Create new branch from current
    run_cmd(["git", "checkout", "-b", branch_name], repo_root)
    return branch_name


def push_branch(repo_root: Path, branch_name: str) -> bool:
    """Push branch to origin."""
    result = run_cmd(["git", "push", "-u", "origin", branch_name], repo_root)
    return result.returncode == 0


def apply_and_push(
    repo_root: Path,
    pr_number: int,
    repo: str,
    fix_results: List[Dict[str, Any]],
    hitl_gate: bool = True,
) -> Dict[str, Any]:
    """Apply fixes, commit, push to PR branch."""
    branch = get_current_branch(repo_root)

    # If not on a hermes branch, create/switch to one
    if not branch.startswith("hermes/"):
        branch = ensure_on_pr_branch(repo_root, pr_number, repo)

    # Get applied fixes
    applied = [r for r in fix_results if r.get("status") == "applied"]
    if not applied:
        return {"branch": branch, "pushed": False, "reason": "No fixes to apply"}

    # Commit
    commit_shas = [r.get("commit_sha") for r in applied if r.get("commit_sha")]

    # Push (skip if HITL gate enabled)
    pushed = False
    if not hitl_gate:
        pushed = push_branch(repo_root, branch)

    return {
        "branch": branch,
        "pushed": pushed,
        "applied_count": len(applied),
        "commit_shas": commit_shas,
        "hitl_gate": hitl_gate,
    }


def main():
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: apply_fixes.py <results.json> <pr_number> <repo> [--hitl-gate]"}))
        sys.exit(1)

    input_file = sys.argv[1]
    pr_number = int(sys.argv[2])
    repo = sys.argv[3]
    hitl_gate = "--hitl-gate" in sys.argv
    repo_root = Path.cwd()

    try:
        with open(input_file) as f:
            data = json.load(f)

        fix_results = data.get("results", [])
        result = apply_and_push(repo_root, pr_number, repo, fix_results, hitl_gate)

        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()