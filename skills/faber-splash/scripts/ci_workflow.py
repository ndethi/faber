#!/usr/bin/env python3
"""
CI/CD Workflow Generator for Faber Splash Page
Generates .github/workflows/deploy.yml for Astro + Cloudflare Pages
"""

def generate_ci_workflow(project_name: str, config: Dict) -> str:
    """Generate GitHub Actions workflow for Cloudflare Pages deployment."""
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

  deploy-staging:
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

  deploy-staging-branch:
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
"""

if __name__ == "__main__":
    import sys
    import json
    config = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(generate_ci_workflow("faber-www", config))