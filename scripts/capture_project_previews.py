#!/usr/bin/env python3
"""Capture production previews directly with a headless browser."""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageStat

if __package__:
    from .profile_config import load_profile
else:
    from profile_config import load_profile


PREVIEWS_DIR = Path("assets/previews")
PREVIEW_WIDTH = 1200
PREVIEW_HEIGHT = 720
PREVIEW_CORNER_RADIUS = 24
MIN_PREVIEW_BYTES = 12_000
MAX_WHITE_RATIO = 0.86
MIN_PIXEL_STDDEV = 9.0


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def is_washed_preview(image_bytes: bytes) -> bool:
    if len(image_bytes) < MIN_PREVIEW_BYTES:
        return True
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            sample = image.convert("RGB")
            sample.thumbnail((220, 132))
            grayscale = sample.convert("L")
            histogram = grayscale.histogram()
            total_pixels = sum(histogram)
            if not total_pixels:
                return True
            white_ratio = sum(histogram[243:]) / total_pixels
            pixel_stddev = ImageStat.Stat(grayscale).stddev[0]
            return white_ratio > MAX_WHITE_RATIO or pixel_stddev < MIN_PIXEL_STDDEV
    except Exception:
        return True


def round_preview_corners(
    image_bytes: bytes, radius: int = PREVIEW_CORNER_RADIUS
) -> bytes:
    if radius <= 0:
        return image_bytes
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.convert("RGBA")
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            (0, 0, image.width - 1, image.height - 1), radius=radius, fill=255
        )
        image.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()


def capture_project(page: Any, project: dict[str, Any]) -> bool:
    name = str(project["name"])
    url = str(project["public_url"])
    destination = PREVIEWS_DIR / f'{slugify(str(project["repo"]))}.png'
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3_500)
        page.add_style_tag(
            content="*,*::before,*::after{animation:none!important;transition:none!important;}"
        )
        image_bytes = page.screenshot(type="png", full_page=False)
        if is_washed_preview(image_bytes):
            print(
                f"[previews] {name} produced an empty or washed-out image; keeping the previous preview.",
                file=sys.stderr,
            )
            return False
        destination.write_bytes(round_preview_corners(image_bytes))
        print(f"[previews] refreshed {name}: {url}")
        return True
    except Exception as err:
        print(
            f"[previews] unable to refresh {name}; keeping the previous preview: {err}",
            file=sys.stderr,
        )
        return False


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as err:
        raise SystemExit(
            "Playwright is required. Install it and run `python3 -m playwright install chromium`."
        ) from err

    profile = load_profile()
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    refreshed = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": PREVIEW_WIDTH, "height": PREVIEW_HEIGHT},
            device_scale_factor=1,
            color_scheme="dark",
            reduced_motion="reduce",
        )
        page.set_extra_http_headers(
            {"Accept-Language": "en-US,en;q=0.9", "DNT": "1"}
        )
        for project in profile["projects"]:
            refreshed += int(capture_project(page, project))
        browser.close()

    print(f"[previews] refreshed {refreshed}/{len(profile['projects'])} previews")


if __name__ == "__main__":
    main()
