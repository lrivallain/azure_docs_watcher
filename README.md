<img src="/static/favicon.svg" width="180" alt="">

# [Azure Docs changes watcher](https://azdocswatch.vupti.me)

Transform changes made to the Azure and Microsoft documentation repositories to
**RSS feed** and subscribe from your preferred RSS tool.

## Features

* Browse ~20 curated **Microsoft documentation repositories** by section — Azure
  core, AI and data, security and identity, guidance and tooling.
    * The full list lives in [`config.py`](config.py).
* Watch any **custom public GitHub repository** the same way.
* **RSS feed** and JSON output for every repository and every section, with feed
  autodiscovery.

## How it works

Commit history is read from the Atom feeds published by the GitHub web
front-end:

```text
https://github.com/<owner>/<repository>/commits/<branch>/<path>.atom
```

> [!NOTE]
> GitHub serves commit feeds as a single, non-paginated page of 20 entries, with
> no date filter. Every view therefore shows the 20 most recent commits of its
> path, and on a very busy path — the root of `azure-docs` sees 40 to 120
> commits a day — those may only span a few hours. Watching a narrower section
> gives a much longer window.

## Endpoints

| Path                               | Description                 |
| ---------------------------------- | --------------------------- |
| `/`                                | Repository index            |
| `/<owner>/<repo>`                  | Sections of a repository    |
| `/<owner>/<repo>/<section>`        | Latest changes of a section |
| `/feed/<owner>/<repo>[/<section>]` | RSS feed                    |
| `/api/<owner>/<repo>[/<section>]`  | JSON output                 |

The feeds are served with an `ETag` and a `Last-Modified` date: a reader that
sends back `If-None-Match` or `If-Modified-Since` — most of them do — gets an
empty `304 Not Modified` until a new commit lands, rather than the same
document over and over.

## Development

[CONTRIBUTING.md](CONTRIBUTING.md) explains how to help

### Run & test it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

flask --app app run --debug     # http://127.0.0.1:5000
ruff check . && ruff format .   # lint and format
pytest                          # replays recorded payloads, runs offline
```

### CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) lints and tests
every push and pull request, then deploys `master` to an Azure App Service 
using a publish profile secret.

## License

MIT — see [LICENSE](LICENSE).
