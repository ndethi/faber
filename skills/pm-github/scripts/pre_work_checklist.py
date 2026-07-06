#!/usr/bin/env python3
"""
Pre-Work Checklist for Faber Framework

Run this before starting any significant work to ensure:
- Environment is clean
- Branch is correct
- Spec references are identified
- Trajectory is established
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class PreWorkChecklist:
    """Interactive pre-work checklist."""

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path.cwd()
        self.results: List[Tuple[str, bool, str]] = []

    def run_cmd(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run command and return (success, output)."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.repo_root, timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def check(self, name: fn, auto_fix: bool = False) -> bool:
        """Run a check and record result."""
        pass

    def check_git_clean(self) -> bool:
        """Working tree is clean (no uncommitted changes)."""
        ok, out = self.run_cmd(["git", "status", "--porcelain"])
        if ok and not out:
            self.results.append(("Git working tree clean", True, ""))
            return True
        self.results.append(("Git working tree clean", False, f"Uncommitted changes:\n{out}"))
        return False

    def check_on_hermes_branch(self) -> bool:
        """Current branch is hermes/<topic>."""
        ok, branch = self.run_cmd(["git", "branch", "--show-current"])
        if ok and branch.startswith("hermes/"):
            self.results.append(("On hermes/<topic> branch", True, f"Branch: {branch}"))
            return True
        self.results.append(("On hermes/<topic> branch", False, f"Current: {branch} (expected hermes/...)"))
        return False

    def check_branch_from_dev(self) -> bool:
        """Branch is based on dev (not main)."""
        ok, merge_base = self.run_cmd(["git", "merge-base", "dev", "HEAD"])
        ok2, dev_tip = self.run_cmd(["git", "rev-parse", "dev"])
        if ok and ok2 and merge_base == dev_tip:
            self.results.append(("Branch based on dev", True, ""))
            return True
        self.results.append(("Branch based on dev", False, "Branch may not be based on current dev"))
        return False

    def check_dev_uptodate(self) -> bool:
        """Local dev is up to date with origin/dev."""
        ok, _ = self.run_cmd(["git", "fetch", "origin", "dev"])
        if not ok:
            self.results.append(("dev up to date with origin", False, "Fetch failed"))
            return False

        ok, local = self.run_cmd(["git", "rev-parse", "dev"])
        ok2, remote = self.run_cmd(["git", "rev-parse", "origin/dev"])
        if ok and ok2 and local == remote:
            self.results.append(("dev up to date with origin", True, ""))
            return True
        self.results.append(("dev up to date with origin", False, "Local dev behind origin — run: git pull origin dev"))
        return False

    def check_gh_auth(self) -> bool:
        """GitHub CLI authenticated."""
        ok, out = self.run_cmd(["gh", "auth", "status"])
        if ok:
            self.results.append(("GitHub CLI authenticated", True, ""))
            return True
        self.results.append(("GitHub CLI authenticated", False, "Run: gh auth login"))
        return False

    def check_pm_config(self) -> bool:
        """pm-config.yaml exists."""
        config = self.repo_root / ".github" / "pm-config.yaml"
        if config.exists():
            self.results.append(("pm-config.yaml exists", True, str(config)))
            return True
        self.results.append(("pm-config.yaml exists", False, "Create .github/pm-config.yaml from skill defaults"))
        return False

    def check_evals_pass(self) -> bool:
        """All skill evals pass."""
        ok, out = self.run_cmd(["python", "-m", "pytest", "skills/", "-q", "--tb=no", "-x"])
        if ok:
            self.results.append(("All skill evals pass", True, ""))
            return True
        self.results.append(("All skill evals pass", False, "Run: python -m pytest skills/ -v"))
        return False

    def check_trajectory_guard(self) -> bool:
        """Trajectory guard passes (if trajectory.md exists)."""
        trajectory = self.repo_root / "trajectory.md"
        if not trajectory.exists():
            self.results.append(("Trajectory guard", True, "No trajectory.md (not started)"))
            return True

        ok, out = self.run_cmd(["python", "-m", "skills.trajectory_guard", "--strictness", "ordered"])
        if ok:
            self.results.append(("Trajectory guard", True, ""))
            return True
        self.results.append(("Trajectory guard", False, f"Drift detected:\n{out}"))
        return False

    def run_all(self) -> int:
        """Run all checks."""
        print("🔍 FABER PRE-WORK CHECKLIST")
        print("=" * 50)

        checks = [
            ("Git clean", self.check_git_clean),
            ("On hermes/ branch", self.check_on_hermes_branch),
            ("Based on dev", self.check_branch_from_dev),
            ("dev up to date", self.check_dev_uptodate),
            ("GH CLI auth", self.check_gh_auth),
            ("pm-config exists", self.check_pm_config),
            ("Evals pass", self.check_evals_pass),
            ("Trajectory guard", self.check_trajectory_guard),
        ]

        all_pass = True
        for name, check_fn in checks:
            print(f"\n📋 {name}...")
            try:
                result = check_fn()
                status = "✅" if result else "❌"
                print(f"   {status} {name}")
                if not result:
                    all_pass = False
                    for r_name, r_ok, r_msg in self.results:
                        if r_name == name and not r_ok:
                            print(f"      → {r_msg}")
            except Exception as e:
                print(f"   ❌ {name} (error: {e})")
                all_pass = False

        print("\n" + "=" * 50)
        if all_pass:
            print("✅ ALL PRE-WORK CHECKS PASSED — Ready to start!")
            print("\nNext steps:")
            print("  1. Write plan to runs/hermes/iteration-log.md")
            print("  2. Run intent-collect if new trajectory")
            print("  3. Begin implementation")
            return 0
        else:
            print("❌ SOME CHECKS FAILED — Fix before proceeding")
            print("\nCommon fixes:")
            print("  - git stash / git commit (clean working tree)")
            print("  - git checkout -b hermes/<topic> dev (new branch)")
            print("  - git pull origin dev (update dev)")
            print("  - gh auth login (authenticate)")
            print("  - python -m pytest skills/ (fix evals)")
            return 1


def main():
    checklist = PreWorkChecklist()
    sys.exit(checklist.run_all())


if __name__ == "__main__":
    main()