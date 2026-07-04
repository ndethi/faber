#!/usr/bin/env python3
"""
Adversarial review: calls a DIFFERENT LLM via OpenRouter to review PR code.
Outputs JSON lines for each issue found, posts as review comments.
"""
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ReviewIssue:
    file: str
    line: int
    severity: str  # BLOCKER, CRITICAL, MAJOR, MINOR, NIT
    category: str  # bug, security, design, spec-violation, missing-test, fabrication, nit
    message: str
    suggestion: str


def build_adversarial_prompt(diff: str, changed_files: List[str]) -> str:
    """Build adversarial review prompt for LLM."""
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
For each issue found, output ONE JSON line (no extra text):
{{
  "file": "path/to/file.py",
  "line": 42,
  "severity": "BLOCKER|CRITICAL|MAJOR|MINOR|NIT",
  "category": "bug|security|design|spec-violation|missing-test|fabrication|nit",
  "message": "Specific, actionable description",
  "suggestion": "Concrete fix suggestion"
}}

If no issues found, output: {{"status": "no_issues"}}

IMPORTANT: Output ONLY valid JSON lines. No markdown, no explanation."""


def call_openrouter(model: str, prompt: str, api_key: str, max_retries: int = 3) -> str:
    """Call OpenRouter API with the given model and prompt, with retry on rate limit."""
    import requests
    import time

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    for attempt in range(max_retries):
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
        )
        if response.status_code == 429:
            wait_time = 2 ** attempt * 5  # 5s, 10s, 20s
            print(f"Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            time.sleep(wait_time)
            continue
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    # If all retries exhausted, raise
    raise RuntimeError(f"Rate limited after {max_retries} retries")


def call_nvidia_nemotron(prompt: str, api_key: str, max_retries: int = 2) -> str:
    """Call NVIDIA Nemotron API as fallback."""
    import requests
    import re
    import time

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    for attempt in range(max_retries):
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
        )
        if response.status_code == 503:
            wait_time = 5 * (attempt + 1)
            print(f"NVIDIA 503, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            time.sleep(wait_time)
            continue
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Nemotron includes reasoning in  tags - strip it
        content = re.sub(r"", "", content, flags=re.DOTALL)
        return content.strip()

    raise RuntimeError(f"NVIDIA unavailable after {max_retries} retries")


def parse_llm_response(response: str) -> List[ReviewIssue]:
    """Parse LLM response into ReviewIssue objects."""
    issues = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("status") == "no_issues":
                continue
            issues.append(ReviewIssue(
                file=data["file"],
                line=int(data["line"]),
                severity=data["severity"],
                category=data["category"],
                message=data["message"],
                suggestion=data.get("suggestion", "N/A"),
            ))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to parse line: {line[:100]}... ({e})", file=sys.stderr)
    return issues


def post_review_comments(pr_number: int, repo: str, issues: List[ReviewIssue], github_token: str) -> int:
    """Post all review comments as a single review."""
    if not issues:
        return 0

    # Get the latest commit SHA
    cmd_sha = ["gh", "api", f"/repos/{repo}/pulls/{pr_number}", "-q", ".head.sha"]
    env = os.environ.copy()
    env["GH_TOKEN"] = github_token
    sha_result = subprocess.run(cmd_sha, capture_output=True, text=True, env=env)
    if sha_result.returncode != 0:
        print(f"Failed to get commit SHA: {sha_result.stderr}", file=sys.stderr)
        return 0
    commit_sha = sha_result.stdout.strip()

    # Build comments array
    import json as json_mod
    comments = []
    for issue in issues:
        body = f"**[{issue.severity}] {issue.category}**\n\n{issue.message}\n\n*Suggestion:* {issue.suggestion}"
        comments.append({
            "path": issue.file,
            "position": issue.line,
            "body": body,
            "side": "RIGHT"
        })

    review_data = {
        "commit_id": commit_sha,
        "body": f"Adversarial review found {len(issues)} issues",
        "event": "COMMENT",
        "comments": comments
    }

    cmd = [
        "gh", "api", "--method", "POST",
        f"/repos/{repo}/pulls/{pr_number}/reviews",
        "--input", "-",
    ]
    env = os.environ.copy()
    env["GH_TOKEN"] = github_token
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, input=json_mod.dumps(review_data))
    if result.returncode != 0:
        print(f"Failed to post review: {result.stderr}", file=sys.stderr)
        return 0
    return len(issues)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--post-comments", action="store_true")
    args = parser.parse_args()

    # Get credentials
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    nvidia_key = os.environ.get("NVIDIA_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    if not openrouter_key:
        print(json.dumps({"error": "OPENROUTER_API_KEY not set"}))
        sys.exit(1)
    if not github_token:
        print(json.dumps({"error": "GITHUB_TOKEN not set"}))
        sys.exit(1)

    print(f"🔍 Running adversarial review on PR #{args.pr_number} with {args.model}", file=sys.stderr)

    # Step 1: Fetch PR diff
    print("📥 Fetching PR diff...", file=sys.stderr)
    diff_cmd = ["gh", "pr", "diff", str(args.pr_number), "--repo", args.repo]
    env = os.environ.copy()
    env["GH_TOKEN"] = github_token
    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, env=env)
    if diff_result.returncode != 0:
        print(json.dumps({"error": f"Failed to fetch diff: {diff_result.stderr}"}))
        sys.exit(1)
    diff = diff_result.stdout

    # Step 2: Get changed files
    files_cmd = ["gh", "pr", "view", str(args.pr_number), "--repo", args.repo, "--json", "files"]
    files_result = subprocess.run(files_cmd, capture_output=True, text=True, env=env)
    if files_result.returncode != 0:
        print(json.dumps({"error": f"Failed to fetch files: {files_result.stderr}"}))
        sys.exit(1)
    files_data = json.loads(files_result.stdout)
    changed_files = [f["path"] for f in files_data.get("files", [])]

    # Step 3: Call LLM for adversarial review (try OpenRouter first, fallback to NVIDIA)
    print("🤖 Calling adversarial LLM...", file=sys.stderr)
    prompt = build_adversarial_prompt(diff, changed_files)
    llm_response = None
    model_used = None
    try:
        llm_response = call_openrouter(args.model, prompt, openrouter_key)
        model_used = f"openrouter:{args.model}"
    except Exception as e:
        print(f"OpenRouter failed: {e}, trying NVIDIA fallback...", file=sys.stderr)
        if not nvidia_key:
            print("No NVIDIA_API_KEY available, skipping adversarial review", file=sys.stderr)
        else:
            try:
                llm_response = call_nvidia_nemotron(prompt, nvidia_key)
                model_used = "nvidia/nemotron-3-ultra-550b-a55b"
            except Exception as e2:
                print(f"NVIDIA fallback failed: {e2}, skipping adversarial review", file=sys.stderr)

    if llm_response is None:
        print("⚠️  Both LLMs unavailable, skipping adversarial review", file=sys.stderr)
        issues = []
    else:
        # Step 4: Parse response
        print("📝 Parsing LLM response...", file=sys.stderr)
        issues = parse_llm_response(llm_response)
        print(f"Found {len(issues)} issues", file=sys.stderr)

    # Step 5: Post comments if requested
    posted = 0
    if args.post_comments and issues:
        print("💬 Posting review comments...", file=sys.stderr)
        posted = post_review_comments(args.pr_number, args.repo, issues, github_token)

    # Output result
    output = {
        "mode": "adversarial_review",
        "pr_number": args.pr_number,
        "repo": args.repo,
        "model": model_used or "unavailable",
        "changed_files": changed_files,
        "issues_found": len(issues),
        "comments_posted": posted,
        "status": "completed",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()