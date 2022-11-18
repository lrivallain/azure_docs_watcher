"""Main module."""

import os
import logging
from markupsafe import escape
from hashlib import sha256

from flask import (
    render_template,
    Response,
    request,
    g,
    jsonify,
    redirect,
)
from werkzeug.middleware.proxy_fix import (
    ProxyFix,
)  # https://flask.palletsprojects.com/en/latest/deploying/proxy_fix/
import coloredlogs

# Import local configuration
from config import *

# Import local modules
from utils import get_feed, cache, cache_home, get_repo_config
from github_lib import get_repo_contents, get_repo, login_management, get_commits
from flask_dance.contrib.github import github as gh_auth
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
    # Manage a redirect from the lasted viewed page when logging in or out
    if session.get("next"):
        log.debug(f"Redirecting to {session.get('next')}")
        next_url = session.get("next")
        session.pop("next", None)
        return redirect(next_url, code=302)
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
    _since = SINCE
    if gh_auth.authorized:
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
    _since = SINCE
    if gh_auth.authorized:
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


@app.route("/api/<repo_owner>/<repo_name>")
@login_management
def repo_api(repo_owner: str, repo_name: str):
    """RSS Feed of commits in the repository

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.

    Returns:
        str: rss feed
    """
    _since = SINCE
    if gh_auth.authorized:
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
    return jsonify(commits)


@app.route("/feed/<repo_owner>/<repo_name>/<path:folder>")
@login_management
def section_feed(repo_owner: str, repo_name: str, folder: str):
    """RSS Feed of commits in a folder of the repository

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.
        folder (str): section to track

    Returns:
        str: rss feed
    """
    _since = SINCE
    if gh_auth.authorized:
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


@app.route("/api/<repo_owner>/<repo_name>/<path:folder>")
@login_management
def section_api(repo_owner: str, repo_name: str, folder: str):
    """RSS Feed of commits in a folder of the repository

    Args:
        repo_owner (str): GitHub repo owner.
        repo_name (str): GitHub repo name.
        folder (str): section to track

    Returns:
        str: rss feed
    """
    _since = SINCE
    if gh_auth.authorized:
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
    return jsonify(commits)
