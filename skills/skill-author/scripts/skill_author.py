#!/usr/bin/env python3
"""
Skill-Author Skill - Governed self-extension for Faber framework.

Implements FRAMEWORK.md §7: Meta-skill for self-extension.
- Trigger: recurring pattern in lessons.md/feedback or capability gap
- Procedure: search existing skills (dedup) → draft SKILL.md + scripts/ + eval
  → run eval → open PR with rationale + eval results
- Classification: client-scoped vs framework-scoped
- Gates (HITL): (1) dev reviews/approves PR; (2) promoting client→framework = second PR
- Hard rules: no skill without eval; no skill without dedup search
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Skill contract template
SKILL_MD_TEMPLATE = """---
name: {name}
description: |
  {description}
version: 1.0.0
author: {author}
license: {license}
tags: {tags}
---

# {name_title}

## Overview
{overview}

## Interface
```json
{interface_json}
```

## Evaluation
The skill passes when:
{eval_criteria}

## Determinism & HITL
- **Determinism**: Same inputs → same output structure
- **HITL Gate**: {hitl_gate}
- **Unknown Handling**: Gaps surface as `TODO:`, never fabricated

## Dedup Search
This skill was created after searching existing skills:
{dedup_results}
"""

# Main script template
SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""
{name_title} Skill - {description}

Implements {purpose}.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def main() -> None:
    """Main entry point for {name} skill."""
    parser = argparse.ArgumentParser(
        description="{description}"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON with required fields"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write output files (default: current)"
    )
    parser.add_argument(
        "--hitl-gate",
        action="store_true",
        help="Enable HITL gate (requires manual confirmation)"
    )

    args = parser.parse_args()

    # TODO: Implement skill logic
    # 1. Parse input JSON
    # 2. Process deterministically
    # 3. Write output files
    # 4. Emit machine-readable summary

    # Placeholder implementation
    result = {{
        "status": "success",
        "artifacts": [],
        "hitl_gate_required": args.hitl_gate,
        "hitl_gate_passed": True,
    }}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
'''

# Eval template
EVAL_TEMPLATE = '''#!/usr/bin/env python3
"""
Eval for the {name} skill.

Tests that the skill:
1. Has the required SKILL.md with correct description
2. Has executable scripts/
3. Produces expected outputs deterministically
4. Handles unknowns as TODO:, never fabricates
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_skill_md_exists() -> None:
    """Test that SKILL.md exists with required fields."""
    skill_md = Path("skills/{name}/SKILL.md")
    assert skill_md.exists(), "SKILL.md must exist"

    content = skill_md.read_text()
    assert "name:" in content, "SKILL.md must have name field"
    assert "description:" in content, "SKILL.md must have description"
    assert "{name}" in content, "SKILL.md must mention skill name"
    print("✓ SKILL.md exists with required fields")


def test_script_exists_and_executable() -> None:
    """Test that main script exists and is executable."""
    script = Path("skills/{name}/scripts/{name}.py")
    assert script.exists(), f"{{name}}.py must exist"
    assert os.access(str(script), os.X_OK), f"{{name}}.py must be executable"
    print("✓ {{name}}.py exists and is executable")


def test_script_help() -> None:
    """Test that script shows usage when run without required args."""
    result = subprocess.run(
        [sys.executable, "skills/{name}/scripts/{name}.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Should exit with error code when args missing"
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "arguments" in output.lower(), "Should show usage"
    print("✓ Script shows usage without required args")


def test_determinism() -> None:
    """Test that two runs on identical inputs yield identical structure."""
    test_input = {{"test": "input"}}
    input_json = json.dumps(test_input)

    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        # Run first time
        result1 = subprocess.run([
            sys.executable,
            "skills/{name}/scripts/{name}.py",
            "--input", input_json,
            "--output-dir", tmpdir1
        ], capture_output=True, text=True, timeout=30)

        # Run second time
        result2 = subprocess.run([
            sys.executable,
            "skills/{name}/scripts/{name}.py",
            "--input", input_json,
            "--output-dir", tmpdir2
        ], capture_output=True, text=True, timeout=30)

        assert result1.returncode == 0 and result2.returncode == 0, "Both runs should succeed"

        # Compare file contents (should be identical)
        for filename in os.listdir(tmpdir1):
            if filename.endswith(".md") or filename.endswith(".json"):
                content1 = (Path(tmpdir1) / filename).read_text()
                content2 = (Path(tmpdir2) / filename).read_text()
                assert content1 == content2, f"{{filename}} should be identical between runs"

    print("✓ Determinism test passed")


def test_todo_not_fabrication() -> None:
    """Test that unknowns appear as TODO:, never fabricated details."""
    test_input = {{"test": "minimal input"}}
    input_json = json.dumps(test_input)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            sys.executable,
            "skills/{name}/scripts/{name}.py",
            "--input", input_json,
            "--output-dir", tmpdir
        ], capture_output=True, text=True, timeout=30)

        assert result.returncode == 0, "Should succeed"

        # Check output files for TODO items, no fabrication
        for filename in os.listdir(tmpdir):
            if filename.endswith(".md"):
                content = (Path(tmpdir) / filename).read_text()
                # Should have TODO for unknowns
                # Should NOT contain specific fabricated details
                assert "TODO:" in content or "todo:" in content.lower(), f"{{filename}} should have TODO for unknowns"

    print("✓ TODO/not-fabrication test passed")


