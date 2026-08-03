#!/usr/bin/env python3
"""
Faber CMS Worker Generator
Generates a complete Cloudflare Worker project from config/defaults.yaml
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent.parent


def load_config(config_path: Path) -> Dict[str, Any]:
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_d1_schema(config: Dict[str, Any]) -> str:
    """Generate D1 SQL schema for all content types."""
    sql_parts = []

    # Base tables (from migration)
    sql_parts.append("-- Base tables (collections, media, users, settings, webhooks, api_keys, audit_log)")
    sql_parts.append("-- See migrations/0001_initial.sql")

    # Content type specific tables
    for ct in config.get("contentTypes", []):
        name = ct["name"]
        has_slug = any(f["name"] == "slug" for f in ct.get("fields", []))

        columns = [
            "id TEXT PRIMARY KEY",
            "collection_id INTEGER NOT NULL REFERENCES collections(name) ON DELETE CASCADE",
            "version INTEGER NOT NULL DEFAULT 1",
            "data TEXT NOT NULL",
            "status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived'))",
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
            "updated_at TEXT DEFAULT CURRENT_TIMESTAMP",
            "published_at TEXT",
            "created_by TEXT NOT NULL",
            "updated_by TEXT NOT NULL",
        ]

        if has_slug:
            columns.append("slug TEXT")

        col_sql = ",\n  ".join(columns)

        if has_slug:
            col_sql += ",\n  UNIQUE(collection_id, slug)"

        sql_parts.append(f"""
CREATE TABLE IF NOT EXISTS content_{name} (
  {col_sql}
);""")

        sql_parts.append(f"CREATE INDEX IF NOT EXISTS idx_content_{name}_collection ON content_{name}(collection_id);")
        sql_parts.append(f"CREATE INDEX IF NOT EXISTS idx_content_{name}_status ON content_{name}(status);")
        if has_slug:
            sql_parts.append(f"CREATE INDEX IF NOT EXISTS idx_content_{name}_slug ON content_{name}(slug);")
        sql_parts.append(f"CREATE INDEX IF NOT EXISTS idx_content_{name}_published_at ON content_{name}(published_at);")

    return "\n".join(sql_parts)


def generate_zod_schemas(config: Dict[str, Any]) -> str:
    """Generate Zod schema definitions for each content type."""
    imports = "import { z } from 'zod';\n\n"
    schemas = []

    for ct in config.get("contentTypes", []):
        name = ct["name"]
        fields = {}

        for field in ct.get("fields", []):
            field_name = field["name"]
            field_type = field["type"]
            required = field.get("required", False)

            if field_type == "string":
                if field.get("format") == "url":
                    schema = "z.string().url()"
                elif field.get("format") == "date-time":
                    schema = "z.string().datetime()"
                elif "enum" in field:
                    enum_vals = ", ".join(f'"{v}"' for v in field["enum"])
                    schema = f"z.enum([{enum_vals}])"
                else:
                    schema = "z.string()"
            elif field_type == "number":
                schema = "z.number()"
            elif field_type == "array":
                items = field.get("items", {})
                if items.get("type") == "string":
                    schema = "z.array(z.string())"
                else:
                    schema = "z.array(z.any())"
            else:
                schema = "z.any()"

            if not required:
                schema += ".optional()"
            if "default" in field:
                if isinstance(field["default"], str):
                    schema += f'.default("{field["default"]}")'
                else:
                    schema += f".default({field['default']})"

            fields[field_name] = schema

        nl = "\n"
        indent = "  "
        field_lines = f"{nl}{indent}".join(f"{k}: {v}" for k, v in fields.items())
        schema_code = f"""export const {name}Schema = z.object({{
{indent}{field_lines}
}});

export type {name.capitalize()} = z.infer<typeof {name}Schema>;
"""
        schemas.append(schema_code)

    return imports + "\n".join(schemas)


def generate_collection_configs(config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate collection configurations for database seeding."""
    collections = {}

    for ct in config.get("contentTypes", []):
        name = ct["name"]
        zod_schema = {}
        ui_config = ct.get("uiConfig", {})

        for field in ct.get("fields", []):
            field_name = field["name"]
            field_type = field["type"]
            required = field.get("required", False)

            if field_type == "string":
                if field.get("format") == "url":
                    zod_schema[field_name] = {"type": "string", "format": "url"}
                elif field.get("format") == "date-time":
                    zod_schema[field_name] = {"type": "string", "format": "date-time"}
                elif "enum" in field:
                    zod_schema[field_name] = {"type": "string", "enum": field["enum"]}
                else:
                    zod_schema[field_name] = {"type": "string"}
            elif field_type == "number":
                zod_schema[field_name] = {"type": "number"}
            elif field_type == "array":
                items = field.get("items", {})
                if items.get("type") == "string":
                    zod_schema[field_name] = {"type": "array", "items": {"type": "string"}}
                else:
                    zod_schema[field_name] = {"type": "array", "items": {}}
            else:
                zod_schema[field_name] = {"type": "any"}

            if not required:
                zod_schema[field_name]["optional"] = True
            if "default" in field:
                zod_schema[field_name]["default"] = field["default"]

        collections[name] = {
            "name": name,
            "label": ct.get("label", name.capitalize()),
            "description": ct.get("description", ""),
            "schema": zod_schema,
            "uiConfig": ui_config,
        }

    return collections


def copy_template_files(output_dir: Path, template_dir: Path):
    """Copy template files from skill directory to output."""
    for item in template_dir.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(template_dir)
            dest = output_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def main():
    parser = argparse.ArgumentParser(description="Generate Faber CMS Worker project")
    parser.add_argument("--config", default="config/defaults.yaml", help="Path to config YAML")
    parser.add_argument("--output-dir", default="worker", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    if args.dry_run:
        print("DRY RUN - Would generate:")
        print(f"  Output directory: {output_dir}")
        print(f"  Content types: {[ct['name'] for ct in config.get('contentTypes', [])]}")
        print(f"  D1 schema tables: collections, media, users, settings, webhooks, api_keys, audit_log")
        for ct in config.get("contentTypes", []):
            print(f"    + content_{ct['name']}")
        return

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy template files
    template_dir = Path(__file__).parent / "worker"
    if template_dir.exists():
        copy_template_files(output_dir, template_dir)

    # Generate D1 schema
    d1_schema = generate_d1_schema(config)
    (output_dir / "schema.sql").write_text(d1_schema)
    print(f"Generated {output_dir}/schema.sql")

    # Generate Zod schemas
    zod_schemas = generate_zod_schemas(config)
    (output_dir / "src" / "db" / "zod-schemas.ts").write_text(zod_schemas)
    print(f"Generated {output_dir}/src/db/zod-schemas.ts")

    # Generate collection configs
    collections = generate_collection_configs(config)
    (output_dir / "collections.json").write_text(json.dumps(collections, indent=2))
    print(f"Generated {output_dir}/collections.json")

    # Install dependencies and verify
    print("\nInstalling dependencies...")
    subprocess.run(["npm", "install"], cwd=output_dir, check=True)

    print("\nRunning typecheck...")
    result = subprocess.run(["npm", "run", "typecheck"], cwd=output_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Typecheck failed:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)

    print("\nRunning tests...")
    result = subprocess.run(["npm", "test"], cwd=output_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Tests failed:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)

    print("\n✅ Worker project generated and verified successfully!")
    print(f"Output: {output_dir.absolute()}")


if __name__ == "__main__":
    main()