---
name: scope-ledger
description: "Tracks baseline scope (from intent-collect) vs extended-scope items with estimated agent cost and dev IP attribution. Surfaces in dashboard for billing and IP tracking."
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - cross-cutting
  - commercial
  - scope-tracking
  - cost-attribution
---

# Scope Ledger Skill

**Cross-cutting skill** — tracks baseline scope vs extended scope with cost and IP attribution (FRAMEWORK.md §9).

## Purpose

Maintains a ledger of scope items: the client-shareable baseline (from intent-collect) plus extended-scope items from feedback loop, each with estimated agent cost and IP attribution.

## Inputs

- `scope_baseline_path` (string, required): Path to scope-baseline.md from intent-collect
- `extended_items` (array, optional): New extended-scope items to add
- `ledger_path` (string, optional): Path to ledger JSON (default: `runs/scope-ledger/ledger.json`)

## Outputs

- **Ledger** (JSON to stdout, also written to `ledger_path`):
  - `baseline`: {content, hash, created_at}
  - `extended`: array of items with:
    - `id`: string (EXT-001, EXT-002, ...)
    - `description`: string
    - `source`: "client-feedback" | "dev-discovered" | "spec-gap" | "regression"
    - `estimated_agent_cost_usd`: float
    - `estimated_tokens`: int
    - `model_route`: "local" | "frontier"
    - `ip_attribution`: "client" | "dev" | "agent" | "shared"
    - `status`: "proposed" | "approved" | "implemented" | "rejected"
    - `created_at`: ISO timestamp
    - `approved_at`: ISO timestamp | null
- **Summary** (JSON to stdout):
  - `baseline_items`: int
  - `extended_items`: int
  - `total_estimated_cost`: float
  - `by_status`: {proposed, approved, implemented, rejected}
  - `by_ip`: {client, dev, agent, shared}

## Interface

```bash
# Initialize ledger from scope-baseline
python skills/scope-ledger/scripts/scope_ledger.py \
  --scope-baseline-path scope-baseline.md \
  [--ledger-path runs/scope-ledger/ledger.json]

# Add extended-scope item
python skills/scope-ledger/scripts/scope_ledger.py \
  --add-item \
  --description "Add user dashboard with analytics" \
  --source "client-feedback" \
  --estimated-cost 0.50 \
  --estimated-tokens 10000 \
  --model-route frontier \
  --ip-attribution shared \
  [--ledger-path runs/scope-ledger/ledger.json]

# Update item status
python skills/scope-ledger/scripts/scope_ledger.py \
  --update-item EXT-001 \
  --status approved \
  [--ledger-path runs/scope-ledger/ledger.json]

# Show ledger
python skills/scope-ledger/scripts/scope_ledger.py \
  --show \
  [--ledger-path runs/scope-ledger/ledger.json]
```

## Evaluation

- `evals/test_scope_ledger.py`: Tests ledger initialization, item CRUD, summary generation

## Dependencies

- Python 3.10+
- Standard library only (json, sys, pathlib, argparse, hashlib, datetime)