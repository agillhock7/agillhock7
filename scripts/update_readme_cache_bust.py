#!/usr/bin/env python3
"""Use stable content hashes as cache-busting versions for README assets."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


README_FILE = Path("README.md")
ASSET_PATTERN = re.compile(
    r"(?P<path>assets/[a-zA-Z0-9._/-]+\.(?:svg|png|jpg))(?:\?v=[a-zA-Z0-9]+)?"
)


def asset_version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def update_asset_versions(text: str, *, root: Path = Path(".")) -> str:
    versions: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        relative = match.group("path")
        path = root / relative
        if not path.is_file():
            return match.group(0)
        if relative not in versions:
            versions[relative] = asset_version(path)
        return f"{relative}?v={versions[relative]}"

    return ASSET_PATTERN.sub(replace, text)


def main() -> None:
    readme = README_FILE.read_text(encoding="utf-8")
    updated = update_asset_versions(readme)
    README_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
