#!/usr/bin/env python3"
"""
Proposal artifact generation for pm-github skill.

Writes proposal batches to runs/hermes/pm-proposals/<batch-id>/ with
structured JSON and human-readable markdown.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProposedIssue:
    """A single proposed issue from classification."""
    title: str
    body: str
    labels: List[str]
    severity: str  # Critical, High, Medium, Low
    issue_type: str  # bug, enhancement, docs, refactor, security, needs-triage
    source_comment_id: str
    source_repo: str
    source_pr: int
    dedup_key: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProposalBatch:
    """A batch of proposed issues."""
    batch_id: str
    created_at: str
    source_repo: str
    source_pr: int
    proposed_issues: List[ProposedIssue]
    total_count: int
    actionable_count: int
    filtered_count: int


def create_batch_id() -> str:
    """Generate a unique batch ID."""
    return f"pm-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def write_proposal_batch(
    batch: ProposalBatch,
    output_dir: Path,
    write_json: bool = True,
    write_markdown: bool = True
) -> Dict[str, Path]:
    """
    Write a proposal batch to disk.

    Creates:
    - <output_dir>/<batch_id>.json (machine-readable)
    - <output_dir>/<batch_id>.md (human-readable PR comment)

    Args:
        batch: The ProposalBatch to write
        output_dir: Directory to write to (will create subdir pm-proposals/)
        write_json: Whether to write JSON file
        write_markdown: Whether to write Markdown file

    Returns:
        Dict with paths to written files
    """
    proposals_dir = output_dir / "pm-proposals" / batch.batch_id
    proposals_dir.mkdir(parents=True, exist_ok=True)

    written = {}

    if write_json:
        json_path = proposals_dir / f"{batch.batch_id}.json"
        # Convert to serializable dict
        batch_dict = asdict(batch)
        json_path.write_text(json.dumps(batch_dict, indent=2))
        written["json"] = json_path

    if write_markdown:
        md_path = proposals_dir / f"{batch.batch_id}.md"
        md_path.write_text(generate_proposal_markdown(batch))
        written["markdown"] = md_path

    # Also write a summary index
    index_path = output_dir / "pm-proposals" / "index.jsonl"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("a") as f:
        f.write(json.dumps({
            "batch_id": batch.batch_id,
            "created_at": batch.created_at,
            "source_repo": batch.source_repo,
            "source_pr": batch.source_pr,
            "total_count": batch.total_count,
            "actionable_count": batch.actionable_count,
        }) + "\n")

    return written


def generate_proposal_markdown(batch: ProposalBatch) -> str:
    """
    Generate human-readable markdown for a proposal batch.

    This is designed to be posted as a PR comment.
    """
    lines = [
        f"## 🤖 PM-GitHub Proposal Batch: `{batch.batch_id}`",
        "",
        f"**Source:** `{batch.source_repo}#PR{batch.source_pr}`  ",
        f"**Created:** {batch.created_at}  ",
        f"**Summary:** Would create **{batch.actionable_count}** actionable issues out of **{batch.total_count}** classified comments  ",
        "",
        "---",
        "",
        "### Proposed Issues",
        ""
    ]

    for i, issue in enumerate(batch.proposed_issues, 1):
        severity_emoji = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢"
        }.get(issue.severity, "⚪")

        type_emoji = {
            "bug": "🐛",
            "enhancement": "✨",
            "docs": "📝",
            "refactor": "♻️",
            "security": "🔒",
            "needs-triage": "❓"
        }.get(issue.issue_type, "📋")

        lines.extend([
            f"#### {i}. {severity_emoji} {type_emoji} {issue.title}",
            "",
            f"**Severity:** {issue.severity}  ",
            f"**Type:** {issue.issue_type}  ",
            f"**Confidence:** {issue.confidence:.0%}  ",
            f"**Dedup Key:** `{issue.dedup_key}`  ",
            f"**Source Comment:** `{issue.source_comment_id}`  ",
            "",
            "**Labels:** " + ", ".join(f"`{l}`" for l in issue.labels) if issue.labels else "**Labels:** *(none)*",
            "",
            "**Body:**",
            "",
            issue.body,
            "",
            "---",
            ""
        ])

    lines.extend([
        "",
        "### Actions",
        "",
        "> **This is a proposal only.** No issues have been created.",
        "",
        "To approve and create these issues, run:",
        "```bash",
        f"pm-github apply --batch-id {batch.batch_id}",
        "```",
        "",
        "Or reply with `/pm-github apply` on this PR (requires workflow setup).",
        "",
        "To view the full proposal details:",
        "```bash",
        f"pm-github plan --batch-id {batch.batch_id}",
        "```",
        "",
        "---",
        "",
        "*Generated by [pm-github](https://github.com/ndethi/faber/tree/dev/skills/pm-github) skill • Faber Framework*"
    ])

    return "\n".join(lines)


def load_proposal_batch(json_path: Path) -> ProposalBatch:
    """Load a proposal batch from JSON file."""
    data = json.loads(json_path.read_text())
    data["proposed_issues"] = [ProposedIssue(**pi) for pi in data["proposed_issues"]]
    return ProposalBatch(**data)


def list_proposal_batches(proposals_dir: Path) -> List[Dict[str, Any]]:
    """List all proposal batches in the proposals directory."""
    index_path = proposals_dir / "index.jsonl"
    if not index_path.exists():
        return []

    batches = []
    with index_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    batches.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return batches


def create_proposal_batch_from_classified(
    classified: List[Dict[str, Any]],
    source_repo: str,
    source_pr: int,
    min_confidence: float = 0.5
) -> ProposalBatch:
    """
    Create a ProposalBatch from classified comments.

    Args:
        classified: List of classified comments from classify.py
        source_repo: Source repository
        source_pr: Source PR number
        min_confidence: Minimum confidence threshold for inclusion

    Returns:
        ProposalBatch ready to write
    """
    # Filter actionable with sufficient confidence
    actionable = [
        c for c in classified
        if c.get("is_actionable", False) and c.get("confidence", 0) >= min_confidence
    ]

    proposed = []
    for c in actionable:
        # Generate title from first sentence or truncated body
        body_text = c.get("body", "").strip()
        title = body_text.split(".")[0][:80] if body_text else "Untitled issue"
        if len(title) >= 80:
            title = title[:77] + "..."

        # Build labels from severity and type
        labels = [c.get("severity", "Medium").lower(), c.get("type", "needs-triage")]
        # Add type-specific labels
        type_label_map = {
            "bug": "bug",
            "enhancement": "enhancement",
            "docs": "documentation",
            "refactor": "refactor",
            "security": "security"
        }
        if c.get("type") in type_label_map:
            labels.append(type_label_map[c["type"]])

        proposed.append(ProposedIssue(
            title=title,
            body=body_text,
            labels=list(set(labels)),  # Deduplicate
            severity=c.get("severity", "Medium"),
            issue_type=c.get("type", "needs-triage"),
            source_comment_id=str(c.get("source_comment_id", "")),
            source_repo=source_repo,
            source_pr=source_pr,
            dedup_key=c.get("dedup_key", ""),
            confidence=c.get("confidence", 0.5),
            metadata={
                "classified_at": datetime.now(timezone.utc).isoformat(),
                "matched_patterns": c.get("matched_patterns", [])
            }
        ))

    return ProposalBatch(
        batch_id=create_batch_id(),
        created_at=datetime.now(timezone.utc).isoformat(),
        source_repo=source_repo,
        source_pr=source_pr,
        proposed_issues=proposed,
        total_count=len(classified),
        actionable_count=len(actionable),
        filtered_count=len(classified) - len(actionable),
    )


def main() -> None:
    """CLI for testing proposal generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate proposal artifacts")
    parser.add_argument("--input", required=True, help="JSON file with classified comments")
    parser.add_argument("--repo", required=True, help="Source repository (owner/name)")
    parser.add_argument("--pr", type=int, required=True, help="Source PR number")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence threshold")
    args = parser.parse_args()

    with open(args.input) as f:
        classified = json.load(f)

    batch = create_proposal_batch_from_classified(classified, args.repo, args.pr, args.min_confidence)
    written = write_proposal_batch(batch, Path(args.output_dir))

    print(f"Batch ID: {batch.batch_id}")
    print(f"Proposed issues: {len(batch.proposed_issues)}")
    print(f"Written files: {written}")


if __name__ == "__main__":
    main()