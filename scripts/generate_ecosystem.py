#!/usr/bin/env python3
"""Generate the animated Forward Lab product ecosystem map."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

if __package__:
    from .profile_config import load_profile
else:
    from profile_config import load_profile


OUTFILE = Path("assets/ecosystem.svg")
NODE_POSITIONS = [
    (245, 145),
    (245, 250),
    (245, 355),
    (955, 145),
    (955, 250),
    (955, 355),
]


def build_svg(projects: list[dict[str, Any]]) -> str:
    if len(projects) != len(NODE_POSITIONS):
        raise ValueError(f"The ecosystem map requires exactly {len(NODE_POSITIONS)} projects.")

    routes: list[str] = []
    nodes: list[str] = []
    for index, (project, (x, y)) in enumerate(zip(projects, NODE_POSITIONS)):
        side = -1 if x < 600 else 1
        start_x = 515 if side < 0 else 685
        end_x = x + (126 if side < 0 else -126)
        control_x = 405 if side < 0 else 795
        accent = str(project["accent"])
        delay = -(index * 1.1)
        routes.append(
            f'<path class="route route-{index}" d="M{start_x} 250 C{control_x} 250 {control_x} {y} {end_x} {y}" '
            f'stroke="{accent}" style="animation-delay:{delay}s" />'
        )

        card_x = x - 126
        card_y = y - 39
        domain = html.escape(str(project["domain"]))
        name = html.escape(str(project["name"]))
        tier = "FLAGSHIP" if project["tier"] == "flagship" else "FROM THE LAB"
        nodes.append(
            f'<g class="node" style="animation-delay:{delay}s">'
            f'<rect x="{card_x}" y="{card_y}" width="252" height="78" rx="13" fill="#0B1916" stroke="{accent}" stroke-opacity="0.6" />'
            f'<rect x="{card_x}" y="{card_y}" width="5" height="78" rx="2.5" fill="{accent}" />'
            f'<circle cx="{card_x + 23}" cy="{card_y + 23}" r="6" fill="{accent}" />'
            f'<text x="{card_x + 39}" y="{card_y + 27}" fill="{accent}" font-size="10" font-weight="700" letter-spacing="1.4">{domain}</text>'
            f'<text x="{card_x + 20}" y="{card_y + 54}" fill="#E8FFF5" font-size="17" font-weight="700">{name}</text>'
            f'<text x="{card_x + 232}" y="{card_y + 27}" text-anchor="end" fill="#58786E" font-size="8" letter-spacing="1">{tier}</text>'
            "</g>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="500" viewBox="0 0 1200 500" role="img" aria-labelledby="ecosystem-title ecosystem-description">
  <title id="ecosystem-title">The Forward Lab product ecosystem</title>
  <desc id="ecosystem-description">Six production systems connect money, movement, identity, media, logistics, and community.</desc>
  <defs>
    <linearGradient id="eco-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07110F" />
      <stop offset="0.5" stop-color="#0B1916" />
      <stop offset="1" stop-color="#091411" />
    </linearGradient>
    <radialGradient id="core-halo">
      <stop offset="0" stop-color="#8CCAAF" stop-opacity="0.28" />
      <stop offset="1" stop-color="#8CCAAF" stop-opacity="0" />
    </radialGradient>
    <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="#8CCAAF" fill-opacity="0.08" />
    </pattern>
    <filter id="eco-glow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .route {{ fill: none; stroke-width: 2; stroke-opacity: .62; stroke-dasharray: 9 14; animation: flow 8s linear infinite; }}
    .node {{ transform-box: fill-box; transform-origin: center; animation: breathe 5s ease-in-out infinite; }}
    .ring {{ transform-origin: 600px 250px; animation: rotate 32s linear infinite; }}
    .core {{ animation: core 3s ease-in-out infinite; }}
    @keyframes flow {{ to {{ stroke-dashoffset: -184; }} }}
    @keyframes breathe {{ 0%, 100% {{ opacity: .82; }} 50% {{ opacity: 1; }} }}
    @keyframes rotate {{ to {{ transform: rotate(360deg); }} }}
    @keyframes core {{ 0%, 100% {{ opacity: .5; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ .route, .node, .ring, .core {{ animation: none !important; }} }}
  </style>

  <rect width="1200" height="500" rx="16" fill="url(#eco-bg)" />
  <rect x="1" y="1" width="1198" height="498" rx="15" fill="none" stroke="#24483F" />
  <rect width="1200" height="500" rx="16" fill="url(#dots)" />

  <g font-family="Verdana,Geneva,DejaVu Sans,sans-serif">
    <text x="48" y="52" fill="#8CCAAF" font-size="13" font-weight="700" letter-spacing="2.4">THE PRODUCT CONSTELLATION</text>
    <text x="1152" y="52" text-anchor="end" fill="#58786E" font-size="11" letter-spacing="1.4">SIX SYSTEMS // ONE OPERATING PHILOSOPHY</text>
    {''.join(routes)}

    <circle cx="600" cy="250" r="142" fill="url(#core-halo)" />
    <circle class="ring" cx="600" cy="250" r="103" fill="none" stroke="#8CCAAF" stroke-opacity="0.28" stroke-dasharray="3 12" />
    <circle cx="600" cy="250" r="84" fill="#07110F" stroke="#315E52" stroke-width="2" />
    <circle class="core" cx="600" cy="250" r="67" fill="#102B25" stroke="#8CCAAF" stroke-opacity="0.55" filter="url(#eco-glow)" />
    <text x="600" y="231" text-anchor="middle" fill="#F1FFF9" font-size="20" font-weight="800" letter-spacing="1.8">FORWARD</text>
    <text x="600" y="257" text-anchor="middle" fill="#8CCAAF" font-size="16" font-weight="700" letter-spacing="4">LAB</text>
    <text x="600" y="281" text-anchor="middle" fill="#668A7E" font-size="9" letter-spacing="1.5">BUILD · SHIP · OPERATE</text>
    {''.join(nodes)}
  </g>
</svg>
"""


def main() -> None:
    profile = load_profile()
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(build_svg(profile["projects"]), encoding="utf-8")


if __name__ == "__main__":
    main()
