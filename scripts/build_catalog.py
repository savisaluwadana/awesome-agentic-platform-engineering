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
    (SITE / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: " + SITE_URL + "sitemap.xml\n", encoding="utf-8"
    )
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{xml_escape(SITE_URL)}</loc></url>\n"
        "</urlset>\n", encoding="utf-8"
    )
    enriched = sum(p["stars"] is not None for p in catalog["projects"])
    print(f"Built {len(catalog['projects'])} projects in {len(catalog['categories'])} categories; "
          f"star counts available for {enriched} projects.")


if __name__ == "__main__":
    main()
