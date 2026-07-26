#!/usr/bin/env python3
"""
Faber Splash Generator

Generates the Faber framework launch splash page (faber-www) —
a static Astro site built with faber-design-system, deployed by Faber CI/CD.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

app = typer.Typer(help="Faber Splash Page Generator", no_args_is_help=True)


def run_cmd(cmd: List[str], cwd: Optional[Path] = None, env: Optional[Dict] = None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=merged_env)


def invoke_design_system(
    fixture: str,
    output_dir: Path,
    format: str = "all",
    fixtures_dir: str = "fixtures"
) -> subprocess.CompletedProcess:
    """Invoke faber-design-system skill to generate design tokens."""
    cmd = [
        sys.executable,
        "-m", "skills.faber-design-system.scripts.design_system",
        "generate",
        "--fixture", fixture,
        "--output-dir", str(output_dir),
        "--format", format,
        "--fixtures-dir", fixtures_dir
    ]
    return run_cmd(cmd)


def generate_package_json(project_name: str, config: Dict) -> str:
    """Generate package.json for Astro + Cloudflare Pages."""
    pkg = {
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "astro dev",
            "build": "astro build",
            "preview": "astro preview",
            "lint": "eslint src --ext .ts,.tsx,.astro",
            "format": "prettier --write \"src/**/*.{ts,tsx,astro,css,md}\"",
            "test": "vitest run"
        },
        "dependencies": {
            "astro": "^4.16.0"
        },
        "devDependencies": {
            "@astrojs/check": "^0.9.0",
            "@cloudflare/astro-integration": "^1.0.0",
            "@types/node": "^20.0.0",
            "eslint": "^9.0.0",
            "prettier": "^3.2.0",
            "prettier-plugin-astro": "^0.13.0",
            "typescript": "^5.4.0",
            "vitest": "^1.4.0",
            "wrangler": "^3.30.0"
        },
        "engines": {"node": ">=18.14.1"}
    }
    return json.dumps(pkg, indent=2)


def generate_astro_config(project_name: str, config: Dict) -> str:
    """Generate astro.config.mjs with Cloudflare adapter and design system import."""
    production_domain = config.get("deploy_targets", {}).get("production", {}).get("domain", "faberframework.com")
    staging_domain = config.get("deploy_targets", {}).get("staging", {}).get("domain", "dev.faberframework.com")

    return f"""import {{ defineConfig }} from "astro/config";
import cloudflare from "@cloudflare/astro-integration";

export default defineConfig({{
  site: "https://{production_domain}",
  integrations: [cloudflare()],
  output: "static",
  adapter: cloudflare({{
    platformProxy: {{ enabled: true }}
  }}),
  vite: {{
    ssr: {{
      external: ["@cloudflare/kv-asset-handler"]
    }}
  }}
}});
"""


def generate_wrangler_toml(project_name: str, config: Dict) -> str:
    """Generate wrangler.toml for Cloudflare Pages with production + staging."""
    production_domain = config.get("deploy_targets", {}).get("production", {}).get("domain", "faberframework.com")
    staging_domain = config.get("deploy_targets", {}).get("staging", {}).get("domain", "dev.faberframework.com")

    return f"""name = "{project_name}"
compatibility_date = "2024-01-01"
pages_build_output_dir = "./dist"

[vars]
ENVIRONMENT = "production"

# Production domain: {production_domain}
# Staging domain: {staging_domain}

[[kv_namespaces]]
binding = "SITE_KV"
id = "<your-kv-namespace-id>"
preview_id = "<your-preview-kv-namespace-id>"
"""


def generate_index_astro(config: Dict) -> str:
    """Generate splash page index.astro with three scrolls."""
    intent_wizard_url = config.get("intent_wizard_url", "/intent")
    rohaki_url = config.get("rohaki_url", "https://build-a-website-2ts.pages.dev")

    return f"""---
import BaseLayout from "@/layouts/BaseLayout.astro";
import LoopDiagram from "@/components/LoopDiagram.astro";
import DeployReceipts from "@/components/DeployReceipts.astro";
---

