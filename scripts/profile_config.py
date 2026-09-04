#!/usr/bin/env python3
"""Load and validate the profile's curated content manifest."""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path
from typing import Any

import yaml


PROFILE_FILE = Path("profile.yml")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
VALID_TIERS = {"flagship", "lab"}


def _required_text(item: dict[str, Any], key: str, context: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string.")
    return value.strip()


def _https_host(url: str, context: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{context} must be an HTTPS URL without embedded credentials.")
    return parsed.hostname.lower().rstrip(".")


def validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    if profile.get("version") != 1:
        raise ValueError("profile.yml version must be 1.")

    brand = profile.get("brand")
    if not isinstance(brand, dict):
        raise ValueError("profile.yml must define a brand mapping.")
    for key in ("name", "eyebrow", "headline", "positioning", "promise"):
        _required_text(brand, key, "brand")
    _https_host(_required_text(brand, "website", "brand"), "brand.website")
    _https_host(_required_text(brand, "github", "brand"), "brand.github")

    now = profile.get("now")
    if not isinstance(now, dict):
        raise ValueError("profile.yml must define a now mapping.")
    for key in ("label", "focus", "signal"):
        _required_text(now, key, "now")

    projects = profile.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ValueError("profile.yml must define at least one project.")

    repos: set[str] = set()
    for index, project in enumerate(projects):
        context = f"projects[{index}]"
        if not isinstance(project, dict):
            raise ValueError(f"{context} must be a mapping.")
        for key in ("repo", "name", "domain", "summary", "outcome"):
            _required_text(project, key, context)
        repo = str(project["repo"])
        if repo.lower() in repos:
            raise ValueError(f"Duplicate project repo: {repo}")
        repos.add(repo.lower())

        tier = _required_text(project, "tier", context)
        if tier not in VALID_TIERS:
            raise ValueError(f"{context}.tier must be one of {sorted(VALID_TIERS)}.")

        public_url = _required_text(project, "public_url", context)
        public_host = _https_host(public_url, f"{context}.public_url")
        hosts = project.get("homepage_hosts")
        if not isinstance(hosts, list) or not all(isinstance(host, str) for host in hosts):
            raise ValueError(f"{context}.homepage_hosts must be a list of hostnames.")
        normalized_hosts = {host.lower().rstrip(".") for host in hosts}
        if public_host not in normalized_hosts:
            raise ValueError(f"{context}.public_url host must be listed in homepage_hosts.")

        capabilities = project.get("capabilities")
        if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 4:
            raise ValueError(f"{context}.capabilities must contain one to four items.")
        if not all(isinstance(capability, str) and capability.strip() for capability in capabilities):
            raise ValueError(f"{context}.capabilities must contain non-empty strings.")

        accent = _required_text(project, "accent", context)
        if not HEX_COLOR.fullmatch(accent):
            raise ValueError(f"{context}.accent must be a six-digit hexadecimal color.")

    stack = profile.get("stack")
    if not isinstance(stack, list) or not stack:
        raise ValueError("profile.yml must define stack groups.")

    principles = profile.get("principles")
    if not isinstance(principles, list) or len(principles) != 3:
        raise ValueError("profile.yml must define exactly three principles.")
    for index, principle in enumerate(principles):
        if not isinstance(principle, dict):
            raise ValueError(f"principles[{index}] must be a mapping.")
        _required_text(principle, "title", f"principles[{index}]")
        _required_text(principle, "body", f"principles[{index}]")

    return profile


def load_profile(path: Path = PROFILE_FILE) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("profile.yml must contain a mapping at its root.")
    return validate_profile(data)
