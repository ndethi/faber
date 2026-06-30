#!/usr/bin/env python3
"""
Resolve categorized comments by applying fixes.
Supports: auto (style/docs/test), llm (logic/design), defer (security/unknown)
"""
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class FixResult:
    comment_id: int
    status: str  # applied, skipped, failed, deferred
    fix_type: str  # auto, llm, defer
    commit_sha: Optional[str] = None
    error: Optional[str] = None
    diff: Optional[str] = None
    category: Optional[str] = None
    path: Optional[str] = None


def run_cmd(cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def apply_style_fixes(repo_root: Path, files: List[str]) -> List[str]:
    """Apply auto-formatting tools to files. Returns list of modified files."""
    modified = []
    for file in files:
        fpath = repo_root / file
        if not fpath.exists():
            continue

        # Python files: ruff + black
        if file.endswith(".py"):
            # ruff --fix
            result = run_cmd(["ruff", "check", "--fix", str(fpath)], repo_root)
            if result.returncode == 0:
                modified.append(file)
            # black
            result = run_cmd(["black", "--quiet", str(fpath)], repo_root)
            if result.returncode == 0:
                if file not in modified:
                    modified.append(file)

        # JS/TS files: prettier
        elif file.endswith((".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".yaml", ".yml")):
            result = run_cmd(["npx", "prettier", "--write", str(fpath)], repo_root)
            if result.returncode == 0:
                modified.append(file)

    return modified


def apply_doc_fixes(repo_root: Path, comment: dict) -> bool:
    """Apply documentation fixes (placeholder - would need LLM for real content)."""
    # For now, just mark as needing human input for content
    # Could integrate with LLM to generate docstrings
    return False


def apply_test_fixes(repo_root: Path, comment: dict) -> bool:
    """Generate test stubs for missing tests (placeholder)."""
    # Could generate pytest template
    return False


def apply_llm_fix(repo_root: Path, comment: dict, context: Dict[str, Any]) -> Optional[str]:
    """Apply LLM-generated fix (placeholder - would call LLM API)."""
    # This would:
    # 1. Get file context around comment line
    # 2. Prompt LLM with comment + context
    # 3. Parse diff from response
    # 4. Apply and test
    return None


def get_git_diff(repo_root: Path) -> str:
    """Get current git diff."""
    result = run_cmd(["git", "diff"], repo_root)
    return result.stdout


def git_commit(repo_root: Path, message: str, files: List[str]) -> Optional[str]:
    """Commit changes and return SHA."""
    if not files:
        return None

    run_cmd(["git", "add"] + files, repo_root)
    result = run_cmd(["git", "commit", "-m", message], repo_root)
    if result.returncode != 0:
        return None

    # Get commit SHA
    result = run_cmd(["git", "rev-parse", "HEAD"], repo_root)
    return result.stdout.strip() if result.returncode == 0 else None


def resolve_comments(
    repo_root: Path,
    categorized: List[dict],
    hitl_gate: bool = True,
) -> List[FixResult]:
    """Resolve all categorized comments."""
    results = []
    auto_files = set()
    llm_fixes = []

    for cat in categorized:
        cid = cat["id"]
        category = cat["category"]
        fix_type = cat["suggested_fix_type"]
        path = cat["path"]

        try:
            if fix_type == "auto" and path:
                if category == "style":
                    modified = apply_style_fixes(repo_root, [path])
                    if modified:
                        auto_files.update(modified)
                        results.append(FixResult(cid, "applied", "auto", category=category, path=path))
                    else:
                        results.append(FixResult(cid, "skipped", "auto", error="No changes from formatter", category=category, path=path))
                elif category == "docs":
                    if apply_doc_fixes(repo_root, cat):
                        auto_files.add(path)
                        results.append(FixResult(cid, "applied", "auto", category=category, path=path))
                    else:
                        results.append(FixResult(cid, "deferred", "auto", error="Doc content needs human", category=category, path=path))
                elif category == "test":
                    if apply_test_fixes(repo_root, cat):
                        auto_files.add(path)
                        results.append(FixResult(cid, "applied", "auto", category=category, path=path))
                    else:
                        results.append(FixResult(cid, "deferred", "auto", error="Test template needs human", category=category, path=path))
                else:
                    results.append(FixResult(cid, "deferred", "auto", error=f"Unknown auto category: {category}", category=category, path=path))

            elif fix_type == "llm":
                # Would call LLM here with context
                diff = apply_llm_fix(repo_root, cat, {})
                if diff:
                    # Apply diff, test, commit
                    results.append(FixResult(cid, "applied", "llm", diff=diff, category=category, path=path))
                else:
                    results.append(FixResult(cid, "deferred", "llm", error="LLM fix not implemented", category=category, path=path))

            else:  # defer
                results.append(FixResult(cid, "deferred", "defer", error="Requires human review", category=category, path=path))

        except Exception as e:
            results.append(FixResult(cid, "failed", fix_type, error=str(e), category=category, path=path))

    # Commit auto fixes if any
    if auto_files:
        commit_msg = f"fix: auto-resolve PR review comments (style/docs/test)\n\n" \
                     f"Resolves: {[r.comment_id for r in results if r.status == 'applied' and r.fix_type == 'auto']}"
        sha = git_commit(repo_root, commit_msg, list(auto_files))
        for r in results:
            if r.status == "applied" and r.fix_type == "auto":
                r.commit_sha = sha

    return results


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: resolve.py <categorized.json> <repo_root> [--hitl]"}))
        sys.exit(1)

    input_file = sys.argv[1]
    repo_root = Path(sys.argv[2]).resolve()
    hitl_gate = "--hitl" in sys.argv

    try:
        with open(input_file) as f:
            data = json.load(f)

        categorized = data.get("categorized", [])
        results = resolve_comments(repo_root, categorized, hitl_gate)

        output = {
            "results": [asdict(r) for r in results],
            "summary": {
                "applied": sum(1 for r in results if r.status == "applied"),
                "deferred": sum(1 for r in results if r.status == "deferred"),
                "failed": sum(1 for r in results if r.status == "failed"),
                "skipped": sum(1 for r in results if r.status == "skipped"),
            },
        }
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()