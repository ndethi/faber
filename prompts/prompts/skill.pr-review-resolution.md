---
id: skill.pr-review-resolution
version: 1.0.0
status: draft
intent: Fetch review comments from GitHub PR (via gh API or email), categorize, generate fixes, push to branch, and update PR — enabling systematic PR iteration.
model: { recommended: claude-opus-4-x, swappable: true }
inputs:
  - name: PR_NUMBER; required: true; note: GitHub PR number to process
  - name: REPO; required: true; note: owner/repo format
  - name: COMMENT_SOURCE; required: false; note: gh-api | email | webhook (default: gh-api)
  - name: HITL_GATE; required: false; note: whether human must approve fixes before push (default: true)
produces:
  - skills/pr-review-resolution/SKILL.md (+ scripts/, evals/)
  - emits at runtime: resolution_report.json (comment_id → fix_sha | deferred | wontfix)
depends_on: [framework.bootstrap@1.0.0, skill.build@1.0.0]
trajectory_strictness: ordered
hitl_gates: [human reviews generated fixes before push (configurable)]
tags: [skill, pr, review, automation, github, copilot]
---

# Skill: pr-review-resolution

## Role
You build the `pr-review-resolution` skill: an automated assistant that fetches review comments from a GitHub PR, categorizes them, generates code fixes, and pushes updates — closing the review-iteration loop.

## Intent (expanded)
Code review is a bottleneck. Copilot and human reviewers leave comments that often require mechanical fixes (style, imports, missing tests, typo corrections). This skill automates the fetch → categorize → fix → push cycle, with human-in-the-loop gates for judgment calls.

## Preconditions
- `gh` CLI authenticated with repo write access
- Target branch is `hermes/<topic>` (per BRANCH-MODEL.md)
- Repo has test suite (`python -m pytest` or equivalent)

## Inputs
`PR_NUMBER`, `REPO`, `COMMENT_SOURCE` (gh-api | email | webhook), `HITL_GATE` (bool)

## Procedure (runtime)
1. **Fetch comments** from source:
   - `gh-api`: `gh pr view <PR> --comments --json comments`
   - `email`: parse via `himalaya` IMAP (subject contains PR #)
   - `webhook`: receive from GitHub webhook payload
2. **Categorize** each comment:
   - `style` — formatting, naming, imports (auto-fixable via ruff/prettier)
   - `logic` — algorithm, control flow (needs LLM + tests)
   - `test` — missing/flaky tests (generate test case)
   - `docs` — docstrings, README, comments (auto-fixable)
   - `security` — secrets, vulns (escalate to human)
   - `design` — architecture, API shape (escalate to human)
3. **Resolve** each comment (per category):
   - Auto-fixable: run linter/formatter, generate patch via AST
   - LLM-fixable: prompt with context + comment, generate diff, run tests
   - Escalate: mark `deferred` with reason, notify human
4. **Commit & push** fixes to `hermes/<topic>` branch:
   - One commit per comment (or grouped by file)
   - Conventional commit msg: `fix: resolve PR-<n> comment <id> — <summary>`
5. **Update PR**: push branch, `gh pr edit` with resolution summary
6. **Emit report**: `resolution_report.json` mapping comment_id → fix_sha | deferred | wontfix

## Building the skill (your task now)
- Write `SKILL.md` with pushy description ("Use whenever a PR has review comments pending resolution…")
- Put fetch/categorize/resolve logic in `scripts/` (deterministic where possible)
- Keep body < 500 lines
- Add **eval**: given fixture PR comments, assert categorization accuracy ≥ 0.9, auto-fixes compile + pass tests, git ops succeed

## Deliverables
`skills/pr-review-resolution/{SKILL.md, scripts/, evals/}`

## Acceptance criteria
- AC-1: Fetches comments from gh API for a real PR
- AC-2: Categorizes 5 comment types with ≥ 90% accuracy on fixture
- AC-3: Auto-fixes (style/docs) apply cleanly, tests pass
- AC-4: LLM fixes generate valid diffs, tests pass
- AC-5: Commits pushed to correct branch, PR updated
- AC-6: Human gate respected (configurable)
- AC-7: Unknown comment types → `deferred`, never fabricated

## Trajectory
`fetch → categorize → resolve → commit → push → report`. Strictness: `ordered`.

## Self-improvement hook
If categorization accuracy drops below threshold on 3+ PRs, propose category taxonomy update via PR to this skill.

## Execution command
> Build the `pr-review-resolution` skill per this entry. Validate against fixture PR comments. Open a PR referencing `skill.pr-review-resolution@1.0.0`.