"""Checks for README-driven catalog parsing; run with unittest discover -s tests."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
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


if __name__ == "__main__":
    unittest.main()
