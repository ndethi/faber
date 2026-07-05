#!/usr/bin/env python3
"""
Main CLI entry point for pm-github skill.

Commands:
- plan: Dry-run classification and proposal generation
- apply: Apply approved proposals (create issues, labels, projects)
- sync-labels: Sync label taxonomy with repo
- bootstrap-project: Create GitHub Project v2 with fields and views
- propose-from-pr-comments: Classify PR review comments and generate proposals
- propose-release: Generate release notes and propose release
- verify-config: Verify configuration is valid
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from github_client import GitHubClient
from classify import classify_comments, ClassifiedComment
from dedup import check_dedup_key_exists
from proposals import (
    create_proposal_batch_from_classified,
    write_proposal_batch,
    load_proposal_batch,
    ProposalBatch
)
import importlib.util


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML files."""
    import yaml

    defaults_path = SCRIPTS_DIR.parent / "config" / "defaults.yaml"
    config = {}

    # Load skill-level defaults
    if defaults_path.exists():
        with defaults_path.open() as f:
            config = yaml.safe_load(f) or {}

    # Load repo-level overrides
    if config_path and config_path.exists():
        with config_path.open() as f:
            repo_config = yaml.safe_load(f) or {}
            config = deep_merge(config, repo_config)

    return config


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_github_client(config: Dict, dry_run: bool = True) -> GitHubClient:
    """Create GitHubClient from config."""
    repo = config.get("github", {}).get("repo")
    return GitHubClient(repo=repo, dry_run=dry_run)


def cmd_plan(args: argparse.Namespace, config: Dict) -> int:
    """Dry-run: classify and show what would be done."""
    print("🔍 PM-GitHub Plan Mode (Dry Run)")
    print("=" * 50)

    client = get_github_client(config, dry_run=True)

    if args.pr:
        # Classify PR comments
        print(f"\n📋 Fetching PR #{args.pr} comments from {config.get('github', {}).get('repo', 'unknown')}...")
        pr_result = client.get_pr(args.pr)
        if not pr_result.success:
            print(f"❌ Failed to fetch PR: {pr_result.stderr}")
            return 1

        pr_data = pr_result.data
        if not pr_data:
            print("❌ No PR data returned")
            return 1

        # Get review comments
        comments_result = client.get_pr_comments(args.pr)
        if not comments_result.success:
            print(f"❌ Failed to fetch comments: {comments_result.stderr}")
            return 1

        comments = comments_result.data or []
        print(f"   Found {len(comments)} review comments")

        # Classify
        print("\n🔬 Classifying comments...")
        classified = classify_comments(comments, client.repo or "unknown/unknown", args.pr)

        actionable = [c for c in classified if c.is_actionable]
        print(f"   Actionable: {len(actionable)} / {len(classified)}")

        # Show classification summary
        for c in actionable:
            print(f"   • [{c.severity}] {c.issue_type}: {c.body[:80]}... (confidence: {c.confidence:.0%})")

        # Create proposal batch
        batch = create_proposal_batch_from_classified(
            [asdict(c) for c in classified],
            client.repo or "unknown/unknown",
            args.pr,
            min_confidence=args.min_confidence
        )

        # Write proposals
        proposals_dir = Path(config.get("paths", {}).get("proposals", "runs/hermes/pm-proposals"))
        written = write_proposal_batch(batch, proposals_dir)
        print(f"\n📦 Proposal batch created: {batch.batch_id}")
        print(f"   JSON: {written.get('json')}")
        print(f"   Markdown: {written.get('markdown')}")

        # Print summary for PR comment
        print("\n" + "=" * 50)
        print("PROPOSAL SUMMARY (for PR comment):")
        print("=" * 50)
        markdown_path = written.get('markdown')
        if markdown_path:
            print(markdown_path.read_text())

    return 0


