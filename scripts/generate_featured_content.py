#!/usr/bin/env python3
"""Generate featured project links, live previews, and snapshot link badges."""

from __future__ import annotations

import json
import os
import re
import struct
import sys
from io import BytesIO
from pathlib import Path
from typing import Any
import urllib.parse
import urllib.error
import urllib.request
import zlib

try:
    from PIL import Image, ImageChops, ImageDraw, ImageStat
except ModuleNotFoundError:
    Image = None
    ImageChops = None
    ImageDraw = None
    ImageStat = None


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
README_FILE = Path("README.md")
LINKS_DIR = Path("assets/links")
PREVIEWS_DIR = Path("assets/previews")

PREVIEW_WIDTH = 1200
PREVIEW_HEIGHT = 720
THUM_WAIT_PRIMARY = 12000
THUM_WAIT_SECONDARY = 18000
MIN_PREVIEW_BYTES = 12000
MAX_WHITE_RATIO = 0.86
MIN_PIXEL_STDDEV = 9.0
PREVIEW_CORNER_RADIUS = 24
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

FEATURED_PROJECTS = [
    {
        "repo": "OnLedge",
        "summary": "Snap receipts, stay organized, and see where your money goes.",
        "homepage_hosts": ["onledge.gops.app"],
    },
    {
        "repo": "EveryMile",
        "summary": "Track movement, true operating cost, and deduction value in one defensible stream.",
        "public_url": "https://em.gops.app",
        "homepage_hosts": ["em.gops.app"],
    },
    {
        "repo": "MySite",
        "summary": "A beginning look at personalized UI with AI.",
        "homepage_hosts": ["my.alexanderjgill.com"],
    },
    {
        "repo": "Slapshot-Snapshot",
        "summary": "Team photos and videos.",
        "homepage_hosts": ["snap.pucc.us"],
    },
    {
        "repo": "parcel-tracker",
        "summary": "Secure shipment tracking across desktop and mobile.",
        "homepage_hosts": ["tb4.alexander.quest"],
    },
    {
        "repo": "feedabum",
        "summary": "Hyperlocal micro-giving for verified neighbors; scan, verify, and donate in under a minute.",
        "homepage_hosts": ["fab.gops.app"],
    },
]

SNAPSHOT_LINKS = [
    ("snapshot-stats", "Stats Card", "assets/github-stats.svg"),
    ("snapshot-langs", "Top Languages", "assets/top-langs.svg"),
    ("snapshot-streak", "Streak", "assets/streak.svg"),
    ("snapshot-activity", "Activity Graph", "assets/activity-graph.svg"),
]

