#!/usr/bin/env python3
"""
Faber Intent Wizard Generator - Main Entry Point

Generates a complete Astro project with /intent wizard route,
D1 schema, Telegram integration, and CI/CD.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

from generate_d1_schema import generate_d1_schema, generate_migration_sql
from generate_intent_route import generate_intent_page, generate_success_page, generate_wizard_components
from generate_telegram_handler import generate_telegram_webhook, generate_intent_api
from generate_backlog_draft import generate_backlog_draft_script
from apply_design_system import apply_design_system
from setup_astro_project import setup_astro_project

app = typer.Typer(help="Faber Intent Wizard Generator - Creates public /intent wizard with D1 + Telegram")


def load_deploy_targets(file_path: str) -> Dict[str, Any]:
    """Load deploy targets from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def load_telegram_config(bot_token: Optional[str], chat_id: Optional[str]) -> Dict[str, str]:
    """Load Telegram config from args or environment."""
    config = {}
    if bot_token:
        config["bot_token"] = bot_token
    elif os.getenv("TELEGRAM_BOT_TOKEN"):
        config["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    else:
        config["bot_token"] = "<your-telegram-bot-token>"

    if chat_id:
        config["chat_id"] = chat_id
    elif os.getenv("TELEGRAM_CHAT_ID"):
        config["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")
    else:
        config["chat_id"] = "<your-telegram-chat-id>"

    return config


@app.command()
def generate(
    project_name: str = typer.Option(..., "--project-name", help="Project name (e.g., faber-intent-wizard)"),
    output_dir: str = typer.Option(..., "--output-dir", help="Output directory for generated project"),
    production_domain: Optional[str] = typer.Option(None, "--production-domain", help="Production domain"),
    staging_domain: Optional[str] = typer.Option(None, "--staging-domain", help="Staging domain"),
    deploy_targets_file: Optional[str] = typer.Option(None, "--deploy-targets-file", help="JSON file with deploy targets"),
    fixture: str = typer.Option("faber-brand", "--fixture", help="Design system fixture (default: faber-brand)"),
    telegram_bot_token: Optional[str] = typer.Option(None, "--telegram-bot-token", help="Telegram bot token"),
    telegram_chat_id: Optional[str] = typer.Option(None, "--telegram-chat-id", help="Telegram chat ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be generated without writing files"),
):
    """Generate the complete intent wizard project."""

    # Build deploy targets
    if deploy_targets_file:
        deploy_targets = load_deploy_targets(deploy_targets_file)
    else:
        production_domain = production_domain or f"{project_name}.example.com"
        staging_domain = staging_domain or f"dev-{project_name}.example.com"
        deploy_targets = {
            "production": {"domain": production_domain, "branch": "main"},
            "staging": {"domain": staging_domain, "branch": "dev"},
        }

    telegram_config = load_telegram_config(telegram_bot_token, telegram_chat_id)

    # Build config object
    config = {
        "project_name": project_name,
        "output_dir": output_dir,
        "deploy_targets": deploy_targets,
        "fixture": fixture,
        "telegram": telegram_config,
    }

    if dry_run:
        typer.echo("=== DRY RUN: Would generate ===")
        typer.echo(json.dumps(config, indent=2))
        typer.echo("\nFiles that would be created:")
        files = [
            f"{output_dir}/src/pages/intent.astro",
            f"{output_dir}/src/pages/intent/success.astro",
            f"{output_dir}/src/pages/api/intent.ts",
            f"{output_dir}/src/pages/api/telegram.ts",
            f"{output_dir}/src/components/wizard/StepGoal.astro",
            f"{output_dir}/src/components/wizard/StepAudience.astro",
            f"{output_dir}/src/components/wizard/StepNonGoals.astro",
            f"{output_dir}/src/components/wizard/StepIA.astro",
            f"{output_dir}/src/components/wizard/StepContentModel.astro",
            f"{output_dir}/src/components/wizard/StepConstraints.astro",
            f"{output_dir}/src/components/wizard/StepMetrics.astro",
            f"{output_dir}/src/components/wizard/StepReview.astro",
            f"{output_dir}/src/components/ui/Button.astro",
            f"{output_dir}/src/components/ui/Input.astro",
            f"{output_dir}/src/components/ui/Textarea.astro",
            f"{output_dir}/src/components/ui/Select.astro",
            f"{output_dir}/src/components/ui/ProgressStepper.astro",
            f"{output_dir}/src/components/ui/Card.astro",
            f"{output_dir}/src/db/schema.sql",
            f"{output_dir}/src/db/migrations/0001_initial.sql",
            f"{output_dir}/wrangler.toml",
            f"{output_dir}/package.json",
            f"{output_dir}/astro.config.mjs",
            f"{output_dir}/.github/workflows/deploy.yml",
        ]
        for f in files:
            typer.echo(f"  {f}")
        return

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Generating intent wizard for {project_name}...")

    # 1. Setup Astro project structure (package.json, astro.config.mjs, wrangler.toml, CI/CD)
    typer.echo("  → Setting up Astro project structure...")
    setup_astro_project(config, out_path)

    # 2. Apply design system tokens
    typer.echo(f"  → Applying design system fixture: {fixture}...")
    apply_design_system(config, out_path)

    # 3. Generate D1 schema and migration
    typer.echo("  → Generating D1 schema...")
    schema_sql = generate_d1_schema()
    migration_sql = generate_migration_sql()
    (out_path / "src" / "db").mkdir(parents=True, exist_ok=True)
    (out_path / "src" / "db" / "schema.sql").write_text(schema_sql)
    (out_path / "src" / "db" / "migrations").mkdir(parents=True, exist_ok=True)
    (out_path / "src" / "db" / "migrations" / "0001_initial.sql").write_text(migration_sql)

    # 4. Generate intent wizard pages
    typer.echo("  → Generating /intent wizard pages...")
    intent_page = generate_intent_page(config)
    success_page = generate_success_page(config)
    (out_path / "src" / "pages" / "intent.astro").write_text(intent_page)
    (out_path / "src" / "pages" / "intent").mkdir(parents=True, exist_ok=True)
    (out_path / "src" / "pages" / "intent" / "success.astro").write_text(success_page)

    # 5. Generate wizard components
    typer.echo("  → Generating wizard step components...")
    components = generate_wizard_components(config)
    (out_path / "src" / "components" / "wizard").mkdir(parents=True, exist_ok=True)
    for name, content in components.items():
        (out_path / "src" / "components" / "wizard" / f"{name}.astro").write_text(content)

    # 6. Generate UI components
    typer.echo("  → Generating UI components...")
    ui_components = generate_ui_components(config)
    (out_path / "src" / "components" / "ui").mkdir(parents=True, exist_ok=True)
    for name, content in ui_components.items():
        (out_path / "src" / "components" / "ui" / f"{name}.astro").write_text(content)

    # 7. Generate API endpoints
    typer.echo("  → Generating API endpoints...")
    intent_api = generate_intent_api(config)
    telegram_webhook = generate_telegram_webhook(config)
    (out_path / "src" / "pages" / "api").mkdir(parents=True, exist_ok=True)
    (out_path / "src" / "pages" / "api" / "intent.ts").write_text(intent_api)
    (out_path / "src" / "pages" / "api" / "telegram.ts").write_text(telegram_webhook)

    # 8. Generate backlog draft script
    typer.echo("  → Generating backlog draft generator...")
    backlog_script = generate_backlog_draft_script(config)
    (out_path / "scripts" / "generate_backlog_draft.py").write_text(backlog_script)
    (out_path / "scripts" / "generate_backlog_draft.py").chmod(0o755)

    typer.echo(f"\n✓ Generated complete intent wizard at {output_dir}")
    typer.echo(f"  Project: {project_name}")
    typer.echo(f"  Fixture: {fixture}")
    typer.echo(f"  Production: {deploy_targets['production']['domain']}")
    typer.echo(f"  Staging: {deploy_targets['staging']['domain']}")
    typer.echo(f"\nNext steps:")
    typer.echo(f"  cd {output_dir}")
    typer.echo(f"  npm install")
    typer.echo(f"  npm run dev")
    typer.echo(f"  # Configure D1 database and Telegram credentials in wrangler.toml")
    typer.echo(f"  # Then deploy: npm run deploy:staging / npm run deploy:production")


def generate_ui_components(config: Dict[str, Any]) -> Dict[str, str]:
    """Generate reusable UI components."""
    project_name = config["project_name"]

    return {
        "Button.astro": """---
// Button.astro - Reusable button component
// Generated by faber-intent-wizard for {project_name}

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  class?: string
  children?: any
}

const {
  variant = 'primary',
  size = 'md',
  disabled = false,
  type = 'button',
  class = '',
  children,
  ...rest
}} = Astro.props;
---

<button
  type={type}
  disabled={disabled}
  class="inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
    {{
      'bg-faber-primary text-white hover:bg-faber-primary-dark focus:ring-faber-primary':
        variant === 'primary',
      'bg-faber-surface border border-faber-border text-faber-text hover:bg-faber-surface-hover focus:ring-faber-border':
        variant === 'secondary',
      'bg-transparent text-faber-text hover:bg-faber-surface focus:ring-faber-border':
        variant === 'ghost',
      'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500':
        variant === 'danger',
    }}
    {{
      'px-3 py-1.5 text-sm': size === 'sm',
      'px-4 py-2 text-base': size === 'md',
      'px-6 py-3 text-lg': size === 'lg',
    }}
    {{ 'opacity-50 cursor-not-allowed': disabled }}
    {{class}}"
  {...rest}
>
  <slot>{children}</slot>
</button>

<style is:global>
  /* Button styles are handled via Tailwind classes */
</style>
""",
        "Input.astro": """---
// Input.astro - Reusable input component

interface Props {
  name: string
  label?: string
  type?: 'text' | 'email' | 'url' | 'number' | 'password'
  placeholder?: string
  value?: string
  required?: boolean
  disabled?: boolean
  error?: string
  class?: string
}

const {
  name,
  label,
  type = 'text',
  placeholder = '',
  value = '',
  required = false,
  disabled = false,
  error,
  class = '',
  ...rest
} = Astro.props;
---

<div class="w-full">
  {label && (
    <label for={name} class="block text-sm font-medium text-faber-text mb-1">
      {label} {required && <span class="text-faber-danger" aria-hidden="true">*</span>}
    </label>
  )}
  <input
    id={name}
    name={name}
    type={type}
    placeholder={placeholder}
    value={value}
    required={required}
    disabled={disabled}
    aria-invalid={error ? 'true' : 'false'}
    aria-describedby={error ? `${name}-error` : undefined}
    class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-faber-surface
      border-faber-border focus:border-faber-primary focus:ring-2 focus:ring-faber-primary/20
      disabled:bg-faber-surface disabled:cursor-not-allowed
      text-faber-text placeholder:text-faber-text-muted
      {error ? 'border-faber-danger focus:border-faber-danger focus:ring-faber-danger/20' : ''}
      {class}"
    {...rest}
  />
  {error && (
    <p id={`${name}-error`} class="mt-1 text-sm text-faber-danger" role="alert">{error}</p>
  )}
</div>
""",
        "Textarea.astro": """---
// Textarea.astro - Reusable textarea component

interface Props {
  name: string
  label?: string
  placeholder?: string
  value?: string
  required?: boolean
  disabled?: boolean
  rows?: number
  error?: string
  class?: string
}

const {
  name,
  label,
  placeholder = '',
  value = '',
  required = false,
  disabled = false,
  rows = 4,
  error,
  class = '',
  ...rest
} = Astro.props;
---

<div class="w-full">
  {label && (
    <label for={name} class="block text-sm font-medium text-faber-text mb-1">
      {label} {required && <span class="text-faber-danger" aria-hidden="true">*</span>}
    </label>
  )}
  <textarea
    id={name}
    name={name}
    placeholder={placeholder}
    required={required}
    disabled={disabled}
    rows={rows}
    aria-invalid={error ? 'true' : 'false'}
    aria-describedby={error ? `${name}-error` : undefined}
    class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-faber-surface
      border-faber-border focus:border-faber-primary focus:ring-2 focus:ring-faber-primary/20
      disabled:bg-faber-surface disabled:cursor-not-allowed
      text-faber-text placeholder:text-faber-text-muted
      resize-y min-h-[100px]
      {error ? 'border-faber-danger focus:border-faber-danger focus:ring-faber-danger/20' : ''}
      {class}"
    {...rest}
  >{value}</textarea>
  {error && (
    <p id={`${name}-error`} class="mt-1 text-sm text-faber-danger" role="alert">{error}</p>
  )}
</div>
""",
        "Select.astro": """---
// Select.astro - Reusable select component

interface Props {
  name: string
  label?: string
  options: { value: string; label: string }[]
  value?: string
  required?: boolean
  disabled?: boolean
  placeholder?: string
  error?: string
  class?: string
}

const {
  name,
  label,
  options = [],
  value = '',
  required = false,
  disabled = false,
  placeholder = 'Select...',
  error,
  class = '',
  ...rest
} = Astro.props;
---

<div class="w-full">
  {label && (
    <label for={name} class="block text-sm font-medium text-faber-text mb-1">
      {label} {required && <span class="text-faber-danger" aria-hidden="true">*</span>}
    </label>
  )}
  <select
    id={name}
    name={name}
    required={required}
    disabled={disabled}
    aria-invalid={error ? 'true' : 'false'}
    aria-describedby={error ? `${name}-error` : undefined}
    class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-faber-surface
      border-faber-border focus:border-faber-primary focus:ring-2 focus:ring-faber-primary/20
      disabled:bg-faber-surface disabled:cursor-not-allowed
      text-faber-text
      {error ? 'border-faber-danger focus:border-faber-danger focus:ring-faber-danger/20' : ''}
      {class}"
    {...rest}
  >
    <option value="" disabled selected hidden>{placeholder}</option>
    {options.map(opt => (
      <option value={opt.value} selected={value === opt.value}>{opt.label}</option>
    ))}
  </select>
  {error && (
    <p id={`${name}-error`} class="mt-1 text-sm text-faber-danger" role="alert">{error}</p>
  )}
</div>
""",
        "ProgressStepper.astro": """---
// ProgressStepper.astro - Multi-step progress indicator

interface Props {
  steps: { id: string; label: string }[]
  currentStep: number
  class?: string
}

const { steps = [], currentStep = 0, class = '' } = Astro.props;
---

<nav aria-label="Wizard progress" class="w-full {class}">
  <ol class="flex items-center" role="list">
    {steps.map((step, index) => (
      <li class="relative flex items-center flex-1" key={step.id}>
        <div class="flex items-center">
          <button
            type="button"
            class="relative z-10 flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium transition-all
              {index < currentStep
                ? 'bg-faber-primary text-white'
                : index === currentStep
                ? 'bg-faber-primary text-white ring-4 ring-faber-primary/20'
                : 'bg-faber-surface border-2 border-faber-border text-faber-text-muted'}"
            aria-current={index === currentStep ? 'step' : undefined}
            aria-label={`Step ${index + 1}: ${step.label}`}
            disabled={index > currentStep}
          >
            {index < currentStep ? (
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <span>{index + 1}</span>
            )}
          </button>
          {index < steps.length - 1 && (
            <div class="hidden md:block absolute left-1/2 right-1/2 -translate-x-1/2 h-0.5
              {index < currentStep ? 'bg-faber-primary' : 'bg-faber-border'}"></div>
          )}
        </div>
        <span class="mt-2 text-center text-xs font-medium
          {index <= currentStep ? 'text-faber-text' : 'text-faber-text-muted'}">
          {step.label}
        </span>
      </li>
    ))}
  </ol>
</nav>
""",
        "Card.astro": """---
// Card.astro - Reusable card component

interface Props {
  title?: string
  description?: string
  class?: string
  headerClass?: string
  bodyClass?: string
}

const { title, description, class = '', headerClass = '', bodyClass = '', ...rest } = Astro.props;
---

<div class="bg-white dark:bg-faber-surface border border-faber-border rounded-xl overflow-hidden {class}" {...rest}>
  {(title || description) && (
    <div class="px-6 py-4 border-b border-faber-border {headerClass}">
      {title && <h3 class="text-lg font-semibold text-faber-text">{title}</h3>}
      {description && <p class="mt-1 text-sm text-faber-text-muted">{description}</p>}
    </div>
  )}
  <div class="p-6 {bodyClass}">
    <slot />
  </div>
</div>
""",
    }


if __name__ == "__main__":
    app()