#!/usr/bin/env python3
"""Generate the Forward Lab hero and footer SVGs."""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any

if __package__:
    from .profile_config import load_profile
else:
    from profile_config import load_profile


OUTFILE = Path("assets/header.svg")
FOOTER_FILE = Path("assets/footer.svg")
HEADER_HEIGHT = int(os.getenv("HEADER_HEIGHT", "340"))


def build_svg(brand: dict[str, Any]) -> str:
    height = max(300, HEADER_HEIGHT)
    name = html.escape(str(brand["name"]))
    eyebrow = html.escape(str(brand["eyebrow"]))
    positioning = html.escape(str(brand["positioning"]))
    promise = html.escape(str(brand["promise"]))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="hero-title hero-description">
  <title id="hero-title">{name} — The Forward Lab</title>
  <desc id="hero-description">{html.escape(str(brand['headline']))} {positioning}.</desc>
  <defs>
    <linearGradient id="hero-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#050B0A" />
      <stop offset="0.55" stop-color="#0A1714" />
      <stop offset="1" stop-color="#102922" />
    </linearGradient>
    <radialGradient id="mint-halo">
      <stop offset="0" stop-color="#8CCAAF" stop-opacity="0.34" />
      <stop offset="1" stop-color="#8CCAAF" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="headline-grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#F1FFF9" />
      <stop offset="0.72" stop-color="#8CCAAF" />
      <stop offset="1" stop-color="#38BDF8" />
    </linearGradient>
    <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M36 0H0V36" fill="none" stroke="#8CCAAF" stroke-opacity="0.07" />
    </pattern>
    <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="5" result="blur" />
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .route {{ stroke-dasharray: 10 13; animation: route 12s linear infinite; }}
    .orbit {{ transform-origin: 936px 174px; animation: orbit 36s linear infinite; }}
    .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 3.8s ease-in-out infinite; }}
    .pulse-b {{ animation-delay: -1.3s; }}
    .pulse-c {{ animation-delay: -2.6s; }}
    .cursor {{ animation: cursor 1.15s steps(1) infinite; }}
    .scan {{ animation: scan 7s ease-in-out infinite; }}
    @keyframes route {{ to {{ stroke-dashoffset: -230; }} }}
    @keyframes orbit {{ to {{ transform: rotate(360deg); }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .55; transform: scale(.88); }} 50% {{ opacity: 1; transform: scale(1.18); }} }}
    @keyframes cursor {{ 50% {{ opacity: 0; }} }}
    @keyframes scan {{ 0%, 100% {{ transform: translateX(-140px); opacity: 0; }} 20%, 80% {{ opacity: .25; }} 50% {{ transform: translateX(1180px); opacity: .08; }} }}
    @media (prefers-reduced-motion: reduce) {{ .route, .orbit, .pulse, .cursor, .scan {{ animation: none !important; }} }}
  </style>

  <rect width="1200" height="{height}" rx="16" fill="url(#hero-bg)" />
  <rect x="1" y="1" width="1198" height="{height - 2}" rx="15" fill="none" stroke="#24483F" />
  <rect width="1200" height="{height}" rx="16" fill="url(#grid)" />
  <circle cx="935" cy="174" r="310" fill="url(#mint-halo)" />
  <path class="scan" d="M-310 0H-170L-30 {height}H-170Z" fill="#8CCAAF" />

  <g font-family="Verdana,Geneva,DejaVu Sans,sans-serif">
    <circle cx="52" cy="45" r="5" fill="#6EE7B7" filter="url(#glow)" />
    <text x="70" y="50" fill="#8CCAAF" font-size="14" font-weight="700" letter-spacing="2.4">{eyebrow}</text>
    <text x="52" y="119" fill="url(#headline-grad)" font-size="40" font-weight="800" letter-spacing="0.4">I BUILD CALM SYSTEMS FOR</text>
    <text x="52" y="170" fill="url(#headline-grad)" font-size="40" font-weight="800" letter-spacing="0.4">MESSY REAL-WORLD WORK.</text>
    <text x="54" y="215" fill="#B6CFC5" font-size="17" letter-spacing="0.5">{positioning}</text>
    <text x="54" y="248" fill="#708E83" font-size="14">{promise}</text>

    <g transform="translate(52 277)">
      <rect width="172" height="34" rx="17" fill="#102B25" stroke="#2D5A4E" />
      <circle cx="19" cy="17" r="5" fill="#22C55E" filter="url(#glow)" />
      <text x="34" y="22" fill="#D9FFF0" font-size="11" font-weight="700" letter-spacing="1">06 LIVE SYSTEMS</text>
      <rect x="184" width="248" height="34" rx="17" fill="#0D2025" stroke="#24495B" />
      <text x="308" y="22" text-anchor="middle" fill="#BCEBFF" font-size="11" font-weight="700" letter-spacing="1">BUILT + OPERATED END TO END</text>
    </g>
  </g>

  <g font-family="Verdana,Geneva,DejaVu Sans,sans-serif">
    <circle class="orbit" cx="936" cy="174" r="121" fill="none" stroke="#8CCAAF" stroke-opacity="0.28" stroke-dasharray="4 11" />
    <circle cx="936" cy="174" r="76" fill="#07120F" stroke="#376A5B" />
    <circle cx="936" cy="174" r="60" fill="#102B25" stroke="#8CCAAF" stroke-opacity="0.5" />
    <text x="936" y="165" text-anchor="middle" fill="#F1FFF9" font-size="14" font-weight="800" letter-spacing="1.4">FORWARD</text>
    <text x="936" y="185" text-anchor="middle" fill="#8CCAAF" font-size="12" font-weight="700" letter-spacing="2">LAB</text>

    <g fill="none" stroke="#407567" stroke-width="1.4" class="route">
      <path d="M936 98C875 74 827 72 785 92" />
      <path d="M1008 133C1057 105 1093 101 1136 115" />
      <path d="M1010 215C1064 243 1095 252 1139 245" />
      <path d="M934 250C884 282 837 290 789 272" />
      <path d="M868 207C824 218 786 212 745 190" />
      <path d="M871 136C835 119 809 117 775 126" />
    </g>

    <g font-size="10" font-weight="700" letter-spacing="1.2">
      <g class="pulse"><circle cx="785" cy="92" r="12" fill="#38BDF8" fill-opacity="0.2" stroke="#38BDF8"/><circle cx="785" cy="92" r="4" fill="#38BDF8"/></g>
      <text x="766" y="70" text-anchor="middle" fill="#8AB9C8">MONEY</text>
      <g class="pulse pulse-b"><circle cx="1136" cy="115" r="12" fill="#2DD4BF" fill-opacity="0.2" stroke="#2DD4BF"/><circle cx="1136" cy="115" r="4" fill="#2DD4BF"/></g>
      <text x="1123" y="92" text-anchor="middle" fill="#8AC8BD">MOVEMENT</text>
      <g class="pulse pulse-c"><circle cx="1139" cy="245" r="12" fill="#A78BFA" fill-opacity="0.2" stroke="#A78BFA"/><circle cx="1139" cy="245" r="4" fill="#A78BFA"/></g>
      <text x="1116" y="274" text-anchor="middle" fill="#B5A8D8">IDENTITY</text>
      <g class="pulse pulse-b"><circle cx="789" cy="272" r="12" fill="#F5B942" fill-opacity="0.2" stroke="#F5B942"/><circle cx="789" cy="272" r="4" fill="#F5B942"/></g>
      <text x="789" y="302" text-anchor="middle" fill="#CBB789">LOGISTICS</text>
      <g class="pulse pulse-c"><circle cx="745" cy="190" r="10" fill="#FB923C" fill-opacity="0.2" stroke="#FB923C"/><circle cx="745" cy="190" r="3.5" fill="#FB923C"/></g>
      <text x="736" y="216" text-anchor="middle" fill="#CBA28A">COMMUNITY</text>
      <g class="pulse"><circle cx="775" cy="126" r="10" fill="#60A5FA" fill-opacity="0.2" stroke="#60A5FA"/><circle cx="775" cy="126" r="3.5" fill="#60A5FA"/></g>
      <text x="758" y="109" text-anchor="middle" fill="#91AEC8">MEDIA</text>
    </g>
  </g>
  <rect class="cursor" x="496" y="286" width="8" height="16" rx="1" fill="#8CCAAF" opacity="0.85" />
