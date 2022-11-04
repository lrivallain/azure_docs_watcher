"""Main module."""

import os
import datetime
import logging
import secrets
from functools import wraps
from markupsafe import escape
from hashlib import sha256

from flask import (
    Flask,
    render_template,
    Response,
    request,
    redirect,
    url_for,
    session,
    g,
)
from werkzeug.middleware.proxy_fix import (
    ProxyFix,
)  # https://flask.palletsprojects.com/en/latest/deploying/proxy_fix/
import coloredlogs
from github import Github, Repository
from github import UnknownObjectException, RateLimitExceededException
from flask_dance.contrib.github import make_github_blueprint, github as gh_auth
from cachetools import cached
from cachetools.keys import hashkey

# Import local configuration
from config import *
from utils import get_commits, get_feed, cache, cache_home

# configure logging
log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# create the Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex()
if app.debug:
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    coloredlogs.install(level="DEBUG")
else:
    # https://flask.palletsprojects.com/en/latest/deploying/proxy_fix/
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    coloredlogs.install(level="INFO")

# configure the gh-based login manager
blueprint = make_github_blueprint(
    client_id=GITHUB_CLIENT_ID, client_secret=GITHUB_CLIENT_SECRET
)
app.register_blueprint(blueprint, url_prefix="/login")


def login_suggested(f):
    """Decorator to manage the GitHub login suggestion to bypass performance limits.

    Args:
        f (_type_): function to decorate

    Returns:
        function: decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        log.debug("Checking if user is authenticated")
        g.using_shared_gh = True
        if not gh_auth.authorized:
            g.gh_token = GITHUB_ACCESS_TOKEN
        else:
            resp = gh_auth.get("/user")
            if not resp.json().get("login"):
                log.warn("User used to be authenticated but is not anymore")
                return redirect(url_for("github.login"))
            log.debug("User is authenticated")
            session["username"] = resp.json()["login"]
            g.gh_token = gh_auth.token.get("access_token")
            g.using_shared_gh = False
        g.gh = Github(g.gh_token)
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login")
def login():
    """Login route.

    Redirects to GitHub login page.
    """
    return redirect(url_for("github.login"))


@app.route("/logout")
def logout():
    """Logout route: remove session data.

    Warning: the GitHub token is not revoked !

    Returns:
        flask.redirect: Redirect to the home page
    """
    session.clear()
    return redirect(url_for("home"))


@cached(cache)
def get_repo_contents(repo: Repository, path: str, cache_key: str) -> list:
    """Get the content of a file in a GitHub repo.

    Args:
        repo (Repository): GitHub repo
        path (str): path to the file
        cache_key (str): key to use for the cache

    Returns:
        list: list of contents
    """
    return repo.get_dir_contents(path)


@cached(cache, key=lambda *args, **kwargs: hashkey(kwargs["cache_key"]))
def get_repo(g, cache_key: str) -> Repository:
    """Get the content of a file in a GitHub repo.

    Args:
        g (g): Falsh global object
        cache_key (str): key to use for the cache

    Returns:
        list: list of contents
    """
    return g.gh.get_repo(f"{AZURE_DOCS_OWNER}/{AZURE_DOCS_REPO}")


@app.route("/")
@login_suggested
def home():
    """List files and folders to get commits logs from.

    Returns:
        str: html page
    """
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    try:
        repo = get_repo(g, cache_key=f"repo-{sha256(g.gh_token.encode()).hexdigest()}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing files and folders", status=500)
    log.debug("Listing files and folders in %s", AZURE_DOCS_ARTICLES_FOLDER_PREFIX)
    try:
        contents = get_repo_contents(
            repo,
            path=AZURE_DOCS_ARTICLES_FOLDER_PREFIX.lstrip("/").rstrip("/"),
            cache_key=f"home-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing files and folders", status=500)
    return render_template(
        "index.html",
        owner=escape(AZURE_DOCS_OWNER),
        repository=escape(AZURE_DOCS_REPO),
        contents=contents,
        since=SINCE,
        max_commits=MAX_COMMITS,
    )


@app.route(f"/{AZURE_DOCS_ARTICLES_FOLDER_PREFIX}<path:folder>")
@login_suggested
def track(folder: str):
    """Track a folder in a repository

    Args:
        folder (str): folder to track

    Returns:
        str: html page
    """
    _since = int(request.args.get("since", SINCE))
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    if not folder:
        return Response("Missing folder or file to like for changes", status=400)
    try:
        repo = get_repo(g, cache_key=f"repo-{sha256(g.gh_token.encode()).hexdigest()}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    _folder_path = os.path.join(AZURE_DOCS_ARTICLES_FOLDER_PREFIX, folder)

    try:
        commits = get_commits(
            repo,
            _folder_path,
            _since,
            shared_token=g.using_shared_gh,
            cache_key=f"track-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    return render_template(
        "commits.html",
        owner=escape(AZURE_DOCS_OWNER),
        repository=escape(AZURE_DOCS_REPO),
        folder=escape(_folder_path),
        commits=commits,
        max_commits=MAX_COMMITS,
        since=_since,
    )


@app.route(f"/feed/{AZURE_DOCS_ARTICLES_FOLDER_PREFIX}<path:folder>")
@login_suggested
def feed(folder: str):
    """RSS Feed of commits in a folder of the repository

    Args:
        folder (str): folder to track

    Returns:
        str: rss feed
    """
    _since = int(request.args.get("since", SINCE))
    log.debug("Looking for repository %s/%s", AZURE_DOCS_OWNER, AZURE_DOCS_REPO)
    if not folder:
        return Response("Missing folder or file to like for changes", status=400)
    try:
        repo = get_repo(g, cache_key=f"repo-{sha256(g.gh_token.encode()).hexdigest()}")
    except UnknownObjectException:
        return Response("Repository not found", status=404)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)
    log.debug("Listing commits in %s", folder)
    _folder_path = os.path.join(AZURE_DOCS_ARTICLES_FOLDER_PREFIX, folder)

    try:
        commits = get_commits(
            repo,
            _folder_path,
            _since,
            shared_token=True,  # simulate a shared token usage to limit the length of the result
            cache_key=f"track-{sha256(g.gh_token.encode()).hexdigest()}",
        )
    except RateLimitExceededException:
        return Response("Rate limit exceeded", status=429)
    except Exception as e:
        log.error(e, e.__traceback__)
        return Response("Error while listing commits", status=500)

    return Response(get_feed(commits, folder), mimetype="text/xml")


@app.route("/favicon.svg")
@cached(cache)
def favicon():
    """Serve the favicon.

    Returns:
        flask.send_from_directory: favicon served by Flask.
    """
    return send_from_directory(
        os.path.join(app.root_path, "static"), "favicon.svg", mimetype="image/svg+xml"
    )


if __name__ == "__main__":
    app.run()
