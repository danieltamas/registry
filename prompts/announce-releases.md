# Prompt: tell the registry about each release

Paste into an agent working in any app listed in the registry (MacMax, Bton, RMJ, Axon, Run.dev, Cloak).
Fill `<name>`: the repository name (`macmax`, `bton`, `runmyjob`, `axon`, `run.dev`, `cloak`).

---

This project is listed in github.com/danieltamas/registry, whose `apps.json` the owner's apps read to show
their More apps page. The registry reads each app's latest GitHub release itself; it only needs a ping when a
release is published, so the new version shows within a minute instead of within the hour.

Read `https://raw.githubusercontent.com/danieltamas/registry/main/docs/PRODUCER.md` (our own repository) and
add the ping and the confirmation line to this project's release:

- With a `.release.json`: append both commands to `verify`, with `<name>` replaced and `{version}` left for the
  release tool.
- Without one: add them as the last step of the release procedure this project already uses (its release
  script, its AGENTS.md release section or its CI release job, in that order of preference). Do not create a
  `.release.json` for this alone.
- Mention the step in the project's release docs (AGENTS.md or docs/RELEASE.md) in one line.

Check the confirmation line once against the current release: with `{version}` replaced by the version the
registry shows today it exits 0. Do not cut a release to test it.

Not in scope: the registry itself, the project's tags or its release format. Tags must already be `X.Y.Z` or
`vX.Y.Z`; if they are not, stop and tell the owner.

---

## Project notes

| Project | Release today | Where the ping goes |
|---|---|---|
| macmax | `.release.json` | `verify` |
| bton | `.release.json` | `verify` |
| run.dev | `.release.json` | `verify` |
| runmyjob | no release yet, no `.release.json` | its release procedure, before the first release |
| axon | no `.release.json` | its release procedure |
| cloak | no `.release.json` | its release procedure |
