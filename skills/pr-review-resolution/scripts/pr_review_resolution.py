#!/usr/bin/env python3
"""
Main entry point for pr-review-resolution skill.
Orchestrates the full pipeline: fetch → categorize → resolve → apply → update → notify
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


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "pr_review_resolution.py <mode> [args...]",
            "modes": {
                "resolve": "<pr_number> <repo> [--hitl] [--no-notify]",
                "analyze": "<repo> <since_YYYY-MM-DD> <output.json> [limit]",
            }
        }))
        sys.exit(1)

    mode = sys.argv[1]
    repo_root = Path(__file__).parent.parent.parent.parent  # scripts/ -> pr-review-resolution/ -> skills/ -> repo root

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
            resolve_result = run_script(
                "resolve.py", resolve_args,
                repo_root
            )
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
                # Combine data for notifications
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
        print(json.dumps({"error": f"Unknown mode: {mode}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()