#!/usr/bin/env python3
"""
Categorize PR review comments by type using deterministic heuristics.
Categories: style, docs, security, test, logic, design, unknown
"""
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
from pathlib import Path


@dataclass
class CategorizedComment:
    id: int
    body: str
    path: str
    line: int
    category: str  # style, docs, security, test, logic, design, unknown
    confidence: float  # 0.0 - 1.0
    suggested_fix_type: str  # auto, llm, defer, manual
    matched_patterns: List[str]


# Deterministic patterns (regex) for each category
PATTERNS: Dict[str, List[Tuple[str, float]]] = {
    "style": [
        (r"\b(?:typo|spelling|capitalize|lowercase|uppercase)\b", 0.9),
        (r"\b(?:formatting|format|indent|whitespace|trailing)\b", 0.9),
        (r"\b(?:naming|variable|function|class).*(?:convention|style|pep8|snake_case|camelCase)\b", 0.8),
        (r"\b(?:import|unused import|wildcard import)\b", 0.9),
        (r"\b(?:lint|ruff|prettier|eslint|flake8|black|isort)\b", 0.95),
        (r"\b(?:sort|organize).*(?:import|imports)\b", 0.85),
        (r"\b(?:line too long|max.line|column)\b", 0.9),
        (r"\b(?:semicolon|semicolons|double quote|single quote)\b", 0.85),
        (r"\b(?:variable|var|name).*(?:not descriptive|descriptive|rename|meaningful)\b", 0.85),
    ],
    "docs": [
        (r"\b(?:docstring|docstrings|documentation|docs)\b", 0.9),
        (r"\b(?:readme|README|comment|comments).*(?:missing|add|update|outdated)\b", 0.85),
        (r"\b(?:type hint|typehint|annotation|typing).*(?:missing|add)\b", 0.85),
        (r"\b(?:example|usage|demo).*(?:missing|add)\b", 0.8),
        (r"\b(?:changelog|CHANGELOG|version|release).*(?:note|entry)\b", 0.8),
    ],
    "security": [
        (r"\b(?:secret|password|token|api.key|private.key|credential)\b", 0.95),
        (r"\b(?:hardcoded|hard.code).*(?:secret|password|token|key)\b", 0.95),
        (r"\b(?:sql.inject|xss|csrf|rce|path.traversal)\b", 0.9),
        (r"\b(?:vulnerability|cve|security).*(?:issue|concern|risk)\b", 0.85),
        (r"\b(?:encrypt|decrypt|hash|salt).*(?:weak|insecure|md5|sha1)\b", 0.9),
    ],
    "test": [
        (r"\b(?:test|tests|testing|coverage|pytest|unittest)\b.*(?:missing|add|flaky|failing|fails)\b", 0.9),
        (r"\b(?:unit test|integration test|e2e)\b.*(?:missing|add)\b", 0.9),
        (r"\b(?:mock|stub|fixture)\b.*(?:missing|incorrect|wrong)\b", 0.85),
        (r"\b(?:edge case|boundary|corner case)\b.*(?:not tested|missing test)\b", 0.9),
        (r"\b(?:assert|expect|verify)\b.*(?:missing|wrong|incorrect)\b", 0.8),
        (r"\b(?:missing|add).*\btest\b", 0.8),
    ],
    "logic": [
        (r"\b(?:bug|incorrect|wrong|error|issue).*(?:logic|algorithm|calculation|condition)\b", 0.9),
        (r"\b(?:off.by.one|infinite.loop|null.pointer|npe|index.out.of.bounds)\b", 0.95),
        (r"\b(?:race.condition|concurrency|thread.safe|deadlock)\b", 0.9),
        (r"\b(?:memory.leak|performance|slow|optimization).*(?:issue|problem)\b", 0.8),
        (r"\b(?:return|result|output).*(?:incorrect|wrong|unexpected)\b", 0.85),
    ],
    "design": [
        (r"\b(?:architecture|design|pattern|structure).*(?:issue|concern|suggest|recommend)\b", 0.85),
        (r"\b(?:api|interface|contract|public).*(?:breaking|change|inconsistent)\b", 0.9),
        (r"\b(?:coupling|cohesion|separation.of.concerns|single.responsibility)\b", 0.85),
        (r"\b(?:refactor|restructure|reorganize|extract).*(?:class|function|module)\b", 0.8),
        (r"\b(?:dependency|import).*(?:cycle|circular|unnecessary)\b", 0.85),
    ],
}


def categorize_comment(comment: dict) -> CategorizedComment:
    """Categorize a single comment using pattern matching."""
    body = comment.get("body", "").lower()
    path = comment.get("path", "")
    line = comment.get("line", 0)
    comment_id = comment.get("id", 0)

    best_category = "unknown"
    best_confidence = 0.0
    matched = []

    for category, patterns in PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, body, re.IGNORECASE):
                if weight > best_confidence:
                    best_confidence = weight
                    best_category = category
                matched.append(pattern)

    # Determine fix type based on category
    fix_type_map = {
        "style": "auto",
        "docs": "auto",
        "security": "defer",  # Security issues need human review
        "test": "auto",  # Can generate test templates
        "logic": "llm",  # Needs code understanding
        "design": "llm",  # Needs architectural context
        "unknown": "defer",
    }
    suggested_fix = fix_type_map.get(best_category, "defer")

    return CategorizedComment(
        id=comment_id,
        body=comment.get("body", ""),
        path=path,
        line=line,
        category=best_category,
        confidence=best_confidence,
        suggested_fix_type=suggested_fix,
        matched_patterns=matched,
    )


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: categorize.py <comments.json>"}))
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file) as f:
            data = json.load(f)

        comments = data.get("comments", [])
        categorized = [categorize_comment(c) for c in comments]

        output = {
            "pr_number": data.get("pr_number"),
            "repo": data.get("repo"),
            "categorized": [asdict(c) for c in categorized],
            "summary": {
                "total": len(categorized),
                "by_category": {},
            },
        }

        for c in categorized:
            output["summary"]["by_category"][c.category] = \
                output["summary"]["by_category"].get(c.category, 0) + 1

        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()