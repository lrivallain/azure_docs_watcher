# History

## Unreleased

### Added

* The RSS feeds answer conditional requests. Every feed carries an `ETag`, a
  `Last-Modified` date and a `Cache-Control` header, so a reader polling a
  subscription gets an empty `304 Not Modified` until a new commit lands
  instead of downloading the same document again.

### Changed

* The serialized feed body is cached, keyed on the commits it publishes: the
  repeated polls of a subscription no longer rebuild an identical document, and
  the `ETag` stays stable between them.
* `feeds` no longer reads the Flask request context. The feed URL and the logo
  URL are passed in by the view, which makes the rendering a pure function of
  its arguments — a prerequisite for caching it — and testable on its own.
  `get_feed` now returns a `FeedPayload` rather than raw bytes.
* The README documents the application as it is today. Its change history moved
  here, and its inline list of watched repositories moved to `config.py`, which
  already owned it.
* `get_repo_config` moved from `utils` into `config`, next to the repository
  list it resolves against; `utils.py` is gone.
* `GITHUB_WEB_BASE` and `GITHUB_API_BASE` were undocumented overrides nothing
  set: they are plain constants again. The `AZDOCSWATCH_*` variables are
  unaffected.
* `python-dotenv` is a development dependency: production runs gunicorn and
  never reads a `.env`.

### Removed

* `AUTHORS.md`, an unreferenced `favicon.png`, a committed tool cache, and the
  cookiecutter leftovers in `.gitignore`, `.editorconfig` and `pyproject.toml`.

### Fixed

* Releases 1.0.0 to 1.3.0 were dated 2021 here; they all shipped in November
  2022, which is why 0.1.0 appeared to postdate them.

## 2.0.1 (2026-08-18)

### Fixed

* Every commit view returned a 500 in production. `datetime.UTC` is an alias
  added in Python 3.11 and the Azure App Service runs Python 3.10, so parsing a
  commit date raised `AttributeError`. The portable `datetime.timezone.utc` is
  used again.
* The CI only tested the version the workflow installed, never the one the App
  Service actually runs, so the failure could not be caught before deployment.
  Tests now run on both, and the ruff rule that introduced the alias is disabled
  until the runtime bump has landed everywhere.

## 2.0.0 (2026-08-17)

Commits are now read from the public GitHub Atom feeds, so the application needs
no GitHub credential of any kind and consumes no REST API rate limit.

### Removed

* `GITHUB_ACCESS_TOKEN` is no longer required nor used. Organizations capping
  personal access token lifetimes made it a recurring manual renewal chore.
* The GitHub oAuth login, with `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`. It
  only existed to raise limits that no longer apply, and dropping it closes the
  SAML enforcement issue (#10).
* The `PyGithub`, `flask_dance`, `authlib` and `Flask-Login` dependencies, along
  with jQuery and `js-cookie`.

### Breaking changes

* The `since` parameter is gone, with `AZDOCSWATCH_SINCE`,
  `AZDOCSWATCH_MAX_SINCE` and `AZDOCSWATCH_MAX_COMMITS`. GitHub caps commit
  feeds at 20 non paginated entries, so a look-back window could only hide
  results: every view now returns the 20 most recent commits, and a quiet
  section shows when it actually last changed instead of reporting no activity.
  Existing `?since=` links keep working, the parameter is ignored.
* The JSON API dropped the `commit` field, which only held a Python object
  representation. Dates are ISO-8601 instead of RFC 822, `sha` is the full sha,
  and messages and author names are no longer HTML escaped.

### Added

* 15 more documentation repositories. Microsoft has been splitting
  `MicrosoftDocs/azure-docs` into per-domain repositories, so virtual machines,
  AKS, Cosmos DB, Monitor, AI services, machine learning and Defender for Cloud
  were no longer reachable from the repositories listed here.
* A grid or dense table layout, shared by the repository, section and commit
  lists. The choice applies to every page and is restored before the first
  paint, so the layout does not flicker.
* RSS autodiscovery links, and per-section RSS and JSON links.
* An offline test suite, `ruff` linting and formatting, and a CI workflow that
  lints and tests before deploying, off the retired v2 artifact actions.

### Fixed

* RSS entries were published oldest first, carried only the first line of the
  commit message, and exposed the author as an email address holding a display
  name. They are now newest first, carry the full message, and use `dc:creator`.
* The RSS channel link pointed at the feed itself instead of the HTML page.
* Commit messages were HTML escaped before being XML escaped, producing double
  escaped entities in the feeds.
* Repository cards showed no hover highlight and commit cards showed two, as
  Bootstrap's `!important` utility classes overrode both.
* A `NameError` was raised instead of the error page when GitHub refused a
  request.
* The Flask secret key was regenerated on every start, breaking sessions across
  restarts and workers.
* The page language was declared as French while the interface is English.

### Changed

* Bootstrap 5.3 and its native colour modes replace the abandoned
  `bootstrap-dark-5` fork, and every CDN asset is pinned and protected by
  subresource integrity.
* Buttons and links carry a styled tooltip built from their title attribute.
* Long commit messages are clamped, so a single 80 line merge message no longer
  stretches every card of its row.
* Section listings show folders first and hide the dot and underscore prefixed
  tooling folders (`.github`, `.vscode`, `.docutune`, `_bread`) that are not
  documentation.
* Repositories without a product icon render a Bootstrap glyph instead of a
  broken image.
* Dependencies are pinned, and the application targets Python 3.13.

## 1.3.0 (2022-11-17)

* JSON outputs for API consumption (#23)

## 1.2.0 (2022-11-10)

* Support for custom repositories tracking (#17)
* Light/dark theme (#19)

## 1.1.0 (2022-11-09)

* Multi-repository support (Azure Docs, Azure SQL, Azure Quantum) (#15)
* Review home page
* Navigation breadcrumb

## 1.0.0 (2022-11-03)

* Use a GitHub oAuth token to increase the rate limit and the number of results.

## 0.1.0 (2022-10-31)

* First release with initial functionality and performance limitations
