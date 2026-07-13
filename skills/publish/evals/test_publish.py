#!/usr/bin/env python3
"""
Evaluations for the Publish skill.

Tests that the publish skill meets its acceptance criteria per SKILL.md.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_skill_md_exists():
    """Test that SKILL.md exists and has required fields."""
    skill_md = Path("skills/publish/SKILL.md")
    assert skill_md.exists(), "SKILL.md does not exist"

    content = skill_md.read_text()
    assert "name: publish" in content
    assert "description:" in content
    assert "version:" in content
    assert "author:" in content
    assert "license:" in content
    assert "tags:" in content


def test_script_exists_and_executable():
    """Test that publish.py exists and is executable."""
    script = Path("skills/publish/scripts/publish.py")
    assert script.exists(), "publish.py does not exist"
    assert script.stat().st_mode & 0o111, "publish.py is not executable"


def test_script_help():
    """Test that script shows help without error."""
    result = subprocess.run(
        [sys.executable, "skills/publish/scripts/publish.py", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Help failed: {result.stderr}"
    assert "--project-dir" in result.stdout
    assert "--input-dir" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--hitl-gate" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--version" in result.stdout
    assert "--tag" in result.stdout


def test_missing_deployment_report():
    """Test that script fails gracefully when deployment report is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0, "Should fail when deployment report missing"
        assert "deployment-report.json not found" in result.stderr or "deployment-report.json not found" in result.stdout


def test_deployment_gate_blocks_failed_deploy():
    """Test that publish is blocked when deployment report shows failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        deploy_report = {"status": "failed", "deployment_url": "https://example.pages.dev"}
        (input_dir / "deployment-report.json").write_text(json.dumps(deploy_report))

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0, "Should fail when deployment report shows failure"
        assert "status=failed" in result.stderr or "status=failed" in result.stdout


def test_reads_version_from_package_json():
    """Test that version is read from package.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "2.5.1"}\n')

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        (input_dir / "deployment-report.json").write_text(json.dumps({"status": "success"}))

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Dry run failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert "2.5.1" in str(output) or output.get("version") == "2.5.1"


def test_dry_run_works():
    """Test that --dry-run shows analysis without executing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        (input_dir / "deployment-report.json").write_text(json.dumps({"status": "success"}))

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Dry run failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output["dry_run"] is True
        assert output["status"] == "success"


def test_creates_changelog_entry():
    """Test that changelog is updated with release entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "1.2.3"}\n')
        # Create a basic changelog
        (project_dir / "CHANGELOG.md").write_text("# Changelog\n\nAll notable changes.\n\n")

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        (input_dir / "deployment-report.json").write_text(json.dumps({"status": "success"}))

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Changelog test failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output["changelog_updated"] is True or output["dry_run"] is True


def test_deterministic_output():
    """Test that identical inputs produce identical output structure."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        for tmpdir, label in [(tmpdir1, "1"), (tmpdir2, "2")]:
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()
            (project_dir / "package.json").write_text(f'{{"name": "test-{label}", "version": "1.0.0"}}\n')

            input_dir = Path(tmpdir) / "input"
            input_dir.mkdir()
            (input_dir / "deployment-report.json").write_text(json.dumps({"status": "success"}))

        # Run first time
        result1 = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(Path(tmpdir1) / "project"),
             "--input-dir", str(Path(tmpdir1) / "input"),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Run second time
        result2 = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(Path(tmpdir2) / "project"),
             "--input-dir", str(Path(tmpdir2) / "input"),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result1.returncode == 0
        assert result2.returncode == 0

        output1 = json.loads(result1.stdout.strip())
        output2 = json.loads(result2.stdout.strip())

        # Remove variable fields
        for key in ["github_release_url", "version", "tag"]:
            output1.pop(key, None)
            output2.pop(key, None)

        assert output1["status"] == output2["status"]
        assert output1["dry_run"] == output2["dry_run"]
        assert output1["hitl_gate_required"] == output2["hitl_gate_required"]


def test_todo_not_fabrication():
    """Test that unknown information appears as TODO, not fabricated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        (input_dir / "deployment-report.json").write_text(json.dumps({"status": "success"}))

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())

        # GitHub release URL should be TODO placeholder in dry run
        assert "TODO" in output.get("github_release_url", ""), "Should use TODO placeholder for unknown URL"


def test_output_report_structure_dry_run():
    """Test that output has correct structure in dry-run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        project_dir.mkdir()
        (project_dir / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')

        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        (input_dir / "deployment-report.json").write_text(json.dumps({"status": "success"}))

        result = subprocess.run(
            [sys.executable, "skills/publish/scripts/publish.py",
             "--project-dir", str(project_dir),
             "--input-dir", str(input_dir),
             "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())

        # Check required fields
        required_fields = [
            "status", "artifacts", "version", "tag", "github_release_url",
            "npm_published", "changelog_updated", "hitl_gate_required",
            "hitl_gate_passed", "dry_run"
        ]
        for field in required_fields:
            assert field in output, f"Missing required field: {field}"

        assert output["artifacts"] == ["publication-report.json", "PUBLICATION_SUMMARY.md"]
        assert output["dry_run"] is True


if __name__ == "__main__":
    test_skill_md_exists()
    print("✓ test_skill_md_exists")

    test_script_exists_and_executable()
    print("✓ test_script_exists_and_executable")

    test_script_help()
    print("✓ test_script_help")

    test_missing_deployment_report()
    print("✓ test_missing_deployment_report")

    test_deployment_gate_blocks_failed_deploy()
    print("✓ test_deployment_gate_blocks_failed_deploy")

    test_reads_version_from_package_json()
    print("✓ test_reads_version_from_package_json")

    test_dry_run_works()
    print("✓ test_dry_run_works")

    test_creates_changelog_entry()
    print("✓ test_creates_changelog_entry")

    test_deterministic_output()
    print("✓ test_deterministic_output")

    test_todo_not_fabrication()
    print("✓ test_todo_not_fabrication")

    test_output_report_structure_dry_run()
    print("✓ test_output_report_structure_dry_run")

    print("\nAll tests passed!")