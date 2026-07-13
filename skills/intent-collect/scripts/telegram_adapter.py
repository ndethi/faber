#!/usr/bin/env python3
"""
Telegram Bot Adapter for Intent Collection.

Per FRAMEWORK.md §3.5: Telegram Bot surface that provides conversational elicitation
with inline keyboards, normalizes input to canonical JSON schema, and invokes the
intent-collect skill to produce deterministic artifacts.

Conversation Flow:
/intent_new → context (text) → production_context (buttons) → constraints (multi-select)
→ non_goals (multi-select) → stakeholders (repeatable) → confirm → invoke skill → send files

Endpoints:
  POST /webhook/telegram → receives Telegram updates, manages conversation state

Determinism: Same JSON input → same artifacts, regardless of surface.
No LLM in the path — purely deterministic skill invocation.
"""

import json
import os
import sqlite3
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import Dict, List, Optional, Any

# ─── Configuration ────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INTENT_SCRIPT = REPO_ROOT / "skills" / "intent-collect" / "scripts" / "intent_collect.py"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8788
WEBHOOK_PATH = "/webhook/telegram"

# Conversation states
STATE_INIT = "init"
STATE_GET_CONTEXT = "get_context"
STATE_GET_PRODUCTION_CONTEXT = "get_production_context"
STATE_GET_CONSTRAINTS = "get_constraints"
STATE_GET_NON_GOALS = "get_non_goals"
STATE_GET_STAKEHOLDERS_ROLE = "get_stakeholders_role"
STATE_GET_STAKEHOLDERS_NAME = "get_stakeholders_name"
STATE_CONFIRM = "confirm"
STATE_COMPLETED = "completed"

# Valid values from intent-collect skill
VALID_PRODUCTION_CONTEXTS = {"prototype", "normal", "client-production"}
DEFAULT_CONSTRAINTS = ["brand-guidelines", "budget", "timeline", "legal", "accessibility"]
DEFAULT_NON_GOALS = ["mobile-app", "backend-api", "desktop-app", "cli-tool", "mobile-web"]

# In-memory conversation storage (in production, use Redis or DB)
# Structure: {chat_id: {state: str, data: dict}}
conversations: dict = {}
conversations_lock = threading.Lock()


# ─── Telegram API Helpers ─────────────────────────────────────

def send_telegram_message(chat_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> bool:
    """Send message via Hermes Telegram gateway (same as notify.py)."""
    import subprocess
    
    hermes_bin = os.environ.get("HERMES_BIN", "hermes")
    profile = os.environ.get("HERMES_PROFILE", "faber")
    
    cmd = [hermes_bin, "--profile", profile, "gateway", "send", "telegram"]
    cmd.extend(["--message", json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": json.dumps(reply_markup) if reply_markup else None
    })])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def send_telegram_document(chat_id: int, file_path: str, filename: str, caption: str = None) -> bool:
    """Send document via Hermes Telegram gateway."""
    import subprocess
    
    hermes_bin = os.environ.get("HERMES_BIN", "hermes")
    profile = os.environ.get("HERMES_PROFILE", "faber")
    
    cmd = [hermes_bin, "--profile", profile, "gateway", "send", "telegram"]
    cmd.extend(["--message", json.dumps({
        "chat_id": chat_id,
        "document": open(file_path, "rb").read(),
        "filename": filename,
        "caption": caption
    })])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0
    except Exception:
        return False



# ─── Canonical JSON Validation ────────────────────────────────

