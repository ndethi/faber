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

After `build.00` completes, replace this file with the canonical AGENTS.md it generates.
