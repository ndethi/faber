#!/usr/bin/env python3
"""
Main entry point for pr-review-resolution skill.
Orchestrates the full pipeline: fetch → categorize → resolve → apply → update → notify

Supports modes:
- resolve: Fix review comments on a PR
- analyze: Analyze PR patterns over time  
- review: Adversarial review of a PR (different model than writer)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List


def run_script(script: str, args: List[str], repo_root: Path) -> Dict[str, Any]:
    """Run a script and return parsed JSON output."""
    cmd = [sys.executable, str(repo_root / "skills" / "pr-review-resolution" / "scripts" / script)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root, timeout=300)
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout, "returncode": result.returncode}
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"error": "Invalid JSON output", "stdout": result.stdout[:500]}


def run_adversarial_review(pr_number: int, repo: str, model: str, adversarial: bool, post_comments: bool, repo_root: Path):
    """Run adversarial review on a PR using a different model."""
    import subprocess
    
    print(f"🔍 Running adversarial review on PR #{pr_number} with {model}", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Step 1: Fetch PR diff and files
        print("📥 Fetching PR diff...", file=sys.stderr)
        diff_file = tmpdir / "pr.diff"
        diff_cmd = ["gh", "pr", "diff", str(pr_number), "--repo", repo]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
        if diff_result.returncode != 0:
            print(json.dumps({"error": f"Failed to fetch diff: {diff_result.stderr}"}))
            sys.exit(1)
        diff_file.write_text(diff_result.stdout)
        
        # Step 2: Get changed files
        files_cmd = ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "files"]
        files_result = subprocess.run(files_cmd, capture_output=True, text=True)
        if files_result.returncode != 0:
            print(json.dumps({"error": f"Failed to fetch files: {files_result.stderr}"}))
            sys.exit(1)
        files_data = json.loads(files_result.stdout)
        changed_files = [f["path"] for f in files_data.get("files", [])]
        
        # Step 3: Run adversarial categorization
        print("🏷️  Running adversarial categorization...", file=sys.stderr)
        
        # Fetch comments first
        fetch_result = run_script("fetch_comments.py", [str(pr_number), repo], repo_root)
        if "error" not in fetch_result:
            fetch_file = tmpdir / "fetched.json"
            fetch_file.write_text(json.dumps(fetch_result))
            
            # Categorize with adversarial flag
            cat_result = run_script("categorize.py", [str(fetch_file), "--adversarial"], repo_root)
            if "error" not in cat_result:
                cat_file = tmpdir / "categorized.json"
                cat_file.write_text(json.dumps(cat_result))
                
                if post_comments:
                    print("💬 Posting review comments...", file=sys.stderr)
                    post_review_comments(pr_number, repo, cat_result, repo_root)
        
        output = {
            "mode": "review",
            "pr_number": pr_number,
            "repo": repo,
            "model": model,
            "adversarial": adversarial,
            "changed_files": changed_files,
            "status": "completed",
        }
        print(json.dumps(output, indent=2))


def build_adversarial_prompt(diff: str, changed_files: list, adversarial: bool) -> str:
    """Build adversarial review prompt."""
    mode = "ADVERSARIAL" if adversarial else "STANDARD"
    return f"""
You are an {mode} code reviewer for the Faber framework.

## Context
- Framework: Faber agentic web framework
- Skills must follow: SKILL.md + scripts/ + evals/
- No fabrication: unknowns = TODO:
- Deterministic scripts, model only orchestrates
- FRAMEWORK.md contract compliance required

## Changed Files
{chr(10).join(changed_files)}

## Diff
{diff[:15000]}

## Review Criteria
1. **Correctness** - Logic errors, edge cases, error handling
2. **Security** - Injection, auth, secrets, validation
3. **Design** - Coupling, abstraction, FRAMEWORK.md compliance
4. **Spec Violation** - Deviates from skill contract
5. **Missing Tests** - No evals, incomplete coverage
6. **Fabrication** - Invents facts, no TODO: for unknowns
7. **Non-determinism** - Scripts must be deterministic