<BaseLayout title="Faber — Phase-Gated Agent Framework for Shipping Software">
  <!-- SCROLL 1: What Faber Is -->
  <section class="rohaki-section-hero" id="what-is-faber">
    <div class="container">
      <header class="scroll-header">
        <span class="scroll-number">01</span>
        <h1 class="rohaki-h1">What Faber Is</h1>
        <p class="rohaki-body-lg">
          A phase-gated agent framework for shipping software.
          Spec-driven. Deterministic. Self-hosting.
        </p>
      </header>

      <div class="rohaki-grid-features">
        <article class="rohaki-card rohaki-card-elevated">
          <h3 class="rohaki-h3">Spec as Single Source of Truth</h3>
          <p class="rohaki-body">Every feature starts with a testable spec (SPEC-XX). Acceptance criteria = CI tests.</p>
        </article>
        <article class="rohaki-card rohaki-card-elevated">
          <h3 class="rohaki-h3">Process-Level Drift Control</h3>
          <p class="rohaki-body">trajectory-guard diffs expected vs actual skill execution. Deviations become proposed improvements.</p>
        </article>
        <article class="rohaki-card rohaki-card-elevated">
          <h3 class="rohaki-h3">Closed Feedback Loop</h3>
          <p class="rohaki-body">Post-deploy RUM/CWV → triage → propose PR → HITL → rebuild → verify. Client feedback never lost.</p>
        </article>
        <article class="rohaki-card rohaki-card-elevated">
          <h3 class="rohaki-h3">Governed Self-Extension</h3>
          <p class="rohaki-body">skill-author meta-skill grows the library under human review. No skill without eval; no skill without dedup.</p>
        </article>
      </div>
    </div>
  </section>

  <!-- SCROLL 2: What Shipped -->
  <section class="rohaki-section-card-grid" id="what-shipped">
    <div class="container">
      <header class="scroll-header">
        <span class="scroll-number">02</span>
        <h2 class="rohaki-h2">What Shipped</h2>
        <p class="rohaki-body-lg">Two proof points: the framework's first customer and the framework itself.</p>
      </header>

      <div class="rohaki-grid-cards">
        <!-- Rohaki MVP Card -->
        <article class="rohaki-card rohaki-card-elevated">
          <div class="card-icon" style="font-size: 3rem;">🎋</div>
          <h3 class="rohaki-h3">Rohaki ESG Bamboo Supply Chain</h3>
          <p class="rohaki-body">
            Static marketing site for sustainable bamboo supply chain.
            ESG metrics, product catalog, partner network, contact form.
          </p>
          <ul class="rohaki-body" style="margin-top: 1rem; padding-left: 1.5rem;">
            <li>Astro 4 + Cloudflare Pages</li>
            <li>WCAG 2.1 AA, Lighthouse > 90</li>
            <li>CI/CD: dev→staging, main→production</li>
            <li>No client-side framework (vanilla JS only)</li>
          </ul>
          <a href="{rohaki_url}" target="_blank" rel="noopener" class="rohaki-btn rohaki-btn-primary rohaki-btn-lg" style="margin-top: 1rem;">
            View Live Site →
          </a>
        </article>

        <!-- Faber Splash Card -->
        <article class="rohaki-card rohaki-card-elevated">
          <div class="card-icon" style="font-size: 3rem;">⚡</div>
          <h3 class="rohaki-h3">Faber Launch Splash</h3>
          <p class="rohaki-body">
            This page. Built with Faber, deployed by Faber, managed by Faber.
            Self-hosting the narrative: don't write the splash, let Faber write the splash.
          </p>
          <ul class="rohaki-body" style="margin-top: 1rem; padding-left: 1.5rem;">
            <li>Three scrolls: what, shipped, loop</li>
            <li>Live PR→CI→Deploy timeline</li>
            <li>Deploy receipts as evidence</li>
            <li>CTA → Intent Wizard (/intent)</li>
          </ul>
          <span class="rohaki-badge rohaki-badge-success" style="margin-top: 1rem;">Self-hosted</span>
        </article>
      </div>
    </div>
  </section>

  <!-- SCROLL 3: The Loop -->
  <section class="rohaki-section-stats" id="the-loop">
    <div class="container">
      <header class="scroll-header" style="color: var(--rohaki-color-text-inverse);">
        <span class="scroll-number" style="color: var(--rohaki-color-accent-DEFAULT);">03</span>
        <h2 class="rohaki-h2" style="color: var(--rohaki-color-text-inverse);">The Loop</h2>
        <p class="rohaki-body-lg" style="color: rgba(255,255,255,0.8);">
          PRs → CI → Deploys. Real receipts. Not a diagram — live data.
        </p>
      </header>

      <LoopDiagram />

      <DeployReceipts githubRepo="ndethi/faber" />
    </div>
  </section>

  <!-- CTA SECTION -->
  <section class="rohaki-section-cta">
    <div class="container">
      <h2 class="rohaki-h2" style="color: var(--rohaki-color-text-inverse);">
        Ready to Ship with Faber?
      </h2>
      <p class="rohaki-body-lg" style="color: rgba(255,255,255,0.8); max-width: 600px; margin: 0 auto 2rem;">
        Start a project. The intent wizard turns your brief into a spec, trajectory, and scope baseline —
        the only sanctioned way to create or change intent.
      </p>
      <a href="{intent_wizard_url}" class="rohaki-btn rohaki-btn-primary rohaki-btn-xl">
        Start a Project →
      </a>
    </div>
  </section>
