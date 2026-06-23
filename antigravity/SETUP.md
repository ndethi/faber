# Antigravity CLI (`agy`) — Setup from Zero

> Verified against June 2026 `agy` behaviour. The CLI moves fast — run `agy --help` and `agy changelog` before scripting against any flag here.
>
> This walks you from **a blank machine and an empty directory** to a state where the build prompts in `AGY-PROMPTS.md` will run safely. Nothing is assumed: you'll install `agy`, populate `_inbox/`, make `agy` see your rules, and **verify** all of that before running anything.

---

## 0. What you need before starting

- A unix-like terminal (macOS / Linux / WSL).
- A Google account (for `agy` sign-in).
- A GitHub account + the `gh` CLI installed (so the agent can open PRs without you leaving the terminal).
- An **Anthropic API key** if you want to switch `agy` to Claude for the reasoning-heavy steps. Optional but recommended for steps 01, 03, 04.

The build artifacts (the files going into `_inbox/`) are the framework files we produced — see **`INBOX-MANIFEST.md`** for the exact list (17–18 files: top-level docs, the prompt registry + 5 entries, and the build-plan README + 7 step files). Have them somewhere local — a download folder is fine. No client fixture is needed at this stage.

---

## 1. Install `agy`

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
# installs the agy binary into ~/.local/bin/agy
```

Make sure `~/.local/bin` is on your `PATH` (add to `.zshrc` / `.bashrc` if not):
```bash
export PATH="$HOME/.local/bin:$PATH"
agy --version          # confirm install
agy --help             # see real flags for YOUR version (this changes often)
```

## 2. Sign in

```bash
agy                    # first launch → choose 1. Google OAuth → browser opens → paste the code back
```
- On a local machine, this opens your browser. Over SSH, it prints a URL + one-time code.
- Optional: pick a colour theme when prompted.

If you'd rather use an API key (for CI later):
```bash
export ANTIGRAVITY_API_KEY="$(cat /path/to/key)"   # never pass as a CLI arg
```

## 3. Create the project directory

```bash
mkdir -p ~/projects/faber
cd ~/projects/faber
git init
git commit --allow-empty -m "chore: empty repo, rollback anchor"
```

That empty commit is your **rollback anchor**. If any agent run goes sideways, `git reset --hard <that sha>` puts you back at zero.

## 4. Populate `_inbox/` (download → unzip → verify)

`_inbox/` is the staging area `build.00` copies from byte-for-byte. The artifacts are bundled in **`faber-framework-v0.2.zip`** (the file shared alongside this guide) with `CHECKSUMS.txt` for byte-exact verification. `INBOX-MANIFEST.md` is the canonical inventory.

> **Why download, not regenerate.** Re-deriving these files from a prompt would defeat the purpose — `_inbox/` exists *because* canonical artifacts shouldn't be regenerated each run. The bundle is the source of truth; the checksums prove integrity.

```bash
# 1) put the bundle into the workspace, unzip into _inbox/
cp ~/Downloads/faber-framework-v0.2.zip .
unzip faber-framework-v0.2.zip -d _staging
mkdir -p _inbox
# move only the bootstrap artifacts (drop the antigravity/ companion docs — they live alongside, not in _inbox)
cp _staging/agentic-web-framework/FRAMEWORK.md            _inbox/
cp _staging/agentic-web-framework/INTERFACE.md            _inbox/
cp _staging/agentic-web-framework/IDENTITY.md             _inbox/
cp _staging/agentic-web-framework/RUNBOOK.md              _inbox/   # optional
cp _staging/agentic-web-framework/CHECKSUMS.txt           _inbox/
cp -r _staging/agentic-web-framework/prompts              _inbox/
cp -r _staging/agentic-web-framework/build-plan           _inbox/

# 2) keep the companion docs (SETUP / AGY-PROMPTS / INBOX-MANIFEST) at the workspace root for reference
cp -r _staging/agentic-web-framework/antigravity .
rm -rf _staging faber-framework-v0.2.zip

# 3) verify the bundle landed intact (byte-exact)
( cd _inbox && sha256sum -c CHECKSUMS.txt --ignore-missing )
# every line must end with "OK". if any line says "FAILED", STOP — your bundle is corrupt or tampered with.
```

The `--ignore-missing` flag lets the same `CHECKSUMS.txt` cover both the `_inbox/` files and the companion docs without complaining about the ones not under `_inbox/`. To check the companions too:
```bash
( cd antigravity && sha256sum -c ../_inbox/CHECKSUMS.txt --ignore-missing )
```

Sanity-check the inventory against the manifest:
```bash
find _inbox -type f -name "*.md" | sort
# expect 17 (without RUNBOOK) or 18 markdown files matching INBOX-MANIFEST.md
```

Ignore `_inbox/` and the staging dir in git so they don't end up in commits — `build.00` copies *out of* `_inbox/` into the real tree:
```bash
printf "_inbox/\n_staging/\n*.zip\n" >> .gitignore
git add .gitignore && git commit -m "chore: ignore staging artifacts"
```

### 4b. Belt-and-braces: have `agy` re-verify before any work

Even if the shell `sha256sum` passed, run this once inside the `agy` TUI so the agent re-confirms in its own context before step 00:

```text
Verify the _inbox/ bundle is intact before I run any build step.
1. Read _inbox/CHECKSUMS.txt.
2. For each file listed under _inbox/ in the checksum file, compute its SHA-256 from disk and compare to the expected hash.
3. Report PASS/FAIL per file. If anything fails, STOP and tell me which file — do not attempt to "fix" it.
4. Also list any files present under _inbox/ that are NOT in CHECKSUMS.txt (unexpected extras), and any expected files that are missing.
Do not modify anything. This is a read-only verification.
```

Only proceed past this point if every checksum is `OK` and the file inventory matches `INBOX-MANIFEST.md`.

> **Rohaki and other client fixtures** are *not* in this bundle. Step 06 (`AGY-PROMPTS.md`) tells you to place client context into `fixtures/<client>/` immediately before running the scaling test. Until then, the framework builds and verifies on its own.

## 5. Write the workspace constitution (`AGENTS.md`)

`agy` natively reads `AGENTS.md` from the workspace root at session start (since v1.20.3, March 2026). We write a **minimal `AGENTS.md` now** to govern the bootstrap itself. After `build.00` runs, the canonical `AGENTS.md` replaces it.

```bash
cat > AGENTS.md <<'EOF'
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
EOF