## Output Format
For each issue found, output JSON lines:
{{
  "file": "path/to/file.py",
  "line": 42,
  "severity": "BLOCKER|CRITICAL|MAJOR|MINOR|NIT",
  "category": "bug|security|design|spec-violation|missing-test|fabrication|nit",
  "message": "Specific, actionable description",
  "suggestion": "Concrete fix suggestion"
}}
"""


def post_review_comments(pr_number: int, repo: str, cat_result: dict, repo_root: Path):
    """Post review comments to PR."""
    import subprocess
    
    for comment in cat_result.get("comments", []):
        if comment.get("severity") in ("BLOCKER", "CRITICAL", "MAJOR"):
            body = f"**[{comment['severity']}] {comment['category']}**\n\n{comment['message']}\n\n*Suggestion:* {comment.get('suggestion', 'N/A')}"
            cmd = [
                "gh", "api", "--method", "POST",
                f"/repos/{repo}/pulls/{pr_number}/comments",
                "-f", f"body={body}",
                "-f", f"path={comment['file']}",
                "-f", f"position={comment.get('line', 1)}"
            ]
            subprocess.run(cmd, capture_output=True)


def main():
    """Main entry point with support for both positional and flag-based modes."""
    import argparse
    
    # Pre-parse to handle both styles
    args = sys.argv[1:]
    mode = None
    if args and not args[0].startswith('-'):
        mode = args[0]
    else:
        # Use argparse for flag-based
        parser = argparse.ArgumentParser()
        parser.add_argument('--mode', choices=['resolve', 'analyze', 'review'])
        parser.add_argument('--pr-number', type=int)
        parser.add_argument('--repo')
        parser.add_argument('--model')
        parser.add_argument('--adversarial', action='store_true')
        parser.add_argument('--post-comments', action='store_true')
        parser.add_argument('--hitl', action='store_true')
        parser.add_argument('--no-notify', action='store_true')
        parser.add_argument('--since')
        parser.add_argument('--output')
        parser.add_argument('--limit', type=int)
        parsed, _ = parser.parse_known_args(args)
        mode = parsed.mode

    repo_root = Path(__file__).parent.parent.parent.parent  # scripts/ -> pr-review-resolution/ -> skills/ -> repo root

    if mode == "review":
        parser = argparse.ArgumentParser()
        parser.add_argument('--pr-number', type=int, required=True)
        parser.add_argument('--repo', required=True)
        parser.add_argument('--model', required=True)
        parser.add_argument('--adversarial', action='store_true')
        parser.add_argument('--post-comments', action='store_true')
        # fixed: "store_true"
        review_args = parser.parse_args(args)
        
        run_adversarial_review(review_args.pr_number, review_args.repo, review_args.model, review_args.adversarial, review_args.post_comments, repo_root)
        return

    if mode == "resolve":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Usage: resolve <pr_number> <repo> [--hitl] [--no-notify]"}))
            sys.exit(1)

        pr_number = int(sys.argv[2])
        repo = sys.argv[3]
        hitl_gate = "--hitl" in sys.argv
        no_notify = "--no-notify" in sys.argv

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Step 1: Fetch comments
            print("📥 Fetching review comments...", file=sys.stderr)
            fetch_result = run_script("fetch_comments.py", [str(pr_number), repo], repo_root)
            if "error" in fetch_result:
                print(json.dumps({"error": f"Fetch failed: {fetch_result['error']}"}))
                sys.exit(1)

            fetch_file = tmpdir / "fetched.json"
            fetch_file.write_text(json.dumps(fetch_result))

            # Notify: fetch
            if not no_notify:
                run_script("notify.py", ["fetch", str(fetch_file)], repo_root)

            # Step 2: Categorize
            print("🏷️  Categorizing comments...", file=sys.stderr)
            cat_result = run_script("categorize.py", [str(fetch_file)], repo_root)
            if "error" in cat_result:
                print(json.dumps({"error": f"Categorize failed: {cat_result['error']}"}))
                sys.exit(1)

            cat_file = tmpdir / "categorized.json"
            cat_file.write_text(json.dumps(cat_result))

            # Step 3: Resolve
            print("🔧 Resolving comments...", file=sys.stderr)
            resolve_args = [str(cat_file), str(repo_root)]
            if hitl_gate:
                resolve_args.append("--hitl")
            resolve_result = run_script("resolve.py", resolve_args, repo_root)
            if "error" in resolve_result:
                print(json.dumps({"error": f"Resolve failed: {resolve_result['error']}"}))
                sys.exit(1)

            resolve_file = tmpdir / "resolved.json"
            resolve_file.write_text(json.dumps(resolve_result))

            # Step 4: Apply fixes (commit + push)
            print("📤 Applying fixes...", file=sys.stderr)
            apply_result = run_script(
                "apply_fixes.py", [str(resolve_file), str(pr_number), repo, "--hitl-gate" if hitl_gate else ""],
                repo_root
            )
            if "error" in apply_result:
                print(json.dumps({"error": f"Apply failed: {apply_result['error']}"}))
                sys.exit(1)

            # Step 5: Update PR with resolution comments
            print("💬 Updating PR...", file=sys.stderr)
            update_result = run_script("update_pr.py", [str(resolve_file), str(pr_number), repo], repo_root)
            if "error" in update_result:
                print(json.dumps({"error": f"Update PR failed: {update_result['error']}"}))
                sys.exit(1)

            # Notify: resolve + push
            if not no_notify:
                combined = {
                    "pr_number": pr_number,
                    "repo": repo,
                    "summary": resolve_result.get("summary", {}),
                    "branch": apply_result.get("branch", ""),
                    "commit_shas": apply_result.get("commit_shas", []),
                    "deferred": [
                        {"comment_id": r["comment_id"], "category": r.get("category"),
                         "path": r.get("path"), "error": r.get("error")}
                        for r in resolve_result.get("results", [])
                        if r.get("status") == "deferred"
                    ],
                }
                combined_file = tmpdir / "combined.json"
                combined_file.write_text(json.dumps(combined))
                run_script("notify.py", ["resolve", str(combined_file)], repo_root)
                run_script("notify.py", ["push", str(combined_file)], repo_root)
                if combined["deferred"]:
                    run_script("notify.py", ["hitl", str(combined_file)], repo_root)

            # Final output
            output = {
                "mode": "resolve",
                "pr_number": pr_number,
                "repo": repo,
                "fetch": fetch_result,
                "categorized": cat_result,
                "resolved": resolve_result,
                "applied": apply_result,
                "updated": update_result,
            }
            print(json.dumps(output, indent=2))

    elif mode == "analyze":
        if len(sys.argv) < 5:
            print(json.dumps({"error": "Usage: analyze <repo> <since_YYYY-MM-DD> <output.json> [limit]"}))
            sys.exit(1)

        repo = sys.argv[2]
        since = sys.argv[3]
        output_file = sys.argv[4]
        limit = int(sys.argv[5]) if len(sys.argv) > 5 else 50

        print(f"📊 Analyzing {repo} PRs since {since}...", file=sys.stderr)
        result = run_script("analyze.py", [repo, since, output_file, str(limit)], repo_root)

        if "error" in result:
            print(json.dumps({"error": result["error"]}))
            sys.exit(1)

        print(json.dumps(result, indent=2))

    else:
        print(json.dumps({"error": f"Unknown mode: {mode}. Use: resolve, analyze, or review"}))
        sys.exit(1)


if __name__ == "__main__":
    main()