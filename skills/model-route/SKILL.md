---
name: model-route
description: "Routes each skill step to local or frontier model based on policy; runs continuous local-vs-frontier evals to gate graduation."
version: 1.0.0
author: Faber Framework
license: MIT
tags:
  - cross-cutting
  - cost-layer
  - model-routing
  - optimization
---

# Model Route Skill

**Cross-cutting skill** — picks local vs frontier model per step; runs continuous comparison evals (FRAMEWORK.md §8).

## Purpose

Optimizes cost by routing routine steps to cheap local models, reserving frontier models for hard reasoning. Maintains a routing policy updated by continuous evals.

## Inputs

- `skill_id` (string, required): Skill to route
- `component` (string, optional): Component within skill
- `context` (string, optional): Additional context for routing decision
- `policy_path` (string, optional): Path to routing policy JSON (default: `runs/model-route/policy.json`)

## Outputs

- **Routing decision** (JSON to stdout):
  - `model`: "local" | "frontier"
  - `endpoint`: string (OpenAI-compatible endpoint URL)
  - `model_name`: string (e.g., "nemotron-3-ultra", "gpt-oss-120b")
  - `reason`: string (why this route was chosen)
  - `estimated_cost_usd`: float
- **Policy update** (writes to `policy_path`):
  - Per-skill routing history
  - Local vs frontier eval comparison results
  - Graduation thresholds

## Routing Policy

Policy is a JSON file with:
```json
{
  "default": "frontier",
  "skills": {
    "intent-collect": "local",
    "build": "local",
    "evaluate": "frontier"
  },
  "graduation_thresholds": {
    "min_samples": 10,
    "quality_threshold": 0.95,
    "cost_savings_min": 0.5
  },
  "eval_history": []
}
```

## Interface

```bash
python skills/model-route/scripts/model_route.py \
  --skill-id intent-collect \
  --component "" \
  [--context "simple extraction"] \
  [--policy-path runs/model-route/policy.json]
```

Returns JSON routing decision on stdout.

## Evaluation

- `evals/test_model_route.py`: Tests routing decisions, policy persistence, graduation logic
- Verifies local model graduation only when eval clears threshold

## Dependencies

- Python 3.10+
- Standard library only (json, sys, pathlib, argparse)
- Optional: requests for frontier API calls