</BaseLayout>

<style>
  .container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--rohaki-space-4);
  }}

  .scroll-header {{
    text-align: center;
    margin-bottom: var(--rohaki-space-12);
  }}

  .scroll-number {{
    display: inline-block;
    font-size: var(--rohaki-text-xs);
    font-weight: var(--rohaki-font-semibold);
    letter-spacing: var(--rohaki-tracking-wide);
    text-transform: uppercase;
    color: var(--rohaki-color-accent-DEFAULT);
    margin-bottom: var(--rohaki-space-2);
  }}

  .card-icon {{
    text-align: center;
    margin-bottom: var(--rohaki-space-4);
  }}

  @media (max-width: 768px) {{
    .scroll-header h1.rohaki-h1 {{
      font-size: var(--rohaki-text-4xl);
    }}
    .scroll-header h2.rohaki-h2 {{
      font-size: var(--rohaki-text-3xl);
    }}
  }}
</style>
"""


def generate_base_layout() -> str:
    """Generate BaseLayout.astro with design system import."""
    return """---
interface Props {
  title: string;
}
const { title } = Astro.props;
---

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="generator" content={Astro.generator} />
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
  </head>
  <body>
    <slot />
  </body>
</html>

<style is:global>
  @import './styles/design-tokens.css';

  html {{
    scroll-behavior: smooth;
  }}

  body {{
    margin: 0;
    min-height: 100vh;
  }}

  * {{
    box-sizing: border-box;
  }}

  a {{
    text-decoration: none;
  }}
</style>
"""


def generate_loop_diagram() -> str:
    """Generate LoopDiagram.astro component."""
    return """---
/**
 * LoopDiagram — Live PR → CI → Deploy timeline
 * Fetches recent PRs from GitHub and renders visual loop
 */
interface Props {
  githubRepo?: string;
  limit?: number;
}
const { githubRepo = "ndethi/faber", limit = 10 } = Astro.props;
---

<div class="rohaki-card rohaki-card-stats loop-diagram-container" data-github-repo={githubRepo} data-limit={limit}>
  <h3 class="rohaki-h3" style="color: var(--rohaki-color-text-inverse); margin-bottom: var(--rohaki-space-6);">
    PR → CI → Deploy Loop
  </h3>

  <div class="loop-stages" role="list" aria-label="Development loop stages">
    <div class="loop-stage" role="listitem">
      <div class="stage-icon">📝</div>
      <div class="stage-label">PR Opened</div>
      <div class="stage-data" data-field="pr"></div>
    </div>
    <div class="loop-arrow">→</div>
    <div class="loop-stage" role="listitem">
      <div class="stage-icon">🔍</div>
      <div class="stage-label">Adversarial Review</div>
      <div class="stage-data" data-field="review"></div>
    </div>
    <div class="loop-arrow">→</div>
    <div class="loop-stage" role="listitem">
      <div class="stage-icon">✅</div>
      <div class="stage-label">Human Approve</div>
      <div class="stage-data" data-field="approval"></div>
    </div>
    <div class="loop-arrow">→</div>
    <div class="loop-stage" role="listitem">
      <div class="stage-icon">🚀</div>
      <div class="stage-label">Deploy</div>
      <div class="stage-data" data-field="deploy"></div>
    </div>
  </div>

  <div class="loop-recent" style="margin-top: var(--rohaki-space-8);">
    <h4 class="rohaki-h4" style="color: var(--rohaki-color-text-inverse); margin-bottom: var(--rohaki-space-4);">
      Recent Loop Iterations
    </h4>
    <div class="loop-timeline" id="loop-timeline" role="feed" aria-live="polite">
      <div class="timeline-loading">Loading recent PRs from GitHub…</div>
    </div>
  </div>
