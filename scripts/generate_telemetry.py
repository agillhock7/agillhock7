#!/usr/bin/env python3
"""Generate a unified live telemetry console for the profile README."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if __package__:
    from . import generate_activity_graph as activity
    from . import generate_stats_card as stats
    from . import generate_streak_card as streak
    from . import generate_top_languages_card as languages
    from .profile_config import load_profile
else:
    import generate_activity_graph as activity
    import generate_stats_card as stats
    import generate_streak_card as streak
    import generate_top_languages_card as languages
    from profile_config import load_profile


OUTFILE = Path("assets/telemetry.svg")
GRAPH_DAYS = 31


@dataclass(frozen=True)
class Telemetry:
    public_repos: int
    private_repos: int | str
    live_systems: int
    stars: int
    followers: int
    total_contributions: int
    current_streak: streak.Streak
    longest_streak: streak.Streak
    last_push: str
    contributions: dict[date, int]
    top_languages: list[tuple[str, int, float]]
    generated_at: datetime


def _metric_card(x: int, label: str, value: int | str, accent: str) -> str:
    safe_label = html.escape(label.upper())
    safe_value = html.escape(f"{value:,}" if isinstance(value, int) else str(value))
    return f"""<g transform="translate({x} 91)">
      <rect width="174" height="82" rx="12" fill="#0B1916" stroke="#203C35" />
      <rect width="4" height="82" rx="2" fill="{accent}" />
      <text x="18" y="28" fill="#6F9185" font-size="9" font-weight="700" letter-spacing="1.2">{safe_label}</text>
      <text x="18" y="61" fill="#EDFFF7" font-size="25" font-weight="800">{safe_value}</text>
    </g>"""


def _activity_plot(contributions: dict[date, int]) -> str:
    days = sorted(contributions)
    if not days:
        return '<text x="60" y="342" fill="#6F9185" font-size="13">No contribution data available.</text>'

    values = [max(0, int(contributions[day])) for day in days]
    axis_max = activity.rounded_axis_max(max(values))
    left, right, top, bottom = 58, 770, 238, 454
    plot_width = right - left
    plot_height = bottom - top
    denominator = max(len(days) - 1, 1)
    points = [
        (
            left + (index * plot_width / denominator),
            bottom - (value * plot_height / axis_max),
        )
        for index, value in enumerate(values)
    ]
    line_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_points = f"{left},{bottom} {line_points} {right},{bottom}"

    grid = []
    labels = []
    for tick in range(5):
        y = bottom - tick * plot_height / 4
        value = tick * axis_max // 4
        grid.append(
            f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="#213A34" />'
        )
        labels.append(
            f'<text x="48" y="{y + 4:.1f}" text-anchor="end" fill="#56746A" font-size="9">{value}</text>'
        )

    date_labels = []
    for index in sorted({0, len(days) // 2, len(days) - 1}):
        x, _ = points[index]
        day = days[index]
        date_labels.append(
            f'<text x="{x:.1f}" y="477" text-anchor="middle" fill="#56746A" font-size="9">{day.strftime("%b")} {day.day}</text>'
        )

    circles = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#9BE9A8"><title>{day.isoformat()}: {value} contributions</title></circle>'
        for day, value, (x, y) in zip(days, values, points)
    )
    return f"""{''.join(grid)}{''.join(labels)}{''.join(date_labels)}
      <polygon points="{area_points}" fill="#1F5F4A" fill-opacity="0.48" />
      <polyline class="telemetry-line" points="{line_points}" fill="none" stroke="#22C55E" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      {circles}"""


def _language_rows(summary: list[tuple[str, int, float]]) -> str:
    if not summary:
        return '<text x="824" y="412" fill="#6F9185" font-size="12">No public language data.</text>'

    rows: list[str] = []
    for index, (language, _, percent) in enumerate(summary[:5]):
        y = 417 + index * 27
        color = languages.language_color(language)
        width = max(4, round(274 * percent / 100))
        rows.append(
            f'<circle cx="825" cy="{y - 4}" r="4" fill="{color}" />'
            f'<text x="837" y="{y}" fill="#CDE7DD" font-size="10" font-weight="700">{html.escape(language)}</text>'
            f'<text x="1122" y="{y}" text-anchor="end" fill="#6F9185" font-size="9">{percent:.1f}%</text>'
            f'<rect x="825" y="{y + 7}" width="297" height="4" rx="2" fill="#172923" />'
            f'<rect x="825" y="{y + 7}" width="{width}" height="4" rx="2" fill="{color}" />'
        )
    return "".join(rows)


def render_svg(data: Telemetry) -> str:
    updated = data.generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    metrics = [
        ("Public repos", data.public_repos, "#38BDF8"),
        ("Private repos", data.private_repos, "#A78BFA"),
        ("Live systems", data.live_systems, "#22C55E"),
        ("Stars earned", data.stars, "#F5B942"),
        ("Followers", data.followers, "#FB923C"),
        ("Contributions", data.total_contributions, "#8CCAAF"),
    ]
    metric_cards = "".join(
        _metric_card(42 + index * 189, label, value, accent)
        for index, (label, value, accent) in enumerate(metrics)
    )
    current_range = html.escape(streak.format_streak_range(data.current_streak))
    longest_range = html.escape(streak.format_streak_range(data.longest_streak))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="590" viewBox="0 0 1200 590" role="img" aria-labelledby="telemetry-title telemetry-description">
  <title id="telemetry-title">Forward Lab live telemetry</title>
  <desc id="telemetry-description">GitHub repository, contribution, streak, and language statistics for Alexander Gill.</desc>
  <defs>
    <linearGradient id="telemetry-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07110F" />
      <stop offset="1" stop-color="#0C1D19" />
    </linearGradient>
    <linearGradient id="telemetry-title-grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8CCAAF" />
      <stop offset="1" stop-color="#38BDF8" />
    </linearGradient>
    <pattern id="telemetry-grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M30 0H0V30" fill="none" stroke="#8CCAAF" stroke-opacity="0.035" />
    </pattern>
  </defs>
  <style>
    .status-dot {{ animation: status 2.4s ease-in-out infinite; }}
    .telemetry-line {{ stroke-dasharray: 1800; stroke-dashoffset: 1800; animation: trace 2.8s ease-out forwards; }}
    @keyframes status {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
    @keyframes trace {{ to {{ stroke-dashoffset: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .status-dot, .telemetry-line {{ animation: none !important; stroke-dashoffset: 0; }} }}
  </style>
  <rect width="1200" height="590" rx="16" fill="url(#telemetry-bg)" />
  <rect x="1" y="1" width="1198" height="588" rx="15" fill="none" stroke="#24483F" />
  <rect width="1200" height="590" rx="16" fill="url(#telemetry-grid)" />
  <g font-family="Verdana,Geneva,DejaVu Sans,sans-serif">
    <circle class="status-dot" cx="48" cy="46" r="6" fill="#22C55E" />
    <text x="66" y="52" fill="url(#telemetry-title-grad)" font-size="20" font-weight="800" letter-spacing="2">LIVE TELEMETRY</text>
    <text x="1152" y="50" text-anchor="end" fill="#58786E" font-size="10" letter-spacing="1">LAST REPO PUSH // {html.escape(data.last_push)}</text>
    {metric_cards}

    <rect x="42" y="198" width="750" height="354" rx="13" fill="#091713" stroke="#203C35" />
    <text x="58" y="225" fill="#8CCAAF" font-size="11" font-weight="700" letter-spacing="1.5">31-DAY CONTRIBUTION SIGNAL</text>
    {_activity_plot(data.contributions)}

    <rect x="807" y="198" width="351" height="154" rx="13" fill="#091713" stroke="#203C35" />
    <text x="825" y="225" fill="#8CCAAF" font-size="11" font-weight="700" letter-spacing="1.5">STREAK ENGINE</text>
    <text x="825" y="276" fill="#EDFFF7" font-size="32" font-weight="800">{data.current_streak.length}</text>
    <text x="825" y="297" fill="#6F9185" font-size="9" letter-spacing="1">CURRENT // {current_range}</text>
    <line x1="978" y1="239" x2="978" y2="323" stroke="#203C35" />
    <text x="1002" y="276" fill="#EDFFF7" font-size="32" font-weight="800">{data.longest_streak.length}</text>
    <text x="1002" y="297" fill="#6F9185" font-size="9" letter-spacing="1">LONGEST</text>
    <text x="1002" y="316" fill="#58786E" font-size="8">{longest_range}</text>

    <rect x="807" y="368" width="351" height="184" rx="13" fill="#091713" stroke="#203C35" />
    <text x="825" y="390" fill="#8CCAAF" font-size="11" font-weight="700" letter-spacing="1.5">LANGUAGE SIGNAL</text>
    {_language_rows(data.top_languages)}
    <text x="1152" y="575" text-anchor="end" fill="#48645B" font-size="9" letter-spacing="1">UPDATED // {updated}</text>
  </g>
</svg>
"""