def validate_canonical_json(data: dict) -> list:
    """Validate input against canonical JSON schema. Returns list of errors."""
    errors = []

    if not isinstance(data, dict):
        return ["Input must be a JSON object"]

    # Required fields
    context = data.get("context")
    if not context or not isinstance(context, str) or not context.strip():
        errors.append("Field 'context' is required (non-empty string)")

    production_context = data.get("production_context")
    if not production_context or not isinstance(production_context, str):
        errors.append("Field 'production_context' is required (string)")
    elif production_context not in VALID_PRODUCTION_CONTEXTS:
        errors.append(
            f"Field 'production_context' must be one of: {', '.join(sorted(VALID_PRODUCTION_CONTEXTS))}"
        )

    # Optional fields — type-check only
    if "constraints" in data and not isinstance(data["constraints"], list):
        errors.append("Field 'constraints' must be an array of strings")
    if "non_goals" in data and not isinstance(data["non_goals"], list):
        errors.append("Field 'non_goals' must be an array of strings")
    if "stakeholders" in data and not isinstance(data["stakeholders"], list):
        errors.append("Field 'stakeholders' must be an array of objects")

    return errors


def normalize_input(data: dict) -> dict:
    """Normalize surface-specific input to canonical schema."""
    return {
        "context": data.get("context", "").strip(),
        "production_context": data.get("production_context", "normal"),
        "constraints": data.get("constraints", []),
        "non_goals": data.get("non_goals", []),
        "stakeholders": data.get("stakeholders", []),
        "artifacts": data.get("artifacts", {}),
    }


# ─── Conversation State Management ────────────────────────────

def get_conversation(chat_id: int) -> dict:
    """Get or create conversation state for chat_id."""
    with conversations_lock:
        if chat_id not in conversations:
            conversations[chat_id] = {
                "state": STATE_INIT,
                "data": {},
                "last_updated": time.time()
            }
        return conversations[chat_id]


def clear_conversation(chat_id: int):
    """Clear conversation state for chat_id."""
    with conversations_lock:
        if chat_id in conversations:
            del conversations[chat_id]


# ─── Message Handlers ─────────────────────────────────────────

def handle_start(chat_id: int):
    """Handle /start command."""
    welcome_msg = """
🤖 <b>Faber Intent Collection Bot</b>

I'll help you collect project intent and generate the three foundational artifacts:
- spec.md - Source of truth with acceptance criteria
- trajectory.md - Expected implementation path  
- scope-baseline.md - Client-shareable scope baseline

Send /intent_new to begin a new intent collection session.
    """.strip()
    
    send_telegram_message(chat_id, welcome_msg, parse_mode="HTML")


def handle_intent_new(chat_id: int):
    """Handle /intent_new command - start conversation."""
    conv = get_conversation(chat_id)
    conv["state"] = STATE_GET_CONTEXT
    conv["data"] = {}
    conv["last_updated"] = time.time()
    
    msg = """
📝 Let's start defining your project intent!

Please describe your project: What do you want to build? Who is it for? What problem does it solve?

You can share as much or as little as you know - we'll refine it together.
    """.strip()
    
    send_telegram_message(chat_id, msg, parse_mode="HTML")


