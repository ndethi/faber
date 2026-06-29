#!/usr/bin/env python3
"""
No-op skill for orchestrator testing.
Exits successfully with a simple message.
"""
import json
import sys


def main():
    print(json.dumps({
        "success": True,
        "message": "No-op skill executed successfully",
        "run_id": "noop-test-001",
    }, indent=2))


if __name__ == "__main__":
    main()