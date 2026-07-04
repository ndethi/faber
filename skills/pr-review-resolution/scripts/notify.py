#!/usr/bin/env python3
"""
Telegram notifications via Hermes gateway.
Sends structured notifications for PR review resolution events.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def send_telegram(message: str, silent: bool = False) -> bool:
    """Send message via Hermes Telegram gateway."""
    # Method 1: Use hermes CLI if available
    hermes_bin = os.environ.get("HERMES_BIN", "hermes")
    profile = os.environ.get("HERMES_PROFILE", "faber")

    cmd = [hermes_bin, "--profile", profile, "gateway", "send", "telegram"]
    if silent:
        cmd.append("--silent")
    cmd.extend(["--message", message])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        return True

    # Method 2: Direct webhook if configured
    webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
    if webhook_url:
        import urllib.request
        data = json.dumps({"text": message, "disable_notification": silent}).encode()
        req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception:
            pass

    # Method 3: Use bot token + chat_id from env
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        import urllib.request
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "disable_notification": silent,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception:
            pass

    return False


def format_fetch_notification(data: Dict[str, Any]) -> str:
    """Format notification for fetch event."""
    pr = data.get("pr_number", "?")
    repo = data.get("repo", "?")
    total = data.get("total", 0)
    return f"📥 <b>PR #{pr}</b> ({repo}) — Fetched <b>{total}</b> review comments"


def format_categorize_notification(data: Dict[str, Any]) -> str:
    """Format notification for categorize event."""
    summary = data.get("summary", {})
    by_cat = summary.get("by_category", {})
    cats = ", ".join(f"{k}: {v}" for k, v in sorted(by_cat.items()))
    return f"🏷️ <b>Categorized</b> — {cats}"


def format_resolve_notification(data: Dict[str, Any]) -> str:
    """Format notification for resolve event."""
    summary = data.get("summary", {})
    applied = summary.get("applied", 0)
    deferred = summary.get("deferred", 0)
    failed = summary.get("failed", 0)
    return f"🔧 <b>Resolved</b> — ✅ {applied} applied, ⏳ {deferred} deferred, ❌ {failed} failed"


def format_push_notification(data: Dict[str, Any]) -> str:
    """Format notification for push event."""
    branch = data.get("branch", "?")
    commits = data.get("commit_shas", [])
    commit_str = ", ".join(c[:7] for c in commits[:3])
    if len(commits) > 3:
        commit_str += f" +{len(commits) - 3} more"
    return f"📤 <b>Pushed</b> to <code>{branch}</code> — commits: {commit_str}"


def format_hitl_notification(data: Dict[str, Any]) -> str:
    """Format notification for HITL needed."""
    deferred = data.get("deferred", [])
    lines = ["⏳ <b>HITL Required</b> — Human review needed for:"]
    for d in deferred[:5]:
        cat = d.get("category", "?")
        path = d.get("path", "?")
        error = d.get("error", "no reason")
        lines.append(f"  • #{d['comment_id']} ({cat}): {path} — {error}")
    if len(deferred) > 5:
        lines.append(f"  … and {len(deferred) - 5} more")
    return "\n".join(lines)


def format_pr_update_notification(data: Dict[str, Any]) -> str:
    """Format notification for PR update."""
    pr = data.get("pr_number", "?")
    repo = data.get("repo", "?")
    return f"💬 <b>PR #{pr}</b> ({repo}) — Updated with resolution comments"


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: notify.py <event> <data_file>"}))
        sys.exit(1)

    event = sys.argv[1]
    data_file = sys.argv[2]

    with open(data_file) as f:
        data = json.load(f)

    formatters = {
        "fetch": format_fetch_notification,
        "categorize": format_categorize_notification,
        "resolve": format_resolve_notification,
        "push": format_push_notification,
        "hitl": format_hitl_notification,
        "pr_update": format_pr_update_notification,
    }

    formatter = formatters.get(event)
    if not formatter:
        print(json.dumps({"error": f"Unknown event: {event}"}))
        sys.exit(1)

    message = formatter(data)
    silent = event in ["fetch", "categorize"]  # Quiet for intermediate steps

    success = send_telegram(message, silent=silent)

    print(json.dumps({"success": success, "event": event, "message": message}))


if __name__ == "__main__":
    main()