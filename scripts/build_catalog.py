#!/usr/bin/env python3
"""Compile the README's curated directory into a static website catalog.

No third-party dependencies. The README remains the only list of projects.
When GITHUB_TOKEN is present, GitHub stars and other repository metadata are
enriched at build time. Failed API requests never create invented metrics.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape as html_escape
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SITE = ROOT / "site"
SITE_URL = "https://savisaluwadana.github.io/awesome-agentic-platform-engineering/"
ENTRY = re.compile(
    r"^- \[([^\]]+)\]\((https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/?\)"
    r"\s*[—–-]\s*(\S.*)$"
)
HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*$")


def parse_readme(markdown: str) -> list[dict]:
    """Return ordered entries, with validation instead of silently losing items."""
    in_directory = False
    category = None
    projects = []
    seen = set()

    for number, raw in enumerate(markdown.splitlines(), start=1):
        line = raw.strip()
        if line == "## Directory":
            in_directory = True
            category = None
            continue
        if in_directory and line.startswith("## "):
            break
        if not in_directory:
            continue
        if line.startswith("### "):
            category = line[4:].strip()
            if not category:
                raise ValueError(f"README line {number}: empty category")
        elif line.startswith("- "):
            if not category:
                raise ValueError(f"README line {number}: item outside a category")
            match = ENTRY.fullmatch(line)
            if not match:
                raise ValueError(
                    f"README line {number}: expected '- [Name](https://github.com/owner/repo) — Description'"
                )
            name, url, description = match.groups()
            description = description.strip()
            if not description or len(description) > 320:
                raise ValueError(f"README line {number}: description must be 1–320 characters")
            parts = urlparse(url).path.strip("/").split("/")
            owner, repository = parts
            slug = f"{owner}-{repository}".lower()
            if slug in seen:
                raise ValueError(f"README line {number}: duplicate project {url}")
            seen.add(slug)
            projects.append({
                "id": slug,
                "name": name.strip(),
                "description": description,
                "category": category,
                "repo": f"{owner}/{repository}",
                "repoUrl": url.rstrip("/"),
                "avatar": f"https://github.com/{quote(owner, safe='')}.png?size=96",
                "stars": None,
                "language": None,
                "homepage": None,
                "updatedAt": None,
                "order": len(projects),
                "pageUrl": SITE_URL + "projects/" + slug + "/",
            })
    if not in_directory or not projects:
        raise ValueError("README must contain '## Directory' with at least one valid item")
    return projects


def fetch_github(repo: str, token: str | None) -> dict:
    url = f"https://api.github.com/repos/{quote(repo, safe='/')}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "awesome-agentic-platform-engineering-directory",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}

    homepage = payload.get("homepage")
    if not isinstance(homepage, str) or not homepage.startswith("https://"):
        homepage = None
    stars = payload.get("stargazers_count")
    return {
        "stars": stars if type(stars) is int and stars >= 0 else None,
        "language": payload.get("language") if isinstance(payload.get("language"), str) else None,
        "homepage": homepage,
        "updatedAt": payload.get("pushed_at") if isinstance(payload.get("pushed_at"), str) else None,
    }


def build(markdown: str, enrich: bool = False, token: str | None = None) -> dict:
    projects = parse_readme(markdown)
    if enrich:
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda p: fetch_github(p["repo"], token), projects))
        for project, info in zip(projects, results):
            project.update(info)

    categories = []
    for p in projects:
        if p["category"] not in categories:
            categories.append(p["category"])
    return {
        "siteName": "Awesome Agentic Platform Engineering",
        "source": "https://github.com/savisaluwadana/awesome-agentic-platform-engineering",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "total": len(projects),
        "categories": categories,
        "projects": projects,
    }



# Keep directory content accessible even when JavaScript is not executed. The
# exact same parsed README entries power HTML, JSON, Markdown and JSON-LD.
def escaped(value: object) -> str:
    return html_escape(str(value), quote=True)


def json_script(data: object) -> str:
    # Escaping '<' prevents an untrusted project description from closing a script.
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def replacement_between(text: str, name: str, replacement: str) -> str:
    start = f"<!-- {name}:START -->"
    end = f"<!-- {name}:END -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Expected exactly one pair of {name} markers in site/index.html")
    a = text.index(start) + len(start)
    b = text.index(end)
    if a > b:
        raise ValueError(f"Markers for {name} are out of order")
    return text[:a] + "\n" + replacement + "\n" + text[b:]


def home_item_list(catalog: dict) -> str:
    entries = []
    for p in catalog["projects"]:
        entries.append(
            '<article class="product-card" data-ssr="true">'
            f'<span class="product-rank">{p["order"] + 1:02d}</span>'
            '<div class="product-info">'
            f'<h3><a href="{escaped(p["pageUrl"])}">{escaped(p["name"])}</a></h3>'
            f'<p class="product-description">{escaped(p["description"])}</p>'
            f'<p class="card-meta"><span class="meta-tag">{escaped(p["category"])}</span> '
            f'<a href="{escaped(p["repoUrl"])}" rel="noopener noreferrer">GitHub repository ↗</a></p>'
            "</div></article>"
        )
    return "\n".join(entries)


def homepage_schema(catalog: dict) -> dict:
    listing = {
        "@type": "ItemList",
        "name": "Open-source agentic platform engineering projects",
        "numberOfItems": catalog["total"],
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": p["order"] + 1,
                "name": p["name"],
                "url": p["pageUrl"],
                "description": p["description"],
            } for p in catalog["projects"]
        ],
    }
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": catalog["siteName"],
                "url": SITE_URL,
                "description": "Independent, community-maintained directory of open-source agent frameworks, Kubernetes developer platforms, MCP, GitOps, observability and security projects.",
            },
            {"@type": "CollectionPage", "name": catalog["siteName"],
             "url": SITE_URL, "mainEntity": listing},
        ],
    }



def homepage_navigation(catalog: dict) -> str:
    links = [
        '<a class="category-button active" href="#directory">'
        '<span class="category-name">▦ All projects</span></a>'
    ]
    for cat in catalog["categories"]:
        url = SITE_URL + "categories/" + slugify(cat) + "/"
        links.append(
            f'<a class="category-button" href="{escaped(url)}">'
            f'<span class="category-name">{escaped(cat)}</span></a>'
        )
    return "\n".join(links)


def render_homepage(catalog: dict) -> None:
    index = SITE / "index.html"
    html = index.read_text(encoding="utf-8")
    html = replacement_between(html, "CATALOG", home_item_list(catalog))
    html = replacement_between(html, "NAV", homepage_navigation(catalog))
    html = replacement_between(html, "SCHEMA", '<script type="application/ld+json">'
                                + json_script(homepage_schema(catalog)) + "</script>")
    index.write_text(html, encoding="utf-8")


def detail_page(project: dict) -> str:
    title = project["name"]
    desc = project["description"]
    url = project["pageUrl"]
    repo = project["repoUrl"]
    home = project["homepage"]
    details = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": f"{title} | Awesome Agentic Platform Engineering",
             "description": desc, "url": url},
            {"@type": "SoftwareSourceCode",
             "name": title, "description": desc, "codeRepository": repo,
             "url": repo, "applicationCategory": project["category"],
             **({"programmingLanguage": project["language"]} if project["language"] else {})},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Directory", "item": SITE_URL},
                {"@type": "ListItem", "position": 2, "name": title, "item": url},
            ]},
        ],
    }
    lang = (f'<dt>Primary language</dt><dd>{escaped(project["language"])}</dd>'
            if project["language"] else "")
    link = (f'<a href="{escaped(home)}" rel="noopener noreferrer">Project website ↗</a>'
            if home else "")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index,follow,max-snippet:-1">
<meta name="description" content="{escaped(desc)[:450]}">
<title>{escaped(title)} | Awesome Agentic Platform Engineering</title>
<link rel="canonical" href="{escaped(url)}">
<link rel="icon" href="../../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../styles.css">
<link rel="alternate" type="application/json" title="Complete directory catalog" href="../../catalog.json">
<meta property="og:title" content="{escaped(title)} | Agentic Platform Engineering">
<meta property="og:description" content="{escaped(desc)[:450]}">
<meta property="og:url" content="{escaped(url)}">
<meta property="og:type" content="article">
<script type="application/ld+json">{json_script(details)}</script>
</head>
<body>
<header class="site-header"><div class="container nav-inner">
<a class="brand" href="../../"><span class="brand-logo" aria-hidden="true">✳</span>
<span class="brand-name">awesome<span class="brand-accent">/</span>agentic<span class="brand-sub">platform engineering</span></span></a>
<nav class="header-links"><a href="../../#directory">All projects</a> <a href="../../catalog.json">Catalog JSON</a></nav>
</div></header>
<main class="container"><article class="agent-detail">
<a class="detail-back" href="../../#directory">← Back to directory</a>
<p class="section-kicker">OPEN-SOURCE PROJECT · {escaped(project["category"])}</p>
<h1>{escaped(title)}</h1>
<p class="detail-summary">{escaped(desc)}</p>
<dl class="project-facts">
<dt>Category</dt><dd>{escaped(project["category"])}</dd>
<dt>Repository</dt><dd><a href="{escaped(repo)}" rel="noopener noreferrer">{escaped(project["repo"])}</a></dd>
{lang}
</dl>
<div class="detail-actions"><a class="button button-primary" href="{escaped(repo)}" rel="noopener noreferrer">View source on GitHub ↗</a>{link}</div>
<section class="detail-context">
<h2>About this listing</h2>
<p>This is a community-maintained entry in Awesome Agentic Platform Engineering. It describes a project that relates to
AI agent workflows or their supporting cloud-native platforms. Being listed does not mean the project is agent-native,
security-audited, production-ready, or endorsed by the directory maintainers.</p>
<h2>Where is the authoritative source?</h2>
<p>The project's own <a href="{escaped(repo)}" rel="noopener noreferrer">GitHub repository</a> is the authoritative source for installation,
license, compatibility, releases, and feature details. The description above is curated in the directory's
<a href="https://github.com/savisaluwadana/awesome-agentic-platform-engineering/blob/main/README.md">public README</a>.
</p>
<h2>Want to correct this listing?</h2><p><a href="https://github.com/savisaluwadana/awesome-agentic-platform-engineering/edit/main/README.md">Submit a README change</a> through a pull request. The site will rebuild after merge.</p>
</section>
</article></main>
<footer class="site-footer"><div class="container footer-inner">
<p>Independent, open-source discovery. No paid rankings or invented reviews.</p>
<a href="../../">Browse all projects →</a></div></footer>
</body></html>
'''


def category_page(category: str, projects: list[dict]) -> str:
    name = escaped(category)
    slug = slugify(category)
    url = SITE_URL + "categories/" + slug + "/"
    entries = "\n".join(
        f'<li><h2><a href="{escaped(p["pageUrl"])}">{escaped(p["name"])}</a></h2>'
        f'<p>{escaped(p["description"])}</p></li>' for p in projects
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage", "name": f"{category} | Agentic Platform Engineering",
        "url": url, "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": p["name"], "url": p["pageUrl"]}
            for i, p in enumerate(projects)
        ]},
    }
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} | Awesome Agentic Platform Engineering</title>
<meta name="description" content="Explore {len(projects)} open-source projects in {name}. Community-maintained references for agentic platform engineering.">
<link rel="canonical" href="{escaped(url)}"><link rel="stylesheet" href="../../styles.css">
<script type="application/ld+json">{json_script(schema)}</script></head>
<body><header class="site-header"><div class="container nav-inner"><a class="brand" href="../../">awesome/agentic</a>
<a href="../../#directory">Browse all projects ↗</a></div></header>
<main class="container"><article class="agent-detail"><p class="section-kicker">OPEN-SOURCE CATEGORY</p>
<h1>{name}</h1><p class="detail-summary">Explore community-curated open-source projects related to {name}.
Descriptions come from the public README; inspect the original repositories for current functionality and licenses.</p>
<ul class="category-detail-list">{entries}</ul>
<p><a href="../../catalog.json">Full machine-readable directory (JSON)</a> · <a href="../../catalog.md">Markdown catalog</a></p>
</article></main></body></html>'''


def render_other_files(catalog: dict) -> None:
    # Remove obsolete project/category landing pages when README entries disappear.
    import shutil
    for directory in ("projects", "categories"):
        shutil.rmtree(SITE / directory, ignore_errors=True)
        (SITE / directory).mkdir(exist_ok=True)

    for p in catalog["projects"]:
        dst = SITE / "projects" / p["id"]
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "index.html").write_text(detail_page(p), encoding="utf-8")

    for cat in catalog["categories"]:
        dst = SITE / "categories" / slugify(cat)
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "index.html").write_text(
            category_page(cat, [p for p in catalog["projects"] if p["category"] == cat]),
            encoding="utf-8",
        )

    # Alternative formats are a convenience for agents, not search ranking signals.
    lines = [
        "# Awesome Agentic Platform Engineering",
        "",
        "Community-maintained discovery directory for open-source agentic platform engineering.",
        "These are curated descriptions, not endorsements or security/production-readiness certifications.",
        "For current features and licensing, inspect each project's official GitHub repository.",
        "",
    ]
    for cat in catalog["categories"]:
        lines.extend([f"## {cat}", ""])
        for p in (p for p in catalog["projects"] if p["category"] == cat):
            lines.append(f"- [{p['name']}]({p['pageUrl']}) — {p['description']} [Source]({p['repoUrl']})")
        lines.append("")
    (SITE / "catalog.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with (SITE / "catalog.ndjson").open("w", encoding="utf-8") as stream:
        for p in catalog["projects"]:
            stream.write(json.dumps(p, ensure_ascii=False) + "\n")

    (SITE / "llms.txt").write_text(
        "# Awesome Agentic Platform Engineering\n\n"
        "> Open-source tools and infrastructure for AI agents and cloud-native developer platforms.\n"
        "> Independent curated directory. Repository source data comes from the README.\n\n"
        "## Discover\n"
        f"- [Directory]({SITE_URL})\n"
        f"- [Complete Markdown catalog]({SITE_URL}catalog.md)\n"
        f"- [Structured JSON catalog]({SITE_URL}catalog.json)\n"
        f"- [Line-delimited JSON]({SITE_URL}catalog.ndjson)\n"
        f"- [Sitemap]({SITE_URL}sitemap.xml)\n"
        "- [Contribute](https://github.com/savisaluwadana/awesome-agentic-platform-engineering/blob/main/CONTRIBUTING.md)\n\n"
        "## Notes\n"
        "- GitHub stars are repository signals, not endorsements or votes.\n"
        "- Consult each linked GitHub repository for current details and licensing.\n"
        "- This file is optional for agents; it is not a Google Search ranking mechanism.\n",
        encoding="utf-8",
    )
    urls = [SITE_URL] + [
        SITE_URL + "categories/" + slugify(cat) + "/" for cat in catalog["categories"]
    ] + [p["pageUrl"] for p in catalog["projects"]]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap.extend(f"  <url><loc>{xml_escape(url)}</loc></url>" for url in urls)
    sitemap.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    # GitHub project Pages live in a subdirectory, so this robots file does
    # not control site-wide crawling; actual robots rules are host-root only.
    (SITE / "robots.txt").write_text(
        "# Informational only on GitHub project Pages (robots rules apply at host root).\n"
        "User-agent: *\nAllow: /\n"
        f"Sitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enrich", action="store_true", help="Fetch public GitHub repository metadata")
    parser.add_argument("--no-enrich", action="store_true", help="Never call the GitHub API")
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    enrich = not args.no_enrich and (args.enrich or bool(token))

    catalog = build(README.read_text(encoding="utf-8"), enrich=enrich, token=token)
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (SITE / ".nojekyll").touch()
    render_homepage(catalog)
    render_other_files(catalog)
    enriched = sum(p["stars"] is not None for p in catalog["projects"])
    print(f"Built {len(catalog['projects'])} projects in {len(catalog['categories'])} categories; "
          f"star counts available for {enriched} projects.")


if __name__ == "__main__":
    main()
