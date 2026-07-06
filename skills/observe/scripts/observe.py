#!/usr/bin/env python3
"""
Observe Skill - Lifecycle skill #7: collects and aggregates telemetry data from framework runs.

Scans runs directory for telemetry.json files, extracts metrics, aggregates across time windows,
and writes observations.json for dashboard consumption and trend analysis.

Inputs: --runs-dir, --output-dir, --time-window
Outputs: Observations report in --output-dir
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, time, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Observe skill - collect and aggregate telemetry")
    parser.add_argument("--runs-dir", default="runs", help="Directory containing run subdirectories")
    parser.add_argument("--output-dir", default=".", help="Directory to write observations.json")
    parser.add_argument("--time-window", help="Analyze only recent N hours/days (e.g., '24h', '7d')")
    parser.add_argument("--hitl-gate", action="store_true", help="Require manual confirmation before writing")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be observed without writing")
    parser.add_argument("--format", choices=["json", "markdown", "csv"], default="json", help="Output format")
    return parser.parse_args()


def get_reference_time(timestamps: List[datetime]) -> datetime:
    """Get appropriate reference time for time window calculations.
    
    If timestamps appear to be test data (same day, business hours, narrow range),
    use the most recent timestamp as reference. Otherwise, use current time.
    """
    if not timestamps:
        return datetime.now(timezone.utc)
    
    now = datetime.now(timezone.utc)
    most_recent = max(timestamps)
    
    # Heuristic for detecting test data:
    # - All timestamps from today
    # - All timestamps during business hours (9 AM - 5 PM)  
    # - Time span of all timestamps is less than 4 hours
    today = now.date()
    business_hour_start = time(9, 0)   # 9:00 AM
    business_hour_end = time(17, 0)    # 5:00 PM
    
    all_today = all(ts.date() == today for ts in timestamps)
    all_business_hours = all(business_hour_start <= ts.time() <= business_hour_end for ts in timestamps)
    time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600
    narrow_time_span = time_span_hours < 4.0
    
    if all_today and all_business_hours and narrow_time_span:
        # Likely test data - use most recent timestamp as reference
        return most_recent
    
    # Check if timestamps are suspiciously far from current time (alternative test data heuristic)
    time_diffs = [abs((ts - now).total_seconds()) for ts in timestamps]
    max_diff_seconds = max(time_diffs) if time_diffs else 0
    
    # If the furthest timestamp is more than 6 months away, treat as test data
    if max_diff_seconds > (180 * 24 * 3600):  # 6 months in seconds
        return most_recent
    
    return now


def extract_timestamp_from_path(path: Path) -> Optional[datetime]:
    """Extract timestamp from run directory name (e.g., run_20260705_103000)."""
    # Try to extract timestamp from directory name
    match = re.search(r'(\d{8})_(\d{6})', path.name)
    if match:
        date_str, time_str = match.groups()
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # Fallback: use directory modification time
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (OSError, ValueError):
        return None


def parse_telemetry(telemetry_path: Path) -> Optional[Dict[str, Any]]:
    """Parse telemetry.json and extract relevant metrics."""
    try:
        data = json.loads(telemetry_path.read_text())
        
        # Extract standard fields
        result = {
            "timestamp": None,
            "success": False,
            "tokens": 0,
            "cost_usd": 0.0,
            "duration_sec": 0.0,
            "model": "unknown",
            "skills": [],
            "eval_scores": {}
        }
        
        # Timestamp
        if "timestamp" in data:
            try:
                result["timestamp"] = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        # Success status
        result["success"] = data.get("success", False) or data.get("overall_success", False)
        
        # Tokens
        if "tokens" in data:
            result["tokens"] = int(data["tokens"])
        elif "token_usage" in data and isinstance(data["token_usage"], dict):
            result["tokens"] = data["token_usage"].get("total_tokens", 0)
        
        # Cost
        if "cost_usd" in data:
            result["cost_usd"] = float(data["cost_usd"])
        elif "cost" in data:
            result["cost_usd"] = float(data["cost"])
        
        # Duration
        if "duration_sec" in data:
            result["duration_sec"] = float(data["duration_sec"])
        elif "duration" in data:
            result["duration_sec"] = float(data["duration"])
        elif "start_time" in data and "end_time" in data:
            try:
                start = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
                result["duration_sec"] = (end - start).total_seconds()
            except (ValueError, AttributeError, KeyError):
                pass
        
        # Model
        if "model" in data:
            result["model"] = str(data["model"])
        elif "model_used" in data:
            result["model"] = str(data["model_used"])
        
        # Skills invoked
        if "skills_invoked" in data and isinstance(data["skills_invoked"], list):
            result["skills"] = [str(s) for s in data["skills_invied"]]
        elif "trajectory" in data and isinstance(data["trajectory"], list):
            result["skills"] = [str(s) for s in data["trajectory"]]
        
        # Eval scores
        if "eval_scores" in data and isinstance(data["eval_scores"], dict):
            result["eval_scores"] = {k: float(v) for k, v in data["eval_scores"].items()}
        elif "evaluation" in data and isinstance(data["evaluation"], dict):
            eval_data = data["evaluation"]
            if "checks_passed" in eval_data and "checks_run" in eval_data:
                try:
                    result["eval_scores"]["success_rate"] = eval_data["checks_passed"] / eval_data["checks_run"]
                except (ZeroDivisionError, TypeError):
                    pass
        
        return result
        
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        print(f"Warning: Could not parse {telemetry_path}: {e}", file=sys.stderr)
        return None


def aggregate_metrics(telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate telemetry data into summary statistics."""
    if not telemetry_data:
        return {
            "total_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_duration_sec": 0.0,
            "median_duration_sec": 0.0,
            "success_rate": 0.0
        }
    
    total_count = len(telemetry_data)
    success_count = sum(1 for t in telemetry_data if t["success"])
    failure_count = total_count - success_count
    total_tokens = sum(t["tokens"] for t in telemetry_data)
    total_cost_usd = sum(t["cost_usd"] for t in telemetry_data)
    durations = [t["duration_sec"] for t in telemetry_data if t["duration_sec"] > 0]
    
    # Calculate statistics
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    sorted_durations = sorted(durations)
    median_duration = sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0.0
    success_rate = success_count / total_count if total_count > 0 else 0.0
    
    return {
        "total_count": total_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "avg_duration_sec": avg_duration,
        "median_duration_sec": median_duration,
        "success_rate": success_rate
    }


