#!/usr/bin/env python3
"""
Deterministic classification rubric for PR review comments.

No LLM calls. Ambiguous comments → severity=Medium, type=needs-triage (never guessed).
"""

import json
import re
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IssueType(Enum):
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    DOCS = "docs"
    REFACTOR = "refactor"
    SECURITY = "security"
    NEEDS_TRIAGE = "needs-triage"


@dataclass
class ClassifiedComment:
    """Result of classifying a PR review comment."""
    source_comment_id: str
    body: str
    path: Optional[str]
    line: Optional[int]
    commit_id: Optional[str]
    user: str
    created_at: str
    is_actionable: bool
    severity: str
    issue_type: str
    confidence: float
    matched_patterns: List[str]
    dedup_key: str


# Keyword-based rubric for deterministic classification
# Order matters: more specific patterns first
SEVERITY_RUBRIC: List[Tuple[re.Pattern, Severity]] = [
    # Critical - production-breaking, data loss, security vuln
    (re.compile(r"\b(crash|data loss|data corruption|security vulnerability|rce|sql injection|xss|auth bypass|privilege escalation|zero.?day|prod(?:uction)?\s*(?:down|outage)|outage|downtime|breaking change|CRITICAL)\b", re.I), Severity.CRITICAL),
    (re.compile(r"\b(blocker|release[.\s]?blocker|p0|sev\.?1)\b", re.I), Severity.CRITICAL),

    # High - significant functionality broken, major perf, a11y
    (re.compile(r"\b(major bug|significant|critical path|core functionality|broken|fails?(?:\s+to|\s+silently)?|doesn't work|not working|broken flow|memory leak|performance regression|accessibility|a11y|wcag|violation|should really|must fix|would be much better)\b", re.I), Severity.HIGH),
    (re.compile(r"\b(high\.?priority|p1|sev\.?2)\b", re.I), Severity.HIGH),

    # Medium (explicit patterns)
    (re.compile(r"\b(consider adding|missing error handling|inconsistent|should be split|type hints? incomplete)\b", re.I), Severity.MEDIUM),

    # Low - nitpicks, style, minor improvements
    (re.compile(r"\b(nit|nitpick|style|formatting|whitespace|typo|spelling|grammar|prettier|eslint|lint|trailing comma|unused import|dead code|simplify|cleanup|refactor.*minor|prefer single|prefer double)\b", re.I), Severity.LOW),
    (re.compile(r"\b(low\.?priority|p3|sev\.?4|nice\.?to\.?have|optional)\b", re.I), Severity.LOW),
]

TYPE_RUBRIC: List[Tuple[re.Pattern, IssueType]] = [
    # Security - check first
    (re.compile(r"\b(security|vulnerability|exploit|attack|injection|xss|csrf|auth(?:orization)?|authentication|rbac|permission|access\.?control|secret|token|credential|bypass)\b", re.I), IssueType.SECURITY),

    # Bug - include "fails" and "failing"
    (re.compile(r"\b(bug|defect|error|exception|crash|fail|fails|failing|broken|incorrect|wrong|fix|regression|violation|outage|data loss)\b", re.I), IssueType.BUG),

    # Refactor - check before enhancement
    (re.compile(r"\b(refactor|restructure|reorganize|cleanup|simplify|extract|move|rename|dead\.?code|duplicate|dry|split|too much|doing too much|should be split)\b", re.I), IssueType.REFACTOR),

    # Enhancement - use word boundaries properly for "add" -> "adding"
    (re.compile(r"\b(enhancement|feature|improvement|add\w*|support|implement|extend|pagination|caching|webhook|would be (much )?better)\b", re.I), IssueType.ENHANCEMENT),

    # Docs
    (re.compile(r"\b(doc|documentation|readme|comment|docstring|typo|spelling|grammar|clarify|explain|example)\b", re.I), IssueType.DOCS),
]


def classify_severity(text: str) -> Tuple[Severity, List[str]]:
    """Classify severity based on keyword matching. Returns (severity, matched_patterns)."""
    matched = []
    for pattern, severity in SEVERITY_RUBRIC:
        if pattern.search(text):
            matched.append(pattern.pattern)
            return severity, matched
    # Default: Medium (never guessed - explicit default)
    return Severity.MEDIUM, ["default:medium"]


def classify_type(text: str) -> Tuple[IssueType, List[str]]:
    """Classify issue type based on keyword matching. Returns (type, matched_patterns)."""
    matched = []
    for pattern, itype in TYPE_RUBRIC:
        if pattern.search(text):
            matched.append(pattern.pattern)
            return itype, matched
    # Default: needs-triage (never guessed)
    return IssueType.NEEDS_TRIAGE, ["default:needs-triage"]


