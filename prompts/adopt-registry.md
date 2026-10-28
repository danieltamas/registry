# Prompt: replace the built-in More apps list with the registry

Paste into an agent working in MacMax, Bton or RMJ. Fill `<App>`, `<id>` and the notes for that project below.

---

The More apps page in <App> carries a hard-coded list of the owner's other apps and asks GitHub for each
one's latest release. Replace both with the registry: one file, `apps.json`, in github.com/danieltamas/registry,
that lists every app with its copy, icon, install command and latest release, kept current by the registry's
own workflow.

Read first, from the registry (our own repository, no inspection needed):
`https://raw.githubusercontent.com/danieltamas/registry/main/docs/CONSUMER.md` (the contract: fields,
validation, states, acceptance lines) and `.../main/scripts/validate.py` (the same rules as code).

Do:

1. Follow this project's AGENTS.md workflow for a feature (acceptance tests by the other vendor from the
   Acceptance lines in CONSUMER.md, implement, full suite, review, docs in the same commit).
2. A Core-level reader with no UI imports: decode and validate `apps.json` per CONSUMER.md, keep the last good
   copy and its read time in the app home, refuse an unknown `schema`, leave out a failing entry and count it.
   The rules are the contract's; do not loosen any.
3. Bundle a snapshot: a script step that copies `apps.json` and `icons/` from a pinned registry commit into the
   app's resources, and the bundle script that ships them. The bundled copy is the first "last good".
4. The page reads only the registry: remove the hard-coded list, the per-app GitHub release calls and any code
   that only they used. Keep the existing card look; map `hue`, `iconShape`, `kind` and `mac` onto it.
   Drop this app's own entry by id `<id>`.
5. Installed-copy detection stays as CONSUMER.md describes (bundle id, `sourceKey` for source builds).
6. Update the docs that named the old list or its network calls (README network section, SECURITY, ARCHITECTURE,
   DESIGN), and LOG.md for the next release.
7. Also do the producer side if it is not done yet: `prompts/announce-releases.md` in the registry.

Not in scope: changing the registry, the app's own update check, or the card design.

Done when: the page shows the registry's list with the snapshot offline, a refresh reads only
`raw.githubusercontent.com/danieltamas/registry`, the acceptance tests pass unchanged, the review has no open
P0-P2, and the app built from source shows the live list. Report what you could not verify.

---

## Project notes

| Project | id | Today | Notes |
|---|---|---|---|
| MacMax | `macmax` | `Sources/MacMax/SettingsMoreApps.swift` (list, cards), `MoreAppsController.swift` (GitHub calls, installed copies), `Support/MoreApps/*.png` | `GitHubReleases` in MacMaxCore stays: the app's own update check uses it. `InstalledStanding` and `InstalledCopy` stay. The snapshot replaces `Support/MoreApps`. |
| Bton | `bton` | `Sources/Bton/MorePane.swift` (list, cards), `ReleaseLookup` / `MoreAppReleases` for the GitHub calls | Bton's list still shows MacMax in amber; the registry's teal (from MacMax's icon) wins. |
| RMJ | `rmj` | `Sources/RMJ/MoreAppsPane.swift` (list, cards, `ReleaseFeed` calls) | Same amber note for MacMax. RMJ has no release yet: its own card in the other apps shows "In development" until it does. |