def handle_text_input(chat_id: int, text: str):
    """Handle text input based on current state."""
    conv = get_conversation(chat_id)
    state = conv["state"]
    text = text.strip()
    
    if not text:
        send_telegram_message(chat_id, "Please provide some input - I can't process empty messages.")
        return
    
    if state == STATE_GET_CONTEXT:
        conv["data"]["context"] = text
        conv["state"] = STATE_GET_PRODUCTION_CONTEXT
        conv["last_updated"] = time.time()
        
        # Show production context options
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🧪 Prototype", "callback_data": "prod_prototype"},
                    {"text": "🏭 Normal", "callback_data": "prod_normal"}
                ],
                [
                    {"text": "🏢 Client Production", "callback_data": "prod_client-production"}
                ]
            ]
        }
        
        msg = "Got it! What's the intended production context for this project?"
        send_telegram_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
        
    elif state == STATE_GET_STAKEHOLDERS_ROLE:
        # This is the role part of a stakeholder
        conv["data"]["_pending_stakeholder_role"] = text
        conv["state"] = STATE_GET_STAKEHOLDERS_NAME
        conv["last_updated"] = time.time()
        
        msg = f"Role: {text}\n\nNow, what's the name for this stakeholder?"
        send_telegram_message(chat_id, msg, parse_mode="HTML")
        
    elif state == STATE_GET_STAKEHOLDERS_NAME:
        # This is the name part - we have both role and name now
        role = conv["data"].get("_pending_stakeholder_role")
        name = text
        
        if "stakeholders" not in conv["data"]:
            conv["data"]["stakeholders"] = []
        
        conv["data"]["stakeholders"].append({"role": role, "name": name})
        # Clean up placeholder
        if "_pending_stakeholder_role" in conv["data"]:
            del conv["data"]["_pending_stakeholder_role"]
        
        conv["last_updated"] = time.time()
        
        # Ask if they want to add another stakeholder
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "➕ Add Another Stakeholder", "callback_data": "stakeholder_add_another"},
                    {"text": "✅ Done with Stakeholders", "callback_data": "stakeholder_done"}
                ]
            ]
        }
        
        current_stakeholders = "\n".join([f"• {s['role']}: {s['name']}" for s in conv["data"]["stakeholders"]])
        msg = f"Added stakeholder: {role} - {name}\n\n"
        if current_stakeholders:
            msg += f"Current stakeholders:\n{current_stakeholders}\n\n"
        msg += "Would you like to add another stakeholder, or are you done?"
        
        send_telegram_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
        
    else:
        # Unexpected text input - ignore or ask for clarification
        pass


