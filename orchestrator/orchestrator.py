#!/usr/bin/env python3
"""
Faber Orchestrator — sequences lifecycle skills per a run plan.

Reads a JSON run plan (ordered skill list + strictness), invokes skills in sequence,
writes runs/<run_id>/telemetry.json against runs/telemetry.schema.json.
"""
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class Orchestrator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.schema_path = repo_root / "runs" / "telemetry.schema.json"

    def load_schema(self) -> Dict:
        with open(self.schema_path, "r") as f:
            return json.load(f)

    def load_run_plan(self, plan_path: Path) -> Dict:
        with open(plan_path, "r") as f:
            plan = json.load(f)

        # Validate required fields
        if "skills" not in plan:
            raise ValueError("Run plan must contain 'skills' array")

        # Validate each step has a valid skill_id
        for i, step in enumerate(plan["skills"]):
            skill_id = step.get("skill_id")
            if not skill_id or not isinstance(skill_id, str) or not skill_id.strip():
                raise ValueError(f"Step {i} must have a non-empty string 'skill_id'")

        return plan

    def validate_telemetry(self, telemetry: Dict) -> bool:
        """Basic validation against schema (full validation would use jsonschema)."""
        required = ["run_id", "timestamp", "skills", "model", "tokens", "cost", "deploy_status"]
        for field in required:
            if field not in telemetry:
                print(f"Missing required field: {field}")
                return False
        return True

    def run_skill(self, skill_id: str, component: str = "", options: Dict = None) -> Dict:
        """
        Invoke a skill by running its script.
        Returns skill execution result with status, duration_ms, etc.
        """
        import time
        start = time.time()

        # Map skill_id to script path
        skill_scripts = {
            "intent-collect": "skills/intent-collect/scripts/intent_collect.py",
            "scaffold": "skills/scaffold/scripts/scaffold.py",
            "build": "skills/build/scripts/build.py",
            "evaluate": "skills/evaluate/scripts/evaluate.py",
            "deploy": "skills/deploy/scripts/deploy.py",
            "publish": "skills/publish/scripts/publish.py",
            "observe": "skills/observe/scripts/observe.py",
            "feedback": "skills/feedback/scripts/collect_feedback.py",
            "noop": "skills/noop/scripts/noop.py",
        }

        script_rel = skill_scripts.get(skill_id)
        if not script_rel:
            return {
                "skill_id": skill_id,
                "status": "failure",
                "duration_ms": 0,
                "error": f"No script mapped for skill: {skill_id}",
            }

        script_path = self.repo_root / script_rel
        if not script_path.exists():
            return {
                "skill_id": skill_id,
                "status": "failure",
                "duration_ms": 0,
                "error": f"Script not found: {script_rel}",
            }

        # Build command
        cmd = [sys.executable, str(script_path)]
        if component:
            cmd.append(component)
        if options:
            for k, v in options.items():
                if isinstance(v, bool):
                    if v:
                        cmd.append(f"--{k.replace('_', '-')}")
                else:
                    # Non-boolean values: pass as --key value
                    cmd.append(f"--{k.replace('_', '-')}")
                    cmd.append(str(v))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            duration_ms = int((time.time() - start) * 1000)

            if result.returncode == 0:
                return {
                    "skill_id": skill_id,
                    "status": "success",
                    "duration_ms": duration_ms,
                    "output": result.stdout.strip() if result.stdout else None,
                }
            else:
                return {
                    "skill_id": skill_id,
                    "status": "failure",
                    "duration_ms": duration_ms,
                    "error": result.stderr.strip() if result.stderr else result.stdout.strip(),
                }
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start) * 1000)
            return {
                "skill_id": skill_id,
                "status": "failure",
                "duration_ms": duration_ms,
                "error": "Timeout (300s)",
            }
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return {
                "skill_id": skill_id,
                "status": "failure",
                "duration_ms": duration_ms,
                "error": str(e),
            }

    def execute_plan(self, plan: Dict, model: str = "nemotron-3-ultra") -> Dict:
        """Execute a run plan and return telemetry record."""
        run_id = plan.get("run_id") or str(uuid.uuid4())
        strictness = plan.get("strictness", "ordered")
        expected_trajectory = plan.get("expected_trajectory", [])

        skills_run = []
        start_time = datetime.now(timezone.utc).isoformat()

        for step in plan.get("skills", []):
            skill_id = step.get("skill_id")
            component = step.get("component", "")
            options = step.get("options", {})

            result = self.run_skill(skill_id, component, options)
            skills_run.append(result)

            # Stop on failure unless configured otherwise
            if result["status"] == "failure" and not step.get("continue_on_failure", False):
                break

        end_time = datetime.now(timezone.utc).isoformat()

        # Build telemetry record
        telemetry = {
            "run_id": run_id,
            "timestamp": start_time,
            "skills": [
                {
                    "skill_id": s["skill_id"],
                    "status": s["status"],
                    "duration_ms": s["duration_ms"],
                }
                for s in skills_run
            ],
            "expected_trajectory": expected_trajectory,
            "trajectory_strictness": strictness,
            "model": model,
            "tokens": {"prompt": 0, "completion": 0, "total": 0},  # TODO: integrate with model-route
            "cost": 0.0,
            "eval_scores": {},
            "deploy_status": "not_deployed",
            "timestamps": {"start": start_time, "end": end_time},
        }

        if not self.validate_telemetry(telemetry):
            raise ValueError("Generated telemetry failed validation")

        return telemetry

    def write_telemetry(self, telemetry: Dict, output_dir: Path) -> Path:
        """Write telemetry JSON to runs/<run_id>/telemetry.json."""
        run_id = telemetry["run_id"]
        out_dir = output_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "telemetry.json"

        with open(out_path, "w") as f:
            json.dump(telemetry, f, indent=2)

        return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <run_plan.json> [--model <model_name>]")
        sys.exit(1)

    plan_path = Path(sys.argv[1]).resolve()
    model = "nemotron-3-ultra"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    repo_root = Path(__file__).parent.parent  # orchestrator/ -> repo root
    orchestrator = Orchestrator(repo_root)

    try:
        plan = orchestrator.load_run_plan(plan_path)
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"error": f"Invalid run plan: {e}"}))
        sys.exit(1)

    telemetry = orchestrator.execute_plan(plan, model)
    output_dir = repo_root / "runs"
    out_path = orchestrator.write_telemetry(telemetry, output_dir)

    print(json.dumps({"run_id": telemetry["run_id"], "telemetry_path": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()