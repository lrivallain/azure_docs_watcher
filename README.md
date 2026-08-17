<img src="/static/favicon.svg" width="250">

# [Azure Docs changes watcher](https://azdocswatch.vupti.me)

Follow the changes made to the Azure documentation repositories, as a web page,
an **RSS feed** or **JSON**.

* Free software: MIT license

## Features

* Browse the sections of the Azure and Microsoft documentation repositories:
  * **Azure core** — [Azure Docs](https://github.com/MicrosoftDocs/azure-docs),
    [Compute](https://github.com/MicrosoftDocs/azure-compute-docs),
    [AKS](https://github.com/MicrosoftDocs/azure-aks-docs),
    [Databases](https://github.com/MicrosoftDocs/azure-databases-docs),
    [SQL](https://github.com/MicrosoftDocs/sql-docs),
    [Monitor](https://github.com/MicrosoftDocs/azure-monitor-docs),
    [Security](https://github.com/MicrosoftDocs/azure-security-docs),
    [Local](https://github.com/MicrosoftDocs/azure-stack-docs),
    [IoT Edge](https://github.com/Azure/iotedge),
    [Quantum](https://github.com/MicrosoftDocs/quantum-docs)
  * **AI and data** — [Azure AI and Foundry](https://github.com/MicrosoftDocs/azure-ai-docs),
    [Microsoft Fabric](https://github.com/MicrosoftDocs/fabric-docs)
  * **Security and identity** — [Microsoft Entra](https://github.com/MicrosoftDocs/entra-docs),
    [Defender and Sentinel](https://github.com/MicrosoftDocs/defender-docs),
    [Intune](https://github.com/MicrosoftDocs/memdocs)
  * **Guidance and tooling** — [Architecture Center](https://github.com/MicrosoftDocs/architecture-center),
    [Cloud Adoption Framework](https://github.com/MicrosoftDocs/cloud-adoption-framework),
    [Azure for Developers](https://github.com/MicrosoftDocs/azure-dev-docs),
    [Azure DevOps](https://github.com/MicrosoftDocs/azure-devops-docs)
* Watch any other public repository the same way (#17)
* See the latest changes for a given service or section
* RSS feed for every repository and every section (#7), with feed autodiscovery
* JSON output for API consumption (#23)
* Caching to keep the service fast and light on GitHub (#9)
* Grid or dense table layout, remembered across pages and visits
* Light and dark theme, following your system preference (#19)
* **No GitHub account, token or login required — anywhere**

> Microsoft has been splitting `MicrosoftDocs/azure-docs` into per-domain
> repositories: virtual machines, AKS, Cosmos DB, Monitor, AI services, machine
> learning and Defender for Cloud no longer live there. The list above follows
> the content to its new homes.

## How it works, and why there is no token

The commit history is read from the **Atom feeds published by the GitHub web
front-end**:

```text
https://github.com/<owner>/<repository>/commits/<branch>/<path>.atom
```

Those feeds are public, require no credential, and are *not* served by
`api.github.com`, so they consume no REST API rate limit at all.

The default branch of a repository is discovered from the title of the
branch-less feed (`Recent Commits to <repository>:<branch>`), which matters
because repositories do not all agree on a default branch name — `sql-docs`
uses `live`.

The only remaining call to the REST API is the directory listing used to build
the section index. It is performed anonymously and cached for a long time.

### Why this replaced the previous access token

The application used to require a shared `GITHUB_ACCESS_TOKEN`. Organizations
can cap personal access token lifetimes to as little as seven days, which turned
the deployment into a recurring manual token renewal chore. Reading public data
through public endpoints removes that dependency entirely.

## Known limitation

GitHub serves commit feeds as a **single, non paginated page of 20 entries**,
with no date filter. A section therefore always shows its 20 most recent
commits, and on a very active path — the root of `azure-docs` receives 40 to 120
commits a day — those 20 entries may only span a few hours.

Watching a more specific section gives a much longer window. The previous
token-based implementation was capped at 20 commits too, so this is not a
regression.

## Configuration

Everything is optional; the application starts with no environment variable set.

| Variable                     | Default | Description                                        |
| ---------------------------- | ------- | -------------------------------------------------- |
| `AZDOCSWATCH_CACHE_SIZE`     | `1024`  | Maximum number of cache entries                    |
| `AZDOCSWATCH_CACHE_TTL`      | `600`   | Base cache lifetime, in seconds                    |
| `AZDOCSWATCH_HTTP_TIMEOUT`   | `10`    | Timeout of the calls to GitHub, in seconds         |
| `AZDOCSWATCH_USER_AGENT`     | —       | `User-Agent` sent to GitHub                        |

## Running it locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

flask --app app run --debug        # http://127.0.0.1:5000
```

Or the way it runs in production:

```bash
gunicorn -b 127.0.0.1:8000 app:app
```

## Development

```bash
ruff check .            # lint
ruff format .           # format
pytest                  # tests, no network access required
```

The tests replay recorded GitHub payloads, so the suite runs offline.

## Deployment

The application is deployed to Azure App Service by
[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml), which lints and
tests every push and pull request, and deploys `master` only when those pass.
Dependencies are installed on Azure by Oryx from `requirements.txt`.

The deployment authenticates with a publish profile stored in the
`AZUREAPPSERVICE_PUBLISHPROFILE_*` secret. Switching to
[OpenID Connect](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect)
with `azure/login@v3` removes that long-lived secret and is recommended.

## Endpoints

| Path                             | Description                        |
| -------------------------------- | ---------------------------------- |
| `/`                              | Repository index                   |
| `/<owner>/<repo>`                | Sections of a repository           |
| `/<owner>/<repo>/<section>`      | Latest changes of a section        |
| `/feed/<owner>/<repo>[/<section>]` | RSS feed                         |
| `/api/<owner>/<repo>[/<section>]`  | JSON output                      |

Every view returns the 20 most recent commits of the path.
