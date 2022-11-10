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
    abort,
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
from utils import get_commits, get_feed, cache, cache_home, get_repo_config
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


@app.route("/<repo_owner>/<repo_name>")
@login_management
def repo_home(repo_owner: str, repo_name: str):
    """List files and folders to get commits logs from.

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.

    Returns:
        str: html page
    """
    config_repo = get_repo_config(repo_owner, repo_name)
    repo = get_repo(
        g,
        config_repo=config_repo,
        cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
    )
    contents = get_repo_contents(
        repo,
        path=config_repo.get("articles_folder").lstrip("/").rstrip("/"),
        cache_key=f"{config_repo.get('name')}-home-{sha256(g.gh_token.encode()).hexdigest()}",
    )
    return render_template(
        "repo_home.html",
        repository=config_repo,
        contents=contents,
        since=SINCE,
        max_commits=MAX_COMMITS,
    )


@app.route("/<repo_owner>/<repo_name>/<path:folder>")
@login_management
def get_commits_from_section(repo_owner: str, repo_name: str, folder: str):
    """Track commits on a specific section of the Azure documentation.

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.
        folder (str): section to track

    Returns:
        str: html page
    """
    _since = int(request.args.get("since", SINCE))
    config_repo = get_repo_config(repo_owner, repo_name)
    repo = get_repo(
        g,
        config_repo=config_repo,
        cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
    )

    _folder_path = os.path.join(config_repo.get("articles_folder"), folder.lstrip("/"))
    commits = get_commits(
        repo,
        _folder_path,
        _since,
        shared_token=g.using_shared_gh,
        cache_key=f"{config_repo.get('name')}-track-{sha256(g.gh_token.encode()).hexdigest()}",
    )

    return render_template(
        "commits.html",
        repository=config_repo,
        folder=escape(folder),
        commits=commits,
        max_commits=MAX_COMMITS,
        since=_since,
    )


@app.route("/feed/<repo_owner>/<repo_name>")
@login_management
def repo_feed(repo_owner: str, repo_name: str):
    """RSS Feed of commits in the repository

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.

    Returns:
        str: rss feed
    """
    _since = int(request.args.get("since", SINCE))
    config_repo = get_repo_config(repo_owner, repo_name)
    repo = get_repo(
        g,
        config_repo=config_repo,
        cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
    )
    commits = get_commits(
        repo,
        config_repo.get("articles_folder"),
        _since,
        shared_token=True,  # simulate a shared token usage to limit the length of the result
        cache_key=f"{config_repo.get('name')}-track-{sha256(g.gh_token.encode()).hexdigest()}",
    )

    return Response(
        get_feed(commits, config_repo.get("articles_folder"), config_repo),
        mimetype="text/xml",
    )


@app.route("/feed/<repo_owner>/<repo_name>/<path:folder>")
@login_management
def feed(repo_owner: str, repo_name: str, folder: str):
    """RSS Feed of commits in a folder of the repository

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.
        folder (str): section to track

    Returns:
        str: rss feed
    """
    _since = int(request.args.get("since", SINCE))
    config_repo = get_repo_config(repo_owner, repo_name)
    repo = get_repo(
        g,
        config_repo=config_repo,
        cache_key=f"{config_repo.get('name')}-{sha256(g.gh_token.encode()).hexdigest()}",
    )

    _folder_path = os.path.join(config_repo.get("articles_folder"), folder.lstrip("/"))
    commits = get_commits(
        repo,
        _folder_path,
        _since,
        shared_token=True,  # simulate a shared token usage to limit the length of the result
        cache_key=f"{config_repo.get('name')}-track-{sha256(g.gh_token.encode()).hexdigest()}",
    )
    return Response(get_feed(commits, folder, config_repo), mimetype="text/xml")
