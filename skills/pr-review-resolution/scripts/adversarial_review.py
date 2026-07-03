#!/usr/bin/env python3
"""
Adversarial review - sends PR diff to LLM for code review.
Uses OpenRouter API to call a different model than the writer.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List


def call_nvidia(model: str, prompt: str, api_key: str) -> str:
    """Call NVIDIA API with the given prompt."""
    import urllib.request
    import json

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert code reviewer. Output ONLY JSON lines. No reasoning, no markdown, no explanation."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8000,
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"].get("content", "")
            # Nemotron includes reasoning_content - use content only
            return content
    except Exception as e:
        return f"ERROR: {e}"


def call_openrouter(model: str, prompt: str, api_key: str) -> str:
    """Call OpenRouter API with the given prompt."""
    import urllib.request
    import json

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ndethi/faber",
        "X-Title": "Faber Adversarial Review",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert code reviewer for the Faber agentic web framework. Find real issues in the code."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


def build_adversarial_prompt(diff: str, changed_files: list) -> str:
    """Build adversarial review prompt."""
    return f"""You are an ADVERSARIAL code reviewer for the Faber framework.

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
For each issue found, output ONE JSON line:
{{
  "file": "path/to/file.py",
  "line": 42,
  "severity": "BLOCKER|CRITICAL|MAJOR|MINOR|NIT",
  "category": "bug|security|design|spec-violation|missing-test|fabrication|nit",
  "message": "Specific, actionable description",
  "suggestion": "Concrete fix suggestion"
}}

Output ONLY JSON lines. No markdown, no explanation."""


def parse_llm_response(response: str) -> List[Dict[str, Any]]:
    """Parse LLM response into list of review comments."""
    comments = []
    for line in response.strip().split('\n'):
        line = line.strip()
        if not line or not line.startswith('{'):
            continue
        try:
            comment = json.loads(line)
            # Validate required fields
            if all(k in comment for k in ('file', 'line', 'severity', 'category', 'message', 'suggestion')):
                comments.append(comment)
        except json.JSONDecodeError:
            continue
    return comments


def post_review_comments(pr_number: int, repo: str, comments: List[Dict[str, Any]], github_token: str):
    """Post review comments to PR via GitHub API."""
    import urllib.request
    import urllib.parse

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for comment in comments:
        body = f"**[{comment['severity']}] {comment['category']}**\n\n{comment['message']}\n\n*Suggestion:* {comment['suggestion']}"
        data = json.dumps({
            "body": body,
            "path": comment["file"],
            "position": comment.get("line", 1),
        }).encode()

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status not in (200, 201):
                    print(f"Failed to post comment: {resp.status}", file=sys.stderr)
        except Exception as e:
            print(f"Error posting comment: {e}", file=sys.stderr)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--pr-number', type=int, required=True)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--provider', choices=['openrouter', 'nvidia'], default='nvidia')
    parser.add_argument('--post-comments', action='store_true')
    args = parser.parse_args()

    # Use NVIDIA API key for NVIDIA provider, OpenRouter key for OpenRouter
    if args.provider == 'nvidia':
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            print(json.dumps({"error": "NVIDIA_API_KEY not set"}))
            sys.exit(1)
        call_fn = call_nvidia
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print(json.dumps({"error": "OPENROUTER_API_KEY not set"}))
            sys.exit(1)
        call_fn = call_openrouter

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}))
        sys.exit(1)

    print(f"🔍 Running adversarial review on PR #{args.pr_number} with {args.model} ({args.provider})", file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Fetch PR diff
        print("📥 Fetching PR diff...", file=sys.stderr)
        diff_cmd = ["gh", "pr", "diff", str(args.pr_number), "--repo", args.repo]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
        if diff_result.returncode != 0:
            print(json.dumps({"error": f"Failed to fetch diff: {diff_result.stderr}"}))
            sys.exit(1)
        diff = diff_result.stdout

        # Get changed files
        files_cmd = ["gh", "pr", "view", str(args.pr_number), "--repo", args.repo, "--json", "files"]
        files_result = subprocess.run(files_cmd, capture_output=True, text=True)
        if files_result.returncode != 0:
            print(json.dumps({"error": f"Failed to fetch files: {files_result.stderr}"}))
            sys.exit(1)
        files_data = json.loads(files_result.stdout)
        changed_files = [f["path"] for f in files_data.get("files", [])]

        # Build prompt and call LLM
        print("🤖 Calling LLM for adversarial review...", file=sys.stderr)
        prompt = build_adversarial_prompt(diff, changed_files)
        llm_response = call_fn(args.model, prompt, api_key)

        if llm_response.startswith("ERROR:"):
            print(json.dumps({"error": llm_response}))
            sys.exit(1)

        # Parse LLM response
        comments = parse_llm_response(llm_response)
        print(f"📝 Parsed {len(comments)} review comments", file=sys.stderr)

        # Post comments if requested
        if args.post_comments and comments:
            print("💬 Posting review comments...", file=sys.stderr)
            post_review_comments(args.pr_number, args.repo, comments, github_token)

        # Output result
        output = {
            "mode": "review",
            "pr_number": args.pr_number,
            "repo": args.repo,
            "model": args.model,
            "provider": args.provider,
            "adversarial": True,
            "changed_files": changed_files,
            "comments_found": len(comments),
            "status": "completed",
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()