FEATURED_START = "<!-- FEATURED_TABLE:START -->"
FEATURED_END = "<!-- FEATURED_TABLE:END -->"
PREVIEWS_START = "<!-- LIVE_PREVIEWS:START -->"
PREVIEWS_END = "<!-- LIVE_PREVIEWS:END -->"
SNAPSHOT_START = "<!-- SNAPSHOT_LINKS:START -->"
SNAPSHOT_END = "<!-- SNAPSHOT_LINKS:END -->"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def api_get(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "custom-profile-featured-generator",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def http_get_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "custom-profile-featured-generator",
            "Accept": "image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def preview_candidates(homepage: str) -> list[str]:
    encoded_relaxed = urllib.parse.quote(homepage, safe=":/?&=%#")
    encoded_strict = urllib.parse.quote(homepage, safe="")
    return [
        (
            "https://image.thum.io/get/"
            f"width/{PREVIEW_WIDTH}/crop/{PREVIEW_HEIGHT}/wait/{THUM_WAIT_PRIMARY}/noanimate/{encoded_relaxed}"
        ),
        (
            "https://image.thum.io/get/"
            f"width/{PREVIEW_WIDTH}/crop/{PREVIEW_HEIGHT}/wait/{THUM_WAIT_SECONDARY}/noanimate/{encoded_relaxed}"
        ),
        f"https://s.wordpress.com/mshots/v1/{encoded_strict}?w={PREVIEW_WIDTH}",
    ]


def default_preview_url(homepage: str) -> str:
    return preview_candidates(homepage)[0]


def is_washed_preview(image_bytes: bytes) -> bool:
    if len(image_bytes) < MIN_PREVIEW_BYTES:
        return True

    if Image is None or ImageStat is None:
        return False

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            sample = image.convert("RGB")
            sample.thumbnail((220, 132))
            grayscale = sample.convert("L")
            histogram = grayscale.histogram()
            total_pixels = sum(histogram)
            if not total_pixels:
                return True

            white_pixels = sum(histogram[243:])
            white_ratio = white_pixels / total_pixels
            pixel_stddev = ImageStat.Stat(grayscale).stddev[0]

            return white_ratio > MAX_WHITE_RATIO or pixel_stddev < MIN_PIXEL_STDDEV
    except Exception:
        return False


def png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(data, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


def paeth_predictor(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    distance_left = abs(estimate - left)
    distance_up = abs(estimate - up)
    distance_up_left = abs(estimate - up_left)
    if distance_left <= distance_up and distance_left <= distance_up_left:
        return left
    if distance_up <= distance_up_left:
        return up
    return up_left


def unfilter_png_rows(raw: bytes, width: int, height: int, bytes_per_pixel: int) -> list[bytearray]:
    row_size = width * bytes_per_pixel
    rows: list[bytearray] = []
    previous = bytearray(row_size)
    cursor = 0

    for _ in range(height):
        if cursor + 1 + row_size > len(raw):
            raise ValueError("PNG data ended before all rows were decoded.")

        filter_type = raw[cursor]
        cursor += 1
        filtered = raw[cursor : cursor + row_size]
        cursor += row_size
        row = bytearray(row_size)

        for i, value in enumerate(filtered):
            left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
            up = previous[i]
            up_left = previous[i - bytes_per_pixel] if i >= bytes_per_pixel else 0

            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                predictor = paeth_predictor(left, up, up_left)
            else:
                raise ValueError(f"Unsupported PNG filter type: {filter_type}")

            row[i] = (value + predictor) & 0xFF

        rows.append(row)
        previous = row

    return rows


def rgba_png_rows(rows: list[bytearray], width: int, color_type: int) -> list[bytearray]:
    if color_type == 6:
        return rows

    rgba_rows: list[bytearray] = []
    for row in rows:
        rgba = bytearray(width * 4)
        for x in range(width):
            source = x * 3
            target = x * 4
            rgba[target : target + 3] = row[source : source + 3]
            rgba[target + 3] = 255
        rgba_rows.append(rgba)
    return rgba_rows


def corner_alpha_coverage(x: int, y: int, width: int, height: int, radius: int) -> float:
    if not ((x < radius or x >= width - radius) and (y < radius or y >= height - radius)):
        return 1.0

    center_x = radius if x < radius else width - radius
    center_y = radius if y < radius else height - radius
    samples = 4
    inside = 0
    radius_squared = radius * radius

    for sample_y in range(samples):
        point_y = y + (sample_y + 0.5) / samples
        for sample_x in range(samples):
            point_x = x + (sample_x + 0.5) / samples
            if (point_x - center_x) ** 2 + (point_y - center_y) ** 2 <= radius_squared:
                inside += 1

    return inside / (samples * samples)


def apply_rounded_alpha(rows: list[bytearray], width: int, height: int, radius: int) -> None:
    radius = max(0, min(radius, width // 2, height // 2))
    if radius == 0:
        return

    for y, row in enumerate(rows):
        if radius <= y < height - radius:
            continue
        for x in range(width):
            coverage = corner_alpha_coverage(x, y, width, height, radius)
            if coverage < 1.0:
                alpha_index = (x * 4) + 3
                row[alpha_index] = round(row[alpha_index] * coverage)


def encode_rgba_png(width: int, height: int, rows: list[bytearray]) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    return (
        PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(raw, level=9))
        + png_chunk(b"IEND", b"")
    )


def round_png_corners(image_bytes: bytes, radius: int) -> bytes | None:
    if not image_bytes.startswith(PNG_SIGNATURE):
        return None

    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = 0
    compressed = bytearray()

    while offset + 8 <= len(image_bytes):
        length = struct.unpack(">I", image_bytes[offset : offset + 4])[0]
        kind = image_bytes[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        if data_end + 4 > len(image_bytes):
            return None

        data = image_bytes[data_start:data_end]
        offset = data_end + 4

        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", data
            )
            if compression != 0 or filter_method != 0:
                return None
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            break

    if bit_depth != 8 or color_type not in {2, 6} or interlace != 0 or not compressed:
        return None

    bytes_per_pixel = 4 if color_type == 6 else 3
    rows = unfilter_png_rows(zlib.decompress(bytes(compressed)), width, height, bytes_per_pixel)
    rgba_rows = rgba_png_rows(rows, width, color_type)
    apply_rounded_alpha(rgba_rows, width, height, radius)
    return encode_rgba_png(width, height, rgba_rows)


def round_preview_corners(image_bytes: bytes, radius: int = PREVIEW_CORNER_RADIUS) -> bytes:
    if radius <= 0:
        return image_bytes

    if Image is not None and ImageDraw is not None and ImageChops is not None:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                rounded = image.convert("RGBA")
                mask = Image.new("L", rounded.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle(
                    (0, 0, rounded.width - 1, rounded.height - 1),
                    radius=radius,
                    fill=255,
                )
                rounded.putalpha(ImageChops.multiply(rounded.getchannel("A"), mask))
                output = BytesIO()
                rounded.save(output, format="PNG", optimize=True)
                return output.getvalue()
        except Exception:
            pass

    try:
        rounded_png = round_png_corners(image_bytes, radius)
    except Exception:
        rounded_png = None
    return rounded_png if rounded_png is not None else image_bytes


def write_preview_image(destination: Path, image_bytes: bytes) -> None:
    destination.write_bytes(round_preview_corners(image_bytes))


def capture_preview(homepage: str, slug: str) -> str:
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    destination = PREVIEWS_DIR / f"{slug}.png"
    fallback_bytes: bytes | None = None

    for source_url in preview_candidates(homepage):
        try:
            image_bytes = http_get_bytes(source_url)
        except Exception:
            continue

        if len(image_bytes) >= MIN_PREVIEW_BYTES and (
            fallback_bytes is None or len(image_bytes) > len(fallback_bytes)
        ):
            fallback_bytes = image_bytes

        if is_washed_preview(image_bytes):
            continue

        write_preview_image(destination, image_bytes)
        return destination.as_posix()

    if fallback_bytes:
        write_preview_image(destination, fallback_bytes)
        return destination.as_posix()

    return default_preview_url(homepage)


def build_badge_svg(label: str, gradient_id: str) -> str:
    text = label.upper()
    width = max(128, int(len(text) * 8.4) + 32)
    height = 32
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="{label}">
  <title>{label}</title>
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1f4d42" />
      <stop offset="100%" stop-color="#8ccfaf" />
    </linearGradient>
    <linearGradient id="{gradient_id}-shine" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#d9fff0" stop-opacity="0.34" />
      <stop offset="100%" stop-color="#d9fff0" stop-opacity="0" />
    </linearGradient>
  </defs>
  <g>
    <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="7" fill="#0f1b19" stroke="#2f5b4f" />
    <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="6" fill="url(#{gradient_id})" />
    <rect x="1" y="1" width="{width - 2}" height="10" rx="6" fill="url(#{gradient_id}-shine)" />
  </g>
  <text
    x="{width / 2}"
    y="21"
    fill="#f1fff9"
    text-anchor="middle"
    font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
    font-size="11"
    font-weight="700"
    letter-spacing="0.8"
  >
    {text}
  </text>
</svg>
"""


def write_badge(path: Path, label: str) -> None:
    gradient_id = f"grad-{slugify(path.stem)}"
    path.write_text(build_badge_svg(label, gradient_id), encoding="utf-8")


def replace_block(readme: str, start: str, end: str, content: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    replacement = f"{start}\n{content}\n{end}"
    return pattern.sub(replacement, readme)


def normalize_homepage(homepage: str) -> str:
    value = homepage.strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://{value}"


def normalize_host(host: str) -> str:
    return host.strip().lower().rstrip(".")


def homepage_host(homepage: str) -> str:
    parsed = urllib.parse.urlparse(homepage)
    return normalize_host(parsed.hostname or "")


def configured_homepage_hosts(project: dict[str, Any]) -> set[str]:
    hosts = project.get("homepage_hosts", [])
    if isinstance(hosts, str):
        hosts = [hosts]
    return {normalize_host(str(host)) for host in hosts if normalize_host(str(host))}


def homepage_is_allowed(homepage: str, allowed_hosts: set[str]) -> bool:
    return bool(homepage) and bool(allowed_hosts) and homepage_host(homepage) in allowed_hosts


def build_project_data() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for project in FEATURED_PROJECTS:
        repo = project["repo"]
        allowed_hosts = configured_homepage_hosts(project)
        public_url = normalize_homepage(str(project.get("public_url", "")))
        if public_url and not homepage_is_allowed(public_url, allowed_hosts):
            raise ValueError(f"Configured public_url for {repo} is not in homepage_hosts.")
        try:
            data = api_get(f"https://api.github.com/repos/{GITHUB_USER}/{repo}")
        except urllib.error.HTTPError as err:
            if err.code == 404:
                if public_url:
                    print(
                        f"[featured] Repo metadata unavailable for {GITHUB_USER}/{repo} (HTTP 404); using public URL.",
                        file=sys.stderr,
                    )
                    data = {}
                else:
                    print(
                        f"[featured] Skipping missing repo: {GITHUB_USER}/{repo} (HTTP 404)",
                        file=sys.stderr,
                    )
                    continue
            else:
                print(
                    f"[featured] Unable to fetch metadata for {GITHUB_USER}/{repo} (HTTP {err.code}); using defaults.",
                    file=sys.stderr,
                )
                data = {}
        except urllib.error.URLError as err:
            print(
                f"[featured] Unable to fetch metadata for {GITHUB_USER}/{repo} ({err.reason}); using defaults.",
                file=sys.stderr,
            )
            data = {}

        if not isinstance(data, dict):
            data = {}

        homepage = normalize_homepage(str(data.get("homepage", "")))
        repo_url = str(data.get("html_url", f"https://github.com/{GITHUB_USER}/{repo}"))
        if homepage and not homepage_is_allowed(homepage, allowed_hosts):
            print(
                f"[featured] Ignoring unexpected homepage for {GITHUB_USER}/{repo}: {homepage}",
                file=sys.stderr,
            )
            homepage = ""
        if public_url:
            homepage = public_url
            repo_url = public_url
        items.append(
            {
                "repo": repo,
                "summary": project["summary"],
                "repo_url": repo_url,
                "homepage": homepage,
                "slug": slugify(repo),
            }
        )
    return items


def build_featured_table(projects: list[dict[str, Any]]) -> str:
    lines = [
        "| Project | Summary |",
        "| --- | --- |",
    ]
    for project in projects:
        badge_src = f"assets/links/project-{project['slug']}.svg"
        link = f'<a href="{project["repo_url"]}"><img src="{badge_src}" alt="{project["repo"]}" /></a>'
        lines.append(f"| {link} | {project['summary']} |")
    return "\n".join(lines)


def build_snapshot_links() -> str:
    chips = []
    for key, label, url in SNAPSHOT_LINKS:
        chips.append(f'<a href="{url}"><img src="assets/links/{key}.svg" alt="{label}" /></a>')
    return '<p align="center">\n  ' + "\n  ".join(chips) + "\n</p>"


def build_live_previews(projects: list[dict[str, Any]]) -> str:
    live_projects = [p for p in projects if p["homepage"]]
    if not live_projects:
        return '<p align="center">Live production previews will appear here when project homepages are configured.</p>'

    cells: list[str] = []
    for project in live_projects:
        homepage = project["homepage"]
        screenshot_url = str(project.get("preview_src", default_preview_url(homepage)))
        live_badge = f'assets/links/live-{project["slug"]}.svg'
        cell = (
            '    <td align="center" width="33%">\n'
            f'      <a href="{homepage}"><img src="{screenshot_url}" alt="{project["repo"]} live preview" width="100%" /></a><br/>\n'
            f'      <a href="{homepage}"><img src="{live_badge}" alt="Visit {project["repo"]}" /></a>\n'
            "    </td>"
        )
        cells.append(cell)

    rows: list[str] = ["<table>", "  <tbody>"]
    for i in range(0, len(cells), 3):
        rows.append("  <tr>")
        for cell in cells[i : i + 3]:
            rows.append(cell)
        rows.append("  </tr>")
    rows.extend(["  </tbody>", "</table>"])
    return "\n".join(rows)


def main() -> None:
    LINKS_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    for existing_preview in PREVIEWS_DIR.glob("*.jpg"):
        existing_preview.unlink()
    for existing_preview in PREVIEWS_DIR.glob("*.png"):
        existing_preview.unlink()

    projects = build_project_data()

    for project in projects:
        write_badge(LINKS_DIR / f'project-{project["slug"]}.svg', project["repo"])
        write_badge(LINKS_DIR / f'live-{project["slug"]}.svg', f'Visit {project["repo"]}')
        if project["homepage"]:
            project["preview_src"] = capture_preview(project["homepage"], project["slug"])

    for key, label, _ in SNAPSHOT_LINKS:
        write_badge(LINKS_DIR / f"{key}.svg", label)

    readme = README_FILE.read_text(encoding="utf-8")
    updated = readme
    updated = replace_block(updated, FEATURED_START, FEATURED_END, build_featured_table(projects))
    updated = replace_block(updated, PREVIEWS_START, PREVIEWS_END, build_live_previews(projects))
    updated = replace_block(updated, SNAPSHOT_START, SNAPSHOT_END, build_snapshot_links())

    README_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
