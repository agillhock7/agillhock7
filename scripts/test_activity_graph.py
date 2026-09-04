#!/usr/bin/env python3
"""Regressions for the locally generated activity graph SVG."""

from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_activity_graph as activity  # noqa: E402


class ActivityGraphTest(unittest.TestCase):
    def test_renders_valid_accessible_svg_with_contribution_data(self) -> None:
        contributions = {
            date(2026, 8, 30): 0,
            date(2026, 8, 31): 1,
            date(2026, 9, 1): 7,
        }

        svg = activity.render_svg(
            contributions,
            generated_at=datetime(2026, 9, 3, 12, 30, tzinfo=timezone.utc),
        )
        root = ET.fromstring(svg)

        self.assertEqual("{http://www.w3.org/2000/svg}svg", root.tag)
        self.assertEqual("activity-title activity-description", root.attrib["aria-labelledby"])
        self.assertIn("2026-09-01: 7 contributions", svg)
        self.assertIn("Updated 2026-09-03 12:30 UTC", svg)
        self.assertIn('stroke="#22c55e"', svg)

    def test_rounds_axis_to_four_integer_intervals(self) -> None:
        self.assertEqual(4, activity.rounded_axis_max(0))
        self.assertEqual(8, activity.rounded_axis_max(7))
        self.assertEqual(16, activity.rounded_axis_max(16))

    def test_workflow_has_no_dependency_on_disabled_graph_service(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/update-profile-cards.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("python3 scripts/generate_telemetry.py", workflow)
        self.assertNotIn("github-readme-activity-graph.vercel.app", workflow)


if __name__ == "__main__":
    unittest.main()
