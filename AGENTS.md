# AGENTS.md (bootstrap-stage constitution)

You are building the Faber framework into this repo. Read these files before acting:
1. `_inbox/FRAMEWORK.md`  — design source of truth
2. `_inbox/INTERFACE.md`  — interface decision
3. `_inbox/IDENTITY.md`   — naming
4. `_inbox/prompts/`      — registry + entries
5. `_inbox/build-plan/`   — ordered build steps

Operating rules during bootstrap:
- The build-plan step referenced in the user's prompt is the spec for this turn. Execute it exactly.
- **Plan before edit.** Show the plan and wait for approval before any file write.
- **Persist `_inbox/` files byte-for-byte** in `build.00`. Never regenerate canonical artifacts.
- One build step at a time. For multi-skill steps, build one skill at a time with its own `/diff`, commit, and PR.
- Reference the registry `id@version` in every PR.
- Stop at any `HITL GATE` in the build-plan step until I approve.
- `git` is the source of truth. No state lives outside the repo.

- **Commit Style Enforcement** – All commits that introduce a *significant feature* or a *bug fix* must conform to the Commitizen spec (e.g., `feat:` for features, `fix:` for bug fixes). Enforce via a pre‑commit hook (`cz check`) or CI validation.

After `build.00` completes, replace this file with the canonical AGENTS.md it generates.
# Commit & Pull‑Request Policy

- All commits that introduce a **significant feature** or a **bug‑fix** must follow the **Commitizen** convention (e.g., `feat:`, `fix:`, `chore:`, etc.) and include a concise, descriptive subject line.
- PR titles should mirror the commit subject and reference the relevant skill or build‑plan step, e.g., `feat: orchestrator + telemetry + intent‑collect`.
- When the GitHub CLI (`gh`) is configured in the repository, PRs are created automatically via `gh pr create`. Otherwise, a reminder comment with the PR title and body will be left for the developer to open manually.
- The `AGENTS.md` file serves as the single source of truth for these conventions; any deviation should be opened as a GitHub issue and addressed with a dedicated “trace‑skill” in a later iteration.

