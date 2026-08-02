#!/usr/bin/env python3
"""
Faber CMS Admin - Design System Applier

Applies design system tokens to the admin UI.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


def apply_design_system(config: Dict[str, Any], output_path: Path) -> None:
    """Apply design system tokens to admin CSS."""
    fixture = config.get("fixture", "faber-brand")

    # Load design system tokens
    design_system_path = Path("../../faber-design-system")
    tokens_file = design_system_path / "assets" / "tokens" / f"{fixture}.json"

    # Default tokens if file not found
    default_tokens = {
        "color": {
            "primary": {"value": "#10b981"},
            "background": {"value": "#ffffff"},
            "surface": {"value": "#f9fafb"},
            "border": {"value": "#e5e7eb"},
            "text": {"value": "#111827"},
            "text-muted": {"value": "#6b7280"}
        },
        "radius": {"value": "0.25rem"},
        "spacing": {"unit": "0.25rem"}
    }

    try:
        if tokens_file.exists():
            with open(tokens_file, 'r') as f:
                token_data = json.load(f)
            tokens = token_data
        else:
            tokens = default_tokens
    except Exception:
        tokens = default_tokens

    # Extract token values with fallbacks
    def get_token_value(path: str, default: str = "") -> str:
        try:
            keys = path.split('.')
            value = tokens
            for key in keys:
                value = value[key]
            return value.get('value', default) if isinstance(value, dict) else str(value)
        except (KeyError, TypeError, AttributeError):
            return default

    primary = get_token_value("color.primary.value", "#10b981")
    primary_dark = get_token_value("color.primaryDark.value", "#059669")
    background = get_token_value("color.background.value", "#ffffff")
    surface = get_token_value("color.surface.value", "#f9fafb")
    border = get_token_value("color.border.value", "#e5e7eb")
    text = get_token_value("color.text.value", "#111827")
    text_muted = get_token_value("color.textSecondary.value", "#6b7280")
    radius = get_token_value("radius.sm.value", "0.25rem")

    # Generate CSS variables
    css_vars = f""":root {{
  --faber-primary: {primary};
  --faber-primary-dark: {primary_dark};
  --faber-background: {background};
  --faber-surface: {surface};
  --faber-border: {border};
  --faber-text: {text};
  --faber-text-muted: {text_muted};
  --faber-radius: {radius};
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --faber-primary: {primary};
    --faber-primary-dark: {primary_dark};
    --faber-background: #0f172a;
    --faber-surface: #1e293b;
    --faber-border: #334155;
    --faber-text: #f8fafc;
    --faber-text-muted: #94a3b8;
  }}
}}
"""

    # Update the admin CSS file
    css_file = output_path / "src" / "styles" / "admin.css"
    if css_file.exists():
        content = css_file.read_text()
        # Replace the :root section
        import re
        # Find and replace the :root block
        pattern = r":root\s*\{[^}]*\}"
        replacement = f":root {{\n  --faber-primary: {primary};\n  --faber-primary-dark: {primary_dark};\n  --faber-background: {background};\n  --faber-surface: {surface};\n  --faber-border: {border};\n  --faber-text: {text};\n  --faber-text-muted: {text_muted};\n  --faber-radius: {radius}\n}}"
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Add dark mode media query if not present
        if "@media (prefers-color-scheme: dark)" not in new_content:
            dark_mode = f"""

@media (prefers-color-scheme: dark) {{
  :root {{
    --faber-primary: {primary};
    --faber-primary-dark: {primary_dark};
    --faber-background: #0f172a;
    --faber-surface: #1e293b;
    --faber-border: #334155;
    --faber-text: #f8fafc;
    --faber-text-muted: #94a3b8;
  }}
}}"""
            new_content = new_content.rstrip() + dark_mode + "\n"
        
        css_file.write_text(new_content)
    else:
        # Create CSS file if it doesn't exist
        css_file.write_text(css_vars)

    print(f"✓ Applied design system fixture '{fixture}' to admin CSS")


if __name__ == "__main__":
    print("Use via generate_admin_ui.py")