#!/usr/bin/env python3
"""
Trajectory Guard — Diffs actual vs expected trajectory.

Implements FRAMEWORK.md §4: process-level drift control.
Compares actual trajectory (from telemetry) against expected trajectory
(strictness: exact | ordered | partial).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_telemetry(path: Path) -> Dict[str, Any]:
    """Load and validate telemetry JSON."""
    with open(path, "r") as f:
        return json.load(f)


def normalize_step(step: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Normalize a step to have consistent keys for comparison."""
    return {
        "skill_id": step.get("skill_id", ""),
        "checkpoint": step.get("checkpoint", step.get("skill_id", "")),
        "gate": step.get("gate", False),
        "index": index,
    }


def compare_exact(expected: List[Dict], actual: List[Dict]) -> Dict[str, Any]:
    """Exact match: actual must equal expected in order and content."""
    expected_norm = [normalize_step(s, i) for i, s in enumerate(expected)]
    actual_norm = [normalize_step(s, i) for i, s in enumerate(actual)]

    missing = [s for s in expected_norm if not any(a["skill_id"] == s["skill_id"] for a in actual_norm)]
    extra = [s for s in actual_norm if not any(e["skill_id"] == s["skill_id"] for e in expected_norm)]

    out_of_order = []
    for i, exp in enumerate(expected_norm):
        if i < len(actual_norm) and actual_norm[i]["skill_id"] != exp["skill_id"]:
            out_of_order.append(exp["skill_id"])

    gate_violations = [
        s["skill_id"] for s in expected_norm if s["gate"]
        and not any(a["skill_id"] == s["skill_id"] for a in actual_norm)
    ]

    match_percent = 100.0 if not missing and not extra and not out_of_order else 0.0
    status = "pass" if match_percent == 100.0 else "fail"

    return {
        "match_percent": match_percent,
        "status": status,
        "missing": [s["skill_id"] for s in missing],
        "extra": [s["skill_id"] for s in extra],
        "out_of_order": out_of_order,
        "gate_violations": gate_violations,
    }


def compare_ordered(expected: List[Dict], actual: List[Dict]) -> Dict[str, Any]:
    """Ordered match: expected steps must appear in order; extras allowed."""
    expected_norm = [normalize_step(s, i) for i, s in enumerate(expected)]
    actual_norm = [normalize_step(s, i) for i, s in enumerate(actual)]

    # Find expected steps in actual (in order)
    matched = []
    actual_idx = 0
    for exp in expected_norm:
        found = False
        while actual_idx < len(actual_norm):
            if actual_norm[actual_idx]["skill_id"] == exp["skill_id"]:
                matched.append(exp["skill_id"])
                actual_idx += 1
                found = True
                break
            actual_idx += 1
        if not found:
            matched.append(None)  # placeholder for missing

    missing = [exp["skill_id"] for exp in expected_norm if exp["skill_id"] not in [m for m in matched if m]]
    extra = [a["skill_id"] for a in actual_norm if a["skill_id"] not in [e["skill_id"] for e in expected_norm]]

    # Check order: expected steps that ARE present must be in correct relative order
    present_expected = [e["skill_id"] for e in expected_norm if e["skill_id"] in [a["skill_id"] for a in actual_norm]]
    present_actual = [a["skill_id"] for a in actual_norm if a["skill_id"] in [e["skill_id"] for e in expected_norm]]
    out_of_order = []
    if present_expected != present_actual:
        # Find which expected steps are out of order
        for i, (e, a) in enumerate(zip(present_expected, present_actual)):
            if e != a:
                out_of_order.append(e)

    gate_violations = [
        s["skill_id"] for s in expected_norm if s["gate"]
        and not any(a["skill_id"] == s["skill_id"] for a in actual_norm)
    ]

    matched_count = sum(1 for m in matched if m is not None)
    match_percent = (matched_count / len(expected_norm) * 100) if expected_norm else 100.0
    status = "pass" if match_percent == 100.0 and not gate_violations else "warning"

    return {
        "match_percent": round(match_percent, 1),
        "status": status,
        "missing": missing,
        "extra": extra,
        "out_of_order": out_of_order,
        "gate_violations": gate_violations,
    }


