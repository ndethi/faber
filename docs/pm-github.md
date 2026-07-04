# pm-github Skill — Human Operator Guide

> **pm-github** is a Faber framework skill that owns all GitHub project-management operations. This guide covers installation, configuration, and common workflows for human operators.

---

## Quick Start

### Prerequisites

```bash
# Install gh CLI (GitHub CLI)
brew install gh          # macOS
# or: sudo apt install gh  # Ubuntu/Debian
# or: winget install GitHub.cli  # Windows

# Authenticate
gh auth login

# Verify access to your repo
gh repo view owner/repo
```

### Verify Configuration

```bash
# From repo root
python skills/pm-github/scripts/cli.py verify-config --config .github/pm-config.yaml
```

Expected output:
```
✅ PM-GitHub Config Verification
==================================================
✅ Configuration is valid
   Repository: owner/repo
   Labels: 18 defined
   Project: Faber Project Board
```

---

## Configuration

### 1. Create repo config (one-time)

```bash
# Copy example and customize
cp .github/pm-config.yaml.example .github/pm-config.yaml
# Edit .github/pm-config.yaml with your repo, labels, project settings
```

Key settings to customize:
- `github.repo` — **required**: your `owner/repo`
- `labels.taxonomy` — add project-specific labels (area:*, team:*, etc.)
- `project.owner` — GitHub user/org that owns the Project v2
- `project.fields` / `views` — customize fields and views

### 2. Configuration resolution

```
Skill defaults (skills/pm-github/config/defaults.yaml)
    ↓ merged over
Repo config (.github/pm-config.yaml) — if exists
    ↓ overridden by
CLI flags (--dry-run, --repo, etc.)
```

---

## Common Workflows

### 1. Dry-run: see what would happen

```bash
# Classify PR #123 review comments and generate proposals
python skills/pm-github/scripts/cli.py plan --pr 123

# Sync labels (dry-run)
python skills/pm-github/scripts/cli.py sync-labels

# Bootstrap project (dry-run)
python skills/pm-github/scripts/cli.py bootstrap-project
```

All commands default to `--dry-run`. Nothing is written to GitHub.

### 2. Apply approved proposals

```bash
# After reviewing a proposal batch comment on a PR
python skills/pm-github/scripts/cli.py apply --batch-id pm-20240115-abc123 --no-dry-run
```