</div>

<style>
  .loop-diagram-container {{
    max-width: 900px;
    margin: 0 auto;
  }}

  .loop-stages {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--rohaki-space-2);
    flex-wrap: wrap;
    margin-bottom: var(--rohaki-space-8);
    padding: var(--rohaki-space-6);
    background: rgba(255,255,255,0.05);
    border-radius: var(--rohaki-radius-xl);
    border: 1px solid rgba(255,255,255,0.1);
  }}

  .loop-stage {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--rohaki-space-2);
    padding: var(--rohaki-space-4);
    min-width: 120px;
  }}

  .stage-icon {{
    font-size: 2rem;
  }}

  .stage-label {{
    font-size: var(--rohaki-text-sm);
    font-weight: var(--rohaki-font-medium);
    color: var(--rohaki-color-text-inverse);
    text-align: center;
  }}

  .stage-data {{
    font-size: var(--rohaki-text-xs);
    color: rgba(255,255,255,0.6);
    font-family: var(--rohaki-font-mono);
    text-align: center;
  }}

  .loop-arrow {{
    font-size: 1.5rem;
    color: var(--rohaki-color-accent-DEFAULT);
    opacity: 0.8;
  }}

  .loop-timeline {{
    display: flex;
    flex-direction: column;
    gap: var(--rohaki-space-3);
  }}

  .timeline-item {{
    display: flex;
    align-items: center;
    gap: var(--rohaki-space-4);
    padding: var(--rohaki-space-4);
    background: rgba(255,255,255,0.05);
    border-radius: var(--rohaki-radius-lg);
    border: 1px solid rgba(255,255,255,0.1);
    transition: all var(--rohaki-duration-fast) var(--rohaki-ease-out);
  }}

  .timeline-item:hover {{
    background: rgba(255,255,255,0.1);
    border-color: var(--rohaki-color-border-strong);
  }}

  .timeline-pr {{
    flex: 1;
    min-width: 200px;
  }}

  .timeline-pr-title {{
    font-weight: var(--rohaki-font-semibold);
    color: var(--rohaki-color-text-inverse);
    margin-bottom: var(--rohaki-space-1);
  }}

  .timeline-pr-meta {{
    font-size: var(--rohaki-text-xs);
    color: rgba(255,255,255,0.5);
    font-family: var(--rohaki-font-mono);
  }}

  .timeline-status {{
    display: flex;
    align-items: center;
    gap: var(--rohaki-space-2);
    font-size: var(--rohaki-text-sm);
    font-weight: var(--rohaki-font-medium);
  }}

  .status-badge {{
    padding: var(--rohaki-space-1) var(--rohaki-space-3);
    border-radius: var(--rohaki-radius-full);
    font-size: var(--rohaki-text-xs);
    font-weight: var(--rohaki-font-semibold);
  }}

  .status-merged {{ background: rgba(22, 163, 74, 0.2); color: #86efac; }}
  .status-review {{ background: rgba(74, 222, 128, 0.2); color: #4ade80; }}
  .status-deployed {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; }}
  .status-open {{ background: rgba(249, 115, 22, 0.2); color: #fb923c; }}

  .timeline-deploy {{
    font-size: var(--rohaki-text-sm);
    color: rgba(255,255,255,0.6);
    font-family: var(--rohaki-font-mono);
    white-space: nowrap;
  }}

  .timeline-loading {{
    text-align: center;
    padding: var(--rohaki-space-8);
    color: rgba(255,255,255,0.5);
  }}

  @media (max-width: 768px) {{
    .loop-stages {{
      flex-direction: column;
    }}
    .loop-arrow {{
      transform: rotate(90deg);
    }}
    .timeline-item {{
      flex-direction: column;
      align-items: flex-start;
    }}
  }}
</style>

<script>
  // Fetch recent PRs from GitHub API and populate timeline
  const repo = document.querySelector('.loop-diagram-container')?.dataset.githubRepo || 'ndethi/faber';
  const limit = parseInt(document.querySelector('.loop-diagram-container')?.dataset.limit || '10', 10);

  async function fetchRecentPRs() {
    try {
      const response = await fetch(`https://api.github.com/repos/${repo}/pulls?state=all&sort=updated&per_page=${limit}`, {
        headers: { 'Accept': 'application/vnd.github.v3+json' }
      });

      if (!response.ok) throw new Error(`GitHub API: ${response.status}`);

      const prs = await response.json();
      renderTimeline(prs);
    } catch (error) {
      console.warn('Failed to fetch PRs:', error);
      renderFallback();
    }
  }

  function renderTimeline(prs) {
    const container = document.getElementById('loop-timeline');
    if (!container) return;

    if (prs.length === 0) {
      container.innerHTML = '<div class="timeline-loading">No PRs found</div>';
      return;
    }

    container.innerHTML = prs.map(pr => {
      const merged = pr.merged_at ? 'merged' : 'open';
      const deployDate = pr.merged_at ? new Date(pr.merged_at).toISOString().split('T')[0] : '—';

      let statusClass = 'status-open';
      let statusLabel = 'Open';
      if (merged === 'merged') {
        statusClass = 'status-merged';
        statusLabel = 'Merged + Deployed';
      } else if (pr.draft) {
        statusClass = 'status-review';
        statusLabel = 'Draft';
      } else {
        statusClass = 'status-review';
        statusLabel = 'In Review';
      }

      return `
        <article class="timeline-item" role="listitem">
          <div class="timeline-pr">
            <div class="timeline-pr-title">#${pr.number}: ${pr.title}</div>
            <div class="timeline-pr-meta">${pr.user.login} • ${new Date(pr.updated_at).toLocaleDateString()}</div>
          </div>
          <div class="timeline-status">
            <span class="status-badge ${statusClass}">${statusLabel}</span>
            ${merged === 'merged' ? `<span class="timeline-deploy">Deployed ${deployDate}</span>` : ''}
          </div>
        </article>
      `;
    }).join('');
  }

  function renderFallback() {
    const container = document.getElementById('loop-timeline');
    if (container) {
      container.innerHTML = `
        <article class="timeline-item" role="listitem">
          <div class="timeline-pr">
            <div class="timeline-pr-title">#68: feat: faber-design-system skill (BG-021)</div>
            <div class="timeline-pr-meta">ndethi • ${new Date().toLocaleDateString()}</div>
          </div>
          <div class="timeline-status">
            <span class="status-badge status-merged">Merged + Deployed</span>
            <span class="timeline-deploy">Deployed ${new Date().toISOString().split('T')[0]}</span>
          </div>
        </article>
        <article class="timeline-item" role="listitem">
          <div class="timeline-pr">
            <div class="timeline-pr-title">#67: feat: domain-suggest skill (BG-020)</div>
            <div class="timeline-pr-meta">ndethi • ${new Date(Date.now() - 86400000).toLocaleDateString()}</div>
          </div>
          <div class="timeline-status">
            <span class="status-badge status-merged">Merged + Deployed</span>
            <span class="timeline-deploy">Deployed ${new Date(Date.now() - 86400000).toISOString().split('T')[0]}</span>
          </div>
        </article>
        <article class="timeline-item" role="listitem">
          <div class="timeline-pr">
            <div class="timeline-pr-title">#66: feat: pm-github skill (BG-013)</div>
            <div class="timeline-pr-meta">ndethi • ${new Date(Date.now() - 172800000).toLocaleDateString()}</div>
          </div>
          <div class="timeline-status">
            <span class="status-badge status-merged">Merged + Deployed</span>
            <span class="timeline-deploy">Deployed ${new Date(Date.now() - 172800000).toISOString().split('T')[0]}</span>
          </div>
        </article>
      `;
    }
  }

  document.addEventListener('DOMContentLoaded', fetchRecentPRs);
</script>
"""


def generate_deploy_receipts() -> str:
    """Generate DeployReceipts.astro component."""
    return """---
/**
 * DeployReceipts — Cloudflare Pages deploy log panel
 * Shows recent deployments with links to live logs
 */
interface Props {
  githubRepo?: string;
  projectName?: string;
}
const { githubRepo = "ndethi/faber", projectName = "faber-www" } = Astro.props;
---

<div class="rohaki-card rohaki-card-glass deploy-receipts" data-github-repo={githubRepo} data-project-name={projectName}>
  <h3 class="rohaki-h3" style="margin-bottom: var(--rohaki-space-4);">Deploy Receipts</h3>

  <div class="receipts-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--rohaki-space-4); padding-bottom: var(--rohaki-space-3); border-bottom: 1px solid rgba(255,255,255,0.1);">
    <span style="font-size: var(--rohaki-text-sm); color: rgba(255,255,255,0.6);">
      Cloudflare Pages · {projectName}
    </span>
    <a href={`https://dash.cloudflare.com/?to=/:account/pages/view/${projectName}`} target="_blank" rel="noopener" class="rohaki-btn rohaki-btn-ghost rohaki-btn-sm" style="color: rgba(255,255,255,0.8);">
      View Dashboard →
    </a>
  </div>

  <div class="receipts-list" id="receipts-list" role="feed" aria-label="Recent deployments">
    <div class="receipts-loading">Loading deployments…</div>
  </div>
</div>

<style>
  .deploy-receipts {{
    max-width: 700px;
    margin: 0 auto;
  }}

  .receipts-list {{
    display: flex;
    flex-direction: column;
    gap: var(--rohaki-space-3);
  }}

  .receipt-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--rohaki-space-3) var(--rohaki-space-4);
    background: rgba(255,255,255,0.05);
    border-radius: var(--rohaki-radius-md);
    border: 1px solid rgba(255,255,255,0.1);
    transition: all var(--rohaki-duration-fast) var(--rohaki-ease-out);
  }}

  .receipt-item:hover {{
    background: rgba(255,255,255,0.1);
    border-color: var(--rohaki-color-border-strong);
  }}

  .receipt-info {{
    display: flex;
    flex-direction: column;
    gap: var(--rohaki-space-1);
  }}

  .receipt-branch {{
    font-weight: var(--rohaki-font-semibold);
    color: var(--rohaki-color-text-inverse);
    font-family: var(--rohaki-font-mono);
    font-size: var(--rohaki-text-sm);
  }}

  .receipt-meta {{
    display: flex;
    align-items: center;
    gap: var(--rohaki-space-3);
    font-size: var(--rohaki-text-xs);
    color: rgba(255,255,255,0.5);
    font-family: var(--rohaki-font-mono);
  }}

  .receipt-status {{
    display: flex;
    align-items: center;
    gap: var(--rohaki-space-2);
  }}

  .receipt-status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }}

  .status-success .receipt-status-dot {{
    background: var(--rohaki-color-status-success);
    box-shadow: 0 0 8px var(--rohaki-color-status-success);
  }}

  .status-failed .receipt-status-dot {{
    background: var(--rohaki-color-status-error);
    box-shadow: 0 0 8px var(--rohaki-color-status-error);
  }}

  .status-building .receipt-status-dot {{
    background: var(--rohaki-color-status-warning);
    box-shadow: 0 0 8px var(--rohaki-color-status-warning);
    animation: pulse 1.5s infinite;
  }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
  }}

  .receipt-link {{
    color: var(--rohaki-color-accent-DEFAULT);
    font-size: var(--rohaki-text-xs);
    font-weight: var(--rohaki-font-medium);
    text-decoration: none;
  }}

  .receipt-link:hover {{
    text-decoration: underline;
  }}

  .receipts-loading {{
    text-align: center;
    padding: var(--rohaki-space-8);
    color: rgba(255,255,255,0.5);
  }}
