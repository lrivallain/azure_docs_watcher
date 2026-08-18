<img src="/static/favicon.svg" width="180" alt="">

# [Azure Docs changes watcher](https://azdocswatch.vupti.me)

Follow the changes made to the Azure and Microsoft documentation repositories,
as a web page, an **RSS feed** or **JSON** — with **no GitHub account, token or
login required**, anywhere.

## Features

* Browse ~20 curated Microsoft documentation repositories by section — Azure
  core, AI and data, security and identity, guidance and tooling. The full list
  lives in [`config.py`](config.py).
* Watch any other public GitHub repository the same way.
* RSS feed and JSON output for every repository and every section, with feed
  autodiscovery.
* Grid or dense table layout, and a light or dark theme following your system
  preference. Both are remembered across pages and visits.
* Anonymous and cached, so the service stays fast and light on GitHub.

## How it works

Commit history is read from the Atom feeds published by the GitHub web
front-end:

```text
https://github.com/<owner>/<repository>/commits/<branch>/<path>.atom
```

Those feeds are public, need no credential, and are *not* served by
`api.github.com`, so they consume no REST API rate limit. The default branch is
taken from the title of the branch-less feed, because repositories do not all
agree on one — `sql-docs` uses `live`. The only remaining REST call is the
anonymous directory listing behind the section index, cached for a long time.

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

## Configuration

Everything is optional; the application starts with no environment variable set.

| Variable                   | Default | Description                                |
| -------------------------- | ------- | ------------------------------------------ |
| `AZDOCSWATCH_CACHE_SIZE`   | `1024`  | Maximum number of cache entries            |
| `AZDOCSWATCH_CACHE_TTL`    | `600`   | Base cache lifetime, in seconds            |
| `AZDOCSWATCH_HTTP_TIMEOUT` | `10`    | Timeout of the calls to GitHub, in seconds |
| `AZDOCSWATCH_USER_AGENT`   | —       | `User-Agent` sent to GitHub                |

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

flask --app app run --debug     # http://127.0.0.1:5000
ruff check . && ruff format .   # lint and format
pytest                          # replays recorded payloads, runs offline
```

## Deployment

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) lints and tests
every push and pull request, then deploys `master` to Azure App Service using a
publish profile secret. There, Oryx installs the dependencies from
`requirements.txt` and starts the application with gunicorn.

> [!IMPORTANT]
> App Service runs this code on **its own** runtime, not the one the workflow
> installs. The migration off Python 3.10 is still in flight, so keep these
> three in step: the App Service `linuxFxVersion`, the matrix in
> [`ci-cd.yml`](.github/workflows/ci-cd.yml), and `target-version` in
> [`pyproject.toml`](pyproject.toml).
>
> ```bash
> az webapp config set --name azdocswatch --resource-group <group> \
>   --linux-fx-version "PYTHON|3.13"
> ```

## License

MIT — see [LICENSE](LICENSE). Release notes are in [HISTORY.md](HISTORY.md), and
[CONTRIBUTING.md](CONTRIBUTING.md) explains how to help.
