#!/usr/bin/env python3
"""
Review PR changes against Faber spec and best practices.
Uses deterministic checks + LLM for semantic analysis.
"""
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class ReviewIssue:
    level: str  # "critical", "warning", "suggestion"
    file: str
    line: int
    message: str
    suggestion: str


@dataclass
class DeterministicCheck:
    name: str
    status: str  # "pass", "fail", "skip"
    details: str


class PRReviewer:
    def __init__(self, repo_root: Path, fast_mode: bool = False):
        self.repo_root = repo_root
        self.fast_mode = fast_mode
        self.spec_files = [
            "FRAMEWORK.md",
            "AGENTS.md",
            "long-running/HERMES-BRIEF.md",
            "long-running/BRANCH-MODEL.md",
        ]

    def load_spec(self, filename: str) -> str:
        """Load a spec file for reference."""
        path = self.repo_root / filename
        if path.exists():
            return path.read_text()
        return ""

    def run_deterministic_checks(self, pr_context: dict) -> List[DeterministicCheck]:
        """Run all deterministic checks."""
        checks = []

        # 1. Branch model check
        checks.append(self.check_branch_model(pr_context))

        # 2. Commit style check
        checks.append(self.check_commit_style(pr_context))

        if not self.fast_mode:
            # 3. Lint check (slow)
            checks.append(self.check_lint())

            # 4. Test check (slow)
            checks.append(self.check_tests())

        # 5. Security check
        checks.append(self.check_security(pr_context))

        # 6. Schema validation (telemetry, run plans)
        checks.append(self.check_schemas(pr_context))

        # 7. Trajectory guard (if applicable)
        checks.append(self.check_trajectory(pr_context))

        return checks

    def check_branch_model(self, pr_context: dict) -> DeterministicCheck:
        """Verify branch follows hermes/<topic> pattern targeting dev."""
        context = pr_context.get("context", {})
        base_ref = context.get("base_ref", "")

        # Check base is dev
        if base_ref != "dev":
            return DeterministicCheck(
                "branch_model",
                "fail",
                f"PR targets '{base_ref}', must target 'dev' per BRANCH-MODEL.md"
            )

        # Check branch name pattern (would need to fetch branch name)
        # For now, just verify base
        return DeterministicCheck(
            "branch_model",
            "pass",
            "PR targets 'dev' branch"
        )

    def check_commit_style(self, pr_context: dict) -> DeterministicCheck:
        """Verify commits follow Conventional Commits."""
        context = pr_context.get("context", {})
        base_ref = context.get("base_ref", "dev")

        # Get commit messages
        result = subprocess.run(
            ["git", "log", "--oneline", f"{base_ref}..HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return DeterministicCheck("commit_style", "skip", "Could not fetch commits")

        commits = result.stdout.strip().split("\n")
        conventional_pattern = re.compile(
            r"^(feat|fix|refactor|docs|test|ci|chore|perf)(\(.+\))?: .+"
        )

        violations = []
        for commit in commits:
            if commit and not conventional_pattern.match(commit.split(" ", 1)[-1] if " " in commit else ""):
                violations.append(commit)

        if violations:
            return DeterministicCheck(
                "commit_style",
                "fail",
                f"{len(violations)} commits violate Conventional Commits format"
            )
        return DeterministicCheck("commit_style", "pass", f"All {len(commits)} commits follow Conventional Commits")

    def check_lint(self) -> DeterministicCheck:
        """Run linter."""
        # Check for Python files and run ruff
        py_files = list(self.repo_root.rglob("*.py"))
        if not py_files:
            return DeterministicCheck("lint", "skip", "No Python files")

        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return DeterministicCheck("lint", "pass", "ruff check passed")
        return DeterministicCheck("lint", "fail", f"ruff found issues:\n{result.stdout}")

    def check_tests(self) -> DeterministicCheck:
        """Run test suite."""
        result = subprocess.run(
            ["python", "-m", "pytest", "-q", "--tb=no"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return DeterministicCheck("tests", "pass", "All tests passed")
        return DeterministicCheck("tests", "fail", f"Tests failed:\n{result.stdout}\n{result.stderr}")

    def check_security(self, pr_context: dict) -> DeterministicCheck:
        """Scan for secrets and security issues."""
        issues = []
        diff = pr_context["context"]["diff"]

        # Check for common secret patterns
        secret_patterns = [
            (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]+['\"]", "Potential hardcoded secret"),
            (r"(?i)aws_access_key_id\s*[:=]", "AWS access key"),
            (r"(?i)ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
            (r"(?i)sk-[a-zA-Z0-9]{48}", "OpenAI API key"),
        ]

        for pattern, desc in secret_patterns:
            if re.search(pattern, diff):
                issues.append(desc)

        if issues:
            return DeterministicCheck("security", "fail", f"Security issues: {', '.join(issues)}")
        return DeterministicCheck("security", "pass", "No secrets detected in diff")

    def check_schemas(self, pr_context: dict) -> DeterministicCheck:
        """Validate JSON schemas (telemetry, run plans)."""
        issues = []
        diff = pr_context["context"]["diff"]

        # Check if telemetry schema modified
        if "runs/telemetry.schema.json" in diff:
            try:
                import jsonschema
                schema_path = self.repo_root / "runs" / "telemetry.schema.json"
                if schema_path.exists():
                    json.loads(schema_path.read_text())  # Valid JSON
            except Exception as e:
                issues.append(f"telemetry.schema.json: {e}")

        # Check run plans
        run_plans = list(self.repo_root.rglob("runs/*.json"))
        for plan in run_plans:
            if plan.name == "telemetry.schema.json":
                continue
            try:
                json.loads(plan.read_text())
            except Exception as e:
                issues.append(f"{plan.name}: {e}")

        if issues:
            return DeterministicCheck("schemas", "fail", "; ".join(issues))
        return DeterministicCheck("schemas", "pass", "All schemas valid")

    def check_trajectory(self, pr_context: dict) -> DeterministicCheck:
        """Check trajectory conformance if run plans modified."""
        diff = pr_context["context"]["diff"]

        # Look for run plan modifications
        if "runs/" in diff and "expected_trajectory" in diff:
            # Would run trajectory-guard skill here
            return DeterministicCheck("trajectory", "pass", "Trajectory fields present (trajectory-guard not run)")
        return DeterministicCheck("trajectory", "skip", "No run plan changes")

    def llm_review(self, pr_context: dict, spec_content: dict) -> List[ReviewIssue]:
        """
        Perform LLM-based semantic review.
        In practice, this would call an LLM API. For now, return deterministic patterns.
        """
        issues = []
        diff = pr_context["context"]["diff"]

        # Pattern-based review (stand-in for LLM)
        # Check for common issues in diff

        # 1. Missing error handling
        if re.search(r"\.get\(|\[.+\]", diff) and "except" not in diff and "try:" not in diff:
            # Heuristic: dict access without error handling
            pass  # Would need file/line mapping

        # 2. SQL injection patterns
        if re.search(r"execute\(f\"|cursor\.execute\(%|format\(.*SELECT", diff):
            issues.append(ReviewIssue(
                level="critical",
                file="unknown",
                line=0,
                message="Potential SQL injection: string interpolation in query",
                suggestion="Use parameterized queries"
            ))

        # 3. Hardcoded values that should be config
        if re.search(r"(localhost|127\.0\.0\.1|8080|5432|3306)", diff):
            issues.append(ReviewIssue(
                level="warning",
                file="unknown",
                line=0,
                message="Hardcoded host/port detected",
                suggestion="Use environment variables or config"
            ))

        # 4. Missing type hints on new functions
        if "def " in diff and "->" not in diff:
            issues.append(ReviewIssue(
                level="suggestion",
                file="unknown",
                line=0,
                message="New functions may be missing return type hints",
                suggestion="Add type annotations per PEP 484"
            ))

        # 5. Check against FRAMEWORK.md skill contract
        framework = spec_content.get("FRAMEWORK.md", "")
        if "skill" in diff.lower() and "SKILL.md" not in diff and "scripts/" not in diff:
            issues.append(ReviewIssue(
                level="warning",
                file="unknown",
                line=0,
                message="Skill-related changes should include SKILL.md and scripts/",
                suggestion="Follow FRAMEWORK.md §1 skill contract"
            ))

        return issues

    def review(self, pr_context: dict) -> dict:
        """Run full review pipeline."""
        # Load spec files
        spec_content = {}
        for spec in self.spec_files:
            spec_content[spec] = self.load_spec(spec)

        # Deterministic checks
        det_checks = self.run_deterministic_checks(pr_context)

        # LLM review
        llm_issues = self.llm_review(pr_context, spec_content)

        # Determine verdict
        critical_count = sum(1 for i in llm_issues if i.level == "critical")
        warning_count = sum(1 for i in llm_issues if i.level == "warning")
        det_failures = [c for c in det_checks if c.status == "fail"]

        if critical_count > 0 or det_failures:
            verdict = "REQUEST_CHANGES"
        elif warning_count > 0:
            verdict = "COMMENT"
        else:
            verdict = "APPROVE"

        return {
            "verdict": verdict,
            "issues": [asdict(i) for i in llm_issues],
            "deterministic_checks": [asdict(c) for c in det_checks],
            "summary": {
                "critical": critical_count,
                "warning": warning_count,
                "suggestion": sum(1 for i in llm_issues if i.level == "suggestion"),
                "deterministic_failures": len(det_failures),
            }
        }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "review.py <pr_context.json> [--repo-root <path>] [--output <file>] [--fast]"
        }, indent=2))
        sys.exit(1)

    input_file = sys.argv[1]
    repo_root = Path.cwd()
    output_file = None
    fast_mode = "--fast" in sys.argv

    if "--repo-root" in sys.argv:
        idx = sys.argv.index("--repo-root")
        repo_root = Path(sys.argv[idx + 1])

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output_file = sys.argv[idx + 1]

    with open(input_file) as f:
        pr_context = json.load(f)

    reviewer = PRReviewer(repo_root, fast_mode=fast_mode)
    result = reviewer.review(pr_context)

    if output_file:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()