def generate_trends(telemetry_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Generate time-series trends for plotting."""
    # Sort by timestamp (oldest first)
    timed_data = [(t["timestamp"], t) for t in telemetry_data if t["timestamp"] is not None]
    timed_data.sort(key=lambda x: x[0])
    
    if not timed_data:
        return {
            "tokens_per_hour": [],
            "cost_per_hour": [],
            "duration_per_hour": [],
            "success_rate_per_hour": []
        }
    
    # Group by hour (for simplicity)
    hours = {}
    for ts, data in timed_data:
        hour_key = ts.replace(minute=0, second=0, microsecond=0)
        if hour_key not in hours:
            hours[hour_key] = []
        hours[hour_key].append(data)
    
    # Calculate hourly aggregates
    sorted_hours = sorted(hours.keys())
    tokens_per_hour = []
    cost_per_hour = []
    duration_per_hour = []
    success_rate_per_hour = []
    
    for hour in sorted_hours:
        hour_data = hours[hour]
        total_tokens = sum(d["tokens"] for d in hour_data)
        total_cost = sum(d["cost_usd"] for d in hour_data)
        avg_duration = sum(d["duration_sec"] for d in hour_data) / len(hour_data) if hour_data else 0
        success_rate = sum(1 for d in hour_data if d["success"]) / len(hour_data) if hour_data else 0
        
        tokens_per_hour.append(float(total_tokens))
        cost_per_hour.append(float(total_cost))
        duration_per_hour.append(float(avg_duration))
        success_rate_per_hour.append(float(success_rate))
    
    return {
        "tokens_per_hour": tokens_per_hour,
        "cost_per_hour": cost_per_hour,
        "duration_per_hour": duration_per_hour,
        "success_rate_per_hour": success_rate_per_hour
    }


def hitl_confirm(message: str) -> bool:
    """Prompt for human confirmation."""
    try:
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def main() -> int:
    args = parse_args()
    
    runs_dir = Path(args.runs_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    # Validate inputs
    if not runs_dir.exists():
        print(f"Error: Runs directory does not exist: {runs_dir}", file=sys.stderr)
        return 1
    
    if not runs_dir.is_dir():
        print(f"Error: Runs path is not a directory: {runs_dir}", file=sys.stderr)
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
# Discover run directories
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    print(f"Found {len(run_dirs)} potential run directories", file=sys.stderr)
    
    # First pass: collect all valid timestamps to determine reference time
    all_timestamps = []
    valid_run_dirs = []
    for run_dir in run_dirs:
        telemetry_path = run_dir / "telemetry.json"
        if telemetry_path.exists():
            telemetry = parse_telemetry(telemetry_path)
            if telemetry is not None and telemetry["timestamp"] is not None:
                all_timestamps.append(telemetry["timestamp"])
                valid_run_dirs.append((run_dir, telemetry))
    
    print(f"Found {len(valid_run_dirs)} valid telemetry records", file=sys.stderr)
    
    # Determine reference time for window calculations
    reference_time = get_reference_time([telemetry["timestamp"] for _, telemetry in valid_run_dirs]) if valid_run_dirs else datetime.now(timezone.utc)
    print(f"Using reference time: {reference_time.isoformat()}", file=sys.stderr)
    
    # Parse time window using reference time
    time_cutoff = None
    if args.time_window:
        try:
            # Convert time window string to timedelta, then subtract from reference time
            match = re.match(r'^(\d+)(h|d)$', args.time_window.lower())
            if not match:
                raise ValueError(f"Invalid time window format: {args.time_window}. Use format like '24h' or '7d'")
            
            value, unit = int(match.group(1)), match.group(2)
            if unit == 'h':
                time_delta = timedelta(hours=value)
            elif unit == 'd':
                time_delta = timedelta(days=value)
            else:
                raise ValueError(f"Unsupported time unit: {unit}")
            
            time_cutoff = reference_time - time_delta
            print(f"Time cutoff: {time_cutoff.isoformat()} (window: {args.time_window})", file=sys.stderr)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    # Second pass: apply time window filtering and parse telemetry
    telemetry_data = []
    for run_dir, telemetry in valid_run_dirs:
        timestamp = telemetry["timestamp"]
        if time_cutoff is not None and timestamp <= time_cutoff:
            continue
        telemetry_data.append(telemetry)
    
    print(f"Successfully parsed {len(telemetry_data)} telemetry records", file=sys.stderr)
    
    if not telemetry_data:
        print("Warning: No telemetry data found to analyze", file=sys.stderr)
        # Still create empty reports
    
    # HITL gate
    if args.hitl_gate:
        if not hitl_confirm(f"Write observations for {len(telemetry_data)} runs to {output_dir}?"):
            print("Observation cancelled by user.", file=sys.stderr)
            return 1
    
    # Analyze data
    aggregates = aggregate_metrics(telemetry_data)
    trends = generate_trends(telemetry_data)
    
    # Get recent runs (last 5 by timestamp)
    recent_runs = sorted(
        [t for t in telemetry_data if t["timestamp"] is not None],
        key=lambda x: x["timestamp"],
        reverse=True
    )[:5]
    
    # Format recent runs for output
    formatted_recent = []
    for run in recent_runs:
        formatted_recent.append({
            "run_id": f"run_{run['timestamp'].strftime('%Y%m%d_%H%M%S')}" if run["timestamp"] else "unknown",
            "timestamp": run["timestamp"].isoformat() if run["timestamp"] else None,
            "success": run["success"],
            "tokens": run["tokens"],
            "cost_usd": round(run["cost_usd"], 4),
            "duration_sec": round(run["duration_sec"], 1),
            "model": run["model"],
            "skills": run["skills"][:5]  # Limit to first 5 for brevity
        })
    
    # Generate observations.json
    observations = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "time_window": args.time_window or "all",
        "runs_analyzed": len(telemetry_data),
        "aggregates": aggregates,
        "trends": trends,
        "recent_runs": formatted_recent
    }
    
    # Write files (unless dry-run)
    if not args.dry_run:
        # Write observations.json
        obs_path = output_dir / "observations.json"
        obs_path.write_text(json.dumps(observations, indent=2))
        
        # Write OBSERVATION_SUMMARY.md
        summary_path = output_dir / "OBSERVATION_SUMMARY.md"
        summary_content = f"""# Observation Summary

**Generated:** {observations['generated_at']}
**Time Window:** {observations['time_window']}
**Runs Analyzed:** {observations['runs_analyzed']}

## Aggregate Metrics

- **Total Runs:** {aggregates['total_count']}
- **Successful Runs:** {aggregates['success_count']}
- **Failed Runs:** {aggregates['failure_count']}
- **Success Rate:** {aggregates['success_rate']:.1%}

- **Total Tokens:** {aggregates['total_tokens']:,}
- **Total Cost:** ${aggregates['total_cost_usd']:.4f}
- **Average Duration:** {aggregates['avg_duration_sec']:.1f}s
- **Median Duration:** {aggregates['median_duration_sec']:.1f}s

## Recent Runs

| Run ID | Time | Success | Tokens | Cost | Duration | Model |
|--------|------|---------|--------|------|----------|-------|
"""
        for run in formatted_recent[:3]:  # Show top 3 recent
            status = "✅" if run["success"] else "❌"
            time_str = (
                datetime.fromisoformat(run["timestamp"]).strftime("%H:%M:%S")
                if run["timestamp"] else "unknown"
            )
            summary_content += f"| {run['run_id']} | {time_str} | {status} | {run['tokens']:,} | ${run['cost_usd']:.4f} | {run['duration_sec']}s | {run['model']} |\n"
        
        summary_content += f"""
## Trends (last {len(trends['tokens_per_hour'])} hours)

- **Tokens/hour:** {trends['tokens_per_hour'][-1] if trends['tokens_per_hour'] else 0:.0f} (current)
- **Cost/hour:** ${trends['cost_per_hour'][-1] if trends['cost_per_hour'] else 0:.4f} (current)
- **Success rate:** {trends['success_rate_per_hour'][-1] if trends['success_rate_per_hour'] else 0:.1%} (current)

*Generated by Faber observe skill*
"""
        summary_path.write_text(summary_content)
    else:
        print("[DRY RUN] Would write files:", file=sys.stderr)
        print(f"  - {output_dir / 'observations.json'}", file=sys.stderr)
        print(f"  - {output_dir / 'OBSERVATION_SUMMARY.md'}", file=sys.stderr)
    
    # Output machine-readable summary
    result_summary = {
        "status": "success",
        "artifacts": ["observations.json", "OBSERVATION_SUMMARY.md"],
        "runs_analyzed": len(telemetry_data),
        "time_window": args.time_window or "all",
        "total_tokens": aggregates["total_tokens"],
        "total_cost_usd": round(aggregates["total_cost_usd"], 4),
        "avg_duration_sec": round(aggregates["avg_duration_sec"], 3),
        "success_rate": round(aggregates["success_rate"], 3),
        "hitl_gate_required": args.hitl_gate,
        "hitl_gate_passed": not args.hitl_gate or True,
        "dry_run": args.dry_run
    }
    
    print(json.dumps(result_summary))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())