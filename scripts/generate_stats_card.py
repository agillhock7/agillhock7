#!/usr/bin/env python3
"""Generate a custom GitHub stats SVG from live GitHub API data."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OUTFILE = Path("assets/github-stats.svg")


def api_get(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-stats-generator",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_repos(user: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{user}/repos?per_page=100&page={page}"
        batch = api_get(url)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def format_iso_day(value: str | None) -> str:
    if not value:
        return "--"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return "--"


def main() -> None:
    user = GITHUB_USER
    repos = fetch_repos(user)
    user_info = api_get(f"https://api.github.com/users/{user}")
    events = api_get(f"https://api.github.com/users/{user}/events/public?per_page=1")

    prs_query = urllib.parse.quote(f"author:{user} type:pr")
    issues_query = urllib.parse.quote(f"author:{user} type:issue")
    prs_info = api_get(f"https://api.github.com/search/issues?q={prs_query}")
    issues_info = api_get(f"https://api.github.com/search/issues?q={issues_query}")

    public_nonfork_repos = sum(1 for r in repos if not r.get("fork"))
    total_stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
    total_forks = sum(int(r.get("forks_count", 0)) for r in repos)
    followers = int(user_info.get("followers", 0))
    total_prs = int(prs_info.get("total_count", 0))
    total_issues = int(issues_info.get("total_count", 0))
    latest_push = format_iso_day(
        max((r.get("pushed_at") for r in repos if r.get("pushed_at")), default=None)
    )
    latest_activity = "--"
    if isinstance(events, list) and events:
        latest_activity = format_iso_day(events[0].get("created_at"))

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        ("Public Repos", public_nonfork_repos),
        ("Total Stars", total_stars),
        ("Total Forks", total_forks),
        ("Followers", followers),
        ("Total PRs", total_prs),
        ("Total Issues", total_issues),
        ("Last Activity", latest_activity),
        ("Last Repo Push", latest_push),
    ]

    svg_lines = []
    y_start = 62
    y_step = 20
    for idx, (label, value) in enumerate(lines):
        y = y_start + idx * y_step
        svg_lines.append(
            f'<text x="26" y="{y}" fill="#93a9bd" font-size="13" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{label}:</text>'
        )
        svg_lines.append(
            f'<text x="200" y="{y}" fill="#dbeafe" font-size="13" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-weight="700">{value}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="430" height="240" role="img" aria-label="GitHub Stats">
  <title>GitHub Stats</title>
  <defs>
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="428" height="238" rx="10" fill="#0d1117" stroke="#2b3545" />
  <text x="22" y="36" fill="url(#titleGrad)" font-size="24" font-weight="700"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Stats</text>
  {''.join(svg_lines)}
  <text x="22" y="222" fill="#6f86a0" font-size="11"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Updated: {timestamp}</text>
  <text x="408" y="222" text-anchor="end" fill="#6f86a0" font-size="11"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Live API</text>
</svg>
"""

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
