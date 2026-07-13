#!/usr/bin/env python3
"""
Intent Collection Web Adapter — HTTP API + static HTML form.

Per FRAMEWORK.md §3.5: Thin normalization layer that accepts input from
a web form or API client, validates it against the canonical JSON schema,
and invokes the intent-collect skill to produce the three deterministic artifacts.

Endpoints:
  GET  /intent            → serves static HTML form (assets/intent-form.html)
  POST /api/intent/collect → accepts canonical JSON, returns artifacts as JSON

Determinism: Same JSON input → same artifacts, regardless of surface.
No LLM in the path — purely deterministic.
"""

import json
import os
import subprocess
import sys
import tempfile
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# ─── Configuration ────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INTENT_SCRIPT = REPO_ROOT / "skills" / "intent-collect" / "scripts" / "intent_collect.py"
STATIC_FORM = REPO_ROOT / "skills" / "intent-collect" / "assets" / "intent-form.html"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8787

VALID_PRODUCTION_CONTEXTS = {"prototype", "normal", "client-production"}


# ─── Canonical JSON Validation ────────────────────────────────

def validate_canonical_json(data: dict) -> list:
    """Validate input against canonical JSON schema. Returns list of errors."""
    errors = []

    if not isinstance(data, dict):
        return ["Input must be a JSON object"]

    # Required fields
    context = data.get("context")
    if not context or not isinstance(context, str) or not context.strip():
        errors.append("Field 'context' is required (non-empty string)")

    production_context = data.get("production_context")
    if not production_context or not isinstance(production_context, str):
        errors.append("Field 'production_context' is required (string)")
    elif production_context not in VALID_PRODUCTION_CONTEXTS:
        errors.append(
            f"Field 'production_context' must be one of: {', '.join(sorted(VALID_PRODUCTION_CONTEXTS))}"
        )

    # Optional fields — type-check only
    if "constraints" in data and not isinstance(data["constraints"], list):
        errors.append("Field 'constraints' must be an array of strings")
    if "non_goals" in data and not isinstance(data["non_goals"], list):
        errors.append("Field 'non_goals' must be an array of strings")
    if "stakeholders" in data and not isinstance(data["stakeholders"], list):
        errors.append("Field 'stakeholders' must be an array of objects")

    return errors


def normalize_input(data: dict) -> dict:
    """Normalize surface-specific input to canonical schema."""
    return {
        "context": data.get("context", "").strip(),
        "production_context": data.get("production_context", "normal"),
        "constraints": data.get("constraints", []),
        "non_goals": data.get("non_goals", []),
        "stakeholders": data.get("stakeholders", []),
        "artifacts": data.get("artifacts", {}),
    }


# ─── Intent-Collect Skill Invocation ──────────────────────────

def invoke_intent_collect(canonical: dict, output_dir: Path = None) -> dict:
    """
    Invoke the deterministic intent-collect skill with normalized input.

    Returns dict with:
      - status: "success" | "error"
      - artifacts: {spec.md, trajectory.md, scope-baseline.md} (on success)
      - skill_output: raw JSON from the skill script
      - errors: list of error messages (on failure)
    """
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="intent_"))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Build command — call the existing deterministic skill
    cmd = [
        sys.executable,
        str(INTENT_SCRIPT),
        "--client-context", canonical["context"],
        "--production-context", canonical["production_context"],
        "--output-dir", str(output_dir),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "errors": [f"Skill exited with code {result.returncode}: {result.stderr.strip()}"],
                "output_dir": str(output_dir),
            }

        # Parse skill's JSON output from stdout
        skill_output = {}
        try:
            # The skill prints JSON to stdout
            stdout_text = result.stdout.strip()
            # Find the JSON object (it's the last line or the whole stdout)
            if stdout_text.startswith("{"):
                skill_output = json.loads(stdout_text)
            else:
                # Try to find JSON in the output
                for line in stdout_text.split("\n"):
                    if line.strip().startswith("{"):
                        skill_output = json.loads(line.strip())
                        break
        except json.JSONDecodeError:
            pass  # Non-fatal — we'll read artifacts from disk

        # Read the three artifacts from the output directory
        artifacts = {}
        for name in ["spec.md", "trajectory.md", "scope-baseline.md"]:
            artifact_path = output_dir / name
            if artifact_path.exists():
                artifacts[name] = artifact_path.read_text()
            else:
                return {
                    "status": "error",
                    "errors": [f"Expected artifact not found: {name}"],
                    "output_dir": str(output_dir),
                }

        return {
            "status": "success",
            "artifacts": artifacts,
            "skill_output": skill_output,
            "output_dir": str(output_dir),
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "errors": ["Skill invocation timed out (60s)"],
            "output_dir": str(output_dir),
        }
    except Exception as e:
        return {
            "status": "error",
            "errors": [f"Unexpected error: {str(e)}"],
            "output_dir": str(output_dir),
        }


# ─── HTTP Server ──────────────────────────────────────────────

class IntentHandler(BaseHTTPRequestHandler):
    """HTTP request handler for intent collection."""

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status_code: int, html: str):
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """Serve the static HTML form at /intent."""
        parsed = urlparse(self.path)

        if parsed.path == "/intent" or parsed.path == "/intent/":
            if STATIC_FORM.exists():
                self._send_html(200, STATIC_FORM.read_text())
            else:
                self._send_html(
                    404,
                    "<html><body><h1>Form not found</h1><p>assets/intent-form.html is missing.</p></body></html>",
                )
            return

        if parsed.path == "/" or parsed.path == "/health":
            self._send_json(200, {"status": "ok", "service": "intent-collect-adapter"})
            return

        self._send_json(404, {"error": "Not found", "path": parsed.path})

    def do_POST(self):
        """Accept canonical JSON at /api/intent/collect and return artifacts."""
        parsed = urlparse(self.path)

        if parsed.path != "/api/intent/collect":
            self._send_json(404, {"error": "Not found", "path": parsed.path})
            return

        # Read and parse request body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"error": "Empty request body", "errors": ["Request body is required"]})
            return

        try:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            self._send_json(400, {"error": "Invalid JSON", "errors": [str(e)]})
            return

        # Validate against canonical schema
        errors = validate_canonical_json(data)
        if errors:
            self._send_json(400, {"error": "Validation failed", "errors": errors})
            return

        # Normalize and invoke skill
        canonical = normalize_input(data)
        result = invoke_intent_collect(canonical)

        if result["status"] == "error":
            self._send_json(500, {
                "error": "Skill invocation failed",
                "errors": result.get("errors", []),
            })
            return

        self._send_json(200, {
            "status": "success",
            "artifacts": result["artifacts"],
            "skill_output": result.get("skill_output", {}),
            "run_id": str(uuid.uuid4()),
        })


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Start the HTTP server."""
    server = HTTPServer((host, port), IntentHandler)
    print(f"Intent Collection Web Adapter")
    print(f"  GET  http://{host}:{port}/intent      → HTML form")
    print(f"  POST http://{host}:{port}/api/intent/collect → JSON API")
    print(f"  GET  http://{host}:{port}/health      → health check")
    print()
    print(f"Listening on {host}:{port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Intent Collection Web Adapter")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind (default: {DEFAULT_PORT})")
    args = parser.parse_args()
    run_server(args.host, args.port)
