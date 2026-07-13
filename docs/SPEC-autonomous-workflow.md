# Autonomous Idea‑to‑MVP Workflow Spec

## Purpose
Define an autonomous loop that uses the Faber framework lifecycle to turn ideas into MVP features, with human‑in‑the‑loop (HITL) only at PR merges to `dev` and `main`.

## Components
1. **Faber Iteration Loop** – runs every 15 minutes (configurable) via a cron job.
   - Anchors @AGENTS.md @FRAMEWORK.md @HERMES-BRIEF.md @STATE.json @backlog.md
   - Picks highest‑priority pending backlog item
   - Writes a 3‑5 line plan to `iteration-log.md`
   - Implements on a new `hermes/<topic>` branch from `dev`
   - Runs skill evals, build, lint, trajectory‑guard
   - Updates backlog (failed→high, judge<0.70→medium, pass→close)
   - Pushes branch and opens a PR targeting `dev`
   - Sends PR URL to Telegram (chat ID 7930912544) with “action‑required”
   - Stops; waits for human merge to `dev`.

2. **Deploy‑on‑Main Watcher** – runs every 5 minutes via cron.
   - Detects new Git tag matching `deploy-*` (created by a post‑merge hook on `main` or manually).
   - If a new tag is found and not yet processed, invokes the `astro-cloudflare-setup` skill to publish the `dist/` folder to Cloudflare Pages.
   - Records the tag in a marker file to avoid re‑deployment.

3. **Post‑Merge Hook (optional)** – When a PR is merged from `dev` to `main`, a `post-merge` hook tags the merge commit with `deploy-<timestamp>` and pushes the tag, triggering the deploy watcher.

## HITL Gates
- **PR `dev` ← `hermes/<topic>`**: Human reviews and merges (no auto‑merge).
- **PR `main` ← `dev`**: Human reviews and merges (no auto‑merge).
- The agent never pushes directly to `dev` or `main`; it only creates PRs.

## Artifacts (kept in the repo)
- `docs/SPEC-autonomous-workflow.md` – this specification.
- `scripts/faber_iteration.sh` – iteration loop script.
- `scripts/deploy_on_main.sh` – deploy watcher script.
- `logs/faber_cron.log`, `logs/deploy_cron.log` – execution logs (generated).
- `backlog.md`, `iteration-log.md`, `STATE.json` – Faber state files.
- Optional: `.git/hooks/post-merge` – tag generator.

## Assumptions
- The repository has `dev` and `main` branches.
- The `gh` CLI is authenticated with write access.
- Cloudflare API token and account ID are configured in the Hermes `exp` profile (`cloudflare.api_token`, `cloudflare.account_id`).
- The build output is located at `dist/` (configurable via `DIST_DIR` environment variable).
- The Telegram bot for the `exp` profile is already running and linked to chat ID 7930912544.

## How to Test
1. Ensure the `exp` profile is configured (model, provider, Cloudflare creds, Telegram bot).
2. Run the iteration script manually: `~/.../faber_iteration.sh` – it should create a PR.
3. Review and merge the PR into `dev`.
4. Verify the next iteration picks the next backlog item.
5. To test deployment, merge a PR from `dev` to `main` (or manually create a `deploy-` tag) and watch the deploy cron push to Cloudflare Pages.

## Extensibility
- Adjust cron intervals by editing the crontab entries.
- Add more sophisticated post‑merge hook to trigger tagging.
- Replace the deploy script with any other CI/CD target (e.g., Vercel, Netlify) by changing the Hermes skill invoked.

---

*This spec lives in the repo as the source of truth for the autonomous workflow. Any deviation from the documented behavior should be treated as a bug and addressed via a PR that updates this file and/or the supporting scripts.*