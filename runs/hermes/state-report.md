# Hermes State Report - 2026-06-25 22:55:58

# Hermes State Report

## Git Snapshot

### Current Branch
hermes/state-report

### Last 20 Commits (HEAD)
3b9aac5 Merge pull request #4 from ndethi/update-hermes-brief-actual
9a2a830 feat: replace Hermes brief placeholder with actual operating contract
0b11d69 Merge pull request #3 from ndethi/update-hermes-brief
b0f1be0 docs: update Hermes brief placeholder with clearer instructions
7ea34b3 Merge pull request #2 from ndethi/update-brief-2
d47075c docs: replace placeholder branch model with actual content from user
9caa820 docs: replace placeholder Hermes brief and branch model with explicit instructions to replace from local outputs
aaac025 Merge pull request #1 from ndethi/hermes/brief
197e439 feat: add hermes brief and branch model under long-running/ (placeholder)
f88240b feat: add feedback, trajectory‑guard, and dashboard skills
658ce99 feat: observe skill – capture run telemetry
bcbc887 chore: add expedited AGENTS.md for bootstrap
47e6c55 feat: lifecycle skills + gated CI

### All Branches
  dev
  expedited-bootstrap
  feat/build-skill
  feat/build-skill-fix
  feat/deploy-skill
* hermes/state-report
  lifecycle-skills-ci
  main
  master
  step02/build-skill
  update-brief
  remotes/origin/dev
  remotes/origin/hermes/brief
  remotes/origin/lifecycle-skills-ci
  remotes/origin/main
  remotes/origin/step02/build-skill
  remotes/origin/update-brief-2
  remotes/origin/update-hermes-brief
  remotes/origin/update-hermes-brief-actual

### Uncommitted Changes
?? .github/
?? AGENTS.backup.md
?? runs/hermes/
?? skills/skill-author/

## Top-level Documents

## Top-level Documents

- README.md: EXISTS
- AGENTS.md: EXISTS
- FRAMEWORK.md: EXISTS
- INTERFACE.md: EXISTS
- IDENTITY.md: EXISTS
- RUNBOOK.md: EXISTS
- CLAUDE.md: EXISTS

### AGENTS.md Audit
- Appears to be BOOTSTRAP version (references _inbox/)

### AGENTS.md Audit
- Appears to be BOOTSTRAP version (references _inbox/)

#### Human Additions (if any)
- - **Commit Style Enforcement** – All commits that introduce a *significant feature* or a *bug fix* must conform to the Commitizen spec (e.g., `feat:` for features, `fix:` for bug fixes). Enforce via a pre‑commit hook (`cz check`) or CI validation.
- # Commit & Pull‑Request Policy
- - All commits that introduce a **significant feature** or a **bug‑fix** must follow the **Commitizen** convention (e.g., `feat:`, `fix:`, `chore:`, etc.) and include a concise, descriptive subject line.
- # Commit & Pull‑Request Policy (expedited)
- - **Commit Style Enforcement** – All commits that introduce a *significant feature* or a *bug fix* must conform to the Commitizen spec (e.g., `feat:` for features, `fix:` for bug fixes). Enforce via a pre‑commit hook (`cz check`) or CI validation.

## Skill Inventory

Checking skills/ directory:
total 0
drwxr-xr-x  15 ndethi  staff  480 Jun 23 06:21 .
drwxr-xr-x  22 ndethi  staff  704 Jun 25 21:39 ..
drwxr-xr-x   6 ndethi  staff  192 Jun 23 20:44 build
drwxr-xr-x   4 ndethi  staff  128 Jun 23 22:32 dashboard
drwxr-xr-x   5 ndethi  staff  160 Jun 23 00:27 deploy
drwxr-xr-x   5 ndethi  staff  160 Jun 23 06:21 evaluate
drwxr-xr-x   4 ndethi  staff  128 Jun 23 22:34 feedback
drwxr-xr-x   2 ndethi  staff   64 Jun 21 23:21 model-route
drwxr-xr-x   3 ndethi  staff   96 Jun 23 22:10 observe
drwxr-xr-x   3 ndethi  staff   96 Jun 23 22:08 publish
drwxr-xr-x   5 ndethi  staff  160 Jun 23 06:21 scaffold
drwxr-xr-x   2 ndethi  staff   64 Jun 21 23:21 scope-ledger
drwxr-xr-x   3 ndethi  staff   96 Jun 23 22:18 skill-author
drwxr-xr-x   4 ndethi  staff  128 Jun 21 23:34 trace-missing-canonical
drwxr-xr-x   4 ndethi  staff  128 Jun 23 22:34 trajectory-guard

