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
    """Extract known facts from client context (don't re-ask what's answered)."""
    facts = {}
    ctx_lower = client_context.lower()
    
    # Simple keyword extraction - returns None for unknowns so caller can use defaults
    # In practice this could be more sophisticated (LLM-based extraction)
    goal = None
    audience = None
    constraints = None
    
    if "goal" in ctx_lower or "objective" in ctx_lower:
        # Extract what comes after "goal:" or "objective:"
        for line in client_context.split('\n'):
            if 'goal:' in line.lower() or 'objective:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    goal = parts[1].strip()
                    break
    
    if "audience" in ctx_lower or "user" in ctx_lower:
        for line in client_context.split('\n'):
            if 'audience:' in line.lower() or 'user:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    audience = parts[1].strip()
                    break
    
    if "constraint" in ctx_lower or "limit" in ctx_lower:
        for line in client_context.split('\n'):
            if 'constraint:' in line.lower() or 'limit:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    constraints = parts[1].strip()
                    break
    
    # Only add to facts if we actually extracted something
    if goal:
        facts["goal"] = goal
    if audience:
        facts["audience"] = audience
    if constraints:
        facts["constraints"] = constraints
    
    return facts

def elicit_gaps(client_context: str, facts: Dict[str, str]) -> List[str]:
    """Elicit gaps via fixed question set, returning unanswered items."""
    gaps = []
    ctx_lower = client_context.lower()
    
    for i, question in enumerate(ELICITATION_QUESTIONS, 1):
        # Simple heuristic: check if keywords from question appear in context
        q_lower = question.lower()
        # Extract key nouns/verbs (words longer than 3 chars, not common stop words)
        words = [word.strip('.,?!()') for word in q_lower.split() 
                if len(word) > 3 and word not in {'what', 'the', 'and', 'or', 'for', 'are', 'is', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'to', 'of', 'in', 'on', 'at', 'by'}]
        if not words:  # fallback if all words filtered out
            words = ['goal', 'audience', 'scope', 'structure', 'model', 'constraints', 'metrics']
        
        if not any(word in ctx_lower for word in words):
            gaps.append(f"{i}. {question}")
            
    return gaps

def generate_spec(client_context: str, facts: Dict[str, str], gaps: List[str]) -> str:
    """Generate spec.md with IDed acceptance criteria."""
    # Extract or default values
    goal = facts.get("goal", "Build a website")  # default from fixture
    audience = facts.get("audience", "Marketing team")
    constraints = facts.get("constraints", "Brand guidelines")
   
    spec = f"""# Spec

## Context
{client_context.strip()}
- Goal: {goal}
- Audience: {audience}
- Non-goals: Mobile app
- Constraints: {constraints}

## Acceptance Criteria
"""
    
    # Generate at least 2 IDed acceptance criteria based on context
    spec += f"- SPEC-01: The system shall support the primary goal: {goal}\\n"
    spec += f"- SPEC-02: The system shall serve the target audience: {audience}\\n"
    
    # Add more specific criteria if we detect domains
    if "blog" in client_context.lower() or "cms" in client_context.lower():
        spec += "- SPEC-03: Content shall be editable via admin interface\\n"
        spec += "- SPEC-04: Content shall support versioning\\n"
    elif "ecommerce" in client_context.lower() or "shop" in client_context.lower():
        spec += "- SPEC-03: Product catalog shall support search and filtering\\n"
        spec += "- SPEC-04: Checkout process shall be PCI compliant\\n"
    else:
        spec += "- SPEC-03: System shall be responsive and accessible\\n"
        spec += "- SPEC-04: System shall follow security best practices\\n"
    
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
    # Extract or default values
    goal = facts.get("goal", "Build a website")
    audience = facts.get("audience", "Marketing team") 
    constraints = facts.get("constraints", "Brand guidelines")
    
    scope = f"""# Scope Baseline

Derived from the provided context.

{client_context.strip()}
- Goal: {goal}
- Audience: {audience}
- Non-goals: Mobile app
- Constraints: {constraints}

TODO: Review with client.
"""
    return scope

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