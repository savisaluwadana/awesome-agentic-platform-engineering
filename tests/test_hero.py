"""Protect the editorial hero and its existing catalog integration."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.classes = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if props.get("id"):
            self.ids.add(props["id"])
        if props.get("class"):
            self.classes.extend(props["class"].split())
        if tag == "a":
            self.links.append(props.get("href", ""))


class EditorialHeroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PageParser()
        cls.page.feed(HTML)

    def test_core_discovery_hooks_remain(self):
        for element_id in ("hero-heading", "heroProjectCount",
                           "heroCategoryCount", "directory", "agent-access",
                           "productList"):
            self.assertIn(element_id, self.page.ids)
        for marker in ("<!-- CATALOG:START -->", "<!-- CATALOG:END -->",
                       "<!-- SCHEMA:START -->", "<!-- SCHEMA:END -->"):
            self.assertIn(marker, HTML)

    def test_hero_links_use_live_catalog_routes(self):
        for href in ("#directory", "#agent-access", "./catalog.json",
                     "./catalog.md", "./sitemap.xml"):
            self.assertIn(href, self.page.links)

    def test_old_promotional_hero_is_gone(self):
        for name in ("hero-visual", "hero-orb", "visual-window", "floating-note",
                     "spotlight-card"):
            self.assertNotIn(name, self.page.classes)
            self.assertNotIn(f".{name}", CSS)
        self.assertNotIn("CURATOR SPOTLIGHT", HTML)

    def test_editorial_layout_has_responsive_rules(self):
        for selector in (".hero{", ".hero-panel{", ".hero-topic{",
                         ".hero-accent{", "@media(max-width:850px)",
                         "@media(max-width:490px)"):
            self.assertIn(selector, CSS)
        self.assertIn("Open-source tools for", HTML)


if __name__ == "__main__":
    unittest.main()
