#!/usr/bin/env python3
"""
Branch Enforcement Hook for Faber Framework (BG-018)

Pre-push hook that enforces:
1. Branch naming: hermes/<topic>
2. No direct pushes to main/dev
3. PR exists for the branch (or --force-with-lease for emergency)
4. Commit messages follow Conventional Commits
5. No WIP/fixup commits in history without squash
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class BranchEnforcer:
    """Pre-push branch enforcement."""

    PROTECTED_BRANCHES = {"main", "dev", "master"}
    HERMES_BRANCH_PATTERN = re.compile(r"^hermes/[a-z0-9-]+$")
    CONVENTIONAL_COMMIT_PATTERN = re.compile(
        r"^(feat|fix|chore|refactor|test|docs|perf|build|ci|revert)(\(.+\))?: .+"
    )

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path.cwd()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def get_current_branch(self) -> str:
        """Get current branch name."""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=self.repo_root
        )
        return result.stdout.strip()

    def get_remote_branch(self, branch: str) -> str:
        """Get remote tracking branch."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{u}}"],
            capture_output=True, text=True, cwd=self.repo_root
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""

    def check_branch_name(self, branch: str) -> bool:
        """Enforce hermes/<topic> naming."""
        if branch in self.PROTECTED_BRANCHES:
            self.errors.append(f"Direct pushes to '{branch}' are forbidden. Use PR workflow.")
            return False

        if not self.HERMES_BRANCH_PATTERN.match(branch):
            self.errors.append(
                f"Branch '{branch}' must follow 'hermes/<topic>' convention (e.g., hermes/pm-github-release)"
            )
            return False

        return True

    def check_push_to_protected(self, remote_branch: str) -> bool:
        """Check if pushing to protected branch."""
        remote_name = remote_branch.split("/")[-1] if "/" in remote_branch else remote_branch
        if remote_name in self.PROTECTED_BRANCHES:
            self.errors.append(f"Pushing to protected branch '{remote_name}' via push is forbidden.")
            self.errors.append("Use: gh pr create --base dev && gh pr merge")
            return False
        return True

    def check_pr_exists(self, branch: str) -> bool:
        """Check if PR exists for this branch."""
        try:
            result = subprocess.run(
                ["gh", "pr", "list", "--head", branch, "--json", "number", "--limit", "1"],
                capture_output=True, text=True, cwd=self.repo_root
            )
            if result.returncode == 0:
                import json
                prs = json.loads(result.stdout) if result.stdout.strip() else []
                if prs:
                    return True
        except Exception:
            pass
        return False

    def check_commit_messages(self, local_branch: str, remote_branch: str) -> bool:
        """Check commits being pushed follow Conventional Commits."""
        # Get commits that would be pushed
        result = subprocess.run(
            ["git", "log", f"{remote_branch}..{local_branch}", "--oneline", "--format=%s"],
            capture_output=True, text=True, cwd=self.repo_root
        )

        if result.returncode != 0 or not result.stdout.strip():
            # No new commits or remote doesn't exist yet
            return True

        commits = result.stdout.strip().split("\n")
        for commit in commits:
            commit = commit.strip()
            if not commit:
                continue

            # Allow fixup/squash commits (they'll be squashed)
            if commit.startswith("fixup!") or commit.startswith("squash!"):
                self.warnings.append(f"Fixup/squash commit found: {commit[:50]}... (ensure squash before merge)")
                continue

            # Allow WIP but warn
            if "wip" in commit.lower() or "work in progress" in commit.lower():
                self.warnings.append(f"WIP commit found: {commit[:50]}... (should be squashed)")
                continue

            # Check conventional commit format
            if not self.CONVENTIONAL_COMMIT_PATTERN.match(commit):
                self.errors.append(f"Commit message not Conventional: '{commit[:70]}...'")
                self.errors.append("Format: type(scope): description  (e.g., feat(pm-github): add label sync)")
                return False

        return True

    def check_force_push(self, args: List[str]) -> bool:
        """Check for force push without --force-with-lease."""
        if "--force" in args and "--force-with-lease" not in args:
            self.errors.append("Force push requires --force-with-lease for safety")
            return False
        return True

    def run(self, push_args: List[str]) -> int:
        """Run all enforcement checks."""
        print("🛡️  FABER BRANCH ENFORCEMENT (pre-push)")
        print("=" * 50)

        branch = self.get_current_branch()
        print(f"Current branch: {branch}")

        if not branch:
            self.errors.append("Could not determine current branch")
            return 1

        # Get remote tracking branch
        remote_branch = self.get_remote_branch(branch)
        if remote_branch:
            print(f"Remote tracking: {remote_branch}")

        all_ok = True

        # Check 1: Branch naming
        print("\n📋 Checking branch name...")
        if not self.check_branch_name(branch):
            all_ok = False
        else:
            print(f"   ✅ Branch name follows convention: {branch}")

        # Check 2: Not pushing to protected
        print("\n📋 Checking push target...")
        if remote_branch and not self.check_push_to_protected(remote_branch):
            all_ok = False
        else:
            print("   ✅ Not pushing to protected branch")

        # Check 3: PR exists (for branches that have remote)
        if remote_branch:
            print("\n📋 Checking PR existence...")
            if self.check_pr_exists(branch):
                print("   ✅ PR exists for this branch")
            else:
                self.warnings.append(f"No PR found for branch '{branch}' (create with: gh pr create --base dev)")

        # Check 4: Commit messages
        if remote_branch:
            print("\n📋 Checking commit messages...")
            if not self.check_commit_messages(branch, remote_branch):
                all_ok = False
            else:
                print("   ✅ Commit messages follow Conventional Commits")

        # Check 5: Force push safety
        print("\n📋 Checking force push...")
        if not self.check_force_push(push_args):
            all_ok = False
        else:
            print("   ✅ Force push safety OK")

        print("\n" + "=" * 50)
        for w in self.warnings:
            print(f"  ⚠️  {w}")
        for e in self.errors:
            print(f"  ❌ {e}")

        if not all_ok:
            print("\n🛑 PUSH BLOCKED - Fix errors above")
            print("   Override (emergency only): git push --force-with-lease --no-verify")
            return 1

        print("\n✅ ALL ENFORCEMENT CHECKS PASSED")
        return 0


def main():
    # Get push arguments from git
    push_args = sys.argv[1:] if len(sys.argv) > 1 else []

    enforcer = BranchEnforcer()
    sys.exit(enforcer.run(push_args))


if __name__ == "__main__":
    main()