def compare_partial(expected: List[Dict], actual: List[Dict]) -> Dict[str, Any]:
    """Partial match: expected checkpoints must be hit; order free."""
    expected_norm = [normalize_step(s, i) for i, s in enumerate(expected)]
    actual_norm = [normalize_step(s, i) for i, s in enumerate(actual)]

    expected_skill_ids = {s["skill_id"] for s in expected_norm}
    actual_skill_ids = {s["skill_id"] for s in actual_norm}

    missing = list(expected_skill_ids - actual_skill_ids)
    extra = list(actual_skill_ids - expected_skill_ids)

    # Gate violations: required gates not hit
    gate_skill_ids = {s["skill_id"] for s in expected_norm if s["gate"]}
    gate_violations = list(gate_skill_ids - actual_skill_ids)

    # No out-of-order check for partial mode
    out_of_order = []

    hit_count = len(expected_skill_ids & actual_skill_ids)
    match_percent = (hit_count / len(expected_skill_ids) * 100) if expected_skill_ids else 100.0
    status = "pass" if match_percent == 100.0 and not gate_violations else "warning"

    return {
        "match_percent": round(match_percent, 1),
        "status": status,
        "missing": missing,
        "extra": extra,
        "out_of_order": out_of_order,
        "gate_violations": gate_violations,
    }


def run_guard(
    telemetry: Dict[str, Any],
    strictness_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Main trajectory guard logic."""
    expected = telemetry.get("expected_trajectory", [])
    actual = telemetry.get("skills", [])
    strictness = strictness_override or telemetry.get("trajectory_strictness", "ordered")

    # Run appropriate comparison
    if strictness == "exact":
        details = compare_exact(expected, actual)
    elif strictness == "ordered":
        details = compare_ordered(expected, actual)
    elif strictness == "partial":
        details = compare_partial(expected, actual)
    else:
        raise ValueError(f"Unknown strictness: {strictness}")

    # Determine exit code
    if details["status"] == "fail":
        exit_code = 1
    elif details["status"] == "warning":
        exit_code = 2
    else:
        exit_code = 0

    report = {
        "run_id": telemetry.get("run_id", "unknown"),
        "strictness": strictness,
        "match_percent": details["match_percent"],
        "status": details["status"],
        "exit_code": exit_code,
        "details": {
            "expected_steps": [normalize_step(s, i) for i, s in enumerate(expected)],
            "actual_steps": [normalize_step(s, i) for i, s in enumerate(actual)],
            "missing": details["missing"],
            "extra": details["extra"],
            "out_of_order": details["out_of_order"],
            "gate_violations": details["gate_violations"],
        },
    }

    return report, exit_code


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trajectory Guard — diff actual vs expected trajectory"
    )
    parser.add_argument(
        "--telemetry-path",
        required=True,
        help="Path to telemetry.json (e.g., runs/<run_id>/telemetry.json)",
    )
    parser.add_argument(
        "--strictness",
        choices=["exact", "ordered", "partial"],
        help="Override strictness mode (default: from telemetry)",
    )
    parser.add_argument(
        "--output",
        help="Write report to file (default: stdout only)",
    )

    args = parser.parse_args()

    telemetry_path = Path(args.telemetry_path)
    if not telemetry_path.exists():
        print(json.dumps({"error": f"Telemetry file not found: {telemetry_path}"}))
        sys.exit(1)

    telemetry = load_telemetry(telemetry_path)

    report, exit_code = run_guard(telemetry, args.strictness)

    # Write to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2))

    # Always print to stdout for orchestration
    print(json.dumps(report, indent=2))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()