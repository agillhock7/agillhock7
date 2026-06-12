#!/usr/bin/env python3
"""Generate a custom GitHub stats SVG from live GitHub API data."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
PRIVATE_REPO_COUNT = os.getenv("PRIVATE_REPO_COUNT", "").strip()
OUTFILE = Path("assets/github-stats.svg")
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
API_RETRIES = int(os.getenv("GITHUB_API_RETRIES", "4"))


def api_get(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-stats-generator",
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
                f"[stats] GitHub API HTTP {err.code}; retrying in {sleep_for}s: {url}",
                file=sys.stderr,
            )
            time.sleep(sleep_for)
        except (TimeoutError, urllib.error.URLError) as err:
            if attempt >= API_RETRIES:
                raise
            sleep_for = retry_delay(err, attempt)
            print(
                f"[stats] GitHub API request failed; retrying in {sleep_for}s: {err}",
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
        url = f"https://api.github.com/users/{user}/repos?per_page=100&page={page}"
        batch = api_get(url)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_private_repo_count(user: str) -> int | str:
    if PRIVATE_REPO_COUNT:
        try:
            return int(PRIVATE_REPO_COUNT)
        except ValueError:
            return PRIVATE_REPO_COUNT

    if not GITHUB_TOKEN:
        return previous_metric("Private Repos") or "--"

    try:
        count = 0
        page = 1
        while True:
            url = (
                "https://api.github.com/user/repos"
                f"?visibility=private&affiliation=owner&per_page=100&page={page}"
            )
            batch = api_get(url)
            if not isinstance(batch, list) or not batch:
                break

            for repo in batch:
                owner = repo.get("owner", {})
                owner_login = str(owner.get("login", "")).lower() if isinstance(owner, dict) else ""
                if repo.get("private") and owner_login == user.lower():
                    count += 1
            page += 1
        return count
    except Exception as err:
        fallback = previous_metric("Private Repos")
        if fallback is not None:
            print(
                f"[stats] Unable to refresh Private Repos; keeping previous value {fallback}: {err}",
                file=sys.stderr,
            )
            return fallback

        print(
            f"[stats] Unable to refresh Private Repos; no previous value available, using --: {err}",
            file=sys.stderr,
        )
        return "--"


def format_iso_day(value: str | None) -> str:
    if not value:
        return "--"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return "--"


def previous_metric(label: str) -> str | None:
    if not OUTFILE.exists():
        return None

    text = OUTFILE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(label) + r":</text>\s*<text[^>]*>\s*([^<]+?)\s*</text>")
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1)


def search_total(user: str, item_type: str, label: str) -> int | str:
    query = urllib.parse.quote(f"author:{user} type:{item_type}")
    try:
        info = api_get(f"https://api.github.com/search/issues?q={query}")
        if not isinstance(info, dict):
            raise RuntimeError(f"Unexpected search response for {item_type}: {type(info).__name__}")
        return int(info.get("total_count", 0))
    except Exception as err:
        fallback = previous_metric(label)
        if fallback is not None:
            print(
                f"[stats] Unable to refresh {label}; keeping previous value {fallback}: {err}",
                file=sys.stderr,
            )
            return fallback

        print(
            f"[stats] Unable to refresh {label}; no previous value available, using 0: {err}",
            file=sys.stderr,
        )
        return 0


def build_stats_svg(lines: list[tuple[str, int | str]], *, timestamp: str) -> str:
    svg_lines = []
    y_start = 58
    y_step = 15
    for idx, (label, value) in enumerate(lines):
        y = y_start + idx * y_step
        svg_lines.append(
            f'<text x="26" y="{y}" fill="#93a9bd" font-size="12" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{label}:</text>'
        )
        svg_lines.append(
            f'<text x="200" y="{y}" fill="#dbeafe" font-size="12" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-weight="700">{value}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="430" height="240" role="img" aria-label="GitHub Stats">
  <title>GitHub Stats</title>
  <defs>
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="428" height="238" rx="10" fill="#0d1117" stroke="#2b3545" />
  <text x="22" y="34" fill="url(#titleGrad)" font-size="24" font-weight="700"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Stats</text>
  {''.join(svg_lines)}
  <text x="22" y="222" fill="#6f86a0" font-size="11"
        font-family="Verdana,Geneva,DejaVu Sans,sans-serif">Updated: {timestamp}</text>
</svg>
"""


def main() -> None:
    user = GITHUB_USER
    repos = fetch_repos(user)
    user_info = api_get(f"https://api.github.com/users/{user}")
    events = api_get(f"https://api.github.com/users/{user}/events/public?per_page=1")

    public_repos = int(user_info.get("public_repos", 0))
    private_repos = fetch_private_repo_count(user)
    public_nonfork_repos = sum(1 for r in repos if not r.get("fork"))
    total_stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
    total_forks = sum(int(r.get("forks_count", 0)) for r in repos)
    followers = int(user_info.get("followers", 0))
    total_prs = search_total(user, "pr", "Total PRs")
    total_issues = search_total(user, "issue", "Total Issues")
    latest_push = format_iso_day(
        max((r.get("pushed_at") for r in repos if r.get("pushed_at")), default=None)
    )
    latest_activity = "--"
    if isinstance(events, list) and events:
        latest_activity = format_iso_day(events[0].get("created_at"))

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        ("Public Repos", public_repos),
        ("Private Repos", private_repos),
        ("Original Repos", public_nonfork_repos),
        ("Total Stars", total_stars),
        ("Total Forks", total_forks),
        ("Followers", followers),
        ("Total PRs", total_prs),
        ("Total Issues", total_issues),
        ("Last Activity", latest_activity),
        ("Last Repo Push", latest_push),
    ]

    svg = build_stats_svg(lines, timestamp=timestamp)

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
