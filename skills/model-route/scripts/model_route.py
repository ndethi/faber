#!/usr/bin/env python3
"""
Model Route — Routes skill steps to local or frontier model.

Implements FRAMEWORK.md §8: cost layer with continuous local-vs-frontier evals
that gate graduation from frontier to local.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_POLICY = {
    "default": "frontier",
    "skills": {
        "intent-collect": "local",
        "build": "local",
        "evaluate": "frontier",
        "scaffold": "local",
        "deploy": "local",
        "publish": "local",
        "observe": "local",
        "feedback": "frontier",
    },
    "graduation_thresholds": {
        "min_samples": 10,
        "quality_threshold": 0.95,
        "cost_savings_min": 0.5,
    },
    "eval_history": [],
    "local_endpoint": "http://localhost:8000/v1",
    "local_model": "gpt-oss-120b",
    "frontier_endpoint": "https://api.openai.com/v1",
    "frontier_model": "gpt-4o",
}


def load_policy(policy_path: Path) -> Dict[str, Any]:
    """Load routing policy, creating default if not exists."""
    if policy_path.exists():
        with open(policy_path, "r") as f:
            policy = json.load(f)
            # Merge with defaults for any missing keys
            for key, value in DEFAULT_POLICY.items():
                if key not in policy:
                    policy[key] = value
            return policy
    else:
        # Create default policy
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        with open(policy_path, "w") as f:
            json.dump(DEFAULT_POLICY, f, indent=2)
        return DEFAULT_POLICY.copy()


def save_policy(policy: Dict[str, Any], policy_path: Path) -> None:
    """Save routing policy."""
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    with open(policy_path, "w") as f:
        json.dump(policy, f, indent=2)


def route_skill(
    skill_id: str,
    component: str = "",
    context: str = "",
    policy: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Determine model route for a skill step."""
    if policy is None:
        policy = DEFAULT_POLICY

    # Check skill-specific routing
    skill_route = policy.get("skills", {}).get(skill_id)
    if skill_route:
        route = skill_route
        reason = f"Skill '{skill_id}' explicitly routed to {route} in policy"
    else:
        route = policy.get("default", "frontier")
        reason = f"Skill '{skill_id}' not in policy, using default: {route}"

    # Context-based override (simple heuristic)
    if context:
        context_lower = context.lower()
        if any(kw in context_lower for kw in ["extract", "parse", "format", "validate", "lint", "format"]):
            if route == "frontier":
                route = "local"
                reason += "; context suggests routine task, downgraded to local"
        elif any(kw in context_lower for kw in ["design", "architecture", "complex", "reasoning", "creative"]):
            if route == "local":
                route = "frontier"
                reason += "; context suggests complex reasoning, upgraded to frontier"

    # Get endpoint and model name
    if route == "local":
        endpoint = policy.get("local_endpoint", DEFAULT_POLICY["local_endpoint"])
        model_name = policy.get("local_model", DEFAULT_POLICY["local_model"])
        estimated_cost = 0.0  # Local is free
    else:
        endpoint = policy.get("frontier_endpoint", DEFAULT_POLICY["frontier_endpoint"])
        model_name = policy.get("frontier_model", DEFAULT_POLICY["frontier_model"])
        # Rough estimate: $0.005 per 1k tokens
        estimated_cost = 0.005

    return {
        "model": route,
        "endpoint": endpoint,
        "model_name": model_name,
        "reason": reason,
        "estimated_cost_usd": estimated_cost,
    }


def record_eval_result(
    policy: Dict[str, Any],
    skill_id: str,
    local_quality: float,
    frontier_quality: float,
    local_cost: float,
    frontier_cost: float,
) -> None:
    """Record eval comparison result for graduation tracking."""
    history = policy.setdefault("eval_history", [])
    history.append({
        "skill_id": skill_id,
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "local_quality": local_quality,
        "frontier_quality": frontier_quality,
        "local_cost": local_cost,
        "frontier_cost": frontier_cost,
        "quality_ratio": local_quality / frontier_quality if frontier_quality > 0 else 0,
        "cost_savings": (frontier_cost - local_cost) / frontier_cost if frontier_cost > 0 else 0,
    })
    # Keep last 100 entries
    if len(history) > 100:
        policy["eval_history"] = history[-100:]


