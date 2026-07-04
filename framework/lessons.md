# Framework Lessons Log

*Append-only log of lessons learned during Faber framework development.
Each entry documents a non-obvious discovery, a process improvement, or a rule clarification.
Referenced in PRs to capture institutional knowledge.*

---

## 2026-07-04: skill-author scaffold extension pattern

**Lesson:** `skill-author` produces a minimal scaffold; framework-scoped skills with multi-module implementations need explicit extension in the same PR.

**Context:** The `skill-author` meta-skill (FRAMEWORK.md §7) generates a complete but minimal skill structure: `SKILL.md`, a single flat `scripts/<name>.py`, and a basic `evals/test_<name>.py`. This satisfies the hard rules (eval present, dedup documented) but is insufficient for framework-scoped skills that require:
- Multiple script modules (`cli.py`, `github_client.py`, `classify.py`, `dedup.py`, `proposals.py`)
- Comprehensive eval suites (4+ test modules + fixtures)
- Configuration files (`config/defaults.yaml`, `.github/pm-config.yaml.example`)
- Bootstrap scripts (`scripts/bootstrap_project.py`)
- GitHub Actions (`.github/workflows/pm-sync.yml`)
- Framework wiring (AGENTS.md, FRAMEWORK.md, docs/)

**Rule:** When authoring a framework-scoped skill via `skill-author`, plan the scaffold extension *before* running the meta-skill, and reference this lesson in the PR body. The extension work happens on the same branch, in the same PR, so the framework docs reflect the complete skill on merge.

**Applied in:** `hermes/pm-github-skill` PR — `skill-author` created the scaffold; Hermes extended it with 5 script modules, 4 eval test files + fixtures, config, bootstrap, workflow, docs, and framework wiring.

**Prevention:** Without this rule, framework-scoped skills would land as minimal scaffolds requiring follow-up PRs, leaving the framework in an inconsistent state between merges.

---

*Add new entries above this line. Format: date, title, context, rule, applied-in.*