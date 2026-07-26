/** @type {import('tailwindcss').Config} */
/**
 * Rohaki Design System - Tailwind Config
 * ESG Bamboo Supply Chain brand tokens
 * 
 * Usage: 
 *   import rohakiConfig from '@faber/fixtures/rohaki/tailwind.config.js';
 *   export default { ...rohakiConfig, content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'] };
 * 
 * This is a FABER FIXTURE - not a framework default.
 * Framework defaults are in skills/scaffold/scripts/scaffold.py
 */

const rohakiColors = {
  // Brand palette
  bamboo: {
    50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 300: '#86efac', 400: '#4ade80',
    500: '#22c55e', 600: '#16a34a', 700: '#15803d', 800: '#166534', 900: '#14532d', 950: '#052e16',
  },
  sage: {
    50: '#f6fef7', 100: '#e8fce5', 200: '#d1f9cb', 300: '#a3f29d', 400: '#70e66f',
    500: '#4ade80', 600: '#22c55e', 700: '#16a34a', 800: '#15803d', 900: '#166534', 950: '#052e16',
  },
  earth: {
    50: '#fdf8f3', 100: '#faefdf', 200: '#f5deb3', 300: '#e8c492', 400: '#d8a76a',
    500: '#c98b4a', 600: '#b87336', 700: '#9a5d2d', 800: '#7d4b28', 900: '#643d23', 950: '#351f11',
  },
  // Semantic colors
  primary: {
    DEFAULT: '#15803d', hover: '#166534', light: '#dcfce7', foreground: '#ffffff',
  },
  secondary: {
    DEFAULT: '#b87336', hover: '#9a5d2d', light: '#faefdf', foreground: '#ffffff',
  },
  accent: {
    DEFAULT: '#4ade80', hover: '#22c55e', light: '#e8fce5', foreground: '#052e16',
  },
  background: {
    DEFAULT: '#ffffff', secondary: '#f0fdf4', tertiary: '#f6fef7', dark: '#052e16',
  },
  text: {
    primary: '#052e16', secondary: '#15803d', muted: '#22c55e', inverse: '#ffffff',
  },
  border: {
    DEFAULT: '#bbf7d0', strong: '#4ade80', focus: '#22c55e',
  },
  status: {
    success: '#16a34a', warning: '#c98b4a', error: '#dc2626', info: '#4ade80',
  },
  // Gradients
  gradients: {
    'brand-primary': 'linear-gradient(135deg, #15803d 0%, #22c55e 100%)',
    'brand-secondary': 'linear-gradient(135deg, #b87336 0%, #d8a76a 100%)',
    'brand-accent': 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
    hero: 'linear-gradient(135deg, #052e16 0%, #166534 50%, #16a34a 100%)',
    card: 'linear-gradient(145deg, #f0fdf4 0%, #f6fef7 100%)',
    stats: 'linear-gradient(135deg, #14532d 0%, #15803d 100%)',
  },
};

const rohakiSpacing = {
  0: '0', 1: '0.25rem', 2: '0.5rem', 3: '0.75rem', 4: '1rem',
  5: '1.25rem', 6: '1.5rem', 8: '2rem', 10: '2.5rem', 12: '3rem',
  16: '4rem', 20: '5rem', 24: '6rem',
};

const rohakiTypography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
    display: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
  },
  fontSize: {
    xs: '0.75rem', sm: '0.875rem', base: '1rem', lg: '1.125rem', xl: '1.25rem',
    '2xl': '1.5rem', '3xl': '1.875rem', '4xl': '2.25rem', '5xl': '3rem',
    '6xl': '3.75rem', '7xl': '4.5rem',
  },
  fontWeight: {
    normal: '400', medium: '500', semibold: '600', bold: '700', extrabold: '800',
  },
  lineHeight: {
    tight: '1.1', snug: '1.375', normal: '1.5', relaxed: '1.625', loose: '2',
  },
  letterSpacing: {
    tight: '-0.02em', normal: '0', wide: '0.02em',
  },
};