def is_actionable_comment(text: str) -> bool:
    """
    Determine if a comment is actionable (should become an issue).
    Non-actionable: pure praise, approvals, questions without action words, discussions without action words.
    """
    text_stripped = text.strip()

    # 1. "Consider X" with action verb -> actionable (check FIRST before suggestions)
    consider_match = re.match(r"^\s*consider\s+(\w+)", text, re.I)
    if consider_match:
        verb = consider_match.group(1).lower()
        action_verbs = {"adding", "implementing", "fixing", "changing", "updating", "removing", "refactoring", "improving"}
        if verb in action_verbs:
            return True
        # Consider without action verb -> check for other action words
        action_words = r"\b(should|must|need to|have to|require|fix|change|update|modify|add|remove|delete|please|can we|could we)\b"
        if not re.search(action_words, text, re.I):
            return False
        return True

    # 2. "nitpick:" at start is actionable (code review comment)
    if re.match(r"^\s*nitpick\s*:", text, re.I):
        return True

    # 3. ONLY pure praise/approval with no other content
    pure_praise_patterns = [
        r"^\s*(lgtm|looks good|approved|ship it|:?\+1:?|👍|thanks|thank you|great job|nice work|awesome|perfect)[\s\W]*$",
        r"^\s*(ack|acknowledged|noted|agreed)[\s\W]*$",
    ]
    for pattern in pure_praise_patterns:
        if re.search(pattern, text, re.I | re.UNICODE):
            return False

    # 4. "Looks good to me" variations
    if re.match(r"^\s*looks good to me", text, re.I):
        action_words = r"\b(should|must|need to|have to|require|fix|change|update|modify|add|remove|delete|please|can we|could we)\b"
        if not re.search(action_words, text, re.I):
            return False

    # 5. Questions starting with question words are non-actionable UNLESS they contain action words
    if re.match(r"^\s*(what|why|how|when|where|who)\b", text, re.I):
        action_words = r"\b(should|must|need to|have to|require|fix|change|update|modify|add|remove|delete|please|can we|could we)\b"
        if not re.search(action_words, text, re.I):
            return False

    # 6. "What's" (with apostrophe) questions
    if re.match(r"^\s*what's\b", text, re.I):
        # Action words as verbs only, not nouns
        action_words = r"\b(should|must|need to|have to|require|fix|update|modify|add|remove|delete|please|can we|could we)\b"
        if not re.search(action_words, text, re.I):
            return False

    # 7. Pure curiosity/discussion without action words
    if re.search(r"\b(curious|wonder|question|ask|confused)\b", text, re.I):
        action_words = r"\b(should|must|need to|have to|require|fix|change|update|modify|add|remove|delete|please|can we|could we)\b"
        if not re.search(action_words, text, re.I):
            return False

    # 8. Suggestions/preferences without action words (but NOT "consider" which is handled above)
    if re.search(r"\b(discuss|discussion|opinion|thoughts|prefer|suggest)\b", text, re.I):
        action_words = r"\b(should|must|need to|have to|require|fix|change|update|modify|add|remove|delete|please|can we|could we)\b"
        if not re.search(action_words, text, re.I):
            return False

    return True


def generate_dedup_key(source_repo: str, source_pr: int, source_comment_id: str) -> str:
    """Generate a deterministic dedup key from source identifiers."""
    content = f"{source_repo}:{source_pr}:{source_comment_id}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def classify_comment(
    comment: Dict[str, Any],
    source_repo: str,
    source_pr: int
) -> ClassifiedComment:
    """
    Classify a single PR review comment.

    Args:
        comment: Dict with keys: id, body, path, line, commit_id, user, created_at
        source_repo: Repository in 'owner/name' format
        source_pr: PR number

    Returns:
        ClassifiedComment with classification results
    """
    body = comment.get("body", "")
    comment_id = str(comment.get("id", ""))

    # Check if actionable
    actionable = is_actionable_comment(body)

    if not actionable:
        return ClassifiedComment(
            source_comment_id=comment_id,
            body=body,
            path=comment.get("path"),
            line=comment.get("line"),
            commit_id=comment.get("commit_id"),
            user=comment.get("user", {}).get("login", "unknown") if isinstance(comment.get("user"), dict) else str(comment.get("user", "unknown")),
            created_at=comment.get("created_at", ""),
            is_actionable=False,
            severity="Low",
            issue_type="non-actionable",
            confidence=1.0,
            matched_patterns=["non-actionable"],
            dedup_key=generate_dedup_key(source_repo, source_pr, comment_id)
        )

    # Classify severity and type
    severity, sev_matches = classify_severity(body)
    itype, type_matches = classify_type(body)

    # Calculate confidence based on number of matches
    total_matches = len(sev_matches) + len(type_matches)
    confidence = min(0.5 + (total_matches * 0.15), 1.0)

    return ClassifiedComment(
        source_comment_id=comment_id,
        body=body,
        path=comment.get("path"),
        line=comment.get("line"),
        commit_id=comment.get("commit_id"),
        user=comment.get("user", {}).get("login", "unknown") if isinstance(comment.get("user"), dict) else str(comment.get("user", "unknown")),
        created_at=comment.get("created_at", ""),
        is_actionable=True,
        severity=severity.value,
        issue_type=itype.value,
        confidence=confidence,
        matched_patterns=sev_matches + type_matches,
        dedup_key=generate_dedup_key(source_repo, source_pr, comment_id)
    )


def classify_comments(
    comments: List[Dict[str, Any]],
    source_repo: str,
    source_pr: int
) -> List[ClassifiedComment]:
    """Classify a list of PR review comments."""
    return [classify_comment(c, source_repo, source_pr) for c in comments]


def main() -> None:
    """CLI entry point for testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Classify PR review comments")
    parser.add_argument("--input", required=True, help="JSON file with PR review comments")
    parser.add_argument("--repo", required=True, help="Source repository (owner/name)")
    parser.add_argument("--pr", type=int, required=True, help="Source PR number")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    with open(args.input) as f:
        comments = json.load(f)

    classified = classify_comments(comments, args.repo, args.pr)
    output = [asdict(c) for c in classified]

    result = json.dumps(output, indent=2)
    if args.output:
        Path(args.output).write_text(result)
    else:
        print(result)


if __name__ == "__main__":
    main()