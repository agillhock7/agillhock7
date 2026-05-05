#!/usr/bin/env python3
"""Generate a GitHub streak SVG from GitHub contribution calendar data."""

from __future__ import annotations

import html
import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
OUTFILE = Path("assets/streak.svg")
GRAPHQL_URL = "https://api.github.com/graphql"
MAX_CONTRIBUTION_DAYS = 365

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@dataclass(frozen=True)
class Streak:
    length: int
    start: date | None = None
    end: date | None = None


@dataclass(frozen=True)
class StreakStats:
    total_contributions: int
    account_created_at: date
    current: Streak
    longest: Streak


def request_json(url: str, body: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-streak-generator",
    }
    data: bytes | None = None
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN or GH_TOKEN is required to query GitHub GraphQL contributions.")

    payload = request_json(GRAPHQL_URL, {"query": query, "variables": variables})
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected GitHub GraphQL response.")
    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL errors: {payload['errors']}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("GitHub GraphQL response did not include data.")
    return data


def fetch_account_created_at(user: str) -> date:
    payload = request_json(f"https://api.github.com/users/{user}")
    if not isinstance(payload, dict) or not payload.get("created_at"):
        raise RuntimeError(f"Unable to fetch account creation date for {user}.")
    return datetime.fromisoformat(str(payload["created_at"]).replace("Z", "+00:00")).date()


def to_github_datetime(day: date, end_of_day: bool) -> str:
    boundary = time(23, 59, 59) if end_of_day else time.min
    return datetime.combine(day, boundary, timezone.utc).isoformat().replace("+00:00", "Z")


def iter_dates(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def fetch_contribution_days(user: str, start: date, end: date) -> dict[date, int]:
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    contributions = {day: 0 for day in iter_dates(start, end)}
    chunk_start = start

    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=MAX_CONTRIBUTION_DAYS - 1), end)
        data = graphql(
            query,
            {
                "login": user,
                "from": to_github_datetime(chunk_start, end_of_day=False),
                "to": to_github_datetime(chunk_end, end_of_day=True),
            },
        )

        user_data = data.get("user")
        if not isinstance(user_data, dict):
            raise RuntimeError(f"GitHub user not found: {user}")
        calendar = (
            user_data.get("contributionsCollection", {})
            .get("contributionCalendar", {})
            .get("weeks", [])
        )
        for week in calendar:
            for item in week.get("contributionDays", []):
                day = date.fromisoformat(str(item["date"]))
                if chunk_start <= day <= chunk_end:
                    contributions[day] = int(item.get("contributionCount", 0))

        chunk_start = chunk_end + timedelta(days=1)

    return contributions


def choose_longer(candidate: Streak, current: Streak) -> Streak:
    if candidate.length > current.length:
        return candidate
    if (
        candidate.length == current.length
        and candidate.end is not None
        and (current.end is None or candidate.end > current.end)
    ):
        return candidate
    return current


def calculate_streaks(contributions: dict[date, int], today: date | None = None) -> tuple[int, Streak, Streak]:
    if not contributions:
        return 0, Streak(0), Streak(0)

    days = sorted(contributions)
    today = today or days[-1]
    total = sum(contributions.values())

    longest = Streak(0)
    run_start: date | None = None
    run_length = 0

    for day in days:
        if contributions[day] > 0:
            if run_start is None:
                run_start = day
            run_length += 1
            continue

        if run_start is not None:
            longest = choose_longer(Streak(run_length, run_start, day - timedelta(days=1)), longest)
        run_start = None
        run_length = 0

    if run_start is not None:
        longest = choose_longer(Streak(run_length, run_start, days[-1]), longest)

    current_end: date | None = None
    if contributions.get(today, 0) > 0:
        current_end = today
    elif contributions.get(today - timedelta(days=1), 0) > 0:
        current_end = today - timedelta(days=1)

    if current_end is None:
        return total, Streak(0), longest

    current_start = current_end
    while contributions.get(current_start - timedelta(days=1), 0) > 0:
        current_start -= timedelta(days=1)

    current = Streak((current_end - current_start).days + 1, current_start, current_end)
    return total, current, longest


def format_day(day: date, include_year: bool = False) -> str:
    value = f"{MONTHS[day.month - 1]} {day.day}"
    if include_year:
        value += f", {day.year}"
    return value


