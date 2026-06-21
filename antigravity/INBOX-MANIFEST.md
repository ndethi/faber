# `_inbox/` Manifest

The exact files required to bootstrap the framework. **These are the only artifacts `build.00` consumes.** Distributed in `faber-framework-v0.2.zip` alongside `CHECKSUMS.txt` for byte-exact verification (see `SETUP.md` §4). The Rohaki fixture is *not* in this list — it belongs to step 06 and you supply it then (see `AGY-PROMPTS.md` step 06).

## Required files (18 total)

### Top-level (4)
- `FRAMEWORK.md`
- `INTERFACE.md`
- `IDENTITY.md`
- `RUNBOOK.md` *(harness-agnostic overview — useful but optional; if absent, `build.00` skips it)*

### Prompt registry (6)
- `prompts/_registry.md`
- `prompts/framework.bootstrap.md`
- `prompts/skill.intent-collector.md`
- `prompts/skill.observe-feedback.md`
- `prompts/meta.skill-author.md`
- `prompts/app.client-portal.md`

### Build plan (8)
- `build-plan/README.md`
- `build-plan/build.00-init-foundations.md`
- `build-plan/build.01-core.md`
- `build-plan/build.02-lifecycle-ci.md`
- `build-plan/build.03-observe-feedback.md`
- `build-plan/build.04-meta-cost.md`
- `build-plan/build.05-client-portal.md`
- `build-plan/build.06-rohaki-fixture.md`

## Verification

After populating `_inbox/`, run:
```bash
find _inbox -type f | sort | wc -l
# expect 17 (if you skipped optional RUNBOOK.md) or 18

# expected layout
find _inbox -type f | sort
```
You should see exactly the files above, nothing else.

## What's NOT in `_inbox/`

- **No Rohaki fixture.** Building the framework does not require client context. The Rohaki materials (or any other client fixture) come in at step 06; they're a separate concern.
- **No skills, no orchestrator code, no CI workflow.** Those don't exist yet — they're produced by `build.01` onwards, not copied from `_inbox/`.
- **No `AGENTS.md`.** The bootstrap `AGENTS.md` you hand-write in setup §5 lives at the workspace root, *not* in `_inbox/`. `build.00` then writes the canonical one over it.
