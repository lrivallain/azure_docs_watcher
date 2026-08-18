# Contributing

Contributions are welcome and appreciated — bug reports, fixes, features and
documentation alike. Credit is always given.

## Reporting bugs and proposing features

Open an issue at
<https://github.com/lrivallain/azure_docs_watcher/issues/new/choose>.

For a bug, include the steps to reproduce it, the URL you were on, and anything
about your setup that might matter. For a feature, explain how it would work and
keep the scope as narrow as possible. Issues tagged `help wanted` are open to
anyone.

## Local development

```bash
git clone git@github.com:<your-fork>/azure_docs_watcher.git
cd azure_docs_watcher

python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

flask --app app run --debug   # http://127.0.0.1:5000
```

No GitHub credential is needed: the application only reads public endpoints.

## Before opening a pull request

* `ruff check .` and `ruff format .` pass.
* `pytest` passes. The suite replays recorded GitHub payloads, so it runs
  offline; new behaviour should come with a test.
* The code runs on every Python version in the CI matrix of
  [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml).
* Public functions have a docstring, and user-visible changes are reflected in
  [`README.md`](README.md) and [`HISTORY.md`](HISTORY.md).

Sign your commits with `git commit -s`, then open the pull request against
`master`.
