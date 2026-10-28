# registry

The public registry of open source apps made by Daniel Tamas: one file, [`apps.json`](apps.json), that lists
each app with its pitch, icon, install command and latest release.

The apps that show a "More apps" page (MacMax, Bton, RMJ) read it instead of carrying their own list, so a new
app or a new release shows in all of them without a release of any of them. Today it lists MacMax, Bton, RMJ,
Axon, Run.dev and Cloak.

## How it stays current

- Each app's release step pings this repository (`repository_dispatch`, [docs/PRODUCER.md](docs/PRODUCER.md)).
- The [refresh workflow](.github/workflows/refresh.yml) then reads every app's latest GitHub release and
  commits `apps.json` when something changed. It also runs every hour, so a missed ping is late, never wrong.
- [`scripts/validate.py`](scripts/validate.py) checks the file on every push and before every refresh commit.

## Reading it

```
https://raw.githubusercontent.com/danieltamas/registry/main/apps.json
```

The fields, the validation rules and how an app shows them: [docs/CONSUMER.md](docs/CONSUMER.md).

## License

MIT, see [LICENSE](LICENSE). The icons belong to their apps.
