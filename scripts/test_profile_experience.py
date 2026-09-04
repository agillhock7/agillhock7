#!/usr/bin/env python3
"""End-to-end regressions for the Forward Lab profile experience."""

from __future__ import annotations

import copy
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_ecosystem as ecosystem  # noqa: E402
from scripts import generate_header as header  # noqa: E402
from scripts import generate_telemetry as telemetry  # noqa: E402
from scripts import update_readme_cache_bust as cache_bust  # noqa: E402
from scripts.generate_streak_card import Streak  # noqa: E402
from scripts.profile_config import load_profile, validate_profile  # noqa: E402


class ManifestTest(unittest.TestCase):
    def test_manifest_defines_complete_product_story(self) -> None:
        profile = load_profile(REPO_ROOT / "profile.yml")

        self.assertEqual(6, len(profile["projects"]))
        self.assertEqual(3, sum(p["tier"] == "flagship" for p in profile["projects"]))
        self.assertEqual(3, sum(p["tier"] == "lab" for p in profile["projects"]))
        self.assertEqual(3, len(profile["principles"]))

    def test_manifest_rejects_unapproved_project_destination(self) -> None:
        profile = copy.deepcopy(load_profile(REPO_ROOT / "profile.yml"))
        profile["projects"][0]["public_url"] = "https://evil.example/login"

        with self.assertRaisesRegex(ValueError, "host must be listed"):
            validate_profile(profile)


class VisualAssetTest(unittest.TestCase):
    def test_signature_svgs_are_valid_accessible_and_motion_safe(self) -> None:
        profile = load_profile(REPO_ROOT / "profile.yml")
        svgs = [
            header.build_svg(profile["brand"]),
            header.build_footer(profile["brand"]),
            ecosystem.build_svg(profile["projects"]),
        ]

        for svg in svgs:
            root = ET.fromstring(svg)
            self.assertEqual("{http://www.w3.org/2000/svg}svg", root.tag)
            self.assertEqual("img", root.attrib["role"])
            self.assertIn("prefers-reduced-motion", svg)
            self.assertNotIn('href="http', svg)

    def test_telemetry_console_integrates_all_signals(self) -> None:
        start = date(2026, 8, 4)
        data = telemetry.Telemetry(
            public_repos=7,
            private_repos=38,
            live_systems=6,
            stars=3,
            followers=4,
            total_contributions=1200,
            current_streak=Streak(4, date(2026, 8, 31), date(2026, 9, 3)),
            longest_streak=Streak(12, date(2026, 7, 1), date(2026, 7, 12)),
            last_push="2026-09-03",
            contributions={start + timedelta(days=i): i % 8 for i in range(31)},
            top_languages=[("Python", 800, 80.0), ("TypeScript", 200, 20.0)],
            generated_at=datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
        )

        svg = telemetry.render_svg(data)
        root = ET.fromstring(svg)

        self.assertEqual("{http://www.w3.org/2000/svg}svg", root.tag)
        for label in (
            "LIVE TELEMETRY",
            "PUBLIC REPOS",
            "LIVE SYSTEMS",
            "31-DAY CONTRIBUTION SIGNAL",
            "STREAK ENGINE",
            "LANGUAGE SIGNAL",
        ):
            self.assertIn(label, svg)
        self.assertIn("prefers-reduced-motion", svg)


class ProfileReadmeTest(unittest.TestCase):
    def test_readme_uses_local_signature_assets_and_clear_hierarchy(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for heading in (
            "## Flagship systems",
            "## The product constellation",
            "## From the lab",
            "## Live telemetry",
            "## How I build",
        ):
            self.assertIn(heading, readme)
        for asset in ("assets/header.svg", "assets/ecosystem.svg", "assets/telemetry.svg", "assets/footer.svg"):
            self.assertIn(asset, readme)
        self.assertNotIn("readme-typing-svg", readme)
        self.assertNotIn("capsule-render", readme)
        self.assertNotIn("github-readme-activity-graph", readme)

    def test_every_local_readme_asset_exists(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        paths = {
            match.group("path")
            for match in cache_bust.ASSET_PATTERN.finditer(readme)
        }
        missing = [path for path in sorted(paths) if not (REPO_ROOT / path).is_file()]
        self.assertEqual([], missing)


class CacheVersionTest(unittest.TestCase):
    def test_versions_change_only_when_asset_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets"
            assets.mkdir()
            asset = assets / "demo.svg"
            asset.write_text("first", encoding="utf-8")
            source = '<img src="assets/demo.svg?v=old" />'

            first = cache_bust.update_asset_versions(source, root=root)
            second = cache_bust.update_asset_versions(first, root=root)
            asset.write_text("second", encoding="utf-8")
            changed = cache_bust.update_asset_versions(second, root=root)

            self.assertEqual(first, second)
            self.assertNotEqual(second, changed)


class WorkflowTest(unittest.TestCase):
    def test_workflows_are_quiet_serialized_and_self_contained(self) -> None:
        update = (REPO_ROOT / ".github/workflows/update-profile-cards.yml").read_text(
            encoding="utf-8"
        )
        previews = (REPO_ROOT / ".github/workflows/refresh-project-previews.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn('cron: "17 7 * * *"', update)
        self.assertNotIn('cron: "17 * * * *"', update)
        self.assertIn("group: profile-readme-writes", update)
        self.assertIn("group: profile-readme-writes", previews)
        self.assertIn("python3 scripts/generate_telemetry.py", update)
        self.assertIn("python3 scripts/capture_project_previews.py", previews)
        self.assertIn("python3 -m playwright install", previews)
        self.assertNotIn("thum.io", update + previews)
        self.assertNotIn("s.wordpress.com/mshots", update + previews)


if __name__ == "__main__":
    unittest.main()
