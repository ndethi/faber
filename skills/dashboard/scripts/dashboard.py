#!/usr/bin/env python3
"""
Dashboard Skill — Generates management dashboard from telemetry.

Implements FRAMEWORK.md §5: single-file HTML dashboard with runs table,
trajectory diffs, cost/model-routing, eval scores, deploy health,
HITL queue, and scope ledger.
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_all_telemetry(runs_dir: Path) -> List[Dict[str, Any]]:
    """Load all telemetry.json files from runs/ directory."""
    telemetry_files = glob.glob(str(runs_dir / "**" / "telemetry.json"), recursive=True)
    telemetry_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

    runs = []
    for tf in telemetry_files:
        try:
            with open(tf, "r") as f:
                data = json.load(f)
                # Add run directory path for reference
                data["_run_dir"] = str(Path(tf).parent)
                runs.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to load {tf}: {e}", file=sys.stderr)
            continue

    return runs


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp for display."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts


def format_duration_ms(ms: int) -> str:
    """Format duration in ms to human readable."""
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms/60000:.1f}m"


def get_run_status(run: Dict) -> str:
    """Determine overall run status from skills."""
    skills = run.get("skills", [])
    if not skills:
        return "empty"
    if all(s.get("status") == "success" for s in skills):
        return "success"
    if any(s.get("status") == "failure" for s in skills):
        return "failure"
    return "mixed"


def calculate_trajectory_match(run: Dict) -> float:
    """Calculate trajectory match percentage from run data."""
    # This would ideally come from trajectory-guard output
    # For now, approximate from skills that succeeded
    skills = run.get("skills", [])
    if not skills:
        return 0.0
    expected = run.get("expected_trajectory", [])
    if not expected:
        return 100.0
    expected_ids = {s.get("skill_id", "") for s in expected}
    actual_ids = {s.get("skill_id", "") for s in skills}
    if not expected_ids:
        return 100.0
    matched = len(expected_ids & actual_ids)
    return round(matched / len(expected_ids) * 100, 1)


def generate_runs_table(runs: List[Dict]) -> str:
    """Generate HTML table for runs list."""
    rows = []
    for run in runs:
        run_id = run.get("run_id", "unknown")[:8]
        timestamp = format_timestamp(run.get("timestamp", ""))
        status = get_run_status(run)
        match_pct = calculate_trajectory_match(run)
        model = run.get("model", "unknown")
        tokens = run.get("tokens", {}).get("total", 0)
        cost = run.get("cost", 0.0)
        deploy = run.get("deploy_status", "not_deployed")

        status_class = "status-success" if status == "success" else ("status-failure" if status == "failure" else "status-mixed")
        deploy_class = f"deploy-{deploy}"

        rows.append(f"""
        <tr>
            <td><code>{run_id}</code></td>
            <td>{timestamp}</td>
            <td><span class="status-badge {status_class}">{status}</span></td>
            <td>{match_pct}%</td>
            <td>{model}</td>
            <td>{tokens:,}</td>
            <td>${cost:.4f}</td>
            <td><span class="deploy-badge {deploy_class}">{deploy}</span></td>
        </tr>""")

    return f"""
    <table class="runs-table">
        <thead>
            <tr>
                <th>Run ID</th>
                <th>Timestamp</th>
                <th>Status</th>
                <th>Traj. Match</th>
                <th>Model</th>
                <th>Tokens</th>
                <th>Cost</th>
                <th>Deploy</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows) if rows else '<tr><td colspan="8" class="empty">No runs found</td></tr>'}
        </tbody>
    </table>"""


def generate_trajectory_detail(run: Dict) -> str:
    """Generate trajectory diff detail for a run."""
    expected = run.get("expected_trajectory", [])
    actual = run.get("skills", [])

    expected_ids = [s.get("skill_id", "") for s in expected]
    actual_ids = [s.get("skill_id", "") for s in actual]

    missing = [e for e in expected_ids if e not in actual_ids]
    extra = [a for a in actual_ids if a not in expected_ids]

    # Simple order check
    out_of_order = []
    exp_idx = 0
    for a_id in actual_ids:
        if a_id in expected_ids:
            expected_pos = expected_ids.index(a_id)
            if expected_pos < exp_idx:
                out_of_order.append(a_id)
            exp_idx = max(exp_idx, expected_pos)

    gate_violations = [
        s.get("skill_id", "") for s in expected
        if s.get("gate", False) and s.get("skill_id", "") not in actual_ids
    ]

    return f"""
    <div class="trajectory-detail">
        <h4>Run: {run.get('run_id', 'unknown')[:8]}</h4>
        <div class="diff-grid">
            <div class="diff-col">
                <h5>Expected ({len(expected_ids)})</h5>
                <ul class="step-list">
                    {''.join(f'<li class="{"missing" if e in missing else ""}">{e}{" 🔒" if any(s.get("gate") for s in expected if s.get("skill_id")==e) else ""}</li>' for e in expected_ids)}
                </ul>
            </div>
            <div class="diff-col">
                <h5>Actual ({len(actual_ids)})</h5>
                <ul class="step-list">
                    {''.join(f'<li class="{"extra" if a in extra else ""} {"out-of-order" if a in out_of_order else ""}">{a}</li>' for a in actual_ids)}
                </ul>
            </div>
        </div>
        <div class="diff-summary">
            {'<span class="badge warning">Missing: ' + ', '.join(missing) + '</span>' if missing else ''}
            {'<span class="badge info">Extra: ' + ', '.join(extra) + '</span>' if extra else ''}
            {'<span class="badge warning">Out of order: ' + ', '.join(out_of_order) + '</span>' if out_of_order else ''}
            {'<span class="badge danger">Gate violations: ' + ', '.join(gate_violations) + '</span>' if gate_violations else ''}
        </div>
    </div>"""


def generate_cost_summary(runs: List[Dict]) -> str:
    """Generate cost summary section."""
    total_cost = sum(r.get("cost", 0.0) for r in runs)
    total_tokens = sum(r.get("tokens", {}).get("total", 0) for r in runs)

    # Per-skill cost (approximate from duration if available)
    skill_costs: Dict[str, float] = {}
    skill_counts: Dict[str, int] = {}

    for run in runs:
        for skill in run.get("skills", []):
            sid = skill.get("skill_id", "unknown")
            skill_counts[sid] = skill_counts.get(sid, 0) + 1
            # Rough estimate: cost proportional to duration
            duration = skill.get("duration_ms", 0)
            skill_costs[sid] = skill_costs.get(sid, 0.0) + (duration / 1000.0 * 0.001)  # $0.001 per second

    skill_rows = ""
    for sid in sorted(skill_costs.keys()):
        skill_rows += f"""
        <tr>
            <td>{sid}</td>
            <td>{skill_counts.get(sid, 0)}</td>
            <td>${skill_costs[sid]:.4f}</td>
        </tr>"""

    return f"""
    <div class="cost-summary">
        <h3>Cost Summary</h3>
        <div class="summary-cards">
            <div class="card">
                <span class="label">Total Cost</span>
                <span class="value">${total_cost:.4f}</span>
            </div>
            <div class="card">
                <span class="label">Total Tokens</span>
                <span class="value">{total_tokens:,}</span>
            </div>
            <div class="card">
                <span class="label">Total Runs</span>
                <span class="value">{len(runs)}</span>
            </div>
        </div>
        <h4>Per-Skill Estimates</h4>
        <table class="skill-cost-table">
            <thead><tr><th>Skill</th><th>Runs</th><th>Est. Cost</th></tr></thead>
            <tbody>{skill_rows or '<tr><td colspan="3" class="empty">No skill cost data</td></tr>'}</tbody>
        </table>
    </div>"""


def generate_model_routing(runs: List[Dict]) -> str:
    """Generate model routing decisions section."""
    # Extract model usage per run
    model_usage: Dict[str, int] = {}
    for run in runs:
        model = run.get("model", "unknown")
        model_usage[model] = model_usage.get(model, 0) + 1

    rows = ""
    for model, count in sorted(model_usage.items()):
        rows += f"<tr><td>{model}</td><td>{count}</td></tr>"

    return f"""
    <div class="model-routing">
        <h3>Model Routing</h3>
        <table class="model-table">
            <thead><tr><th>Model</th><th>Runs</th></tr></thead>
            <tbody>{rows or '<tr><td colspan="2" class="empty">No model data</td></tr>'}</tbody>
        </table>
    </div>"""


def generate_eval_scores(runs: List[Dict]) -> str:
    """Generate eval scores section."""
    all_metrics: Dict[str, List[float]] = {}

    for run in runs:
        for metric, value in run.get("eval_scores", {}).items():
            if metric not in all_metrics:
                all_metrics[metric] = []
            all_metrics[metric].append(value)

    rows = ""
    for metric, values in sorted(all_metrics.items()):
        avg = sum(values) / len(values) if values else 0
        rows += f"<tr><td>{metric}</td><td>{len(values)}</td><td>{avg:.3f}</td><td>{min(values):.3f}</td><td>{max(values):.3f}</td></tr>"

    return f"""
    <div class="eval-scores">
        <h3>Eval Scores</h3>
        <table class="eval-table">
            <thead><tr><th>Metric</th><th>Runs</th><th>Avg</th><th>Min</th><th>Max</th></tr></thead>
            <tbody>{rows or '<tr><td colspan="5" class="empty">No eval data</td></tr>'}</tbody>
        </table>
    </div>"""


def generate_hitl_queue() -> str:
    """Generate HITL queue section (placeholder - would integrate with GitHub API)."""
    return """
    <div class="hitl-queue">
        <h3>HITL Queue</h3>
        <p class="placeholder">HITL queue integration requires GitHub API access. Pending:</p>
        <ul>
            <li>Open PRs awaiting review</li>
            <li>Skill-author PRs pending approval</li>
            <li>Spec changes awaiting confirmation</li>
        </ul>
    </div>"""


def generate_scope_ledger() -> str:
    """Generate scope ledger section (placeholder)."""
    return """
    <div class="scope-ledger">
        <h3>Scope Ledger</h3>
        <p class="placeholder">Scope ledger tracks baseline vs extended scope. Requires integration with intent-collect output and feedback loop.</p>
        <table class="scope-table">
            <thead><tr><th>Item</th><th>Type</th><th>Est. Cost</th><th>IP Attribution</th><th>Status</th></tr></thead>
            <tbody><tr><td colspan="5" class="empty">No scope data</td></tr></tbody>
        </table>
    </div>"""


def generate_html(runs: List[Dict], summary: Dict) -> str:
    """Generate complete HTML dashboard."""
    runs_table = generate_runs_table(runs)
    trajectory_details = "".join(generate_trajectory_detail(r) for r in runs)
    cost_summary = generate_cost_summary(runs)
    model_routing = generate_model_routing(runs)
    eval_scores = generate_eval_scores(runs)
    hitl_queue = generate_hitl_queue()
    scope_ledger = generate_scope_ledger()

    total_runs = len(runs)
    total_cost = summary.get("total_cost", 0.0)
    avg_match = summary.get("avg_trajectory_match", 0.0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Faber Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a2e; background: #f5f5f7; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
        header {{ margin-bottom: 32px; }}
        h1 {{ font-size: 2rem; font-weight: 700; color: #1a1a2e; }}
        .subtitle {{ color: #6b6b7b; margin-top: 4px; }}
        .summary-bar {{ display: flex; gap: 16px; margin-bottom: 32px; flex-wrap: wrap; }}
        .summary-card {{ background: white; border-radius: 12px; padding: 20px 24px; min-width: 180px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .summary-card .label {{ font-size: 0.875rem; color: #6b6b7b; text-transform: uppercase; letter-spacing: 0.05em; }}
        .summary-card .value {{ font-size: 1.75rem; font-weight: 700; color: #1a1a2e; margin-top: 4px; }}
        .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .section h2 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eaeaee; }}
        .section h3 {{ font-size: 1rem; font-weight: 600; margin: 20px 0 12px; color: #3d3d4d; }}
        .section h4 {{ font-size: 0.9375rem; font-weight: 600; margin: 16px 0 8px; color: #3d3d4d; }}
        .section h5 {{ font-size: 0.875rem; font-weight: 500; margin: 8px 0 4px; color: #6b6b7b; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px 12px; text-align: left; font-size: 0.875rem; }}
        th {{ font-weight: 600; color: #6b6b7b; border-bottom: 1px solid #eaeaee; }}
        td {{ border-bottom: 1px solid #f0f0f3; }}
        tr:last-child td {{ border-bottom: none; }}
        code {{ background: #f0f0f3; padding: 2px 6px; border-radius: 4px; font-size: 0.8125rem; }}
        .empty {{ color: #a0a0b0; font-style: italic; text-align: center; padding: 24px !important; }}
        .placeholder {{ color: #a0a0b0; font-style: italic; }}

        /* Status badges */
        .status-badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
.status-success {{ background: #dcfce7; color: #166534; }}
        .status-failure {{ background: #fee2e2; color: #991b1b; }}
        .status-mixed {{ background: #fef3c7; color: #92400e; }}

        .deploy-badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
        .deploy-deployed {{ background: #dcfce7; color: #166534; }}
        .deploy-failed {{ background: #fee2e2; color: #991b1b; }}
        .deploy-not_deployed {{ background: #e5e5eb; color: #525262; }}

        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 500; margin: 4px 8px 4px 0; }}
        .badge.warning {{ background: #fef3c7; color: #92400e; }}
        .badge.danger {{ background: #fee2e2; color: #991b1b; }}
        .badge.info {{ background: #dbeafe; color: #1e40af; }}

        .step-list {{ list-style: none; padding: 0; }}
        .step-list li {{ padding: 6px 10px; margin: 2px 0; border-radius: 4px; font-size: 0.8125rem; }}
        .step-list li.missing {{ background: #fee2e2; color: #991b1b; }}
        .step-list li.extra {{ background: #dbeafe; color: #1e40af; }}
        .step-list li.out-of-order {{ background: #fef3c7; color: #92400e; }}

        .diff-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 12px 0; }}
        .diff-col {{ background: #fafafa; border-radius: 8px; padding: 12px; }}
        .diff-summary {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}

        .summary-cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }}
        .card {{ background: #fafafa; border-radius: 8px; padding: 16px; min-width: 150px; flex: 1; }}
        .card .label {{ display: block; font-size: 0.75rem; color: #6b6b7b; text-transform: uppercase; }}
        .card .value {{ font-size: 1.5rem; font-weight: 700; color: #1a1a2e; margin-top: 4px; }}

        .trajectory-detail {{ margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #eaeaee; }}
        .trajectory-detail:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}

        @media (max-width: 768px) {{
            .diff-grid {{ grid-template-columns: 1fr; }}
            .summary-bar {{ flex-direction: column; }}
            .summary-card {{ min-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Faber Dashboard</h1>
            <p class="subtitle">Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • {total_runs} runs • ${total_cost:.4f} total cost • {avg_match:.1f}% avg trajectory match</p>
        </header>

        <div class="summary-bar">
            <div class="summary-card"><span class="label">Total Runs</span><span class="value">{total_runs}</span></div>
            <div class="summary-card"><span class="label">Total Cost</span><span class="value">${total_cost:.4f}</span></div>
            <div class="summary-card"><span class="label">Avg Traj. Match</span><span class="value">{avg_match:.1f}%</span></div>
            <div class="summary-card"><span class="label">Success Rate</span><span class="value">{summary.get('success_rate', 0):.1f}%</span></div>
        </div>

        <div class="section">
            <h2>Runs</h2>
            {runs_table}
        </div>

        <div class="section">
            <h2>Trajectory Conformance</h2>
            {trajectory_details or '<p class="placeholder">No trajectory data</p>'}
        </div>

        <div class="section">
            {cost_summary}
        </div>

        <div class="section">
            {model_routing}
        </div>

        <div class="section">
            {eval_scores}
        </div>

        <div class="section">
            {hitl_queue}
        </div>

        <div class="section">
            {scope_ledger}
        </div>
    </div>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dashboard — generate management dashboard from telemetry"
    )
    parser.add_argument(
        "--runs-dir",
        required=True,
        help="Path to runs/ directory containing telemetry.json files",
    )
    parser.add_argument(
        "--output-dir",
        default="dashboard",
        help="Output directory for index.html (default: dashboard/)",
    )

    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        print(json.dumps({"error": f"Runs directory not found: {runs_dir}"}))
        sys.exit(1)

    runs = load_all_telemetry(runs_dir)

    # Calculate summary
    total_cost = sum(r.get("cost", 0.0) for r in runs)
    matches = [calculate_trajectory_match(r) for r in runs]
    avg_match = sum(matches) / len(matches) if matches else 0.0
    success_count = sum(1 for r in runs if get_run_status(r) == "success")
    success_rate = (success_count / len(runs) * 100) if runs else 0.0

    summary = {
        "total_runs": len(runs),
        "total_cost": total_cost,
        "avg_trajectory_match": avg_match,
        "success_rate": success_rate,
    }

    # Generate HTML
    html = generate_html(runs, summary)

    # Write output
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html)

    # Emit summary JSON
    result = {
        "runs_processed": len(runs),
        "dashboard_path": str(output_path),
        "summary": summary,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()