This creates the actual issues with dedup protection (won't duplicate).

### 3. Sync label taxonomy

```bash
# Create/update labels to match config
python skills/pm-github/scripts/cli.py sync-labels --apply
```

- New labels → created
- Existing labels with different color/description → updated
- Labels not in config → **left alone** (never deleted)

### 4. Bootstrap a GitHub Project v2

```bash
# Create project with standard fields and views
python skills/pm-github/scripts/cli.py bootstrap-project --apply
```

Creates:
- Project v2 with title/description from config
- Fields: Status, Priority, Severity, Type, Target Release, Epic
- Views: By Status (Board), By Priority (Table), By Type (Table), All Issues

### 5. Generate release notes

```bash
# Propose release v1.2.0 with notes from merged PRs
python skills/pm-github/scripts/cli.py propose-release --tag v1.2.0
```

---

## GitHub Actions Integration

### PR Comment Sync (Automatic)

The `.github/workflows/pm-sync.yml` workflow runs on every PR review comment:

1. **Triggers**: `pull_request_review_comment` (created, edited)
2. **Classifies** all review comments on the PR
3. **Posts a proposal comment** with "would create N issues; approve to materialize"
4. **Never applies** — human must run `pm-github apply` manually

### Viewing Proposals

On any PR with review comments, look for a comment from the workflow bot:

```
## 🤖 PM-GitHub Proposal Batch: `pm-20240115-143022-a1b2c3d4`

### Proposed Issues

#### 1. 🔴 🐛 Fix critical auth bypass
**Severity:** Critical  **Type:** security  **Confidence:** 90%
**Dedup Key:** `a1b2c3d4e5f67890`
**Source Comment:** `1234567890`

**Labels:** `critical`, `security`, `bug`

**Body:**
SECURITY: Authentication bypass allows admin access...

---
### Actions
> **This is a proposal only.** No issues have been created.
> To approve: `pm-github apply --batch-id pm-20240115-143022-a1b2c3d4 --no-dry-run`
```

### Applying Proposals

1. Review the proposed issues in the PR comment
2. If approved, run locally:
   ```bash
   pm-github apply --batch-id pm-20240115-143022-a1b2c3d4 --no-dry-run
   ```
3. Or use the future `pm-apply.yml` workflow (workflow_dispatch gated)

---

## Classification Rules (Deterministic)

The skill uses **keyword rubrics** — no LLM calls. Same input → same output.

### Severity Keywords

| Severity | Keywords (case-insensitive) |
|----------|----------------------------|
| **Critical** | crash, data loss, security vulnerability, rce, sql injection, xss, auth bypass, privilege escalation, production outage, blocker, p0 |
| **High** | broken, fails, major bug, performance regression, accessibility, memory leak, core functionality |
| **Medium** | (default) missing error handling, inconsistent naming, consider adding, should split |
| **Low** | nit, nitpick, style, formatting, whitespace, typo, unused import, simplify |

### Type Keywords

| Type | Keywords |
|------|----------|
| **security** | security, vulnerability, injection, xss, csrf, auth, secret, credential |
| **bug** | bug, error, exception, crash, fail, broken, regression, incorrect |
| **enhancement** | enhancement, feature, improve, add, support, implement, extend |
| **documentation** | doc, documentation, readme, typo, comment, example |
| **refactor** | refactor, restructure, cleanup, simplify, extract, technical debt |

### Non-Actionable (Ignored)

Comments matching these patterns produce **no proposals**:
- Pure approvals: `LGTM`, `looks good`, `approved`, `ship it`, `👍`
- Questions: `why did you...`, `what's the...`, `curious about...`
- Discussions: `discuss`, `opinion`, `prefer`, `consider`, `suggest`

### Ambiguous → Safe Defaults

If a comment is actionable but matches no keywords:
- **Severity**: `Medium` (never `Critical`/`High` by guess)
- **Type**: `needs-triage` (human must review)

---

## Dedup & Idempotency

Every proposed issue carries a **dedup key**:
```
dedup-key: `sha256(source_repo:pr_number:comment_id)[:16]`
```

- Re-running `apply` on the same batch **never duplicates** issues
- Existing issues with the same dedup key are skipped with a notice
- Audit log: `runs/hermes/pm-log.jsonl` records every operation

---

## Audit Log

All operations (dry-run and live) append to `runs/hermes/pm-log.jsonl`:

```json
{"timestamp": "2024-01-15T14:30:22Z", "operation": "create_issue", "details": {"title": "Fix bug", "labels": ["bug"]}, "dry_run": true, "repo": "owner/repo"}
{"repo"}
```

Use for compliance, debugging, and retrospective analysis.

---

## Extending the Skill

### Add Custom Labels

Edit `.github/pm-config.yaml`:

```yaml
labels:
  taxonomy:
    - name: "area:payments"
      color: "FF6B6B"
      description: "Payments subsystem"
    - name: "team:backend"
      color: "4ECDC4"
      description: "Backend team ownership"
```

Then run:
```bash
pm-github sync-labels --apply
```

### Add Custom Project Fields

```yaml
project:
  fields:
    - name: "Team"
      type: "SINGLE_SELECT"
      options: ["Platform", "Product", "Design"]
    - name: "Sprint"
      type: "TEXT"
```

Then run:
```bash
pm-github bootstrap-project --apply
```

### Add Custom Views

```yaml
project:
  views:
    - name: "By Team"
      type: "TABLE"
      group_by: "Team"
    - name: "Sprint Board"
      type: "BOARD"
      group_by: "Status"
      filters:
        - field: "Sprint"
          operator: "IS_NOT_EMPTY"
```

---

## Troubleshooting

### "gh CLI not found"
```bash
brew install gh  # or apt/winget
gh auth login
```

### "Repository not configured"
```bash
# Ensure .github/pm-config.yaml exists with github.repo set
cat .github/pm-config.yaml | grep repo
```

### "Proposal batch not found"
```bash
# List all proposal batches
ls runs/hermes/pm-proposals/
# Or check the PR comment for the batch ID
```

### "Permission denied creating issues"
- Ensure `GITHUB_TOKEN` has `issues:write` permission
- For workflows: check `permissions:` block in `.github/workflows/pm-sync.yml`
- For local: `gh auth status` should show `write` access to repo

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    pm-github Skill                          │
├─────────────────────────────────────────────────────────────┤
│  CLI (cli.py)          → Entry point, command dispatch     │
│  GitHubClient          → gh CLI wrapper, dry-run enforcement │
│  Classify              → Deterministic rubric classification│
│  Dedup                 → SHA256 keys, existence checks      │
│  Proposals             → JSON + Markdown artifacts          │
│  Config                → YAML merge (skill → repo → CLI)    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub (via gh CLI)                       │
│  Issues, Labels, Projects v2, Releases, PR Comments         │
└─────────────────────────────────────────────────────────────┘
```

**Invariant**: Every write path requires `dry_run=False` explicitly. Default is `True`.

---

## See Also

- [FRAMEWORK.md §12](../FRAMEWORK.md) — Design rationale
- [AGENTS.md §2.11](../AGENTS.md) — Operating rules
- `skills/pm-github/config/defaults.yaml` — All defaults with comments
- `.github/pm-config.yaml.example` — Repo config template
- `runs/hermes/pm-log.jsonl` — Audit log (after operations)