#!/usr/bin/env python3
"""Update cache-busting query params for README image assets."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


README_FILE = Path("README.md")
VERSION = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")

ASSETS = [
    "assets/header.svg",
    "assets/github-stats.svg",
    "assets/top-langs.svg",
    "assets/streak.svg",
    "assets/activity-graph.svg",
]


def update_asset_versions(text: str) -> str:
    updated = text
    for asset in ASSETS:
        pattern = re.compile(re.escape(asset) + r"(?:\?v=\d+)?")
        updated = pattern.sub(f"{asset}?v={VERSION}", updated)
    return updated


def main() -> None:
    readme = README_FILE.read_text(encoding="utf-8")
    updated = update_asset_versions(readme)
    README_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