</svg>
"""


def build_footer(brand: dict[str, Any]) -> str:
    name = html.escape(str(brand["name"]).upper())
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="126" viewBox="0 0 1200 126" role="img" aria-label="Keep moving forward">
  <defs>
    <linearGradient id="footer-line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#07110F" />
      <stop offset="0.5" stop-color="#8CCAAF" />
      <stop offset="1" stop-color="#38BDF8" />
    </linearGradient>
  </defs>
  <style>
    .dash {{ stroke-dasharray: 12 18; animation: move 12s linear infinite; }}
    @keyframes move {{ to {{ stroke-dashoffset: -300; }} }}
    @media (prefers-reduced-motion: reduce) {{ .dash {{ animation: none; }} }}
  </style>
  <rect width="1200" height="126" rx="14" fill="#07110F" />
  <path class="dash" d="M45 34H1155" stroke="url(#footer-line)" stroke-width="2" />
  <text x="600" y="76" text-anchor="middle" fill="#D9FFF0" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="18" font-weight="700" letter-spacing="3">MAKE IT USEFUL · SHIP IT · KEEP MOVING FORWARD</text>
  <text x="600" y="101" text-anchor="middle" fill="#58786E" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="10" letter-spacing="2">{name} // THE FORWARD LAB</text>
</svg>
"""


def main() -> None:
    profile = load_profile()
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(build_svg(profile["brand"]), encoding="utf-8")
    FOOTER_FILE.write_text(build_footer(profile["brand"]), encoding="utf-8")


if __name__ == "__main__":
    main()
