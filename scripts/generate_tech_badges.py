#!/usr/bin/env python3
"""Generate custom tech stack badges with icon-forward styling."""

from __future__ import annotations

import base64
import urllib.request
from pathlib import Path


OUTDIR = Path("assets/stack")

ICON_ITEMS = [
    ("vue", "Vue", "simple:vuedotjs"),
    ("vite", "Vite", "simple:vite"),
    ("typescript", "TypeScript", "simple:typescript"),
    ("javascript", "JavaScript", "simple:javascript"),
    ("lua", "Lua", "simple:lua"),
    ("php", "PHP", "simple:php"),
    ("wordpress", "WordPress", "simple:wordpress"),
    ("apache", "Apache", "simple:apache"),
    ("cpanel", "cPanel", "simple:cpanel"),
    ("mysql", "MySQL", "simple:mysql"),
    ("postgresql", "PostgreSQL", "simple:postgresql"),
    ("linux", "Linux", "simple:linux"),
    ("ubuntu", "Ubuntu", "simple:ubuntu"),
    ("ssl-tls", "SSL/TLS", "simple:letsencrypt"),
    ("git", "Git", "simple:git"),
    ("vscode", "VS Code", "url:https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vscode/vscode-original.svg"),
    ("roblox-studio", "Roblox Studio", "simple:robloxstudio"),
    ("hosting", "Hosting", "custom:hosting"),
]

CODEX_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path fill="#ffffff" d="M16.585 10a6.585 6.585 0 1 0-13.17 0 6.585 6.585 0 0 0 13.17 0m-3.252 1.418.135.014a.665.665 0 0 1 0 1.302l-.135.014h-2.5a.665.665 0 0 1 0-1.33zm-5.68 1.008a.665.665 0 0 1-1.14-.685zm1.25-2.768a.66.66 0 0 1 0 .684l-1.25 2.084-.57-.343-.57-.342L7.557 10 6.513 8.259l.57-.342.57-.343zM6.741 7.347a.665.665 0 0 1 .912.227l-1.14.685a.665.665 0 0 1 .228-.912M17.915 10a7.915 7.915 0 1 1-15.83 0 7.915 7.915 0 0 1 15.83 0"/>
</svg>"""

HOSTING_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="9" fill="none" stroke="#60A5FA" stroke-width="1.8"/>
  <ellipse cx="12" cy="12" rx="4.4" ry="9" fill="none" stroke="#38BDF8" stroke-width="1.6"/>
  <path d="M3 12h18M4.8 8.2h14.4M4.8 15.8h14.4" fill="none" stroke="#93C5FD" stroke-width="1.4" stroke-linecap="round"/>
</svg>"""


def fetch_simple_icon(slug: str) -> str:
    url = f"https://cdn.simpleicons.org/{slug}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "custom-profile-tech-badge-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_svg_url(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "custom-profile-tech-badge-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_icon(source: str) -> str:
    if source.startswith("simple:"):
        return fetch_simple_icon(source.split(":", 1)[1])
    if source.startswith("url:"):
        return fetch_svg_url(source.split(":", 1)[1])
    if source == "custom:hosting":
        return HOSTING_ICON
    raise ValueError(f"Unsupported icon source: {source}")


def to_data_uri(svg_source: str) -> str:
    encoded = base64.b64encode(svg_source.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_badge(label: str, icon_uri: str, gradient_id: str) -> str:
    icon_panel_width = 44
    label_panel_width = max(82, int(len(label) * 8.6) + 22)
    total_width = icon_panel_width + label_panel_width
    height = 36
    text_x = icon_panel_width + (label_panel_width / 2)
    right_edge = total_width - 1
    bottom_edge = height - 1
    right_corner_start = total_width - 8
    bottom_corner_start = height - 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label}">
  <title>{label}</title>
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1e4a3f" />
      <stop offset="100%" stop-color="#8ccfaf" />
    </linearGradient>
    <linearGradient id="{gradient_id}-top" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#d9fff0" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#d9fff0" stop-opacity="0" />
    </linearGradient>
  </defs>
  <g>
    <rect x="0.5" y="0.5" width="{total_width - 1}" height="{height - 1}" rx="8" fill="#0f1a18" stroke="#2b4c44"/>
    <path d="M{icon_panel_width} 1 H{right_corner_start} Q{right_edge} 1 {right_edge} 8 V{bottom_corner_start} Q{right_edge} {bottom_edge} {right_corner_start} {bottom_edge} H{icon_panel_width} Z" fill="url(#{gradient_id})"/>
    <rect x="1" y="1" width="{total_width - 2}" height="11" rx="8" fill="url(#{gradient_id}-top)" />
  </g>
  <image x="11" y="7" width="22" height="22" href="{icon_uri}" />
  <text
    x="{text_x}"
    y="23"
    fill="#f1fff9"
    text-anchor="middle"
    font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
    font-size="11"
    font-weight="700"
    letter-spacing="0.9"
  >
    {label.upper()}
  </text>
</svg>
"""


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    for filename, label, icon_source in ICON_ITEMS:
        icon_svg = fetch_icon(icon_source)
        icon_uri = to_data_uri(icon_svg)
        badge_svg = build_badge(label, icon_uri, f"grad-{filename}")
        (OUTDIR / f"{filename}.svg").write_text(badge_svg, encoding="utf-8")

    codex_uri = to_data_uri(CODEX_ICON)
    codex_badge = build_badge("Codex", codex_uri, "grad-codex")
    (OUTDIR / "codex.svg").write_text(codex_badge, encoding="utf-8")


if __name__ == "__main__":
    main()
