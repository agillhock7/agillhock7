#!/usr/bin/env python3
"""Generate an activity graph SVG from GitHub contribution calendar data."""

from __future__ import annotations

import html
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if __package__:
    from .generate_streak_card import fetch_contribution_range
else:
    from generate_streak_card import fetch_contribution_range


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
OUTFILE = Path("assets/activity-graph.svg")
GRAPH_DAYS = 31
WIDTH = 1200
HEIGHT = 420
PLOT_LEFT = 90
PLOT_RIGHT = 1150
PLOT_TOP = 80
PLOT_BOTTOM = 350
Y_TICKS = 4


def rounded_axis_max(maximum: int) -> int:
    """Return an integer axis maximum that produces four whole-number intervals."""

    return max(Y_TICKS, ((maximum + Y_TICKS - 1) // Y_TICKS) * Y_TICKS)


def render_svg(
    contributions: dict[date, int],
    *,
    title: str = "Contribution Activity",
    generated_at: datetime | None = None,
) -> str:
    if not contributions:
        raise ValueError("At least one contribution day is required.")

    days = sorted(contributions)
    counts = [max(0, int(contributions[day])) for day in days]
    axis_max = rounded_axis_max(max(counts))
    plot_width = PLOT_RIGHT - PLOT_LEFT
    plot_height = PLOT_BOTTOM - PLOT_TOP
    denominator = max(len(days) - 1, 1)

    points = [
        (
            PLOT_LEFT + (index * plot_width / denominator),
            PLOT_BOTTOM - (count * plot_height / axis_max),
        )
        for index, count in enumerate(counts)
    ]
    line_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_points = (
        f"{PLOT_LEFT},{PLOT_BOTTOM} {line_points} {PLOT_RIGHT},{PLOT_BOTTOM}"
    )

    grid_lines = []
    y_labels = []
    for tick in range(Y_TICKS + 1):
        value = tick * axis_max // Y_TICKS
        y = PLOT_BOTTOM - (tick * plot_height / Y_TICKS)
        grid_lines.append(
            f'<line x1="{PLOT_LEFT}" x2="{PLOT_RIGHT}" y1="{y:.1f}" y2="{y:.1f}" '
            'stroke="#243247" stroke-width="1" />'
        )
        y_labels.append(
            f'<text x="76" y="{y + 4:.1f}" text-anchor="end" fill="#8ccfaf" '
            f'font-size="12">{value}</text>'
        )

    label_indexes = sorted({0, len(days) - 1, *range(5, len(days), 5)})
    x_labels = []
    for index in label_indexes:
        x, _ = points[index]
        day = days[index]
        x_labels.append(
            f'<text x="{x:.1f}" y="376" text-anchor="middle" fill="#8ccfaf" '
            f'font-size="12">{day.strftime("%b")} {day.day}</text>'
        )

    point_nodes = []
    for day, count, (x, y) in zip(days, counts, points):
        noun = "contribution" if count == 1 else "contributions"
        point_nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#9be9a8">'
            f'<title>{day.isoformat()}: {count} {noun}</title></circle>'
        )

    generated_at = generated_at or datetime.now(timezone.utc)
    updated = generated_at.astimezone(timezone.utc).strftime("Updated %Y-%m-%d %H:%M UTC")
    safe_title = html.escape(title)
    description = html.escape(
        f"Daily GitHub contributions from {days[0].isoformat()} through {days[-1].isoformat()}."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="activity-title activity-description">
  <title id="activity-title">{safe_title}</title>
  <desc id="activity-description">{description}</desc>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="#0b1220" />
  <text x="{PLOT_LEFT}" y="43" fill="#8ccfaf" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="24" font-weight="700">{safe_title}</text>
  <text x="{PLOT_RIGHT}" y="43" text-anchor="end" fill="#6f86a0" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">{updated}</text>
  <g font-family="Verdana,Geneva,DejaVu Sans,sans-serif">
    {''.join(grid_lines)}
    {''.join(y_labels)}
    {''.join(x_labels)}
    <polygon points="{area_points}" fill="#1f5f4a" fill-opacity="0.55" />
    <polyline points="{line_points}" fill="none" stroke="#22c55e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
    {''.join(point_nodes)}
    <text x="620" y="405" text-anchor="middle" fill="#8ccfaf" font-size="12">Date</text>
    <text x="21" y="215" text-anchor="middle" fill="#8ccfaf" font-size="12" transform="rotate(-90 21 215)">Contributions</text>
  </g>
</svg>
"""


def main() -> None:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=GRAPH_DAYS - 1)
    contribution_data = fetch_contribution_range(GITHUB_USER, start, end)
    svg = render_svg(contribution_data.days)

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(svg, encoding="utf-8")
    print(
        f"[activity] generated {len(contribution_data.days)} days for {GITHUB_USER}; "
        f"total={sum(contribution_data.days.values())}"
    )


if __name__ == "__main__":
    main()
