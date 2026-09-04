#!/usr/bin/env python3
"""Generate the manifest-driven narrative sections of the profile README."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

if __package__:
    from .profile_config import load_profile
else:
    from profile_config import load_profile


GITHUB_USER = os.getenv("GITHUB_USER", "agillhock7")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
README_FILE = Path("README.md")
LINKS_DIR = Path("assets/links")

PROFILE = load_profile()
FEATURED_PROJECTS = PROFILE["projects"]

NOW_START = "<!-- NOW:START -->"
NOW_END = "<!-- NOW:END -->"
FLAGSHIP_START = "<!-- FLAGSHIPS:START -->"
FLAGSHIP_END = "<!-- FLAGSHIPS:END -->"
LAB_START = "<!-- LAB:START -->"
LAB_END = "<!-- LAB:END -->"
STACK_START = "<!-- STACK:START -->"
STACK_END = "<!-- STACK:END -->"
PRINCIPLES_START = "<!-- PRINCIPLES:START -->"
PRINCIPLES_END = "<!-- PRINCIPLES:END -->"

STACK_LABELS = {
    "vue": "Vue",
    "vite": "Vite",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "lua": "Lua",
    "php": "PHP",
    "wordpress": "WordPress",
    "apache": "Apache",
    "cpanel": "cPanel",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "phpmyadmin": "phpMyAdmin",
    "phppgadmin": "phpPgAdmin",
    "linux": "Linux",
    "ubuntu": "Ubuntu",
    "ssl-tls": "SSL/TLS",
    "git": "Git",
    "docker": "Docker",
    "vscode": "VS Code",
    "roblox-studio": "Roblox Studio",
    "hosting": "Hosting",
    "domains": "Domains",
    "codex": "Codex",
}


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def api_get(url: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "forward-lab-profile-generator",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


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
        repo = str(project["repo"])
        allowed_hosts = configured_homepage_hosts(project)
        public_url = normalize_homepage(str(project.get("public_url", "")))
        if public_url and not homepage_is_allowed(public_url, allowed_hosts):
            raise ValueError(f"Configured public_url for {repo} is not in homepage_hosts.")

        data: dict[str, Any] = {}
        source_url = ""
        try:
            response = api_get(f"https://api.github.com/repos/{GITHUB_USER}/{repo}")
            if isinstance(response, dict):
                data = response
                if not response.get("private"):
                    source_url = str(response.get("html_url", ""))
        except urllib.error.HTTPError as err:
            print(
                f"[profile] Repo metadata unavailable for {GITHUB_USER}/{repo} (HTTP {err.code}); using manifest.",
                file=sys.stderr,
            )
        except urllib.error.URLError as err:
            print(
                f"[profile] Repo metadata unavailable for {GITHUB_USER}/{repo} ({err.reason}); using manifest.",
                file=sys.stderr,
            )

        remote_homepage = normalize_homepage(str(data.get("homepage", "")))
        if remote_homepage and not homepage_is_allowed(remote_homepage, allowed_hosts):
            print(
                f"[profile] Ignoring unexpected homepage for {GITHUB_USER}/{repo}: {remote_homepage}",
                file=sys.stderr,
            )
            remote_homepage = ""
        homepage = public_url or remote_homepage
        repo_url = homepage or source_url or f"https://github.com/{GITHUB_USER}/{repo}"

        items.append(
            {
                **project,
                "repo_url": repo_url,
                "source_url": source_url,
                "homepage": homepage,
                "slug": slugify(repo),
                "pushed_at": str(data.get("pushed_at", "")),
            }
        )
    return items


def build_badge_svg(label: str, gradient_id: str, accent: str = "#8CCAAF") -> str:
    safe_label = html.escape(label.upper())
    width = max(118, int(len(label) * 8.2) + 34)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="32" role="img" aria-label="{safe_label}">
  <title>{safe_label}</title>
  <defs>
    <linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#0B1916" />
      <stop offset="1" stop-color="{accent}" stop-opacity="0.38" />
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{width - 1}" height="31" rx="8" fill="url(#{gradient_id})" stroke="{accent}" stroke-opacity="0.7" />
  <circle cx="17" cy="16" r="4" fill="{accent}" />
  <text x="{(width + 17) / 2:.1f}" y="20.5" fill="#F1FFF9" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="10" font-weight="700" letter-spacing="0.8">{safe_label}</text>
</svg>
"""


def write_badge(path: Path, label: str, accent: str = "#8CCAAF") -> None:
    path.write_text(
        build_badge_svg(label, f"grad-{slugify(path.stem)}", accent), encoding="utf-8"
    )