def check_graduation(policy: Dict[str, Any], skill_id: str) -> Dict[str, Any]:
    """Check if a skill should graduate from frontier to local."""
    history = [h for h in policy.get("eval_history", []) if h["skill_id"] == skill_id]
    thresholds = policy.get("graduation_thresholds", DEFAULT_POLICY["graduation_thresholds"])

    if len(history) < thresholds.get("min_samples", 10):
        return {
            "should_graduate": False,
            "reason": f"Insufficient samples: {len(history)}/{thresholds['min_samples']}",
            "samples": len(history),
        }

    # Calculate averages over recent samples
    recent = history[-thresholds["min_samples"]:]
    avg_quality_ratio = sum(h["quality_ratio"] for h in recent) / len(recent)
    avg_cost_savings = sum(h["cost_savings"] for h in recent) / len(recent)

    quality_threshold = thresholds.get("quality_threshold", 0.95)
    cost_savings_min = thresholds.get("cost_savings_min", 0.5)

    should_graduate = (
        avg_quality_ratio >= quality_threshold
        and avg_cost_savings >= cost_savings_min
    )

    return {
        "should_graduate": should_graduate,
        "reason": (
            f"Quality ratio: {avg_quality_ratio:.3f} (threshold: {quality_threshold}), "
            f"Cost savings: {avg_cost_savings:.3f} (min: {cost_savings_min})"
        ),
        "samples": len(history),
        "avg_quality_ratio": avg_quality_ratio,
        "avg_cost_savings": avg_cost_savings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Model Route — route skill steps to local or frontier model"
    )
    parser.add_argument(
        "--skill-id",
        required=True,
        help="Skill to route (e.g., intent-collect, build, evaluate)",
    )
    parser.add_argument(
        "--component",
        default="",
        help="Component within skill (optional)",
    )
    parser.add_argument(
        "--context",
        default="",
        help="Additional context for routing decision (optional)",
    )
    parser.add_argument(
        "--policy-path",
        default="runs/model-route/policy.json",
        help="Path to routing policy JSON (default: runs/model-route/policy.json)",
    )
    parser.add_argument(
        "--record-eval",
        action="store_true",
        help="Record eval comparison result (requires --local-quality, --frontier-quality, --local-cost, --frontier-cost)",
    )
    parser.add_argument(
        "--local-quality",
        type=float,
        help="Local model quality score (0-1) for --record-eval",
    )
    parser.add_argument(
        "--frontier-quality",
        type=float,
        help="Frontier model quality score (0-1) for --record-eval",
    )
    parser.add_argument(
        "--local-cost",
        type=float,
        help="Local model cost for --record-eval",
    )
    parser.add_argument(
        "--frontier-cost",
        type=float,
        help="Frontier model cost for --record-eval",
    )
    parser.add_argument(
        "--check-graduation",
        action="store_true",
        help="Check graduation status for skill",
    )

    args = parser.parse_args()

    policy_path = Path(args.policy_path)
    policy = load_policy(policy_path)

    if args.record_eval:
        if None in (args.local_quality, args.frontier_quality, args.local_cost, args.frontier_cost):
            print(json.dumps({"error": "--record-eval requires --local-quality, --frontier-quality, --local-cost, --frontier-cost"}))
            sys.exit(1)
        record_eval_result(
            policy,
            args.skill_id,
            args.local_quality,
            args.frontier_quality,
            args.local_cost,
            args.frontier_cost,
        )
        save_policy(policy, policy_path)
        print(json.dumps({"status": "recorded", "skill_id": args.skill_id}))
        return

    if args.check_graduation:
        result = check_graduation(policy, args.skill_id)
        print(json.dumps(result, indent=2))
        return

    # Normal routing
    decision = route_skill(args.skill_id, args.component, args.context, policy)
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()