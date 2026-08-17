# History

## 2.0.0 (2026-08-17)

### Removed the need for any GitHub credential

* Commits are now read from the public GitHub Atom feeds, which need no
  credential and consume no REST API rate limit.
* `GITHUB_ACCESS_TOKEN` is **no longer required nor used**. Organizations capping
  personal access token lifetimes made it a recurring manual renewal chore.
* The GitHub oAuth login was removed altogether: it only existed to raise the
  limits that no longer apply. `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are
  no longer used.
* Closes #10: the SAML enforcement issue disappears with the login flow.

### Breaking changes

* The JSON API no longer returns the `commit` field, which only held a Python
  object representation.
* JSON dates are now ISO-8601 instead of RFC 822.
* JSON commit messages and author names are no longer HTML escaped, and `sha` is
  the full sha instead of the short one.
* The `since` parameter was removed, along with `AZDOCSWATCH_SINCE`,
  `AZDOCSWATCH_MAX_SINCE` and `AZDOCSWATCH_MAX_COMMITS`. GitHub caps commit feeds at 20 non paginated entries,
  so a look-back window could only ever hide results: every view now returns the
  20 most recent commits. A quiet section shows when it actually last changed
  instead of reporting no activity. Existing `?since=` links keep working, the
  parameter is simply ignored.

### Fixed

* RSS entries were published in ascending date order; they are now newest first.
* The RSS channel link pointed at the feed itself instead of the HTML page.
* The RSS author was published as an email address holding a display name; it is
  now a proper `dc:creator`.
* RSS entries carry the full commit message as their description.
* Commit messages were HTML escaped before being XML escaped, producing double
  escaped entities in the feeds.
* A `NameError` was raised instead of the intended error page when GitHub
  refused a request.
* The Flask secret key was regenerated on every start, breaking sessions across
  restarts and workers.
* The page language was declared as French while the interface is English.

### Changed

* Bootstrap 5.3 with its native colour modes replaces the abandoned
  `bootstrap-dark-5` fork; jQuery and `js-cookie` are gone.
* All CDN assets are pinned and protected by subresource integrity.
* Pages advertise their RSS feed through autodiscovery links.
* Section listings show folders first and expose per-section RSS and JSON links.
* Dependencies are pinned, and `PyGithub`, `flask_dance`, `authlib` and
  `Flask-Login` were dropped.
* Added a test suite that runs offline, plus `ruff` linting and formatting.
* The CI workflow now lints and tests before deploying, and no longer relies on
  the retired v2 artifact actions.
* Python 3.13.

## 1.3.0 (2021-11-17)

* JSON outputs for API consumption (#23)

## 1.2.0 (2021-11-10)

* Support for custom repositories tracking (#17)
* Light/dark theme (#19)

## 1.1.0 (2021-11-09)

* Multi-repository support (Azure Docs, Azure SQL, Azure Quantum) (#15)
* Review home page
* Navigation breadcrumb

## 1.0.0 (2021-11-03)

* Use a GitHub oAuth token to increase the rate limit and the number of results.

## 0.1.0 (2022-10-31)

* First release with initial functionality and performance limitations
