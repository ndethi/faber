#!/usr/bin/env python3
"""
Intent-Collect Skill - Deterministic front door of Faber lifecycle.

Implements structured elicitation: extract → elicit → spec → trajectory → 
scope-baseline → [HITL] confirm.

Produces:
- spec.md - Source of truth with IDed acceptance criteria
- trajectory.md - Expected path (ordered DAG of lifecycle steps)
- scope-baseline.md - Client-shareable scope baseline
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Fixed question set for elicitation (per FRAMEWORK.md §3)
ELICITATION_QUESTIONS = [
    "What is the primary goal or outcome desired?",
    "Who are the primary audiences/users and their jobs-to-be-done?",
    "What is explicitly out of scope (non-goals)?",
    "What information architecture or content structure is needed?",
    "What is the content model (types, fields, relationships)?",
    "What constraints exist (brand, legal, technical, temporal)?",
    "What are the success metrics or acceptance criteria?",
]

# Labels that identify each field in a brief, in ELICITATION_QUESTIONS order
FIELD_LABELS = {
    "goal": ["goal", "goals", "objective", "objectives"],
    "audience": ["audience", "audiences", "users", "user"],
    "non_goals": ["non-goals", "non-goal", "non goals", "out of scope"],
    "information_architecture": ["pages", "sitemap", "information architecture"],
    "content_model": ["content model"],
    "constraints": ["constraints", "constraint", "limits", "limit"],
    "success_metrics": ["success metrics", "metrics", "success criteria", "acceptance criteria"],
}

UNKNOWN = "TODO: not stated in client context"

LABEL_TO_FIELD = {
    label: field for field, labels in FIELD_LABELS.items() for label in labels
}
# Longest first, so "non-goals" is never read as "goals"
LABEL_RE = re.compile(
    r"(?<![\w-])("
    + "|".join(re.escape(l) for l in sorted(LABEL_TO_FIELD, key=len, reverse=True))
    + r")\s*:",
    re.IGNORECASE,
)
# A value also ends at a blank line, a heading, or a line with some other label
VALUE_BREAK_RE = re.compile(r"\n\s*\n|\n\s*#|\n\s*[-*]?\s*[A-Z][\w /-]{0,30}:")

# Lifecycle stages in order (per FRAMEWORK.md §2)
LIFECYCLE_STAGES = [
    "intent-collect",
    "scaffold", 
    "build",
    "evaluate",
    "deploy",
    "publish",
    "observe",
    "feedback"
]

# Checkpoints/gates that can appear in trajectory
CHECKPOINTS = ["HITL confirmation", "spec review", "trajectory review"]

def extract_facts(client_context: str) -> Dict[str, str]:
    """Extract labelled facts from client context; unlabelled fields stay absent."""
    facts: Dict[str, str] = {}
    matches = list(LABEL_RE.finditer(client_context))

    for i, match in enumerate(matches):
        value_end = matches[i + 1].start() if i + 1 < len(matches) else len(client_context)
        value = client_context[match.end():value_end]
        value_break = VALUE_BREAK_RE.search(value)
        if value_break:
            value = value[:value_break.start()]
        value = value.strip(" \t\r\n-*.;,")
        if value and not value.lower().startswith("todo"):
            facts.setdefault(LABEL_TO_FIELD[match.group(1).lower()], value)

    return facts

def elicit_gaps(client_context: str, facts: Dict[str, str]) -> List[str]:
    """Return each fixed question whose field was not found in the context."""
    return [
        f"{i}. {question}"
        for i, (field, question) in enumerate(zip(FIELD_LABELS, ELICITATION_QUESTIONS), 1)
        if field not in facts
    ]

def split_items(value: str, split_commas: bool = False) -> List[str]:
    """Split a stated value into list items, dropping bullets and punctuation."""
    pattern = r"[;,\n]" if split_commas else r"[;\n]"
    items = (item.strip(" \t\r-*.") for item in re.split(pattern, value))
    return [re.sub(r"^and\s+", "", item, flags=re.IGNORECASE) for item in items if item]

def generate_criteria(facts: Dict[str, str]) -> List[str]:
    """Build acceptance criteria only from what the client actually stated."""
    criteria = [
        f"The system shall support the primary goal: {facts.get('goal', UNKNOWN)}",
        f"The system shall serve the target audience: {facts.get('audience', UNKNOWN)}",
    ]
    if "information_architecture" in facts:
        criteria += [
            f"The site shall include the page: {page}"
            for page in split_items(facts["information_architecture"], split_commas=True)
        ]
    if "constraints" in facts:
        criteria += [
            f"The system shall meet the constraint: {constraint}"
            for constraint in split_items(facts["constraints"])
        ]
    if "success_metrics" in facts:
        criteria += [
            f"The system shall meet the success measure: {metric}"
            for metric in split_items(facts["success_metrics"])
        ]
    return [f"- SPEC-{i:02d}: {criterion}" for i, criterion in enumerate(criteria, 1)]

def render_context(client_context: str, facts: Dict[str, str]) -> str:
    """Render the brief followed by the fields read from it."""
    return f"""{client_context.strip()}
