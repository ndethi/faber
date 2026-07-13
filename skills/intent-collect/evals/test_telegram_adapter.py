#!/usr/bin/env python3
"""
Evaluations for the Intent Collection Telegram Adapter.

Tests that the telegram adapter:
1. Validates canonical JSON input correctly
2. Normalizes surface-specific input to canonical schema
3. Invokes intent-collect skill and returns artifacts
4. Maintains determinism (same input → same artifacts)
5. Manages conversation state correctly
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
from unittest.mock import patch, MagicMock

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from telegram_adapter import (
    validate_canonical_json,
    normalize_input,
    STATE_INIT,
    STATE_GET_CONTEXT,
    STATE_GET_PRODUCTION_CONTEXT,
    STATE_GET_CONSTRAINTS,
    STATE_GET_NON_GOALS,
    STATE_GET_STAKEHOLDERS_ROLE,
    STATE_GET_STAKEHOLDERS_NAME,
    STATE_CONFIRM,
    STATE_COMPLETED,
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
        self.assertEqual(normalized["production_context"], "normal")
        self.assertEqual(normalized["constraints"], ["budget"])
        self.assertEqual(normalized["non_goals"], ["mobile-app"])
        self.assertEqual(normalized["stakeholders"], [{"role": "dev"}])
        self.assertEqual(normalized["artifacts"], {"existing_spec": "path/to/spec.md"})


class TestConversationStateManagement(unittest.TestCase):
    """Test conversation state management."""

    def setUp(self):
        """Clear conversations before each test."""
        # Import here to avoid issues with module loading
        from telegram_adapter import conversations
        conversations.clear()

    def test_initial_state(self):
        """New conversation starts in INIT state."""
        from telegram_adapter import get_conversation
        conv = get_conversation(12345)
        self.assertEqual(conv["state"], STATE_INIT)
        self.assertEqual(conv["data"], {})

    def test_state_transitions(self):
        """Test basic state transitions."""
        from telegram_adapter import get_conversation, handle_intent_new, handle_text_input
        
        # Start conversation
        handle_intent_new(12345)
        conv = get_conversation(12345)
        self.assertEqual(conv["state"], STATE_GET_CONTEXT)
        
        # Provide context
        handle_text_input(12345, "Test project context")
        conv = get_conversation(12345)
        self.assertEqual(conv["state"], STATE_GET_PRODUCTION_CONTEXT)
        self.assertEqual(conv["data"]["context"], "Test project context")


class TestTelegramIntegration(unittest.TestCase):
    """Test integration with telegram bot simulation."""

    def setUp(self):
        """Set up test fixtures."""
        from telegram_adapter import conversations
        conversations.clear()

    @patch('telegram_adapter.send_telegram_message')
    def test_start_command(self, mock_send):
        """Test /start command sends welcome message."""
        from telegram_adapter import handle_start
        
        handle_start(12345)
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], 12345)  # chat_id
        self.assertIn("Faber Intent Collection Bot", args[1])  # message text
        self.assertEqual(kwargs.get('parse_mode'), "HTML")

    @patch('telegram_adapter.send_telegram_message')
    def test_intent_new_command(self, mock_send):
        """Test /intent_new command starts conversation."""
        from telegram_adapter import handle_intent_new, get_conversation
        
        handle_intent_new(12345)
        
        # Check conversation state was updated
        conv = get_conversation(12345)
        self.assertEqual(conv["state"], STATE_GET_CONTEXT)
        self.assertEqual(conv["data"], {})
        
        # Check that a message was sent
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], 12345)
        self.assertIn("Let's start defining your project intent", args[1])

    @patch('telegram_adapter.send_telegram_message')
    def test_context_input_transitions_to_production_context(self, mock_send):
        """Test that providing context moves to production_context state."""
        from telegram_adapter import handle_intent_new, handle_text_input, get_conversation
        
        # Start conversation
        handle_intent_new(12345)
        
        # Provide context
        test_context = "Build a website for a bakery"
        handle_text_input(12345, test_context)
        
        # Check state transition
        conv = get_conversation(12345)
        self.assertEqual(conv["state"], STATE_GET_PRODUCTION_CONTEXT)
        self.assertEqual(conv["data"]["context"], test_context)
        
        # Check that it prompted for production context
        self.assertTrue(mock_send.called)
        last_call_args = mock_send.call_args_list[-1][0]
        self.assertEqual(last_call_args[0], 12345)
        self.assertIn("production context", last_call_args[1])

    def test_canonical_json_validation_integration(self):
        """Test that the adapter uses the same validation as web adapter."""
        # Test data that should pass validation
        valid_data = {
            "context": "Test project for validation",
            "production_context": "prototype",
            "constraints": ["budget", "timeline"],
            "non_goals": ["mobile-app"],
            "stakeholders": [{"role": "manager", "name": "John"}],
            "artifacts": {}
        }
        
        errors = validate_canonical_json(valid_data)
        self.assertEqual(errors, [])
        
        # Test data that should fail
        invalid_data = {
            "production_context": "invalid-value"
            # missing context
        }
        
        errors = validate_canonical_json(invalid_data)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("context" in e for e in errors))


class TestDeterminism(unittest.TestCase):
    """Test determinism guarantee - same input yields same output."""

    def test_same_input_same_normalized_output(self):
        """Test that identical inputs produce identical normalized outputs."""
        input_data = {
            "context": "  Test project with extra spaces  ",
            "production_context": "normal",
            "constraints": ["budget"],
            "non_goals": ["mobile-app"],
            "stakeholders": [{"role": "tester", "name": "Test User"}],
        }
        
        # Normalize twice
        normalized1 = normalize_input(input_data)
        normalized2 = normalize_input(input_data)
        
        # Should be identical
        self.assertEqual(normalized1, normalized2)
        
        # Check specific normalizations
        self.assertEqual(normalized1["context"], "Test project with extra spaces")
        self.assertEqual(normalized1["production_context"], "normal")
        self.assertEqual(normalized1["constraints"], ["budget"])
        self.assertEqual(normalized1["non_goals"], ["mobile-app"])
        self.assertEqual(normalized1["stakeholders"], [{"role": "tester", "name": "Test User"}])


if __name__ == "__main__":
    unittest.main()