#!/usr/bin/env python3
"""Generate featured project links, live previews, and snapshot link badges."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
README_FILE = Path("README.md")
LINKS_DIR = Path("assets/links")

FEATURED_PROJECTS = [
    {
        "repo": "OnLedge",
        "summary": "Snap receipts, stay organized, and see where your money goes.",
    },
    {
        "repo": "EveryMile",
        "summary": "Track movement, true operating cost, and deduction value in one defensible stream.",
    },
    {
        "repo": "MySite",
        "summary": "A beginning look at personalized UI with AI.",
    },
    {
        "repo": "Slapshot-Snapshot",
        "summary": "Team photos and videos.",
    },
    {
        "repo": "parcel-tracker",
        "summary": "Secure shipment tracking across desktop and mobile.",
    },
    {
        "repo": "feedabum",
        "summary": "Hyperlocal micro-giving for verified neighbors; scan, verify, and donate in under a minute.",
    },
]

SNAPSHOT_LINKS = [
    ("snapshot-stats", "Stats Card", "assets/github-stats.svg"),
    ("snapshot-langs", "Top Languages", "assets/top-langs.svg"),
    ("snapshot-streak", "Streak", "assets/streak.svg"),
    ("snapshot-activity", "Activity Graph", "assets/activity-graph.svg"),
]

FEATURED_START = "<!-- FEATURED_TABLE:START -->"
FEATURED_END = "<!-- FEATURED_TABLE:END -->"
PREVIEWS_START = "<!-- LIVE_PREVIEWS:START -->"
PREVIEWS_END = "<!-- LIVE_PREVIEWS:END -->"
SNAPSHOT_START = "<!-- SNAPSHOT_LINKS:START -->"
SNAPSHOT_END = "<!-- SNAPSHOT_LINKS:END -->"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def api_get(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-featured-generator",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def build_badge_svg(label: str, gradient_id: str) -> str:
    text = label.upper()
    width = max(128, int(len(text) * 8.4) + 32)
    height = 32
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="{label}">
  <title>{label}</title>
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1f4d42" />
      <stop offset="100%" stop-color="#8ccfaf" />
    </linearGradient>
    <linearGradient id="{gradient_id}-shine" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#d9fff0" stop-opacity="0.34" />
      <stop offset="100%" stop-color="#d9fff0" stop-opacity="0" />
    </linearGradient>
  </defs>
  <g shape-rendering="geometricPrecision">
    <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="7" fill="#0f1b19" stroke="#2f5b4f" />
    <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="6" fill="url(#{gradient_id})" />
    <path d="M1 1 H{width - 1} V11 H1 Z" fill="url(#{gradient_id}-shine)" />
  </g>
  <text
    x="{width / 2}"
    y="21"
    fill="#f1fff9"
    text-anchor="middle"
    font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
    font-size="11"
    font-weight="700"
    letter-spacing="0.8"
  >
    {text}
  </text>
</svg>
"""


def write_badge(path: Path, label: str) -> None:
    gradient_id = f"grad-{slugify(path.stem)}"
    path.write_text(build_badge_svg(label, gradient_id), encoding="utf-8")


def replace_block(readme: str, start: str, end: str, content: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    replacement = f"{start}\n{content}\n{end}"
    return pattern.sub(replacement, readme)


def normalize_homepage(homepage: str) -> str:
    value = homepage.strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://{value}"


def build_project_data() -> list[dict]:
    items: list[dict] = []
    for project in FEATURED_PROJECTS:
        repo = project["repo"]
        data = api_get(f"https://api.github.com/repos/{GITHUB_USER}/{repo}")
        if not isinstance(data, dict):
            continue
        homepage = normalize_homepage(str(data.get("homepage", "")))
        repo_url = str(data.get("html_url", f"https://github.com/{GITHUB_USER}/{repo}"))
        items.append(
            {
                "repo": repo,
                "summary": project["summary"],
                "repo_url": repo_url,
                "homepage": homepage,
                "slug": slugify(repo),
            }
        )
    return items


def build_featured_table(projects: list[dict]) -> str:
    lines = [
        "| Project | Summary |",
        "| --- | --- |",
    ]
    for project in projects:
        badge_src = f"assets/links/project-{project['slug']}.svg"
        link = f'<a href="{project["repo_url"]}"><img src="{badge_src}" alt="{project["repo"]}" /></a>'
        lines.append(f"| {link} | {project['summary']} |")
    return "\n".join(lines)


def build_snapshot_links() -> str:
    chips = []
    for key, label, url in SNAPSHOT_LINKS:
        chips.append(
            f'<a href="{url}"><img src="assets/links/{key}.svg" alt="{label}" /></a>'
        )
    return '<p align="center">\n  ' + "\n  ".join(chips) + "\n</p>"


def build_live_previews(projects: list[dict]) -> str:
    live_projects = [p for p in projects if p["homepage"]]
    if not live_projects:
        return '<p align="center">Live production previews will appear here when project homepages are configured.</p>'

    cells: list[str] = []
    for project in live_projects:
        homepage = project["homepage"]
        encoded = urllib.parse.quote(homepage, safe=":/?&=%#")
        screenshot_url = (
            f"https://image.thum.io/get/width/1200/crop/720/wait/5000/noanimate/{encoded}"
        )
        live_badge = f'assets/links/live-{project["slug"]}.svg'
        cell = (
            '    <td align="center" width="33%">\n'
            f'      <a href="{homepage}"><img src="{screenshot_url}" alt="{project["repo"]} live preview" width="100%" /></a><br/>\n'
            f'      <a href="{homepage}"><img src="{live_badge}" alt="Visit {project["repo"]}" /></a>\n'
            "    </td>"
        )
        cells.append(cell)

    rows: list[str] = ["<table>", "  <tbody>"]
    for i in range(0, len(cells), 3):
        rows.append("  <tr>")
        for cell in cells[i : i + 3]:
            rows.append(cell)
        rows.append("  </tr>")
    rows.extend(["  </tbody>", "</table>"])
    return "\n".join(rows)


def main() -> None:
    LINKS_DIR.mkdir(parents=True, exist_ok=True)
    projects = build_project_data()

    for project in projects:
        write_badge(LINKS_DIR / f'project-{project["slug"]}.svg', project["repo"])
        write_badge(LINKS_DIR / f'live-{project["slug"]}.svg', f'Visit {project["repo"]}')

    for key, label, _ in SNAPSHOT_LINKS:
        write_badge(LINKS_DIR / f"{key}.svg", label)

    readme = README_FILE.read_text(encoding="utf-8")
    updated = readme
    updated = replace_block(updated, FEATURED_START, FEATURED_END, build_featured_table(projects))
    updated = replace_block(updated, PREVIEWS_START, PREVIEWS_END, build_live_previews(projects))
    updated = replace_block(updated, SNAPSHOT_START, SNAPSHOT_END, build_snapshot_links())

    README_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
