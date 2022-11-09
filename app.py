"""Main module."""

import os
import datetime
import logging
from markupsafe import escape
from hashlib import sha256

from flask import (
    Flask,
    render_template,
    Response,
    request,
    g,
)
from werkzeug.middleware.proxy_fix import (
    ProxyFix,
)  # https://flask.palletsprojects.com/en/latest/deploying/proxy_fix/
import coloredlogs
from github import UnknownObjectException, RateLimitExceededException
from cachetools import cached
from cachetools.keys import hashkey

# Import local configuration
from config import *

# Import local modules
from utils import get_commits, get_feed, cache, cache_home
from github_lib import get_repo_contents, get_repo, login_management
from base_routes import *

# configure logging
log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# create the Flask app
if app.debug:
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    coloredlogs.install(level="DEBUG")
else:
    # https://flask.palletsprojects.com/en/latest/deploying/proxy_fix/
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    coloredlogs.install(level="INFO")


@app.route("/")
@login_management
def home():
    """Home page.

    Returns:
        flask.render_template: Home page
    """
    log.debug("Rendering home page")
    repos_list = []
    for repo in AZURE_DOCS_REPOS:
        repos_list.append(AZURE_DOCS_REPOS[repo])
    return render_template(
        "home.html",
        repos=repos_list,
        since=SINCE,
        max_commits=MAX_COMMITS,
    )


@app.route("/<repo>")
@app.route("/<repo>/")
@login_management
def repo_home(repo: str):
    """List files and folders to get commits logs from.

    Returns:
        str: html page
    """
    log.debug(f"Looking for repository {repo}")
    config_repo = AZURE_DOCS_REPOS.get(repo)
    if not config_repo:
        return Response("Repository not found", status=404)

    log.debug(f"Found repo in config: {config_repo}")
    try:
        repo = get_repo(
            g,
            config_repo=config_repo,
            cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    log.debug(f"Listing files and folders in {config_repo.get('articles_folder')}")
    try:
        contents = get_repo_contents(
            repo,
            path=config_repo.get("articles_folder").lstrip("/").rstrip("/"),
            cache_key=f"{config_repo.get('name')}-home-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing files and folders", status=500)
    return render_template(
        "repo_home.html",
        repository=config_repo,
        contents=contents,
        since=SINCE,
        max_commits=MAX_COMMITS,
    )


@app.route("/<repo>/<path:folder>")
@login_management
def get_commits_from_section(repo: str, folder: str):
    """Track commits on a specific section of the Azure documentation.

    Args:
        repo (str): Name of a configured repository
        folder (str): section to track

    Returns:
        str: html page
    """
    _since = int(request.args.get("since", SINCE))
    log.debug(f"Looking for repository {repo}")
    config_repo = AZURE_DOCS_REPOS.get(repo)
    if not config_repo:
        return Response("Repository not found", status=404)

    log.debug(f"Found repo in config: {config_repo}")
    if not folder:
        return Response("Missing folder or file to like for changes", status=400)
    try:
        repo = get_repo(
            g,
            config_repo=config_repo,
            cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    _folder_path = os.path.join(config_repo.get("articles_folder"), folder.lstrip("/"))
    log.debug(f"Looking for commits in {_folder_path}")

    try:
        commits = get_commits(
            repo,
            _folder_path,
            _since,
            shared_token=g.using_shared_gh,
            cache_key=f"{config_repo.get('name')}-track-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    return render_template(
        "commits.html",
        repository=config_repo,
        folder=escape(folder),
        commits=commits,
        max_commits=MAX_COMMITS,
        since=_since,
    )


@app.route("/feed/<repo>")
@login_management
def repo_feed(repo: str):
    """RSS Feed of commits in the repository

    Args:
        repo (str): Name of a configured repository

    Returns:
        str: rss feed
    """
    _since = int(request.args.get("since", SINCE))
    log.debug(f"Looking for repository {repo}")
    config_repo = AZURE_DOCS_REPOS.get(repo)
    if not config_repo:
        return Response("Repository not found", status=404)

    log.debug(f"Found repo in config: {config_repo}")
    try:
        repo = get_repo(
            g,
            config_repo=config_repo,
            cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    log.debug(f"Looking for commits in {config_repo.get('name')}")

    try:
        commits = get_commits(
            repo,
            config_repo.get("articles_folder"),
            _since,
            shared_token=True,  # simulate a shared token usage to limit the length of the result
            cache_key=f"{config_repo.get('name')}-track-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    return Response(
        get_feed(commits, config_repo.get("articles_folder"), config_repo),
        mimetype="text/xml",
    )


@app.route("/feed/<repo>/<path:folder>")
@login_management
def feed(repo: str, folder: str):
    """RSS Feed of commits in a folder of the repository

    Args:
        repo (str): Name of a configured repository
        folder (str): section to track

    Returns:
        str: rss feed
    """
    _since = int(request.args.get("since", SINCE))
    log.debug(f"Looking for repository {repo}")
    config_repo = AZURE_DOCS_REPOS.get(repo)
    if not config_repo:
        return Response("Repository not found", status=404)

    log.debug(f"Found repo in config: {config_repo}")
    if not folder:
        return Response("Missing folder or file to like for changes", status=400)
    try:
        repo = get_repo(
            g,
            config_repo=config_repo,
            cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    _folder_path = os.path.join(config_repo.get("articles_folder"), folder.lstrip("/"))
    log.debug(f"Looking for commits in {_folder_path}")

    try:
        commits = get_commits(
            repo,
            _folder_path,
            _since,
            shared_token=True,  # simulate a shared token usage to limit the length of the result
            cache_key=f"{config_repo.get('name')}-track-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    return Response(get_feed(commits, folder, config_repo), mimetype="text/xml")


if __name__ == "__main__":
    app.run()
