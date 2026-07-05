#!/usr/bin/env python3
"""
Roadmap parser for pm-github skill.

Parses docs/roadmap.md (SSOT) into structured data for GitHub Project sync.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class RoadmapItem:
    """A single backlog item from the roadmap."""
    id: str
    title: str
    type: str
    priority: str
    severity: str
    status: str
    epic: str
    target_release: str
    milestone: str  # The milestone section this belongs to


@dataclass
class Milestone:
    """A milestone from the roadmap."""
    title: str
    target_date: str
    status: str
    items: List[RoadmapItem]


def parse_roadmap(roadmap_path: Path) -> List[Milestone]:
    """
    Parse docs/roadmap.md into structured milestones and items.

    Expected format:
    ### v0.3.0 — Milestone Title
    **Target:** YYYY-MM-DD | **Status:** In Progress

    | ID | Title | Type | Priority | Severity | Status | Epic |
    |----|-------|------|----------|----------|--------|------|
    | BG-001 | Title | Enhancement | High | High | Backlog | Core |
    """
    content = roadmap_path.read_text()

    milestones = []
    current_milestone = None
    in_table = False

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Match milestone header: ### v0.3.0 — Title (or ##)
        milestone_match = re.match(r'^#{2,3}\s+(v?\d+\.\d+\.\d+)\s*[—-]\s*(.+)$', line)
        if milestone_match:
            version = milestone_match.group(1)
            title = milestone_match.group(2).strip()
            # Look for target/status on next line
            target_date = ""
            status = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                target_match = re.search(r'\*\*Target:\*\*\s*([^\|]+)', next_line)
                status_match = re.search(r'\*\*Status:\*\*\s*(.+)', next_line)
                if target_match:
                    target_date = target_match.group(1).strip()
                if status_match:
                    status = status_match.group(1).strip()

            current_milestone = Milestone(
                title=f"{version} — {title}",
                target_date=target_date,
                status=status,
                items=[]
            )
            milestones.append(current_milestone)
            i += 1
            continue

        # Match table header
        if '| ID | Title | Type | Priority | Severity | Status | Epic |' in line:
            in_table = True
            i += 1  # Skip separator line
            if i < len(lines):
                i += 1
            continue

        # Match table rows
        if in_table and line.startswith('|') and not line.startswith('|---'):
            # Parse: | BG-001 | Title | Type | Priority | Severity | Status | Epic |
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 8:  # First and last are empty from split
                item_id = parts[1]
                title = parts[2]
                item_type = parts[3]
                priority = parts[4]
                severity = parts[5]
                status = parts[6]
                epic = parts[7]

                if current_milestone and item_id and item_id != 'ID':
                    current_milestone.items.append(RoadmapItem(
                        id=item_id,
                        title=title,
                        type=item_type,
                        priority=priority,
                        severity=severity,
                        status=status,
                        epic=epic,
                        target_release=current_milestone.title.split(' — ')[0],
                        milestone=current_milestone.title
                    ))
            i += 1
            continue

        # End of table
        if in_table and not line.startswith('|'):
            in_table = False

        i += 1

    # Also parse the "Backlog Items (Source: runs/hermes/backlog.md)" section
    # This is a simpler list format
    backlog_section = False
    for line in content.split('\n'):
        if '## Backlog Items' in line:
            backlog_section = True
            continue
        if backlog_section and line.startswith('## '):
            backlog_section = False
            continue

        if backlog_section and line.strip().startswith('- **'):
            # Match: - **BG-006** — _inbox/ & build-plan persistence (Enhancement, Medium/Medium, Backlog, Core Framework)
            match = re.match(r'-\s*\*\*(BG-\d+)\*\*\s*[—-]\s*(.+?)\s*\((\w+),\s*([^/]+)/([^,]+),\s*(\w+),\s*(.+)\)', line.strip())
            if match:
                item_id = match.group(1)
                title = match.group(2).strip()
                item_type = match.group(3)
                priority = match.group(4)
                severity = match.group(5)
                status = match.group(6)
                epic = match.group(7).rstrip(')').strip()

                # Add to "Unassigned" milestone or create one
                unassigned = next((m for m in milestones if 'Unassigned' in m.title), None)
                if not unassigned:
                    unassigned = Milestone(
                        title="Unassigned",
                        target_date="",
                        status="Backlog",
                        items=[]
                    )
                    milestones.append(unassigned)

                unassigned.items.append(RoadmapItem(
                    id=item_id,
                    title=title,
                    type=item_type,
                    priority=priority,
                    severity=severity,
                    status=status,
                    epic=epic,
                    target_release="",
                    milestone="Unassigned"
                ))

    return milestones


def get_all_items(roadmap_path: Path) -> List[RoadmapItem]:
    """Get all roadmap items as a flat list."""
    milestones = parse_roadmap(roadmap_path)
    items = []
    for m in milestones:
        items.extend(m.items)
    return items


def items_to_project_fields(item: RoadmapItem) -> dict:
    """Convert a roadmap item to project field values."""
    return {
        "Status": item.status,
        "Priority": item.priority,
        "Severity": item.severity,
        "Type": item.type,
        "Target Release": item.target_release,
        "Epic": item.epic
    }


def main():
    import sys
    roadmap_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/roadmap.md")
    milestones = parse_roadmap(roadmap_path)

    for m in milestones:
        print(f"\n=== {m.title} ===")
        print(f"  Target: {m.target_date}, Status: {m.status}")
        for item in m.items:
            print(f"  {item.id}: {item.title} [{item.type}] P={item.priority} S={item.severity} Status={item.status} Epic={item.epic}")


if __name__ == "__main__":
    main()