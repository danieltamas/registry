#!/usr/bin/env python3
"""Checks apps.json and icons/ against the registry contract (docs/CONSUMER.md). This file is that contract's code.

Stdlib only, so CI and every agent run it the same way: python3 scripts/validate.py [path]. Exit 0 when the
file is valid, 1 with one line per problem otherwise. Consumers apply the same rules when they read the file,
so anything this accepts they accept, and anything it refuses never ships.
"""
import json
import re
import struct
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
MAX_FILE_BYTES = 64 * 1024
MAX_ICON_BYTES = 64 * 1024
ICON_SIZE = 256
# Every link and every URL inside an install command must point at one of these.
HOSTS = {"github.com", "raw.githubusercontent.com", "getrun.dev", "getcloak.dev"}
OWNER = "danieltamas"

TOP_KEYS = ["schema", "updated", "apps"]
APP_KEYS = ["id", "name", "kind", "platform", "pitch", "detail", "repo", "site", "icon", "iconShape",
            "install", "mac", "hue", "latest"]
LATEST_KEYS = ["version", "tag", "publishedAt", "url"]
ISO_Z = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
VERSION = re.compile(r"[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}")
# Printable ASCII only: no curly quotes, dashes, ellipsis or invisible characters.
PLAIN = re.compile(r"[ -~]*")
# The only two install commands a user is offered: a tap formula or cask, or one https script piped into a shell.
BREW = re.compile(rf"brew install (--cask )?{OWNER}/tap/[a-z0-9-]{{1,32}}")
CURL = re.compile(r"curl -fsSL (https://[A-Za-z0-9.-]+/[A-Za-z0-9._/-]{1,80}) \| (sh|bash)")


def text(problems, where, value, limit):
    if not isinstance(value, str) or not value.strip():
        problems.append(f"{where}: must be non-empty text")
    elif len(value) > limit:
        problems.append(f"{where}: longer than {limit} characters")
    elif not PLAIN.fullmatch(value):
        problems.append(f"{where}: only plain ASCII characters are allowed")


def allowed_url(value):
    try:
        url = urlparse(value)
        return url.scheme == "https" and url.hostname in HOSTS and not url.username and not url.password \
            and url.port is None
    except ValueError:  # urlparse raises on a malformed port or netloc: not an allowed address
        return False


def png_size(path):
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None, len(data)
    return struct.unpack(">II", data[16:24]), len(data)


def real_time(value):
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except (TypeError, ValueError):
        return False


def check_install(problems, where, command):
    if not isinstance(command, str) or len(command) > 120:
        problems.append(f"{where}: text of at most 120 characters")
        return
    curl = CURL.fullmatch(command)
    if curl:
        if not allowed_url(curl.group(1)):
            problems.append(f"{where}: {curl.group(1)} is not on an allowed host")
    elif not BREW.fullmatch(command):
        problems.append(f"{where}: 'brew install [--cask ]{OWNER}/tap/<name>' or 'curl -fsSL https://<host>/<path> | sh'")


