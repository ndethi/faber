#!/usr/bin/env python3
"""
Scope Ledger — Tracks baseline scope vs extended scope with cost and IP attribution.

Implements FRAMEWORK.md §9: commercial layer with baseline scope (from intent-collect)
and extended-scope items from feedback loop.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_LEDGER = {
    "baseline": {
        "content": "",
        "hash": "",
        "created_at": "",
    },
    "extended": [],
}


def load_ledger(ledger_path: Path) -> Dict[str, Any]:
    """Load scope ledger, creating default if not exists."""
    if ledger_path.exists():
        with open(ledger_path, "r") as f:
            return json.load(f)
    else:
        return DEFAULT_LEDGER.copy()


def save_ledger(ledger: Dict[str, Any], ledger_path: Path) -> None:
    """Save scope ledger."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=2)


def init_from_baseline(scope_baseline_path: Path, ledger_path: Path) -> Dict[str, Any]:
    """Initialize ledger from scope-baseline.md."""
    if not scope_baseline_path.exists():
        raise FileNotFoundError(f"Scope baseline not found: {scope_baseline_path}")

    content = scope_baseline_path.read_text()
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    created_at = datetime.now(timezone.utc).isoformat()

    ledger = {
        "baseline": {
            "content": content,
            "hash": content_hash,
            "created_at": created_at,
        },
        "extended": [],
    }

    save_ledger(ledger, ledger_path)
    return ledger


def add_extended_item(
    ledger: Dict[str, Any],
    description: str,
    source: str,
    estimated_cost: float,
    estimated_tokens: int,
    model_route: str,
    ip_attribution: str,
) -> Dict[str, Any]:
    """Add an extended-scope item."""
    # Generate ID
    count = len(ledger.get("extended", [])) + 1
    item_id = f"EXT-{count:03d}"

    item = {
        "id": item_id,
        "description": description,
        "source": source,
        "estimated_agent_cost_usd": estimated_cost,
        "estimated_tokens": estimated_tokens,
        "model_route": model_route,
        "ip_attribution": ip_attribution,
        "status": "proposed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
    }

    if "extended" not in ledger:
        ledger["extended"] = []
    ledger["extended"].append(item)

    return item


def update_item_status(ledger: Dict[str, Any], item_id: str, status: str) -> bool:
    """Update status of an extended item."""
    valid_statuses = ["proposed", "approved", "implemented", "rejected"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    for item in ledger.get("extended", []):
        if item["id"] == item_id:
            item["status"] = status
            if status == "approved":
                item["approved_at"] = datetime.now(timezone.utc).isoformat()
            return True
    return False


def get_summary(ledger: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics."""
    extended = ledger.get("extended", [])

    by_status = {"proposed": 0, "approved": 0, "implemented": 0, "rejected": 0}
    by_ip = {"client": 0, "dev": 0, "agent": 0, "shared": 0}
    total_cost = 0.0
    total_tokens = 0

    for item in extended:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        by_ip[item["ip_attribution"]] = by_ip.get(item["ip_attribution"], 0) + 1
        total_cost += item.get("estimated_agent_cost_usd", 0.0)
        total_tokens += item.get("estimated_tokens", 0)

    return {
        "baseline_items": 1 if ledger.get("baseline", {}).get("content") else 0,
        "extended_items": len(extended),
        "total_estimated_cost_usd": round(total_cost, 4),
        "total_estimated_tokens": total_tokens,
        "by_status": by_status,
        "by_ip": by_ip,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scope Ledger — track baseline vs extended scope"
    )
    parser.add_argument(
        "--scope-baseline-path",
        help="Path to scope-baseline.md (for init)",
    )
    parser.add_argument(
        "--ledger-path",
        default="runs/scope-ledger/ledger.json",
        help="Path to ledger JSON (default: runs/scope-ledger/ledger.json)",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize ledger from scope-baseline.md",
    )
    parser.add_argument(
        "--add-item",
        action="store_true",
        help="Add extended-scope item (requires --description, --source, --estimated-cost, --estimated-tokens, --model-route, --ip-attribution)",
    )
    parser.add_argument(
        "--description",
        help="Description for new extended item",
    )
    parser.add_argument(
        "--source",
        choices=["client-feedback", "dev-discovered", "spec-gap", "regression"],
        help="Source of extended item",
    )
    parser.add_argument(
        "--estimated-cost",
        type=float,
        help="Estimated agent cost in USD",
    )
    parser.add_argument(
        "--estimated-tokens",
        type=int,
        help="Estimated token count",
    )
    parser.add_argument(
        "--model-route",
        choices=["local", "frontier"],
        help="Model route for estimation",
    )
    parser.add_argument(
        "--ip-attribution",
        choices=["client", "dev", "agent", "shared"],
        help="IP attribution",
    )
    parser.add_argument(
        "--update-item",
        help="Update status of extended item (provide item ID like EXT-001)",
    )
    parser.add_argument(
        "--status",
        choices=["proposed", "approved", "implemented", "rejected"],
        help="New status for --update-item",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show ledger contents",
    )

    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)

    if args.init:
        if not args.scope_baseline_path:
            print(json.dumps({"error": "--init requires --scope-baseline-path"}))
            sys.exit(1)
        ledger = init_from_baseline(Path(args.scope_baseline_path), ledger_path)
        summary = get_summary(ledger)
        print(json.dumps({"status": "initialized", "summary": summary}, indent=2))
        return

    # Load existing ledger
    ledger = load_ledger(ledger_path)

    if args.add_item:
        if not all([args.description, args.source, args.estimated_cost is not None,
                    args.estimated_tokens is not None, args.model_route, args.ip_attribution]):
            print(json.dumps({"error": "--add-item requires --description, --source, --estimated-cost, --estimated-tokens, --model-route, --ip-attribution"}))
            sys.exit(1)

        item = add_extended_item(
            ledger,
            args.description,
            args.source,
            args.estimated_cost,
            args.estimated_tokens,
            args.model_route,
            args.ip_attribution,
        )
        save_ledger(ledger, ledger_path)
        summary = get_summary(ledger)
        print(json.dumps({"status": "added", "item": item, "summary": summary}, indent=2))
        return

    if args.update_item:
        if not args.status:
            print(json.dumps({"error": "--update-item requires --status"}))
            sys.exit(1)

        success = update_item_status(ledger, args.update_item, args.status)
        if not success:
            print(json.dumps({"error": f"Item not found: {args.update_item}"}))
            sys.exit(1)

        save_ledger(ledger, ledger_path)
        summary = get_summary(ledger)
        print(json.dumps({"status": "updated", "item_id": args.update_item, "new_status": args.status, "summary": summary}, indent=2))
        return

    if args.show:
        summary = get_summary(ledger)
        print(json.dumps({"ledger": ledger, "summary": summary}, indent=2))
        return

    # Default: show summary
    summary = get_summary(ledger)
    print(json.dumps({"ledger": ledger, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()