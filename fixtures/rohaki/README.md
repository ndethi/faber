# Rohaki Design Tokens — Faber Fixture

Rohaki ESG Bamboo Supply Chain brand design tokens for the Faber framework.

## What This Is

This is a **Faber fixture** — not a framework default. It's the Rohaki brand's design system expressed as design tokens that Faber projects can adopt via the `faber-design-system` skill.

The Faber framework's scaffold skill generates *generic* defaults (blue primary, system fonts, basic spacing). This fixture provides Rohaki-specific tokens:

- **Brand palette**: Bamboo greens (primary), Sage greens (secondary), Earth tones (warmth)
- **Green gradients**: Hero, card, stats, brand-primary/secondary/accent
- **Component patterns**: Card grids, stats grids, feature grids
- **Typography**: Plus Jakarta Sans display, Inter body
- **Motion**: Spring easing, brand-colored shadows

## Files

| File | Purpose |
|------|---------|
| `design-tokens.json` | W3C Design Tokens format (tools: Style Dictionary, Figma, etc.) |
| `design-tokens.css` | CSS custom properties + utility classes (drop-in for Astro) |
| `tailwind.config.js` | Tailwind config extending framework defaults |

## Usage

### In an Astro Project (recommended)

```bash
# Copy the CSS file to your project
cp fixtures/rohaki/design-tokens.css src/styles/rohaki-tokens.css
```

```astro
<!-- src/styles/global.css -->
@import './rohaki-tokens.css';

/* Use utility classes */
.hero { @apply rohaki-section-hero; }
.card { @apply rohaki-card; }
.btn-primary { @apply rohaki-btn rohaki-btn-primary; }
```

### With Tailwind

```js
// tailwind.config.js
import rohakiConfig from '@faber/fixtures/rohaki/tailwind.config.js';

export default {
  ...rohakiConfig,
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
};
```

```astro
<!-- Use Tailwind classes -->
<div class="rohaki-section-hero">
  <h1 class="rohaki-h1">Sustainable Bamboo Supply Chain</h1>
  <button class="rohaki-btn rohaki-btn-primary rohaki-btn-lg">Get Started</button>
</div>

<div class="rohaki-grid-stats">
  <div class="rohaki-card rohaki-card-stats">
    <span class="rohaki-stat-value">10,000+</span>
    <span class="rohaki-stat-label">Hectares Managed</span>
  </div>
</div>
```

### With Design Tools (Figma, Style Dictionary)

```json
// design-tokens.json is W3C Design Tokens format
// Import into Style Dictionary, Figma Tokens Studio, etc.
{
  "source": ["fixtures/rohaki/design-tokens.json"],
  "platforms": { "css": { "transformGroup": "css", "buildPath": "dist/", "files": [{ "destination": "variables.css", "format": "css/variables" }] } }
}
```

## Token Reference

### Colors

| Category | Tokens |
|----------|--------|
| **Bamboo** (primary) | `--bamboo-50` through `--bamboo-950` |
| **Sage** (secondary) | `--sage-50` through `--sage-950` |
| **Earth** (warmth) | `--earth-50` through `--earth-950` |
| **Semantic** | `--primary`, `--secondary`, `--accent`, `--background`, `--text`, `--border`, `--status` |
| **Gradients** | `--gradient-brand-primary`, `--gradient-hero`, `--gradient-stats`, etc. |

### Spacing

`--space-0` through `--space-24` (0 to 6rem)

### Typography

- Font families: `--font-sans`, `--font-display`, `--font-mono`
- Sizes: `--text-xs` through `--text-7xl`
- Weights: `--font-normal` through `--font-extrabold`
- Line heights, letter spacing

### Components (utility classes)

| Pattern | Classes |
|---------|---------|
| Cards | `.rohaki-card`, `.rohaki-card-elevated`, `.rohaki-card-stats`, `.rohaki-card-glass` |
| Buttons | `.rohaki-btn`, `.rohaki-btn-{sm,md,lg,xl}`, `.rohaki-btn-{primary,secondary,outline,ghost,stats}` |
| Badges | `.rohaki-badge`, `.rohaki-badge-{default,success,earth,stats}` |
| Grids | `.rohaki-grid-cards`, `.rohaki-grid-stats`, `.rohaki-grid-features` |
| Sections | `.rohaki-section`, `.rohaki-section-hero`, `.rohaki-section-stats`, `.rohaki-section-cta` |
| Typography | `.rohaki-heading`, `.rohaki-h1`–`.rohaki-h6`, `.rohaki-body`, `.rohaki-stat-value`, `.rohaki-stat-label` |

## Integration with Faber

When the `faber-design-system` skill is built (BG-021), it will:

1. Read this fixture from `fixtures/rohaki/`
2. Generate a project-specific `tailwind.config.js` extending framework defaults
3. Output CSS custom properties to `src/styles/design-tokens.css`
4. Create component templates using these patterns

## Not a Framework Default

**Important**: The Faber framework's scaffold skill (`skills/scaffold/scripts/scaffold.py`) generates *generic* defaults:
- Blue primary (`#0066cc`)
- System UI fonts
- Basic spacing/shadows
- No gradients, no component patterns

This fixture is **opt-in**. Projects choose to adopt Rohaki branding by using this fixture. Other fixtures (other brands) can coexist.

## License

Part of the Faber framework. MIT licensed.