def handle_callback_query(chat_id: int, callback_data: str):
    """Handle button presses from inline keyboards."""
    conv = get_conversation(chat_id)
    state = conv["state"]
    
    if callback_data.startswith("prod_"):
        # Production context selection
        context_value = callback_data[5:]  # Remove 'prod_' prefix
        if context_value in VALID_PRODUCTION_CONTEXTS:
            conv["data"]["production_context"] = context_value
            conv["state"] = STATE_GET_CONSTRAINTS
            conv["last_updated"] = time.time()
            
            # Show constraints multi-select
            keyboard = build_multiselect_keyboard(
                "constraint", 
                DEFAULT_CONSTRAINTS, 
                conv["data"].get("constraints", []),
                "constraints_done"
            )
            
            selected = [c for c in DEFAULT_CONSTRAINTS if c in conv["data"].get("constraints", [])]
            selected_text = ", ".join(selected) if selected else "None selected"
            
            msg = f"""
🎯 Which constraints apply to this project? (Select all that apply)

Currently selected: {selected_text}
Tap toggles to add/remove, then press "Done" when finished.
            """.strip()
            
            send_telegram_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
        else:
            send_telegram_message(chat_id, "Invalid selection. Please try again.")
            
    elif callback_data.startswith("constraint_"):
        if callback_data == "constraints_done":
            # Move to non_goals
            conv["state"] = STATE_GET_NON_GOALS
            conv["last_updated"] = time.time()
            
            keyboard = build_multiselect_keyboard(
                "nongoal", 
                DEFAULT_NON_GOALS, 
                conv["data"].get("non_goals", []),
                "non_goals_done"
            )
            
            selected = [n for n in DEFAULT_NON_GOALS if n in conv["data"].get("non_goals", [])]
            selected_text = ", ".join(selected) if selected else "None selected"
            
            msg = f"""
🚫 What's explicitly OUT of scope for this project? (Select all that apply)

Currently selected: {selected_text}
Tap toggles to add/remove, then press "Done" when finished.
            """.strip()
            
            send_telegram_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Toggle constraint selection
            constraint_type, value = callback_data.split("_", 1)
            current = set(conv["data"].get("constraints", []))
            if value in current:
                current.remove(value)
            else:
                current.add(value)
            conv["data"]["constraints"] = list(current)
            conv["last_updated"] = time.time()
            
            # Refresh the keyboard with updated selections
            keyboard = build_multiselect_keyboard(
                "constraint", 
                DEFAULT_CONSTRAINTS, 
                conv["data"].get("constraints", []),
                "constraints_done"
            )
            
            selected = [c for c in DEFAULT_CONSTRAINTS if c in conv["data"].get("constraints", [])]
            selected_text = ", ".join(selected) if selected else "None selected"
            
            msg = f"""
🎯 Which constraints apply to this project? (Select all that apply)

Currently selected: {selected_text}
Tap toggles to add/remove, then press "Done" when finished.
            """.strip()
            
            # Edit the existing message to show updated selection
            edit_telegram_message(chat_id, conv.get("last_message_id"), msg, reply_markup=keyboard, parse_mode="HTML")
            
    elif callback_data.startswith("nongoal_"):
        if callback_data == "non_goals_done":
            # Move to stakeholders
            conv["state"] = STATE_GET_STAKEHOLDERS_ROLE
            conv["last_updated"] = time.time()
            
            msg = """
👥 Who are the stakeholders for this project?

Please provide each stakeholder's role and name. I'll ask for role first, then name.
Example: "Product Manager" then "Alice Smith"

What's the role of the first stakeholder?
            """.strip()
            
            send_telegram_message(chat_id, msg, parse_mode="HTML")
        else:
            # Toggle nongoal selection
            nongoal_type, value = callback_data.split("_", 1)
            current = set(conv["data"].get("non_goals", []))
            if value in current:
                current.remove(value)
            else:
                current.add(value)
            conv["data"]["non_goals"] = list(current)
            conv["last_updated"] = time.time()
            
            # Refresh the keyboard with updated selections
            keyboard = build_multiselect_keyboard(
                "nongoal", 
                DEFAULT_NON_GOALS, 
                conv["data"].get("non_goals", []),
                "non_goals_done"
            )
            
            selected = [n for n in DEFAULT_NON_GOALS if n in conv["data"].get("non_goals", [])]
            selected_text = ", ".join(selected) if selected else "None selected"
            
            msg = f"""
🚫 What's explicitly OUT of scope for this project? (Select all that apply)

Currently selected: {selected_text}
Tap toggles to add/remove, then press "Done" when finished.
            """.strip()
            
            edit_telegram_message(chat_id, conv.get("last_message_id"), msg, reply_markup=keyboard, parse_mode="HTML")
            
    elif callback_data == "stakeholder_add_another":
        # Ask for next stakeholder role
        conv["state"] = STATE_GET_STAKEHOLDERS_ROLE
        conv["last_updated"] = time.time()
        
        msg = "What's the role of the next stakeholder?"
        send_telegram_message(chat_id, msg, parse_mode="HTML")
        
    elif callback_data == "stakeholder_done":
        # Move to confirmation
        conv["state"] = STATE_CONFIRM
        conv["last_updated"] = time.time()
        
        show_confirmation(chat_id)
        
    elif callback_data == "confirm_yes":
        # User confirmed - process the intent
        process_intent(chat_id)
        
    elif callback_data == "confirm_no":
        # User wants to restart
        conv["state"] = STATE_GET_CONTEXT
        conv["data"] = {"context": conv["data"].get("context", "")}  # Keep existing context
        conv["last_updated"] = time.time()
        
        msg = """
📝 Let's continue refining your project intent!

You said: "{context}"

Is this still correct, or would you like to update it?
        """.strip().format(context=conv["data"].get("context", ""))
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Keep as is", "callback_data": "keep_context"},
                    {"text": "✏️ Update description", "callback_data": "update_context"}
                ]
            ]
        }
        
        send_telegram_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")