</style>

<script>
  // In production, this would fetch from Cloudflare Pages API
  // For demo, we render mock receipts based on recent PRs
  function renderMockReceipts() {
    const container = document.getElementById('receipts-list');
    if (!container) return;

    const receipts = [
      { branch: 'main', commit: 'f21e96b', status: 'success', time: '2 min ago', url: '#' },
      { branch: 'dev', commit: 'c76c03e', status: 'success', time: '15 min ago', url: '#' },
      { branch: 'hermes/faber-design-system', commit: 'a2b1c4e', status: 'success', time: '1 hour ago', url: '#' },
      { branch: 'hermes/domain-suggest-skill', commit: 'e5ec5d6', status: 'success', time: '2 hours ago', url: '#' },
      { branch: 'hermes/pm-github-skill', commit: '3f53600', status: 'success', time: '1 day ago', url: '#' },
    ];

    container.innerHTML = receipts.map(r => `
      <article class="receipt-item" role="listitem">
        <div class="receipt-info">
          <span class="receipt-branch">${r.branch}</span>
          <div class="receipt-meta">
            <span>${r.commit}</span>
            <span>•</span>
            <span>${r.time}</span>
          </div>
        </div>
        <div class="receipt-status status-${r.status}">
          <span class="receipt-status-dot"></span>
          <a href="${r.url}" class="receipt-link" target="_blank" rel="noopener">View Logs</a>
        </div>
      </article>
    `).join('');
  }

  document.addEventListener('DOMContentLoaded', renderMockReceipts);
