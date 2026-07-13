#!/usr/bin/env python3
"""
Deploy Skill - Lifecycle skill #5: deploys evaluated project to Cloudflare Pages.

Reads project config and evaluation results, runs build, deploys via wrangler,
and outputs deployment summary.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy skill - deploy to Cloudflare Pages")
    parser.add_argument("--project-dir", required=True, help="Directory of the scaffolded project to deploy")
    parser.add_argument("--input-dir", required=True, help="Directory containing evaluation-report.json and artifacts")
    parser.add_argument("--output-dir", default=".", help="Directory to write deployment report (default: .)")
    parser.add_argument("--hitl-gate", action="store_true", help="Require manual confirmation before deploying")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deployed without executing")
    parser.add_argument("--env", choices=["preview", "production"], default="production", help="Deployment environment")
    return parser.parse_args()


def load_evaluation_report(input_dir: Path) -> Dict[str, Any]:
    """Load and validate evaluation report."""
    eval_path = input_dir / "evaluation-report.json"
    if not eval_path.exists():
        raise FileNotFoundError(f"evaluation-report.json not found in {input_dir}")

    with open(eval_path) as f:
        report = json.load(f)

    if not report.get("overall_success", False):
        raise ValueError("Evaluation report indicates failure: overall_success is false")

    return report


def parse_wrangler_config(project_dir: Path) -> Dict[str, str]:
    """Parse wrangler.toml for deployment config."""
    wrangler_path = project_dir / "wrangler.toml"
    config = {"name": "unknown-app", "pages_build_output_dir": "dist"}

    if not wrangler_path.exists():
        print(f"Warning: wrangler.toml not found at {wrangler_path}, using defaults", file=sys.stderr)
        return config

    try:
        content = wrangler_path.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("name") and "=" in line:
                config["name"] = line.split("=")[1].strip().strip('"').strip("'")
            elif line.startswith("pages_build_output_dir") and "=" in line:
                config["pages_build_output_dir"] = line.split("=")[1].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Warning: Could not parse wrangler.toml: {e}", file=sys.stderr)

    return config


def run_build(project_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Run npm build in project directory."""
    pkg_json = project_dir / "package.json"
    if not pkg_json.exists():
        return {"success": False, "error": "package.json not found"}

    try:
        pkg_data = json.loads(pkg_json.read_text())
        scripts = pkg_data.get("scripts", {})
        if "build" not in scripts:
            return {"success": False, "error": "No build script in package.json"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid package.json"}

    if dry_run:
        return {"success": True, "command": "npm run build", "dry_run": True}

    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Build timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def deploy_to_pages(
    project_dir: Path,
    dist_dir: Path,
    project_name: str,
    env: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Deploy to Cloudflare Pages using wrangler."""
    if dry_run:
        return {
            "success": True,
            "command": f"npx wrangler pages deploy {dist_dir} --project-name={project_name} --branch=main",
            "deployment_url": "https://TODO.pages.dev",
            "deployment_id": "TODO",
            "dry_run": True,
        }

    try:
        cmd = ["npx", "wrangler", "pages", "deploy", str(dist_dir), "--project-name", project_name, "--branch", "main"]
        if env == "production":
            cmd.append("--commit-dirty=true")

        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=180,
        )

        # Parse deployment URL from output
        deployment_url = "https://TODO.pages.dev"
        deployment_id = "TODO"

        for line in result.stdout.splitlines():
            if "https://" in line and ".pages.dev" in line:
                deployment_url = line.strip()
                break

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "deployment_url": deployment_url,
            "deployment_id": deployment_id,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Deployment timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def hitl_confirm(message: str) -> bool:
    """Prompt for human confirmation."""
    try:
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def write_reports(
    output_dir: Path,
    project_name: str,
    deployment_url: str,
    deployment_id: str,
    env: str,
    hitl_gate: bool,
    hitl_passed: bool,
    dry_run: bool,
    build_result: Dict[str, Any],
    deploy_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Write deployment report files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # deployment-report.json
    report = {
        "project_name": project_name,
        "environment": env,
        "deployment_url": deployment_url,
        "deployment_id": deployment_id,
        "hitl_gate_required": hitl_gate,
        "hitl_gate_passed": hitl_passed,
        "dry_run": dry_run,
        "build": {
            "success": build_result.get("success", False),
            "command": build_result.get("command", "npm run build"),
        },
        "deploy": {
            "success": deploy_result.get("success", False),
            "command": deploy_result.get("command", "wrangler pages deploy"),
        },
        "status": "success" if (build_result.get("success") and deploy_result.get("success")) else "failed",
    }

    (output_dir / "deployment-report.json").write_text(json.dumps(report, indent=2))

    # DEPLOYMENT_SUMMARY.md
    summary = f"""# Deployment Summary

**Project:** {project_name}
**Environment:** {env}
**Status:** {report['status'].upper()}
**Deployment URL:** {deployment_url}
**Deployment ID:** {deployment_id}

## Build
- **Command:** {report['build']['command']}
- **Success:** {report['build']['success']}

## Deploy
- **Command:** {report['deploy']['command']}
- **Success:** {report['deploy']['success']}

## Gates
- **HITL Required:** {report['hitl_gate_required']}
- **HITL Passed:** {report['hitl_gate_passed']}
- **Dry Run:** {report['dry_run']}

*Generated by Faber deploy skill*
"""
    (output_dir / "DEPLOYMENT_SUMMARY.md").write_text(summary)

    return {
        "status": report["status"],
        "artifacts": ["deployment-report.json", "DEPLOYMENT_SUMMARY.md"],
        "deployment_url": deployment_url,
        "deployment_id": deployment_id,
        "environment": env,
        "hitl_gate_required": hitl_gate,
        "hitl_gate_passed": hitl_passed,
        "dry_run": dry_run,
    }


def main() -> int:
    args = parse_args()

    project_dir = Path(args.project_dir).resolve()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    # Validate inputs
    if not project_dir.exists():
        print(f"Error: Project directory does not exist: {project_dir}", file=sys.stderr)
        return 1

    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    try:
        # Load and validate evaluation report
        eval_report = load_evaluation_report(input_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Parse project config
    wrangler_config = parse_wrangler_config(project_dir)
    project_name = wrangler_config["name"]
    dist_dir = project_dir / wrangler_config["pages_build_output_dir"]

    # HITL gate
    hitl_passed = True
    if args.hitl_gate:
        if not hitl_confirm(f"Deploy {project_name} to {args.env} environment?"):
            print("Deployment cancelled by user.", file=sys.stderr)
            return 1
        hitl_passed = True

    # Run build
    print(f"Building project {project_name}...", file=sys.stderr)
    build_result = run_build(project_dir, args.dry_run)
    if not build_result.get("success", False):
        print(f"Build failed: {build_result.get('error', build_result.get('stderr', 'Unknown error'))}", file=sys.stderr)
        # Still write report showing build failure
        deploy_result = {"success": False, "error": "Build failed"}
        summary = write_reports(output_dir, project_name, "https://TODO.pages.dev", "TODO", args.env,
                                args.hitl_gate, hitl_passed, args.dry_run, build_result, deploy_result)
        print(json.dumps(summary))
        return 1

    # Deploy
    print(f"Deploying to Cloudflare Pages ({args.env})...", file=sys.stderr)
    deploy_result = deploy_to_pages(project_dir, dist_dir, project_name, args.env, args.dry_run)

    if not deploy_result.get("success", False):
        print(f"Deployment failed: {deploy_result.get('error', deploy_result.get('stderr', 'Unknown error'))}", file=sys.stderr)

    # Write reports
    deployment_url = deploy_result.get("deployment_url", "https://TODO.pages.dev")
    deployment_id = deploy_result.get("deployment_id", "TODO")

    summary = write_reports(
        output_dir, project_name, deployment_url, deployment_id, args.env,
        args.hitl_gate, hitl_passed, args.dry_run, build_result, deploy_result,
    )

    # Output machine-readable summary
    print(json.dumps(summary))

    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())