def collect_telemetry() -> Telemetry:
    profile = load_profile()
    now = datetime.now(timezone.utc)
    today = now.date()

    repos = stats.fetch_repos(stats.GITHUB_USER)
    user_info = stats.api_get(f"https://api.github.com/users/{stats.GITHUB_USER}")
    if not isinstance(user_info, dict):
        raise RuntimeError("GitHub user response was not an object.")

    account_created_at = streak.fetch_account_created_at(streak.GITHUB_USER)
    contribution_data = streak.fetch_contribution_range(
        streak.GITHUB_USER, account_created_at, today
    )
    total, current, longest = streak.calculate_streaks(
        contribution_data.days,
        today=today,
        total_contributions=contribution_data.total_contributions,
    )
    graph_start = today - timedelta(days=GRAPH_DAYS - 1)
    graph_days = {
        graph_start + timedelta(days=index): contribution_data.days.get(
            graph_start + timedelta(days=index), 0
        )
        for index in range(GRAPH_DAYS)
    }

    original_repos = languages.original_public_repos(repos)
    language_sets = languages.fetch_repo_language_totals(original_repos)
    language_summary = languages.summarize_language_totals(language_sets, limit=5)
    last_push = stats.format_iso_day(
        max((repo.get("pushed_at") for repo in repos if repo.get("pushed_at")), default=None)
    )

    return Telemetry(
        public_repos=int(user_info.get("public_repos", 0)),
        private_repos=stats.fetch_private_repo_count(stats.GITHUB_USER),
        live_systems=len(profile["projects"]),
        stars=sum(int(repo.get("stargazers_count", 0)) for repo in repos),
        followers=int(user_info.get("followers", 0)),
        total_contributions=total,
        current_streak=current,
        longest_streak=longest,
        last_push=last_push,
        contributions=graph_days,
        top_languages=language_summary,
        generated_at=now,
    )


def main() -> None:
    data = collect_telemetry()
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(render_svg(data), encoding="utf-8")
    print(
        f"[telemetry] repos={data.public_repos} live={data.live_systems} "
        f"contributions={data.total_contributions} streak={data.current_streak.length}"
    )


if __name__ == "__main__":
    main()
