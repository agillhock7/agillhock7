#!/usr/bin/env python3
"""Generate custom tech stack badges with icon-forward styling."""

from __future__ import annotations

import base64
import urllib.request
from pathlib import Path


OUTDIR = Path("assets/stack")

SIMPLE_ICON_ITEMS = [
    ("vue", "Vue", "vuedotjs"),
    ("vite", "Vite", "vite"),
    ("typescript", "TypeScript", "typescript"),
    ("javascript", "JavaScript", "javascript"),
    ("php", "PHP", "php"),
    ("wordpress", "WordPress", "wordpress"),
    ("apache", "Apache", "apache"),
    ("cpanel", "cPanel", "cpanel"),
    ("mysql", "MySQL", "mysql"),
    ("postgresql", "PostgreSQL", "postgresql"),
    ("linux", "Linux", "linux"),
    ("ubuntu", "Ubuntu", "ubuntu"),
    ("ssl-tls", "SSL/TLS", "letsencrypt"),
    ("git", "Git", "git"),
]

CODEX_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path fill="#ffffff" d="M16.585 10a6.585 6.585 0 1 0-13.17 0 6.585 6.585 0 0 0 13.17 0m-3.252 1.418.135.014a.665.665 0 0 1 0 1.302l-.135.014h-2.5a.665.665 0 0 1 0-1.33zm-5.68 1.008a.665.665 0 0 1-1.14-.685zm1.25-2.768a.66.66 0 0 1 0 .684l-1.25 2.084-.57-.343-.57-.342L7.557 10 6.513 8.259l.57-.342.57-.343zM6.741 7.347a.665.665 0 0 1 .912.227l-1.14.685a.665.665 0 0 1 .228-.912M17.915 10a7.915 7.915 0 1 1-15.83 0 7.915 7.915 0 0 1 15.83 0"/>
</svg>"""


def fetch_simple_icon(slug: str) -> str:
    url = f"https://cdn.simpleicons.org/{slug}/white"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "custom-profile-tech-badge-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def to_data_uri(svg_source: str) -> str:
    encoded = base64.b64encode(svg_source.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_badge(label: str, icon_uri: str, gradient_id: str) -> str:
    icon_panel_width = 42
    label_panel_width = max(76, int(len(label) * 8.5) + 18)
    total_width = icon_panel_width + label_panel_width
    height = 34
    text_x = icon_panel_width + (label_panel_width / 2)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label}">
  <title>{label}</title>
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1d4ed8" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>
  </defs>
  <g shape-rendering="geometricPrecision">
    <rect x="0.5" y="0.5" width="{total_width - 1}" height="{height - 1}" rx="7" fill="#0b1220" stroke="#1f2a3a"/>
    <rect x="{icon_panel_width}" y="1" width="{label_panel_width - 1}" height="{height - 2}" rx="6" fill="url(#{gradient_id})"/>
  </g>
  <image x="11" y="7" width="20" height="20" href="{icon_uri}" />
  <text
    x="{text_x}"
    y="22"
    fill="#ffffff"
    text-anchor="middle"
    font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
    font-size="12"
    font-weight="700"
    letter-spacing="0.8"
  >
    {label.upper()}
  </text>
</svg>
"""


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    for filename, label, slug in SIMPLE_ICON_ITEMS:
        icon_svg = fetch_simple_icon(slug)
        icon_uri = to_data_uri(icon_svg)
        badge_svg = build_badge(label, icon_uri, f"grad-{filename}")
        (OUTDIR / f"{filename}.svg").write_text(badge_svg, encoding="utf-8")

    codex_uri = to_data_uri(CODEX_ICON)
    codex_badge = build_badge("Codex", codex_uri, "grad-codex")
    (OUTDIR / "codex.svg").write_text(codex_badge, encoding="utf-8")


if __name__ == "__main__":
    main()
