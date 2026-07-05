#!/usr/bin/env python3
"""
Test for roadmap parser and sync-backlog-to-project command.
"""

import tempfile
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from roadmap import parse_roadmap, get_all_items, items_to_project_fields


def test_parse_roadmap_milestones():
    """Test parsing milestone tables from roadmap."""
    # Create a test roadmap
    test_content = """# Test Roadmap

### v0.3.0 — Test Milestone
**Target:** 2026-07-15 | **Status:** In Progress

| ID | Title | Type | Priority | Severity | Status | Epic |
|----|-------|------|----------|----------|--------|------|
| BG-001 | Test Item 1 | Enhancement | High | High | Backlog | Core |
| BG-002 | Test Item 2 | Bug | Medium | Medium | In Progress | Core |

### v0.4.0 — Next Milestone
**Target:** 2026-08-15 | **Status:** Planned

| ID | Title | Type | Priority | Severity | Status | Epic |
|----|-------|------|----------|----------|--------|------|
| BG-003 | Test Item 3 | Docs | Low | Low | Backlog | Quality |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        roadmap_path = Path(f.name)

    try:
        milestones = parse_roadmap(roadmap_path)
        
        assert len(milestones) == 2, f"Expected 2 milestones, got {len(milestones)}"
        
        assert milestones[0].title == "v0.3.0 — Test Milestone"
        assert milestones[0].target_date == "2026-07-15", f"Expected target date 2026-07-15, got {milestones[0].target_date}"
        assert milestones[0].status == "In Progress"
        assert len(milestones[0].items) == 2
        
        assert milestones[1].title == "v0.4.0 — Next Milestone"
        assert milestones[1].target_date == "2026-08-15"
        assert milestones[1].status == "Planned"
        assert len(milestones[1].items) == 1
        
        # Check items
        item1 = milestones[0].items[0]
        assert item1.id == "BG-001"
        assert item1.title == "Test Item 1"
        assert item1.type == "Enhancement"
        assert item1.priority == "High"
        assert item1.severity == "High"
        assert item1.status == "Backlog"
        assert item1.epic == "Core"
        assert item1.target_release == "v0.3.0"
        assert item1.milestone == "v0.3.0 — Test Milestone"
        
        item2 = milestones[0].items[1]
        assert item2.id == "BG-002"
        assert item2.status == "In Progress"
        
        item3 = milestones[1].items[0]
        assert item3.id == "BG-003"
        assert item3.type == "Docs"
        assert item3.target_release == "v0.4.0"
        
        print("✅ test_parse_roadmap_milestones passed")
        
    finally:
        roadmap_path.unlink()


def test_get_all_items():
    """Test getting all items as flat list."""
    test_content = """# Test Roadmap

### v0.3.0 — Test Milestone
**Target:** 2026-07-15 | **Status:** In Progress

| ID | Title | Type | Priority | Severity | Status | Epic |
|----|-------|------|----------|----------|--------|------|
| BG-001 | Test Item 1 | Enhancement | High | High | Backlog | Core |
| BG-002 | Test Item 2 | Bug | Medium | Medium | In Progress | Core |
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        roadmap_path = Path(f.name)

    try:
        items = get_all_items(roadmap_path)
        
        assert len(items) == 2, f"Expected 2 items, got {len(items)}"
        assert items[0].id == "BG-001"
        assert items[1].id == "BG-002"
        
        print("✅ test_get_all_items passed")
        
    finally:
        roadmap_path.unlink()


def test_items_to_project_fields():
    """Test converting items to project field values."""
    from roadmap import RoadmapItem
    
    item = RoadmapItem(
        id="BG-001",
        title="Test Item",
        type="Enhancement",
        priority="High",
        severity="High",
        status="Backlog",
        epic="Core",
        target_release="v0.3.0",
        milestone="v0.3.0 — Test Milestone"
    )
    
    fields = items_to_project_fields(item)
    
    assert fields["Status"] == "Backlog"
    assert fields["Priority"] == "High"
    assert fields["Severity"] == "High"
    assert fields["Type"] == "Enhancement"
    assert fields["Target Release"] == "v0.3.0"
    assert fields["Epic"] == "Core"
    
    print("✅ test_items_to_project_fields passed")


def test_parse_real_roadmap():
    """Test parsing the actual docs/roadmap.md."""
    roadmap_path = Path("docs/roadmap.md")
    if not roadmap_path.exists():
        print("⚠️  docs/roadmap.md not found, skipping")
        return
    
    milestones = parse_roadmap(roadmap_path)
    items = get_all_items(roadmap_path)
    
    # Should have 3 milestones + Unassigned
    assert len(milestones) >= 3
    # Should have at least 10 items (7 unique + 3 duplicates from backlog section)
    assert len(items) >= 10
    
    # Check specific items exist
    item_ids = {item.id for item in items}
    assert "BG-006" in item_ids
    assert "BG-007" in item_ids
    assert "BG-013" in item_ids
    assert "BG-016" in item_ids
    
    print(f"✅ test_parse_real_roadmap passed: {len(milestones)} milestones, {len(items)} items")


def main():
    tests = [
        test_parse_roadmap_milestones,
        test_get_all_items,
        test_items_to_project_fields,
        test_parse_real_roadmap,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())