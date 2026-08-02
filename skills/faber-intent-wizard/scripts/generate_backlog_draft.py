#!/usr/bin/env python3
"""
Faber Intent Wizard - Backlog Draft Generator

Generates a script that creates GitHub issue-ready backlog items from submitted intent.
"""

from typing import Any, Dict


def generate_backlog_draft_script(config: Dict[str, Any]) -> str:
    """Generate the backlog draft generation script."""
    project_name = config["project_name"]
    fixture = config.get("fixture", "faber-brand")

    # This is a template that generates a Python script
    # The inner script uses {{ }} for its own template placeholders
    # We need to escape braces for the outer f-string
    inner_script = """#!/usr/bin/env python3
\"\"\"
Backlog Draft Generator - Faber Intent Wizard

Generates GitHub issue-ready backlog markdown from intent submission data.
Can be run standalone or imported.
\"\"\"

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract_facts(client_context: str) -> Dict[str, str]:
    \"\"\"Extract known facts from client context (mirrors intent-collect logic).\"\"\"
    facts = {}
    ctx_lower = client_context.lower()

    goal = None
    audience = None
    constraints = None

    if "goal" in ctx_lower or "objective" in ctx_lower:
        for line in client_context.split('\\n'):
            if 'goal:' in line.lower() or 'objective:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    goal = parts[1].strip()
                    break

    if "audience" in ctx_lower or "user" in ctx_lower:
        for line in client_context.split('\\n'):
            if 'audience:' in line.lower() or 'user:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    audience = parts[1].strip()
                    break

    if "constraint" in ctx_lower or "limit" in ctx_lower:
        for line in client_context.split('\\n'):
            if 'constraint:' in line.lower() or 'limit:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    constraints = parts[1].strip()
                    break

    if goal:
        facts["goal"] = goal
    if audience:
        facts["audience"] = audience
    if constraints:
        facts["constraints"] = constraints

    return facts


def elicit_gaps(client_context: str, facts: Dict[str, str]) -> List[str]:
    \"\"\"Elicit gaps via fixed question set (mirrors intent-collect logic).\"\"\"
    gaps = []
    ctx_lower = client_context.lower()

    ELICITATION_QUESTIONS = [
        "What is the primary goal or outcome desired?",
        "Who are the primary audiences/users and their jobs-to-be-done?",
        "What is explicitly out of scope (non-goals)?",
        "What information architecture or content structure is needed?",
        "What is the content model (types, fields, relationships)?",
        "What constraints exist (brand, legal, technical, temporal)?",
        "What are the success metrics or acceptance criteria?",
    ]

    for i, question in enumerate(ELICITATION_QUESTIONS, 1):
        q_lower = question.lower()
        words = [word.strip('.,?!()') for word in q_lower.split()
                if len(word) > 3 and word not in {'what', 'the', 'and', 'or', 'for', 'are', 'is', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'to', 'of', 'in', 'on', 'at', 'by'}]
        if not words:
            words = ['goal', 'audience', 'scope', 'structure', 'model', 'constraints', 'metrics']

        if not any(word in ctx_lower for word in words):
            gaps.append(f"{i}. {question}")

    return gaps


def generate_spec(client_context: str, facts: Dict[str, str], gaps: List[str]) -> str:
    \"\"\"Generate spec.md with IDed acceptance criteria (mirrors intent-collect logic).\"\"\"
    goal = facts.get("goal", "Build a website")
    audience = facts.get("audience", "Target audience")
    constraints = facts.get("constraints", "Brand guidelines")

    spec = f\"\"\"# Spec

## Context
{client_context.strip()}
- Goal: {goal}
- Audience: {audience}
- Non-goals: None specified
- Constraints: {constraints}

## Acceptance Criteria

- SPEC-01: The system shall support the primary goal: {goal}
- SPEC-02: The system shall serve the target audience: {audience}
\"\"\"

    if "blog" in client_context.lower() or "cms" in client_context.lower():
        spec += "- SPEC-03: Content shall be editable via admin interface\\n"
        spec += "- SPEC-04: Content shall support versioning\\n"
    elif "ecommerce" in client_context.lower() or "shop" in client_context.lower():
        spec += "- SPEC-03: Product catalog shall support search and filtering\\n"
        spec += "- SPEC-04: Checkout process shall be PCI compliant\\n"
    else:
        spec += "- SPEC-03: System shall be responsive and accessible\\n"
        spec += "- SPEC-04: System shall follow security best practices\\n"

    if gaps:
        spec += "\\n## TODO (Elicited Gaps)\\n"
        for gap in gaps:
            spec += f"- TODO: {gap}\\n"

    return spec


def generate_trajectory(production_context: str = "normal") -> str:
    \"\"\"Generate trajectory.md with ordered DAG of lifecycle steps.\"\"\"
    strictness_map = {
        "prototype": "partial",
        "normal": "ordered",
        "client-production": "exact"
    }
    strictness = strictness_map.get(production_context.lower(), "ordered")

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

    trajectory_steps = []
    for stage in LIFECYCLE_STAGES:
        trajectory_steps.append(f"{len(trajectory_steps)+1}. {stage}")

    if "HITL" not in "\\n".join(trajectory_steps):
        trajectory_steps.append(f"{len(trajectory_steps)+1}. HITL confirmation")

    trajectory = f\"\"\"# Trajectory (strictness: {strictness})

{chr(10).join(trajectory_steps)}
\"\"\"
    return trajectory


def generate_scope_baseline(client_context: str, facts: Dict[str, str]) -> str:
    \"\"\"Generate scope-baseline.md - plain language, client-shareable.\"\"\"
    goal = facts.get("goal", "Build a website")
    audience = facts.get("audience", "Target audience")
    constraints = facts.get("constraints", "Brand guidelines")

    scope = f\"\"\"# Scope Baseline

Derived from the provided context.

{client_context.strip()}
- Goal: {goal}
- Audience: {audience}
- Non-goals: None specified
- Constraints: {constraints}

TODO: Review with client.
\"\"\"
    return scope


def generate_backlog_draft(
    client_context: str,
    facts: Dict[str, str],
    spec: str,
    fixture: str = "{fixture}"
) -> str:
    \"\"\"Generate GitHub issue-ready backlog draft markdown.\"\"\"
    goal = facts.get("goal", "Build a website")

    # Extract SPEC items from spec
    spec_lines = spec.split("\\n")
    spec_items = [line.strip() for line in spec_lines if line.strip().startswith("- SPEC-")]

    # Extract TODO items from spec
    todo_items = [line.strip() for line in spec_lines if line.strip().startswith("- TODO:")]

    backlog = f\"\"\"# Backlog Draft — Generated from Intent

*Auto-generated from intent submission by {project_name}. Review and refine before adding to project backlog.*

## Epic: {goal}

### Functional Requirements
- [ ] Implement core functionality for: {goal}
- [ ] Support target audience: {facts.get('audience', 'TBD')}
- [ ] Meet constraints: {facts.get('constraints', 'TBD')}

### Technical Requirements
- [ ] Astro + Cloudflare Pages setup
- [ ] D1 database schema for content
- [ ] CI/CD pipeline (lint → test → deploy-preview → deploy-staging → deploy-production)
- [ ] Design system integration ({fixture} fixture)

### Acceptance Criteria (from spec)
\"\"\"

    for item in spec_items:
        # Convert "- SPEC-01: description" to "- [ ] SPEC-01: description"
        backlog += f"- [ ] {item[2:]}\\n"

    backlog += "\\n### Open Questions (from elicited gaps)\\n"

    if todo_items:
        for item in todo_items:
            backlog += f"- [ ] {item[8:]}\\n"  # Remove "- TODO: "
    else:
        backlog += "- [ ] No elicited gaps\\n"

    backlog += f\"\"\"
---
*Generated by Faber Intent Wizard ({fixture} fixture) on {{__import__('datetime').datetime.now().isoformat()}}*
\"\"\"

    return backlog


def main() -> None:
    \"\"\"Main entry point - can be used as CLI or imported.\"\"\"
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate backlog draft from intent submission"
    )
    parser.add_argument(
        "--client-context",
        required=True,
        help="Client context string (from intent submission)"
    )
    parser.add_argument(
        "--production-context",
        default="normal",
        choices=["prototype", "normal", "client-production"],
        help="Production context"
    )
    parser.add_argument(
        "--fixture",
        default="{fixture}",
        help="Design system fixture"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON with all artifacts"
    )

    args = parser.parse_args()

    # Process through intent-collect pipeline
    facts = extract_facts(args.client_context)
    gaps = elicit_gaps(args.client_context, facts)
    spec = generate_spec(args.client_context, facts, gaps)
    trajectory = generate_trajectory(args.production_context)
    scope_baseline = generate_scope_baseline(args.client_context, facts)
    backlog = generate_backlog_draft(args.client_context, facts, spec, args.fixture)

    if args.json:
        result = {
            "spec_md": spec,
            "trajectory_md": trajectory,
            "scope_baseline_md": scope_baseline,
            "backlog_draft_md": backlog,
            "extracted_facts": facts,
            "elicited_gaps": gaps,
        }
        output = json.dumps(result, indent=2)
    else:
        output = backlog

    if args.output:
        Path(args.output).write_text(output)
        print(f"Backlog draft written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
"""

    # Now substitute the template variables
    return inner_script.format(project_name=project_name, fixture=fixture)