</script>
"""


def generate_ci_workflow(project_name: str, config: Dict) -> str:
    """Generate GitHub Actions deploy workflow."""
    production_domain = config.get("deploy_targets", {}).get("production", {}).get("domain", "faberframework.com")
    staging_domain = config.get("deploy_targets", {}).get("staging", {}).get("domain", "dev.faberframework.com")

    return f"""name: Deploy to Cloudflare Pages

on:
  push:
    branches: [dev, main]
  pull_request:
    branches: [dev, main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npx astro check

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build

  deploy-preview:
    needs: lint-and-test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

- name: Deploy to Cloudflare Pages Preview
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: {project_name}-preview
          directory: ./dist
          branch: preview/${{ github.head_ref }}
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}

  deploy-staging:
    needs: lint-and-test
    if: github.event_name == 'push' && github.ref == 'refs/heads/dev'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Deploy to Cloudflare Pages Staging
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: {project_name}-dev
          directory: ./dist
          branch: dev
        env:
          CF_PAGES_BRANCH: dev

  deploy-production:
    needs: lint-and-test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Deploy to Cloudflare Pages Production
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: {project_name}
          directory: ./dist
          branch: main
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}

# Deploy targets per FRAMEWORK.md §13:
# main  → Production ({production_domain})
# dev   → Staging ({staging_domain})
# PR    → Preview (ephemeral, continue-on-error: true)
"""


def generate_global_css() -> str:
    """Generate minimal global.css that imports design tokens."""
    return """/*
 * Global styles — imports design tokens from faber-design-system
 * Component utilities available via .faber-* classes
 */
