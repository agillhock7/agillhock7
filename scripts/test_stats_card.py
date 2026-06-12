#!/usr/bin/env python3
"""Regressions for the generated GitHub stats SVG."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_stats_card as stats_card  # noqa: E402


class StatsCardTest(unittest.TestCase):
    def test_card_includes_private_repos_and_omits_live_api_badge(self) -> None:
        svg = stats_card.build_stats_svg(
            [
                ("Public Repos", 8),
                ("Private Repos", 4),
                ("Original Repos", 7),
                ("Last Repo Push", "2026-06-11"),
            ],
            timestamp="2026-06-11 12:00 UTC",
        )

        self.assertIn("Private Repos:</text>", svg)
        self.assertIn(">4</text>", svg)
        self.assertNotIn("Live API", svg)


if __name__ == "__main__":
    unittest.main()
