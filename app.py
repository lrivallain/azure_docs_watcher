"""Azure Docs changes watcher.

A small Flask application exposing, as HTML pages, RSS feeds and JSON, the
recent commits touching a section of a public documentation repository.

It runs without any GitHub credential: see ``github_client`` for the details.
"""

import logging
import os

import coloredlogs
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    send_from_directory,
    url_for,
)
from werkzeug.exceptions import HTTPException

# https://flask.palletsprojects.com/en/latest/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix

import github_client
from config import ATOM_FEED_SIZE, AZURE_DOCS_REPOS
from errors import GitHubError
from feeds import get_feed
from utils import get_repo_config

log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

app = Flask(__name__, static_folder="static")
app.url_map.strict_slashes = False

if app.debug:
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    coloredlogs.install(level="DEBUG")
else:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    coloredlogs.install(level="INFO")


def _join_path(prefix: str, folder: str = None) -> str:
    """Join a repository articles folder and a section into a clean path.

    Args:
        prefix (str): the repository articles folder, e.g. ``/articles/``.
        folder (str, optional): the watched section.

    Returns:
        str: a slash separated path without leading nor trailing slash.
    """
    parts = [part.strip("/") for part in (prefix, folder) if part]
    return "/".join(part for part in parts if part)


def _commits_for(config_repo: dict, folder: str = None) -> list:
    """Collect the most recent commits of a section.

    Args:
        config_repo (dict): repository configuration.
        folder (str, optional): the watched section.

    Returns:
        list: the commits, most recent first.
    """
    return github_client.get_commits(
        owner=config_repo["owner"],
        repository=config_repo["repository"],
        path=_join_path(config_repo.get("articles_folder"), folder),
    )


def _as_json(commits: list) -> Response:
    """Serialize commits for the JSON API, using ISO-8601 dates.

    Args:
        commits (list): the commits to serialize.

    Returns:
        Response: the JSON response.
    """
    return jsonify(
        [
            {**commit, "date": commit["date"].isoformat() if commit["date"] else None}
            for commit in commits
        ]
    )


@app.route("/")
def home():
    """Home page, listing the curated repositories.

    Returns:
        str: html page.
    """
    return render_template(
        "home.html",
        repos=list(AZURE_DOCS_REPOS.values()),
    )


@app.route("/<repo_owner>/<repo_name>")
def repo_home(repo_owner: str, repo_name: str):
    """List the sections available for a repository.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.

    Returns:
        str: html page.
    """
    config_repo = get_repo_config(repo_owner, repo_name)
    contents = github_client.get_directory(
        owner=config_repo["owner"],
        repository=config_repo["repository"],
        path=_join_path(config_repo.get("articles_folder")),
    )
    return render_template(
        "repo_home.html",
        repository=config_repo,
        contents=contents,
        # A section index is only ever a list: a grid of cards would add
        # nothing, so the layout switch is not offered here.
        forced_view="list",
    )


@app.route("/<repo_owner>/<repo_name>/<path:folder>")
def get_commits_from_section(repo_owner: str, repo_name: str, folder: str):
    """Track the commits of a specific section of a documentation repository.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.
        folder (str): section to track.

    Returns:
        str: html page.
    """
    config_repo = get_repo_config(repo_owner, repo_name)
    commits = _commits_for(config_repo, folder)
    return render_template(
        "commits.html",
        repository=config_repo,
        folder=folder,
        commits=commits,
        feed_size=ATOM_FEED_SIZE,
    )


@app.route("/feed/<repo_owner>/<repo_name>")
@app.route("/feed/<repo_owner>/<repo_name>/<path:folder>")
def repo_feed(repo_owner: str, repo_name: str, folder: str = None):
    """RSS feed of the commits of a repository or of one of its sections.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.
        folder (str, optional): section to track.

    Returns:
        Response: the RSS feed.
    """
    config_repo = get_repo_config(repo_owner, repo_name)
    commits = _commits_for(config_repo, folder)
    if folder:
        page_url = url_for(
            "get_commits_from_section",
            repo_owner=repo_owner,
            repo_name=repo_name,
            folder=folder,
            _external=True,
        )
    else:
        page_url = url_for(
            "repo_home", repo_owner=repo_owner, repo_name=repo_name, _external=True
        )
    return Response(
        get_feed(
            commits,
            folder or config_repo.get("articles_folder"),
            config_repo,
            page_url,
        ),
        mimetype="application/rss+xml",
    )


@app.route("/api/<repo_owner>/<repo_name>")
@app.route("/api/<repo_owner>/<repo_name>/<path:folder>")
def repo_api(repo_owner: str, repo_name: str, folder: str = None):
    """JSON view of the commits of a repository or of one of its sections.

    Args:
        repo_owner (str): GitHub repository owner.
        repo_name (str): GitHub repository name.
        folder (str, optional): section to track.

    Returns:
        Response: the JSON response.
    """
    config_repo = get_repo_config(repo_owner, repo_name)
    commits = _commits_for(config_repo, folder)
    return _as_json(commits)


# Issue #21: the RSS readers look for a favicon at the root of the domain.
@app.route("/favicon.ico")
def favicon():
    """Serve the favicon from the static folder.

    Returns:
        Response: the favicon.
    """
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.errorhandler(GitHubError)
def github_error(error: GitHubError):
    """Render the failures raised while talking to GitHub.

    Args:
        error (GitHubError): the raised error.

    Returns:
        tuple: the rendered page and its status code.
    """
    log.warning("GitHub error %s: %s", error.status_code, error.message)
    return (
        render_template(
            "error.html", error_code=error.status_code, error_message=error.message
        ),
        error.status_code,
    )


@app.errorhandler(HTTPException)
def http_error(error: HTTPException):
    """Render any HTTP error with the application layout.

    Args:
        error (HTTPException): the raised error.

    Returns:
        tuple: the rendered page and its status code.
    """
    log.info("%s: %s", error.code, error.description)
    return (
        render_template(
            "error.html", error_code=error.code, error_message=error.description
        ),
        error.code,
    )
