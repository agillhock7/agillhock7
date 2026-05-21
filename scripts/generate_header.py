#!/usr/bin/env python3
"""Generate a custom profile header SVG."""

from __future__ import annotations

import os
from pathlib import Path


OUTFILE = Path("assets/header.svg")
HEADER_HEIGHT = int(os.getenv("HEADER_HEIGHT", "240"))


def build_svg(name: str, slogan: str) -> str:
    width = 1200
    height = max(180, HEADER_HEIGHT)
    h = height
    name_y = int(h * 0.52)
    slogan_y = int(h * 0.72)

    base_0 = f"M0 0 H1200 V{h-72} Q900 {h-37} 600 {h-54} T0 {h-46} V0 Z"
    base_1 = f"M0 0 H1200 V{h-64} Q900 {h-52} 600 {h-64} T0 {h-54} V0 Z"
    base_2 = f"M0 0 H1200 V{h-82} Q900 {h-42} 600 {h-46} T0 {h-38} V0 Z"

    wave1_0 = f"M0 0 L0 {h-110} Q300 {h-68} 600 {h-95} T1200 {h-75} L1200 0 Z"
    wave1_1 = f"M0 0 L0 {h-75} Q300 {h-68} 600 {h-85} T1200 {h-100} L1200 0 Z"
    wave1_2 = f"M0 0 L0 {h-55} Q300 {h-103} 600 {h-55} T1200 {h-100} L1200 0 Z"

    wave2_0 = f"M0 0 L0 {h-95} Q300 {h-42} 600 {h-70} T1200 {h-58} L1200 0 Z"
    wave2_1 = f"M0 0 L0 {h-72} Q300 {h-113} 600 {h-113} T1200 {h-86} L1200 0 Z"
    wave2_2 = f"M0 0 L0 {h-80} Q300 {h-107} 600 {h-70} T1200 {h-51} L1200 0 Z"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="Alexander Gill header">
  <title>Alexander Gill - Moving Forward</title>
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#171F1F" />
      <stop offset="100%" stop-color="#8CCAAF" />
    </linearGradient>
    <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="5" stdDeviation="4" flood-color="#120f1f" flood-opacity="0.5"/>
    </filter>
  </defs>

  <path d="{base_0}" fill="url(#bgGrad)" >
    <animate
      attributeName="d"
      dur="20s"
      repeatCount="indefinite"
      keyTimes="0;0.333;0.667;1"
      calcMode="spline"
      keySplines="0.2 0 0.2 1;0.2 0 0.2 1;0.2 0 0.2 1"
      begin="-5s"
      values="{base_0};{base_1};{base_2};{base_0}">
    </animate>
  </path>
  <path d="{wave1_0}" fill="#8CCAAF" opacity="0.18" >
    <animate
      attributeName="d"
      dur="20s"
      repeatCount="indefinite"
      keyTimes="0;0.333;0.667;1"
      calcMode="spline"
      keySplines="0.2 0 0.2 1;0.2 0 0.2 1;0.2 0 0.2 1"
      begin="-10s"
      values="{wave1_0};{wave1_1};{wave1_2};{wave1_0}">
    </animate>
  </path>
  <path d="{wave2_0}" fill="#171F1F" opacity="0.22" >
      <animate
        attributeName="d"
        dur="20s"
        repeatCount="indefinite"
        keyTimes="0;0.333;0.667;1"
        calcMode="spline"
        keySplines="0.2 0 0.2 1;0.2 0 0.2 1;0.2 0 0.2 1"
        begin="0s"
        values="{wave2_0};{wave2_1};{wave2_2};{wave2_0}">
      </animate>
    </path>

  <g filter="url(#softGlow)">
    <text x="60" y="{name_y}" fill="#8ecfb3" font-size="88" font-weight="800" font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{name}</text>
    <text x="60" y="{slogan_y}" fill="#8ecfb3" opacity="0.95" font-size="47" font-weight="700" font-family="Verdana,Geneva,DejaVu Sans,sans-serif">{slogan}</text>
  </g>
</svg>
"""


def main() -> None:
    svg = build_svg("Alexander Gill", "Moving Forward")
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
