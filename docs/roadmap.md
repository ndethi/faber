# Faber Framework Roadmap

**Single Source of Truth for milestones and project tracking.** This file is the authoritative source — GitHub Projects, Milestones, and Issues are derived from here. Edit this file to change the roadmap; automation syncs downstream.

---

## Milestones

### v0.3.0 — Lifecycle Skills Complete
**Target:** 2026-07-15 | **Status:** In Progress

| ID | Title | Type | Priority | Severity | Status | Epic |
|----|-------|------|----------|----------|--------|------|
| BG-006 | _inbox/ & build-plan persistence | Enhancement | Medium | Medium | Backlog | Core Framework |
| BG-007 | CI workflow per build-plan | Enhancement | Medium | Medium | Backlog | Core Framework |
| BG-009 | Eval audit: no skill without eval | Refactor | Low | Low | Backlog | Quality |
| BG-010 | AGENTS.md vs FRAMEWORK.md alignment | Docs | Low | Low | Backlog | Governance |

### v0.4.0 — Client Portal & Polish
**Target:** 2026-08-15 | **Status:** Planned

| ID | Title | Type | Priority | Severity | Status | Epic |
|----|-------|------|----------|----------|--------|------|
| BG-008 | Client portal (app.client-portal@0.1.0) | Enhancement | Medium | Medium | Backlog | Client Portal |
| BG-013 | PM Automation: Backlog → Project sync | Enhancement | High | High | In Progress | PM Automation |
| BG-014 | PM Automation: Release/tag automation | Enhancement | High | High | Planned | PM Automation |
| BG-015 | PM Automation: Label/Project sync | Enhancement | Medium | Medium | Planned | PM Automation |

### v1.0.0 — Production Ready
**Target:** 2026-09-30 | **Status:** Planned

| ID | Title | Type | Priority | Severity | Status | Epic |
|----|-------|------|----------|----------|--------|------|
| BG-016 | Multi-repo portfolio management | Enhancement | Medium | Medium | Backlog | PM Automation |
| BG-017 | Linear/Jira sync skill | Enhancement | Low | Low | Backlog | PM Automation |

---

## Backlog Items (Source: runs/hermes/backlog.md)

### High Priority
- **BG-006** — _inbox/ & build-plan persistence (Enhancement, Medium/Medium, Backlog, Core Framework)
- **BG-007** — CI workflow per build-plan (Enhancement, Medium/Medium, Backlog, Core Framework)

### Medium Priority
- **BG-009** — Eval audit: no skill without eval (Refactor, Low/Low, Backlog, Quality)
- **BG-010** — AGENTS.md vs FRAMEWORK.md alignment (Docs, Low/Low, Backlog, Governance)

### Completed (Reference)
- BG-001: AGENTS.md swap to canonical ✅
- BG-002: skills/build/ correction ✅
- BG-003: Orchestrator + telemetry ✅
- BG-004: Missing lifecycle skills (intent-collect done, others pending) 🔄
- BG-005: Cross-cutting skills (6/6 done) ✅
- BG-011: PR Review Resolution Skill ✅
- BG-012: PR Review Skill ✅

---

## Sync Rules

1. **Source of truth:** This file (`docs/roadmap.md`) is the only place to edit milestones, priorities, types, severities, statuses, and epics.
2. **Downstream sync:** GitHub Project v2 items, Milestones, and Issue labels are generated from this file via `pm-github sync-backlog-to-project`.
3. **Upstream feedback:** GitHub Issue status changes (e.g., moved to "In Progress", "In Review", "Done") are synced back to this file via `pm-github sync-project-to-roadmap` (future).
4. **Milestone mapping:** Each milestone in this file maps to a GitHub Milestone with the same title and due date.
5. **Field mapping:**
   - `Status` → Project single-select (Backlog, Ready, In Progress, In Review, Done)
   - `Priority` → Project single-select (Critical, High, Medium, Low)
   - `Severity` → Project single-select (Critical, High, Medium, Low)
   - `Type` → Project single-select (Bug, Enhancement, Docs, Refactor, Security, Needs Triage)
   - `Target Release` → Project text field (maps to Milestone)
   - `Epic` → Project text field (grouping label)

---

## Automation Triggers

| Workflow | Trigger | Action |
|----------|---------|--------|
| `pm-backlog-sync.yml` | Push to `dev`, schedule (daily) | Sync this file → GitHub Project v2 |
| `pm-release.yml` | Push to `main`, `workflow_dispatch` | Semantic version, tag, release notes, update this file |
| `pm-label-sync.yml` | Push to `dev` | Sync label taxonomy |
| `pm-project-bootstrap.yml` | `workflow_dispatch` | Bootstrap Project v2 for new repos |