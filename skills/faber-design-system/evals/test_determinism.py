#!/usr/bin/env python3
"""
Tests for faber-design-system skill - determinism.

Verifies that same input produces byte-for-byte identical output.
"""

import hashlib
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestDeterminism:
    """Test deterministic output from design system generator."""

    FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "rohaki"
    SKILL_DIR = Path(__file__).parent.parent.parent / "faber-design-system"
    SCRIPT = SKILL_DIR / "scripts" / "design_system.py"

    def run_generate(self, output_dir: Path, format: str = "all") -> subprocess.CompletedProcess:
        """Run the generate command."""
        cmd = [
            "python", str(self.SCRIPT),
            "generate",
            "--fixture", "rohaki",
            "--output-dir", str(output_dir),
            "--format", format,
            "--fixtures-dir", str(self.FIXTURE_DIR.parent)
        ]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=self.SKILL_DIR.parent.parent.parent)

    def file_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file."""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_css_deterministic(self):
        """Test CSS output is deterministic."""
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1)
            out2 = Path(d2)

            result1 = self.run_generate(out1, "css")
            assert result1.returncode == 0, result1.stderr

            result2 = self.run_generate(out2, "css")
            assert result2.returncode == 0, result2.stderr

            # Compare file hashes
            css1 = out1 / "design-tokens.css"
            css2 = out2 / "design-tokens.css"

            assert css1.exists() and css2.exists()

            hash1 = self.file_hash(css1)
            hash2 = self.file_hash(css2)

            assert hash1 == hash2, f"CSS output not deterministic: {hash1} != {hash2}"

    def test_tailwind_deterministic(self):
        """Test Tailwind config output is deterministic."""
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1)
            out2 = Path(d2)

            result1 = self.run_generate(out1, "tailwind")
            assert result1.returncode == 0, result1.stderr

            result2 = self.run_generate(out2, "tailwind")
            assert result2.returncode == 0, result2.stderr

            tw1 = out1 / "tailwind.config.js"
            tw2 = out2 / "tailwind.config.js"

            assert tw1.exists() and tw2.exists()

            hash1 = self.file_hash(tw1)
            hash2 = self.file_hash(tw2)

            assert hash1 == hash2, f"Tailwind output not deterministic: {hash1} != {hash2}"

    def test_json_deterministic(self):
        """Test JSON output is deterministic."""
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1)
            out2 = Path(d2)

            result1 = self.run_generate(out1, "json")
            assert result1.returncode == 0, result1.stderr

            result2 = self.run_generate(out2, "json")
            assert result2.returncode == 0, result2.stderr

            json1 = out1 / "design-tokens.json"
            json2 = out2 / "design-tokens.json"

            assert json1.exists() and json2.exists()

            hash1 = self.file_hash(json1)
            hash2 = self.file_hash(json2)

            assert hash1 == hash2, f"JSON output not deterministic: {hash1} != {hash2}"

    def test_all_formats_deterministic(self):
        """Test all formats together are deterministic."""
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1)
            out2 = Path(d2)

            result1 = self.run_generate(out1, "all")
            assert result1.returncode == 0, result1.stderr

            result2 = self.run_generate(out2, "all")
            assert result2.returncode == 0, result2.stderr

            for fname in ["design-tokens.css", "tailwind.config.js", "design-tokens.json"]:
                hash1 = self.file_hash(out1 / fname)
                hash2 = self.file_hash(out2 / fname)
                assert hash1 == hash2, f"{fname} not deterministic: {hash1} != {hash2}"

    def test_overrides_deterministic(self):
        """Test that overrides produce deterministic output."""
        import json

        overrides = {
            "tokens": {
                "color": {
                    "brand": {
                        "bamboo": {
                            "500": {"value": "#00ff00", "type": "color"}
                        }
                    }
                }
            }
        }

        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1)
            out2 = Path(d2)

            # Write overrides file
            overrides_file1 = out1 / "overrides.json"
            overrides_file1.write_text(json.dumps(overrides))

            overrides_file2 = out2 / "overrides.json"
            overrides_file2.write_text(json.dumps(overrides))

            cmd1 = [
                "python", str(self.SCRIPT),
                "generate",
                "--fixture", "rohaki",
                "--output-dir", str(out1 / "output"),
                "--format", "all",
                "--fixtures-dir", str(self.FIXTURE_DIR.parent),
                "--overrides", str(overrides_file1)
            ]

            cmd2 = [
                "python", str(self.SCRIPT),
                "generate",
                "--fixture", "rohaki",
                "--output-dir", str(out2 / "output"),
                "--format", "all",
                "--fixtures-dir", str(self.FIXTURE_DIR.parent),
                "--overrides", str(overrides_file2)
            ]

            result1 = subprocess.run(cmd1, capture_output=True, text=True, cwd=self.SKILL_DIR.parent.parent.parent)
            assert result1.returncode == 0, result1.stderr

            result2 = subprocess.run(cmd2, capture_output=True, text=True, cwd=self.SKILL_DIR.parent.parent.parent)
            assert result2.returncode == 0, result2.stderr

            for fname in ["design-tokens.css", "tailwind.config.js", "design-tokens.json"]:
                hash1 = self.file_hash(out1 / "output" / fname)
                hash2 = self.file_hash(out2 / "output" / fname)
                assert hash1 == hash2, f"{fname} with overrides not deterministic: {hash1} != {hash2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])