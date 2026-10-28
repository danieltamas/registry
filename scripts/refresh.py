#!/usr/bin/env python3
"""Writes each app's latest GitHub release into apps.json. Run by .github/workflows/refresh.yml.

Only the `latest` fields and `updated` change; everything else is the hand-edited registry. A release is the
truth for a version: this reads GitHub's `releases/latest` (drafts and prereleases never count) and nothing else.

A failed read keeps the app's previous `latest`: writing null would claim "no release yet", which is a different
answer. The script still exits 2 so the workflow run turns red and someone looks. A 404 is "no release" only when
the repository itself still answers: GitHub also says 404 for a repository made private, renamed or deleted.

Usage: python3 scripts/refresh.py. GITHUB_TOKEN, when set, raises the API limit.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "apps.json"
TAG = re.compile(r"v?([0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9})")
ISO_Z = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


class ReadFailed(Exception):
    pass


class NotFound(Exception):
    pass


def github(path):
    request = urllib.request.Request(f"https://api.github.com/{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "danieltamas-registry"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise NotFound(path) from error
        raise ReadFailed(f"GitHub answered {error.code} for {path}") from error
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise ReadFailed(f"could not read {path} ({error})") from error
    if not isinstance(body, dict):
        raise ReadFailed(f"{path} did not answer an object")
    return body


def latest_release(repo):
    """The release as the registry stores it, None when the repository has none, ReadFailed otherwise."""
    try:
        body = github(f"repos/{repo}/releases/latest")
    except NotFound:
        try:
            github(f"repos/{repo}")
        except NotFound as error:
            raise ReadFailed("the repository does not answer (private, renamed or deleted?)") from error
        return None
    tag = body.get("tag_name")
    match = TAG.fullmatch(tag) if isinstance(tag, str) else None
    if not match:
        raise ReadFailed(f"the latest tag {tag!r} is not X.Y.Z")
    if body.get("draft") is not False or body.get("prerelease") is not False:
        raise ReadFailed("the latest release is not marked final")
    published = body.get("published_at")
    if not isinstance(published, str) or not ISO_Z.fullmatch(published):
        raise ReadFailed(f"published_at {published!r} is not YYYY-MM-DDTHH:MM:SSZ")
    try:
        datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise ReadFailed(f"published_at {published!r} is not a real time") from error
    return {"version": match.group(1), "tag": tag, "publishedAt": published,
            "url": f"https://github.com/{repo}/releases/tag/{tag}"}


def main():
    document = json.loads(REGISTRY.read_text(encoding="ascii"))
    changed, failed = [], []
    for app in document["apps"]:
        try:
            latest = latest_release(app["repo"])
        except ReadFailed as error:
            failed.append(f"{app['repo']}: {error}")
            continue
        if latest != app["latest"]:
            app["latest"] = latest
            changed.append(f"{app['id']} {latest['version'] if latest else 'none'}")
    if changed:
        document["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        REGISTRY.write_text(json.dumps(document, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    for line in changed:
        print(f"changed: {line}")
    for line in failed:
        print(f"failed: {line}", file=sys.stderr)
    if not changed and not failed:
        print("unchanged")
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