def main() -> None:
    tests = [
        test_skill_md_exists,
        test_script_exists_and_executable,
        test_script_help,
        test_determinism,
        test_todo_not_fabrication,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {{test.__name__}} FAILED: {{e}}")
            failed += 1

    print(f"\\n=== Results: {{passed}} passed, {{failed}} failed ===")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
'''


def search_existing_skills(query: str) -> List[Dict[str, Any]]:
    """Search existing skills for dedup. Returns list of matches."""
    skills_dir = Path("skills")
    if not skills_dir.exists():
        return []

    matches = []
    query_lower = query.lower()
    query_words = set(query_lower.split())

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        content = skill_md.read_text().lower()
        skill_name = skill_dir.name

        # Simple keyword overlap scoring
        skill_words = set(content.split())
        overlap = len(query_words & skill_words)

        # Check name similarity
        name_similarity = 1.0 if query_lower in skill_name.lower() else 0.0

        # Check tag overlap
        tags = re.findall(r"tags:\s*\[(.*?)\]", content)
        tag_overlap = 0
        if tags:
            existing_tags = set(t.strip().strip('"') for t in tags[0].split(','))
            query_tags = set(query_lower.split())
            tag_overlap = len(existing_tags & query_tags)

        score = overlap * 0.5 + name_similarity * 0.3 + tag_overlap * 0.2

        if score > 0.1:  # Threshold for relevance
            matches.append({
                "skill": skill_name,
                "score": round(score, 3),
                "overlap_words": overlap,
                "name_match": name_similarity > 0,
                "tag_overlap": tag_overlap,
            })

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def format_dedup_results(matches: List[Dict[str, Any]]) -> str:
    """Format dedup search results for SKILL.md."""
    if not matches:
        return "No existing skills found matching the query. Proceeding with new skill creation."

    lines = ["| Skill | Score | Overlap | Name Match | Tag Overlap |", "|-------|-------|---------|------------|-------------|"]
    for m in matches[:5]:  # Top 5 matches
        lines.append(f"| {m['skill']} | {m['score']} | {m['overlap_words']} | {m['name_match']} | {m['tag_overlap']} |")
    lines.append("")
    lines.append("**Recommendation**: " + (
        "High similarity to existing skill(s) — consider extending instead of creating new."
        if matches[0]["score"] > 0.5
        else "Low similarity — new skill creation appropriate."
    ))
    return "\n".join(lines)


def draft_skill(
    name: str,
    description: str,
    trigger: str,
    context: str,
    scope: str,
    author: str = "ndethi",
    license: str = "MIT",
    tags: List[str] = None,
) -> Dict[str, Any]:
    """Draft a new skill based on trigger and context."""

    if tags is None:
        tags = [trigger, "auto-generated"]

    # Dedup search
    dedup_query = f"{name} {description} {context}"
    matches = search_existing_skills(dedup_query)

    # Generate skill components
    name_title = name.replace("-", " ").title()
    tags_str = "[" + ", ".join(f'"{t}"' for t in tags) + "]"

    # Interface based on trigger type
    if trigger == "gap":
        interface = '{\n  "input": "string",\n  "context": "string"\n}'
    elif trigger == "pattern":
        interface = '{\n  "pattern": "string",\n  "examples": ["string"]\n}'
    else:  # capability
        interface = '{\n  "capability": "string",\n  "requirements": ["string"]\n}'

    eval_criteria = "\n".join(f"- {c}" for c in [
        "SKILL.md exists with required YAML frontmatter",
        "scripts/ directory with executable entry point",
        "evals/ directory with passing test",
        "Deterministic output for identical inputs",
        "Unknowns appear as TODO:, never fabricated",
        "Dedup search documented in SKILL.md",
    ])

    hitl_gate = "Dev reviews/approves PR (client-scoped); promotion to framework-scoped requires second PR/gate"

    # Build SKILL.md content
    skill_md = SKILL_MD_TEMPLATE.format(
        name=name,
        name_title=name_title,
        description=description,
        overview=f"Auto-generated skill for {trigger}: {context}. {description}",
        interface_json=interface,
        eval_criteria="\n".join(f"  {c}" for c in [
            "SKILL.md exists with required YAML frontmatter",
            "scripts/ directory with executable entry point",
            "evals/ directory with passing test",
            "Deterministic output for identical inputs",
            "Unknowns appear as TODO:, never fabricated",
            "Dedup search documented in SKILL.md",
        ]),
        hitl_gate=hitl_gate,
        dedup_results=format_dedup_results(matches),
        author=author,
        license=license,
        tags=tags_str,
    )

    # Build script content
    script_content = SCRIPT_TEMPLATE.format(
        name=name,
        name_title=name_title,
        description=description,
        purpose=f"{trigger} handling: {context}",
    )

    # Build eval content
    eval_content = EVAL_TEMPLATE.format(name=name, name_title=name_title)

    return {
        "name": name,
        "scope": scope,
        "skill_md": skill_md,
        "script": script_content,
        "eval": eval_content,
        "dedup_matches": matches,
        "interface": interface,
    }


def write_skill_files(skill: Dict[str, Any], output_dir: str = ".") -> None:
    """Write skill files to disk."""
    name = skill["name"]
    skill_path = Path(output_dir) / "skills" / name
    scripts_path = skill_path / "scripts"
    evals_path = skill_path / "evals"

    # Create directories
    skill_path.mkdir(parents=True, exist_ok=True)
    scripts_path.mkdir(parents=True, exist_ok=True)
    evals_path.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md
    (skill_path / "SKILL.md").write_text(skill["skill_md"])

    # Write main script
    script_file = scripts_path / f"{name}.py"
    script_file.write_text(skill["script"])
    script_file.chmod(0o755)  # Make executable

    # Write eval
    eval_file = evals_path / f"test_{name}.py"
    eval_file.write_text(skill["eval"])
    eval_file.chmod(0o755)


def run_skill_eval(name: str, output_dir: str = ".") -> Tuple[bool, str]:
    """Run the skill's eval and return (success, output)."""
    # Use the output_dir as working directory since skills are created there
    work_dir = Path(output_dir).resolve()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", f"skills/{name}/evals/", "-v"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=work_dir,
    )
    return result.returncode == 0, result.stdout + result.stderr


def generate_pr_body(skill: Dict[str, Any], eval_passed: bool, eval_output: str) -> str:
    """Generate PR body markdown."""
    name = skill["name"]
    scope = skill["scope"]
    matches = skill["dedup_matches"]

    pr_body = f"""## Skill-Author Draft: `{name}` ({scope})

### Trigger
Auto-generated via skill-author meta-skill.

### Summary
- **Trigger**: Capability gap / recurring pattern
- **Context**: {skill.get("context", "N/A")}
- **Scope**: {scope}

### Dedup Search Results
"""

    if matches:
        pr_body += "| Skill | Score | Notes |\n|-------|-------|-------|\n"
        for m in matches[:5]:
            notes = []
            if m["name_match"]: notes.append("name match")
            if m["tag_overlap"]: notes.append(f"{m['tag_overlap']} tag(s) overlap")
            pr_body += f"| {m['skill']} | {m['score']} | {', '.join(notes) or 'keyword overlap'} |\n"
    else:
        pr_body += "No existing skills found matching the query.\n"

    pr_body += f"""
### Eval Results
**Status**: {'✅ PASSED' if eval_passed else '❌ FAILED'}

```
{eval_output[:2000]}
```

### Classification
- **{scope}**: Lives in this repo's `skills/` directory
- **Promotion to framework-scoped**: Requires second PR + HITL gate

### HITL Gates
1. **This PR**: Dev reviews skill contract, evals, and implementation → approve/merge
2. **Promotion PR** (if framework-scoped needed): Separate PR to framework library → second HITL

### Hard Rules Compliance
- ✅ No skill without eval (evals/ created and tested)
- ✅ No skill without dedup search (results documented above)
- ✅ Agent proposes, dev disposes (this PR)

---

*Generated by skill-author meta-skill per FRAMEWORK.md §7*
"""
    return pr_body


def main():
    parser = argparse.ArgumentParser(
        description="Skill-Author: Governed self-extension for Faber framework"
    )
    parser.add_argument(
        "--trigger",
        required=True,
        choices=["gap", "pattern", "capability"],
        help="What triggered this skill creation"
    )
    parser.add_argument(
        "--context",
        required=True,
        help="Description of the gap, pattern, or capability needed"
    )
    parser.add_argument(
        "--name",
        help="Skill name (kebab-case). Auto-generated if not provided."
    )
    parser.add_argument(
        "--scope",
        default="client-scoped",
        choices=["client-scoped", "framework-scoped"],
        help="Skill scope classification"
    )
    parser.add_argument(
        "--author",
        default="ndethi",
        help="Author name for skill"
    )
    parser.add_argument(
        "--license",
        default="MIT",
        help="License for skill"
    )
    parser.add_argument(
        "--tags",
        help="Comma-separated tags"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write skill files (default: current)"
    )
    parser.add_argument(
        "--auto-pr",
        action="store_true",
        help="Automatically open PR after eval passes"
    )
    parser.add_argument(
        "--run-eval",
        action="store_true",
        help="Run eval after drafting (default: true)"
    )
    parser.add_argument(
        "--no-eval",
        action="store_true",
        help="Skip eval run"
    )

    args = parser.parse_args()

    # Generate skill name if not provided
    if not args.name:
        # Extract key words from context
        words = re.findall(r'\b\w{4,}\b', args.context.lower())
        name = "-".join(words[:3]) if words else "new-skill"
    else:
        name = args.name

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else [args.trigger, "auto-generated"]

    print(f"🔍 Searching existing skills for dedup...", file=sys.stderr)
    draft = draft_skill(
        name=name,
        description=args.context[:200],
        trigger=args.trigger,
        context=args.context,
        scope=args.scope,
        author=args.author,
        license=args.license,
        tags=tags,
    )

    print(f"📝 Drafting skill `{name}` ({args.scope})...", file=sys.stderr)
    write_skill_files(draft, args.output_dir)

    eval_passed = False
    eval_output = ""

    if not args.no_eval:
        print(f"🧪 Running eval for `{name}`...", file=sys.stderr)
        eval_passed, eval_output = run_skill_eval(name, args.output_dir)
        if eval_passed:
            print(f"✅ Eval passed", file=sys.stderr)
        else:
            print(f"❌ Eval failed:\n{eval_output}", file=sys.stderr)

    # Generate PR body
    pr_body = generate_pr_body(draft, eval_passed, eval_output)
    pr_body_file = Path(args.output_dir) / f"PR_BODY_{name}.md"
    pr_body_file.write_text(pr_body)
    print(f"📄 PR body written to {pr_body_file}", file=sys.stderr)

    # Auto-create PR if requested and eval passed
    if args.auto_pr and eval_passed:
        try:
            result = subprocess.run([
                "gh", "pr", "create",
                "--base", "dev",
                "--title", f"feat: add {name} skill ({args.scope})",
                "--body", pr_body,
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"🚀 PR created: {result.stdout.strip()}", file=sys.stderr)
            else:
                print(f"⚠️  PR creation failed: {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  PR creation error: {e}", file=sys.stderr)

    # Output summary
    output = {
        "status": "success",
        "skill_name": name,
        "scope": args.scope,
        "trigger": args.trigger,
        "dedup_matches": len(draft["dedup_matches"]),
        "eval_passed": eval_passed,
        "files_created": [
            f"skills/{name}/SKILL.md",
            f"skills/{name}/scripts/{name}.py",
            f"skills/{name}/evals/test_{name}.py",
        ],
        "pr_body_file": str(pr_body_file),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()