const rohakiBorderRadius = {
  none: '0', sm: '0.25rem', DEFAULT: '0.5rem', md: '0.75rem',
  lg: '1rem', xl: '1.5rem', '2xl': '2rem', full: '9999px',
};

const rohakiShadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  brand: '0 4px 14px 0 rgb(22 163 74 / 0.25)',
  'brand-lg': '0 10px 30px 0 rgb(22 163 74 / 0.3)',
};

const rohakiAnimation = {
  duration: { fast: '150ms', normal: '200ms', slow: '300ms', slower: '500ms' },
  easing: {
    linear: 'linear',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
};

const config = {
  content: [],
  theme: {
    extend: {
      colors: rohakiColors,
      spacing: rohakiSpacing,
      ...rohakiTypography,
      borderRadius: rohakiBorderRadius,
      boxShadow: rohakiShadows,
      transitionDuration: rohakiAnimation.duration,
      transitionTimingFunction: rohakiAnimation.easing,
      // Gradients as background images
      backgroundImage: {
        'rohaki-brand-primary': rohakiColors.gradients['brand-primary'],
        'rohaki-brand-secondary': rohakiColors.gradients['brand-secondary'],
        'rohaki-brand-accent': rohakiColors.gradients['brand-accent'],
        'rohaki-hero': rohakiColors.gradients.hero,
        'rohaki-card': rohakiColors.gradients.card,
        'rohaki-stats': rohakiColors.gradients.stats,
      },
      // Component utilities (available as @apply classes)
      // These are also exposed as CSS custom properties in design-tokens.css
    },
  },
  plugins: [
    function({ addUtilities, addComponents, theme }) {
      // Card component variants
      const cardComponents = {
        '.rohaki-card': {
          backgroundColor: theme('colors.background.DEFAULT'),
          borderWidth: '1px',
          borderColor: theme('colors.border.DEFAULT'),
          borderRadius: theme('borderRadius.xl'),
          padding: theme('spacing.6'),
          boxShadow: theme('boxShadow.md'),
          transitionProperty: 'all',
          transitionDuration: theme('transitionDuration.normal'),
          transitionTimingFunction: theme('transitionTimingFunction.out'),
        },
        '.rohaki-card:hover': {
          boxShadow: theme('boxShadow.brand-lg'),
          transform: 'translateY(-4px)',
          borderColor: theme('colors.border.strong'),
        },
        '.rohaki-card-elevated': { boxShadow: theme('boxShadow.brand') },
        '.rohaki-card-stats': {
          backgroundImage: theme('backgroundImage.rohaki-stats'),
          color: theme('colors.text.inverse'),
          border: 'none',
        },
        '.rohaki-card-glass': {
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(12px)',
          borderWidth: '1px',
          borderColor: 'rgba(255, 255, 255, 0.2)',
        },
      };
      addComponents(cardComponents);

      // Button component variants
      const buttonComponents = {
        '.rohaki-btn': {
          fontFamily: theme('fontFamily.sans'),
          fontWeight: theme('fontWeight.semibold'),
          borderRadius: theme('borderRadius.lg'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          fontSize: theme('fontSize.sm'),
          lineHeight: theme('lineHeight.normal'),
          transitionProperty: 'all',
          transitionDuration: theme('transitionDuration.fast'),
          transitionTimingFunction: theme('transitionTimingFunction.out'),
          cursor: 'pointer',
          border: 'none',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: theme('spacing.2'),
        },
        // Button sizes
        '.rohaki-btn-sm': { padding: `${theme('spacing.2')} ${theme('spacing.4')}`, fontSize: theme('fontSize.xs') },
        '.rohaki-btn-md': { padding: `${theme('spacing.3')} ${theme('spacing.6')}`, fontSize: theme('fontSize.sm') },
        '.rohaki-btn-lg': { padding: `${theme('spacing.4')} ${theme('spacing.8')}`, fontSize: theme('fontSize.base') },
        '.rohaki-btn-xl': { padding: `${theme('spacing.5')} ${theme('spacing.10')}`, fontSize: theme('fontSize.lg') },
        // Button variants
        '.rohaki-btn-primary': {
          backgroundImage: theme('backgroundImage.rohaki-brand-primary'),
          color: theme('colors.primary.foreground'),
          boxShadow: theme('boxShadow.brand'),
        },
        '.rohaki-btn-primary:hover': { boxShadow: theme('boxShadow.brand-lg'), transform: 'translateY(-2px)' },
        '.rohaki-btn-primary:active': { transform: 'translateY(0)', boxShadow: theme('boxShadow.brand') },
        '.rohaki-btn-secondary': {
          backgroundColor: theme('colors.secondary.DEFAULT'),
          color: theme('colors.secondary.foreground'),
        },
        '.rohaki-btn-secondary:hover': { backgroundColor: theme('colors.secondary.hover') },
        '.rohaki-btn-outline': {
          backgroundColor: 'transparent',
          color: theme('colors.primary.DEFAULT'),
          borderWidth: '2px',
          borderColor: theme('colors.primary.DEFAULT'),
        },
        '.rohaki-btn-outline:hover': {
          backgroundColor: theme('colors.primary.light'),
          color: theme('colors.primary.DEFAULT'),
        },
        '.rohaki-btn-ghost': {
          backgroundColor: 'transparent',
          color: theme('colors.text.secondary'),
        },
        '.rohaki-btn-ghost:hover': {
          backgroundColor: theme('colors.background.secondary'),
          color: theme('colors.text.primary'),
        },
        '.rohaki-btn-stats': {
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          color: theme('colors.text.inverse'),
          borderWidth: '1px',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          backdropFilter: 'blur(8px)',
        },
        '.rohaki-btn-stats:hover': { backgroundColor: 'rgba(255, 255, 255, 0.2)' },
      };
      addComponents(buttonComponents);

      // Badge component
      const badgeComponents = {
        '.rohaki-badge': {
          display: 'inline-flex', alignItems: 'center',
          padding: `${theme('spacing.1')} ${theme('spacing.3')}`,
          fontSize: theme('fontSize.xs'),
          fontWeight: theme('fontWeight.medium'),
          borderRadius: theme('borderRadius.full'),
          gap: theme('spacing.1'),
        },
        '.rohaki-badge-default': {
          backgroundColor: theme('colors.primary.light'),
          color: theme('colors.primary.DEFAULT'),
        },
        '.rohaki-badge-success': {
          backgroundColor: 'color-mix(in srgb, ' + theme('colors.status.success') + ' 15%, transparent)',
          color: theme('colors.status.success'),
        },
        '.rohaki-badge-earth': {
          backgroundColor: theme('colors.earth.100'),
          color: theme('colors.earth.700'),
        },
        '.rohaki-badge-stats': {
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          color: theme('colors.text.inverse'),
          borderWidth: '1px',
          borderColor: 'rgba(255, 255, 255, 0.2)',
        },
      };
      addComponents(badgeComponents);

      // Grid patterns
      const gridComponents = {
        '.rohaki-grid-cards': {
          display: 'grid',
          gap: theme('spacing.6'),
          gridTemplateColumns: 'repeat(1, minmax(0, 1fr))',
        },
        '@media (min-width: 768px)': { '.rohaki-grid-cards': { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' } },
        '@media (min-width: 1024px)': { '.rohaki-grid-cards': { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' } },
        '@media (min-width: 1280px)': { '.rohaki-grid-cards': { gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' } },
        '.rohaki-grid-stats': {
          display: 'grid', gap: theme('spacing.4'), gridTemplateColumns: 'repeat(1, minmax(0, 1fr))',
        },
        '@media (min-width: 640px)': { '.rohaki-grid-stats': { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' } },
        '@media (min-width: 1024px)': { '.rohaki-grid-stats': { gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' } },
        '.rohaki-grid-features': {
          display: 'grid', gap: theme('spacing.8'), gridTemplateColumns: 'repeat(1, minmax(0, 1fr))',
        },
        '@media (min-width: 1024px)': { '.rohaki-grid-features': { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' } },
        '@media (min-width: 1280px)': { '.rohaki-grid-features': { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' } },
      };
      addComponents(gridComponents);

      // Section patterns
      const sectionComponents = {
        '.rohaki-section': { padding: `${theme('spacing.16')} ${theme('spacing.4')}` },
        '@media (min-width: 1024px)': { '.rohaki-section': { padding: `${theme('spacing.20')} ${theme('spacing.6')}` } },
        '@media (min-width: 1280px)': { '.rohaki-section': { padding: `${theme('spacing.24')} ${theme('spacing.8')}` } },
        '.rohaki-section-hero': {
          padding: `${theme('spacing.20')} ${theme('spacing.4')}`,
          minHeight: '90vh', display: 'flex', alignItems: 'center',
          backgroundImage: theme('backgroundImage.rohaki-hero'),
        },
        '@media (min-width: 1024px)': { '.rohaki-section-hero': { padding: `${theme('spacing.28')} ${theme('spacing.6')}`, minHeight: '100vh' } },
        '.rohaki-section-stats': {
          padding: `${theme('spacing.12')} ${theme('spacing.4')}`,
          backgroundImage: theme('backgroundImage.rohaki-stats'),
        },
        '@media (min-width: 1024px)': { '.rohaki-section-stats': { padding: `${theme('spacing.16')} ${theme('spacing.6')}` } },
        '.rohaki-section-card-grid': { backgroundColor: theme('colors.background.secondary') },
        '.rohaki-section-feature': { backgroundColor: theme('colors.background.DEFAULT') },
        '.rohaki-section-cta': {
          backgroundImage: theme('backgroundImage.rohaki-brand-primary'),
          textAlign: 'center',
        },
      };
      addComponents(sectionComponents);

      // Typography patterns
      const typographyComponents = {
        '.rohaki-heading': {
          fontFamily: theme('fontFamily.display'),
          fontWeight: theme('fontWeight.bold'),
          lineHeight: theme('lineHeight.tight'),
          letterSpacing: theme('letterSpacing.tight'),
          color: theme('colors.text.primary'),
        },
        '.rohaki-h1': { fontSize: theme('fontSize.5xl') },
        '@media (min-width: 1024px)': { '.rohaki-h1': { fontSize: theme('fontSize.6xl') } },
        '.rohaki-h2': { fontSize: theme('fontSize.4xl') },
        '@media (min-width: 1024px)': { '.rohaki-h2': { fontSize: theme('fontSize.5xl') } },
        '.rohaki-h3': { fontSize: theme('fontSize.3xl') },
        '@media (min-width: 1024px)': { '.rohaki-h3': { fontSize: theme('fontSize.4xl') } },
        '.rohaki-h4': { fontSize: theme('fontSize.2xl') },
        '.rohaki-h5': { fontSize: theme('fontSize.xl') },
        '.rohaki-h6': { fontSize: theme('fontSize.lg') },
        '.rohaki-body': {
          fontFamily: theme('fontFamily.sans'),
          fontWeight: theme('fontWeight.normal'),
          lineHeight: theme('lineHeight.relaxed'),
          color: theme('colors.text.secondary'),
        },
        '.rohaki-body-sm': { fontSize: theme('fontSize.sm') },
        '.rohaki-body-base': { fontSize: theme('fontSize.base') },
        '.rohaki-body-lg': { fontSize: theme('fontSize.lg') },
        '.rohaki-stat-value': {
          fontFamily: theme('fontFamily.display'),
          fontWeight: theme('fontWeight.extrabold'),
          lineHeight: theme('lineHeight.tight'),
          fontSize: theme('fontSize.4xl'),
          color: theme('colors.text.inverse'),
        },
        '@media (min-width: 1024px)': { '.rohaki-stat-value': { fontSize: theme('fontSize.5xl') } },
        '.rohaki-stat-label': {
          fontFamily: theme('fontFamily.sans'),
          fontWeight: theme('fontWeight.medium'),
          fontSize: theme('fontSize.sm'),
          color: 'rgba(255, 255, 255, 0.8)',
          textTransform: 'uppercase',
          letterSpacing: theme('letterSpacing.wide'),
        },
      };
      addComponents(typographyComponents);
    },
  ],
};

export default config;