def check_app(problems, index, app, ids, root):
    where = f"apps[{index}]"
    if not isinstance(app, dict) or list(app.keys()) != APP_KEYS:
        problems.append(f"{where}: keys must be exactly {', '.join(APP_KEYS)} in that order")
        return
    where = f"apps[{app.get('id')}]"
    if not isinstance(app["id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", app["id"]):
        problems.append(f"{where}.id: lowercase letters, digits and '-', at most 32")
    elif app["id"] in ids:
        problems.append(f"{where}.id: duplicate")
    else:
        ids.add(app["id"])
    text(problems, f"{where}.name", app["name"], 32)
    if app["kind"] not in ("menu-bar", "terminal"):
        problems.append(f"{where}.kind: menu-bar or terminal")
    text(problems, f"{where}.platform", app["platform"], 32)
    text(problems, f"{where}.pitch", app["pitch"], 80)
    text(problems, f"{where}.detail", app["detail"], 200)
    if not isinstance(app["repo"], str) or not re.fullmatch(rf"{OWNER}/[A-Za-z0-9._-]+", app["repo"]) \
            or app["repo"].split("/")[1] in (".", ".."):
        problems.append(f"{where}.repo: {OWNER}/<name>")
    if app["site"] is not None and not (isinstance(app["site"], str) and len(app["site"]) <= 100
                                        and PLAIN.fullmatch(app["site"]) and allowed_url(app["site"])):
        problems.append(f"{where}.site: null or an https address on an allowed host, at most 100 characters")
    icon = app["icon"]
    if not isinstance(icon, str) or not re.fullmatch(r"icons/[a-z0-9-]+\.png", icon):
        problems.append(f"{where}.icon: icons/<name>.png")
    elif not (root / icon).is_file():
        problems.append(f"{where}.icon: {icon} does not exist")
    else:
        size, length = png_size(root / icon)
        if size != (ICON_SIZE, ICON_SIZE):
            problems.append(f"{where}.icon: must be a {ICON_SIZE} x {ICON_SIZE} PNG")
        if length > MAX_ICON_BYTES:
            problems.append(f"{where}.icon: larger than {MAX_ICON_BYTES} bytes")
    if app["iconShape"] not in ("macos", "full-bleed"):
        problems.append(f"{where}.iconShape: macos or full-bleed")
    check_install(problems, f"{where}.install", app["install"])
    mac = app["mac"]
    if mac is not None:
        if not isinstance(mac, dict) or list(mac.keys()) != ["bundleId", "sourceKey"]:
            problems.append(f"{where}.mac: null or exactly bundleId, sourceKey")
        else:
            if not isinstance(mac["bundleId"], str) or not re.fullmatch(r"ro\.danieltamas\.[a-z0-9.-]+", mac["bundleId"]):
                problems.append(f"{where}.mac.bundleId: ro.danieltamas.<name>")
            if mac["sourceKey"] is not None and not (isinstance(mac["sourceKey"], str)
                                                     and re.fullmatch(r"[A-Za-z]{1,32}Source", mac["sourceKey"])):
                problems.append(f"{where}.mac.sourceKey: null or <Name>Source")
    hue = app["hue"]
    if not isinstance(hue, dict) or list(hue.keys()) != ["dark", "light"] \
            or not all(isinstance(v, str) and re.fullmatch(r"#[0-9A-F]{6}", v) for v in hue.values()):
        problems.append(f"{where}.hue: dark and light as #RRGGBB, uppercase")
    latest = app["latest"]
    if latest is not None:
        if not isinstance(latest, dict) or list(latest.keys()) != LATEST_KEYS:
            problems.append(f"{where}.latest: null or exactly {', '.join(LATEST_KEYS)}")
            return
        if not isinstance(latest["version"], str) or not VERSION.fullmatch(latest["version"]):
            problems.append(f"{where}.latest.version: X.Y.Z")
        if latest["tag"] not in (latest["version"], f"v{latest['version']}"):
            problems.append(f"{where}.latest.tag: the version, with or without a leading v")
        if not isinstance(latest["publishedAt"], str) or not ISO_Z.fullmatch(latest["publishedAt"]) \
                or not real_time(latest["publishedAt"]):
            problems.append(f"{where}.latest.publishedAt: YYYY-MM-DDTHH:MM:SSZ")
        if latest["url"] != f"https://github.com/{app['repo']}/releases/tag/{latest['tag']}":
            problems.append(f"{where}.latest.url: https://github.com/<repo>/releases/tag/<tag>")


def validate(path):
    problems = []
    raw = path.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        problems.append(f"{path.name}: larger than {MAX_FILE_BYTES} bytes")
    try:
        document = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as error:
        return [f"{path.name}: not ASCII JSON ({error})"]
    if not isinstance(document, dict) or list(document.keys()) != TOP_KEYS:
        return problems + [f"{path.name}: keys must be exactly {', '.join(TOP_KEYS)}"]
    if type(document["schema"]) is not int or document["schema"] != 1:  # not True, not 1.0
        problems.append("schema: must be 1")
    if document["updated"] is not None and not (isinstance(document["updated"], str) and ISO_Z.fullmatch(document["updated"])
                                                and real_time(document["updated"])):
        problems.append("updated: null or YYYY-MM-DDTHH:MM:SSZ")
    apps = document["apps"]
    if not isinstance(apps, list) or not 1 <= len(apps) <= 32:
        return problems + ["apps: a list of 1 to 32 apps"]
    ids = set()
    for index, app in enumerate(apps):
        check_app(problems, index, app, ids, path.parent)
    return problems


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "apps.json"
    problems = validate(path)
    for problem in problems:
        print(f"invalid: {problem}")
    if not problems:
        print(f"valid: {path.name}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
