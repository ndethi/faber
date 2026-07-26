#!/usr/bin/env python3
"""
Faber Design System Skill - Generate design system assets from fixtures.

Reads fixture tokens (W3C Design Tokens format) and generates:
- CSS custom properties + component utilities
- Tailwind config extending framework defaults
- W3C Design Tokens JSON (for tools/Figma)
"""

import json
import re
import typer
from pathlib import Path
from typing import Any, Dict, List, Optional

app = typer.Typer(help="Generate design system assets from Faber fixtures")


def load_fixture_tokens(fixture: str, fixtures_dir: Path) -> Dict[str, Any]:
    """Load W3C Design Tokens from fixture directory."""
    tokens_path = fixtures_dir / fixture / "design-tokens.json"
    if not tokens_path.exists():
        # Fallback: check for CSS file and parse
        css_path = fixtures_dir / fixture / "design-tokens.css"
        if css_path.exists():
            typer.secho(f"  Warning: No design-tokens.json found, CSS-only fixture", fg=typer.colors.YELLOW)
            return {"fixture": fixture, "tokens": {}}
        raise FileNotFoundError(f"Fixture '{fixture}' not found at {tokens_path}")

    with open(tokens_path, "r") as f:
        return json.load(f)


def resolve_token_references(tokens: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve {token.path} references in token values.

    Handles references like {color.brand.bamboo.700} in semantic color values
    and gradient definitions. Matches paths relative to the "tokens" root.
    """
    # Collect all token values from the "tokens" section
    token_values = {}

    def collect_values(obj: Any, path: List[str]):
        if isinstance(obj, dict):
            if "value" in obj and "type" in obj:
                # Store with path relative to "tokens" root
                token_values[".".join(path)] = obj["value"]
            else:
                for k, v in obj.items():
                    collect_values(v, path + [k])
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                collect_values(v, path + [str(i)])

    # Start collecting from inside the "tokens" key
    if "tokens" in tokens:
        collect_values(tokens["tokens"], [])

    # Resolve references in strings - pattern {path.to.token}
    ref_pattern = re.compile(r"\{([^}]+)\}")

    def resolve_value(value: Any) -> Any:
        if isinstance(value, str):
            def replace_ref(match):
                ref_path = match.group(1)
                if ref_path in token_values:
                    return str(token_values[ref_path])
                return match.group(0)  # Leave unresolved refs as-is
            return ref_pattern.sub(replace_ref, value)
        return value

    def walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [walk(v) for v in obj]
        else:
            return resolve_value(obj)

    return walk(tokens)


def tokens_to_css_vars(tokens: Dict[str, Any], prefix: str = "rohaki") -> Dict[str, str]:
    """Convert token dict to flat CSS custom properties."""
    css_vars = {}

    def walk(obj: Any, path: List[str]):
        if isinstance(obj, dict):
            if "value" in obj and "type" in obj:
                name = "-".join([prefix] + path)
                css_vars[name] = str(obj["value"])
            else:
                for k, v in obj.items():
                    walk(v, path + [k])

    walk(tokens, [])
    return css_vars


def tokens_to_tailwind(tokens: Dict[str, Any]) -> Dict[str, Any]:
    """Convert tokens to Tailwind theme.extend structure."""
    tailwind = {"theme": {"extend": {}}}
    t = tokens.get("tokens", {})

    # Colors (exclude gradients - they go to backgroundImage)
    if "color" in t:
        color_ext = {}

        def extract_colors(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                if "value" in obj and "type" in obj and obj["type"] == "color":
                    key = prefix.rstrip("-")
                    color_ext[key] = obj["value"]
                else:
                    for k, v in obj.items():
                        extract_colors(v, f"{prefix}{k}-")

        for category, scales in t["color"].items():
            if category == "gradients":
                continue
            extract_colors(scales, f"{category}-")

        if color_ext:
            tailwind["theme"]["extend"]["colors"] = color_ext

    # Spacing
    if "spacing" in t and "space" in t["spacing"]:
        spacing_ext = {}
        for k, v in t["spacing"]["space"].items():
            if isinstance(v, dict) and "value" in v:
                spacing_ext[k] = v["value"]
        if spacing_ext:
            tailwind["theme"]["extend"]["spacing"] = spacing_ext

    # Typography
    if "typography" in t:
        typo = t["typography"]
        if "fontFamilies" in typo:
            ff = {}
            for k, v in typo["fontFamilies"].items():
                if isinstance(v, dict) and "value" in v:
                    ff[k] = v["value"].split(", ")
            if ff:
                tailwind["theme"]["extend"]["fontFamily"] = ff

        if "fontSizes" in typo:
            fs = {}
            for k, v in typo["fontSizes"].items():
                if isinstance(v, dict) and "value" in v:
                    line_height = typo.get("lineHeights", {}).get("normal", {}).get("value", "1.5")
                    fs[k] = [v["value"], {"lineHeight": line_height}]
            if fs:
                tailwind["theme"]["extend"]["fontSize"] = fs

        if "fontWeights" in typo:
            fw = {}
            for k, v in typo["fontWeights"].items():
                if isinstance(v, dict) and "value" in v:
                    fw[k] = v["value"]
            if fw:
                tailwind["theme"]["extend"]["fontWeight"] = fw

    # Border radius
    if "borderRadius" in t:
        br = {}
        for k, v in t["borderRadius"].items():
            if isinstance(v, dict) and "value" in v:
                br[k] = v["value"]
        if br:
            tailwind["theme"]["extend"]["borderRadius"] = br

    # Shadows
    if "shadow" in t:
        sh = {}
        for k, v in t["shadow"].items():
            if isinstance(v, dict) and "value" in v:
                sh[k] = v["value"]
        if sh:
            tailwind["theme"]["extend"]["boxShadow"] = sh

    # Animation
    if "animation" in t:
        anim = t["animation"]
        if "duration" in anim:
            dur = {}
            for k, v in anim["duration"].items():
                if isinstance(v, dict) and "value" in v:
                    dur[k] = v["value"]
            if dur:
                tailwind["theme"]["extend"]["transitionDuration"] = dur
        if "easing" in anim:
            ease = {}
            for k, v in anim["easing"].items():
                if isinstance(v, dict) and "value" in v:
                    ease[k] = v["value"]
            if ease:
                tailwind["theme"]["extend"]["transitionTimingFunction"] = ease

    # Z-index
    if "zIndex" in t:
        zi = {}
        for k, v in t["zIndex"].items():
            if isinstance(v, dict) and "value" in v:
                zi[k] = v["value"]
        if zi:
            tailwind["theme"]["extend"]["zIndex"] = zi

    # Background images (gradients)
    if "color" in t and "gradients" in t["color"]:
        bg = {}
        for k, v in t["color"]["gradients"].items():
            if isinstance(v, dict) and "value" in v:
                bg[f"rohaki-{k}"] = v["value"]
        if bg:
            tailwind["theme"]["extend"]["backgroundImage"] = bg

    return tailwind


def generate_css_custom_properties(css_vars: Dict[str, str]) -> str:
    """Generate CSS :root block with custom properties."""
    lines = [":root {"]
    for name, value in sorted(css_vars.items()):
        lines.append(f"  --{name}: {value};")
    lines.append("}")
    return "\n".join(lines)


def generate_component_css(fixture: str, css_vars: Dict[str, str]) -> str:
    """Generate component utility classes from tokens."""
    return f"""/* === {fixture.title()} Component Utilities === */
/* Generated from {fixture} design tokens */

/* Card */
.{fixture}-card {{
  background: var(--{fixture}-color-background-DEFAULT, #ffffff);
  border: 1px solid var(--{fixture}-color-border-DEFAULT, #bbf7d0);
  border-radius: var(--{fixture}-borderRadius-xl, 1.5rem);
  padding: var(--{fixture}-spacing-space-6, 1.5rem);
  box-shadow: var(--{fixture}-shadow-md, 0 4px 6px -1px rgb(0 0 0 / 0.1));
  transition: all var(--{fixture}-animation-duration-normal, 200ms) var(--{fixture}-animation-easing-easeOut, cubic-bezier(0, 0, 0.2, 1));
}}

.{fixture}-card:hover {{
  box-shadow: var(--{fixture}-shadow-brand-lg, 0 10px 30px 0 rgb(22 163 74 / 0.3));
  transform: translateY(-4px);
  border-color: var(--{fixture}-color-border-strong, #4ade80);
}}

.{fixture}-card-elevated {{
  box-shadow: var(--{fixture}-shadow-brand, 0 4px 14px 0 rgb(22 163 74 / 0.25));
}}

.{fixture}-card-stats {{
  background: var(--{fixture}-gradient-stats, linear-gradient(135deg, #14532d 0%, #15803d 100%));
  color: var(--{fixture}-color-text-inverse, #ffffff);
  border: none;
}}

.{fixture}-card-glass {{
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}}

/* Button */
.{fixture}-btn {{
  font-family: var(--{fixture}-font-sans, Inter, system-ui, sans-serif);
  font-weight: var(--{fixture}-font-semibold, 600);
  border-radius: var(--{fixture}-borderRadius-lg, 1rem);
  padding: var(--{fixture}-spacing-space-3, 0.75rem) var(--{fixture}-spacing-space-6, 1.5rem);
  font-size: var(--{fixture}-text-sm, 0.875rem);
  line-height: var(--{fixture}-leading-normal, 1.5);
  transition: all var(--{fixture}-animation-duration-fast, 150ms) var(--{fixture}-animation-easing-easeOut, cubic-bezier(0, 0, 0.2, 1));
  cursor: pointer;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--{fixture}-spacing-space-2, 0.5rem);
}}

.{fixture}-btn-sm {{ padding: var(--{fixture}-spacing-space-2, 0.5rem) var(--{fixture}-spacing-space-4, 1rem); font-size: var(--{fixture}-text-xs, 0.75rem); }}
.{fixture}-btn-md {{ padding: var(--{fixture}-spacing-space-3, 0.75rem) var(--{fixture}-spacing-space-6, 1.5rem); font-size: var(--{fixture}-text-sm, 0.875rem); }}
.{fixture}-btn-lg {{ padding: var(--{fixture}-spacing-space-4, 1rem) var(--{fixture}-spacing-space-8, 2rem); font-size: var(--{fixture}-text-base, 1rem); }}
.{fixture}-btn-xl {{ padding: var(--{fixture}-spacing-space-5, 1.25rem) var(--{fixture}-spacing-space-10, 2.5rem); font-size: var(--{fixture}-text-lg, 1.125rem); }}

.{fixture}-btn-primary {{
  background: var(--{fixture}-gradient-brand-primary, linear-gradient(135deg, #15803d 0%, #22c55e 100%));
  color: var(--{fixture}-color-primary-foreground, #ffffff);
  box-shadow: var(--{fixture}-shadow-brand, 0 4px 14px 0 rgb(22 163 74 / 0.25));
}}
.{fixture}-btn-primary:hover {{
  box-shadow: var(--{fixture}-shadow-brand-lg, 0 10px 30px 0 rgb(22 163 74 / 0.3));
  transform: translateY(-2px);
}}
.{fixture}-btn-primary:active {{
  transform: translateY(0);
  box-shadow: var(--{fixture}-shadow-brand, 0 4px 14px 0 rgb(22 163 74 / 0.25));
}}

.{fixture}-btn-secondary {{
  background: var(--{fixture}-color-secondary-DEFAULT, #b87336);
  color: var(--{fixture}-color-secondary-foreground, #ffffff);
}}
.{fixture}-btn-secondary:hover {{ background: var(--{fixture}-color-secondary-hover, #9a5d2d); }}

.{fixture}-btn-outline {{
  background: transparent;
  color: var(--{fixture}-color-primary-DEFAULT, #15803d);
  border: 2px solid var(--{fixture}-color-primary-DEFAULT, #15803d);
}}
.{fixture}-btn-outline:hover {{
  background: var(--{fixture}-color-primary-light, #dcfce7);
  color: var(--{fixture}-color-primary-DEFAULT, #15803d);
}}

.{fixture}-btn-ghost {{
  background: transparent;
  color: var(--{fixture}-color-text-secondary, #15803d);
}}
.{fixture}-btn-ghost:hover {{
  background: var(--{fixture}-color-background-secondary, #f0fdf4);
  color: var(--{fixture}-color-text-primary, #052e16);
}}

.{fixture}-btn-stats {{
  background: rgba(255, 255, 255, 0.1);
  color: var(--{fixture}-color-text-inverse, #ffffff);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
}}
.{fixture}-btn-stats:hover {{ background: rgba(255, 255, 255, 0.2); }}

/* Badge */
.{fixture}-badge {{
  display: inline-flex;
  align-items: center;
  padding: var(--{fixture}-spacing-space-1, 0.25rem) var(--{fixture}-spacing-space-3, 0.75rem);
  font-size: var(--{fixture}-text-xs, 0.75rem);
  font-weight: var(--{fixture}-font-medium, 500);
  border-radius: var(--{fixture}-borderRadius-full, 9999px);
  gap: var(--{fixture}-spacing-space-1, 0.25rem);
}}

.{fixture}-badge-default {{
  background: var(--{fixture}-color-primary-light, #dcfce7);
  color: var(--{fixture}-color-primary-DEFAULT, #15803d);
}}

.{fixture}-badge-success {{
  background: color-mix(in srgb, var(--{fixture}-color-status-success, #16a34a) 15%, transparent);
  color: var(--{fixture}-color-status-success, #16a34a);
}}

.{fixture}-badge-earth {{
  background: var(--{fixture}-color-brand-earth-100, #faefdf);
  color: var(--{fixture}-color-brand-earth-700, #9a5d2d);
}}

.{fixture}-badge-stats {{
  background: rgba(255, 255, 255, 0.15);
  color: var(--{fixture}-color-text-inverse, #ffffff);
  border: 1px solid rgba(255, 255, 255, 0.2);
}}

/* Grid Patterns */
.{fixture}-grid-cards {{
  display: grid;
  gap: var(--{fixture}-spacing-space-6, 1.5rem);
  grid-template-columns: repeat(1, minmax(0, 1fr));
}}
@media (min-width: 768px) {{ .{fixture}-grid-cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (min-width: 1024px) {{ .{fixture}-grid-cards {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
@media (min-width: 1280px) {{ .{fixture}-grid-cards {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }} }}

.{fixture}-grid-stats {{
  display: grid;
  gap: var(--{fixture}-spacing-space-4, 1rem);
  grid-template-columns: repeat(1, minmax(0, 1fr));
}}
@media (min-width: 640px) {{ .{fixture}-grid-stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (min-width: 1024px) {{ .{fixture}-grid-stats {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }} }}

.{fixture}-grid-features {{
  display: grid;
  gap: var(--{fixture}-spacing-space-8, 2rem);
  grid-template-columns: repeat(1, minmax(0, 1fr));
}}
@media (min-width: 1024px) {{ .{fixture}-grid-features {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (min-width: 1280px) {{ .{fixture}-grid-features {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}

/* Section Patterns */
.{fixture}-section {{
  padding: var(--{fixture}-spacing-space-16, 4rem) var(--{fixture}-spacing-space-4, 1rem);
}}
@media (min-width: 1024px) {{ .{fixture}-section {{ padding: var(--{fixture}-spacing-space-20, 5rem) var(--{fixture}-spacing-space-6, 1.5rem); }} }}
@media (min-width: 1280px) {{ .{fixture}-section {{ padding: var(--{fixture}-spacing-space-24, 6rem) var(--{fixture}-spacing-space-8, 2rem); }} }}

.{fixture}-section-hero {{
  padding: var(--{fixture}-spacing-space-20, 5rem) var(--{fixture}-spacing-space-4, 1rem);
  min-height: 90vh;
  display: flex;
  align-items: center;
  background: var(--{fixture}-gradient-hero, linear-gradient(135deg, #052e16 0%, #166534 50%, #16a34a 100%));
}}
@media (min-width: 1024px) {{ .{fixture}-section-hero {{ padding: var(--{fixture}-spacing-space-28, 7rem) var(--{fixture}-spacing-space-6, 1.5rem); min-height: 100vh; }} }}

.{fixture}-section-stats {{
  padding: var(--{fixture}-spacing-space-12, 3rem) var(--{fixture}-spacing-space-4, 1rem);
  background: var(--{fixture}-gradient-stats, linear-gradient(135deg, #14532d 0%, #15803d 100%));
}}
@media (min-width: 1024px) {{ .{fixture}-section-stats {{ padding: var(--{fixture}-spacing-space-16, 4rem) var(--{fixture}-spacing-space-6, 1.5rem); }} }}

.{fixture}-section-card-grid {{ background: var(--{fixture}-color-background-secondary, #f0fdf4); }}
.{fixture}-section-feature {{ background: var(--{fixture}-color-background-DEFAULT, #ffffff); }}
.{fixture}-section-cta {{
  background: var(--{fixture}-gradient-brand-primary, linear-gradient(135deg, #15803d 0%, #22c55e 100%));
  text-align: center;
}}

/* Typography */
.{fixture}-heading {{
  font-family: var(--{fixture}-font-display, 'Plus Jakarta Sans', Inter, system-ui, sans-serif);
  font-weight: var(--{fixture}-font-bold, 700);
  line-height: var(--{fixture}-leading-tight, 1.1);
  letter-spacing: var(--{fixture}-tracking-tight, -0.02em);
  color: var(--{fixture}-color-text-primary, #052e16);
}}

.{fixture}-h1 {{ font-size: var(--{fixture}-text-5xl, 3rem); }}
@media (min-width: 1024px) {{ .{fixture}-h1 {{ font-size: var(--{fixture}-text-6xl, 3.75rem); }} }}

.{fixture}-h2 {{ font-size: var(--{fixture}-text-4xl, 2.25rem); }}
@media (min-width: 1024px) {{ .{fixture}-h2 {{ font-size: var(--{fixture}-text-5xl, 3rem); }} }}

.{fixture}-h3 {{ font-size: var(--{fixture}-text-3xl, 1.875rem); }}
@media (min-width: 1024px) {{ .{fixture}-h3 {{ font-size: var(--{fixture}-text-4xl, 2.25rem); }} }}

.{fixture}-h4 {{ font-size: var(--{fixture}-text-2xl, 1.5rem); }}
.{fixture}-h5 {{ font-size: var(--{fixture}-text-xl, 1.25rem); }}
.{fixture}-h6 {{ font-size: var(--{fixture}-text-lg, 1.125rem); }}

.{fixture}-body {{
  font-family: var(--{fixture}-font-sans, Inter, system-ui, sans-serif);
  font-weight: var(--{fixture}-font-normal, 400);
  line-height: var(--{fixture}-leading-relaxed, 1.625);
  color: var(--{fixture}-color-text-secondary, #15803d);
}}

.{fixture}-body-sm {{ font-size: var(--{fixture}-text-sm, 0.875rem); }}
.{fixture}-body-base {{ font-size: var(--{fixture}-text-base, 1rem); }}
.{fixture}-body-lg {{ font-size: var(--{fixture}-text-lg, 1.125rem); }}

.{fixture}-stat-value {{
  font-family: var(--{fixture}-font-display, 'Plus Jakarta Sans', Inter, system-ui, sans-serif);
  font-weight: var(--{fixture}-font-extrabold, 800);
  line-height: var(--{fixture}-leading-tight, 1.1);
  font-size: var(--{fixture}-text-4xl, 2.25rem);
  color: var(--{fixture}-color-text-inverse, #ffffff);
}}
@media (min-width: 1024px) {{ .{fixture}-stat-value {{ font-size: var(--{fixture}-text-5xl, 3rem); }} }}

.{fixture}-stat-label {{
  font-family: var(--{fixture}-font-sans, Inter, system-ui, sans-serif);
  font-weight: var(--{fixture}-font-medium, 500);
  font-size: var(--{fixture}-text-sm, 0.875rem);
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: var(--{fixture}-tracking-wide, 0.02em);
}}
"""


def write_output(content: str, path: Path):
    """Write content to file, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    typer.secho(f"  ✓ {path}", fg=typer.colors.GREEN)


@app.command()
def generate(
    fixture: str = typer.Option(..., "--fixture", "-f", help="Fixture name (e.g., rohaki)"),
    output_dir: str = typer.Option("src/styles", "--output-dir", "-o", help="Output directory"),
    format: str = typer.Option("all", "--format", help="Output format: css, tailwind, json, all"),
    fixtures_dir: str = typer.Option("fixtures", "--fixtures-dir", help="Fixtures directory"),
    overrides_file: Optional[str] = typer.Option(None, "--overrides", help="JSON file with token overrides"),
):
    """Generate design system assets from a fixture."""
    project_root = Path.cwd()
    fixtures_path = project_root / fixtures_dir
    output_path = project_root / output_dir

    # Load fixture tokens
    tokens = load_fixture_tokens(fixture, fixtures_path)

    # Apply overrides if provided
    if overrides_file:
        with open(overrides_file, "r") as f:
            overrides = json.load(f)

        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for k, v in override.items():
                if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                    result[k] = deep_merge(result[k], v)
                else:
                    result[k] = v
            return result

        tokens = deep_merge(tokens, overrides)

    # Resolve token references (once, for all outputs)
    tokens = resolve_token_references(tokens)

    # Convert to CSS vars
    css_vars = tokens_to_css_vars(tokens.get("tokens", {}), prefix=fixture)

    # Convert to Tailwind
    tailwind_config = tokens_to_tailwind(tokens)

    generated = []

    if format in ("css", "all"):
        # CSS custom properties
        css_content = generate_css_custom_properties(css_vars)

        # Component utilities
        component_css = generate_component_css(fixture, css_vars)

        full_css = css_content + "\n\n" + component_css
        css_path = output_path / "design-tokens.css"
        write_output(full_css, css_path)
        generated.append(str(css_path))

    if format in ("tailwind", "all"):
        # Tailwind config
        tw_path = output_path / "tailwind.config.js"
        tailwind_js = generate_tailwind_config(fixture, tailwind_config)
        write_output(tailwind_js, tw_path)
        generated.append(str(tw_path))

    if format in ("json", "all"):
        # W3C Design Tokens JSON
        json_path = output_path / "design-tokens.json"
        write_output(json.dumps(tokens, indent=2), json_path)
        generated.append(str(json_path))

    typer.secho(f"\nGenerated {len(generated)} file(s) for fixture '{fixture}':", fg=typer.colors.BLUE, bold=True)
    for f in generated:
        typer.echo(f"  {f}")


def generate_tailwind_config(fixture: str, tailwind_config: Dict[str, Any]) -> str:
    """Generate Tailwind config as JS string."""
    import json

    theme_extend = tailwind_config.get("theme", {}).get("extend", {})

    def to_js(obj: Any, indent: int = 0) -> str:
        spaces = "  " * indent
        if isinstance(obj, dict):
            if not obj:
                return "{}"
            items = []
            for k, v in obj.items():
                key = f'"{k}"' if not k.replace("-", "").isalnum() else k
                items.append(f"{spaces}  {key}: {to_js(v, indent + 1)}")
            return "{\n" + ",\n".join(items) + f"\n{spaces}}}"
        elif isinstance(obj, list):
            return "[" + ", ".join(to_js(v, indent) for v in obj) + "]"
        elif isinstance(obj, str):
            return f'"{obj}"'
        elif isinstance(obj, bool):
            return "true" if obj else "false"
        elif obj is None:
            return "null"
        else:
            return str(obj)

    theme_js = to_js(theme_extend, 2)

    return f"""/**
 * {fixture.title()} Tailwind Config
 * Extends Faber framework defaults with {fixture} design tokens.
 * 
 * Usage:
 *   import {fixture}Config from './tailwind.config.js';
 *   export default {{ ...{fixture}Config, content: ['./src/**/*.{{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}}'] }};
 */

import defaultConfig from '@faber/tailwind-config/default';

const {fixture}Theme = {{
  theme: {{
    extend: {theme_js}
  }},
  plugins: [
    // Component utilities added via @apply in design-tokens.css
    function({{ addUtilities, addComponents, theme }}) {{
      // Custom utilities are in design-tokens.css
    }},
  ],
}};

export default {{
  ...defaultConfig,
  ...{fixture}Theme,
}};
"""


@app.command()
def apply(
    project_root: str = typer.Option(".", "--project-root", "-p", help="Project root directory"),
    fixture: str = typer.Option(..., "--fixture", "-f", help="Fixture name (e.g., rohaki)"),
    output_dir: str = typer.Option("src/styles", "--output-dir", "-o", help="Output directory relative to project root"),
    fixtures_dir: str = typer.Option("fixtures", "--fixtures-dir", help="Fixtures directory"),
):
    """Apply design system to an existing Astro project."""
    import shutil

    proj = Path(project_root).resolve()
    fixtures_path = proj / fixtures_dir
    output_path = proj / output_dir

    # First generate the assets
    tokens = load_fixture_tokens(fixture, fixtures_path)
    tokens = resolve_token_references(tokens)
    css_vars = tokens_to_css_vars(tokens.get("tokens", {}), prefix=fixture)
    tailwind_config = tokens_to_tailwind(tokens)

    # Generate CSS
    css_content = generate_css_custom_properties(css_vars)
    component_css = generate_component_css(fixture, css_vars)
    full_css = css_content + "\n\n" + component_css
    css_path = output_path / "design-tokens.css"
    write_output(full_css, css_path)

    # Generate Tailwind
    tw_path = output_path / "tailwind.config.js"
    tailwind_js = generate_tailwind_config(fixture, tailwind_config)
    write_output(tailwind_js, tw_path)

    # Generate JSON
    json_path = output_path / "design-tokens.json"
    write_output(json.dumps(tokens, indent=2), json_path)

    # Update astro.config.mjs to import design tokens
    astro_config = proj / "astro.config.mjs"
    if astro_config.exists():
        content = astro_config.read_text()
        import_line = "import './src/styles/design-tokens.css';"
        if import_line not in content:
            lines = content.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith("export "):
                    insert_idx = i + 1
                    break
            lines.insert(insert_idx, import_line)
            astro_config.write_text("\n".join(lines))
            typer.secho(f"  ✓ Updated {astro_config} with design tokens import", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  - {astro_config} already imports design tokens", fg=typer.colors.YELLOW)

    # Update global.css to use design tokens
    global_css = proj / "src" / "styles" / "global.css"
    if global_css.exists():
        content = global_css.read_text()
        if "@import './design-tokens.css';" not in content:
            global_css.write_text("@import './design-tokens.css';\n\n" + content)
            typer.secho(f"  ✓ Updated {global_css} to import design tokens", fg=typer.colors.GREEN)

    typer.secho(f"\n✓ Design system applied to {proj}", fg=typer.colors.GREEN, bold=True)


if __name__ == "__main__":
    app()