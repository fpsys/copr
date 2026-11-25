#!/usr/bin/env python3
"""Update kiri.spec from the latest stable Kiri GitHub release."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

REPOSITORY = "SeniorMatt/kiri"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
SPEC = Path("kiri.spec")


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "kiri-copr-release-check"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "kiri-copr-release-check"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def replace_once(pattern: str, replacement: str, content: str, description: str) -> str:
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Could not update {description}: expected exactly one match")
    return updated


def main() -> int:
    release = fetch_json(API_URL)
    tag = release.get("tag_name", "")
    version = tag.removeprefix("v")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
        raise RuntimeError(f"Unsupported release tag: {tag!r}")

    content = SPEC.read_text(encoding="utf-8")
    current_match = re.search(r"^Version:\s*(\S+)\s*$", content, re.MULTILINE)
    if not current_match:
        raise RuntimeError("Version field not found in kiri.spec")
    current_version = current_match.group(1)
    if version == current_version:
        print(f"Kiri is already up to date ({version}).")
        return 0

    assets = [asset for asset in release.get("assets", []) if asset.get("name", "").endswith(".tar.gz")]
    if len(assets) != 1:
        names = [asset.get("name") for asset in assets]
        raise RuntimeError(f"Expected exactly one .tar.gz release asset; found {names!r}")

    asset = assets[0]
    archive_url = asset.get("browser_download_url")
    if not archive_url:
        raise RuntimeError("Release archive has no browser_download_url")
    archive = download(archive_url)
    digest = hashlib.sha256(archive).hexdigest()

    # Validate the archive before changing packaging metadata. Kiri's RPM build
    # requires both the KWin script payload and the native CMake project.
    import io

    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        members = tar.getmembers()
        roots = {member.name.split("/", 1)[0] for member in members if member.name}
        if len(roots) != 1:
            raise RuntimeError(f"Expected one top-level archive directory; found {sorted(roots)!r}")
        root = next(iter(roots))
        required = {f"{root}/effect-cpp/CMakeLists.txt", f"{root}/package/metadata.json", f"{root}/kiri-mode"}
        present = {member.name for member in members}
        missing = required - present
        if missing:
            raise RuntimeError(f"Release archive is missing required Kiri files: {sorted(missing)!r}")

    content = replace_once(r"^Version:\s*\S+[ \t]*$", f"Version:        {version}", content, "Version")
    content = replace_once(r"^Source0:\s*\S+[ \t]*$", f"Source0:        {archive_url}", content, "Source0")
    content = replace_once(
        r"^echo '[0-9a-f]{64}  %\{SOURCE0\}' \| sha256sum --check --status$",
        f"echo '{digest}  %{{SOURCE0}}' | sha256sum --check --status",
        content,
        "Source0 checksum",
    )
    content = replace_once(
        r"^%autosetup -n \S+[ \t]*$", f"%autosetup -n {root}", content, "autosetup directory"
    )

    SPEC.write_text(content, encoding="utf-8")
    print(f"Updated Kiri spec: {current_version} -> {version}")
    print(f"Release asset: {asset['name']}")
    print(f"SHA-256: {digest}")
    print(f"Archive root: {root}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # fail closed; never commit an unverified spec update
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