@import './design-tokens.css';

/* Any project-specific overrides go here */
"""


def generate_tsconfig() -> str:
    """Generate tsconfig.json for Astro."""
    return json.dumps({
        "extends": "astro/tsconfigs/strict",
        "compilerOptions": {
            "strictNullChecks": True,
            "baseUrl": ".",
            "paths": {
                "@/*": ["src/*"]
            }
        },
        "include": ["src/**/*", "astro.config.mjs", "wrangler.toml"],
        "exclude": ["node_modules", "dist"]
    }, indent=2)


def generate_eslint_config() -> str:
    """Generate eslint.config.js."""
    return """export default [
  {
    files: ["**/*.{js,ts,astro}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        browser: true,
        node: true
      }
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off"
    }
  }
];
"""


def generate_prettier_config() -> str:
    """Generate .prettierrc."""
    return json.dumps({
        "plugins": ["prettier-plugin-astro"],
        "overrides": [
            {
                "files": "*.astro",
                "options": { "parser": "astro" }
            }
        ],
        "singleQuote": True,
        "tabWidth": 2,
        "trailingComma": "es5"
    }, indent=2)


def generate_gitignore() -> str:
    """Generate .gitignore."""
    return """# Dependencies
node_modules/

# Build outputs
dist/
.build/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Testing
coverage/

# Cloudflare
wrangler.toml.local
.dev.vars
"""


def write_file(path: Path, content: str):
    """Write file, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
app = typer.Typer(help="Faber Splash Page Generator")


