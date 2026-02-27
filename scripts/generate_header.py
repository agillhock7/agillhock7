#!/usr/bin/env python3
"""Generate a custom profile header SVG with top-right metric chips."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OUTFILE = Path("assets/header.svg")


def api_get_json(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-header-generator",
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
        batch = api_get_json(url)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_profile_views(user: str) -> int:
    url = f"https://komarev.com/ghpvc/?username={user}&label=Profile%20Views&style=flat"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "custom-profile-header-generator"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        svg = resp.read().decode("utf-8")

    matches = re.findall(r'<text[^>]*y="14">([^<]+)</text>', svg)
    for text in reversed(matches):
        value = text.replace(",", "").strip()
        if value.isdigit():
            return int(value)
    return 0


def fmt(n: int) -> str:
    return f"{n:,}"


def estimate_text_width(text: str, font_size: float, letter_spacing: float) -> float:
    compact = len(text.replace(" ", ""))
    spaces = text.count(" ")
    return (compact * (font_size * 0.58 + letter_spacing)) + (spaces * (font_size * 0.34))


def octicon_path(kind: str) -> str:
    paths = {
        "eye": "M1.5 8s2.7-4.5 6.5-4.5S14.5 8 14.5 8s-2.7 4.5-6.5 4.5S1.5 8 1.5 8Zm6.5 2.4a2.4 2.4 0 1 0 0-4.8 2.4 2.4 0 0 0 0 4.8Z",
        "users": "M5.2 7.1a2.1 2.1 0 1 1 4.2 0 2.1 2.1 0 0 1-4.2 0Zm-3 8.4v-.8c0-2.3 1.9-4.2 4.2-4.2h1.8c2.3 0 4.2 1.9 4.2 4.2v.8H2.2Zm10.5-9.3a1.8 1.8 0 1 1 0 3.6h-.6a2.8 2.8 0 0 0 .6-3.6Zm.4 9.3v-.8c0-1.2-.4-2.3-1.1-3.2h.3c1.9 0 3.4 1.5 3.4 3.4v.6h-2.6Z",
        "star": "M8 1.25a.75.75 0 0 1 .67.42l1.88 3.81 4.2.61a.75.75 0 0 1 .41 1.28l-3.04 2.97.72 4.19a.75.75 0 0 1-1.09.79L8 13.35l-3.77 1.97a.75.75 0 0 1-1.08-.79l.71-4.19L.82 7.37a.75.75 0 0 1 .42-1.28l4.2-.61L7.32 1.67A.75.75 0 0 1 8 1.25Z",
    }
    return paths.get(kind, "")


def chip_svg(x: int, y: int, label: str, value: str, icon: str) -> tuple[str, int]:
    label_text = label.upper()
    value_text = value
    label_font_size = 10
    label_letter_spacing = 0.2
    label_text_w = estimate_text_width(label_text, label_font_size, label_letter_spacing)
    label_w = max(84, int(label_text_w + 34))
    value_w = max(34, int(len(value_text) * 7 + 18))
    h = 32
    total_w = label_w + value_w
    icon_path = octicon_path(icon)
    text_y = 21
    value_x = label_w + (value_w / 2)
    label_text_x = 26
    label_available_w = label_w - label_text_x - 8

    svg = f"""
  <g transform="translate({x} {y})">
    <rect x="0" y="0" width="{total_w}" height="{h}" rx="7" fill="#1d1328" stroke="#5b2e66" />
    <rect x="0" y="0" width="{label_w}" height="{h}" rx="7" fill="#311a44" />
    <rect x="{label_w - 6}" y="0" width="6" height="{h}" fill="#311a44" />
    <rect x="{label_w}" y="0" width="{value_w}" height="{h}" rx="7" fill="url(#copperGrad)" />
    <rect x="{label_w}" y="0" width="6" height="{h}" fill="url(#copperGrad)" />
    <g transform="translate(8 9) scale(0.78)" fill="#fdf2f8" opacity="0.95">
      <path d="{icon_path}" />
    </g>
    <text x="{label_text_x}" y="{text_y}" fill="#fde7ff" font-size="{label_font_size}" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-weight="700" letter-spacing="{label_letter_spacing}" textLength="{label_available_w}" lengthAdjust="spacingAndGlyphs">{label_text}</text>
    <text x="{value_x}" y="{text_y}" text-anchor="middle" fill="#fff9f0" font-size="14" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-weight="800">{value_text}</text>
  </g>
