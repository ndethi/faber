#!/usr/bin/env python3
"""
GitHub CLI client wrapper for pm-github skill.

Thin subprocess wrapper around `gh` CLI. Every write path takes `dry_run: bool = True`
as a mandatory parameter to enforce the "agents propose, humans dispose" invariant.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class GHResult:
    """Result of a gh command execution."""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    data: Optional[Dict[str, Any]] = None


class GitHubClient:
    """Wrapper for gh CLI operations with dry-run enforcement."""

    def __init__(self, repo: Optional[str] = None, dry_run: bool = True):
        """
        Initialize the GitHub client.

        Args:
            repo: Repository in 'owner/name' format. If None, uses current directory's repo.
            dry_run: If True (default), write operations are simulated only.
        """
        self.repo = repo
        self.dry_run = dry_run
        self._log_entries: List[Dict[str, Any]] = []

    def _run_gh(self, args: List[str], capture_json: bool = False) -> GHResult:
        """Run a gh command and return structured result."""
        cmd = ["gh"]
        if self.repo:
            cmd.extend(["-R", self.repo])
        cmd.extend(args)

        if self.dry_run and self._is_write_operation(args):
            # Simulate write operation in dry-run mode
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would execute: gh {' '.join(cmd[1:])}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "command": cmd}
            )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            data = None
            if capture_json and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            return GHResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                data=data
            )
        except subprocess.TimeoutExpired:
            return GHResult(
                success=False,
                stdout="",
                stderr="Command timed out after 60s",
                returncode=-1
            )
        except FileNotFoundError:
            return GHResult(
                success=False,
                stdout="",
                stderr="gh CLI not found. Install with: brew install gh",
                returncode=-1
            )

    def _is_write_operation(self, args: List[str]) -> bool:
        """Check if the gh command is a write operation."""
        write_commands = {
            "issue", "pr", "label", "project", "release", "workflow",
            "api"  # Some API calls are writes
        }
        if not args:
            return False
        # Check if first arg is a write command
        if args[0] in write_commands:
            # For subcommands, check if it's a create/edit/delete operation
            if len(args) > 1 and args[1] in {"create", "edit", "delete", "close", "reopen", "lock", "unlock", "pin", "unpin"}:
                return True
            if args[0] == "api" and len(args) > 1:
                # Check if API method is write
                if "--method" in args:
                    idx = args.index("--method")
                    if idx + 1 < len(args) and args[idx + 1].upper() in {"POST", "PUT", "PATCH", "DELETE"}:
                        return True
                # Default assume GET for api
        return False

    def _log(self, operation: str, details: Dict[str, Any], dry_run: bool) -> None:
        """Log an operation for audit trail."""
        from datetime import datetime, timezone
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "details": details,
            "dry_run": dry_run,
            "repo": self.repo
        }
        self._log_entries.append(entry)

    def flush_log(self, log_path: Union[str, Path] = "runs/hermes/pm-log.jsonl") -> None:
        """Write accumulated log entries to JSONL file."""
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            for entry in self._log_entries:
                f.write(json.dumps(entry) + "\n")
        self._log_entries.clear()

    # ============ Issue Operations ============

    def list_issues(self, state: str = "open", labels: Optional[List[str]] = None,
                    search: Optional[str] = None, limit: int = 100) -> GHResult:
        """List issues with optional filters."""
        args = ["issue", "list", "--state", state, "--limit", str(limit), "--json", "number,title,body,labels,state,assignees,milestone,createdAt,updatedAt"]
        if labels:
            for label in labels:
                args.extend(["--label", label])
        if search:
            args.extend(["--search", search])
        return self._run_gh(args, capture_json=True)

    def get_issue(self, number: int) -> GHResult:
        """Get a single issue by number."""
        args = ["issue", "view", str(number), "--json", "number,title,body,labels,state,assignees,milestone,createdAt,updatedAt,comments"]
        return self._run_gh(args, capture_json=True)

    def create_issue(self, title: str, body: str = "", labels: Optional[List[str]] = None,
                     assignees: Optional[List[str]] = None, milestone: Optional[str] = None,
                     dry_run: Optional[bool] = None) -> GHResult:
        """Create a new issue. dry_run overrides instance default."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["issue", "create", "--title", title, "--body", body]
        if labels:
            for label in labels:
                args.extend(["--label", label])
        if assignees:
            for assignee in assignees:
                args.extend(["--assignee", assignee])
        if milestone:
            args.extend(["--milestone", milestone])

        self._log("create_issue", {"title": title, "labels": labels, "assignees": assignees}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create issue: {title}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "title": title, "labels": labels}
            )
        return self._run_gh(args)

    def edit_issue(self, number: int, title: Optional[str] = None, body: Optional[str] = None,
                   add_labels: Optional[List[str]] = None, remove_labels: Optional[List[str]] = None,
                   state: Optional[str] = None, dry_run: Optional[bool] = None) -> GHResult:
        """Edit an existing issue."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["issue", "edit", str(number)]
        if title:
            args.extend(["--title", title])
        if body is not None:
            args.extend(["--body", body])
        if add_labels:
            for label in add_labels:
                args.extend(["--add-label", label])
        if remove_labels:
            for label in remove_labels:
                args.extend(["--remove-label", label])
        if state:
            args.extend(["--state", state])

        self._log("edit_issue", {"number": number, "title": title, "add_labels": add_labels, "remove_labels": remove_labels}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would edit issue #{number}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "number": number}
            )
        return self._run_gh(args)

    # ============ Label Operations ============

    def list_labels(self) -> GHResult:
        """List all labels in the repository."""
        args = ["label", "list", "--json", "name,color,description"]
        return self._run_gh(args, capture_json=True)

    def create_label(self, name: str, color: str, description: str = "",
                     dry_run: Optional[bool] = None) -> GHResult:
        """Create a new label."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["label", "create", "--name", name, "--color", color, "--description", description]
        self._log("create_label", {"name": name, "color": color, "description": description}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create label: {name}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "name": name}
            )
        return self._run_gh(args)

    def edit_label(self, name: str, new_name: Optional[str] = None,
                   color: Optional[str] = None, description: Optional[str] = None,
                   dry_run: Optional[bool] = None) -> GHResult:
        """Edit an existing label."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["label", "edit", "--name", name]
        if new_name:
            args.extend(["--new-name", new_name])
        if color:
            args.extend(["--color", color])
        if description is not None:
            args.extend(["--description", description])
        self._log("edit_label", {"name": name, "new_name": new_name, "color": color}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would edit label: {name}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "name": name}
            )
        return self._run_gh(args)

    def delete_label(self, name: str, dry_run: Optional[bool] = None) -> GHResult:
        """Delete a label."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["label", "delete", "--name", name, "--yes"]
        self._log("delete_label", {"name": name}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would delete label: {name}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "name": name}
            )
        return self._run_gh(args)

    # ============ Project v2 Operations ============

    def list_projects(self, owner: Optional[str] = None) -> GHResult:
        """List GitHub Projects v2."""
        args = ["project", "list", "--format", "json", "--limit", "50"]
        if owner:
            args.extend(["--owner", owner])
        result = self._run_gh(args, capture_json=True)
        # gh project list returns {"projects": [...]} - normalize to array
        if result.success and result.data and isinstance(result.data, dict):
            result.data = result.data.get("projects", [])
        return result

    def create_project(self, title: str, owner: str, body: str = "",
                       dry_run: Optional[bool] = None) -> GHResult:
        """Create a new GitHub Project v2."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["project", "create", "--title", title, "--owner", owner, "--format", "json"]
        self._log("create_project", {"title": title, "owner": owner}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create project: {title}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "title": title, "id": "DRY-RUN-PROJECT-ID"}
            )
        return self._run_gh(args, capture_json=True)

    def get_project(self, number: int, owner: str) -> GHResult:
        """Get a project by number."""
        args = ["project", "view", str(number), "--owner", owner, "--format", "json"]
        return self._run_gh(args, capture_json=True)

    def create_project_field(self, project_id: str, name: str, data_type: str,
                             options: Optional[List[str]] = None,
                             dry_run: Optional[bool] = None) -> GHResult:
        """Create a custom field in a project."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["project", "field-create", project_id, "--name", name, "--data-type", data_type]
        if options and data_type == "SINGLE_SELECT":
            for opt in options:
                args.extend(["--single-select-option", opt])
        self._log("create_project_field", {"project_id": project_id, "name": name, "data_type": data_type}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create field: {name} ({data_type})",
                stderr="",
                returncode=0,
                data={"dry_run": True, "field_id": "DRY-RUN-FIELD-ID"}
            )
        return self._run_gh(args, capture_json=True)

    def create_project_view(self, project_id: str, name: str, view_type: str = "TABLE",
                            dry_run: Optional[bool] = None) -> GHResult:
        """Create a project view."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["project", "view-create", project_id, "--name", name, "--type", view_type]
        self._log("create_project_view", {"project_id": project_id, "name": name, "type": view_type}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create view: {name}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "view_id": "DRY-RUN-VIEW-ID"}
            )
        return self._run_gh(args, capture_json=True)

    def add_item_to_project(self, project_id: str, content_id: str, content_type: str = "ISSUE",
                            dry_run: Optional[bool] = None) -> GHResult:
        """Add an issue/PR to a project."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["project", "item-add", project_id, "--url", f"https://github.com/{self.repo}/issues/{content_id}" if content_type == "ISSUE" else f"https://github.com/{self.repo}/pull/{content_id}"]
        self._log("add_item_to_project", {"project_id": project_id, "content_id": content_id}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would add item to project",
                stderr="",
                returncode=0,
                data={"dry_run": True}
            )
        return self._run_gh(args, capture_json=True)

    def update_project_item_field(self, project_id: str, item_id: str, field_id: str, value: Any,
                                  dry_run: Optional[bool] = None) -> GHResult:
        """Update a project item's field value."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        # This uses gh api for complex field updates
        self._log("update_project_item_field", {"project_id": project_id, "item_id": item_id, "field_id": field_id, "value": value}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would update project item field",
                stderr="",
                returncode=0,
                data={"dry_run": True}
            )
        # Actual implementation would use gh api
        return GHResult(
            success=False,
            stdout="",
            stderr="Not implemented: requires GraphQL mutation",
            returncode=-1
        )

    # ============ Milestone Operations ============

    def list_milestones(self, state: str = "open") -> GHResult:
        """List milestones."""
        args = ["api", f"repos/{self.repo}/milestones", "--jq", ".[] | {number, title, state, description, due_on, open_issues, closed_issues}"]
        return self._run_gh(args, capture_json=True)

    def create_milestone(self, title: str, description: str = "", due_on: Optional[str] = None,
                         dry_run: Optional[bool] = None) -> GHResult:
        """Create a milestone."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        data = {"title": title, "description": description}
        if due_on:
            data["due_on"] = due_on
        args = ["api", f"repos/{self.repo}/milestones", "--method", "POST", "--input", "-"]
        self._log("create_milestone", data, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create milestone: {title}",
                stderr="",
                returncode=0,
                data={"dry_run": True, **data}
            )
        # Would need stdin input for api
        return GHResult(
            success=False,
            stdout="",
            stderr="Not fully implemented: requires stdin for api",
            returncode=-1
        )

    # ============ Release Operations ============

    def create_release(self, tag: str, title: str, notes: str = "",
                       draft: bool = False, prerelease: bool = False,
                       dry_run: Optional[bool] = None) -> GHResult:
        """Create a release."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["release", "create", tag, "--title", title, "--notes", notes]
        if draft:
            args.append("--draft")
        if prerelease:
            args.append("--prerelease")
        self._log("create_release", {"tag": tag, "title": title}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would create release: {tag}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "tag": tag}
            )
        return self._run_gh(args)

    def list_releases(self, limit: int = 20) -> GHResult:
        """List releases."""
        args = ["release", "list", "--limit", str(limit), "--json", "tagName,name,isDraft,isPrerelease,createdAt"]
        return self._run_gh(args, capture_json=True)

    def get_release(self, tag: str) -> GHResult:
        """Get a specific release by tag."""
        args = ["release", "view", tag, "--json", "tagName,name,body,publishedAt,isDraft,isPrerelease,createdAt"]
        return self._run_gh(args, capture_json=True)

    # ============ PR Operations ============

    def list_prs(self, state: str = "open", limit: int = 50) -> GHResult:
        """List pull requests."""
        args = ["pr", "list", "--state", state, "--limit", str(limit), "--json", "number,title,body,state,author,headRefName,baseRefName,labels,createdAt,updatedAt"]
        return self._run_gh(args, capture_json=True)

    def get_pr(self, number: int) -> GHResult:
        """Get a single PR."""
        args = ["pr", "view", str(number), "--json", "number,title,body,state,author,headRefName,baseRefName,labels,createdAt,updatedAt,comments,reviews,files"]
        return self._run_gh(args, capture_json=True)

    def get_pr_comments(self, number: int) -> GHResult:
        """Get review comments on a PR."""
        args = ["api", f"repos/{self.repo}/pulls/{number}/comments", "--jq", ".[] | {id, body, path, line, commit_id, user, created_at, updated_at}"]
        return self._run_gh(args, capture_json=True)

    def create_pr_comment(self, number: int, body: str, dry_run: Optional[bool] = None) -> GHResult:
        """Create a comment on a PR."""
        effective_dry_run = dry_run if dry_run is not None else self.dry_run
        args = ["pr", "comment", str(number), "--body", body]
        self._log("create_pr_comment", {"number": number, "body_preview": body[:100]}, effective_dry_run)

        if effective_dry_run:
            return GHResult(
                success=True,
                stdout=f"[DRY-RUN] Would comment on PR #{number}",
                stderr="",
                returncode=0,
                data={"dry_run": True, "number": number}
            )
        return self._run_gh(args)

    # ============ Config / Repo Info ============

    def get_repo_info(self) -> GHResult:
        """Get repository information."""
        args = ["repo", "view", "--json", "name,owner,description,url,defaultBranchRef"]
        return self._run_gh(args, capture_json=True)


def main() -> None:
    """CLI entry point for testing."""
    import argparse
    parser = argparse.ArgumentParser(description="GitHub Client wrapper for pm-github")
    parser.add_argument("--repo", help="Repository in owner/name format")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run in dry-run mode (default)")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Actually execute write operations")
    parser.add_argument("command", nargs="*", help="Command to pass to gh")
    args = parser.parse_args()

    client = GitHubClient(repo=args.repo, dry_run=args.dry_run)

    if args.command:
        # Pass through to gh
        result = client._run_gh(args.command, capture_json=True)
        print(json.dumps({
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "data": result.data
        }, indent=2))
    else:
        print("GitHubClient module - use as library or pass gh commands as arguments")


if __name__ == "__main__":
    main()