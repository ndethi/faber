#!/usr/bin/env python3
"""
Feedback Skill - Lifecycle skill #8: collects user feedback after each run.

Reads the telemetry/observations of a run, optionally prompts for rating/notes,
and writes a feedback.json payload to the run directory.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Feedback skill - collect user feedback")
    parser.add_argument("--run-dir", required=True, help="Path to run directory (contains observations.json)")
    parser.add_argument("--output-dir", default=".", help="Directory to write feedback.json (default: run-dir)")
    parser.add_argument("--hitl-gate", action="store_true", help="Require manual confirmation before writing")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")
    parser.add_argument("--rating", type=int, choices=range(1, 6), help="Rating 1-5 (for non-interactive)")
    parser.add_argument("--notes", help="Feedback notes (for non-interactive)")
    return parser.parse_args()


def load_observations(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Load observations.json from run directory."""
    obs_path = run_dir / "observations.json"
    if not obs_path.exists():
        return None
    try:
        return json.loads(obs_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def load_telemetry(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Load telemetry.json from run directory."""
    telemetry_path = run_dir / "telemetry.json"
    if not telemetry_path.exists():
        return None
    try:
        return json.loads(telemetry_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def prompt_rating() -> int:
    """Prompt user for rating 1-5."""
    while True:
        try:
            response = input("Rate this run (1-5): ").strip()
            rating = int(response)
            if 1 <= rating <= 5:
                return rating
            print("Please enter a number between 1 and 5")
        except (ValueError, EOFError, KeyboardInterrupt):
            return 3  # Default neutral


def prompt_notes() -> str:
    """Prompt user for optional notes."""
    try:
        return input("Notes (optional, press Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def collect_feedback(
    run_dir: Path,
    output_dir: Path,
    hitl_gate: bool = False,
    dry_run: bool = False,
    rating: Optional[int] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Collect feedback and write to feedback.json."""
    
    # Load context
    observations = load_observations(run_dir)
    telemetry = load_telemetry(run_dir)
    
    run_id = run_dir.name
    
    # Determine rating/notes
    if rating is None:
        if hitl_gate:
            rating = prompt_rating()
        else:
            rating = 3  # Default neutral
    
    if notes is None:
        if hitl_gate:
            notes = prompt_notes()
        else:
            notes = ""
    
    # Build feedback payload
    feedback = {
        "run_id": run_id,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "rating": rating,
        "notes": notes,
        "context": {
            "runs_analyzed": observations.get("runs_analyzed") if observations else None,
            "success_rate": observations.get("aggregates", {}).get("success_rate") if observations else None,
            "total_tokens": observations.get("aggregates", {}).get("total_tokens") if observations else None,
            "total_cost_usd": observations.get("aggregates", {}).get("total_cost_usd") if observations else None,
            "skills_invoked": telemetry.get("skills", []) if telemetry else [],
            "trajectory_status": telemetry.get("trajectory_strictness") if telemetry else None,
        },
        "hitl_gate": hitl_gate,
        "dry_run": dry_run,
    }
    
    # Write or show
    output_path = output_dir / "feedback.json"
    
    if dry_run:
        print(f"[DRY RUN] Would write feedback to: {output_path}", file=sys.stderr)
        print(json.dumps(feedback, indent=2), file=sys.stderr)
    else:
        if hitl_gate:
            confirm = input(f"Write feedback to {output_path}? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Cancelled.", file=sys.stderr)
                return {"status": "cancelled", "feedback": feedback}
        
        output_path.write_text(json.dumps(feedback, indent=2))
        print(f"Feedback written to: {output_path}", file=sys.stderr)
    
    return {
        "status": "success",
        "artifacts": ["feedback.json"],
        "rating": rating,
        "notes": notes,
        "hitl_gate_required": hitl_gate,
        "hitl_gate_passed": not hitl_gate or True,
        "dry_run": dry_run,
    }


def main() -> int:
    args = parse_args()
    
    run_dir = Path(args.run_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    if not run_dir.exists():
        print(f"Error: Run directory does not exist: {run_dir}", file=sys.stderr)
        return 1
    
    if not run_dir.is_dir():
        print(f"Error: Run path is not a directory: {run_dir}", file=sys.stderr)
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        result = collect_feedback(
            run_dir=run_dir,
            output_dir=output_dir,
            hitl_gate=args.hitl_gate,
            dry_run=args.dry_run,
            rating=args.rating,
            notes=args.notes,
        )
        print(json.dumps(result))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())