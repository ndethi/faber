# Feedback Skill

> Collects user feedback after each run and stores it as `feedback.json`.

## Overview
The **feedback** skill reads the telemetry of a run, optionally prompts (placeholder) for a rating and notes, and writes a JSON payload to `<run_dir>/feedback.json`.

## Specification
- **Input**: path to a run directory.
- **Process**:
  1. Load `<run_dir>/observations.json` if it exists.
  2. Create a feedback payload with a static rating (5) and notes.
  3. Write the payload to `<run_dir>/feedback.json`.
- **Output**: `feedback.json` written next to `observations.json`.

## Implementation
Implemented in `skills/feedback/scripts/collect_feedback.py`.
