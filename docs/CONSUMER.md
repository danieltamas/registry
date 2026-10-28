# Showing More apps from the registry

The contract for any app that lists the other apps (MacMax, Bton, RMJ). The app reads one file, `apps.json`,
and the icons next to it. It makes no other call for this page: no GitHub API, no per-app lookups.

## Where to read

```
https://raw.githubusercontent.com/danieltamas/registry/main/apps.json
https://raw.githubusercontent.com/danieltamas/registry/main/<icon>      e.g. .../main/icons/bton.png
```

`raw.githubusercontent.com` is a file host: no API rate limit, no token, cached by GitHub for about five
minutes. Send a `User-Agent` naming the app (`MacMax/0.4.0`). Timeouts: 10 s per request, 30 s overall.

## The file

```json
{
  "schema": 1,
  "updated": "2026-10-28T14:00:00Z",
  "apps": [
    {
      "id": "bton",
      "name": "Bton",
      "kind": "menu-bar",
      "platform": "macOS",
      "pitch": "Pull requests that move themselves.",
      "detail": "Runs your team's review flow with coding agents, ...",
      "repo": "danieltamas/bton",
      "site": null,
      "icon": "icons/bton.png",
      "iconShape": "macos",
      "install": "brew install --cask danieltamas/tap/bton",
      "mac": {"bundleId": "ro.danieltamas.bton", "sourceKey": "BtonSource"},
      "hue": {"dark": "#5EE6E0", "light": "#0B7F86"},
      "latest": {"version": "0.10.1", "tag": "v0.10.1", "publishedAt": "2026-10-20T09:12:44Z",
                 "url": "https://github.com/danieltamas/bton/releases/tag/v0.10.1"}
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `schema` | `1`. A consumer reads only the schema numbers it knows (below). |
| `updated` | When the refresh last changed a `latest`; `null` before the first refresh. |
| `id` | Stable slug. A consumer drops its own id from the list. |
| `kind` | `menu-bar` or `terminal`: the two groups on the page, in that order. |
| `platform` | Short chip text: `macOS`, `macOS and Linux`, `CLI and VS Code`. |
| `pitch`, `detail` | One line (at most 80 characters) and two lines (at most 200). |
| `repo` | `danieltamas/<name>`. The GitHub link is `https://github.com/<repo>`. |
| `site` | `null` or the app's website. |
| `icon`, `iconShape` | A 256 x 256 PNG. `macos`: already a macOS icon with its own margin and shape, draw it as is. `full-bleed`: a square that fills its canvas, inset it 10% and clip to a continuous 22.5% corner. |
| `install` | One command the user copies. |
| `mac` | `null` for apps with no Mac bundle. `bundleId` finds the installed copy; `sourceKey`, when not `null`, names the Info.plist key a source build stamps with `git describe`. |
| `hue` | The card's accent, `#RRGGBB`, for dark and light appearance. |
| `latest` | `null`: no release yet. Otherwise the newest final release, written by the registry's refresh. |

The order of `apps` is the order to show. Fields may be added within schema 1; a consumer ignores keys it
does not know. A field removed or a meaning changed bumps `schema`.

## Reading it

1. **Ship a snapshot.** The app bundles a copy of `apps.json` and the icons, taken at build time from this
   repository, so the page is full on first launch and offline. The bundled copy is the starting "last good".
2. **Refresh** when the page opens and the last good is older than one hour, and on the page's refresh button
   (always). Never on a timer while the page is closed.
3. **Validate the whole file before using any of it.** The rules are those of `scripts/validate.py`, the code
   form of this contract, with two differences: a consumer ignores keys it does not know (the script refuses
   them), and it checks the `icon` path's form, not that the file exists (step 6 handles icons). In short:
   ASCII JSON at most 64 KiB; `schema` known; every field present with its type and limits; ASCII digits only;
   times that are real UTC times; `repo` under `danieltamas/`; `site` `null` or `https` on `github.com`,
   `raw.githubusercontent.com`, `getrun.dev` or `getcloak.dev`; `install` exactly
   `brew install [--cask ]danieltamas/tap/<name>` or `curl -fsSL https://<allowed host>/<path> | sh` (or
   `| bash`), matched whole, never by searching inside it.
   A file whose top level fails (not JSON, too large, unknown `schema`, `apps` not a list) is refused whole:
   keep the last good and show the problem. An app entry that fails a rule is left out, and the header says
   "<n> app(s) need a newer <App> to show": a host added after this release is the usual cause. Never show an
   entry that failed.
