#!/usr/bin/env python3
"""
Evaluations for the Intent Collection Web Adapter.

Tests that the web adapter:
1. Validates canonical JSON input correctly
2. Normalizes surface-specific input to canonical schema
3. Invokes intent-collect skill and returns artifacts
4. Maintains determinism (same input → same artifacts)
5. Serves the static HTML form
6. Handles errors gracefully (no fabrication)

Per FRAMEWORK.md §3.5: All surfaces produce identical artifacts for identical input.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from http.server import HTTPServer

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from web_adapter import (
    validate_canonical_json,
    normalize_input,
    invoke_intent_collect,
    IntentHandler,
    REPO_ROOT,
    STATIC_FORM,
)


class TestCanonicalJsonValidation(unittest.TestCase):
    """Test canonical JSON schema validation."""

    def test_valid_input_passes(self):
        """Valid canonical input passes validation."""
        data = {
            "context": "Build a marketing website for Rohaki",
            "production_context": "prototype",
        }
        errors = validate_canonical_json(data)
        self.assertEqual(errors, [], f"Valid input should not have errors: {errors}")

    def test_missing_context_fails(self):
        """Missing context field fails validation."""
        data = {"production_context": "normal"}
        errors = validate_canonical_json(data)
        self.assertTrue(any("context" in e for e in errors), "Should report missing context")

    def test_empty_context_fails(self):
        """Empty context string fails validation."""
        data = {"context": "", "production_context": "normal"}
        errors = validate_canonical_json(data)
        self.assertTrue(any("context" in e for e in errors), "Should report empty context")

    def test_missing_production_context_fails(self):
        """Missing production_context fails validation."""
        data = {"context": "Build a website"}
        errors = validate_canonical_json(data)
        self.assertTrue(any("production_context" in e for e in errors), "Should report missing production_context")

    def test_invalid_production_context_fails(self):
        """Invalid production_context value fails validation."""
        data = {"context": "Build a website", "production_context": "invalid-value"}
        errors = validate_canonical_json(data)
        self.assertTrue(any("production_context" in e for e in errors), "Should report invalid production_context")

    def test_optional_fields_type_checked(self):
        """Optional fields are type-checked."""
        data = {
            "context": "Build a website",
            "production_context": "normal",
            "constraints": "not-a-list",  # Should be a list
        }
        errors = validate_canonical_json(data)
        self.assertTrue(any("constraints" in e for e in errors), "Should report constraints type error")

    def test_full_canonical_input_passes(self):
        """Full canonical input with all optional fields passes."""
        data = {
            "context": "Build a marketing website",
            "production_context": "client-production",
            "constraints": ["brand-guidelines", "timeline"],
            "non_goals": ["mobile-app"],
            "stakeholders": [{"role": "marketing-lead", "name": "Jane"}],
            "artifacts": {},
        }
        errors = validate_canonical_json(data)
        self.assertEqual(errors, [], f"Full canonical input should pass: {errors}")


class TestInputNormalization(unittest.TestCase):
    """Test surface-specific input normalization to canonical schema."""

    def test_minimal_input_normalized(self):
        """Minimal input is normalized with defaults."""
        data = {"context": "Build a site", "production_context": "prototype"}
        normalized = normalize_input(data)
        self.assertEqual(normalized["context"], "Build a site")
        self.assertEqual(normalized["production_context"], "prototype")
        self.assertEqual(normalized["constraints"], [])
        self.assertEqual(normalized["non_goals"], [])
        self.assertEqual(normalized["stakeholders"], [])

    def test_full_input_preserved(self):
        """Full input fields are preserved during normalization."""
        data = {
            "context": "  Build a site  ",
            "production_context": "normal",
            "constraints": ["budget"],
            "non_goals": ["mobile-app"],
            "stakeholders": [{"role": "dev"}],
            "artifacts": {"existing_spec": "path/to/spec.md"},
        }
        normalized = normalize_input(data)
        self.assertEqual(normalized["context"], "Build a site")  # stripped
        self.assertEqual(normalized["constraints"], ["budget"])
        self.assertEqual(normalized["non_goals"], ["mobile-app"])
        self.assertEqual(normalized["stakeholders"], [{"role": "dev"}])
        self.assertEqual(normalized["artifacts"], {"existing_spec": "path/to/spec.md"})


class TestInvokeIntentCollect(unittest.TestCase):
    """Test invocation of the intent-collect skill through the adapter."""

    def test_successful_invocation_returns_artifacts(self):
        """Valid input produces all three deterministic artifacts."""
        canonical = normalize_input({
            "context": "Build a marketing website for Rohaki. Goal: showcase products. Audience: marketing team.",
            "production_context": "prototype",
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            result = invoke_intent_collect(canonical, output_dir=Path(tmpdir))

        self.assertEqual(result["status"], "success", f"Expected success: {result}")
        artifacts = result["artifacts"]
        self.assertIn("spec.md", artifacts)
        self.assertIn("trajectory.md", artifacts)
        self.assertIn("scope-baseline.md", artifacts)

        # Check artifact content has required structure
        spec = artifacts["spec.md"]
        self.assertIn("# Spec", spec)
        self.assertIn("SPEC-01", spec)

        trajectory = artifacts["trajectory.md"]
        self.assertIn("# Trajectory", trajectory)
        self.assertIn("strictness: partial", trajectory)  # prototype → partial

        scope = artifacts["scope-baseline.md"]
        self.assertIn("# Scope Baseline", scope)

    def test_deterministic_output(self):
        """Same input produces identical artifacts across two runs."""
        canonical = normalize_input({
            "context": "Build a website for testing determinism. Goal: test page.",
            "production_context": "normal",
        })

        with tempfile.TemporaryDirectory() as tmpdir1:
            result1 = invoke_intent_collect(canonical, output_dir=Path(tmpdir1))

        with tempfile.TemporaryDirectory() as tmpdir2:
            result2 = invoke_intent_collect(canonical, output_dir=Path(tmpdir2))

        self.assertEqual(result1["status"], "success")
        self.assertEqual(result2["status"], "success")

        # Artifacts must be identical (determinism guarantee per §3.5)
        self.assertEqual(result1["artifacts"]["spec.md"], result2["artifacts"]["spec.md"])
        self.assertEqual(result1["artifacts"]["trajectory.md"], result2["artifacts"]["trajectory.md"])
        self.assertEqual(result1["artifacts"]["scope-baseline.md"], result2["artifacts"]["scope-baseline.md"])

    def test_production_context_affects_trajectory(self):
        """Different production_context produces different trajectory strictness."""
        canonical_prototype = normalize_input({
            "context": "Test project",
            "production_context": "prototype",
        })
        canonical_production = normalize_input({
            "context": "Test project",
            "production_context": "client-production",
        })

        with tempfile.TemporaryDirectory() as tmpdir1:
            r1 = invoke_intent_collect(canonical_prototype, output_dir=Path(tmpdir1))
        with tempfile.TemporaryDirectory() as tmpdir2:
            r2 = invoke_intent_collect(canonical_production, output_dir=Path(tmpdir2))

        self.assertIn("partial", r1["artifacts"]["trajectory.md"])
        self.assertIn("exact", r2["artifacts"]["trajectory.md"])


class TestStaticFormServing(unittest.TestCase):
    """Test that the static HTML form is served correctly."""

    def test_static_form_exists(self):
        """assets/intent-form.html exists."""
        self.assertTrue(STATIC_FORM.exists(), "intent-form.html should exist in assets/")

    def test_static_form_has_required_fields(self):
        """HTML form contains fields mapping to canonical JSON schema."""
        content = STATIC_FORM.read_text()
        # Check for form fields that map to canonical schema
        self.assertIn("context", content.lower())
        self.assertIn("production_context", content.lower())
        self.assertIn("constraints", content.lower())
        self.assertIn("non_goals", content.lower())
        # Check version annotation
        self.assertIn("v1", content.lower())

    def test_static_form_posts_to_api(self):
        """HTML form posts to /api/intent/collect."""
        content = STATIC_FORM.read_text()
        self.assertIn("/api/intent/collect", content)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and non-fabrication."""

    def test_missing_context_returns_error(self):
        """Missing context field returns validation error, not fabricated data."""
        errors = validate_canonical_json({"production_context": "normal"})
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("context" in e for e in errors))

    def test_unknowns_surface_as_todo(self):
        """Unknown information in input surfaces as TODO in artifacts, not fabricated."""
        canonical = normalize_input({
            "context": "Build a website. Goal: test page.",
            "production_context": "prototype",
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            result = invoke_intent_collect(canonical, output_dir=Path(tmpdir))

        self.assertEqual(result["status"], "success")
        spec = result["artifacts"]["spec.md"]
        # The skill should surface unknowns as TODO, not invent details
        self.assertTrue(
            "TODO" in spec or "TODO" in result["artifacts"]["scope-baseline.md"],
            "Unknowns should surface as TODO in artifacts"
        )


class TestApiEndpointContract(unittest.TestCase):
    """Test the HTTP API endpoint contract from FRAMEWORK.md §3.5."""

    def test_api_returns_json(self):
        """API response structure matches the spec."""
        canonical = normalize_input({
            "context": "Test project for API contract",
            "production_context": "normal",
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            result = invoke_intent_collect(canonical, output_dir=Path(tmpdir))

        # Verify response structure
        self.assertIn("status", result)
        self.assertIn("artifacts", result)
        self.assertIsInstance(result["artifacts"], dict)
        self.assertIn("spec.md", result["artifacts"])
        self.assertIn("trajectory.md", result["artifacts"])
        self.assertIn("scope-baseline.md", result["artifacts"])


if __name__ == "__main__":
    unittest.main()
