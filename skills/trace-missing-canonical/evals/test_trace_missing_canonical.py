#!/usr/bin/env python3
"""
Trace Missing Canonical Skill Eval
"""

import hashlib
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_SH = REPO_ROOT / "skills" / "trace-missing-canonical" / "run.sh"
# Snapshot of the gitignored _inbox/CHECKSUMS.txt, so CI can check the shipped bundle's hashes.
CHECKSUMS = Path(__file__).resolve().parent / "fixtures" / "CHECKSUMS.txt"
CANONICAL_FILES = ["IDENTITY.md", "INTERFACE.md", "RUNBOOK.md"]


def load_checksums() -> dict:
    """Return {path: sha256} from the committed CHECKSUMS.txt snapshot."""
    entries = {}
    for line in CHECKSUMS.read_text().splitlines():
        if line.strip():
            digest, path = line.split(maxsplit=1)
            entries[path] = digest
    return entries


def test_skill_structure():
    """Test that trace-missing-canonical skill has required files."""
    skill_dir = Path("skills/trace-missing-canonical")
    assert skill_dir.exists(), "skills/trace-missing-canonical directory missing"
    assert (skill_dir / "SKILL.md").exists(), "SKILL.md missing"
    assert (skill_dir / "run.sh").exists(), "run.sh script missing"
    print("✓ Trace-missing-canonical skill structure exists")


def test_run_script_executable():
    """Test that run.sh is executable."""
    run_sh = Path("skills/trace-missing-canonical/run.sh")
    assert run_sh.stat().st_mode & 0o111, "run.sh should be executable"
    print("✓ run.sh is executable")


def make_bundle(root: Path) -> Path:
    """Create a repo with a matching _inbox/ bundle and CHECKSUMS.txt in root."""
    inbox = root / "_inbox"
    inbox.mkdir()
    checksums = []
    for name in CANONICAL_FILES + ["FRAMEWORK.md"]:
        content = f"# {name}\ncanonical content\n"
        (inbox / name).write_text(content)
        (root / name).write_text(content)
        checksums.append(f"{hashlib.sha256(content.encode()).hexdigest()}  {name}")
    (inbox / "CHECKSUMS.txt").write_text("\n".join(checksums) + "\n")
    return root


def run_guard(cwd: Path) -> subprocess.CompletedProcess:
    """Run the real run.sh against the bundle in cwd."""
    return subprocess.run(["bash", str(RUN_SH)], capture_output=True, text=True, cwd=cwd)


def test_run_script_passes_on_clean_bundle(tmp_path):
    """Test that run.sh exits 0 when every canonical file matches."""
    result = run_guard(make_bundle(tmp_path))
    assert result.returncode == 0, result.stdout
    assert "OK: no drift detected" in result.stdout


def test_run_script_no_critical_drift(tmp_path):
    """Test that an evolved FRAMEWORK.md is reported and the other files still match."""
    make_bundle(tmp_path)
    (tmp_path / "FRAMEWORK.md").write_text("# FRAMEWORK.md\nevolved\n")

    result = run_guard(tmp_path)

    assert "OK: IDENTITY.md matches _inbox" in result.stdout
    assert "OK: INTERFACE.md matches _inbox" in result.stdout
    assert "OK: RUNBOOK.md matches _inbox" in result.stdout
    assert "DRIFT DETECTED: FRAMEWORK.md" in result.stdout
    print("✓ run.sh executes and reports canonical file status correctly")


def test_run_script_detects_drift(tmp_path):
    """Test that run.sh fails when a repo file differs from _inbox."""
    make_bundle(tmp_path)
    with open(tmp_path / "IDENTITY.md", "a") as f:
        f.write("\n# MODIFIED - DRIFT!")

    result = run_guard(tmp_path)

    assert result.returncode != 0, result.stdout
    assert "DRIFT DETECTED: IDENTITY.md" in result.stdout
    assert "FAIL: drift detected" in result.stdout
    print("✓ run.sh detects drift")


def test_run_script_detects_missing_file(tmp_path):
    """Test that run.sh fails when a canonical file is missing from the repo."""
    make_bundle(tmp_path)
    (tmp_path / "RUNBOOK.md").unlink()

    result = run_guard(tmp_path)

    assert result.returncode != 0, result.stdout
    assert "MISSING IN REPO: RUNBOOK.md" in result.stdout


def test_run_script_detects_checksum_mismatch(tmp_path):
    """Test that run.sh fails when an _inbox file no longer matches CHECKSUMS.txt."""
    make_bundle(tmp_path)
    for location in (tmp_path / "_inbox", tmp_path):
        (location / "INTERFACE.md").write_text("altered in both places\n")

    result = run_guard(tmp_path)

    assert result.returncode != 0, result.stdout
    assert "CHECKSUM MISMATCH: _inbox/INTERFACE.md" in result.stdout


def test_checksums_exist():
    """Test that the committed CHECKSUMS.txt snapshot covers the canonical files."""
    assert CHECKSUMS.exists(), f"{CHECKSUMS} missing"
    assert set(CANONICAL_FILES) <= set(load_checksums())
    print("✓ CHECKSUMS.txt exists")


def test_tracked_canonical_files_match_checksums():
    """Test that the repo's canonical files still match the shipped bundle.

    FRAMEWORK.md is left out because it is expected to evolve.
    """
    expected = load_checksums()
    for name in CANONICAL_FILES:
        actual = hashlib.sha256((REPO_ROOT / name).read_bytes()).hexdigest()
        assert actual == expected[name], f"{name} has drifted from the shipped bundle"


@pytest.mark.skipif(not (REPO_ROOT / "_inbox").exists(), reason="_inbox/ is gitignored and only exists locally")
def test_real_inbox_has_no_critical_drift():
    """Test the repo against the real _inbox/ bundle where one is present."""
    result = run_guard(REPO_ROOT)
    for name in CANONICAL_FILES:
        assert f"OK: {name} matches _inbox" in result.stdout


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
