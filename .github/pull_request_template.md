# Pull Request Template

<!--
Faber Framework PR Template
All fields are mandatory unless marked optional.
Delete sections that don't apply.
-->

## Summary

**What:** <!-- One-line description of the change -->
**Why:** <!-- Link to issue, spec, or rationale -->
**How:** <!-- Brief technical approach -->

---

## Spec Traceability

| Spec Reference | Status |
|----------------|--------|
| FRAMEWORK.md § | ☐ Addressed / ☐ N/A |
| AGENTS.md § | ☐ Addressed / ☐ N/A |
| HERMES-BRIEF.md § | ☐ Addressed / ☐ N/A |
| Skill: `skills/<name>/SKILL.md` | ☐ Updated / ☐ N/A |
| SPEC-ID (if applicable) | `SPEC-XXX` |

---

## Pre-Merge Checklist (BG-018 Gate)

**All items must be ✅ before merge. Check each box manually.**

### Branch & Commit Hygiene
- [ ] Branch follows `hermes/<topic>` convention (from `dev`)
- [ ] All commits follow Conventional Commits (`type(scope): message`)
- [ ] No WIP/fixup commits in history (squashed)
- [ ] No direct commits to `dev` or `main`

### Code Quality
- [ ] All new/modified code has passing evals (`python -m pytest skills/<name>/evals/`)
- [ ] No `TODO:` or `FIXME:` left in production code (move to backlog if needed)
- [ ] No fabrication — unknowns documented as `TODO:` with Telegram surface
- [ ] Type hints added for new functions (Python) / JSDoc (TypeScript)

### Testing & Verification
- [ ] Evals pass locally: `python -m pytest skills/<name>/evals/ -v`
- [ ] Determinism verified: same inputs → same outputs
- [ ] Dry-run mode works (no accidental writes)
- [ ] HITL gate respected: no auto-merge, human review required

### PM & Governance
- [ ] `docs/roadmap.md` updated if milestone/item status changed
- [ ] `runs/hermes/backlog.md` updated with PR references
- [ ] pm-github config updated if label/project schema changed
- [ ] `.github/pm-config.yaml` present in repo (or skill defaults sufficient)

### Documentation
- [ ] SKILL.md updated if skill interface changed
- [ ] README/docs updated for user-facing changes
- [ ] CHANGELOG/release notes entry added (for releases)

### CI/CD
- [ ] Pre-push hook passes locally (`git push --dry-run`)
- [ ] GitHub Actions workflows pass (check PR checks)
- [ ] Adversarial review completed (different model than author)
- [ ] Human review completed (explicit LGTM/approve)

---

## Reviewer Guidelines

### Adversarial Review (Automated + Different Model)
- [ ] Logic errors / edge cases
- [ ] Security issues (injection, auth bypass, secrets)
- [ ] Spec violations (FRAMEWORK.md, AGENTS.md, skill contract)
- [ ] Missing tests / fabrication
- [ ] At least 1 issue found OR explicit approve with reasoning

### Human Review (You)
- [ ] Read the diff — understand the change
- [ ] Verify spec traceability table is accurate
- [ ] Confirm evals pass and cover the change
- [ ] Check no scope creep beyond linked issue/SPEC
- [ ] **Explicitly approve** — no auto-merge

---

## Deployment Notes (if applicable)

- **Environment:** staging / production
- **Migration needed:** yes / no
- **Rollback plan:** <!-- brief description -->
- **Feature flag:** <!-- flag name if applicable -->

---

## Related

- Closes: <!-- issue # -->
- Related PRs: <!-- #xxx -->
- Follow-up: <!-- #xxx or TODO -->