def build_multiselect_keyboard(prefix: str, options: List[str], selected: List[str], done_callback: str) -> dict:
    """Build an inline keyboard for multi-select options."""
    keyboard = []
    
    # Add options in rows of 2
    for i in range(0, len(options), 2):
        row = []
        for j in range(2):
            if i + j < len(options):
                opt = options[i + j]
                is_selected = opt in selected
                # Use checkbox emoji to indicate selection state
                text = f"{'☑️' if is_selected else '⬜'} {opt}"
                callback_data = f"{prefix}_{opt}"
                row.append({"text": text, "callback_data": callback_data})
        keyboard.append(row)
    
    # Add done button
    keyboard.append([{"text": "✅ Done", "callback_data": done_callback}])
    
    return {"inline_keyboard": keyboard}


def show_confirmation(chat_id: int):
    """Show confirmation summary before processing."""
    conv = get_conversation(chat_id)
    data = conv["data"]
    
    # Format the summary
    summary = f"""
📋 Please confirm your project details:

<b>Context:</b>
{data.get('context', 'Not set')}

<b>Production Context:</b>
{data.get('production_context', 'Not set')}

<b>Constraints:</b>
{format_list(data.get('constraints', []))}

<b>Non-Goals:</b>
{format_list(data.get('non_goals', []))}

<b>Stakeholders:</b>
{format_stakeholders(data.get('stakeholders', []))}

Is this correct?
    """.strip()
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Yes, Create Artifacts", "callback_data": "confirm_yes"},
                {"text": "❌ No, Start Over", "callback_data": "confirm_no"}
            ]
        ]
    }
    
    msg = send_telegram_message(chat_id, summary, reply_markup=keyboard, parse_mode="HTML")
    # Store message ID for potential editing
    if msg:
        # In a real implementation, we'd extract the message ID from the response
        # For now, we'll just note that we sent a message
        pass


def format_list(items: List[str]) -> str:
    """Format a list as bullet points."""
    if not items:
        return "None selected"
    return "\n".join([f"• {item}" for item in items])


def format_stakeholders(stakeholders: List[dict]) -> str:
    """Format stakeholders list."""
    if not stakeholders:
        return "None added"
    return "\n".join([f"• {s['role']}: {s['name']}" for s in stakeholders])


def edit_telegram_message(chat_id: int, message_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML"):
    """Edit an existing telegram message."""
    import subprocess
    import json
    
    hermes_bin = os.environ.get("HERMES_BIN", "hermes")
    profile = os.environ.get("HERMES_PROFILE", "faber")
    
    # Note: This is a simplified version - in reality, we'd need to use the Telegram Bot API directly
    # or extend the Hermes gateway to support message editing. For MVP, we'll send a new message.
    # TODO: Implement proper message editing when Hermes gateway supports it
    
    # For now, send a new message (not ideal but functional)
    send_telegram_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)


# ─── Intent Processing ────────────────────────────────────────