def format_streak_range(streak: Streak) -> str:
    if streak.start is None or streak.end is None:
        return "--"
    if streak.start == streak.end:
        return format_day(streak.start)
    include_year = streak.start.year != streak.end.year
    return f"{format_day(streak.start, include_year)} - {format_day(streak.end, include_year)}"


def format_account_range(created_at: date) -> str:
    return f"{format_day(created_at, include_year=True)} - Present"


def render_svg(stats: StreakStats) -> str:
    total = html.escape(f"{stats.total_contributions:,}")
    account_range = html.escape(format_account_range(stats.account_created_at))
    current_count = html.escape(str(stats.current.length))
    current_range = html.escape(format_streak_range(stats.current))
    longest_count = html.escape(str(stats.longest.length))
    longest_range = html.escape(format_streak_range(stats.longest))

    return f"""<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'
                style='isolation: isolate' viewBox='0 0 495 195' width='495px' height='195px' direction='ltr' role='img' aria-label='GitHub streak stats'>
        <title>GitHub streak stats</title>
        <style>
            @keyframes currstreak {{
                0% {{ font-size: 3px; opacity: 0.2; }}
                80% {{ font-size: 34px; opacity: 1; }}
                100% {{ font-size: 28px; opacity: 1; }}
            }}
            @keyframes fadein {{
                0% {{ opacity: 0; }}
                100% {{ opacity: 1; }}
            }}
        </style>
        <defs>
            <clipPath id='outer_rectangle'>
                <rect width='495' height='195' rx='4.5'/>
            </clipPath>
            <mask id='mask_out_ring_behind_fire'>
                <rect width='495' height='195' fill='white'/>
                <ellipse id='mask-ellipse' cx='247.5' cy='32' rx='13' ry='18' fill='black'/>
            </mask>
        </defs>
        <g clip-path='url(#outer_rectangle)'>
            <g style='isolation: isolate'>
                <rect stroke='#000000' stroke-opacity='0' fill='#1A1B27' rx='4.5' x='0.5' y='0.5' width='494' height='194'/>
            </g>
            <g style='isolation: isolate'>
                <line x1='165' y1='28' x2='165' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#E4E2E2' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
                <line x1='330' y1='28' x2='330' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#E4E2E2' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(82.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#70A5FD' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>{total}</text>
                </g>
                <g transform='translate(82.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#70A5FD' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.7s'>Total Contributions</text>
                </g>
                <g transform='translate(82.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#38BDAE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.8s'>{account_range}</text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(247.5, 108)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#22c55e' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>Current Streak</text>
                </g>
                <g transform='translate(247.5, 145)'>
                    <text x='0' y='21' stroke-width='0' text-anchor='middle' fill='#38BDAE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>{current_range}</text>
                </g>
                <g mask='url(#mask_out_ring_behind_fire)'>
                    <circle cx='247.5' cy='71' r='40' fill='none' stroke='#22c55e' stroke-width='5' style='opacity: 0; animation: fadein 0.5s linear forwards 0.4s'></circle>
                </g>
                <g transform='translate(247.5, 19.5)' stroke-opacity='0' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                    <path d='M -12 -0.5 L 15 -0.5 L 15 23.5 L -12 23.5 L -12 -0.5 Z' fill='none'/>
                    <path d='M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z' fill='#22c55e' stroke-opacity='0'/>
                </g>
                <g transform='translate(247.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#BF91F3' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='animation: currstreak 0.6s linear forwards'>{current_count}</text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <g transform='translate(412.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#70A5FD' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.2s'>{longest_count}</text>
                </g>
                <g transform='translate(412.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#70A5FD' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.3s'>Longest Streak</text>
                </g>
                <g transform='translate(412.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#38BDAE' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.4s'>{longest_range}</text>
                </g>
            </g>
        </g>
    </svg>
"""


def main() -> None:
    today = datetime.now(timezone.utc).date()
    account_created_at = fetch_account_created_at(GITHUB_USER)
    contributions = fetch_contribution_days(GITHUB_USER, account_created_at, today)
    total, current, longest = calculate_streaks(contributions, today=today)

    stats = StreakStats(
        total_contributions=total,
        account_created_at=account_created_at,
        current=current,
        longest=longest,
    )
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(render_svg(stats), encoding="utf-8")
    print(
        f"[streak] total={total} current={current.length} "
        f"longest={longest.length} range={format_streak_range(longest)}"
    )


if __name__ == "__main__":
    main()
