#!/usr/bin/env python3
"""
Telemetry emission for pm-github skill (BG-018: trajectory-guard integration).

Emits telemetry in the format expected by trajectory-guard:
- runs/telemetry.jsonl (one line per skill invocation)
- Includes: run_id, skill, command, dry_run, success, duration_ms, timestamp
"""

import json
import os
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TelemetryEvent:
    """Single telemetry event for trajectory-guard."""
    run_id: str
    skill: str
    command: str
    dry_run: bool
    success: bool
    duration_ms: int
    timestamp: str
    repo: Optional[str] = None
    error: Optional[str] = None


class PmGithubTelemetry:
    """Telemetry emitter for pm-github skill."""

    def __init__(self, repo: Optional[str] = None, telemetry_dir: Optional[Path] = None):
        self.repo = repo
        self.telemetry_dir = telemetry_dir or Path("runs")
        self.telemetry_file = self.telemetry_dir / "telemetry.jsonl"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure telemetry directory exists."""
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, event: TelemetryEvent) -> None:
        """Emit a telemetry event to JSONL file."""
        # Also emit to stdout for CI capture
        print(json.dumps(asdict(event)), file=sys.stderr)
        # Write to file
        with self.telemetry_file.open("a") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def emit_skill_invocation(
        self,
        skill: str,
        command: str,
        dry_run: bool,
        success: bool,
        duration_ms: int,
        error: Optional[str] = None
    ) -> None:
        """Emit a skill invocation event."""
        event = TelemetryEvent(
            run_id=str(uuid.uuid4())[:8],
            skill=skill,
            command=command,
            dry_run=dry_run,
            success=success,
            duration_ms=duration_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
            repo=self.repo,
            error=error
        )
        self.emit(event)


class TelemetryContext:
    """Context manager for automatic telemetry emission around skill execution."""

    def __init__(
        self,
        telemetry: PmGithubTelemetry,
        skill: str,
        command: str,
        dry_run: bool = True
    ):
        self.telemetry = telemetry
        self.skill = skill
        self.command = command
        self.dry_run = dry_run
        self.start_time: Optional[datetime] = None
        self.success = False
        self.error: Optional[str] = None

    def __enter__(self) -> "TelemetryContext":
        self.start_time = datetime.now(timezone.utc)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        duration_ms = int((datetime.now(timezone.utc) - self.start_time).total_seconds() * 1000)
        self.success = exc_type is None
        self.error = str(exc_val) if exc_val else None

        self.telemetry.emit_skill_invocation(
            skill=self.skill,
            command=self.command,
            dry_run=self.dry_run,
            success=self.success,
            duration_ms=duration_ms,
            error=self.error
        )
        # Don't suppress exceptions
        return False


def main() -> None:
    """CLI for testing telemetry emission."""
    import argparse

    parser = argparse.ArgumentParser(description="Emit test telemetry")
    parser.add_argument("--skill", default="pm-github")
    parser.add_argument("--command", default="test")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--success", action="store_true", default=True)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--duration-ms", type=int, default=100)
    parser.add_argument("--error", default=None)

    args = parser.parse_args()

    telemetry = PmGithubTelemetry(repo=args.repo)
    telemetry.emit_skill_invocation(
        skill=args.skill,
        command=args.command,
        dry_run=args.dry_run,
        success=args.success,
        duration_ms=args.duration_ms,
        error=args.error
    )
    print(f"Telemetry emitted to {telemetry.telemetry_file}")


if __name__ == "__main__":
    main()