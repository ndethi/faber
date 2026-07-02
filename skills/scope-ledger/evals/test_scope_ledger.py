#!/usr/bin/env python3
"""
Eval for the scope-ledger skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Initializes from scope-baseline.md
4. Adds extended-scope items
5. Updates item status
6. Generates correct summary stats
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/scope-ledger/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "scope-ledger" in content, "SKILL.md must mention scope-ledger"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that scope_ledger.py exists and is executable."""
    script = Path("skills/scope-ledger/scripts/scope_ledger.py")
    assert script.exists(), "scope_ledger.py must exist"
    assert os.access(str(script), os.X_OK), "scope_ledger.py must be executable"
    print("✓ scope_ledger.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/scope-ledger/scripts/scope_ledger.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Should succeed with no args (shows summary)"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower() or "ledger" in output.lower(), "Should show usage or summary"
    print("✓ Script runs without required args")


def test_init_from_baseline() -> None:
    """Test initializing ledger from scope-baseline.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "scope-baseline.md"
        baseline_path.write_text("# Scope Baseline\n\nGoal: Build a blog\nAudience: Writers")

        ledger_path = Path(tmpdir) / "ledger.json"

        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--init",
                "--scope-baseline-path", str(baseline_path),
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output["status"] == "initialized"
        assert "summary" in output
        assert output["summary"]["baseline_items"] == 1

        # Verify ledger file exists and has correct content
        assert ledger_path.exists()
        ledger = json.loads(ledger_path.read_text())
        assert "baseline" in ledger
        assert "extended" in ledger
        assert ledger["baseline"]["content"] == "# Scope Baseline\n\nGoal: Build a blog\nAudience: Writers"
        assert "created_at" in ledger["baseline"]

    print("✓ Init from baseline test")


def test_add_extended_item() -> None:
    """Test adding extended-scope items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"

        # First init
        baseline_path = Path(tmpdir) / "scope-baseline.md"
        baseline_path.write_text("# Scope Baseline\nGoal: Build a blog")
        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--init", "--scope-baseline-path", str(baseline_path),
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        # Add first extended item
        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--add-item",
                "--description", "Add comment system",
                "--source", "client-feedback",
                "--estimated-cost", "0.50",
                "--estimated-tokens", "10000",
                "--model-route", "frontier",
                "--ip-attribution", "client",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Add item failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output["status"] == "added"
        assert "item" in output
        assert output["item"]["id"] == "EXT-001"
        assert output["item"]["description"] == "Add comment system"
        assert output["item"]["status"] == "proposed"
        assert output["summary"]["extended_items"] == 1
        assert output["summary"]["total_estimated_cost_usd"] == 0.50

        # Add second extended item
        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--add-item",
                "--description", "Add search functionality",
                "--source", "dev-discovered",
                "--estimated-cost", "0.30",
                "--estimated-tokens", "5000",
                "--model-route", "local",
                "--ip-attribution", "dev",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert output["item"]["id"] == "EXT-002"
        assert output["summary"]["extended_items"] == 2
        assert output["summary"]["total_estimated_cost_usd"] == 0.80

    print("✓ Add extended item test")


def test_update_item_status() -> None:
    """Test updating extended item status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"
        baseline_path = Path(tmpdir) / "scope-baseline.md"
        baseline_path.write_text("# Baseline")
        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--init", "--scope-baseline-path", str(baseline_path),
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        # Add item
        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--add-item", "--description", "New feature",
                "--source", "client-feedback", "--estimated-cost", "0.10",
                "--estimated-tokens", "2000", "--model-route", "local",
                "--ip-attribution", "client", "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        # Update to approved
        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--update-item", "EXT-001",
                "--status", "approved",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Update failed: {result.stderr}"
        output = json.loads(result.stdout.strip())
        assert output["status"] == "updated"
        assert output["item_id"] == "EXT-001"
        assert output["new_status"] == "approved"
        assert output["summary"]["by_status"]["approved"] == 1

        # Update to implemented
        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--update-item", "EXT-001",
                "--status", "implemented",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert output["summary"]["by_status"]["implemented"] == 1
        assert output["summary"]["by_status"]["approved"] == 0

    print("✓ Update item status test")


def test_invalid_update() -> None:
    """Test updating non-existent item fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"
        baseline_path = Path(tmpdir) / "scope-baseline.md"
        baseline_path.write_text("# Baseline")
        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--init", "--scope-baseline-path", str(baseline_path),
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--update-item", "EXT-999",
                "--status", "approved",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 1, "Should fail for non-existent item"
        output = json.loads(result.stdout.strip())
        assert "error" in output

    print("✓ Invalid update test")


def test_show_ledger() -> None:
    """Test showing ledger contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"
        baseline_path = Path(tmpdir) / "scope-baseline.md"
        baseline_path.write_text("# Baseline\nGoal: Build app")
        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--init", "--scope-baseline-path", str(baseline_path),
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--add-item", "--description", "Feature X",
                "--source", "client-feedback", "--estimated-cost", "0.25",
                "--estimated-tokens", "5000", "--model-route", "frontier",
                "--ip-attribution", "client", "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--show",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert "ledger" in output
        assert "summary" in output
        assert output["ledger"]["baseline"]["content"] == "# Baseline\nGoal: Build app"
        assert len(output["ledger"]["extended"]) == 1
        assert output["summary"]["extended_items"] == 1

    print("✓ Show ledger test")


def test_default_show_summary() -> None:
    """Test default behavior shows summary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"

        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert "ledger" in output
        assert "summary" in output
        assert output["summary"]["baseline_items"] == 0
        assert output["summary"]["extended_items"] == 0

    print("✓ Default show summary test")


def test_ip_attribution_summary() -> None:
    """Test IP attribution summary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"
        baseline_path = Path(tmpdir) / "scope-baseline.md"
        baseline_path.write_text("# Baseline")
        subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--init", "--scope-baseline-path", str(baseline_path),
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            timeout=30,
        )

        # Add items with different IP attributions
        for i, ip in enumerate(["client", "dev", "agent", "shared"]):
            subprocess.run(
                [
                    sys.executable,
                    "skills/scope-ledger/scripts/scope_ledger.py",
                    "--add-item", "--description", f"Item {i}",
                    "--source", "client-feedback", "--estimated-cost", "0.10",
                    "--estimated-tokens", "1000", "--model-route", "local",
                    "--ip-attribution", ip, "--ledger-path", str(ledger_path),
                ],
                capture_output=True,
                timeout=30,
            )

        result = subprocess.run(
            [
                sys.executable,
                "skills/scope-ledger/scripts/scope_ledger.py",
                "--show",
                "--ledger-path", str(ledger_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = json.loads(result.stdout.strip())
        assert output["summary"]["by_ip"]["client"] == 1
        assert output["summary"]["by_ip"]["dev"] == 1
        assert output["summary"]["by_ip"]["agent"] == 1
        assert output["summary"]["by_ip"]["shared"] == 1

    print("✓ IP attribution summary test")


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_init_from_baseline,
        test_add_extended_item,
        test_update_item_status,
        test_invalid_update,
        test_show_ledger,
        test_default_show_summary,
        test_ip_attribution_summary,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()