if __name__ == "__main__":
    # When run directly, execute the script logic
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Generate backlog draft from intent submission"
    )
    parser.add_argument(
        "--client-context",
        required=False,
        help="Client context string (from intent submission)"
    )
    parser.add_argument(
        "--production-context",
        default="normal",
        choices=["prototype", "normal", "client-production"],
        help="Production context"
    )
    parser.add_argument(
        "--fixture",
        default="faber-brand",
        help="Design system fixture"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON with all artifacts"
    )

    args = parser.parse_args()

    if not args.client_context:
        parser.print_help()
        sys.exit(1)

    # Process through intent-collect pipeline (using the functions defined above)
    def extract_facts(client_context: str):
        facts = {}
        ctx_lower = client_context.lower()
        goal = None
        audience = None
        constraints = None

        if "goal" in ctx_lower or "objective" in ctx_lower:
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

        if goal:
            facts["goal"] = goal
        if audience:
            facts["audience"] = audience
        if constraints:
            facts["constraints"] = constraints

        return facts

    def elicit_gaps(client_context: str, facts):
        gaps = []
        ctx_lower = client_context.lower()

        ELICITATION_QUESTIONS = [
            "What is the primary goal or outcome desired?",
            "Who are the primary audiences/users and their jobs-to-be-done?",
            "What is explicitly out of scope (non-goals)?",
            "What information architecture or content structure is needed?",
            "What is the content model (types, fields, relationships)?",
            "What constraints exist (brand, legal, technical, temporal)?",
            "What are the success metrics or acceptance criteria?",
        ]

        for i, question in enumerate(ELICITATION_QUESTIONS, 1):
            q_lower = question.lower()
            words = [word.strip('.,?!()') for word in q_lower.split()
                    if len(word) > 3 and word not in {'what', 'the', 'and', 'or', 'for', 'are', 'is', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'to', 'of', 'in', 'on', 'at', 'by'}]
            if not words:
                words = ['goal', 'audience', 'scope', 'structure', 'model', 'constraints', 'metrics']

            if not any(word in ctx_lower for word in words):
                gaps.append(f"{i}. {question}")

        return gaps

    def generate_spec(client_context: str, facts, gaps):
        goal = facts.get("goal", "Build a website")
        audience = facts.get("audience", "Target audience")
        constraints = facts.get("constraints", "Brand guidelines")

        spec = f"""# Spec

## Context
{client_context.strip()}
- Goal: {goal}
- Audience: {audience}
- Non-goals: None specified
- Constraints: {constraints}

## Acceptance Criteria

- SPEC-01: The system shall support the primary goal: {goal}
- SPEC-02: The system shall serve the target audience: {audience}
"""

        if "blog" in client_context.lower() or "cms" in client_context.lower():
            spec += "- SPEC-03: Content shall be editable via admin interface\n"
            spec += "- SPEC-04: Content shall support versioning\n"
        elif "ecommerce" in client_context.lower() or "shop" in client_context.lower():
            spec += "- SPEC-03: Product catalog shall support search and filtering\n"
            spec += "- SPEC-04: Checkout process shall be PCI compliant\n"
        else:
            spec += "- SPEC-03: System shall be responsive and accessible\n"
            spec += "- SPEC-04: System shall follow security best practices\n"

        if gaps:
            spec += "\n## TODO (Elicited Gaps)\n"
            for gap in gaps:
                spec += f"- TODO: {gap}\n"

        return spec

    def generate_trajectory(production_context: str = "normal"):
        strictness_map = {
            "prototype": "partial",
            "normal": "ordered",
            "client-production": "exact"
        }
        strictness = strictness_map.get(production_context.lower(), "ordered")

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

        trajectory_steps = []
        for stage in LIFECYCLE_STAGES:
            trajectory_steps.append(f"{len(trajectory_steps)+1}. {stage}")

        if "HITL" not in "\n".join(trajectory_steps):
            trajectory_steps.append(f"{len(trajectory_steps)+1}. HITL confirmation")

        trajectory = f"""# Trajectory (strictness: {strictness})

{chr(10).join(trajectory_steps)}
"""
        return trajectory

    def generate_scope_baseline(client_context: str, facts):
        goal = facts.get("goal", "Build a website")
        audience = facts.get("audience", "Target audience")
        constraints = facts.get("constraints", "Brand guidelines")

        scope = f"""# Scope Baseline

Derived from the provided context.

{client_context.strip()}
- Goal: {goal}
- Audience: {audience}
- Non-goals: None specified
- Constraints: {constraints}

TODO: Review with client.
"""
        return scope

    def generate_backlog_draft(client_context: str, facts, spec, fixture):
        goal = facts.get("goal", "Build a website")

        spec_lines = spec.split("\n")
        spec_items = [line.strip() for line in spec_lines if line.strip().startswith("- SPEC-")]
        todo_items = [line.strip() for line in spec_lines if line.strip().startswith("- TODO:")]

        backlog = f"""# Backlog Draft — Generated from Intent

*Auto-generated from intent submission. Review and refine before adding to project backlog.*

## Epic: {goal}

### Functional Requirements
- [ ] Implement core functionality for: {goal}
- [ ] Support target audience: {facts.get('audience', 'TBD')}
- [ ] Meet constraints: {facts.get('constraints', 'TBD')}

### Technical Requirements
- [ ] Astro + Cloudflare Pages setup
- [ ] D1 database schema for content
- [ ] CI/CD pipeline (lint → test → deploy-preview → deploy-staging → deploy-production)
- [ ] Design system integration ({fixture} fixture)

### Acceptance Criteria (from spec)
"""

        for item in spec_items:
            backlog += f"- [ ] {item[2:]}\n"

        backlog += "\n### Open Questions (from elicited gaps)\n"

        if todo_items:
            for item in todo_items:
                backlog += f"- [ ] {item[8:]}\n"
        else:
            backlog += "- [ ] No elicited gaps\n"

        backlog += f"""
---
*Generated by Faber Intent Wizard ({fixture} fixture)*
"""
        return backlog

    facts = extract_facts(args.client_context)
    gaps = elicit_gaps(args.client_context, facts)
    spec = generate_spec(args.client_context, facts, gaps)
    trajectory = generate_trajectory(args.production_context)
    scope_baseline = generate_scope_baseline(args.client_context, facts)
    backlog = generate_backlog_draft(args.client_context, facts, spec, args.fixture)

    if args.json:
        result = {
            "spec_md": spec,
            "trajectory_md": trajectory,
            "scope_baseline_md": scope_baseline,
            "backlog_draft_md": backlog,
            "extracted_facts": facts,
            "elicited_gaps": gaps,
        }
        output = json.dumps(result, indent=2)
    else:
        output = backlog

    if args.output:
        Path(args.output).write_text(output)
        print(f"Backlog draft written to {args.output}", file=sys.stderr)
    else:
        print(output)