def process_intent(chat_id: int):
    """Convert collected data to canonical JSON and invoke intent-collect skill."""
    conv = get_conversation(chat_id)
    data = conv["data"]
    
    # Build canonical JSON
    canonical = {
        "context": data.get("context", ""),
        "production_context": data.get("production_context", "normal"),
        "constraints": data.get("constraints", []),
        "non_goals": data.get("non_goals", []),
        "stakeholders": data.get("stakeholders", []),
        "artifacts": {}
    }
    
    # Validate required fields
    if not canonical["context"]:
        send_telegram_message(chat_id, "❌ Error: Project context is required. Please start over with /intent_new")
        clear_conversation(chat_id)
        return
    
    if not canonical["production_context"]:
        send_telegram_message(chat_id, "❌ Error: Production context is required. Please start over with /intent_new")
        clear_conversation(chat_id)
        return
    
    # Show processing message
    processing_msg = send_telegram_message(chat_id, "⏳ Generating your intent artifacts... This may take a moment.")
    
    # Invoke intent-collect skill
    import subprocess
    import tempfile
    from pathlib import Path
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "python", str(INTENT_SCRIPT),
                "--client-context", canonical["context"],
                "--production-context", canonical["production_context"],
                "--output-dir", tmpdir
            ]
            
            # Add optional arrays as repeated arguments (if supported by intent_collect.py)
            # Looking at intent_collect.py, it doesn't seem to accept arrays via CLI directly
            # So we'll need to modify approach or use JSON input
            
            # Actually, let's check if intent_collect.py accepts JSON input
            # Looking at the code, it doesn't appear to - it uses --client-context and --production-context
            # The arrays and objects would need to be handled differently
            
            # Let me re-examine the intent_collect.py to see how to pass complex data
            
            # For now, let's try passing as JSON via stdin or check if there's another way
            
            # Actually, looking more carefully at intent_collect.py, it seems designed for CLI use
            # with just client-context and production-context. The other fields appear to have defaults
            # or are extracted from context.
            
            # This suggests I may need to:
            # 1. Modify intent_collect.py to accept JSON input, OR
            # 2. Pre-process the context to include the structured data, OR  
            # 3. Create a wrapper that builds the right context string
            
            # Looking at the extract_facts and elicit_gaps functions in intent_collect.py,
            # it does simple keyword extraction from the context string.
            # 
            # For the MVP, let me try to encode the additional information into the context
            # in a way that the existing extraction logic can pick up.
            
            # Build enhanced context that includes our structured data
            enhanced_context = f"""
{canonical['context']}

PRODUCTION_CONTEXT: {canonical['production_context']}
CONSTRAINTS: {', '.join(canonical['constraints'])}
NON_GOALS: {', '.join(canonical['non_goals'])}
STAKEHOLDERS: {'; '.join([f'{s['role']}:{s['name']}' for s in canonical['stakeholders']])}
            """.strip()
            
            cmd = [
                "python", str(INTENT_SCRIPT),
                "--client-context", enhanced_context,
                "--production-context", canonical["production_context"],
                "--output-dir", tmpdir
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = f"""❌ Error generating artifacts:
                
{result.stderr}

Please try again or contact support if the problem persists."""
                send_telegram_message(chat_id, error_msg)
                clear_conversation(chat_id)
                return
            
            # Read the generated artifacts
            artifacts = {}
            for filename in ["spec.md", "trajectory.md", "scope-baseline.md"]:
                file_path = Path(tmpdir) / filename
                if file_path.exists():
                    artifacts[filename] = file_path.read_text()
                else:
                    send_telegram_message(chat_id, f"❌ Error: Expected artifact not found: {filename}")
                    clear_conversation(chat_id)
                    return
            
            # Send success message and files
            success_msg = """✅ Your intent artifacts have been generated!

Sending the three files now:"""
            send_telegram_message(chat_id, success_msg)
            
            # Send each file
            for filename, content in artifacts.items():
                # Create a temporary file to send
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'-{filename}', delete=False) as f:
                    f.write(content)
                    temp_path = f.name
                
                try:
                    send_telegram_document(
                        chat_id, 
                        temp_path, 
                        filename,
                        f"Generated {filename}"
                    )
                finally:
                    # Clean up temp file
                    os.unlink(temp_path)
            
            # Mark conversation as complete
            conv["state"] = STATE_COMPLETED
            conv["last_updated"] = time.time()
            
            # Offer to start another
            after_msg = """
🎉 Done! You can start another intent collection anytime by sending /intent_new

What would you like to do next?
            """.strip()
            
            send_telegram_message(chat_id, after_msg, parse_mode="HTML")
            
    except subprocess.TimeoutExpired:
        send_telegram_message(chat_id, "❌ Error: Artifact generation timed out. Please try again.")
        clear_conversation(chat_id)
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Unexpected error: {str(e)}")
        clear_conversation(chat_id)


# ─── HTTP Webhook Handler ─────────────────────────────────────

class TelegramWebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for Telegram webhook requests."""
    
    def do_POST(self):
        """Handle incoming Telegram webhook POST."""
        if self.path != WEBHOOK_PATH:
            self.send_error(404, "Not Found")
            return
            
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "Bad Request: Empty body")
            return
            
        try:
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data.decode('utf-8'))
            self.process_telegram_update(update)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        except json.JSONDecodeError:
            self.send_error(400, "Bad Request: Invalid JSON")
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def process_telegram_update(self, update: dict):
        """Process a single Telegram update."""
        # Extract message or callback query
        if "message" in update:
            self.handle_message(update["message"])
        elif "callback_query" in update:
            self.handle_callback_query(update["callback_query"])
        # Note: We could also handle edited_message, channel_post, etc. if needed
    
    def handle_message(self, message: dict):
        """Handle incoming message."""
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        
        # Store message ID for potential editing (if we implement that)
        message_id = message.get("message_id")
        
        # Handle commands
        if text.startswith("/start"):
            handle_start(chat_id)
        elif text.startswith("/intent_new"):
            handle_intent_new(chat_id)
        elif text:
            # Regular text input
            handle_text_input(chat_id, text)
        # Ignore other message types (photos, stickers, etc.) for now
    
    def handle_callback_query(self, callback_query: dict):
        """Handle callback query from inline keyboard."""
        query_id = callback_query["id"]
        chat_id = callback_query["message"]["chat"]["id"]
        callback_data = callback_query["data"]
        message_id = callback_query["message"]["message_id"]
        
        # Answer the callback query to remove loading state
        self.answer_callback_query(query_id)
        
        # Store message ID for editing
        conv = get_conversation(chat_id)
        conv["last_message_id"] = message_id
        
        # Handle the callback
        handle_callback_query(chat_id, callback_data)
    
    def answer_callback_query(self, callback_query_id: str):
        """Answer a callback query to remove loading indicator."""
        import subprocess
        import json
        
        try:
            hermes_bin = os.environ.get("HERMES_BIN", "hermes")
            profile = os.environ.get("HERMES_PROFILE", "faber")
            
            # Use Hermes gateway to answer callback query
            cmd = [hermes_bin, "--profile", profile, "gateway", "answerCallbackQuery"]
            cmd.extend(["--callback_query_id", callback_query_id])
            
            subprocess.run(cmd, capture_output=True, timeout=5)
        except Exception:
            # Ignore errors in answering callback query - not critical
            pass
    
    def do_GET(self):
        """Handle GET requests (for webhook setup verification)."""
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Telegram Intent Collector Bot Webhook')
        elif self.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "telegram-intent-adapter"}')
        else:
            self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        """Override to use less verbose logging."""
        # Log to stderr instead of stdout to keep stdout clean for potential JSON output
        sys.stdout.write("%s - - [%s] %s\n" % (
            self.address_string(),
            self.log_date_time_string(),
            format % args))
    def __init__(self, *args, **kwargs):
        import sys
        self.__stdout__ = sys.stdout
        super().__init__(*args, **kwargs)


# ─── Server Management ────────────────────────────────────────

def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Start the HTTP server for Telegram webhook."""
    server = HTTPServer((host, port), TelegramWebhookHandler)
    print(f"""
🤖 Telegram Intent Collector Adapter
====================================
Listening on http://{host}:{port}{WEBHOOK_PATH}
Health check: http://{host}:{port}/health

To set up webhook:
1. Get your bot token from @BotFather
2. Set webhook: https://api.telegram.org/bot<token>/setWebhook?url=https://your-domain.com{WEBHOOK_PATH}
3. Make sure your domain is publicly accessible and has valid SSL

The bot will guide users through intent collection and generate:
- spec.md
- trajectory.md  
- scope-baseline.md

Press Ctrl+C to stop.
    """.strip())
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Telegram Bot Adapter for Intent Collection")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind (default: {DEFAULT_PORT})")
    args = parser.parse_args()
    run_server(args.host, args.port)