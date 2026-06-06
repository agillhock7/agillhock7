#!/usr/bin/env python3
"""Focused regressions for public-profile security controls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_featured_content as featured  # noqa: E402


class FeaturedHomepagePolicyTest(unittest.TestCase):
    def test_rejects_featured_homepage_outside_expected_hosts(self) -> None:
        projects = [
            {
                "repo": "OnLedge",
                "summary": "Snap receipts, stay organized, and see where your money goes.",
                "homepage_hosts": ["onledge.gops.app"],
            }
        ]

        def fake_api_get(_url: str) -> dict[str, str]:
            return {
                "homepage": "https://evil.example/login",
                "html_url": "https://github.com/agillhock7/OnLedge",
            }

        with patch.object(featured, "FEATURED_PROJECTS", projects), patch.object(
            featured, "api_get", fake_api_get
        ):
            [project] = featured.build_project_data()

        self.assertEqual("", project["homepage"])
        self.assertEqual("https://github.com/agillhock7/OnLedge", project["repo_url"])

    def test_allows_featured_homepage_on_expected_host(self) -> None:
        projects = [
            {
                "repo": "OnLedge",
                "summary": "Snap receipts, stay organized, and see where your money goes.",
                "homepage_hosts": ["onledge.gops.app"],
            }
        ]

        def fake_api_get(_url: str) -> dict[str, str]:
            return {
                "homepage": "onledge.gops.app",
                "html_url": "https://github.com/agillhock7/OnLedge",
            }

        with patch.object(featured, "FEATURED_PROJECTS", projects), patch.object(
            featured, "api_get", fake_api_get
        ):
            [project] = featured.build_project_data()

        self.assertEqual("https://onledge.gops.app", project["homepage"])

    def test_public_url_override_does_not_trust_remote_homepage(self) -> None:
        projects = [
            {
                "repo": "EveryMile",
                "summary": "Track movement, true operating cost, and deduction value in one defensible stream.",
                "public_url": "https://em.gops.app",
                "homepage_hosts": ["em.gops.app"],
            }
        ]

        def fake_api_get(_url: str) -> dict[str, str]:
            return {
                "homepage": "https://evil.example/login",
                "html_url": "https://github.com/agillhock7/EveryMile",
            }

        with patch.object(featured, "FEATURED_PROJECTS", projects), patch.object(
            featured, "api_get", fake_api_get
        ):
            [project] = featured.build_project_data()

        self.assertEqual("https://em.gops.app", project["homepage"])
        self.assertEqual("https://em.gops.app", project["repo_url"])


class WorkflowSecurityPolicyTest(unittest.TestCase):
    def test_token_bearing_workflow_uses_default_branch_not_selected_ref(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/update-profile-cards.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("TARGET_BRANCH", workflow)
        self.assertNotIn("github.ref_name", workflow)
        self.assertNotIn("GITHUB_REF_NAME", workflow)


if __name__ == "__main__":
    unittest.main()
