---
name: trace-missing-canonical
description: Detects when canonical files from `_inbox/` are missing or have been altered during a build step. It runs a diff between `_inbox/` and the corresponding repository locations, reports any mismatches, and fails the step if drift is found.
---

## Overview
This skill is intended to be used as a *pre‑step guard* for any build‑plan step. It ensures that the repository still contains the exact byte‑for‑byte copies of the canonical artifacts that were originally shipped in the bundle.

## Procedure
1. Execute `diff -r _inbox <repo‑paths>` where `<repo‑paths>` are the locations where the canonical files should reside (e.g., `FRAMEWORK.md`, `INTERFACE.md`, `IDENTITY.md`, `RUNBOOK.md`, `prompts/`, `build‑plan/`).
2. If the diff output is non‑empty, print the differences and exit with a non‑zero status code.
3. Optionally, compute SHA‑256 checksums for the files listed in `CHECKSUMS.txt` and compare them with the current files; report any mismatches.

## Usage
```bash
# Run the trace skill (fails if drift is detected)
agy -p "Run trace-missing-canonical" --exec "sh ./skills/trace-missing-canonical/run.sh"
```

## Implementation
Create a small shell script `run.sh` in the same directory that performs the diff and checksum verification. The skill itself is just the markdown description above; the script contains the actual logic.

## Evaluation
The skill is considered successful when it exits with status 0 and prints `OK: no drift detected`. Any output on `stderr` or a non‑zero exit status is treated as a failure, causing the surrounding build step to halt.
---
