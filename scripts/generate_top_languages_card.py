#!/usr/bin/env python3
"""Generate an account-level top-languages SVG from GitHub API language bytes."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Iterable
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OUTFILE = Path("assets/top-langs.svg")
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
API_RETRIES = int(os.getenv("GITHUB_API_RETRIES", "4"))
LANGUAGE_LIMIT = int(os.getenv("TOP_LANGUAGE_LIMIT", "7"))
EXCLUDED_LANGUAGE_BUCKETS = {
    language.strip()
    for language in os.getenv("TOP_LANGUAGE_EXCLUDE", "Vue").split(",")
    if language.strip()
}

LANGUAGE_COLORS = {
    "Astro": "#ff5d01",
    "Blade": "#f7523f",
    "CSS": "#563d7c",
    "Dockerfile": "#384d54",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "Lua": "#000080",
    "PHP": "#4f5d95",
    "PLpgSQL": "#336790",
    "Python": "#3572a5",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
    "TypeScript": "#3178c6",
}

FALLBACK_COLORS = [
    "#8ccfaf",
    "#38bdf8",
    "#a78bfa",
    "#f59e0b",
    "#f472b6",
    "#22c55e",
    "#fb7185",
]


def api_get(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-top-languages-generator",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(API_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code not in TRANSIENT_STATUS_CODES or attempt >= API_RETRIES:
                raise
            sleep_for = retry_delay(err, attempt)
            print(
                f"[top-langs] GitHub API HTTP {err.code}; retrying in {sleep_for}s: {url}",
                file=sys.stderr,
            )
            time.sleep(sleep_for)
        except (TimeoutError, urllib.error.URLError) as err:
            if attempt >= API_RETRIES:
                raise
            sleep_for = retry_delay(err, attempt)
            print(
                f"[top-langs] GitHub API request failed; retrying in {sleep_for}s: {err}",
                file=sys.stderr,
            )
            time.sleep(sleep_for)

    raise RuntimeError(f"Unable to fetch GitHub API URL after retries: {url}")


def retry_delay(err: BaseException, attempt: int) -> int:
    retry_after = None
    if isinstance(err, urllib.error.HTTPError):
        retry_after = err.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return min(int(retry_after), 60)
    return min(2**attempt, 30)


def fetch_repos(user: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}"
        batch = api_get(url)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def original_public_repos(repos: Iterable[dict]) -> list[dict]:
    return [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("disabled")
        and repo.get("languages_url")
    ]


def fetch_repo_language_totals(repos: Iterable[dict]) -> list[dict[str, int]]:
    language_sets: list[dict[str, int]] = []
    for repo in repos:
        try:
            data = api_get(str(repo["languages_url"]))
        except urllib.error.HTTPError as err:
            print(
                f"[top-langs] Skipping {repo.get('full_name', repo.get('name', 'repo'))}: HTTP {err.code}",
                file=sys.stderr,
            )
            continue

        if isinstance(data, dict):
            language_sets.append(
                {
                    str(language): int(byte_count)
                    for language, byte_count in data.items()
                    if isinstance(byte_count, int) and byte_count > 0
                }
            )
    return language_sets


def summarize_language_totals(
    language_sets: Iterable[dict[str, int]],
    *,
    limit: int = LANGUAGE_LIMIT,
    excluded: set[str] | None = None,
) -> list[tuple[str, int, float]]:
    excluded = EXCLUDED_LANGUAGE_BUCKETS if excluded is None else excluded
    totals: Counter[str] = Counter()
    for language_set in language_sets:
        for language, byte_count in language_set.items():
            if language in excluded or byte_count <= 0:
                continue
            totals[language] += byte_count

    total_bytes = sum(totals.values())
    if total_bytes <= 0:
        return []

    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [
        (language, byte_count, round((byte_count / total_bytes) * 100, 1))
        for language, byte_count in ranked
    ]


def language_color(language: str) -> str:
    if language in LANGUAGE_COLORS:
        return LANGUAGE_COLORS[language]
    digest = hashlib.sha256(language.encode("utf-8")).digest()
    return FALLBACK_COLORS[digest[0] % len(FALLBACK_COLORS)]


def format_bytes(byte_count: int) -> str:
    if byte_count >= 1_000_000:
        return f"{byte_count / 1_000_000:.1f} MB"
    if byte_count >= 1_000:
        return f"{byte_count / 1_000:.1f} KB"
    return f"{byte_count} B"


def build_svg(
    summary: list[tuple[str, int, float]],
    *,
    repo_count: int,
    timestamp: str,
) -> str:
    width = 430
    height = 240
    bar_x = 152
    bar_width = 230
    bar_height = 9
    y_start = 72
    y_step = 20
    largest = max((byte_count for _, byte_count, _ in summary), default=1)

    rows = []
    for index, (language, byte_count, percent) in enumerate(summary):
        y = y_start + index * y_step
        color = language_color(language)
        current_bar_width = max(3, round((byte_count / largest) * bar_width))
        rows.append(
            f'<rect x="26" y="{y - 9}" width="10" height="10" rx="2" fill="{color}" />'
            f'<text x="44" y="{y}" fill="#dbeafe" font-size="12" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{escape(language)}</text>'
            f'<rect x="{bar_x}" y="{y - 9}" width="{bar_width}" height="{bar_height}" rx="4.5" fill="#1c2633" />'
            f'<rect x="{bar_x}" y="{y - 9}" width="{current_bar_width}" height="{bar_height}" rx="4.5" fill="{color}" />'
            f'<text x="405" y="{y}" text-anchor="end" fill="#93a9bd" font-size="11" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{percent:.1f}%</text>'
            f'<text x="44" y="{y + 12}" fill="#6f86a0" font-size="9" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{format_bytes(byte_count)}</text>'
        )

    if not rows:
        rows.append(
            '<text x="26" y="116" fill="#93a9bd" font-size="13" '
            'font-family="Verdana,Geneva,DejaVu Sans,sans-serif">No public language data found.</text>'
        )

    footer = f"{repo_count} public original repos"
    if EXCLUDED_LANGUAGE_BUCKETS:
        footer += f" | excluded: {', '.join(sorted(EXCLUDED_LANGUAGE_BUCKETS))}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="Top Languages by Code">
  <title>Top Languages by Code</title>
  <defs>
    <linearGradient id="languageTitleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#8ccfaf" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="#0d1117" stroke="#2b3545" />
  <text x="22" y="34" fill="url(#languageTitleGrad)" font-size="22" font-weight="700"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Top Languages by Code</text>
  <text x="22" y="52" fill="#6f86a0" font-size="11"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">GitHub Linguist bytes across public original repos</text>
  {''.join(rows)}
  <text x="22" y="222" fill="#6f86a0" font-size="10"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{escape(footer)}</text>
  <text x="408" y="222" text-anchor="end" fill="#6f86a0" font-size="10"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Updated: {escape(timestamp)}</text>
</svg>
"""


def main() -> None:
    repos = original_public_repos(fetch_repos(GITHUB_USER))
    language_sets = fetch_repo_language_totals(repos)
    summary = summarize_language_totals(language_sets)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(
        build_svg(summary, repo_count=len(repos), timestamp=timestamp),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
