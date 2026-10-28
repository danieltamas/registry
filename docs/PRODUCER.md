# Announcing a release to the registry

Every app in `apps.json` tells the registry when it releases. The registry then reads the release from GitHub
itself and writes `latest`; an app never writes a version into this repository.

Why a ping and not a commit: the release stays the only truth for a version, a release made by hand or a
failed release step can never leave the registry wrong (the hourly refresh corrects it), and no app holds
write access to another repository's files.

## The ping

After the GitHub release is published, run:

```
gh api repos/danieltamas/registry/dispatches -f event_type=release
```

It needs `gh` logged in as an account that can write to danieltamas/registry (the owner's). It carries no
payload: the refresh reads every app, so the ping only says "now, not at the next hour".

Then confirm the registry shows the version (the refresh takes under a minute; this waits up to three):

```
for i in $(seq 18); do v=$(gh api repos/danieltamas/registry/contents/apps.json --jq '.content | @base64d | fromjson | .apps[] | select(.repo == "danieltamas/<name>") | .latest.version'); test "$v" = "{version}" && exit 0; sleep 10; done; echo "registry shows ${v:-no release} for danieltamas/<name>, not {version}"; exit 1
```

### Projects that release with the `release` tool

Append both lines to `verify` in `.release.json`, with `<name>` replaced (`{version}` is substituted by the
tool):

```json
"verify": [
  "...the project's own checks...",
  "gh api repos/danieltamas/registry/dispatches -f event_type=release",
  "for i in $(seq 18); do v=$(gh api ...); ... exit 1"
]
```

### Projects that release another way

Add the two commands as the last step of the project's release procedure (its script, its AGENTS.md release
section, or its CI release job). A CI job needs a secret with `contents: write` on danieltamas/registry
(a fine-grained token limited to that one repository) passed to `gh` as `GH_TOKEN`; prefer running the ping
from the owner's machine when the release is cut there.

A failed ping is not a failed release: the hourly refresh picks the version up within the hour. The
confirmation line fails the verify step so the owner sees it, and re-running it is safe.

## What counts as a release

The refresh reads `GET /repos/<repo>/releases/latest`: the newest release that is neither a draft nor a
prerelease. Its tag must be `X.Y.Z` or `vX.Y.Z`; any other tag fails the refresh for that app and keeps the
previous value (the run turns red). A public repository with no release reads as `latest: null`; a repository
that does not answer at all (made private, renamed, deleted) keeps its previous value and turns the run red.

## Adding or changing an app

Edit `apps.json` by hand, never `latest` or `updated`, then `python3 scripts/validate.py`:

- `id`: lowercase slug, stable forever (consumers key their caches and their own exclusion on it).
- Copy: `pitch` one line, at most 80 characters, `detail` at most 200, plain ASCII punctuation, written for
  the user ("what it does for you"), no internal architecture.
- Icon: `icons/<id>.png`, 256 x 256 PNG, at most 64 KiB, `iconShape` `macos` for a real macOS icon or
  `full-bleed` for a square mark. **A changed icon gets a new file name** (`icons/<id>-2.png`): consumers cache
  icons by path and never re-read one.
- `install`: the one command a user copies, exactly `brew install [--cask ]danieltamas/tap/<name>` or
  `curl -fsSL https://<allowed host>/<path> | sh` (or `| bash`). Anything else is refused.
- `mac`: `null` unless it is a Mac app bundle; `sourceKey` is the Info.plist key its source build stamps.
- `hue`: the app's accent, taken from its icon or its theme, for dark and light.
- A new host in `site` or `install`: add it to `HOSTS` in `scripts/validate.py` and to the list in
  `docs/CONSUMER.md` in the same commit. Consumers carry their own copy of the list and leave out an entry on
  an unknown host, so that card shows only after each consumer's next release.

Then the new app's own repository gets the ping (above), and the consumers need no change: their next refresh
shows the card.
