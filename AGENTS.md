# registry: instructions for agents

The public list of the owner's open source apps (`apps.json` plus `icons/`), read by the apps that show a
More apps page. Owner: Daniel Tamas. Repo: github.com/danieltamas/registry. MIT.

## Layout

```
apps.json                       the registry, schema 1
icons/<id>.png                  256 x 256 PNG, at most 64 KiB
scripts/validate.py             the contract as code; CI and the refresh run it
scripts/refresh.py              writes each app's `latest` from GitHub; only the workflow runs it
.github/workflows/refresh.yml   hourly and on `repository_dispatch` type `release`
.github/workflows/ci.yml        validate on every push and pull request
docs/CONSUMER.md                how an app reads and shows the registry
docs/PRODUCER.md                how an app pings on release; how to add or change an app
prompts/                        prompts to paste into the agents of the other projects
```

## Rules

- **Never hand-edit `latest` or `updated`.** The refresh owns them; a release on GitHub is the only truth for a
  version. Everything else in `apps.json` is edited by hand, then `python3 scripts/validate.py` exits 0.
- **Consumers in the field read this file.** A field removed or a meaning changed breaks shipped apps: bump
  `schema` and update `docs/CONSUMER.md`, or do not do it. Adding a field is fine within schema 1.
- **A changed icon gets a new file name**; consumers cache icons by path.
- **A new host** in `site` or `install` goes into `HOSTS` in `scripts/validate.py` and the list in
  `docs/CONSUMER.md` in the same commit.
- Stdlib-only Python, no dependencies. Plain ASCII in every file. No vendor or AI attribution.
- Copy is for users: what the app does for them, no internals.
- Author `Daniel Tamas <hello@danieltamas.ro>`, Conventional Commits, no co-author trailers. Push to `main`.
  The refresh workflow's own commits (`chore: refresh latest releases`) are authored by github-actions[bot].