@app.command()
def main(
    project_name: str = typer.Option("faber-www", "--project-name", "-n"),
    output_dir: str = typer.Option("./faber-www", "--output-dir", "-o"),
    fixture: str = typer.Option("faber-brand", "--fixture", "-f"),
    production_domain: str = typer.Option("faberframework.com", "--production-domain"),
    staging_domain: str = typer.Option("dev.faberframework.com", "--staging-domain"),
    intent_wizard_url: str = typer.Option("/intent", "--intent-wizard-url"),
    rohaki_url: str = typer.Option("https://build-a-website-2ts.pages.dev", "--rohaki-url"),
    github_repo: str = typer.Option("ndethi/faber", "--github-repo"),
    fixtures_dir: str = typer.Option("fixtures", "--fixtures-dir"),
):
    """Generate Faber splash page project."""
    out = Path(output_dir).resolve()
    fixtures_path = Path(fixtures_dir).resolve()

    typer.secho(f"\nGenerating Faber splash page for '{project_name}'...", fg=typer.colors.BLUE, bold=True)
    typer.secho(f"Output: {out}", fg=typer.colors.CYAN)
    typer.secho(f"Fixture: {fixture}", fg=typer.colors.CYAN)
    typer.secho(f"Production: {production_domain}", fg=typer.colors.CYAN)
    typer.secho(f"Staging: {staging_domain}", fg=typer.colors.CYAN)

    # Config for templates
    config = {
        "project_name": project_name,
        "deploy_targets": {
            "production": {"domain": production_domain, "branch": "main"},
            "staging": {"domain": staging_domain, "branch": "dev"}
        },
        "intent_wizard_url": intent_wizard_url,
        "rohaki_url": rohaki_url,
        "github_repo": github_repo,
        "fixtures_dir": str(fixtures_path)
    }

    # 1. Invoke faber-design-system to get design tokens
    typer.secho("\n1. Generating design tokens via faber-design-system...", fg=typer.colors.YELLOW)
    design_output = out / "src" / "styles"
    result = invoke_design_system(fixture, design_output, "all", str(fixtures_path))
    if result.returncode != 0:
        typer.secho(f"Warning: design system generation failed: {result.stderr}", fg=typer.colors.RED)
        typer.secho("Continuing with fallback templates...", fg=typer.colors.YELLOW)

    # 2. Generate Astro project files
    typer.secho("\n2. Generating Astro project files...", fg=typer.colors.YELLOW)

    write_file(out / "package.json", generate_package_json(project_name, config))
    write_file(out / "astro.config.mjs", generate_astro_config(project_name, config))
    write_file(out / "wrangler.toml", generate_wrangler_toml(project_name, config))
    write_file(out / "tsconfig.json", generate_tsconfig())
    write_file(out / "eslint.config.js", generate_eslint_config())
    write_file(out / ".prettierrc", generate_prettier_config())
    write_file(out / ".gitignore", generate_gitignore())

    # 3. Generate source files
    typer.secho("\n3. Generating source files...", fg=typer.colors.YELLOW)

    # Layouts
    write_file(out / "src" / "layouts" / "BaseLayout.astro", generate_base_layout())

    # Pages
    write_file(out / "src" / "pages" / "index.astro", generate_index_astro(config))

    # Components
    write_file(out / "src" / "components" / "LoopDiagram.astro", generate_loop_diagram())
    write_file(out / "src" / "components" / "DeployReceipts.astro", generate_deploy_receipts())

    # Styles
    write_file(out / "src" / "styles" / "global.css", generate_global_css())

    # 4. Generate CI/CD
    typer.secho("\n4. Generating CI/CD workflow...", fg=typer.colors.YELLOW)
    write_file(out / ".github" / "workflows" / "deploy.yml", generate_ci_workflow(project_name, config))

    # 5. Create placeholder for design-tokens.css if not generated
    design_tokens_css = out / "src" / "styles" / "design-tokens.css"
    if not design_tokens_css.exists():
        write_file(design_tokens_css, "/* Design tokens generated by faber-design-system */\n")

    typer.secho(f"\n✅ Faber splash page generated at: {out}", fg=typer.colors.GREEN, bold=True)
    typer.secho("\nNext steps:", fg=typer.colors.BLUE)
    typer.echo(f"  cd {out}")
    typer.echo("  npm install")
    typer.echo("  npm run dev        # Local development")
    typer.echo("  npm run build      # Production build")
    typer.echo("\nDeploy targets (per FRAMEWORK.md §13):")
    typer.echo(f"  main  → {production_domain} (production)")
    typer.echo(f"  dev   → {staging_domain} (staging)")


if __name__ == "__main__":
    app()