git add AGENTS.md && git commit -m "chore: bootstrap AGENTS.md"
```

## 6. **Verify** `agy` sees the workspace and the rules

This is the step that catches the "I assumed it was loaded" failure. Run `agy` from the project root and use its own inspection commands.

```bash
cd ~/projects/faber
agy
```

In the TUI, when prompted, **trust the folder** ("Yes, I trust this folder"). Then:

```text
/config         # confirm the workspace path is ~/projects/faber
/context        # confirm AGENTS.md appears in the loaded context
```

If your `agy` version has it (recent builds do), also run:
```text
/btw            # then ask: "Run agy inspect" — or exit and run it from the shell:
```
```bash
# from shell (outside the TUI)
agy inspect     # lists the configuration files loaded (AGENTS.md should be among them)
```

If `AGENTS.md` is **not** listed:
- Confirm `agy --version` is ≥ 1.20.3 (native AGENTS.md support).
- Try also creating `.antigravity.md` as a same-content fallback (`cp AGENTS.md .antigravity.md`); on newer builds it takes precedence over `GEMINI.md`. Restart `agy`.
- Last resort: copy the body into `GEMINI.md` (legacy name, fully supported for backward compatibility).

Do not proceed until `agy inspect` (or `/context`) shows the constitution is loaded.

## 7. Set permissions to keep humans in the loop

In the TUI:
```text
/settings       # or /config
```
Set / confirm:
- Approval mode: **request-review** (the agent asks before writes/commands).
- `allowNonWorkspaceAccess`: **false**.
- Optional: `enableTerminalSandbox`: **true** (or launch with `--sandbox`).
- **Do not** enable `--dangerously-skip-permissions`.

Verify with a deliberate trip-wire:
```text
> Create a file called probe.txt with the content "hello".
```
You should see a permission prompt (or `/diff` preview) before anything is written. Decline. If it wrote without asking, your settings aren't active — fix before continuing.

## 8. Pick your model (and know the quota)

```text
/model          # shows current model + lets you switch
/models         # list available (e.g. Gemini 3 Pro/Flash, Claude Opus/Sonnet, GPT-OSS variants)
/usage          # current quota usage — KEEP AN EYE ON THIS
```

- Routine steps (`build.00`, scaffolding, dashboard, portal): **Gemini 3 Pro / Flash**.
- Reasoning-heavy (`build.01` intent-collect, `build.03` trajectory-guard/feedback, `build.04` skill-author, `build.06` Rohaki intent): switch with `/model` to **Claude** (requires your Anthropic key in `/settings`).
- The hosted **GPT-OSS** is the same open-weights family you'll later self-host (gpt-oss / Nemotron on DGX / DGX Spark) — useful for `build.04` rehearsal.
- **Quota is shared across CLI / desktop / SDK and the agent can't self-throttle.** Cap parallel subagents at 3–5; run `/grill-me` before expensive steps so it plans before it spends.

## 9. Quick reference (the slash commands you'll actually use)

`/grill-me` (plan before spend) · `/diff` (review changes) · `/context` (what's loaded) · `/config` `/settings` · `/model` `/models` · `/usage` (quota) · `/agents` (subagents — Ctrl+J review, Ctrl+K approve) · `/browser` (UI verification) · `/btw` (sidequestion without context bloat) · `/resume` (reopen a session) · `/rewind` `/undo` (roll back the conversation) · `!` (shell mode toggle) · **Ctrl+R** (Artifact Review Panel).

---

## You're ready when…

- [ ] `agy --version` prints, and you've run `agy --help` and `agy changelog` for your version.
- [ ] You're signed in (Google OAuth completed).
- [ ] `~/projects/faber` exists with an empty-commit rollback anchor.
- [ ] `_inbox/` is fully populated per `INBOX-MANIFEST.md`; `find _inbox -type f | wc -l` shows 17 or 18.
- [ ] `.gitignore` ignores `_inbox/`.
- [ ] `AGENTS.md` (bootstrap version) exists in the workspace root.
- [ ] `agy inspect` (or `/context`) **confirms `AGENTS.md` is loaded** — this is non-negotiable.
- [ ] Permission mode is `request-review`; the probe in §7 was blocked as expected.
- [ ] You know your current model and have `/usage` open in your head.

Now go to **`AGY-PROMPTS.md`** and run `build.00` first.
