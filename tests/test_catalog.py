"""Checks for README-driven catalog parsing; run with unittest discover -s tests."""
import sys
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_catalog
from build_catalog import parse_readme, build


SAMPLE = """# Collection

## Directory

### Agent Frameworks & Orchestration
- [Example](https://github.com/org/example) — A workflow engine.

### Security & Policy
- [Policy](https://github.com/org/policy) - Enforces policies.

## Contributing
- [Unrelated](https://github.com/org/ignored) — Not a catalog entry.
"""


class CatalogTests(unittest.TestCase):
    def test_parses_only_directory(self):
        items = parse_readme(SAMPLE)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["repo"], "org/example")
        self.assertEqual(items[1]["category"], "Security & Policy")

    def test_rejects_bad_entry(self):
        invalid = SAMPLE.replace("- [Policy](https://github.com/org/policy) - Enforces policies.",
                                 "- Policy - https://github.com/org/policy")
        with self.assertRaises(ValueError):
            parse_readme(invalid)

    def test_rejects_duplicates(self):
        invalid = SAMPLE.replace("## Contributing",
                                 "- [Copy](https://github.com/org/example) — Duplicate.\n\n## Contributing")
        with self.assertRaises(ValueError):
            parse_readme(invalid)

    def test_catalog_has_no_fake_stars(self):
        catalog = build(SAMPLE)
        self.assertEqual(catalog["total"], 2)
        self.assertIsNone(catalog["projects"][0]["stars"])
        self.assertEqual(len(catalog["categories"]), 2)


    def test_render_static_pages_and_agent_feeds(self):
        catalog = build(SAMPLE)
        # A temporary Pages output dir keeps the working tree untouched.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = (
                "<html><head><!-- SCHEMA:START --><!-- SCHEMA:END --></head>"
                "<body><div><!-- NAV:START --><!-- NAV:END --></div>"
                "<main><!-- CATALOG:START --><!-- CATALOG:END --></main></body></html>"
            )
            (root / "index.html").write_text(html, encoding="utf-8")
            with patch.object(build_catalog, "SITE", root):
                build_catalog.render_homepage(catalog)
                build_catalog.render_other_files(catalog)
                rendered = (root / "index.html").read_text(encoding="utf-8")
                self.assertIn("A workflow engine.", rendered)
                self.assertIn('application/ld+json', rendered)
                self.assertIn("categories/security-policy/", rendered)
                self.assertTrue((root / "projects" / "org-example" / "index.html").exists())
                self.assertTrue((root / "categories" / "security-policy" / "index.html").exists())
                self.assertEqual(len((root / "catalog.ndjson").read_text().splitlines()), 2)
                self.assertEqual(len(json.loads((root / "catalog.ndjson").read_text().splitlines()[0])["repo"]), 11)
                self.assertIn("org/example", (root / "catalog.md").read_text())
                self.assertIn("org-example/", (root / "sitemap.xml").read_text())
                self.assertIn("not a Google Search ranking", (root / "llms.txt").read_text())
                # Re-runs are deterministic and do not duplicate project markup.
                build_catalog.render_homepage(catalog)
                self.assertEqual(rendered, (root / "index.html").read_text())

    def test_markup_escapes_user_submitted_descriptions(self):
        markdown = (
            "## Directory\n\n### Tools\n"
            "- [Example](https://github.com/org/example) — <script>alert('x')</script>\n"
        )
        catalog = build(markdown)
        output = build_catalog.detail_page(catalog["projects"][0])
        self.assertNotIn("<script>alert", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertIn("SoftwareSourceCode", output)


if __name__ == "__main__":
    unittest.main()