4. **Unknown schema**: keep the last good and say "This version of <App> can't read the newer app list.
   Update <App> to see it." This is the one case the last good is knowingly old.
5. **Store** the accepted file's bytes as read, unchanged, and the time of the read, in the app home
   (`~/.macmax/registry/`, `~/.bton/registry/`, ...), mode 0600. On launch, validate the stored bytes again
   with step 3 (so the left-out count is the same as when it was read; a stored file that no longer validates
   is dropped for the bundled one). A relaunch starts from the newest good copy, not the bundled one.
6. **Icons**: fetch an icon when it is not cached, or when the accepted file names a different icon path than
   the cache holds (a changed icon always gets a new file name, so a path is never re-read). Accept only a PNG
   of at most 64 KiB whose header says 256 x 256. A failed icon keeps the cached or bundled one, else the app's
   fallback glyph; an icon never hides a card.

Present, absent and failed are three states. A failed refresh changes nothing on the cards: they keep the last
good file's values, and the header names the time of that read and the problem, so "up to date" is always
"up to date as of <time>".

## Installed copy (Mac apps only)

For an app with `mac`, find it with `NSWorkspace.shared.urlForApplication(withBundleIdentifier:)` and read
its `Contents/Info.plist`:

- `sourceKey` present in the plist: it is a source build. Its version is the stamp only when the stamp is
  exactly a clean tag (`v?X.Y.Z`); otherwise the version is unknown and the card says "Built from source"
  (help text: the stamp). Source builds keep a placeholder `CFBundleShortVersionString`; never compare it.
- Otherwise `CFBundleShortVersionString`, when it is `X.Y.Z`.

Compare against `latest.version` numerically, part by part: equal is up to date, lower is behind, higher is
ahead (a local build past the release).

## What the card says

| State | Release chip | Installed chip |
|---|---|---|
| `latest` set | `v<version>`, "Released <relative time>" | "Installed <v>, up to date" / "Installed <v>, <latest> is out" / "Installed <v>" (ahead) |
| `latest` null | "In development" | "Built from source" or "Installed <v>"; when not installed: "No release yet: watch the repository for the first one." |
| installed, version unknown | as above | "Installed, version unknown" |
| refresh failed | the last good values | the last good values, plus the problem under the header |

Show the install command only when `latest` is set: a command for an app with no release fails.
The header line says "Latest releases, checked <relative time>" with the time of the last good read, and a
refresh button that shows progress while it reads.

## Acceptance (for the tests the other vendor writes)

- A valid file is accepted; the list is in file order, grouped by `kind`, without the consumer's own id.
- A top-level failure in "Reading it" step 3 keeps the last good and shows the problem; an entry that fails
  any rule (an `http` site, a host not on the list, `brew install x | sh` or `brew install x & y` in
  `install`, a 300-character `detail`, Arabic-Indic digits in a version, `2026-99-99T99:99:99Z`) is left out
  and counted in the header, and the other entries show.
- A stored file is validated again on launch; the left-out count matches the one shown when it was read.
- An entry whose icon cannot be fetched shows with the fallback glyph.
- `schema` 2 keeps the last good and asks for an app update; an unknown extra key in schema 1 is ignored.
- No network and no stored copy: the bundled snapshot shows, with its own time.
- A refresh younger than one hour is served from the store on page open; the button always reads.
- `latest: null` shows "In development" and no install command.
- A source build stamped `v0.10.1` compares as 0.10.1; stamped `v0.10.1-57-g73f6f78` shows "Built from source".
- An icon that is not a 256 x 256 PNG, or is larger than 64 KiB, is refused and the previous icon stays.

## Reference

MacMax's first version of the page, before the registry, is the visual reference:
`Sources/MacMax/SettingsMoreApps.swift` and `MoreAppsController.swift` in danieltamas/macmax (cards, chips,
install line, icons). The registry replaces its hard-coded list and its GitHub calls; the look stays.