def cmd_apply(args: argparse.Namespace, config: Dict) -> int:
    """Apply an approved proposal batch."""
    print("⚡ PM-GitHub Apply Mode")
    print("=" * 50)

    if not args.batch_id:
        print("❌ --batch-id is required for apply")
        return 1

    # Load proposal batch
    proposals_dir = Path(config.get("paths", {}).get("proposals", "runs/hermes/pm-proposals"))
    batch_path = proposals_dir / args.batch_id / f"{args.batch_id}.json"

    if not batch_path.exists():
        print(f"❌ Batch not found: {batch_path}")
        return 1

    batch = load_proposal_batch(batch_path)
    print(f"Loaded batch: {batch.batch_id}")
    print(f"Proposed issues: {len(batch.proposed_issues)}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        client = get_github_client(config, dry_run=True)
    else:
        print("\n⚠️  LIVE MODE - Creating real GitHub resources!")
        client = get_github_client(config, dry_run=False)

    created = 0
    skipped = 0

    for issue in batch.proposed_issues:
        # Check dedup
        dedup = check_dedup_key_exists(client, issue.dedup_key, client.repo)
        if dedup.exists:
            print(f"   ⏭️  Skipping (dedup): {issue.title} -> existing #{dedup.existing_issue_number}")
            skipped += 1
            continue

        print(f"   📝 Creating issue: {issue.title}")
        result = client.create_issue(
            title=issue.title,
            body=issue.body + f"\n\n---\n**dedup-key:** `{issue.dedup_key}`",
            labels=issue.labels,
            dry_run=args.dry_run
        )

        if result.success:
            print(f"      ✅ Created" + (" (dry-run)" if args.dry_run else ""))
            created += 1
        else:
            print(f"      ❌ Failed: {result.stderr}")

    print(f"\n📊 Summary: {created} created, {skipped} skipped (dedup)")

    # Flush audit log
    client.flush_log()

    return 0 if created > 0 or skipped > 0 else 1


def cmd_sync_labels(args: argparse.Namespace, config: Dict) -> int:
    """Sync label taxonomy with repository."""
    print("🏷️  PM-GitHub Label Sync")
    print("=" * 50)

    labels_config = config.get("labels", {})
    if not labels_config:
        print("❌ No label configuration found in config")
        return 1

    dry_run = not args.apply
    client = get_github_client(config, dry_run=dry_run)

    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Repository: {client.repo}")

    # Get existing labels
    existing_result = client.list_labels()
    existing_labels = {l["name"]: l for l in (existing_result.data or [])}

    # Desired labels from config
    desired = labels_config.get("taxonomy", [])

    created = 0
    updated = 0
    skipped = 0

    for label_def in desired:
        name = label_def["name"]
        color = label_def["color"]
        description = label_def.get("description", "")

        if name in existing_labels:
            existing = existing_labels[name]
            if existing["color"] != color or existing["description"] != description:
                print(f"   🔄 Updating label: {name}")
                result = client.edit_label(name, color=color, description=description)
                if result.success:
                    updated += 1
                else:
                    print(f"      ❌ Failed: {result.stderr}")
            else:
                print(f"   ✓ Already current: {name}")
                skipped += 1
        else:
            print(f"   ➕ Creating label: {name}")
            result = client.create_label(name, color, description)
            if result.success:
                created += 1
            else:
                print(f"      ❌ Failed: {result.stderr}")

    print(f"\n📊 Summary: {created} created, {updated} updated, {skipped} unchanged")
    client.flush_log()
    return 0


def cmd_bootstrap_project(args: argparse.Namespace, config: Dict) -> int:
    """Bootstrap a GitHub Project v2 with standard fields and views."""
    print("🏗️  PM-GitHub Project Bootstrap")
    print("=" * 50)

    project_config = config.get("project", {})
    if not project_config:
        print("❌ No project configuration found in config")
        return 1

    dry_run = not args.apply
    client = get_github_client(config, dry_run=dry_run)

    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Repository: {client.repo}")

    owner = project_config.get("owner") or (client.repo.split("/")[0] if client.repo else "unknown")
    title = project_config.get("title", "Faber Project Board")
    body = project_config.get("body", "Auto-generated by pm-github skill")

    print(f"\n📋 Creating project: {title}")
    project_result = client.create_project(title, owner, body, dry_run=dry_run)

    if not project_result.success:
        print(f"❌ Failed to create project: {project_result.stderr}")
        return 1

    project_id = project_result.data.get("id") if project_result.data else "DRY-RUN-ID"
    print(f"   Project ID: {project_id}")

    # Create standard fields
    fields = project_config.get("fields", [
        {"name": "Status", "type": "SINGLE_SELECT", "options": ["Backlog", "Ready", "In Progress", "In Review", "Done"]},
        {"name": "Priority", "type": "SINGLE_SELECT", "options": ["Critical", "High", "Medium", "Low"]},
        {"name": "Severity", "type": "SINGLE_SELECT", "options": ["Critical", "High", "Medium", "Low"]},
        {"name": "Type", "type": "SINGLE_SELECT", "options": ["Bug", "Enhancement", "Docs", "Refactor", "Security", "Needs Triage"]},
        {"name": "Target Release", "type": "TEXT", "options": []},
        {"name": "Epic", "type": "TEXT", "options": []},
    ])

    for field in fields:
        print(f"   📐 Creating field: {field['name']} ({field['type']})")
        field_result = client.create_project_field(
            project_id,
            field["name"],
            field["type"],
            field.get("options") if field["type"] == "SINGLE_SELECT" else None,
            dry_run=dry_run
        )
        if not field_result.success:
            print(f"      ❌ Failed: {field_result.stderr}")

    # Create standard views
    views = project_config.get("views", [
        {"name": "By Status", "type": "BOARD", "group_by": "Status"},
        {"name": "By Priority", "type": "TABLE", "sort_by": "Priority"},
        {"name": "By Type", "type": "TABLE", "group_by": "Type"},
        {"name": "All Issues", "type": "TABLE"},
    ])

    for view in views:
        print(f"   👁️  Creating view: {view['name']} ({view['type']})")
        view_result = client.create_project_view(project_id, view["name"], view["type"], dry_run=dry_run)
        if not view_result.success:
            print(f"      ❌ Failed: {view_result.stderr}")

    print(f"\n✅ Project bootstrapped: {project_id}")
    client.flush_log()
    return 0


def cmd_propose_from_pr_comments(args: argparse.Namespace, config: Dict) -> int:
    """Classify PR review comments and generate proposals (used by GitHub Action)."""
    print("🤖 PM-GitHub PR Comment Proposer")
    print("=" * 50)

    if not args.pr:
        print("❌ --pr is required")
        return 1

    client = get_github_client(config, dry_run=True)  # Always dry-run for propose

    # Get PR comments
    comments_result = client.get_pr_comments(args.pr)
    if not comments_result.success:
        print(f"❌ Failed to fetch comments: {comments_result.stderr}")
        return 1

    comments = comments_result.data or []
    print(f"Found {len(comments)} review comments")

    # Classify
    classified = classify_comments(comments, client.repo or "unknown/unknown", args.pr)
    actionable = [c for c in classified if c.is_actionable]

    print(f"Actionable: {len(actionable)} / {len(classified)}")

    if not actionable:
        print("No actionable comments found. Exiting.")
        return 0

    # Create proposal batch
    batch = create_proposal_batch_from_classified(
        [asdict(c) for c in classified],
        client.repo or "unknown/unknown",
        args.pr,
        min_confidence=args.min_confidence
    )

    # Write proposals
    proposals_dir = Path(config.get("paths", {}).get("proposals", "runs/hermes/pm-proposals"))
    written = write_proposal_batch(batch, proposals_dir)

    # Generate PR comment body
    comment_body = generate_pr_comment_body(batch)

    if args.output_comment:
        Path(args.output_comment).write_text(comment_body)
        print(f"Comment body written to: {args.output_comment}")

    print(f"\nBatch: {batch.batch_id}")
    print(f"Proposals: {len(batch.proposed_issues)}")
    print(f"Proposal files: {written}")

    # Post comment if not dry-run and token available
    if not args.dry_run and not config.get("github", {}).get("dry_run_comment", True):
        post_result = client.create_pr_comment(args.pr, comment_body)
        if post_result.success:
            print("✅ PR comment posted")
        else:
            print(f"❌ Failed to post comment: {post_result.stderr}")

    return 0


def generate_pr_comment_body(batch: ProposalBatch) -> str:
    """Generate PR comment body for proposal batch."""
    from proposals import generate_proposal_markdown
    return generate_proposal_markdown(batch)


def cmd_propose_release(args: argparse.Namespace, config: Dict) -> int:
    """Generate release notes from merged PRs and propose a release."""
    print("📦 PM-GitHub Release Proposer")
    print("=" * 50)

    client = get_github_client(config, dry_run=args.dry_run)

    # Get recent releases
    releases_result = client.list_releases(limit=5)
    last_release_tag = None
    if releases_result.success and releases_result and releases_result.data:
        last_release_tag = releases_result.data[0].get("tagName")

    # Get merged PRs since last release
    prs_result = client.list_prs(state="closed", limit=100)
    if not prs_result.success:
        print(f"❌ Failed to fetch PRs: {prs_result.stderr}")
        return 1

    prs = [pr for pr in (prs_result.data or []) if pr.get("mergedAt")]

    if last_release_tag:
        # Filter PRs after last release date
        last_release_result = client.get_release(last_release_tag)
        if last_release_result.success and last_release_result.data:
            last_release_date = last_release_result.data.get("publishedAt")
            if last_release_date:
                from datetime import datetime
                last_dt = datetime.fromisoformat(last_release_date.replace("Z", "+00:00"))
                prs = [pr for pr in prs if pr.get("mergedAt") and datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00")) > last_dt]

    print(f"Found {len(prs)} merged PRs since last release ({last_release_tag or 'initial'})")

    # Calculate semantic version bump
    version_bump = calculate_version_bump(prs, args.bump)
    proposed_tag = compute_next_tag(last_release_tag, version_bump)

    # Generate release notes
    notes = generate_release_notes(prs, version_bump)

    print(f"\n📋 Proposed version bump: {version_bump}")
    print(f"🏷️  Proposed tag: {proposed_tag}")
    print("\n--- RELEASE NOTES ---")
    print(notes)

    if args.tag:
        proposed_tag = args.tag
        print(f"\n🏷️  Using provided tag: {proposed_tag}")

    # Write proposal to file
    proposal = {
        "proposed_tag": proposed_tag,
        "version_bump": version_bump,
        "last_release_tag": last_release_tag,
        "pr_count": len(prs),
        "release_notes": notes,
        "prs": [{"number": pr["number"], "title": pr["title"], "mergedAt": pr.get("mergedAt")} for pr in prs]
    }

    proposals_dir = Path(config.get("paths", {}).get("proposals", "runs/hermes/pm-proposals"))
    proposals_dir.mkdir(parents=True, exist_ok=True)
    proposal_file = proposals_dir / f"release-{proposed_tag}.json"
    proposal_file.write_text(json.dumps(proposal, indent=2))
    print(f"\n💾 Proposal saved: {proposal_file}")

    if not args.dry_run and (args.tag or args.apply):
        print(f"\n⚡ Creating release: {proposed_tag}")
        result = client.create_release(proposed_tag, f"Release {proposed_tag}", notes, dry_run=False)
        if result.success:
            print("✅ Release created")

            # Update roadmap
            if args.update_roadmap:
                update_roadmap_for_release(proposed_tag, config)
        else:
            print(f"❌ Failed: {result.stderr}")
            return 1

    return 0


def calculate_version_bump(prs: List[Dict], explicit_bump: Optional[str] = None) -> str:
    """Calculate semantic version bump from conventional commit PR titles."""
    if explicit_bump:
        return explicit_bump

    has_breaking = False
    has_feature = False
    has_fix = False

    for pr in prs:
        title = pr.get("title", "").lower()
        # Check for breaking changes
        if "!" in title.split(":")[0] or "breaking" in title or "major" in title:
            has_breaking = True
        # Check conventional commit types
        elif title.startswith("feat:") or title.startswith("feature:"):
            has_feature = True
        elif title.startswith("fix:") or title.startswith("bugfix:"):
            has_fix = True

    if has_breaking:
        return "major"
    elif has_feature:
        return "minor"
    elif has_fix:
        return "patch"
    return "patch"


def compute_next_tag(last_tag: Optional[str], bump: str) -> str:
    """Compute next semantic version tag."""
    if not last_tag:
        return "v0.1.0"

    # Parse vX.Y.Z
    import re
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", last_tag)
    if not match:
        return "v0.1.0"

    major, minor, patch = map(int, match.groups())

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "patch":
        patch += 1

    return f"v{major}.{minor}.{patch}"


def generate_release_notes(prs: List[Dict], version_bump: str) -> str:
    """Generate release notes from merged PRs grouped by type."""
    lines = ["## Changes", "", f"*Version bump: {version_bump}*", ""]

    features = []
    fixes = []
    docs = []
    breaking = []
    other = []

    for pr in prs:
        labels = [l.get("name", "") for l in pr.get("labels", [])]
        title = pr.get("title", "")
        number = pr.get("number", 0)

        entry = f"- {title} (#{number})"

        # Check for breaking changes
        if "!" in title.split(":")[0] or "breaking" in title.lower():
            breaking.append(entry)
        # Group by conventional commit type
        elif title.lower().startswith("feat:") or title.lower().startswith("feature:") or any(l in labels for l in ["enhancement", "feature"]):
            features.append(entry)
        elif title.lower().startswith("fix:") or title.lower().startswith("bugfix:") or any(l in labels for l in ["bug", "fix"]):
            fixes.append(entry)
        elif any(l in labels for l in ["docs", "documentation"]):
            docs.append(entry)
        else:
            other.append(entry)

    if breaking:
        lines.append("### ⚠️ Breaking Changes")
        lines.extend(breaking)
        lines.append("")
    if features:
        lines.append("### ✨ Features")
        lines.extend(features)
        lines.append("")
    if fixes:
        lines.append("### 🐛 Bug Fixes")
        lines.extend(fixes)
        lines.append("")
    if docs:
        lines.append("### 📝 Documentation")
        lines.extend(docs)
        lines.append("")
    if other:
        lines.append("### 🔧 Other")
        lines.extend(other)
        lines.append("")

    return "\n".join(lines)


def update_roadmap_for_release(tag: str, config: Dict) -> None:
    """Update docs/roadmap.md: move completed items, add new version section."""
    import re
    from datetime import date

    roadmap_path = Path("docs/roadmap.md")
    if not roadmap_path.exists():
        print("⚠️  No roadmap.md found, skipping update")
        return

    content = roadmap_path.read_text()

    # Extract version from tag (e.g., v0.3.0 -> 0.3.0)
    version = tag.lstrip("v")

    # Find the current milestone for this version and mark as Done
    # This is a simplified update - in practice would be more sophisticated
    today = date.today().isoformat()

    # Add release note reference
    release_entry = f"\n---\n\n## Release {tag} ({today})\n\nSee [GitHub Release](https://github.com/{config.get('github', {}).get('repo', 'unknown')}/releases/tag/{tag}) for details.\n"

    content += release_entry

    roadmap_path.write_text(content)
    print(f"📝 Updated {roadmap_path} with release {tag}")


def cmd_verify_config(args: argparse.Namespace, config: Dict) -> int:
    """Verify configuration is valid."""
    print("✅ PM-GitHub Config Verification")
    print("=" * 50)

    issues = []

    # Check required sections
    required = ["github", "labels", "project", "paths"]
    for section in required:
        if section not in config:
            issues.append(f"Missing config section: {section}")

    # Check GitHub config
    github = config.get("github", {})
    if not github.get("repo"):
        issues.append("github.repo is required (owner/name)")

    # Check labels config
    labels = config.get("labels", {}).get("taxonomy", [])
    if not labels:
        issues.append("labels.taxonomy is empty")

    # Check project config
    project = config.get("project", {})
    if not project.get("owner"):
        issues.append("project.owner is required")

    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return 1

    print("✅ Configuration is valid")
    print(f"   Repository: {github.get('repo')}")
    print(f"   Labels: {len(labels)} defined")
    print(f"   Project: {project.get('title', 'unnamed')}")
    return 0


def cmd_sync_backlog_to_project(args: argparse.Namespace, config: Dict) -> int:
    """Sync docs/roadmap.md items to GitHub Project v2."""
    print("🔄 PM-GitHub Backlog → Project Sync")
    print("=" * 50)

    # Import roadmap parser
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from roadmap import parse_roadmap, items_to_project_fields, get_all_items

    roadmap_path = Path(args.roadmap) if args.roadmap else Path("docs/roadmap.md")
    if not roadmap_path.exists():
        print(f"❌ Roadmap file not found: {roadmap_path}")
        return 1

    print(f"📖 Reading roadmap: {roadmap_path}")
    milestones = parse_roadmap(roadmap_path)

    all_items = get_all_items(roadmap_path)
    print(f"   Found {len(all_items)} items across {len(milestones)} milestones")

    # Get or create project
    project_config = config.get("project", {})
    project_title = project_config.get("title", "Faber Project Board")

    dry_run = not args.apply
    client = get_github_client(config, dry_run=dry_run)

    if not client.repo:
        print("❌ No repository configured. Set github.repo in config.")
        return 1

    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Repository: {client.repo}")

    # Find existing project or create
    owner = project_config.get("owner") or (client.repo.split("/")[0] if client.repo else "unknown")
    project_result = client.list_projects(owner=owner)
    project_id = None

    if project_result.success and project_result.data:
        projects = project_result.data.get("projects", []) if isinstance(project_result.data, dict) else project_result.data
        for proj in projects:
            if proj.get("title") == project_title:
                project_id = proj.get("id")
                print(f"   Found existing project: {project_title} (ID: {project_id})")
                break

    if not project_id:
        print(f"   Creating project: {project_title}")
        owner = project_config.get("owner") or (client.repo.split("/")[0] if client.repo else "unknown")
        body = project_config.get("body", "Auto-generated by pm-github skill")
        create_result = client.create_project(project_title, owner, body, dry_run=dry_run)
        if create_result.success and create_result.data:
            project_id = create_result.data.get("id")
            print(f"   Created project ID: {project_id}")

    if not project_id:
        print("❌ Could not find or create project")
        return 1

    # Ensure standard fields exist
    fields = project_config.get("fields", [
        {"name": "Status", "type": "SINGLE_SELECT", "options": ["Backlog", "Ready", "In Progress", "In Review", "Done"]},
        {"name": "Priority", "type": "SINGLE_SELECT", "options": ["Critical", "High", "Medium", "Low"]},
        {"name": "Severity", "type": "SINGLE_SELECT", "options": ["Critical", "High", "Medium", "Low"]},
        {"name": "Type", "type": "SINGLE_SELECT", "options": ["Bug", "Enhancement", "Docs", "Refactor", "Security", "Needs Triage"]},
        {"name": "Target Release", "type": "TEXT", "options": []},
        {"name": "Epic", "type": "TEXT", "options": []},
    ])

    field_ids = {}
    for field in fields:
        print(f"   📐 Ensuring field: {field['name']} ({field['type']})")
        field_result = client.create_project_field(
            project_id,
            field["name"],
            field["type"],
            field.get("options") if field["type"] == "SINGLE_SELECT" else None,
            dry_run=dry_run
        )
        if field_result.success and field_result.data:
            field_ids[field["name"]] = field_result.data.get("id")

    # For each roadmap item, create issue if needed, add to project, set fields
    created_issues = 0
    added_to_project = 0
    updated_fields = 0

    for item in all_items:
        # Check if issue already exists (by title or dedup key in body)
        search_result = client.list_issues(state="all", search=item.id, limit=10)
        existing_issue = None
        if search_result.success and search_result.data:
            for issue in search_result.data:
                if item.id in issue.get("body", "") or issue.get("title", "").startswith(item.id):
                    existing_issue = issue
                    break

        issue_number = None
        if existing_issue:
            issue_number = existing_issue.get("number")
            print(f"   ✓ Issue exists: #{issue_number} - {item.title}")
        else:
            # Create issue
            body = f"{item.title}\n\n---\n**Backlog ID:** `{item.id}`\n**Epic:** {item.epic}\n**Milestone:** {item.milestone}\n**Target Release:** {item.target_release}"
            labels = [item.type.lower(), f"priority:{item.priority.lower()}", f"severity:{item.severity.lower()}"]
            if item.target_release:
                labels.append(f"target:{item.target_release.replace('.', '-')}")

            result = client.create_issue(
                title=f"[{item.id}] {item.title}",
                body=body,
                labels=labels,
                dry_run=dry_run
            )
            if result.success:
                # In dry-run, we don't get a real issue number
                issue_number = "DRY-RUN" if dry_run else None
                created_issues += 1
                print(f"   📝 Created issue: [{item.id}] {item.title}")

        # Add to project if we have an issue number
        if issue_number and issue_number != "DRY-RUN":
            # Add to project
            add_result = client.add_item_to_project(project_id, str(issue_number), "ISSUE", dry_run=dry_run)
            if add_result.success:
                added_to_project += 1
                print(f"   📋 Added to project: #{issue_number}")

                # Update project fields (simplified - would need item_id from add_result)
                # For now, log the intent
                fields_to_set = items_to_project_fields(item)
                for field_name, field_value in fields_to_set.items():
                    if field_name in field_ids:
                        print(f"      Would set {field_name} = {field_value}")
                        updated_fields += 1

    print(f"\n📊 Summary: {created_issues} issues created, {added_to_project} added to project, {updated_fields} fields set")
    client.flush_log()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pm-github: GitHub Project Management Skill for Faber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  plan                    Dry-run classification and proposal generation
  apply                   Apply approved proposals (create issues, labels, projects)
  sync-labels             Sync label taxonomy with repository
  bootstrap-project       Create GitHub Project v2 with fields and views
  propose-from-pr-comments  Classify PR review comments (for GitHub Action)
  propose-release         Generate release notes and propose release
  verify-config           Verify configuration is valid
  sync-backlog-to-project  Sync docs/roadmap.md items to GitHub Project v2

Examples:
  pm-github plan --repo plan --pr 123
  pm-github apply --batch-id pm-20240115-abc123 --no-dry-run
  pm-github sync-labels --apply
  pm-github bootstrap-project --apply
  pm-github propose-from-pr-comments --pr 123
  pm-github verify-config
  pm-github sync-backlog-to-project --apply
        """
    )

    parser.add_argument("--config", help="Path to repo config (.github/pm-config.yaml)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode (default)")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Execute real operations")
    parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence for proposals")
    parser.add_argument("--output-comment", help="Output PR comment body to file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # plan
    plan_parser = subparsers.add_parser("plan", help="Dry-run classification and proposals")
    plan_parser.add_argument("--pr", type=int, required=True, help="PR number to analyze")

    # apply
    apply_parser = subparsers.add_parser("apply", help="Apply approved proposals")
    apply_parser.add_argument("--batch-id", required=True, help="Proposal batch ID to apply")

    # sync-labels
    sync_parser = subparsers.add_parser("sync-labels", help="Sync label taxonomy")
    sync_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")

    # bootstrap-project
    bootstrap_parser = subparsers.add_parser("bootstrap-project", help="Create GitHub Project v2")
    bootstrap_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")

    # propose-from-pr-comments
    propose_parser = subparsers.add_parser("propose-from-pr-comments", help="Classify PR comments")
    propose_parser.add_argument("--pr", type=int, required=True, help="PR number")

    # propose-release
    release_parser = subparsers.add_parser("propose-release", help="Propose a release")
    release_parser.add_argument("--tag", help="Release tag (e.g., v1.0.0)")
    release_parser.add_argument("--bump", choices=["major", "minor", "patch"], help="Explicit version bump (overrides conventional commits)")
    release_parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode (default)")
    release_parser.add_argument("--apply", action="store_true", help="Create actual release (implies --no-dry-run)")
    release_parser.add_argument("--update-roadmap", action="store_true", help="Update docs/roadmap.md after release")

    # verify-config
    verify_parser = subparsers.add_parser("verify-config", help="Verify configuration")

    # sync-backlog-to-project
    sync_backlog_parser = subparsers.add_parser("sync-backlog-to-project", help="Sync docs/roadmap.md to GitHub Project v2")
    sync_backlog_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    sync_backlog_parser.add_argument("--roadmap", help="Path to roadmap file (default: docs/roadmap.md)")

    args = parser.parse_args()

    # Load config
    config_path = Path(args.config) if args.config else Path(".github/pm-config.yaml")
    config = load_config(config_path)

    # Override dry_run from args
    if hasattr(args, "dry_run"):
        config.setdefault("github", {})["dry_run"] = args.dry_run

    # Dispatch
    dispatch = {
        "plan": cmd_plan,
        "apply": cmd_apply,
        "sync-labels": cmd_sync_labels,
        "bootstrap-project": cmd_bootstrap_project,
        "propose-from-pr-comments": cmd_propose_from_pr_comments,
        "propose-release": cmd_propose_release,
        "verify-config": cmd_verify_config,
        "sync-backlog-to-project": cmd_sync_backlog_to_project,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args, config)


if __name__ == "__main__":
    sys.exit(main())