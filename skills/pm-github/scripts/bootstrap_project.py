#!/usr/bin/env python3
"""
Bootstrap GitHub Project v2 with standard fields, views, and automation.

Creates a Project v2 with:
- Standard fields: Status, Priority, Severity, Type, Target Release, Epic
- Standard views: Board (by Status), Table (by Priority), Table (by Type), All Issues
- Dry-run first; explicit --apply to actually create

Usage:
  python bootstrap_project.py --dry-run
  python bootstrap_project.py --apply
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from github_client import GitHubClient


# Standard field definitions
STANDARD_FIELDS = [
    {
        "name": "Status",
        "type": "SINGLE_SELECT",
        "options": ["Backlog", "Ready", "In Progress", "In Review", "Done"],
        "description": "Current workflow status"
    },
    {
        "name": "Priority",
        "type": "SINGLE_SELECT",
        "options": ["Critical", "High", "Medium", "Low"],
        "description": "Business priority for scheduling"
    },
    {
        "name": "Severity",
        "type": "SINGLE_SELECT",
        "options": ["Critical", "High", "Medium", "Low"],
        "description": "Technical impact severity"
    },
    {
        "name": "Type",
        "type": "SINGLE_SELECT",
        "options": ["Bug", "Enhancement", "Docs", "Refactor", "Security", "Needs Triage"],
        "description": "Work item classification"
    },
    {
        "name": "Target Release",
        "type": "TEXT",
        "options": [],
        "description": "Target release version (e.g., v1.2.0)"
    },
    {
        "name": "Epic",
        "type": "TEXT",
        "options": [],
        "description": "Epic identifier or name"
    },
]

# Standard view definitions
STANDARD_VIEWS = [
    {
        "name": "By Status",
        "type": "BOARD",
        "group_by": "Status",
        "description": "Kanban board grouped by workflow status"
    },
    {
        "name": "By Priority",
        "type": "TABLE",
        "sort_by": "Priority",
        "description": "Table view sorted by priority"
    },
    {
        "name": "By Type",
        "type": "TABLE",
        "group_by": "Type",
        "description": "Table view grouped by work type"
    },
    {
        "name": "By Severity",
        "type": "TABLE",
        "sort_by": "Severity",
        "description": "Table view sorted by severity"
    },
    {
        "name": "All Issues",
        "type": "TABLE",
        "description": "Flat table of all project items"
    },
    {
        "name": "My Items",
        "type": "TABLE",
        "filters": [{"field": "Assignees", "operator": "IS", "value": "ME"}],
        "description": "Items assigned to current user"
    },
]


def load_config() -> dict:
    """Load configuration from .github/pm-config.yaml or defaults."""
    import yaml

    config = {}
    # Try repo config
    repo_config_path = Path(".github/pm-config.yaml")
    if repo_config_path.exists():
        with repo_config_path.open() as f:
            config = yaml.safe_load(f) or {}

    # Try skill defaults
    defaults_path = SCRIPTS_DIR.parent / "config" / "defaults.yaml"
    if defaults_path.exists():
        with defaults_path.open() as f:
            defaults = yaml.safe_load(f) or {}
            config = deep_merge(defaults.get("project", {}), config.get("project", {}))

    return config.get("project", {})


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_github_client(config: dict, dry_run: bool) -> GitHubClient:
    """Create GitHubClient from config."""
    github_config = config.get("github", {})
    repo = github_config.get("repo")
    if not repo:
        # Try to detect from git remote
        import subprocess
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                if "github.com" in url:
                    # Parse owner/repo from URL
                    if url.startswith("git@"):
                        repo = url.split(":")[1].replace(".git", "")
                    else:
                        repo = url.split("github.com/")[1].replace(".git", "")
        except Exception:
            pass

    if not repo:
        print("❌ Could not determine repository. Set github.repo in config or run from git repo.")
        sys.exit(1)

    return GitHubClient(repo=repo, dry_run=dry_run)


def bootstrap_project(client: GitHubClient, config: dict) -> str:
    """
    Bootstrap the GitHub Project v2.

    Returns:
        Project ID if successful
    """
    project_config = config.get("project", {})
    owner = project_config.get("owner") or (client.repo.split("/")[0] if client.repo else "unknown")
    title = project_config.get("title", "Faber Project Board")
    body = project_config.get("body", "Auto-generated by pm-github skill\n\n## Overview\nThis project tracks issues and work items using GitHub Projects v2.\n\n## Fields\n- **Status**: Backlog → Ready → In Progress → In Review → Done\n- **Priority**: Critical, High, Medium, Low\n- **Severity**: Critical, High, Medium, Low\n- **Type**: Bug, Enhancement, Docs, Refactor, Security, Needs Triage\n- **Target Release**: Version string (e.g., v1.2.0)\n- **Epic**: Epic identifier\n\n## Views\n- **By Status**: Kanban board\n- **By Priority**: Sorted table\n- **By Type**: Grouped table\n- **All Issues**: Flat table")

    # Custom fields from config
    fields = project_config.get("fields", STANDARD_FIELDS)
    views = project_config.get("views", STANDARD_VIEWS)

    print(f"🏗️  Bootstrapping Project: {title}")
    print(f"   Owner: {owner}")
    print(f"   Dry-run: {client.dry_run}")
    print()

    # Step 1: Create Project
    print("📋 Creating project...")
    project_result = client.create_project(title, owner, body)

    if not project_result.success:
        print(f"❌ Failed to create project: {project_result.stderr}")
        return None

    project_id = project_result.data.get("id") if project_result.data else "DRY-RUN-ID"
    print(f"   ✅ Project created: {project_id}")

    if client.dry_run:
        print("   (dry-run - no actual project created)")
        return project_id

    # Step 2: Create Fields
    print("\n📐 Creating custom fields...")
    field_ids = {}
    for field in fields:
        print(f"   Creating field: {field['name']} ({field['type']})")
        field_result = client.create_project_field(
            project_id,
            field["name"],
            field["type"],
            field.get("options") if field["type"] == "SINGLE_SELECT" else None
        )
        if field_result.success and field_result.data:
            field_ids[field["name"]] = field_result.data.get("id")
            print(f"      ✅ Created (ID: {field_ids[field['name']]})")
        else:
            print(f"      ❌ Failed: {field_result.stderr}")

    # Step 3: Create Views
    print("\n👁️  Creating views...")
    for view in views:
        print(f"   Creating view: {view['name']} ({view['type']})")
        view_result = client.create_project_view(
            project_id,
            view["name"],
            view["type"]
        )
        if view_result.success:
            print(f"      ✅ Created")
        else:
            print(f"      ❌ Failed: {view_result.stderr}")

    # Step 4: Summary
    print(f"\n✅ Project bootstrapped successfully!")
    print(f"   Project ID: {project_id}")
    print(f"   Fields created: {len(field_ids)}")
    print(f"   Views created: {len(views)}")

    return project_id


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap GitHub Project v2 with standard fields and views",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (default) - shows what would be created
  python bootstrap_project.py

  # Actually create the project
  python bootstrap_project.py --apply

  # Specify config ists the project without creating
  python bootstrap_project.py --dry-run --config .github/pm-config.yaml
        """
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create the project (default: dry-run)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be done without creating (default)"
    )
    parser.add_argument(
        "--config",
        help="Path to config file (default: .github/pm-config.yaml)"
    )
    parser.add_argument(
        "--repo",
        help="Override repository (owner/name)"
    )

    args = parser.parse_args()

    # Determine dry-run mode
    dry_run = not args.apply
    if args.dry_run and not args.apply:
        dry_run = True

    # Load config
    config = load_config()
    if args.repo:
        config.setdefault("github", {})["repo"] = args.repo

    # Create client
    client = get_github_client(config, dry_run)

    # Run bootstrap
    project_id = bootstrap_project(client, config)

    if project_id:
        if dry_run:
            print("\n🔍 This was a dry-run. Use --apply to actually create the project.")
        return 0
    else:
        print("\n❌ Project bootstrap failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())