def replace_block(readme: str, start: str, end: str, content: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(readme):
        raise ValueError(f"README block markers are missing: {start} / {end}")
    return pattern.sub(f"{start}\n{content}\n{end}", readme)


def build_now(profile: dict[str, Any], projects: list[dict[str, Any]]) -> str:
    current = profile["now"]
    latest = max(projects, key=lambda project: project.get("pushed_at", ""), default=None)
    latest_text = "SYSTEMS ONLINE"
    if latest and latest.get("pushed_at"):
        latest_text = f"LATEST SIGNAL // {latest['name']}"
    return f"""<table>
  <tr>
    <td width="72%"><strong>🟢 {html.escape(str(current['label']))}</strong><br/><sub>{html.escape(str(current['focus']))}</sub></td>
    <td width="28%" align="right"><code>{html.escape(latest_text)}</code></td>
  </tr>
</table>

<p align="center"><sub>{html.escape(str(current['signal']))}</sub></p>"""


def _action_links(project: dict[str, Any]) -> str:
    links: list[str] = []
    slug = project["slug"]
    if project.get("homepage"):
        links.append(
            f'<a href="{html.escape(str(project["homepage"]), quote=True)}"><img src="assets/links/live-{slug}.svg" alt="Open {html.escape(str(project["name"]))}" /></a>'
        )
    if project.get("source_url"):
        links.append(
            f'<a href="{html.escape(str(project["source_url"]), quote=True)}"><img src="assets/links/source-{slug}.svg" alt="View {html.escape(str(project["name"]))} source" /></a>'
        )
    return " ".join(links)


def build_flagships(projects: list[dict[str, Any]]) -> str:
    rows = ["<table>", "  <tbody>"]
    for project in (item for item in projects if item["tier"] == "flagship"):
        capabilities = " · ".join(
            f"<code>{html.escape(str(item))}</code>" for item in project["capabilities"]
        )
        rows.extend(
            [
                "  <tr>",
                '    <td width="54%">',
                f'      <a href="{html.escape(str(project["repo_url"]), quote=True)}"><img src="assets/previews/{project["slug"]}.png" alt="{html.escape(str(project["name"]))} production preview" width="100%" /></a>',
                "    </td>",
                '    <td width="46%" valign="top">',
                f'      <sub><strong>{html.escape(str(project["domain"]))} // FLAGSHIP SYSTEM</strong></sub>',
                f'      <h3>{html.escape(str(project["name"]))}</h3>',
                f'      <p><strong>{html.escape(str(project["summary"]))}</strong></p>',
                f'      <p><sub>{html.escape(str(project["outcome"]))}</sub></p>',
                f"      <p>{capabilities}</p>",
                f"      <p>{_action_links(project)}</p>",
                "    </td>",
                "  </tr>",
            ]
        )
    rows.extend(["  </tbody>", "</table>"])
    return "\n".join(rows)


def build_lab(projects: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for project in (item for item in projects if item["tier"] == "lab"):
        cards.append(
            '    <td width="33%" align="center" valign="top">\n'
            f'      <a href="{html.escape(str(project["repo_url"]), quote=True)}"><img src="assets/previews/{project["slug"]}.png" alt="{html.escape(str(project["name"]))} production preview" width="100%" /></a><br/>\n'
            f'      <sub><strong>{html.escape(str(project["domain"]))}</strong></sub><br/>\n'
            f'      <strong>{html.escape(str(project["name"]))}</strong><br/>\n'
            f'      <sub>{html.escape(str(project["summary"]))}</sub><br/><br/>\n'
            f"      {_action_links(project)}\n"
            "    </td>"
        )
    return "<table>\n  <tr>\n" + "\n".join(cards) + "\n  </tr>\n</table>"


def build_stack(groups: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for group in groups:
        badges = "\n  ".join(
            f'<img src="assets/stack/{slug}.svg" alt="{html.escape(STACK_LABELS.get(str(slug), str(slug)))}" />'
            for slug in group["items"]
        )
        sections.append(
            f'<p align="center"><sub><strong>{html.escape(str(group["name"]))}</strong></sub><br/>\n  {badges}\n</p>'
        )
    return "\n\n".join(sections)


def build_principles(principles: list[dict[str, Any]]) -> str:
    cells = []
    for principle in principles:
        cells.append(
            '    <td width="33%" align="center" valign="top">'
            f'<strong>{html.escape(str(principle["title"]))}</strong><br/>'
            f'<sub>{html.escape(str(principle["body"]))}</sub></td>'
        )
    return "<table>\n  <tr>\n" + "\n".join(cells) + "\n  </tr>\n</table>"


def write_link_badges(profile: dict[str, Any], projects: list[dict[str, Any]]) -> None:
    LINKS_DIR.mkdir(parents=True, exist_ok=True)
    write_badge(LINKS_DIR / "cta-portfolio.svg", "ENTER THE FORWARD LAB", "#8CCAAF")
    write_badge(LINKS_DIR / "cta-github.svg", "EXPLORE THE CODE", "#38BDF8")
    for project in projects:
        accent = str(project["accent"])
        write_badge(LINKS_DIR / f'live-{project["slug"]}.svg', "OPEN LIVE SYSTEM", accent)
        if project.get("source_url"):
            write_badge(LINKS_DIR / f'source-{project["slug"]}.svg', "VIEW SOURCE", accent)


def main() -> None:
    profile = load_profile()
    projects = build_project_data()
    write_link_badges(profile, projects)

    readme = README_FILE.read_text(encoding="utf-8")
    updated = replace_block(readme, NOW_START, NOW_END, build_now(profile, projects))
    updated = replace_block(
        updated, FLAGSHIP_START, FLAGSHIP_END, build_flagships(projects)
    )
    updated = replace_block(updated, LAB_START, LAB_END, build_lab(projects))
    updated = replace_block(updated, STACK_START, STACK_END, build_stack(profile["stack"]))
    updated = replace_block(
        updated,
        PRINCIPLES_START,
        PRINCIPLES_END,
        build_principles(profile["principles"]),
    )
    README_FILE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