"""
    return svg, total_w


def build_svg(name: str, slogan: str, views: int, followers: int, stars: int) -> str:
    width = 1200
    height = 220
    chips = [
        ("Profile Views", fmt(views), "eye"),
        ("Followers", fmt(followers), "users"),
        ("Stars", fmt(stars), "star"),
    ]

    spacing = 8
    chip_parts: list[str] = []
    total_chip_width = 0
    chip_widths = []
    for label, value, icon in chips:
        _, w = chip_svg(0, 0, label, value, icon)
        chip_widths.append(w)
        total_chip_width += w
    total_chip_width += spacing * (len(chips) - 1)

    start_x = width - total_chip_width - 28
    chip_y = 22
    cursor = start_x
    for idx, (label, value, icon) in enumerate(chips):
        snippet, w = chip_svg(cursor, chip_y, label, value, icon)
        chip_parts.append(snippet)
        cursor += w
        if idx < len(chips) - 1:
            cursor += spacing

    chips_group = "".join(chip_parts)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="Alexander Gill header">
  <title>Alexander Gill - Moving Forward</title>
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#171F1F" />
      <stop offset="100%" stop-color="#8CCAAF" />
    </linearGradient>
    <linearGradient id="copperGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#b46a3a" />
      <stop offset="100%" stop-color="#d49a62" />
    </linearGradient>
    <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="5" stdDeviation="4" flood-color="#120f1f" flood-opacity="0.5"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bgGrad)" />
  <g transform="translate(0,220) scale(1.40515,-1.40515)">
    <path d="M0 0L 0 60Q 213.5 100 427 70T 854 95L 854 0 Z" fill="url(#bgGrad)" opacity="0.4" >
      <animate
        attributeName="d"
        dur="20s"
        repeatCount="indefinite"
        keyTimes="0;0.333;0.667;1"
        calcMode="spline"
        keySplines="0.2 0 0.2 1;0.2 0 0.2 1;0.2 0 0.2 1"
        begin="0s"
        values="M0 0L 0 60Q 213.5 100 427 70T 854 95L 854 0 Z;M0 0L 0 85Q 213.5 100 427 80T 854 70L 854 0 Z;M0 0L 0 105Q 213.5 75 427 105T 854 70L 854 0 Z;M0 0L 0 60Q 213.5 100 427 70T 854 95L 854 0 Z">
      </animate>
    </path>
    <path d="M0 0L 0 75Q 213.5 120 427 90T 854 100L 854 0 Z" fill="url(#bgGrad)" opacity="0.4" >
      <animate
        attributeName="d"
        dur="20s"
        repeatCount="indefinite"
        keyTimes="0;0.333;0.667;1"
        calcMode="spline"
        keySplines="0.2 0 0.2 1;0.2 0 0.2 1;0.2 0 0.2 1"
        begin="-10s"
        values="M0 0L 0 75Q 213.5 120 427 90T 854 100L 854 0 Z;M0 0L 0 90Q 213.5 60 427 60T 854 80L 854 0 Z;M0 0L 0 85Q 213.5 65 427 90T 854 105L 854 0 Z;M0 0L 0 75Q 213.5 120 427 90T 854 100L 854 0 Z">
      </animate>
    </path>
  </g>

  <g filter="url(#softGlow)">
    <text x="60" y="122" fill="#8ecfb3" font-size="88" font-weight="800" font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{name}</text>
    <text x="60" y="170" fill="#8ecfb3" opacity="0.95" font-size="47" font-weight="700" font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{slogan}</text>
  </g>

  <g filter="url(#softGlow)">
    <rect x="{start_x - 10}" y="{chip_y - 7}" width="{total_chip_width + 20}" height="46" rx="10" fill="#1b1624" opacity="0.35"/>
    {chips_group}
  </g>
</svg>
"""


def main() -> None:
    user_info = api_get_json(f"https://api.github.com/users/{GITHUB_USER}")
    repos = fetch_repos(GITHUB_USER)

    followers = 0
    if isinstance(user_info, dict):
        followers = int(user_info.get("followers", 0))
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos if isinstance(r, dict))
    views = fetch_profile_views(GITHUB_USER)

    svg = build_svg("Alexander Gill", "Moving Forward", views, followers, stars)
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
