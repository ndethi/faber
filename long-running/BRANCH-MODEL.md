# Branch Model — Faber

Three-tier flow. **`main` is production**, **`dev` is integration**, **`hermes/<topic>` are working branches**.

```
hermes/<topic>     →    dev    →    main
   (work)             (integration)   (production)
```

## The rules

1. **`main`** receives merges only from `dev`, via human-reviewed promotion PRs. Never from a topic branch. No agent (Hermes or otherwise) opens PRs to `main` directly.

2. **`dev`** receives merges from `hermes/<topic>` branches, via human-reviewed PRs. No direct commits.

3. **`hermes/<topic>`** branches are created freely by Hermes (or by humans). Each branch carries one logical change and one PR. The PR's base is **always `dev`**, never `main`.

4. **`hermes/brief`** is the single special branch that holds `long-running/HERMES-BRIEF.md`. It merges into `dev` once on first publish, and updates only via further PRs from `hermes/brief-v<n>` or `hermes/brief-update-<topic>`.

5. **`expedited`** is archived. It was the prior working trunk; its contents have been consolidated into `dev`. Treat it as a tag, not a branch — read-only, no new commits.

## Why three tiers (and not two)

- A pure `main` ← `topic` model means every Hermes PR is a production-readiness decision. Too high a stakes-per-decision; the human reviewer becomes a bottleneck.
- Inserting `dev` lets Hermes ship integration work continuously (PRs into `dev`) while `dev → main` is a deliberate, infrequent promotion gate the human chooses when to pull.
- It also lets you batch a set of Hermes PRs on `dev`, verify them together (a "release candidate" snapshot), and promote that snapshot to `main` once — rather than promoting each topic individually.

## Promotion: `dev → main`

This is the only path to production. It's a human action.

```bash
git fetch --all
git checkout main
git pull
git merge --no-ff dev          # or: gh pr create --base main --head dev --title "release: <date> snapshot"
# CI runs against main; if green, deploy
git push origin main
```

Tag the promotion (suggested):
```bash
git tag -a "v$(date +%Y.%m.%d)" -m "promotion: <one-line summary>"
git push origin --tags
```

## Hermes's relationship to this model

- It reads `BRANCH-MODEL.md` at the start of every session (per the brief's §0.3 anchor list).
- It never sets a PR base to `main` — every `gh pr create` includes `--base dev`.
- It treats new commits to `expedited` as a constraint violation (§1.1) — surfaces, does not "tidy."
- If `dev` doesn't exist when Hermes wakes up, it halts and notifies. Branch consolidation is a human operation (see `BRANCH-CONSOLIDATION.md`).

## What this changes for the human reviewer

- Reviews happen at two levels now: per-PR (Hermes → dev) and per-promotion (dev → main).
- Per-PR reviews can be lighter — failing in `dev` is recoverable.
- Promotion reviews are the production gate — apply the most scrutiny here. Look at the *cumulative diff* `git log main..dev` since the last promotion, not just the latest PR.
- Tagging promotions makes rollback to a known-good production state trivial: `git reset --hard <tag>`. - branch model
# Updated via HERMES brief sync on 2026-06-27 18:35:18 UTC
