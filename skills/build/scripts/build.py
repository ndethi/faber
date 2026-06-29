#!/usr/bin/env python3
"""
Astro build wrapper for Faber build skill.

Runs `astro build` with Cloudflare Pages adapter and outputs
a JSON summary of generated files with SHA-256 hashes.
"""
import json
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run_astro_build(component_dir: Path, minify: bool = True) -> Dict:
    """Run `astro build` in the component directory."""
    # Fast fail: check for package.json with astro dependency
    pkg_json = component_dir / "package.json"
    if not pkg_json.exists():
        return {
            "success": False,
            "error": f"No package.json found in {component_dir}. Astro project required.",
            "command": "check_package_json",
        }

    try:
        pkg_data = json.loads(pkg_json.read_text())
        deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
        if "astro" not in deps:
            return {
                "success": False,
                "error": f"Astro not found in package.json dependencies at {component_dir}",
                "command": "check_package_json",
            }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Invalid package.json at {component_dir}",
            "command": "check_package_json",
        }

    cmd = ["npx", "astro", "build"]
    if minify:
        cmd.append("--minify")

    result = subprocess.run(
        cmd,
        cwd=component_dir,
        capture_output=True,
        text=True,
        timeout=120,  # 2 minute timeout for actual build
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr or result.stdout,
            "command": " ".join(cmd),
        }

    # Find the dist directory (Astro default output)
    dist_dir = component_dir / "dist"
    if not dist_dir.exists():
        # Check for Cloudflare Pages output (.vercel/output/static or similar)
        # For Cloudflare Pages adapter, output is typically in `dist/`
        # But let's check common locations
        for candidate in [component_dir / "dist", component_dir / ".vercel" / "output" / "static"]:
            if candidate.exists():
                dist_dir = candidate
                break
        else:
            return {
                "success": False,
                "error": f"No output directory found after build. Checked: {component_dir}/dist",
                "command": " ".join(cmd),
            }

    # Collect all files with hashes
    files = []
    for file_path in dist_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dist_dir)
            files.append({
                "path": str(rel_path),
                "absolute_path": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "sha256": sha256_file(file_path),
            })

    return {
        "success": True,
        "dist_dir": str(dist_dir),
        "files": files,
        "file_count": len(files),
        "total_bytes": sum(f["size_bytes"] for f in files),
        "command": " ".join(cmd),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: build.py <component_dir> [--no-minify]",
        }))
        sys.exit(1)

    component_dir = Path(sys.argv[1]).resolve()
    minify = "--no-minify" not in sys.argv

    if not component_dir.exists():
        print(json.dumps({
            "success": False,
            "error": f"Component directory does not exist: {component_dir}",
        }))
        sys.exit(1)

    result = run_astro_build(component_dir, minify)
    print(json.dumps(result, indent=2))

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()