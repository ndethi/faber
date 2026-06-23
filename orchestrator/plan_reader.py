import json
import sys

def read_plan(plan_path: str) -> dict:
    """Read a JSON run‑plan.
    Expected shape:
    {
        "run_id": "string",
        "skills": [
            {"skill_id": "string", "entry": "path/to/script.py"},
            ...
        ]
    }
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plan_reader.py <plan_path>")
        sys.exit(1)
    plan = read_plan(sys.argv[1])
    print(json.dumps(plan, indent=2))