- Goal: {facts.get("goal", UNKNOWN)}
- Audience: {facts.get("audience", UNKNOWN)}
- Non-goals: {facts.get("non_goals", UNKNOWN)}
- Constraints: {facts.get("constraints", UNKNOWN)}"""

def generate_spec(client_context: str, facts: Dict[str, str], gaps: List[str]) -> str:
    """Generate spec.md with IDed acceptance criteria."""
    spec = f"""# Spec

## Context
{render_context(client_context, facts)}

## Acceptance Criteria
"""
    spec += "\n".join(generate_criteria(facts)) + "\n"

    # Surface gaps as TODO items (per non-fabrication rule)
    if gaps:
        spec += "\n## TODO (Elicited Gaps)\n"
        for gap in gaps:
            spec += f"- TODO: {gap}\n"

    return spec

def generate_trajectory(production_context: str) -> str:
    """Generate trajectory.md with ordered DAG of lifecycle steps."""
    # Map production_context to strictness (per FRAMEWORK.md §4)
    strictness_map = {
        "prototype": "partial",
        "normal": "ordered", 
        "client-production": "exact"
    }
    strictness = strictness_map.get(production_context.lower(), "ordered")
    
    # Build trajectory: core lifecycle + checkpoints
    trajectory_steps = []
    
    # Add lifecycle steps
    for stage in LIFECYCLE_STAGES:
        trajectory_steps.append(f"{len(trajectory_steps)+1}. {stage}")
        
    # Add checkpoints/gates (simplified - in reality these would be contextual)
    if "HITL" not in "\n".join(trajectory_steps):
        trajectory_steps.append(f"{len(trajectory_steps)+1}. HITL confirmation")
        
    trajectory = f"""# Trajectory (strictness: {strictness})

{chr(10).join(trajectory_steps)}
"""
    return trajectory

def generate_scope_baseline(client_context: str, facts: Dict[str, str]) -> str:
    """Generate scope-baseline.md - plain language, client-shareable."""
    return f"""# Scope Baseline

Derived from the provided context.

{render_context(client_context, facts)}

TODO: Review with client.
"""

def write_files(spec: str, trajectory: str, scope: str, output_dir: str = ".") -> None:
    """Write the three output files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    (output_path / "spec.md").write_text(spec)
    (output_path / "trajectory.md").write_text(trajectory)
    (output_path / "scope-baseline.md").write_text(scope)

def main() -> None:
    """Main entry point for intent-collect skill."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Intent-collect: deterministic front door of Faber lifecycle"
    )
    parser.add_argument(
        "--client-context", 
        required=True,
        help="Client conversation, brief, or distilled context"
    )
    parser.add_argument(
        "--production-context",
        required=True, 
        choices=["prototype", "normal", "client-production"],
        help="Production context: sets default strictness for trajectory"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write output files (default: current)"
    )
    parser.add_argument(
        "--hitl-gate",
        action="store_true",
        help="Enable HITL gate (requires manual confirmation of scope-baseline)"
    )
    
    args = parser.parse_args()
    
    # Process: extract → elicit → spec → elicit → spec → trajectory → scope-baseline
    facts = extract_facts(args.client_context)
    gaps = elicit_gaps(args.client_context, facts)
    
    spec = generate_spec(args.client_context, facts, gaps)
    trajectory = generate_trajectory(args.production_context)
    scope = generate_scope_baseline(args.client_context, facts)
    
    # HITL gate: if enabled, require manual confirmation of scope-baseline
    hitl_gate_passed = True
    if args.hitl_gate:
        print("\n=== HITL GATE: Scope Baseline Review Required ===")
        print("Generated scope-baseline.md:")
        print("-" * 60)
        print(scope)
        print("-" * 60)
        print("Do you confirm this scope baseline? [y/N]: ", end="", flush=True)
        try:
            response = input().strip().lower()
            if response not in ('y', 'yes'):
                hitl_gate_passed = False
                print("HITL gate not passed. Exiting without writing files.")
            else:
                print("HITL gate passed. Proceeding...")
        except (EOFError, KeyboardInterrupt):
            hitl_gate_passed = False
            print("\nHITL gate interrupted. Exiting without writing files.")
    
    if not hitl_gate_passed:
        result = {
            "status": "hitl_gate_failed",
            "artifacts": [],
            "hitl_gate_required": True,
            "hitl_gate_passed": False,
            "extracted_facts": facts,
            "elicited_gaps": gaps,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    write_files(spec, trajectory, scope, args.output_dir)
    
    # Emit machine-readable summary for orchestration
    result = {
        "status": "success",
        "artifacts": ["spec.md", "trajectory.md", "scope-baseline.md"],
        "hitl_gate_required": args.hitl_gate,
        "hitl_gate_passed": True,
        "extracted_facts": facts,
        "elicited_gaps": gaps,
        "spec_lines": len(spec.splitlines()),
        "trajectory_lines": len(trajectory.splitlines()),
        "scope_lines": len(scope.splitlines())
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()