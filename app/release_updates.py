"""User-initiated release discovery shared by the Skrivi applications."""

from __future__ import annotations

import json
import re
import urllib.request


def version_key(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Unsupported release version")
    return tuple(int(part) for part in match.groups())


def select_release(
    releases: list[dict], current: str, *, test_releases: bool
) -> dict | None:
    installed = version_key(current)
    candidates = []
    for release in releases:
        if release.get("draft") or (release.get("prerelease") and not test_releases):
            continue
        try:
            version = version_key(release.get("tag_name", ""))
        except (ValueError, TypeError):
            continue
        if version > installed:
            candidates.append((version, release))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def check_release(
    repository: str, current: str, *, test_releases: bool = True
) -> str | None:
    if repository not in ("Skrivi-STT", "Skrivi-TTS"):
        raise ValueError("Unknown Skrivi repository")
    request = urllib.request.Request(
        f"https://api.github.com/repos/workavoidance/{repository}/releases?per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Skrivi"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        releases = json.loads(response.read(2 * 1024 * 1024))
    if not isinstance(releases, list):
        raise ValueError("Unexpected release response")
    result = select_release(releases, current, test_releases=test_releases)
    return result["tag_name"].removeprefix("v") if result else None
