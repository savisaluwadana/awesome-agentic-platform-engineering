# Contributing

Thanks for helping developers discover practical, trustworthy projects for agentic platform engineering.

## What belongs here?

Open-source tools and resources that enable agent workflows, platform automation, tool connectivity/MCP, developer platforms and control planes, deployment, evaluation, observability, governance, or infrastructure security. Foundational projects are welcome when their relationship to agentic platform engineering is clear.

A submission should have a working public repository, identifiable maintainers, an understandable license, and evidence of what it does. Experimental projects may be included; we do not automatically imply production readiness. No pay-to-play entries, affiliate tracking URLs, duplicated entries, or empty marketing landing pages.

## Add a project

Edit the **Directory** section in README.md. Keep the category headings unchanged unless proposing a new one in your pull request. The site reads the Markdown directly.

```markdown
### MCP & Tool Infrastructure

- [Example Project](https://github.com/example-org/example-project) — A clear, neutral sentence describing what it helps engineers do.
```

Use one bullet per project; the dash in the example can also be an em dash. Include only the direct project repository URL. The description should explain the benefit or capability, not announce that the product is "world-class", "revolutionary", or "the best". Put the most directly relevant projects first within a category, and avoid changing existing entries unnecessarily.

## Pull request checklist

- [ ] The project is open source and relevant to this directory.
- [ ] The repository URL is correct and not a duplicate.
- [ ] The description is factual and concise.
- [ ] The bullet is inside `## Directory` and a `###` category.
- [ ] `python3 scripts/build_catalog.py` succeeds.
- [ ] `python3 -m unittest discover -s tests` passes.

## How the website works

`scripts/build_catalog.py` parses the README and generates `site/catalog.json`. It adds public repository metadata (stars, language, homepage, etc.) when GitHub API access is available. If the API is unavailable, the directory still builds, but unavailable metadata is omitted, not fabricated.

The front end is static HTML, CSS, and JavaScript. There is no extra listing database. GitHub Actions runs on changes to the README or website and once per day to refresh GitHub stars.

Run locally:

```bash
python3 scripts/build_catalog.py
python3 -m http.server --directory site 8000
```

Then visit http://localhost:8000. To deploy, enable GitHub Pages with **GitHub Actions** as the source in repository Settings → Pages. The `deploy-pages` workflow handles publication after merges to `main`.

## Moderation

Maintainers may edit categories, remove broken or abandoned links, reject off-topic submissions, or correct misleading descriptions. Inclusion and ranking are editorial, not certifications or product recommendations. GitHub star counts are external social signals and not a substitute for security or technical evaluation.