### Skill Details
#### build
- SKILL.md: EXISTS
- scripts/: EXISTS
- evals/: MISSING
  First few lines of SKILL.md:
    ---
    name: build
    description: |
      Compiles source files, bundles assets, and produces the final artifact for a Faber component. The skill is deterministic, runs locally with the same configuration each time, and outputs a summary of generated files.
    version: 1.0.0

#### dashboard
- SKILL.md: EXISTS
- scripts/: EXISTS
- evals/: MISSING
  First few lines of SKILL.md:
    # Dashboard Skill
    
    > Generates a simple HTML dashboard aggregating run observations and feedback.
    
    ## Overview

#### deploy
- SKILL.md: MISSING
- scripts/: EXISTS
- evals/: MISSING

#### evaluate
- SKILL.md: MISSING
- scripts/: EXISTS
- evals/: MISSING

#### feedback
- SKILL.md: EXISTS
- scripts/: EXISTS
- evals/: MISSING
  First few lines of SKILL.md:
    # Feedback Skill
    
    > Collects user feedback after each run and stores it as `feedback.json`.
    
    ## Overview

#### model-route
- SKILL.md: MISSING
- scripts/: MISSING
- evals/: MISSING

#### observe
- SKILL.md: EXISTS
- scripts/: MISSING
- evals/: MISSING
  First few lines of SKILL.md:
    # Observe Skill
    
    ## Description
    Collects telemetry data from each run and stores it in `runs/<run_id>/observations.json`.
    

#### publish
- SKILL.md: MISSING
- scripts/: EXISTS
- evals/: MISSING

#### scaffold
- SKILL.md: MISSING
- scripts/: EXISTS
- evals/: MISSING

#### scope-ledger
- SKILL.md: MISSING
- scripts/: MISSING
- evals/: MISSING

#### skill-author
- SKILL.md: MISSING
- scripts/: EXISTS
- evals/: MISSING

#### trace-missing-canonical
- SKILL.md: EXISTS
- scripts/: MISSING
- evals/: MISSING
  First few lines of SKILL.md:
    ---
    name: trace-missing-canonical
    description: Detects when canonical files from `_inbox/` are missing or have been altered during a build step. It runs a diff between `_inbox/` and the corresponding repository locations, reports any mismatches, and fails the step if drift is found.
    ---
    

#### trajectory-guard
- SKILL.md: EXISTS
- scripts/: EXISTS
- evals/: MISSING
  First few lines of SKILL.md:
    # Trajectory‑Guard Skill
    
    > Enforces that each run’s telemetry matches the baseline `trajectory.md`.
    
    ## Overview


## Orchestrator + Telemetry
- orchestrator/: EXISTS
- runs/telemetry.schema.json: EXISTS
  Content:
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "Telemetry Record",
      "type": "object",
      "required": ["run_id", "timestamp", "skills", "model", "tokens", "cost", "deploy_status"],
      "properties": {
        "run_id": { "type": "string", "description": "Unique identifier for the run (UUID or similar)." },
        "timestamp": { "type": "string", "format": "date-time", "description": "Run start timestamp in ISO‑8601 format." },
        "skills": {
          "type": "array",
          "description": "Ordered list of skill executions.",
          "items": {
            "type": "object",
            "required": ["skill_id", "status", "duration_ms"],
            "properties": {
              "skill_id": { "type": "string" },
              "status": { "type": "string", "enum": ["success", "failure", "skipped"] },
              "duration_ms": { "type": "integer", "minimum": 0 }
            }
          }

## CI
- .github/workflows/ci.yml: EXISTS
  Content (first 30 lines):
    name: CI
    
    on:
      pull_request:
        branches: [ main ]
      push:
        branches: [ main ]
    
    jobs:
      guard:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.11'
          - name: Install dependencies
            run: pip install --quiet jsonschema
          - name: Run trajectory‑guard
            run: |
              python skills/trajectory-guard/scripts/guard.py
            # The script exits non‑zero on drift, which fails the job.
    
      dashboard:
        if: github.event_name == 'push'
        runs-on: ubuntu-latest
        needs: guard
        steps:
          - uses: actions/checkout@v3

## Portal (app/)
- app/: MISSING

## _inbox/ and build-plan/
- _inbox/: EXISTS
CHECKSUMS.txt
FRAMEWORK.md
IDENTITY.md
INTERFACE.md
RUNBOOK.md
build-plan
prompts
- build-pan/: EXISTS
build-plan

## Divergences from FRAMEWORK.md (placeholder - to be filled after review)
- FRAMEWORK.md exists. Need to compare with actual repo state.

