#!/usr/bin/env python3
"""Regressions for the generated top-languages SVG."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_top_languages_card as top_languages  # noqa: E402


class TopLanguagesCardTest(unittest.TestCase):
    def test_summarizes_language_bytes_and_omits_framework_bucket(self) -> None:
        summary = top_languages.summarize_language_totals(
            [
                {"PHP": 600, "Vue": 400},
                {"TypeScript": 300, "JavaScript": 100},
            ]
        )

        self.assertEqual(
            [
                ("PHP", 600, 60.0),
                ("TypeScript", 300, 30.0),
                ("JavaScript", 100, 10.0),
            ],
            summary,
        )

    def test_card_uses_uncluttered_code_language_layout(self) -> None:
        svg = top_languages.build_svg(
            [
                ("PHP", 600, 60.0),
                ("TypeScript", 300, 30.0),
                ("JavaScript", 100, 10.0),
            ],
            repo_count=2,
            timestamp="2026-06-11 12:00 UTC",
        )

        self.assertIn("Top Languages by Code", svg)
        self.assertNotIn("Top Languages by Repo", svg)
        self.assertNotIn("GitHub Linguist bytes", svg)
        self.assertNotIn("excluded:", svg)
        self.assertNotIn("public original repos", svg)
        self.assertNotIn("600 B", svg)
        self.assertNotIn("300 B", svg)


if __name__ == "__main__":
    unittest.main()
